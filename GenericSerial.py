import serial

class GenericSerial:
	
	def __init__ ( self, visitor, obj=None, config=None ):
		"""___init___ () - Inits the driver
		"""
		self.visitor = visitor
		if obj == None:
			self.port = ''
			self.baud = 115200
			self.ser = None
		else:
			self.port = obj.port
			self.baud = obj.baud
			self.ser = obj.ser

	def Connect ( self, port = None, baud = None, timeout = 0 ):
		"""Connect ( com, baud = 115200, timeout = 1)
			Attempt to connect to the Display.
		com - Com Port to attach to (i.e. COM 12)
		baud - 115200 is default, 19200 is allowed
		"""
		if port != None: 
			self.port = port
		if baud != None:
			self.baud = baud
		if self.Connected(): self.Disconnect()
		self.ser = serial.Serial(self.port, self.baud, timeout = timeout, writeTimeout = timeout) # Connect
		if self.ser.isOpen():
			self.active = True
			self.emit('display-connected')
			return True
		return False

	def Connected(self):
		if self.ser: return self.ser.isOpen()
		return False

	def Disconnect (self):
		""" Disconnect () - Disconnects from the display """
		self.active = False
		if not self.ser: return
		self.emit('display-disconnected-before')
		self.ser.flushInput()
		self.ser.flushOutput()
		self.ser.close()
		self.ser = None
		self.emit('display-disconnected')

	def ReadChar(self):
		''' Note that this returns a character as an integer value. Use ReadData(1) for a char. '''
		if not self.ser or not self.ser.isOpen(): 
			return ''
		data = -1
		try: data = self.ser.read(1)
		except OSError:
			pass
		if data != -1 and data != '':
			data = ord(data)
		return data

	def ReadData(self, len):
		if not self.ser or not self.ser.isOpen(): 
			return ''
		data = ''
		try:
			data = self.ser.read(len)
		except OSError:
			pass
		return data
		
