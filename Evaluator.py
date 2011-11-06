import os, time

from Constants import *
from Functions import *

from PluginUptime import PluginUptime
from PluginCPUInfo import PluginCPUInfo
from PluginMemInfo import PluginMemInfo
from PluginProcStat import PluginProcStat
from PluginLoadAvg import PluginLoadAvg
from PluginNetDev import PluginNetDev
from PluginNetInfo import PluginNetInfo
from PluginPython import PluginPython
from Plugini2c import Plugini2c
from PluginUname import PluginUname
from PluginDOW import PluginDOW

T_UNDEF = 0 
T_NAME = 1 
T_NUMBER = 2 
T_STRING = 3 
T_OPERATOR = 4 
T_VARIABLE = 5 
T_FUNCTION = 6

O_UNDEF = 0
O_LST = 1
O_SET = 2
O_CND = 3
O_COL = 4
O_OR = 5
O_AND = 6
O_NEQ = 7
O_NNE = 8
O_NLT = 9
O_NLE = 10
O_NGT = 11
O_NGE = 12
O_SEQ = 13
O_SNE = 14
O_SLT = 15
O_SLE = 16
O_SGT = 17
O_SGE = 18
O_ADD = 19
O_SUB = 20
O_SGN = 21
O_CAT = 22
O_MUL = 23
O_DIV = 24
O_MOD = 25
O_POW = 26
O_NOT = 27
O_BRO = 28
O_COM = 29
O_BRC = 30 

class RESULT:
	def __init__(self, type=0, size=0, number=0.0, string=''):
		self.type = type
		self.size = size
		self.number = number
		self.string = string

class PATTERN:
	def __init__(self, pattern = '', len = 0, op = O_UNDEF):
		self.pattern = pattern
		self.len = len
		self.op = op

class VARIABLE:
	def __init__(self, name=None, value=None):
		self.name = name
		self.value = value

class FUNCTION:
	def __init__(self, name=None, argc=0, func = None):
		self.name = name
		self.argc = argc
		self.func = func

class NODE:
	def __init__(self):
		self.Token = T_UNDEF
		self.Operator = O_UNDEF
		self.Result = RESULT()
		self.Variable = VARIABLE()
		self.Function = FUNCTION()
		self.Children = 0
		self.Child = {}

Pattern1 = {}
Pattern1[0] = PATTERN(";", 1, O_LST)		# expression lists */
Pattern1[1] = PATTERN("=", 1, O_SET)		# variable assignements */
Pattern1[2] = PATTERN("?", 1, O_CND)		# conditional a?b:c */
Pattern1[3] = PATTERN(":", 1, O_COL)		# colon a?b:c */
Pattern1[4] = PATTERN("|", 1, O_OR)		 # logical OR */
Pattern1[5] = PATTERN("&", 1, O_AND)		# logical AND */
Pattern1[6] = PATTERN("<", 1, O_NLT)		# numeric less than */
Pattern1[7] = PATTERN(">", 1, O_NGT)		# numeric greater than */
Pattern1[8] = PATTERN("+", 1, O_ADD)		# addition */
Pattern1[9] = PATTERN("-", 1, O_SUB)		# subtraction or sign */
Pattern1[10] = PATTERN(".", 1, O_CAT)		# string concatenation */
Pattern1[11] = PATTERN("*", 1, O_MUL)		# multiplication */
Pattern1[12] = PATTERN("/", 1, O_DIV)		# division */
Pattern1[13] = PATTERN("%", 1, O_MOD)		# modulo */
Pattern1[14] = PATTERN("^", 1, O_POW)		# power */
Pattern1[15] = PATTERN("!", 1, O_NOT)		# logical NOT */
Pattern1[16] = PATTERN("(", 1, O_BRO)		# open brace */
Pattern1[17] = PATTERN(",", 1, O_COM)		# comma (argument seperator) */
Pattern1[18] = PATTERN(")", 1, O_BRC)		# closing brace */
Pattern1[19] = PATTERN("==", 2, O_NEQ)	   # numeric equal */
Pattern1[20] = PATTERN("!=", 2, O_NNE)	   # numeric not equal */
Pattern1[21] = PATTERN("<=", 2, O_NLE)	   # numeric less or equal */
Pattern1[22] = PATTERN(">=", 2, O_NGE)	   # numeric greater or equal */

Pattern2 = {}
Pattern2[0] = PATTERN("eq", 2, O_SEQ)	   # string equal */
Pattern2[1] = PATTERN("ne", 2, O_SNE)	   # string not equal */
Pattern2[2] = PATTERN("lt", 2, O_SLT)	   # string less than */
Pattern2[3] = PATTERN("le", 2, O_SLE)	   # string less or equal */
Pattern2[4] = PATTERN("gt", 2, O_SGT)	   # string greater than */
Pattern2[5] = PATTERN("ge", 2, O_SGE)	   # string greater or equal */

class Evaluator(object):
	def _get(self):
		tmp = ''
		for c in self._Word:
			if c == '\0': break
			tmp = tmp + c
		return tmp

	def _set(self, val):
		self._Word = [x for x in val]

	def _del(self):
		del(self._Word)
		self._Word = []

	Word = property(_get, _set, _del, "Word")

	def __init__(self):
		self.Word = []
		self.Expression = ''
		self.ExprPtr = 0
		self.Token = T_UNDEF
		self.Operator = O_UNDEF
		self.Variable = resizeList([], 255, VARIABLE)
		self.nVariable = 0
		self.Function = []
		self.nFunction = 0
		PluginUptime(self)
		PluginCPUInfo(self)
		PluginMemInfo(self)
		PluginProcStat(self)
		PluginLoadAvg(self)
		PluginNetDev(self)
		PluginNetInfo(self)
		PluginPython(self)
		Plugini2c(self)
		PluginUname(self)
		PluginDOW(self)
		
	def DelResult(self, result):
		'''
	 * void DelResult (RESULT *result)
	 *   sets a result to none
	 *   frees a probably allocated memory
		'''
		result.type = 0
		result.size = 0
		result.number = 0.0
		result.string = ''

	def FreeResult(self, result):
		if result:
			self.DelResult(result)

	def NewResult(self):
		result = RESULT()
		result.type = 0
		result.size = 0
		result.number = 0.0
		result.string = ''
		
		return result
	
	def SetResult(self, result, type, value):
		'''
	 * RESULT* SetResult (RESULT **result, int type, void *value)
	 *   initializes a result
		'''
		if result == None:
			result = self.NewResult()
		elif type ==  R_NUMBER:
			self.DelResult(result)

		if type == R_NUMBER:
			result.type = type
			result.size = 0
			try:
				result.number = float(value)
			except ValueError:
				result.number = 0.0
			except TypeError:
				result.number = 0.0
			result.string = ''

		elif type == R_STRING:
			result.size = len(value)
			result.type = type
			result.number = 0.0
			result.string = value

		else:
			error("Evaluator: internal error: invalid result type %d" % (type))

		return result

	def CopyResult(self, result, value):
		if result == None:
			result = self.NewResult()
		
		result.type = value.type
		result.number = value.number

		result.size = value.size
		result.string = value.string

		return result

		
	
	def R2N(self, result):
		'''
	 * double R2N (RESULT *result)
	 *   converts a result into a number
		'''
		if result == None:
			error("Evaluator: internal error: None result")
			return 0.0

		if result.type == 0:
			return 0.0

		if result.type & R_NUMBER:
			return result.number

		if result.type & R_STRING:
			try:
				result.number = float(result.string)
				result.type = result.type | R_NUMBER
			except ValueError:
				error("ValueError: R2N couldn't convert <%s> to a number: %s" % (result.string, self.Expression))
				result.number = 0.0
			except TypeError:
				error("TypeError: R2N couldn't convert <%s> to a number: %s" % (result.string, sefl.Expression))
				result.number = 0.0
			return result.number

		error("Evaluator: internal error: invalid result type %d" % (result.type))
		return 0.0
	
	def R2S(self, result):
		'''
	 * char* R2S (RESULT *result)
	 *   converts a result into a string
		'''
		if result == None:
			error("Evaluator: internal error: None result")
			return None

		if result.type == 0:
			return ''

		if result.type & R_STRING:
			return result.string

		if result.type & R_NUMBER:
			result.type = result.type | R_STRING
			result.size = CHUNK_SIZE
			result.string = str(result.number)
			return result.string

		error("Evaluator: internal error: invalid result type %d" % (result.type))

	def FindVariable(self, name):
		for i in range(self.nVariable):
			if name == self.Variable[i].name:
				return self.Variable[i]
		return None

	def SetVariable(self, name, value):
		V = self.FindVariable(name)
		if V != None:
			self.CopyResult(V.value, value)
			return 1

		if self.nVariable >= len(self.Variable):
			error("Evaluator: cannot set   variable <%s>: out of slots" % (name))
			return -1

		self.nVariable = self.nVariable + 1
		self.Variable[self.nVariable - 1].name = name
		self.Variable[self.nVariable - 1].value = RESULT()
		self.CopyResult(self.Variable[self.nVariable - 1].value, value)

		return 0

	def SetVariableNumeric(self, name, value):
		result = RESULT()

		self.SetResult(result, R_NUMBER, value)

		return self.SetVariable(name, result)

	def SetVariableString(self, name, value):
		result = RESULT()

		self.SetResult(result, R_STRING, value)

		return self.SetVariable(name, result)

	def DeleteVariables(self):
		self.nVariables = 0

	def FindFunction(self, name):
		for item in self.Function:
			if item.name == name:
				return item
		return None

	def AddFunction(self, name, argc, func):
		self.nFunction = self.nFunction + 1
		self.Function = resizeList(self.Function, self.nFunction, FUNCTION)
		self.Function[self.nFunction - 1].name = name
		self.Function[self.nFunction - 1].argc = argc
		self.Function[self.nFunction - 1].func = func

	def DeleteFunctions(self):
		self.nFunction = 0
	
	def Parse(self):
		if self.ExprPtr >= len(self.Expression):
			self.Word = []
			return
		self.Token = T_UNDEF;
		self.Operator = O_UNDEF

		if self.Word:
			self.Word = []

		if self.Expression == '':
			self.Word = []
			return

		# skip leading whitespaces
		while self.ExprPtr < len(self.Expression)-1 and is_space(self.Expression[self.ExprPtr]):
			self.ExprPtr = self.ExprPtr + 1

		# names
		if is_alpha(self.Expression[self.ExprPtr]):
			start = self.ExprPtr
			while self.ExprPtr < len(self.Expression) and is_alnum(self.Expression[self.ExprPtr]):
				self.ExprPtr = self.ExprPtr + 1

			if self.ExprPtr + 2 < len(self.Expression) and self.Expression[self.ExprPtr] == ':' and self.Expression[self.ExprPtr + 1] == ':' and is_alpha(self.Expression[self.ExprPtr + 2]):
				self.ExprPtr = self.ExprPtr + 3
				while self.ExprPtr < len(self.Expression) and is_alnum(self.Expression[self.ExprPtr]):
					self.ExprPtr = self.ExprPtr + 1
			self.Word = strndup2(self.Expression[start:], self.ExprPtr - start)
			self.Token = T_NAME

			i = len(Pattern2) - 1
			while i >= 0:
				if strcmp(self.Word, Pattern2[i].pattern) == 0:
					self.Token = T_OPERATOR
					self.Operator = Pattern2[i].op
					break
				i = i - 1

		# numbers
		elif is_digit(self.Expression[self.ExprPtr]) or (self.Expression[self.ExprPtr] == '.' and is_digit(self.Expression[self.ExprPtr+1])):
			start = self.ExprPtr
			reset = False
			while self.ExprPtr < len(self.Expression) and is_digit(self.Expression[self.ExprPtr]):
				self.ExprPtr = self.ExprPtr + 1

			if self.ExprPtr < len(self.Expression) and self.Expression[self.ExprPtr] == '.':
				self.ExprPtr = self.ExprPtr + 1
				while self.ExprPtr < len(self.Expression) and is_digit(self.Expression[self.ExprPtr]):
					self.ExprPtr = self.ExprPtr + 1
			self.Word = strndup2(self.Expression[start:], self.ExprPtr - start)
			self.Token = T_NUMBER

		# strings
		elif self.Expression[self.ExprPtr] == "'":
			length = 0
			size = CHUNK_SIZE
			self.Word = resizeList([], size, str)
			self.ExprPtr = self.ExprPtr + 1
			while self.ExprPtr < len(self.Expression) and self.Expression[self.ExprPtr] != "'":
				if self.Expression[self.ExprPtr] == "\\":
					ch = self.Expression[self.ExprPtr+1]
					if ch[0] == '\\' or ch[0] == "'":
						if ch[0] == '\\':
							self._Word[length] = '0'
						else:
							self._Word[length] = self.Expression[self.ExprPtr+1]
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == 'a':
						self._Word[length] = '\a'
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == 'b':
						self._Word[length] = '\b'
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == 't':
						self._Word[length] = '\t'
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == 'n':
						self._Word[length] = '\n'
						length = length + 1
					elif ch[0] == 'v':
						self._Word[length] = '\v'
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == 'f':
						self._Word[length] = '\f'
						length = length + 1
						self.ExprPtr = self.ExprPtr + 2
					elif ch[0] == '0' or ch[0] == '1' or ch[0] == '2' or ch[0] == '3':
						ch2 = ord(self.Expression[self.ExprPtr+2])
						ch3 = ord(self.Expression[self.ExprPtr+3])
						o0 = ord('0')
						o7 = ord('7')
						if ch2 >= o0 and ch2 <= o7 and ch3 >= o0 and ch3 <= o7:
							self._Word[length] = chr(int(self.Expression[self.ExprPtr+1]) * 64 + int(self.Expression[self.ExprPtr+2]) * 8 + int(self.Expression[self.ExprPtr+3]))
							length = length + 1
							self.ExprPtr = self.ExprPtr + 4
						else:
							error("Evaluator: illegal octal sequence: '\\%c%c%c' in <%s>" % (self.Expression[self.ExprPtr+1], self.Expression[self.ExprPtr+2], self.Expression[self.ExprPtr+3], self.Expression))
							self._Word[length] = self.Expression[self.ExprPtr]
							length = length + 1
							self.ExprPtr = self.ExprPtr + 1
					else:
						error("Evaluator: unknown escape sequence '\\%c' in <%s>" % (ExprPtr[ptr+1], self.Expression))
						self._Word[length] = self.Expression[self.ExprPtr]
						length = length + 1
						self.ExprPtr = self.ExprPtr + 1
				else:
					self._Word[length] = self.Expression[self.ExprPtr]
					length = length + 1
					self.ExprPtr = self.ExprPtr + 1
				if length >= size:
					tmp = size
					size = size + CHUNK_SIZE
					word = value(self.Word)
					self.Word = strndup2(word + ' ' * CHUNK_SIZE, size)
			self._Word[length] = '\0'
			self.Token = T_STRING
			if self.Expression[self.ExprPtr] == "'":
				self.ExprPtr = self.ExprPtr + 1
			else:
				error("Evaluator: unterminated string in <%s>" % ( self.Expression))
		# non-alpha operators
		else:
			i = len(Pattern1) - 1
			while i >= 0:
				length = Pattern1[i].len
				if strncmp(self.Expression[self.ExprPtr:], Pattern1[i].pattern, length) == 0:
					self.Word = strndup2(self.Expression[self.ExprPtr:], length)
					self.Token = T_OPERATOR
					self.Operator = Pattern1[i].op
					self.ExprPtr = self.ExprPtr + length
					break
				i = i - 1
		# syntax check
		if self.Token == T_UNDEF and self.ExprPtr >= len(self.Expression) - 1:
			error("Evaluator: parse error in <%s>: garbage <%s>: index: %g" % (self.Expression, self.Expression[self.ExprPtr:], self.ExprPtr))
					
				
	def NewNode(self, Child):
		N = NODE()

		N.Token = self.Token
		N.Operator = self.Operator

		if Child != None:
			N.Children = 1
			N.Child[0] = Child
		return N

	def JunkNode(self, isNum=False):
		Junk = self.NewNode(None)
		if isNum:
			Junk.Token = T_NUMBER
			self.SetResult(Junk.Result, R_NUMBER, 0.0)
		else:
			Junk.Token = T_STRING
			self.SetResult(Junk.Result, R_STRING, "")

		return Junk

	def LinkNode(self, Root, Child):
		if Child == None:
			return

		Root.Children = Root.Children + 1
		child = Root.Child
		for i in range(Root.Children-1):
			Root.Child[i] = child[i]
		if Root.Child == None:
			return
		Root.Child[Root.Children - 1] = Child

	# literal numbers, variables, functions
	def Level12(self):
		if self.Token == T_OPERATOR and self.Operator == O_BRO:
			self.Parse()
			Root = self.Level01()
			if self.Token != T_OPERATOR or self.Operator != O_BRC:
				error("Evaluator: unbalanced parentheses in <%s>" % (Expression))
				self.LinkNode(Root, self.JunkNode())
		elif self.Token == T_NUMBER:
			try:
				value = float(self.Word)
			except ValueError:
				value = 0.0
			except TypeError:
				value = 0.0
			Root = self.NewNode(None)
			self.SetResult(Root.Result, R_NUMBER, value)
		elif self.Token == T_STRING:
			Root = self.NewNode(None)
			self.SetResult(Root.Result, R_STRING, self.Word)
		elif self.Token == T_NAME:
			if self.ExprPtr < len(self.Expression) and self.Expression[self.ExprPtr] == '(':
				argc = 0
				Root = self.NewNode(None)
				Root.Token = T_FUNCTION
				Root.Result = self.NewResult()
				Root.Function = self.FindFunction(self.Word)
				if Root.Function == None:
					error("Evaluator: unknown function '%s' in <%s>" % (self.Word, self.Expression))
					Root.Token = T_STRING
					self.SetResult(Root.Result, R_STRING, "")

				self.Parse()
				first_pass = True
				while (self.Token == T_OPERATOR and self.Operator == O_COM) or first_pass:
					first_pass = False
					self.Parse()
					if self.Token == T_OPERATOR and self.Operator == O_BRC:
						break
					elif self.Token == T_OPERATOR and self.Operator == O_COM:
						error("Evaluator: empty argument in <%s>" % (self.Expression))
						self.LinkNode(Root, self.JunkNode())
					else:
						self.LinkNode(Root, self.Level01())
					argc = argc + 1
				if self.Token != T_OPERATOR and self.Operator == O_COM:
					error("Evaluator: missing closing brace in <%s>" % ( self.Expression ))

				if Root.Function != None and Root.Function.argc >= 0 and Root.Function.argc != argc:
					error("Evaluator: wrong number of arguments in <%s>" % (self.Expression))
					while argc < Root.Function.argc:
						self.LinkNode(Root, self.JunkNode())
						argc = argc + 1
			else:
				Root = self.NewNode(None)
				Root.Token = T_VARIABLE;
				Root.Result = self.NewResult()
				Root.Variable = self.FindVariable(self.Word)
				if Root.Variable == None:
					self.SetVariableString(self.Word, "")
					Root.Variable = self.FindVariable(self.Word)
		else:
			error("Evaluator: syntax error in <%s>: Word: <%s>: Index: %g" % (self.Expression, self.Word, self.ExprPtr))
			Root = self.NewNode(None)
			Root.Token = T_STRING
			self.SetResult(Root.Result, R_STRING, "")

		self.Parse()
		return Root
		
	# unary + or - signs or logical 'not'
	def Level11(self):
		sign = T_UNDEF
		if self.Token == T_OPERATOR and (self.Operator == O_ADD or self.Operator == O_SUB or self.Operator == O_NOT):
			sign = self.Operator
			if sign == O_SUB:
				sign = O_SGN
			self.Parse()

		Root = self.Level12()

		if sign == O_SGN or sign == O_NOT:
			Root = self.NewNode(Root)
			Root.Token = T_OPERATOR
			Root.Operator = sign

		return Root

	# x^y
	def Level10(self):
		Root = self.Level11()

		while self.Token == T_OPERATOR and self.Operator == O_POW:
			Root = self.NewNode(Root)
			self.Parse()
			LinkNode(Root, Level11())

		return Root

	# multiplication, division, modulo
	def Level09(self):
		Root = self.Level10()

		while self.Token == T_OPERATOR and (self.Operator == O_MUL or self.Operator == O_DIV or self.Operator == O_MOD):
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level10())

		return Root

	# addition, subtraction, string concatenation
	def Level08(self):
		Root = self.Level09()

		while self.Token == T_OPERATOR and (self.Operator == O_ADD or self.Operator == O_SUB or self.Operator == O_CAT):
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level09())

		return Root

	# relational operators
	def Level07(self):
		Root = self.Level08()

		while self.Token == T_OPERATOR and (self.Operator == O_NGT or self.Operator == O_NGE or self.Operator == O_NLT or self.Operator == O_NLE or self.Operator == O_SGT or self.Operator == O_SGE or self.Operator == O_SLT or self.Operator == O_SLE):

			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level08())
		return Root

	# equal, not equal
	def Level06(self):
		Root = self.Level07()

		while self.Token == T_OPERATOR and (self.Operator == O_NEQ or self.Operator == O_NNE or self.Operator == O_SEQ or self.Operator == O_SNE):
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, Level07())

		return Root

	# logical 'and'
	def Level05(self):
		Root = self.Level06()
		
		while self.Token == T_OPERATOR and self.Operator == O_AND:
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level06())

		return Root

	# logical 'or'
	def Level04(self):
		Root = self.Level05()

		while self.Token == T_OPERATOR and self.Operator == O_OR:
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level05())

		return Root

	# conditional expression a?b:c
	def Level03(self):
		Root = self.Level04()

		if self.Token == T_OPERATOR and self.Operator == O_CND:
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level04())
			if self.Token == T_OPERATOR and self.Operator == O_COL:
				self.Parse()
				self.LinkNode(Root, Level04())
			else:
				error("Evaluator: syntax error in <%s>: expecting ':' got '%s'" % (self.Expression, self.Word))
				self.LinkNode(Root, self.JunkNode())
		return Root

	# variable assignments
	def Level02(self):
		if self.ExprPtr+1 < len(self.Expression) and self.Token == T_NAME and (self.Expression[self.ExprPtr] == '=' and self.Expression[self.ExprPtr+1] != '='):
			name = self.Word
			V = self.FindVariable(name)
			if V == None:
				self.SetVariableString(name, "")
				V = self.FindVariable(name)
			self.Parse()
			Root = self.NewNode(None)
			Root.Variable = V
			self.Parse()
			self.LinkNode(Root, Level03())
		else:
			Root = self.Level03()

		return Root
		
			
	# expression lists
	def Level01(self):
		Root = self.Level02()

		while self.Token == T_OPERATOR and self.Operator == O_LST:
			Root = self.NewNode(Root)
			self.Parse()
			self.LinkNode(Root, self.Level02())

		return Root

	def EvalTree(self, Root):
		type = -1
		number = 0.0
		freeme = 0
		

		if Root.Token == T_NUMBER or Root.Token == T_STRING:
			return 0

		elif Root.Token == T_VARIABLE:
			self.CopyResult(Root.Result, Root.Variable.value)
			return 0

		elif Root.Token == T_FUNCTION:
			argc = Root.Children
			param = resizeList([], argc, RESULT)
			for i in range(argc):
				self.EvalTree(Root.Child[i])
				param[i] = Root.Child[i].Result

			self.DelResult(Root.Result)
			Root.Function.func(Root.Result, *param)
			return 0

		elif Root.Token == T_OPERATOR:
			if Root.Operator == O_LST: # expression list: result is last expression
				for i in range(Root.Children):
					self.EvalTree(Root.Child[i])
				type = Root.Child[Root.Children-1].Result.type
				number = Root.Child[Root.Children-1].Result.number
				string = Root.Child[Root.Children-1].Result.string

			elif Root.Operator == O_SET: # variable assignment
				self.EvalTree(Root.Child[0])
				self.CopyResult(Root.Variable.value, Root.Child[0].Result)
				type = Root.Child[0].Result.type
				number = Root.Child[0].Result.number
				string = Root.Child[0].Result.string

			elif Root.Operator == O_CND: # conditional expression
				self.EvalTree(Root.Child[0])
				i = 1 + (self.R2N(Root.Child[0].Result) == 0.0)
				self.EvalTree(Root.Child[i])
				type = Root.Child[i].Result.type
				number = Root.Child[i].Result.number
				string = Root.Child[i].Result.string

			elif Root.Operator == O_OR: #logical OR
				type = R_NUMBER
				self.EvalTree(Root.Child[1])
				if R2n(Root.Child[1].Result) == 0.0:
					self.EvalTree(Root.Child[1])
					number = self.R2N(Root.Child[1].Result) != 0.0
				else:
					number = 1.0

			elif Root.Operator == O_AND: # logical AND
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				if self.R2N(Root.Child[0].Result) == 0.0:
					self.EvalTree(Root.Child[1])
					number = self.R2N(Root.Child[1].Result) != 0.0
				else:
					number = 0.0

			elif Root.Operator == O_NEQ: # numeric equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) == self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_NNE: # numeric not equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) != self.R2N(Root.Child[1].Result)
			
			elif Root.Operator == O_NLT: # numeric less than
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) < self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_NLE: # numeric less equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) <= self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_NGT: # numeric greater than
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) > self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_NGE: # numeric greater equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) >= self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_SEQ: # string equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) == 0

			elif Root.Operator == O_SNE: # string not equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) != 0

			elif Root.Operator == O_SLT: # string less than
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) < 0

			elif Root.Operator == O_SLE: # string less equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) <= 0

			elif Root.Operator == O_SGT: # string greater than
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) > 0

			elif Root.Operator == O_SGE: # string greater equal
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = strcmp(self.R2S(Root.Child[0].Result), self.R2S(Root.Child[1].Result)) >= 0

			elif Root.Operator == O_ADD: # addition
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) + self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_SUB: # subtraction
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) - self.R2N(Root.Child[1].Result)

			elif Root.Operator == O_SGN: # sign
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				number = -self.R2N(Root.Child[0].Result)

			elif Root.Operator == O_CAT: # string concatenation
				type = R_STRING
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				s1 = self.R2S(Root.Child[0].Result)
				s2 = self.R2S(Root.Child[1].Result)
				string = s1 + s2

			elif Root.Operator == O_MUL: # multiplication
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) * self.R2N(Root.Child[1].Result)
				number = "%.2f" % number
				number = float(number)

			elif Root.Operator == O_DIV: # division
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = self.R2N(Root.Child[0].Result) / self.R2N(Root.Child[1].Result)
				number = "%.2f" % number
				number = float(number)

			
			elif Root.Operator == O_MOD: # modulus
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				dummy = self.R2N(Root.Child[1].Result)
				if dummy == 0:
					error("Evaluator: warning division by zero")
					number = 0.0
				else:
					number = self.R2N(Root.Child[0].Result) % self.R2N(Root.Child[1].Result)
			
			elif Root.Operator == O_POW: # x^y
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				self.EvalTree(Root.Child[1])
				number = pow(self.R2N(Root.Child[0].Result), self.R2N(Root.Child[1].Result))

			elif Root.Operator == O_NOT:
				type = R_NUMBER
				self.EvalTree(Root.Child[0])
				number = self.R2N(Root.Child[0].Result) == 0.0

			else:
				error("Evaluator: internal error: unhandled operator <%d>" % ( Root.Operator))
				self.SetResult(Root.Result, R_STRING, "")
				return -1

			if type == R_NUMBER:
				self.SetResult(Root.Result, R_NUMBER, number)
				return 0
			elif type == R_STRING:
				self.SetResult(Root.Result, R_STRING, string)
				return 0
			error("Evaluator: internal error: unhandled type <%d>" % (type))
			return -1
		else:
			error("Evaluator: internal error: unhandled token <%d>" % (Root.Token.value))
			return -1
		return 0
			
	def Compile(self, expression):
		'''
	 * int Compile (char* expression, void **tree)
	 *   compiles a expression into a tree
		'''
		if expression == '': return self.JunkNode()
		if expression is None: return self.JunkNode(True)

		self.Expression = expression
		self.ExprPtr = 0

		self.Parse()

		if self._Word and self.Word[0] == '\0':
			self.Word = []
			return -1

		Root = self.Level01()

		if len(self.Word) > 0 and self.Word[0] != '\0':
			error("Evaluator: syntax error in <%s>: garbage <%s>: index: %g" %(self.Expression, self.Word, self.ExprPtr))
			self.Word = []
			return -1

		return Root
	
	def Eval(self, tree, result):
		'''
	 * int Eval (void *tree, RESULT *result)
	 *   evaluates an expression
		'''
		Tree = tree

		self.DelResult(result)

		if Tree == None:
			self.SetResult(result, R_STRING, "")
			return 0

		ret = self.EvalTree(Tree)

		result.type = Tree.Result.type
		result.size = Tree.Result.size
		result.number = Tree.Result.number
		if result.size > 0:
			if Tree.Result.string != '':
				result.string = Tree.Result.string
			else:
				result.string = ''
		else:
			result.string = ''

		return ret
			
	def DelTree(self, tree):
		'''
	 * void DelTree (void *tree)
	 *   frees a compiled tree
		'''
		Tree = tree

		if Tree == None:
			return

		for i in range(Tree.Children):
			self.DelTree(Tree.Child[i])

		if Tree.Result:
			self.FreeResult(Tree.Result)
		
def start():
	evaluator = Evaluator()
	
	expression = "proc_stat('cpu.user', 500)"
	expression = "loadavg(1)"
	expression = "netdev('wlan0', 'Rx_bytes', 500)"
	expression = "netinfo::exists('wlan0')"
	#expression = "netinfo::hwaddr('wlan0')"
	#expression = "netinfo::ipaddr('wlan0')"
	#expression = "netinfo::netmask('wlan0')"
	#expression = "netinfo::bcaddr('wlan0')"
	#expression = "uptime('test')"
	#expression = "python::exec('tmp', 'my_func2')"
	expression = "i2c_sensors('temp1_input')"
	expression = "meminfo('Active')/1024 . ' Active'"
	expression = "proc_stat::cpu('idle', 500)"
	expression = "uname('sysname').' '.uname('nodename').' '.uname('release').' '.uname('machine').' '.cpuinfo('model name')"

	expression="(netdev('wlan0', 'Rx_bytes', 500) + netdev('wlan0', 'Tx_bytes', 500)) /1024"
	expression="proc_stat::cpu('system', 0)"
	expression="'\\200'"
	expression="meminfo('Active')/1024"
	expression="(meminfo('MemTotal')/1024) . 'MB'"
	expression="(netdev('wlan0', 'Rx_bytes', 500) + netdev('wlan0', 'Tx_bytes', 500)) /1024"
	expression="300"
	evaluator.SetVariableString("test", "Foo")
	def func(result, *arg1):
		#print result, arg1
		evaluator.SetResult(result, R_NUMBER, 1.0)

	evaluator.AddFunction('foo2', -1, func)

	tree = evaluator.Compile(expression)
	while tree != -1:
		result = RESULT(0, 0, 0, '')
		evaluator.Eval(tree, result)
		if result.type == R_NUMBER:
			if debug: print "Number: %g, Expression: %s" % (evaluator.R2N(result), expression)
		elif result.type == R_STRING:
			#print "String: '%s', Expression: %s" % (result.string, expression), [result.string]
		elif result.type == (R_NUMBER | R_STRING):
			#print "String: '%s' Number: (%g), Expression: %s" % (evaluator.R2S(result), evaluator.R2N(result), expression)
		else:
			#print "internal error: unknown result type %d, Expression: %s" % (result.type, expression)
		time.sleep(.5)

if __name__ == "__main__":
	start()
