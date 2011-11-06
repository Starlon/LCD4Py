import time

from Constants import *
from Functions import *

class PluginLoadAvg:
	def __init__(self, visitor):
		self.visitor = visitor
		self.last_value = 0
		self.nelem = -1
		self.loadavg = [0, 0, 0]
		visitor.AddFunction("loadavg", 1, self.my_loadavg)

	def getloadavg(self, nelem):
		fd = open("/proc/loadavg", "r")
		if not fd: return -1

		buf = fd.readline()
		fd.close()

		if not buf: return -1

		buf = buf.split(' ')
		
		i = len(buf) - 1
		while i >= 0:
			buf[i] = buf[i].strip()
			if buf[i] == '': buf.pop(i)
			i = i - 1

		i = 0
		while i < nelem:
			self.loadavg[i] = buf[i]
			i = i + 1
		return i
		
	def my_loadavg(self, result, *argv):
		now = time.time()
		age = now - self.last_value
		if self.nelem == -1 or age == 0 or age > 10:
			self.nelem = self.getloadavg(3)
			if self.nelem < 0:
				error("getloadavg() failed!")
				self.visitor.SetResult(result, R_STRING, "")
				return
			self.last_value = now

		index = int(self.visitor.R2N(argv[0]))
		if index < 1 or index > self.nelem:
			error("loadavg(%d): index out of range!" %( index))
			return

		self.visitor.SetResult(result, R_NUMBER, self.loadavg[index - 1])

