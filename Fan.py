
class Fan(object):
	def __init__(self):
		self.active = False
		self.rpm = 0
		self.ppr = 3
		self.glitch = None
		self.power = None

	def __getitem__(self, key):
		if key == 'rpm':
			return self.rpm
		elif key == 'num':
			return self.num
		elif key == 'ppr':
			return self.ppr
		elif key == 'power':
			return self.power
		elif key == 'glitch':
			return self.glitch
		elif key == 'active':
			return self.active
		else:
			raise KeyError, key

	def __setitem__(self, key, val):
		if key == 'rpm':
			self.rpm = val
		elif key == 'num':
			self.num = val
		elif key == 'ppr':
			self.ppr = val
		elif key == 'power':
			self.power = val
		elif key == 'glitch':
			self.glitch = val
		elif key == 'active':
			self.active = val
		else:
			raise KeyError, key


