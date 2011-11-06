
from Constants import *

class PluginCPUInfo:
	def __init__(self, visitor):
		self.CPUinfo = {}
		self.visitor = visitor
		visitor.AddFunction("cpuinfo", 1, self.cpuinfo)

	def parse_cpuinfo(self):
		fd = open("/proc/cpuinfo", "r")
		if not fd: return -1
		line = fd.readline()
		while line:
			if line.strip() != '':
				line = line[:-2].replace('\t', ' ').split(":")
				key = line[0].strip()
				if len(line) < 2:
					value = ''
				else:
					value = line[1].strip()
				self.CPUinfo[key] = value
			line = fd.readline()
		fd.close()
		return 0

	def cpuinfo(self, result, *argv):
		if len(argv) < 1:
			self.visitor.SetResult(result, R_STRING, "")
			return
		
		if self.parse_cpuinfo() < 0:
			self.visitor.SetResult(result, R_STRING, "")
			return

		k = self.visitor.R2S(argv[0])
		if k in self.CPUinfo.keys():
			val = self.CPUinfo[k]
		else:
			val = ''

		self.visitor.SetResult(result, R_STRING, val)

