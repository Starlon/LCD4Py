from Hash import *

class PluginNetDev:
	def __init__(self, visitor):
		self.visitor = visitor
		self.NetDev = HASH()
		visitor.AddFunction("netdev", 3, self.my_netdev)
		visitor.AddFunction("netdev::fast", 3, self.my_netdev_fast)

	def parse_netdev(self):
		fd = open("/proc/net/dev", "r")
		if not fd: 
			error("open(/proc/net/dev) failed")
			return -1

		fd.readline()
		line = fd.readline()
		RxTx = line.rfind("|")
		while line:
			halves = line.split(":")
			if len(halves) < 2:
				RxTx = halves[0].split("|")
				RxTx.pop(0)
				RxTx[0] = RxTx[0].split(" ")
				RxTx[1] = RxTx[1].strip().split(" ")
				for j in range(2):
					i = len(RxTx[j]) - 1
					while i >= 0:
						if RxTx[j][i] == '':
							RxTx[j].pop(i)
						i = i - 1
				
				col = 0
				for j in range(2):
					i = 0
					for key in RxTx[j]:
						key = "%s_%s" %(("Rx", "Tx")[j == 0], key)
						hash_set_column(self.NetDev, col, key)
						col = col + 1
			else:
				dev = halves[0]
				buffer = halves[1]
				hash_put_delta(self.NetDev, dev, buffer)
			
			line = fd.readline().strip()
		fd.close()
		return 0

	def my_netdev(self, result, *argv):
		if self.parse_netdev() < 0:
			self.visitor.SetResult(result, R_STRING, "")
			return

		dev = self.visitor.R2S(argv[0])
		key = self.visitor.R2S(argv[1])
		delay = self.visitor.R2N(argv[2])

		value = hash_get_regex(self.NetDev, dev, key, delay)

		self.visitor.SetResult(result, R_NUMBER, value)



	def my_netdev_fast(self, result, *argv):
		if self.parse_netdev() < 0:
			self.SetResult(result, R_STRING, "")
			return

		dev = self.visitor.R2S(argv[0])
		key = self.visitor.R2S(argv[1])
		delay = self.visitor.R2N(argv[2])

		value = hash_get_delta(self.NetDev, dev, key, delay)

		self.visitor.SetResult(result, R_NUMBER, value)

