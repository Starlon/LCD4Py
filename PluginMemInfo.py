from Constants import *

class PluginMemInfo:
	def __init__(self, visitor):
		self.visitor = visitor
		self.MemInfo = {}
		visitor.AddFunction("meminfo", 1, self.meminfo)

	
	def parse_meminfo(self):
		fd = open("/proc/meminfo", "r")
		if not fd: return -1
		line = fd.readline().strip()
		while line:
			if line != '':
				l = len(line)
				if line[l-1] == 'B' and line[l-2] == 'k' and line[l-3] == ' ':
					line = line[:-3].strip().split(":")
					key = line[0].strip()
					if len(line) < 2:
						value = ''
					else:
						value = line[1].strip()
					self.MemInfo[key] = value
			line = fd.readline().strip()
		fd.close()
		return 0

	def meminfo(self, result, *argv):
		
		if self.parse_meminfo() < 0:
			self.visitor.SetResult(result, R_STRING, "")
			return

		key = self.visitor.R2S(argv[0])
		if key in self.MemInfo.keys():
			val = self.MemInfo[key]
		else:
			val = 0.0

		self.visitor.SetResult(result, R_NUMBER, val)
