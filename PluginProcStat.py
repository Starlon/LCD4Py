from ctypes import *
import ctypes.util
libc = cdll.LoadLibrary("libc.so.6")

import time

from Constants import *
from Functions import *

from Hash import *

class PluginProcStat:
	def __init__(self, visitor):
		self.visitor = visitor
		self.ProcStat = HASH()
		visitor.AddFunction("proc_stat", -1, self.proc_stat)
		visitor.AddFunction("proc_stat::cpu", 2, self.proc_stat_cpu)
		visitor.AddFunction("proc_stat::disk", 3, self.proc_stat_disk)

	def hash_put1(self, key, val):
		hash_put_delta(self.ProcStat, key, val)

	def hash_put2(self, key1, key2, val):
		key = "%s.%s" % (key1, key2)
		self.hash_put1(key, val)

	def hash_put3(self, key1, key2, key3, val):
		key = "%s.%s.%s" % (key1, key2, key3)
		self.hash_put1(key, val)
		
	def parse_proc_stat(self):

		age = hash_age(self.ProcStat, None)
		if age > 0 and age < 10:
			return 0

		fd = open("/proc/stat", "r")

		if not fd: return -1

		line = fd.readline()
		while line:
			if strncmp(line, "cpu", 3) == 0:
				key = ['user', 'nice', 'system', 'idle', 'iow', 'irq', 'sirq']
				line = line.split(" ")
				i = len(key) - 1
				diff = 0
				while i >= 0:
					if line[i] == '':
						line.pop(i)
					i = i - 1

				i = 0
				while i < len(key):
					self.hash_put2(line[0], key[i], line[i+1])
					i = i + 1
				
			line = fd.readline()
		fd.close()
		return 0

	def proc_stat(self, result, *argv):

		if self.parse_proc_stat() < 0:
			self.visitor.SetResult(result, R_STRING, "")
			return

		if len(argv) == 1:
			string = hash_get(self.ProcStat, self.R2S(argv[0]), None)
			if string == None:
				string = ''
			self.visitor.SetResult(result, R_STRING, string)
		elif len(argv) == 2:
			number = hash_get_delta(self.ProcStat, self.R2S(argv[0]), None, self.R2N(argv[1]))
			self.visitor.SetResult(result, R_NUMBER, number)
		else:
			error("Wrong number of arguments for proc_stat")
			

	def proc_stat_cpu(self, result, arg1, arg2):
		if self.parse_proc_stat() < 0 :
			self.visitor.SetResult(result, R_STRING, "")
			return
		key = self.visitor.R2S(arg1)
		delay = self.visitor.R2N(arg2)

		cpu_user = hash_get_delta(self.ProcStat, "cpu.user", None, delay)
		cpu_nice = hash_get_delta(self.ProcStat, "cpu.nice", None, delay)
		cpu_system = hash_get_delta(self.ProcStat, "cpu.system", None, delay)
		cpu_idle = hash_get_delta(self.ProcStat, "cpu.idle", None, delay)
		cpu_iow = hash_get_delta(self.ProcStat, "cpu.iow", None, delay)
		cpu_irq = hash_get_delta(self.ProcStat, "cpu.irq", None, delay)
		cpu_sirq = hash_get_delta(self.ProcStat, "cpu.sirq", None, delay)
		
		cpu_total = cpu_user + cpu_nice + cpu_system + cpu_idle + cpu_iow + cpu_irq + cpu_sirq

		if key == 'user':
			value = cpu_user
		elif key == 'nice':
			value = cpu_nice
		elif key == 'system':
			value = cpu_system
		elif key == 'idle':
			value = cpu_idle
		elif key == 'iowait':
			value = cpu_iowait
		elif key == 'irq':
			value = cpu_irq
		elif key == 'softirq':
			value = cpu_sirq
		elif key == 'busy':
			value = cpu_total - cpu_idle

		if cpu_total > 0.0:
			value = 100 * value / cpu_total
		else:
			value = 0.0

		self.visitor.SetResult(result, R_NUMBER, value)

		value = hash_get_delta(self.ProcStat, key, None, delay)
		

	def proc_stat_disk(self, result, *argv):
		pass
