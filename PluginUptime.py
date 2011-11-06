import time

from Buffer import Buffer

from Constants import *
from Functions import *

class PluginUptime:
	def __init__(self, visitor):
		self.visitor = visitor
		self.last_value = time.time()
		visitor.AddFunction('uptime', -1, self.uptime)

	def uptime(self, result, *argv):
		argc = len(argv)
		if argc > 1:
			error("uptime(): wrong number of parameters");
			self.visitor.SetResult(result, R_STRING, "")
			return

		now = time.time() + .1
		

		uptime = 0
		if now - self.last_value > .1:
			uptime = self.getuptime()
			if uptime < 0.0:
				error("parse(/proc/uptime) failed!")
				self.visitor.SetResult(result, R_STRING, "")
				return
			self.last_value = now

		if argc == 0:
			self.visitor.SetResult(result, R_NUMBER, uptime)
		else:
			self.visitor.SetResult(result, R_STRING, self.struptime(uptime, self.R2S(argv[0])))

	def getuptime(self):
		fd = open("/proc/uptime", "r")
		if not fd: return -1
		buffer = fd.read()
		fd.close()
		buffer = buffer.split(" ")
		return float(buffer[0])
		

	def struptime(self, uptime, format):
		size = 255
		src = format
		dst = Buffer(size)
		sptr = 0
		dptr = 0
		length = 0

		while length < size:
			if src[sptr] == '%':
				sptr = sptr + 1
				if re.match("[sSmMhHd]", src[sptr]):
					value = 0
					leading_zero = 0
					if src[sptr] == 's':
						value = uptime
					elif src[sptr] == 'S':
						value = uptime % 60
						leading_zero = 1
					elif src[sptr] == 'm':
						value = int(uptime / 60)
					elif src[sptr] == 'M':
						value = int(uptime / 60) % 60
						leading_zero = 1
					elif src[sptr] == 'h':
						value = int(uptime / 60 / 60)
					elif src[sptr] == 'H':
						value = int(uptime / 60 / 60) % 24
						leading_zero = 1
					elif src[sptr] == 'd':
						value = int(uptime / 60 / 60 / 24)
	
					if leading_zero and value < 10:
						length = length + 1
						dst[dptr] = '0'
						dptr = dptr + 1
	
					a = str(value)
					aptr = 0
					while length < size and aptr < len(a):
						length = length + 1
						dst[dptr] = a[aptr]
						dptr = dptr + 1
						aptr = aptr + 1

				elif src[sptr] == '%':
					length = length + 1
					dst[dptr] = '%'
					dptr = dptr + 1
				else:
					length = length + 2
					dst[dptr] = '%'
					dptr = dptr + 1
					dst[dptr] = src[sptr]
					dptr = dptr + 1
					sptr = sptr + 1
			else:
				length = length + 1
				dst[dptr] = src[sptr]
				dptr = dptr + 1
				sptr = sptr + 1
				if sptr >= len(src):
					break
						
					
			length = length + 1
		
		return dst.buffer
		
		
