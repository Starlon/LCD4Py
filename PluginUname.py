import os

from Constants import *
from Functions import strcasecmp, error

class PluginUname:
	def __init__(self, visitor):
		self.visitor = visitor
		visitor.AddFunction("uname", 1, self.my_uname)
	
	def my_uname(self, result, arg1):
		key = self.visitor.R2S(arg1)

		u = os.uname()

		if strcasecmp(key, "sysname") == 0:
			value = u[0]
		elif strcasecmp(key, "domainname") == 0:
			value = u[1]
		elif strcasecmp(key, "version") == 0:
			value = u[2]
		elif strcasecmp(key, "release") == 0:
			value = u[3]
		elif strcasecmp(key, "nodename") == 0:
			value = u[4]
		else:
			error("uname: unknown field '%s'" % key)
			value = ''

		self.visitor.SetResult(result, R_STRING, value)
