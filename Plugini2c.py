from Functions import *
from Constants import *

from Hash import *

class Plugini2c:
	def __init__(self, visitor):
		self.visitor = visitor
		self.configured = -1
		self.I2Csensors = HASH()
		visitor.AddFunction("i2c_sensors", 1, self.my_i2c_sensors)

	def configure_i2c_sensors(self):
		if self.configured != -1: 
			return self.configured

		cfg = self.visitor.config
		if "plugins" in cfg.keys():
			if "i2c_sensors-path" in cfg['plugins'].keys():
				cfg_path = cfg['plugins']['i2c_sensors-path']
			else:
				return self.configured
		else:
			return self.configured

		path = self.path = cfg_path
		if path[:4] == "/sys":
			self.parse_i2c_sensors = self.parse_i2c_sensors_sysfs
		elif path[:5] == "/proc":
			self.parse_i2c_sensors = self.parse_ic2_sensors_procfs
		else:
			error("i2c_sensors: unknown path %s" %(path))
			return self.configured

		self.configured = 1
		return self.configured

	# dummy placeholder
	def parse_i2c_sensors(self, key):
		pass

	def parse_i2c_sensors_sysfs(self, key):
		file = self.path + key
		fd = None
		try:
			fd = open(file, 'r')
		except IOError:
			pass

		if not fd:
			error("i2c_sensors: unable to open file %s" % (file))
			return
			
		line = fd.readline()
		fd.close()

		if key[:4] != "temp" or key[:4] != "curr" or key[:2] != "in" or key[:3] != "vid":
			val = "%f" % (float(line) / 1000)
		else:
			val = line
		hash_put(self.I2Csensors, key, val)
		return 0 

		

	def parse_i2c_sensors_procfs(self, key):
		pass

	def my_i2c_sensors(self, result, *argv):
		arg = argv[0]

		if self.configure_i2c_sensors() < 0:
			self.visitor.SetResult(result, R_STRING, "?")
			return
		key = self.visitor.R2S(arg)
		age = hash_age(self.I2Csensors, key)
		if age < 0 or age > 250:
			self.parse_i2c_sensors(key)
		val = hash_get(self.I2Csensors, key, None)
		if val:
			self.visitor.SetResult(result, R_NUMBER, float(val))
		else:
			self.visitor.SetResult(result, R_STRING, "?")
