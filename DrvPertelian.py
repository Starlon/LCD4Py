import Queue
import threading
import gobject
import time

from Text import Text
from Generic import Generic
from GenericSerial import GenericSerial

from Constants import *
from Functions import *

from ThreadedTask import ThreadedTask

rowoffset = [0x80, 0xC0, 0x94, 0xD4 ]
PERTELIAN_LCDCOMMAND = 0xFE
			
class DrvPertelian(Generic, GenericSerial, Text):
	
	def __init__ ( self, visitor, obj=None, config=None):
		Generic.__init__(self, visitor, obj, config)
		GenericSerial.__init__(self, visitor, obj, config)
		Text.__init__(self, rows=4, cols=20, yres=8, xres=5, goto=2, chars=8, char0=0)
		if obj == None:
			self.name = 'noname'
			self.port = ''
			self.baud = 19200
			self.layout_timeout = 0 #Default layout timeout. 0 = no transitions. Override at layout level.
			self.layouts = {}
			self.write_rate = .0165
		else:
			self.name = obj.name
			self.port = obj.port
			self.baud = obj.baud
			self.layout_timeout = obj.layout_timeout
			self.layouts = obj.layouts
			self.write_rate = obj.write_rate
		self.app = visitor
		self.debug = visitor.debug
		self.AddFunction("backlight", 0, self.my_backlight)
		self.write_thread = threading.Thread(target=self.write_worker)
		self.write_active = False
		self.write_queue = Queue.Queue()

	def write_worker(self):
		while self.write_active:
			byte = None
			if not self.write_queue.empty():
				try:
					byte = self.write_queue.get_nowait()
				except Queue.Empty:
					pass
			if byte is not None:
				self.ser.write(byte)
				self.ser.flushInput()
				self.ser.flushOutput()
				time.sleep(self.write_rate)

	def real_write(self, row, col, data_start, len):
		if len == 0: return
		self.SetText(row, col, self.DisplayFB[data_start:data_start+len])

	def my_backlight(self, result):
		self.SetResult(result, R_NUMBER, self.backlight)

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		self.CFGVariablesSetup()
		self.rows = self.cfg_fetch_num(self.config[key], 'rows', 4)
		self.cols = self.cfg_fetch_num(self.config[key], 'cols', 20)
		self.port = self.cfg_fetch_raw(self.config[key], 'port', '')
		self.speed = self.cfg_fetch_num(self.config[key], 'speed', 115200)
		self.backlight = self.cfg_fetch_num(self.config[key], 'backlight', 1)
		Generic.CFGSetup(self, key)

	def SetupDevice(self):
		print self.name, "CF635.SetupDevice"
		if not self.Connected(): return
		if not self.write_active:
			self.write_active = True
			self.write_thread.start()
		
		self.initiate_pertelian()
		self.adjust_backlight(self.backlight)
		self.drv_clear()

	def drv_clear(self, send_now=False):
		cmd = resizeList([], 2, int)
		cmd[0] = PERTELIAN_LCDCOMMAND
		cmd[1] = 0x01
		buffer = ''.join([chr(x) for x in cmd])
		self.drv_send(buffer, send_now)

	def adjust_backlight(self, backlight):
		cmd = resizeList([], 2, int)
		if backlight <= 0:
			backlight = 2
		elif backlight >= 1:
			backlight = 3

		cmd[0] = PERTELIAN_LCDCOMMAND
		cmd[1] = backlight
		buffer = ''.join([chr(x) for x in cmd])
		self.drv_send(buffer)

	def initiate_pertelian(self):
		cmd = resizeList([], 8, int)
		cmd[0] = PERTELIAN_LCDCOMMAND
		cmd[1] = 0x38
		cmd[2] = PERTELIAN_LCDCOMMAND
		cmd[3] = 0x06
		cmd[4] = PERTELIAN_LCDCOMMAND
		cmd[5] = 0x10 # move cursor on data write
		cmd[6] = PERTELIAN_LCDCOMMAND
		cmd[7] = 0x0c
		buffer = ''.join([chr(x) for x in cmd])
		self.drv_send(buffer)

	def TakeDown(self):
		self.write_active = False
		self.drv_clear(send_now=True)

	def SetText(self, row, col, data):
		cmd = resizeList([], 2, int)
		cmd[0] = PERTELIAN_LCDCOMMAND
		cmd[1] = rowoffset[row] + col
		buffer = ''.join([chr(x) for x in cmd])
		self.drv_send( buffer + data )

	def SetSpecialChar(self, ch, data):
		cmd = resizeList([], 11, int)
		cmd[0] = PERTELIAN_LCDCOMMAND
		cmd[1] = 0x40 + (8 * ch)
		for i in range(8):
			cmd[i + 2] = data[i] & 0x1f
		buffer = ''.join([chr(x) for x in cmd])
		self.drv_send(buffer)	

	def drv_send(self, data, send_now=False):
		for c in data:
			if send_now:
				self.ser.write(c)
				time.sleep(self.write_rate)
			else:
				self.write_queue.put(c)

