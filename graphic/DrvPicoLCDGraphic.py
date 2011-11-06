import weakref
import threading
import Queue
import gobject
import time
import gtk, gtk.gdk
from ctypes import *

from Graphic import Graphic
from Generic import Generic
from Threaded import threaded

from Functions import *
from Constants import *

from OpenUSB import *

VENDOR_ID = 0x04d8
PRODUCT_ID = 0xc002
CLASS_CODE = 0
SUBCLASS_CODE = 0

INTERFACE_ID = 0
OUT_REPORT_LED_STATE = 0x81
OUT_REPORT_LCD_BACKLIGHT = 0x91
OUT_REPORT_LCD_CONTRAST = 0x92
OUT_REPORT_CMD = 0x94
OUT_REPORT_DATA = 0x95
OUT_REPORT_CMD_DATA = 0x96
_USBLCD_MAX_DATA_LEN = 24
IN_REPORT_KEY_STATE = 0x11
SCREEN_H = 64
SCREEN_W = 256

class DrvPicoLCDGraphic(Generic, Graphic):
	
	def __init__ ( self, visitor, obj=None, config=None, key=None):
		Generic.__init__(self, visitor, obj, config, TYPE_GRAPHIC)
		section = self.cfg_fetch_raw(config, key, None)
		Graphic.__init__(self, section, rows=SCREEN_H, cols=SCREEN_W)
		self.rows = SCREEN_H / 8
		self.cols = SCREEN_W / 6
		self.CHARS = self.rows * self.cols
		self.CHAR0 = 0
		self.chars = []
		if obj == None:
			self.contrast = 127
			self.backlight = 100
			self.command_queue = Queue.Queue()
			self.command_rate = 1
			self.layout_timeout = 0
			self.name = 'noname'
			self.connected = False
		else:
			self.contrast = obj.contrast
			self.backlight = obj.backlight
			self.command_queue = obj.command_queue0
			self.layout_timeout = obj.layout_timeout
			self.command_rate = obj.command_rate
			self.name = obj.name
			self.connected = obj.connected
		self.app = visitor
		self.debug = visitor.debug
		self.AddFunction("LCD::contrast", 1, self.my_contrast)
		self.AddFunction("LCD::backlight", 1, self.my_backlight)
		self.AddFunction("LCD::gpo", 2, self.my_gpo)
		self.command_id = None
		#self.device_poll_thread = threading.Thread(target=self.device_poll)
		self.framebuffer = resizeList([],  256 * 64, bool)
		self.inverted = 0
		self.command_time = time.time()
		self.graphic_real_blit = self.drv_blit
		#self.graphic_clear = self.drv_clear
		self.drv_locked = False

		self.libhandle = OPENUSB_HANDLE()
		self.usbhandle = OPENUSB_DEV_HANDLE()
		self.request_handle = (OPENUSB_REQUEST_HANDLE * 1)()
		self.rq_handle_references = []

	#def command_worker(self):
	#	if self.drv_locked: # or time.time() - self.command_time < self.command_rate:
	#		return True
	#	try:
	#		tmp = self.command_queue.get_nowait()
	#	except Queue.Empty:
	#		return True
	#	tmp.func(*tmp.args)
	#	self.command_time = time.time()
	#	return True

	def my_contrast(self, result, arg1):
		contrast = self.drv_contrast(self.R2N(arg1))
		self.SetResult(result, R_NUMBER, contrast)

	def my_backlight(self, result, arg1):
		backlight = self.drv_backlight(self.R2N(arg1))
		self.SetResult(result, R_NUMBER, backlight)

	def my_gpo(self, result, arg1, arg2):
		gpo = self.drv_gpo(self.R2N(arg1), self.R2N(arg2))
		self.SetResult(result, R_NUMBER, gpo)

	def SetupDevice(self):
		print self.name, "DrvPicoGraphics.SetupDevice"
		if not self.Connected(): return
		#if self.command_rate_thread.stopped():
		#	self.command_rate_thread.start()

		#if self.command_id is None:
		#	self.command_id = gobject.timeout_add(1, self.command_worker)

		#self.device_poll_thread.start()
		
		#self.initiate_contrast_backlight()

		self.drv_clear()

	def TakeDown(self):
		print "DrvPicoGraphics.TakeDown"
		#self.command_rate_thread.stop()
		if self.command_id is not None:
			gobject.source_remove(self.command_id)
			self.command_id = None

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		self.CFGVariablesSetup()
		self.contrast = self.cfg_fetch_num(self.config[key], 'contrast', 120)
		self.backlight = self.cfg_fetch_num(self.config[key], 'backlight', 100)
		Generic.CFGSetup(self, key)

	def Connect(self):
		self.drv_open()
		self.connected = True

	def Connected(self):
		return self.connected

	def Disconnect(self):
		self.connected = False
		self.drv_close()

	def initiate_contrast_backlight(self):
		self.drv_contrast(self.contrast)
		self.drv_backlight(self.backlight)
		self.emit('contrast-backlight-ready')

	def drv_open(self) :
		bus = POINTER(OPENUSB_BUSID)()
		devids = POINTER(OPENUSB_DEVID)()

		busnum = c_uint32()
		devnum = c_uint32()


		if lib.openusb_init(0, byref(self.libhandle)) != OPENUSB_SUCCESS:
			print "OpenUSB initialization error."
			return

		#lib.openusb_set_debug(self.libhandle, 5000, 0, 0)

		lib.openusb_get_busid_list(self.libhandle, byref(bus), byref(busnum))

		j = 0
		while j < busnum.value:
			print "busnum", busnum.value, j
			i = 0
			lib.openusb_get_devids_by_bus(self.libhandle, bus[j], byref(devids), byref(devnum))
			while i < devnum.value:
				devdata = POINTER(OPENUSB_DEV_DATA)()
				print "devnum", devnum.value, i
				lib.openusb_get_device_data(self.libhandle, devids[i], 0, byref(devdata))
				if devdata[0].dev_desc.bDeviceSubClass == SUBCLASS_CODE and \
					devdata[0].dev_desc.bDeviceClass == CLASS_CODE and \
					devdata[0].dev_desc.idProduct == PRODUCT_ID and \
					devdata[0].dev_desc.idVendor == VENDOR_ID:
					lib.openusb_free_device_data(devdata)
					break
				lib.openusb_free_device_data(devdata)
				i += 1
			if i >= devnum.value:
				lib.openusb_free_devid_list(devids)
			else:
				break
			j += 1

		if j >= busnum.value:
			print "OpenUSB: Cannot find device"
			return

		r = lib.openusb_open_device(self.libhandle, devids[i], USB_INIT_DEFAULT, byref(self.usbhandle))
		if r != 0:
			print "OpenUSB: Cannot open device", r, i
			return

		print "Device found"
		lib.openusb_free_devid_list(devids)
		lib.openusb_free_busid_list(bus)

		if lib.openusb_claim_interface(self.usbhandle, INTERFACE_ID, USB_INIT_DEFAULT) != OPENUSB_SUCCESS:
			print "OpenUSB: Cannot claim interface"
			return

		print "Successfully claimed interface"

	def drv_close(self):
		lib.openusb_release_interface(self.usbhandle, INTERFACE_ID)
		lib.openusb_reset(self.usbhandle)
		lib.openusb_close_device(self.usbhandle)
		lib.openusb_fini(self.libhandle)

	def drv_read(self, size):
		#if self.drv_locked or time.time() - self.command_time < self.command_rate:
		#	self.command_queue.put(Command(self.drv_read, size))
		#	return
		buffer = cast((c_char * size)(), POINTER(c_ubyte))
		libusb_fill_interrupt_transfer(self.transfer, self.handle, LIBUSB_ENDPOINT_IN + 1, byref(buffer), size, LIBUSB_TRANSFER_CB_FN(self.cb_read_transfer), None, 0)
		lib.libusb_submit_transfer(self.transfer)

	def drv_send(self, data, size):
		if not self.Connected():
			return

		buffer = ''.join(chr(c) for c in data[:size])
		out_buffer = cast(buffer, POINTER(c_uint8))
		request = (OPENUSB_INTR_REQUEST * 1)()
		request_handle = (OPENUSB_REQUEST_HANDLE * 1)()
		self.rq_handle_references.append(request_handle)

		def callback(req):
			#print "callback", req[0].req.intr[0].result.status
			self.rq_handle_references.remove(request_handle)
			return 0

		request_handle[0].dev = self.usbhandle
		request_handle[0].interface = INTERFACE_ID
		request_handle[0].endpoint = LIBUSB_ENDPOINT_OUT + 1
		request_handle[0].type = USB_TYPE_INTERRUPT
		request_handle[0].req.intr = request
		request_handle[0].cb = REQUEST_CALLBACK(callback)
		request_handle[0].arg = None

		request[0].payload = out_buffer
		request[0].length = size
		request[0].timeout = 5000
		request[0].flags = 0
		request[0].next = None

		r = lib.openusb_xfer_aio(request_handle)
		#print "result", r



	def drv_update_img(self):
		cmd3 = resizeList([], 64, int)
		cmd4 = resizeList([], 64, int)

		for cs in range(4):
			chipsel = cs << 2
			for line in range(8):
				cmd3[0] = OUT_REPORT_CMD_DATA
				cmd3[1] = chipsel
				cmd3[2] = 0x02
				cmd3[3] = 0x00
				cmd3[4] = 0x00
				cmd3[5] = 0xb8 | line
				cmd3[6] = 0x00
				cmd3[7] = 0x00
				cmd3[8] = 0x40
				cmd3[9] = 0x00
				cmd3[10] = 0x00
				cmd3[11] = 32

				cmd4[0] = OUT_REPORT_DATA
				cmd4[1] = chipsel | 0x01
				cmd4[2] = 0x00
				cmd4[3] = 0x00
				cmd4[4] = 32

				for index in range(32):
					pixel = 0x00

					for bit in range(8):
						x = cs * 64 + index
						y = (line * 8 + bit + 0) % SCREEN_H
						if self.framebuffer[y * 256 + x] ^ self.inverted:
							pixel = pixel | (1 << bit)

					cmd3[12 + index] = pixel

				for index in range(32, 64):
					pixel = 0x00

					for bit in range(8):
						x = cs * 64 + index
						y = (line * 8 + bit + 0) % SCREEN_H
						if self.framebuffer[y * 256 + x] ^ self.inverted:
							pixel = pixel | (1 << bit)

					cmd4[5 + (index - 32)] = pixel

				self.drv_send(cmd3, 44)
				self.drv_send(cmd4, 38)


	def drv_blit(self, row, col, height, width):
		for r in range(row, row + height):
			for c in range(col, col + width):
				self.framebuffer[r * 256 + c] = self.graphic_black(r, c)

		self.drv_update_img()

	def drv_clear(self):
		cmd = [0x93, 0x01, 0x00]
		cmd2 = resizeList([OUT_REPORT_CMD], 9, int)
		cmd3 = resizeList([OUT_REPORT_CMD_DATA], 64, int)
		cmd4 = resizeList([OUT_REPORT_CMD_DATA], 64, int)

		self.drv_send(cmd, 3)

		for init in range(4):
			cs = (init << 2) & 0xff
			cmd2[0] = OUT_REPORT_CMD
			cmd2[1] = cs
			cmd2[2] = 0x02
			cmd2[3] = 0x00
			cmd2[4] = 0x64
			cmd2[5] = 0x3f
			cmd2[6] = 0x00
			cmd2[7] = 0x64
			cmd2[8] = 0xc0
			
			self.drv_send(cmd2, 9)

		for cs in range(4):
			chipsel = cs << 2
			for line in range(8):
				cmd3[0] = OUT_REPORT_CMD_DATA
				cmd3[1] = chipsel
				cmd3[2] = 0x02
				cmd3[3] = 0x00
				cmd3[4] = 0x00
				cmd3[5] = 0xb8 | line
				cmd3[6] = 0x00
				cmd3[7] = 0x00
				cmd3[8] = 0x40
				cmd3[9] = 0x00
				cmd3[10] = 0x00
				cmd3[11] = 32

				temp = 0

				for index in range(32):
					cmd3[12 + index] = temp

				self.drv_send(cmd3, 64)

				cmd4[0] = OUT_REPORT_DATA
				cmd4[1] = chipsel | 0x01
				cmd4[2] = 0x00
				cmd4[3] = 0x00
				cmd4[4] = 32

				for index in range(32, 64):
					cmd4[5 + (index - 32)] = 0x00

				self.drv_send(cmd4, 64)

	def drv_contrast(self, contrast):
		cmd = [0x92, 0x00]
		if contrast < 0:
			contrast = 0
		if contrast > 255:
			contrast = 255

		cmd[1] = contrast

		self.drv_send(cmd, 2)

		return contrast

	def drv_backlight(self, backlight):
		cmd = [0x92, 0x00]

		if backlight < 0:
			backlight = 0
		if backlight >= 1:
			backlight = 200

		cmd[1] = backlight

		self.drv_send(cmd, 2)

		return backlight

	def drv_gpi(self):
		read_packet = self.drv_read(_USBLCD_MAX_DATA_LEN)

		if read_packet and read_packet[0] == IN_REPORT_KEY_STATE:
			self.emit('key-packet-ready', read_packet[1])

	def drv_gpo(self, num, val):
		cmd = [0x81, 0x00]
		if num < 0:
			num = 0
		if num > 7:
			num = 7

		if val < 0:
			val = 0
		if val > 1:
			val = 1

		if val:
			self.gpo |= 1 << num
		else:
			gpo &= ~(1 << num)

		cmd[1] = gpo
		self.drv_send(cmd, 2)

		return val

