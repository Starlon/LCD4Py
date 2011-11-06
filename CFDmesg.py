import subprocess
import re

class CFDmesg:
	hints = None
	hints_index = []

	def __init__(self):
		self.get_dmesg()	
	#def sensors_show(self):
	#	self.set_current_window('sensors')
	#	self._('window_sensors_view').show()
	def get_dmesg(self):
		p = subprocess.Popen("/bin/dmesg", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		buffer, error = p.communicate()
		if error != '':
			print "Error reading dmesg", error
		buffer_lines = self.split_lines(buffer)
		self.hints = self.parse_dmesg_lines(buffer_lines)

	def parse_dmesg_lines(self, lines):
		hints = {}
		c = 0
				
		while c < len(lines):
			m = re.match("usb (.*): New USB device found, idVendor=0403, idProduct=(.*)", lines[c])
			if m: 
				id = m.group(1)
				if id not in hints.keys():
					hints[id] = {'product_id':m.group(2), 'serial_number':'', 'serial_device':'', 'indexed':None}
				else:
					hints[id]['product_id'] = m.group(2)

			m = re.match("usb (.*):.*SerialNumber: (.*)", lines[c])
			if m:
				id = m.group(1)
				if id not in hints.keys():
					hints[id] = {'product_id':None, 'serial_number':m.group(2), 'serial_device':None, 'indexed':None}
				else:
					hints[id]['serial_number'] = m.group(2)

			m = re.match("usb (.*):.*now attached to (.*)", lines[c])
			if m:
				id = m.group(1)
				if id not in hints.keys():
					hints[id] = {'product_id':None, 'serial_number':None, 'serial_device':m.group(2), 'indexed':None}
				else:
					hints[id]['serial_device'] = m.group(2)

			for k in hints.keys():
				if hints[k]['product_id'] and hints[k]['serial_number'] and hints[k]['serial_device'] and hints[k]['indexed'] == None:
					self.hints_index.append(k)
					hints[k]['indexed'] = len(self.hints_index) - 1
				

			c = c + 1	
		self.hints = hints


