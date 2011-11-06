from Evaluator import RESULT
from configobj import ConfigObj

from Functions import error

class CFG:
	def __init__(self, config=None):
		if config is None:
			self.config = ConfigObj("config.ini")
		else:
			self.config = config
		self.config.interpolation = "Template"
		self.cfg_fetch_number = self.cfg_fetch_num

	def cfg_fetch_raw(self, section, key, defval=None):
		if not section: return
		if type(defval).__name__ == "int" or type(defval).__name__ == "float":
			defval = str(defval)
		keys = dict([(entry.lower(), entry) for entry in section.keys()])
		if key.lower() in keys.keys():
			real_key = keys[key.lower()]
			return section[real_key]
		return defval

	def cfg_fetch(self, section, key, defval=None):
		val = self.cfg_fetch_raw(section, key, defval)
		tree = self.Compile(val)
		if tree != -1:
			result = RESULT()
			self.Eval(tree, result)
			if type(defval).__name__ == "str":
				return self.R2S(result)
			else:
				return self.R2N(result)
		return defval
	
	def cfg_fetch_num(self, section, key, defval=None):
		if not section: return
		val = self.cfg_fetch(section, key, defval)
		try:
			val = int(val)
		except ValueError:
			error("Configuration error: expected number under section <%s>: %s" % (key, val))
			val = defval
		return val
	
	def cfg_fetch_float(self, section, key, defval=None):
		if not section: return
		val = self.cfg_fetch(section, key, defval)
		try:
			val = float(val)
		except ValueError:
			val = defval
		return val

