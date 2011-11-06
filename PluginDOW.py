from Constants import *

class RESULT:
	def __init__(self, type=0, size=0, number=0.0, string=''):
		self.type = type
		self.size = size
		self.number = number
		self.string = string

class PluginDOW:
	def __init__(self, visitor):
		self.CPUinfo = {}
		self.visitor = visitor
		visitor.AddFunction("dow", -1, self.my_dow)


	def my_dow(self, result, index=None, method=RESULT(type=R_NUMBER,number=0.0), selection=RESULT(type=R_STRING,string=''), *argv):
		if index == None or len(argv) > 0:
			error("Function dow() - Not enough or too many arguments.")
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return
		index = int(self.visitor.R2N(index))
		method = self.visitor.R2N(method)
		selection = self.visitor.R2S(selection)
		device = self.visitor.app.find_display(selection)
		dallas = False

		if index < 0 or index > 31:
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return

		if not hasattr(device, "dallas"):
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return

		if device:
			if len(device.dallas) < index:
				self.visitor.SetResult(result, R_NUMBER, 0.0)
				return
			dallas = device.dallas[index]
		elif index >= len(self.dallas):
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return

		if not dallas and not hasattr(self, "dallas"):
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return

		if not dallas and len(self.dallas) > index:
			dallas = self.visitor.dallas[index]

		if type(dallas).__name__ == 'bool':
			self.visitor.SetResult(result, R_NUMBER, 0.0)
			return

		if method == 0:
			self.visitor.SetResult(result, R_NUMBER, dallas['degc'])
		else:
			self.visitor.SetResult(result, R_NUMBER, dallas['degf'])
