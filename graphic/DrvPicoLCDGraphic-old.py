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

from ThreadedTask import ThreadedTask

VENDOR_ID = 0x04d8
PRODUCT_ID = 0xc002
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
LIBUSB_ENDPOINT_IN = 0x80
LIBUSB_ENDPOINT_OUT = 0x00

class EnumerationType(type(c_uint)):  
	def __new__(metacls, name, bases, dict):  
		if not "_members_" in dict:  
			_members_ = {}  
			for key,value in dict.items():  
				if not key.startswith("_"):  
					_members_[key] = value  
			dict["_members_"] = _members_  
		cls = type(c_uint).__new__(metacls, name, bases, dict)  
		for key,value in cls._members_.items():  
			globals()[key] = value  
		return cls  

	def __contains__(self, value):
		return value in self._members_.values()

	def __repr__(self):
		return "<Enumeration %s>" % self.__name__

class Enumeration(c_uint):
	__metaclass__ = EnumerationType
	_members_ = {}
	def __init__(self, value):
		for k,v in self._members_.items():
			if v == value:
				self.name = k
				break
		else:
			raise ValueError("No enumeration member with value %r" % value)
		c_uint.__init__(self, value)


	@classmethod
	def from_param(cls, param):
		if isinstance(param, Enumeration):
			if param.__class__ != cls:
				raise ValueError("Cannot mix enumeration members")
			else:
				return param
		else:
			return cls(param)

	def __repr__(self):
		return "<member %s=%d of %r>" % (self.name, self.value, self.__class__)


class LIBUSB_TRANSFER_STATUS(Enumeration):
	_members_ = {'LIBUSB_TRANSFER_COMPLETED':0,
			'LIBUSB_TRANSFER_ERROR':1,
			'LIBUSB_TRANSFER_TIMED_OUT':2,
			'LIBUSB_TRANSFER_CANCELLED':3,
			'LIBUSB_TRANSFER_STALL':4,
			'LIBUSB_TRANSFER_NO_DEVICE':5,
			'LIBUSB_TRANSFER_OVERFLOW':6}

class LIBUSB_TRANSFER_FLAGS(Enumeration):
	_members_ = {'LIBUSB_TRANSFER_SHORT_NOT_OK':1<<0,
			'LIBUSB_TRANSFER_FREE_BUFFER':1<<1,
			'LIBUSB_TRANSFER_FREE_TRANSFER':1<<2}

class LIBUSB_TRANSFER_TYPE(Enumeration):
	_members_ = {'LIBUSB_TRANSFER_TYPE_CONTROL':0,
			'LIBUSB_TRANSFER_TYPE_ISOCHRONOUS':1,
			'LIBUSB_TRANSFER_TYPE_BULK':2,
			'LIBUSB_TRANSFER_TYPE_INTERRUPT':3}

class LIBUSB_CONTEXT(Structure):
	pass

class LIBUSB_DEVICE(Structure):
	pass

class LIBUSB_DEVICE_HANDLE(Structure):
	pass

class LIBUSB_CONTROL_SETUP(Structure):
	_fields_ = [("bmRequestType", c_ubyte),
			("bRequest", c_ubyte),
			("wValue", c_ushort),
			("wIndex", c_ushort),
			("wLength", c_ushort)]

class LIBUSB_ISO_PACKET_DESCRIPTOR(Structure):
	_fields_ = [("length", c_uint),
			("actual_length", c_uint),
			("status", LIBUSB_TRANSFER_STATUS)]


class LIBUSB_TRANSFER(Structure):
	pass

LIBUSB_TRANSFER_CB_FN = CFUNCTYPE(c_void_p, POINTER(LIBUSB_TRANSFER))

LIBUSB_TRANSFER._fields_ = [("dev_handle", POINTER(LIBUSB_DEVICE_HANDLE)),
			("flags", c_byte),
			("endpoint", c_ubyte),
			("type", c_ubyte),
			("timeout", c_uint),
			("status", LIBUSB_TRANSFER_STATUS),
			("length", c_int),
			("actual_length", c_int),
			("callback", LIBUSB_TRANSFER_CB_FN),
			("user_data", c_void_p),
			("buffer", POINTER(c_ubyte)),
			("num_iso_packets", c_int),
			("iso_packet_desc", POINTER(LIBUSB_ISO_PACKET_DESCRIPTOR))]

class TIMEVAL(Structure):
	_fields_ = [('tv_sec', c_long), ('tv_usec', c_long)]

lib = cdll.LoadLibrary("libusb-1.0.so")
lib.libusb_open_device_with_vid_pid.restype = POINTER(LIBUSB_DEVICE_HANDLE)
lib.libusb_alloc_transfer.restype = POINTER(LIBUSB_TRANSFER)

def libusb_fill_interrupt_transfer(transfer, dev_handle, endpoint, buffer, length, callback, user_data, timeout):
	transfer[0].dev_handle = dev_handle
	transfer[0].endpoint = endpoint
	transfer[0].type = LIBUSB_TRANSFER_TYPE_INTERRUPT
	transfer[0].timeout = timeout
	transfer[0].buffer = buffer
	transfer[0].length = length
	transfer[0].user_data = user_data
	transfer[0].callback = callback

class Command:
	def __init__(self, func=None, *args):
		self.func = func
		self.args = args

class DrvPicoLCDGraphic(Generic, Graphic):
	
	def __init__ ( self, visitor, obj=None, config=None, key=None):
		Generic.__init__(self, visitor, obj, config, DRV_GRAPHIC)
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
		self.device_poll_thread = threading.Thread(target=self.device_poll)
		self.framebuffer = resizeList([],  256 * 64, bool)
		lib.libusb_init(None)
		self.transfer = lib.libusb_alloc_transfer(0)
		self.handle = lib.libusb_open_device_with_vid_pid(None, VENDOR_ID, PRODUCT_ID)
		self.inverted = 0
		self.command_time = time.time()
		self.graphic_real_blit = self.drv_blit
		#self.graphic_clear = self.drv_clear
		self.drv_locked = False

	def device_poll(self):
		while self.Connected():
			tv = TIMEVAL(1, 0)
			r = lib.libusb_handle_events_timeout(None, byref(tv))
			if r < 0:
				break

	def command_worker(self):
		if self.drv_locked: # or time.time() - self.command_time < self.command_rate:
			return True
		try:
			tmp = self.command_queue.get_nowait()
		except Queue.Empty:
			return True
		tmp.func(*tmp.args)
		self.command_time = time.time()
		return True

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

		if self.command_id is None:
			self.command_id = gobject.timeout_add(1, self.command_worker)

		self.device_poll_thread.start()
		
		#self.initiate_contrast_backlight()

		#self.drv_clear()

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
		if lib.libusb_kernel_driver_active(self.handle, 0) < 0:
			if lib.libusb_detach_kernel_driver(self.handle, 0) < 0:
				print "Couldn't detach HID from kernel"
				return
		lib.libusb_claim_interface(self.handle, 0)

	def drv_close(self):
		lib.libusb_release_interface(self.handle, 0)
		lib.libusb_close(self.handle)
		lib.libusb_exit(None)
		lib.libusb_free_transfer(self.transfer)

	def cb_read_transfer(self, transfer):
		if transfer[0].status.value != LIBUSB_TRANSFER_COMPLETED:
			error("%s: transfer status %d" % (self.name, transfer.status))
		print "cb_read_transfer"
		#lib.libusb_submit_transfer(self.transfer)

	def cb_send_transfer(self, transfer):
		if transfer[0].status.value != LIBUSB_TRANSFER_COMPLETED:
			error("%s: transfer status %d" % (self.name, transfer.status))
		print "cb_send_transfer"
		self.drv_locked = False
		#lib.libusb_free_transfer(transfer)
		#lib.libusb_submit_transfer(self.transfer)

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

		#def f(data):
		self.drv_locked = True
		buffer = ''.join([chr(c) for c in data[:size]])
		length = len(buffer)
		out_buffer = cast(buffer, POINTER(c_ubyte))
		#transfer = lib.libusb_alloc_transfer(0)
		libusb_fill_interrupt_transfer(self.transfer, self.handle, LIBUSB_ENDPOINT_OUT + 1, out_buffer, length, LIBUSB_TRANSFER_CB_FN(self.cb_send_transfer), None, 0)
		lib.libusb_submit_transfer(self.transfer)
		while self.drv_locked:
			r = lib.libusb_handle_events(None)
			if r < 0:
				if r == LIBUSB_ERROR_INTERRUPTED:
					continue
				lib.libusb_cancel_transfer(transfer)
				while self.drv_locked:
					if lib.libusb_handle_events(None) < 0:
						break
		print "drv_send"

		#self.command_queue.put(Command(f, data))


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

		for r in range(64):
			buffer = ''
			for c in range(256):
				buffer = buffer + str(self.framebuffer[r * 256 + c])
			#print [buffer]
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

