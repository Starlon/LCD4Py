from Constants import *
from Functions import *
from Evaluator import RESULT, NODE

class Property:
	def __init__(self, visitor, section, name, defval=None):
		self.visitor = visitor
		self.name = name
		self.is_valid = 0
		self.compiled = None
		self.result = RESULT()
		self.expression = visitor.cfg_fetch_raw(section, name, defval)
		if self.expression != None:
			self.is_valid = 1
			self.compiled = visitor.Compile(self.expression)


	def valid(self):
		return self.is_valid

	def eval(self):
		old = RESULT()

		old.type = self.result.type
		old.number = self.result.number
		old.string = self.result.string

		self.visitor.DelResult(self.result)

		self.visitor.Eval(self.compiled, self.result)

		update = 1
		if self.result.type & R_NUMBER and old.type & R_NUMBER and self.result.number == old.number:
			update = 0
		if self.result.type & R_STRING and old.type & R_STRING:
			if self.result.string == '' and old.string == '':
				update = 0
			elif self.result.string != '' and old.string != '' and strcmp(self.result.string, old.string) == 0:
				update = 0

		return update

	def P2N(self):
		return self.visitor.R2N(self.result)

	def P2S(self):
		return self.visitor.R2S(self.result)
