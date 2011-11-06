#import threading

class BufferedReader:
	def __init__(self):
		self.buffer = ''
		self.current = 0
		#self.lock = threading.Lock()
		self.locked = False
		self.dumped = 0

	def peek(self, bytes=1):
		if self.current+bytes > len(self.buffer): 
			return ''
		tmp = self.buffer[self.current:bytes+self.current]
		if len(tmp) < bytes: 
			return ''
		self.current = self.current+bytes
		return tmp

	def read(self, bytes=1):
		tmp = self.buffer[:bytes]
		val = (len(self.buffer)-len(tmp))*-1
		length = len(self.buffer)
		self.buffer = self.buffer[val:]
		if length == len(self.buffer): self.buffer = ''
		self.current = 0
		return tmp

	def add_data(self, data):
		self.buffer = self.buffer + data
	
	def set_current(self, current):
		self.current = current

	def get_current(self):
		return self.current

