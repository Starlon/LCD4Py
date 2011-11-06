
from Functions import *
from Constants import *

class PluginPython:
	def __init__(self, visitor):
		self.visitor = visitor
		visitor.AddFunction("python::exec", -1, self.my_exec)

	def my_exec(self, result, *argv):
		if len(argv) < 2:
			error("python::exec: Not enough arguments.")
			self.visitor.SetResult(result, R_STRING, "")
			return
		mod = self.visitor.R2S(argv[0])
		func = self.visitor.R2S(argv[1])
		if len(argv) > 2:
			args = argv[2:]	
		else:
			args = []

		# Import the module
		try:
			module = __import__(mod)
		except ImportError, e:
			error("python::exec(%s, %s): %s" % (mod, func, e))
			self.visitor.SetResult(result, R_STRING, "")
			return

		# Does the function exist?
		if func not in module.__dict__.keys():
			error("python::exec(%s, %s): Module does not contain function." % (mod, func))
			self.visitor.SetResult(result, R_STRING, "")
			return

		# Call function and handle return
		ret = module.__dict__[func](*args)
		if type(ret).__name__ == 'float' or type(ret).__name__ == 'int':
			self.visitor.SetResult(result, R_NUMBER, ret)
		elif type(ret).__name__ == 'str':
			self.visitor.SetResult(result, R_STRING, ret)
		elif type(ret).__name__ == 'NoneType':
			self.visitor.SetResult(result, R_STRING, "")
		else:
			error("python::exec(%s, %s) Invalid return type." % (mod, func))
			self.visitor.SetResult(result, R_STRING, "")

		
		
		
