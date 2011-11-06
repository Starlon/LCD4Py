import serial
import re
from array import array
from time import sleep
import threading
import Queue
import gobject, gtk, gtk.gdk
import time

from BufferedReader import BufferedReader
from Fan import Fan
from Text import Text
from Generic import Generic
from GenericSerial import GenericSerial

from Buffer import Buffer

from Constants import *
from Functions import *

from ThreadedTask import ThreadedTask

MAX_COMMAND = 36
MAX_DATA_LENGTH = 22

class CRC(object):
	def __init__(self):
		self.crc = '00'
	
	def copy(self):
		tmp = CRC()
		tmp.crc = self.crc
		return tmp

	def as_word(self):
		return ord(self.crc[0])+ord(self.crc[1])*256
	
	def set_crc(self, crc):
		self.crc = crc

	def __setitem__(self, key, val):
		if key == 0 and val:
			self.crc = '%c%c' % (val, self.crc[1])
		elif key == 1 and val:
			self.crc = '%c%c' % (self.crc[0], val)

	def __getitem__(self, key):
		return self.crc[key]
	
class Packet:
	def __init__(self):
		self.command = ''
		self.data = ''
		self.data_length = 0
		self.crc = CRC()

	def deepcopy(self):
		tmp = Packet()
		tmp.command = self.command
		tmp.data = self.data
		tmp.data_length = self.data_length
		tmp.crc.crc = self.crc.crc
		return tmp

class ReadLCDMemory:
	first_left = 128
	first_center = 128+8
	first_right = 128+16
	second_left = 160
	second_center = 160+8
	second_right = 160+16
	third_left = 192
	third_center = 192+8
	third_right = 192+16
	fourth_left = 224
	fourth_center = 224+8
	fourth_right = 224+16
	timeout = 500
	def __init__(self, visitor):
		self.cgram_data = {}
		self.data = {}
		self.responses = {}
		self.event_source = None
		self.start_time = time.time()
		self.visitor = visitor
		self.accum = 0
		for line in range(4,8):
			self.responses[line*32] = False
			self.data[line*32] = ''
			self.responses[line*32+8] = False
			self.data[line*32+8] = ''
			self.responses[line*32+16] = False
			self.data[line*32+16] = ''
		for char in range(0, 8):
			self.cgram_data[char*8+64] = {'char':char, 'response':False, 'data':''}
		
	def start(self):
		if self.event_source != None: gobject.source_remove(self.event_source)
		self.event_source = gobject.timeout_add(100, self.start_watch)
		self.fill_start()

	def fill_start(self):
		self.initiation_time = time.time()
		self.start_time = time.time() - self.timeout
		self.visitor.emit("8byte-fill-start")
	
	
	def cgram(self):
		buffer = ''
		for char in range(0, 8):
			if self.cgram_data[char*8+64]['response'] == False: return ''
			buffer = buffer + self.cgram_data[char*8+64]['data']
		return buffer

	def line_one(self):
		if not self.responses[self.first_left] or not self.responses[self.first_center] or not self.responses[self.first_right]: return ''
		return self.data[self.first_left] + self.data[self.first_center] + self.data[self.first_right]

	def line_two(self):
		if not self.responses[self.second_left] or not self.responses[self.second_center] or not self.responses[self.second_right]: return ''
		return self.data[self.second_left] + self.data[self.second_center] + self.data[self.second_right]

	def line_three(self):
		if not self.responses[self.third_left] or not self.responses[self.third_center] or not self.responses[self.third_right]: return ''
		return self.data[self.third_left] + self.data[self.third_center] + self.data[self.third_right]

	def line_four(self):
		if not self.responses[self.fourth_left] or not self.responses[self.fourth_center] or not self.responses[self.fourth_right]: return ''
		return self.data[self.fourth_left] + self.data[self.fourth_center] + self.data[self.fourth_right]

	def set(self, address, val):
		if address < self.first_left:
			if self.cgram_data[address]['response'] == True: print "Cgram address already filled", address; return
			self.cgram_data[address]['response'] = True
			self.cgram_data[address]['data'] = val
		else:
			if self.responses[address] == True: print "Ram address already filled", address; return
			self.responses[address] = True
			self.data[address] = val
		self.accum = self.accum + 1

	def restart(self):
		self.__init__(self.visitor)
		self.start()

	def start_watch(self):
		if not self.visitor.Connected(): return
		test = True
		c = 0
		for char in range(0, 8):
			if self.cgram_data[char*8+64]['response'] != True: test = False; c = c + 1
		for line in range(4,8):
			if self.responses[line*32] != True: test = False; c = c + 1
			if self.responses[line*32+8] != True: test = False; c = c + 1
			if self.responses[line*32+16] != True: test = False; c = c + 1
		if test:
			#print self.visitor.name, "-----Memory done-----", "Time taken", time.time()-self.initiation_time, "Commaand rate", str(self.visitor.command_rate)+"mS"
			self.visitor.emit('lcd-memory-ready', self)
			return False
		if time.time()-self.start_time > self.timeout:
			#print "Timed out filling 8byte memory -- sending new packets", self.accum
			for char in range(0, 8):
				address = char*8+64
				if self.cgram_data[address]['response'] != True:
					print "Resending for 8Bytes address", address
					self.visitor.Read8BytesMemory(address, self.callback_8bytes_memory)
			for line in range(4, 8):
				if self.responses[line*32] != True:
					print "Resending for 8bytes address", line*32
					self.visitor.Read8BytesMemory(line*32, self.callback_8bytes_memory)
				if self.responses[line*32+8] != True:
					print "Resending for 8bytes address", line*32+8
					self.visitor.Read8BytesMemory(line*32+8, self.callback_8bytes_memory)
				if self.responses[line*32+16] != True:
					print "Resending for 8bytes address", line*32+16
					self.visitor.Read8BytesMemory(line*32+16, self.callback_8bytes_memory)
			self.start_time = time.time()
		return True

	def callback_8bytes_memory(self, packet):
		address = ord(packet.data[0])
		if address >= 0x40 and address <= 0xF3:
			self.set(address, packet.data[1:])
			self.visitor.emit('8byte-packet-ready')

class Bin:
	def __init__(self, visitor):
		self.visitor = visitor
		self.dict = {}
		self.locked = False
		self.lock = threading.Lock()
		self.resent_commands = []
		self.current_memory = []
		#self.watch = threading.Thread(None, self.start_watch)
		#self.watch.start()
		gobject.timeout_add(200, self.watch)
		#visitor.connect('layout-change-before', self.empty)

	def add_current_address(self, address):
		self.current_memory.append( address)

	def del_current_address(self, address):
		for current_address in self.current_memory:
			if address == current_address: 
				self.current_memory.remove(address)

	def add(self, command, data, callback, args, priority):
		#self.lock.acquire()
		if type(args) != type([]):
			args = [args]
		r = 0x40|command
		if r not in self.dict.keys():
			self.dict[r] = []
		self.dict[r].append([command, data, callback, args, priority, time.time()])
		self.visitor.commands_sent = self.visitor.commands_sent + 1
		#self.lock.release()

	def empty(self, data=None):
		self.dict = {}
		self.locked = False
		self.resent_commands = []
		self.current_memory = []

	def process_packet(self, visitor, packet): # command, data):
		#self.lock.acquire()
		if packet.command in self.dict.keys():
			if self.dict[packet.command]:
				tmp = None
				if packet.command ^ 0x40 in self.visitor.current_command: 
					pos = self.visitor.current_command.index(packet.command ^ 0x40)
					command = self.visitor.current_command[pos] | 0x40
					if command in self.dict and command | 0x40 == 74:
						if ord(packet.data[0]) in self.current_memory:
							for i in range(0, len(self.dict[command])):
								if len(self.dict[command][i]) > 0 and len(self.dict[command][i][1]) > 0 and self.dict[command][i][1][0] == packet.data[0]: 
									self.del_current_address(ord(packet.data[0]))
									tmp = self.dict[command].pop(i)
									break
					else:
						tmp = self.dict[packet.command].pop()
				
				if tmp and tmp[2] != None: 
					tmp[2](packet, *tmp[3]) #packet, args
					self.visitor.commands_received = self.visitor.commands_received + 1
					self.visitor.response_state = self.visitor.response_state - 1
				elif tmp:
					self.visitor.response_state = self.visitor.response_state - 1
		#self.lock.release()

	def watch(self):
		#self.lock.acquire()
		if self.locked: return
		self.locked = True
		for key in self.dict.keys():
			if len(self.dict[key]) > 0:
				for i in range(0, len(self.dict[key])):
					item = self.dict[key][i]
					if time.time()-item[5] > self.visitor.response_timeout:
						if self.visitor.response_state <= 0:
							break
						self.dict[key].pop(i)
						if item[0] == 10:
							self.del_current_address(ord(item[1][0]))
						#for k in self.dict.keys():
						#	for j in range(0, len(self.dict[k])):
						#		self.dict[k][j][5] = time.time()
						#print "Fooball Timeout", self.visitor.response_timeout, "Command sent time", time.time()-item[5], self.visitor.device_name, self.visitor.response_state, "Resending command", item[0], "FirstByte", len(item[1]) > 0 and ord(item[1][0])
						self.visitor.response_state = self.visitor.response_state - 1
						self.visitor.SendCommand(item[0], item[1], item[2], item[3], item[4])
						self.resent_commands.append(item)
						self.visitor.commands_resent = self.visitor.commands_resent + 1
						#print "Sent", self.visitor.commands_sent, "Received", self.visitor.commands_received, "Resent", self.visitor.commands_resent
						break
		self.locked = False
		#self.lock.release()
		return True
							
						
						
				
			
			
class Command:
	def __init__(self, func, command, data, args):
		self.func = func
		self.command = command
		self.args = args
		self.data = data

class CFPacketVersion(Generic, GenericSerial, Text):
	
	def __init__ ( self, visitor, obj=None, config=None):
		Generic.__init__(self, visitor, obj, config)
		GenericSerial.__init__(self, visitor, obj, config)
		Text.__init__(self, rows=self.model.rows, cols=self.model.cols, yres=8, xres=6, goto=self.model.goto, chars=self.model.chars, char0=self.model.char0)
		self.commands_sent = 0
		self.commands_received = 0
		self.commands_resent = 0
		self.tossed = 0
		self.errors = 0
		self.packet = Packet()
		self.fill_buffer_thread = ThreadedTask(self.fill_buffer, None, 1)
		self.check_thread = ThreadedTask(self.check_for_packet, None, 1)
		self.buffer = BufferedReader()
		if obj == None:
			self.port = ''
			self.baud = 115200
			self.display_name = ''
			self.device_name = ''
			self.serial_number = ''
			self.path = ''
			self.device_version = ""
			self.hardware_version = ""
			self.firmware_version = ""
			self.fans = []
			self.current_command = [-1, -1]
			for i in range(0, 4):
				self.fans.append(Fan())
			self.dallas = []
			self.contrast = 127
			self.backlight = 100
			self.memory = ReadLCDMemory(self)
			self.command_queue0 = Queue.Queue()
			self.command_queue1 = Queue.Queue()
			self.response_bin = Bin(self)
			self.response = None
			self.response_state = 0
			self.response_time_init = time.time()
			self.command_limit = 0 # 0 means 1 command every <command_rate> interval. 1 means 2 commands.
			self.command_rate = 1
			self.response_timeout = 0.25
			self.active = False
			self.layout_timeout = 0 #Default layout timeout. 0 = no transitions. Override at layout level.
			self.layouts = {}
			self.name = 'noname'
		else:
			self.name = obj.name
			self.port = obj.port
			self.baud = obj.baud
			self.display_name = obj.display_name
			self.device_name = obj.device_name
			self.serial_number = obj.serial_number
			self.path = obj.path
			self.device_version = obj.device_version
			self.hardware_version = obj.hardware_version
			self.firmware_version = obj.firmware_version
			self.books = obj.books
			self.fans = obj.fans
			self.current_command = obj.current_command
			self.command_limit = obj.command_limit
			self.dallas = obj.dallas
			self.contrast = obj.contrast
			self.backlight = obj.backlight
			self.memory = ReadLCDMemory(self)
			self.command_queue0 = obj.command_queue0
			self.command_queue1 = obj.command_queue1
			self.response_bin = Bin(self)
			self.response = obj.response
			self.response_state = obj.response_state
			self.response_time_init = obj.response_time_init
			self.command_rate = obj.command_rate
			self.response_timeout = obj.response_timeout
			self.active = obj.active
			self.layout_timeout = obj.layout_timeout
			self.layouts = obj.layouts
		self.app = visitor
		self.debug = visitor.debug
		self.waiting = False
		self.AddFunction("contrast", 0, self.my_contrast)
		self.AddFunction("backlight", 0, self.my_backlight)
		self.connect('packet-ready', self.response_bin.process_packet)
		self.command_thread = ThreadedTask(self.command_worker, None, self.command_rate)
		self.crcLookupTable = array ('H',  # Define the CRC lookup table
		[0x00000,0x01189,0x02312,0x0329B,0x04624,0x057AD,0x06536,0x074BF,
		 0x08C48,0x09DC1,0x0AF5A,0x0BED3,0x0CA6C,0x0DBE5,0x0E97E,0x0F8F7,
		 0x01081,0x00108,0x03393,0x0221A,0x056A5,0x0472C,0x075B7,0x0643E,
		 0x09CC9,0x08D40,0x0BFDB,0x0AE52,0x0DAED,0x0CB64,0x0F9FF,0x0E876,
		 0x02102,0x0308B,0x00210,0x01399,0x06726,0x076AF,0x04434,0x055BD,
		 0x0AD4A,0x0BCC3,0x08E58,0x09FD1,0x0EB6E,0x0FAE7,0x0C87C,0x0D9F5,
		 0x03183,0x0200A,0x01291,0x00318,0x077A7,0x0662E,0x054B5,0x0453C,
		 0x0BDCB,0x0AC42,0x09ED9,0x08F50,0x0FBEF,0x0EA66,0x0D8FD,0x0C974,
		 0x04204,0x0538D,0x06116,0x0709F,0x00420,0x015A9,0x02732,0x036BB,
		 0x0CE4C,0x0DFC5,0x0ED5E,0x0FCD7,0x08868,0x099E1,0x0AB7A,0x0BAF3,
		 0x05285,0x0430C,0x07197,0x0601E,0x014A1,0x00528,0x037B3,0x0263A,
		 0x0DECD,0x0CF44,0x0FDDF,0x0EC56,0x098E9,0x08960,0x0BBFB,0x0AA72,
		 0x06306,0x0728F,0x04014,0x0519D,0x02522,0x034AB,0x00630,0x017B9,
		 0x0EF4E,0x0FEC7,0x0CC5C,0x0DDD5,0x0A96A,0x0B8E3,0x08A78,0x09BF1,
		 0x07387,0x0620E,0x05095,0x0411C,0x035A3,0x0242A,0x016B1,0x00738,
		 0x0FFCF,0x0EE46,0x0DCDD,0x0CD54,0x0B9EB,0x0A862,0x09AF9,0x08B70,
		 0x08408,0x09581,0x0A71A,0x0B693,0x0C22C,0x0D3A5,0x0E13E,0x0F0B7,
		 0x00840,0x019C9,0x02B52,0x03ADB,0x04E64,0x05FED,0x06D76,0x07CFF,
		 0x09489,0x08500,0x0B79B,0x0A612,0x0D2AD,0x0C324,0x0F1BF,0x0E036,
		 0x018C1,0x00948,0x03BD3,0x02A5A,0x05EE5,0x04F6C,0x07DF7,0x06C7E,
		 0x0A50A,0x0B483,0x08618,0x09791,0x0E32E,0x0F2A7,0x0C03C,0x0D1B5,
		 0x02942,0x038CB,0x00A50,0x01BD9,0x06F66,0x07EEF,0x04C74,0x05DFD,
		 0x0B58B,0x0A402,0x09699,0x08710,0x0F3AF,0x0E226,0x0D0BD,0x0C134,
		 0x039C3,0x0284A,0x01AD1,0x00B58,0x07FE7,0x06E6E,0x05CF5,0x04D7C,
		 0x0C60C,0x0D785,0x0E51E,0x0F497,0x08028,0x091A1,0x0A33A,0x0B2B3,
		 0x04A44,0x05BCD,0x06956,0x078DF,0x00C60,0x01DE9,0x02F72,0x03EFB,
		 0x0D68D,0x0C704,0x0F59F,0x0E416,0x090A9,0x08120,0x0B3BB,0x0A232,
		 0x05AC5,0x04B4C,0x079D7,0x0685E,0x01CE1,0x00D68,0x03FF3,0x02E7A,
		 0x0E70E,0x0F687,0x0C41C,0x0D595,0x0A12A,0x0B0A3,0x08238,0x093B1,
		 0x06B46,0x07ACF,0x04854,0x059DD,0x02D62,0x03CEB,0x00E70,0x01FF9,
		 0x0F78F,0x0E606,0x0D49D,0x0C514,0x0B1AB,0x0A022,0x092B9,0x08330,
		 0x07BC7,0x06A4E,0x058D5,0x0495C,0x03DE3,0x02C6A,0x01EF1,0x00F78])

	def command_worker(self):
		if not hasattr(self, "response_bin") or self.response_bin.locked: # Drivers supply the response bin
			return
		self.response_bin.locked = True
		i = self.response_state
		tmp = None
		priority = 0
		if i > self.command_limit:
			self.response_bin.locked = False
			return
		if not self.command_queue1.empty():
			try:
				tmp = self.command_queue1.get_nowait()
			except Queue.Empty:
				pass
		elif not self.command_queue0.empty():
			try:
				tmp = self.command_queue0.get_nowait()
			except Queue.Empty:
				pass
		if tmp:
			self.current_command[i] = tmp.command
			self.response_time_init = time.time()
			if tmp.command == 10:
				self.response_bin.add_current_address(ord(tmp.data[0]))
			tmp.func(tmp.data, *tmp.args)
		self.response_bin.locked = False

	def cancel_all_commands(self):
		while not self.command_queue0.empty():
			try:
				self.command_queue0.get_nowait()
			except Queue.Empty:
				break
		while not self.command_queue1.empty():
			try:
				self.command_queue1.get_nowait()
			except Queue.Empty:
				break
		self.response_bin.empty()

	def real_write(self, row, col, data_start, len):
		if len == 0: return
		self.SetText(row, col, self.DisplayFB[data_start:data_start+len])

	def my_contrast(self, result):
		self.SetResult(result, R_NUMBER, self.contrast)

	def my_backlight(self, result):
		self.SetResult(result, R_NUMBER, self.backlight)

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		self.CFGVariablesSetup()
		self.rows = self.cfg_fetch_num(self.config[key], 'rows', self.model.rows)
		self.cols = self.cfg_fetch_num(self.config[key], 'cols', self.model.cols)
		self.port = self.cfg_fetch_raw(self.config[key], 'port', '')
		self.baud = self.cfg_fetch_num(self.config[key], 'speed', 115200)
		self.contrast = self.cfg_fetch_num(self.config[key], 'contrast', 120)
		self.backlight = self.cfg_fetch_num(self.config[key], 'backlight', 100)
		Generic.CFGSetup(self, key)

	def SetupDevice(self):
		print self.name, "CF635.SetupDevice"
		if not self.Connected(): return
		if self.command_thread.stopped():
			self.command_thread.start()
		if self.fill_buffer_thread.stopped():
			self.fill_buffer_thread.start()
		if self.check_thread.stopped():
			self.check_thread.start()

		#self.initiate_memory()
		self.initiate_version()
		self.initiate_contrast_backlight()

		self.ClearLCD()
		self.SetLCDCursorStyle()
		Generic.SetupDevice(self)

	def TakeDown(self):
		self.check_thread.stop()
		self.fill_buffer_thread.stop()
		self.command_thread.stop()
		#Generic.TakeDown(self)
		self.Reboot(send_now=True)

	def initiate_version(self):
		def f(packet):
			version = packet.data
			if type(version).__name__ != 'str': return
			m = re.match('CFA(.*):h(.*),v(.*)', version)
			if not m: return
			if self.model != m.group(1):
				error("Specified model doesn't match version response %s vs. %s: %s" % (self.model, m.group(1), self.port))
			self.hardware_version = m.group(2)
			self.firmware_version = m.group(3)
			self.emit('version-ready')

		self.GetVersion(f)

	def initiate_contrast_backlight(self):
		self.SetLCDContrast(self.contrast)
		self.SetLCDBacklight(self.backlight)
		self.emit('contrast-backlight-ready')

	def getCRC (self, buffer):
		"""GetCRC (buffer) - Finds the CRC checksum buffer. SRC: CrystalFontz"""
		newCRC = 0xFFFF # Set the CRC
		for i in buffer: newCRC = (newCRC >> 8) ^ self.crcLookupTable[(newCRC^ord(i)) & 0xFF]
		return 0x10000+~newCRC; # Return the ones complement of the CRC value

	def SendCommand ( self, command, data, callback=None, args=[], priority=0, send_now=None):
		"""SendCommand (...) - Send command to display."""
		if self.ser is None or not self.ser.isOpen():
			print self.port, "Error: Not connected!"
			return

		def send(d=None):
			self.response_bin.add(command, data, callback, args, priority)
			if self.ser is None or not self.ser.isOpen():
				print self.port, "Serial not available"; return
			#print "SendingCommand on:", self.port, "Command:", command, "FirstByte:", data and ord(data[0]), "Data:", [data]
			output = '%c%c%s' % (chr(command), chr(len(data)), data )
			CRCValue = self.getCRC(output)
			output = "%s%c%c" % (output, chr(CRCValue & 0xFF), chr((CRCValue>>8)&0xFF) )
			#self.ser.flushOutput()
			#self.ser.flushInput()
			self.ser.write(output)
			self.response_state = self.response_state + 1

		if send_now:
			send()
		elif priority == 0: self.command_queue0.put(Command(send, command, data, [])) #Normal priority
		elif priority == 1: self.command_queue1.put(Command(send, command, data, [])) #Low priority

	def fill_buffer(self):
		if not self.ser: return
		if self.buffer.locked: return
		tmp = self.ReadData(MAX_DATA_LENGTH*2)
		if tmp == '': return
		self.buffer.locked = True
		self.buffer.add_data(tmp)
		self.buffer.locked = False

	def check_for_packet(self):
		if not self.ser: return
		if self.buffer.locked: return
		self.buffer.locked = True
		self.buffer.set_current(0)
		if len(self.buffer.peek(4)) != 4: self.buffer.locked = False; return
		self.buffer.set_current(0)
		tmp = self.buffer.peek()
		if tmp == '': self.buffer.locked = False; return
		if MAX_COMMAND<(0x3F&ord(tmp)): 
			self.buffer.read() 
			self.tossed = self.tossed + 1
			self.buffer.locked = False
			return 
		if (ord(tmp)&0xC0) == 0xC0:
			self.buffer.read()
			self.errors = self.errors ^ ord(tmp)
			self.buffer.locked = False
			err = ord(tmp)
			error("Report from display: %g: %s" % (err, error_names[err & 0x3F]))
			return
		self.packet.command = ord(tmp)
		tmp = self.buffer.peek()
		if tmp == '': self.buffer.locked = False; return
		if MAX_DATA_LENGTH<ord(tmp):
			self.buffer.read()
			self.tossed = self.tossed + 1
			self.buffer.locked = False
			return
		self.packet.data_length = ord(tmp)
		if len(self.buffer.peek(self.packet.data_length + 2)) < self.packet.data_length + 2:
			self.buffer.locked = False
			return
		self.buffer.set_current(self.buffer.get_current()-(self.packet.data_length + 2))
		self.packet.data = self.buffer.peek(self.packet.data_length)
		self.packet.crc[0] = self.buffer.peek()
		self.packet.crc[1] = self.buffer.peek()

		if self.packet.crc.as_word() != self.getCRC('%c%c%s' % (chr(self.packet.command), chr(self.packet.data_length), self.packet.data)):
			self.buffer.read()
			self.tossed = self.tossed + 1
			self.buffer.locked = False
			return
		self.buffer.read(self.packet.data_length+4)
		self.read_packet(self.packet.deepcopy())
		self.buffer.locked = False
		return
		
	def read_packet(self, packet):
		if packet.command == 0x80: # Keys
			self.emit('key-packet-ready', ord(packet.data[0]))
		elif packet.command == 0x81: # Fans
			if len(packet.data) < 4: return
			fan = ord(packet.data[0])
			if fan < 0 or fan > 3: return
			tach_cycles = ord(packet.data[1])
			lsb = ord(packet.data[2])
			msb = ord(packet.data[3])
			if msb == 0: return
			rpm = ((27692308L/self.fans[fan].ppr)*(tach_cycles-2))/(msb*256 + lsb)
			self.fans[fan]['rpm'] = rpm
			self.emit('fan-packet-ready', fan)
			#print "Incoming fan packet", fan, rpm
		elif packet.command == 0x82: # Temperature
			if len(packet.data) < 4: return
			index = ord(packet.data[0])
			if index > len(self.dallas)-1: return
			lsb = ord(packet.data[1])
			msb = ord(packet.data[2])
			crc_status = ord(packet.data[3])
			if crc_status == 0: return
			degc = (msb*256 + lsb) / 16
			degf = (degc*9.0)/5.0+32
			if not self.dallas[index]:
				error("Received temperature packet from unknown device.")
				return
			self.dallas[index]['degc'] = degc
			self.dallas[index]['degf'] = degf
			self.emit('temperature-packet-ready', index)
			#print "Incoming temperature packet", index, degc, degf
		else:
			#print "Incoming packet", "Command", packet.command, command_names[packet.command & 0x3F], "First Byte", packet.data and ord(packet.data[0]), "Data", [packet.data]
			self.emit('packet-ready', packet)
		return

class Protocol1(Generic, GenericSerial, Text):
	def __init__(self, model, visitor, obj=None, config=None):
		self.model = model
		Generic.__init__(self, visitor, obj, config)
		GenericSerial.__init__(self, visitor, obj, config)
		Text.__init__(self, rows=model.rows, cols=model.cols, yres=8, xres=6, goto=model.goto, chars=model.chars, char0=model.char0)
		if obj is None:
			self.port = ''
			self.baud = 19200
			self.command_rate = .0165
			self.layout_timeout = 0
		else:
			self.port = obj.port
			self.baud = obj.baud
			self.command_rate = obj.command_rate
			self.layout_timeout = obj.layout_timeout

		self.command_thread = ThreadedTask(self.command_worker, None, 1)
		self.command_queue = Queue.Queue()
		self.command_time = time.time()

	def command_worker(self):
		if time.time() - self.command_time < self.command_rate:
			return
		cmd = None
		if not self.command_queue.empty():
			try:
				cmd = self.command_queue.get_nowait()
			except Queue.Empty:
				pass
		if cmd:
			cmd()
			self.command_time = time.time()

	def real_write(self, row, col, data_start, len):
		if len == 0: return
		self.SetText(row, col, self.DisplayFB[data_start:data_start+len])

	def SetupDevice(self):
		if not self.Connected(): return
		if self.command_thread.stopped():
			self.command_thread.start()
		self.ClearLCD()
		self.QueueWrite(chr(4)) # hide cursor
		self.QueueWrite(chr(24)) # scroll off
		self.QueueWrite(chr(30)) # wrap off

		self.initiate_contrast_backlight()

	def TakeDown(self):
		self.command_thread.stop()
		self.ClearLCD(send_now=True)
		self.ser.write(' ' * 9 + chr(26) * 2) # Reboot

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		self.CFGVariablesSetup()
		self.rows = self.cfg_fetch_num(self.config[key], 'rows', self.model.rows)
		self.cols = self.cfg_fetch_num(self.config[key], 'cols', self.model.cols)
		self.port = self.cfg_fetch_raw(self.config[key], 'port', '')
		self.baud = self.cfg_fetch_num(self.config[key], 'speed', 19200)
		self.contrast = self.cfg_fetch_num(self.config[key], 'contrast', 50)
		self.backlight = self.cfg_fetch_num(self.config[key], 'backlight', 100)
		Generic.CFGSetup(self, key)

	def initiate_contrast_backlight(self):
		self.SetLCDBacklight(self.backlight)
		self.SetLCDContrast(self.contrast)

	def SetText( self, row, col, buf ):
		if not self.SetCursorPos(row, col): return
		if col + len(buf) >= self.cols:
			buf = buf[:self.cols-col-len(buf)-1]
		if self.model == "634" or self.model == "632":
			buf = self.convertToCgrom2(buf)
		self.QueueWrite(buf)

	def SetCursorPos(self, row, col):
		if row > self.rows or row < 0: return False
		if col > self.cols or col < 0: return False
		buf = "%c%c%c" % ( chr(17), chr(col), chr(row) )
		self.QueueWrite(buf)
		return True

	def  SetLCDContrast(self, level):
		if level < 0:
			level = 0
		if level > 100:
			level = 100
		buf = "%c%c" % (chr(15), chr(level))
		self.QueueWrite(buf)

	def SetLCDBacklight(self, level):
		if level < 0:
			level = 0
		if level > 100:
			level = 100
		buf = "%c%c" % (chr(14), chr(level))
		self.QueueWrite(buf)

	def SetSpecialChar(self, ch, data):
		buf = ''.join([chr(x & 0x3f) for x in data])
		buf = chr(25) + chr(ch) + buf
		self.QueueWrite(buf)	

	def ClearLCD(self, send_now = False):
		if send_now:
			self.ser.write(chr(12))
		else:
			self.QueueWrite(chr(12))

	def convertToCgrom2(self, str):
		buf = Buffer()
		buf.buffer = str
		for i in range(len(buf)):
			ch = ord(buf[i])
			if ch == 0x5d:
				buf[i] = chr(252)
			elif ch == 0x5b:
				buf[i] = chr(250)
			elif ch == 0x24:
				buf[i] = chr(162)
			elif ch == 0x40:
				buf[i] = chr(160)
			elif ch == 0x5c:
				buf[i] = chr(251)
			elif ch == 0x7b:
				buf[i] = chr(253)
			elif ch == 0x7d:
				buf[i] = chr(255)
			elif ch == 0x7c:
				buf[i] = chr(254)
			elif ch == 0x27 or ch == 0x60 or ch == 0xB4:
				buf[i] = chr(39)
			elif ch == 0xe8:
				buf[i] = chr(164)
			elif ch == 0xe9:
				buf[i] = chr(165)
			elif ch == 0xc8:
				buf[i] = chr(197)
			elif ch == 0xc9:
				buf[i] = chr(207)
			elif ch == 0xe4:
				buf[i] = chr(123)
			elif ch == 0xc4:
				buf[i] = chr(91)
			elif ch == 0xf6:
				buf[i] = chr(124)
			elif ch == 0xd6:
				buf[i] = chr(92)
			elif ch == 0xfc:
				buf[i] = chr(126)
			elif ch == 0xdc:
				buf[i] = chr(94)
			elif ch == 0x5e:
				buf[i] = chr(253)
			elif ch == 0x5f:
				buf[i] = chr(254)

		return buf.buffer

	def QueueWrite(self, data):
		def f():
			#print "queuewrite", [data]
			self.ser.write(data)
			#self.ser.flushInput()
			#self.ser.flushOutput()

		self.command_queue.put(f)

class Protocol2(CFPacketVersion):
	def __init__(self, model, visitor, obj=None, config=None):
		self.model = model
		CFPacketVersion.__init__(self, visitor, obj, config)
		self.FB = Buffer()

	def GetVersion ( self, callback):
		"""GetVersion () - Gets the current version of the LCD."""
		self.SendCommand(1, '', callback)

	def Reboot(self, callback=None, send_now=False):
		self.SendCommand(5, '%c%c%c' % (chr(8), chr(18), chr(99)), callback, send_now=send_now)

	def ClearLCD ( self ):
		self.SendCommand(6,"")
			
	def SetText ( self, row, col, buf, send_now=False):
		"""SetText ( row, col, buf ) - Sets the specified (row,col) to buf."""
		if row > 3 | row < 0: return False # Check in bounds
		if col > 19 | col < 0: return False # Check in bounds
		if len(buf) == 0: return False
		if (col+len(buf))>20: buf = buf[:20-col] # Check in bounds
		output = "%c%c%s" % ( chr(col), chr(row), buf ) # Parse the command
		self.SendCommand ( 31, output, send_now=send_now)

	def SetSpecialChar ( self, num, buf):
		"""SetSpecialChar ( num, buf) - Sets special character num to buf."""
		if num < 0 | num > 7: return False
		if len (buf) != 8: return False 
		output = ""
		for row in buf:
			output = output + chr(row)
		output = "%c%s" % ( chr(num), output )
		self.SendCommand ( 9, output)

	def SetLCDCursorStyle (self, style=0, callback=None):
		"""SetLCDCursorSytle ( style = 0) - Sets the Cursor style."""
		if (style < 0): return False # Bad Style specification
		elif ( style > 4): return False
		self.SendCommand(12, chr(style))

	def SetLCDContrast(self, level):
		if level < 0:
			level = 0
		if level > 50:
			level = 50
		self.SendCommand(13, chr(level))

	def SetLCDBacklight(self, level):
		if level < 0:
			level = 0
		if level > 100:
			level = 100
		self.SendCommand(14, chr(level))

	def SetGPO(self, num, val):
		if val < 0:
			val = 0
		if val > 100:
			val = 100
		tmp = [chr(0) for x in range(4)]
		tmp[num] = chr(val)
		self.SendCommand(17, "".join(tmp))
		
class Protocol3(CFPacketVersion):
	def __init__(self, model, visitor, obj=None, config=None):
		print "Protocol 3"
		self.model = model
		CFPacketVersion.__init__(self, visitor, obj, config)

	def initiate_memory(self):
		def f(packet):
			print "Memory start"
			self.memory.start()

		self.Ping("", f)

	def ReadUserFlash (self, callback):
		"""ReadUserFlash () - Reads the 16 byte user flash area."""
		self.SendCommand(3, "", callback)
	
	def SaveAsBootState (self):
		"""SaveAsBootState () - Saves the current state as the boot state."""
		self.SendCommand(4,"")

	def Reboot(self, callback=None, send_now=False):
		self.SendCommand(5, '%c%c%c' % (chr(8), chr(18), chr(99)), callback, send_now=send_now)

	def Read8BytesMemory(self, address, callback):
		"""Read8BytesMemory (callback) -- Read 8 bytes of LCD memory
		"""
		self.SendCommand(10, chr(address), callback, priority=1)

	def SetCursorPos (self, row, col):
		"""SetCursorPos (row, col) - Sets the cursor position to (row,col)"""
		if line > 3 | line < 0: return False # Check bounds
		if col > 19 | col < 0: return False # Check in bounds
		output = "%c%c" % (chr(col), chr(row))
		self.SendCommand (11, output)
	
	def SetLCDContrast (self, level = 95):
		"""SetLCDConstrast (level = 95) - Sets the LCD contrast level."""
		if (level > 255): level = 255
		elif (level < 0): level = 0
		self.SendCommand (13, chr(level))
	
	def SetLCDBacklight (self, level = 100):
		"""SetLCDBacklight ( level = 100 ) - Sets the LCD Back Light Level."""
		if (level > 100): level = 100
		elif (level < 0): level = 0
		self.SendCommand (14, chr(level))
	
	def ConfigureKeyReporting (self, press=63, release=63):
		"""ConfigureKeyReporting ( press = 63, release = 63 )
			Configures key reporting (nothing implement to receive this commands.
		"""
		self.SendCommand (23, "%c%c" % (chr(press),chr(release)) )
	
	def ReadKeyPad (self, callback):
		"""ReadKeyPad () - Reads the keypad (changes since last query."""
		self.SendCommand (24, "", callback)

	def ReadReportingAndStatus (self, callback):
		"""ReadReportingAndStatus () - Reads the state of the Display"""
		self.SendCommand (30, "", callback)

	def GetLCDContrast (self, callback):
		"""GetLCDConstrast () - Gets the current LCD contrast setting."""
		self.ReadReportingAndStatus(callback)
		
	def GetLCDBacklight (self, callback):
		"""GetLCDBacklight () - Gets the current backlight setting."""
		self.ReadReportingAndStatus(callback)
	
	def SetLCDCursorStyle (self, style=0, callback=None):
		"""SetLCDCursorSytle ( style = 0) - Sets the Cursor style."""
		if (style < 0): return False # Bad Style specification
		elif ( style > 4): return False
		self.SendCommand(12, chr(style))
	
	def SetBaud (self, baud=115200):
		"""SetBaud (baud = 115200) - Sets the baud rate to 115200 or 19200"""
		if baud == 19200: output =  chr(0) # Set to 19200 baud
		else: output = chr(1) # Set to 115200 baud
		self.SendCommand (33,output)
	
	def SetGPO(self, num, val):
		if val < 0:
			val = 0
		if val > 100:
			val = 100
		self.SendCommand(34, "%c%c" % (num + 1, val))

	def SetLED ( self, LED, red, green):
		"""SetLED ( LED, red, green ) - Set LED to (red,green) levels (0-100)"""
		if red > 100: red = 100 # Check the LED levels
		if red < 0: red = 0
		if green > 100: green = 100
		if green < 0: green = 0
		GreenChan = (3-LED)*2+5 # Find the green channel
		RedChan = (3-LED)*2+6 # Find the red channel
		self.SendCommand(34,"%c%c" % (chr(GreenChan),chr(green)))
		self.SendCommand(34,"%c%c" % (chr(RedChan),chr(red)))
	
	def WriteUserFlash (self, msg):
		"""WriteUserFlash (msg) - Write a 16 byte user string to the LCD."""
		if (len(msg) > 16): msg = msg[:15]
		elif (len(msg) < 16): msg = msg.ljust(16)
		self.SendCommand(2,msg)

	def Ping ( self, msg, f):
		"""Ping ( msg ) - Pings the LCD with msg, returns msg on success."""
		self.SendCommand(0, msg, f)
	
	def GetVersion ( self, callback):
		"""GetVersion () - Gets the current version of the LCD."""
		self.SendCommand(1, '', callback)
	
	def ClearLCD ( self ):
		"""ClearLCD () - Clears the LCD panel. """
		self.SendCommand(6,"")
	
	def ResetLCD ( self ):
		"""ResetLCD () - Resets the LCD panel to a default state."""
		self.ClearLCD()
		self.SetLCDCursorStyle ( 0 )
		self.SetLED (0,0,0)
		self.SetLED(1,0,0)
		self.SetLED(2,0,0)
		self.SetLED(3,0,0)
	
	def DimBacklight ( self, start = -1, stop = 0):
		"""DimBacklight ( start = -1, stop = 0 )
			Dims the backlight up or down.
		start - Starting backlight (-1 specifies the current backlight)
		stop - Ending backlight
		"""
		if start == -1: start = self.GetBacklight() # Get the current level
		
		if stop < start: # If going up, switch start & stop
			start, stop = stop, start
			rang = range (start, stop+1, 2)
			rang.reverse()
		else: rang = range (start, stop+1, 2)
			
		for i in rang: # Dim the backlight
			self.SetLCDBacklight ( i )
	
	def SetLine ( self, line, buf ):
		"""SetLine (line, buf) - Sets LINE to buf."""
		if line > 3 | line < 0: return False # Check bounds
		if len(buf) < 20: buf.ljust (20) # Pad to 20
		elif len(buf) > 20: buf = buf[0:19] # Drop the remainder
		output = "\000%c%s" % ( chr(line), buf ) # Parse the command
		self.SendCommand ( 31, output )
		
	def SetText ( self, row, col, buf, send_now=False):
		"""SetText ( row, col, buf ) - Sets the specified (row,col) to buf."""
		if row > 3 | row < 0: return False # Check in bounds
		if col > 19 | col < 0: return False # Check in bounds
		if len(buf) == 0: return False
		if (col+len(buf))>20: buf = buf[:20-col] # Check in bounds
		output = "%c%c%s" % ( chr(col), chr(row), buf ) # Parse the command
		self.SendCommand ( 31, output, send_now=send_now)
	
	def SetSpecialChar ( self, num, buf):
		"""SetSpecialChar ( num, buf) - Sets special character num to buf."""
		if num < 0 | num > 7: return False # Verify you are setting a valid character
		if len (buf) != 8: return False # Must be 8 characters long
		output = "" # Set the output to null
		for row in buf:
			output = output + chr(row)
		output = "%c%s" % ( chr(num), output )
		self.SendCommand ( 9, output)
		
class DrvCrystalfontz:
	@classmethod
	def get(cls, model, visitor, obj=None, config=None):
		scab = False
		if model[len(model)-1] == "+":
			model = model[:-1]
			scab = True
		if model not in Models.keys():
			error("Unknown Crystalfontz model %s" % model)
			return
		model = Models[model]
		if model.protocol == 1:
			MyClass = Protocol1
		elif model.protocol == 2:
			MyClass = Protocol2
		elif model.protocol == 3:
			if scab:
				MyClass = type(model.name, (SCAB, Protocol3), {})
			else:
				MyClass = Protocol3
		return MyClass(model, visitor, obj, config)
		
class Model:
	def __init__(self, name, rows, cols, gpis, gpos, protocol, payload):
		self.name = name
		self.rows = rows
		self.cols = cols
		self.gpis = gpis
		self.gpos = gpos
		self.protocol = protocol
		self.payload = payload
		if protocol == 1:
			self.goto = 3
			self.char0 = 128
		elif protocol == 2:
			self.goto = -1
			self.char0 = 0
		elif protocol == 3:
			self.goto = 3
			self.char0 = 0
		self.chars = 8

Models = {
	"533":Model("533", 2, 16, 4, 4, 2, 18),
	"626":Model("626", 2, 16, 0, 0, 1, 0),
	"631":Model("631", 2, 20, 4, 0, 3, 22),
	"632":Model("632", 2, 16, 0, 0, 1, 0),
	"633":Model("633", 2, 16, 4, 4, 2, 18),
	"634":Model("634", 4, 20, 0, 0, 1, 0),
	"635":Model("635", 4, 20, 4, 12, 3, 22),
	"636":Model("636", 2, 16, 0, 0, 1, 0),
}

class SCAB:
	FAN1 = 0x01
	FAN2 = 0x02
	FAN3 = 0x04
	FAN4 = 0x08
	def __init__(self, model, visitor, obj=None, config=None):
		Protocol3.__init__(self, model, visitor, obj, config)
		self.temp_b1, self.temp_b2, self.temp_b3, self.temp_b4 = 0, 0, 0, 0
		for c in range(0,32):
			self.dallas.append(False)

	def SetupDevice(self):
		print "SCAB.SetupDevice"
		if not self.Connected(): return
		Protocol3.SetupDevice(self)
		self.SetupDOWDevices()

	def initiate_scab(self):
		def f(packet):
			self.SetupFans()
			self.SetupFanReporting(1,1,1,1)
			self.SetupTemperatureReporting(-1)
			self.SetupDOWDevices()

		self.GetVersion(f)

	def SetupFans(self):
		print "SetupFans"
		def f(packet):
			for i in range(0, 4):
				self.fans[i]['power'] = ord(packet.data[i])
			if self.fans[0]['glitch'] != None: self.emit('fans-ready')

		self.QueryFanPowerAndFailSafeMask(f)	

		def f(packet):
			for i in range(0, 4):
				self.fans[i]['glitch'] = ord(packet.data[9+i])
			if self.fans[0]['power'] != None: self.emit('fans-ready')
	
		self.ReadReportingAndStatus(f)

	def SetupDOWDevices(self):
		print "SetupDOWDevices"
		c = [0]
		func = None
		def func(packet):
			if len(packet.data) != 9: return
			i = int(ord(packet.data[0]))
			tmp = False
			type = ord(packet.data[1])
			if type == 0x22 or type == 0x28:
				tmp = packet.data[1:]
			if not tmp: return
			tmp = {'i':i, 'type':type, 'degc':0, 'degf':0, 'name':'', 'id':"0x%02X%02X%02X%02X%02X%02X%02X%02X" %
				(ord(tmp[0]), ord(tmp[1]), ord(tmp[2]), ord(tmp[3]), ord(tmp[4]), ord(tmp[5]), ord(tmp[6]), ord(tmp[7]))}
			self.dallas[i] = tmp
			self.emit("dow-ready", i)
			self.SetupTemperatureReporting(i)
			c[0] = c[0] + 1
			self.ReadDOWDeviceInformation(c[0], func)

		self.ReadDOWDeviceInformation(c[0], func)

	def SetFanPowerFailSafe(self, fan, timeout):
		self.SendCommand(25, '%c%c' % (chr(fan), chr(timeout)))

	def SetFanTachometerGlitchFilter(self,fan1, fan2, fan3, fan4):
		self.SendCommand(26, '%c%c%c%c' % (chr(fan1), chr(fan2), chr(fan3), chr(fan4)))

	def QueryFanPowerAndFailSafeMask(self, callback):
		self.SendCommand(27, '', callback)

	def ResetHost(self):
		self.SendCommand(5, '%c%c%c' % (chr(12), chr(28), chr(97)) )

	def TurnOffHost(self):
		self.SendCommand(5, '%c%c%c' % (chr(5), chr(11), chr(95)) )

	def SetupFanReporting(self, fan1=0, fan2=0, fan3=0, fan4=0):
		print "SEtup fan reporting"
		bm = 0
		if fan1:
			bm = bm ^ self.FAN1
		if fan2:
			bm = bm ^ self.FAN2
		if fan3:
			bm = bm ^ self.FAN3
		if fan4:
			bm = bm ^ self.FAN4
		self.SendCommand(16, chr(bm))

	def ReadDOWDeviceInformation(self, index, callback):
		self.SendCommand(18, chr(index), callback, priority=1)

	def SetupTemperatureReporting(self, index):
		'''Use -1 to turn off all reporting. 0 is first device.'''
		b1, b2, b3, b4 = self.temp_b1, self.temp_b2, self.temp_b3, self.temp_b4
		if index == -1:
			b1, b2, b3, b4 = 0, 0, 0, 0
		elif index < 8:
			b1 = b1 ^ (2**index)
		elif index < 16:
			b2 = b2 ^ (2**index)
		elif index < 24:
			b3 = b3 ^ (2**index)
		elif index < 32:
			b4 = b4 ^ (2**index)
		else:
			return
		tmp = '%c%c%c%c' % (chr(b1), chr(b2), chr(b3), chr(b4))
		self.SendCommand(19, tmp)
		self.temp_b1, self.temp_b2, self.temp_b3, self.temp_b4 = b1, b2, b3, b4

	
