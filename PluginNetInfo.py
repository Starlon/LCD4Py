import socket
import fcntl
import struct
import array

#iface = "wlan0"
#fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#tmp = fcntl.ioctl(self.fd, 35099, struct.pack('256s', iface))[20:24]

#print socket.inet_ntop(socket.AF_INET, tmp)

from Functions import *
from Constants import *

MAX_INET = 128

SIOCGIFNETMASK = 0x891b
SIOCGIFBRDADDR = 0x8919
SIOCGIFADDR = 0x8915
SIOCGIFHWADDR = 0x8927
SIOCGIFCONF = 0x8912

class PluginNetInfo:
	def __init__(self, visitor):
		self.visitor = visitor
		self.fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		visitor.AddFunction("netinfo::exists", 1, self.my_exists)
		visitor.AddFunction("netinfo::hwaddr", 1, self.my_hwaddr)
		visitor.AddFunction("netinfo::ipaddr", 1, self.my_ipaddr)
		visitor.AddFunction("netinfo::netmask", 1, self.my_netmask)
		visitor.AddFunction("netinfo::bcaddr", 1, self.my_bcaddr)
		
	def my_exists(self, result, *argv):
		iface = self.visitor.R2S(argv[0])
		bytes = MAX_INET * 32
		names = array.array("B", '\0' * bytes)
		ioctl = fcntl.ioctl(self.fd, SIOCGIFCONF, struct.pack('iL', bytes, names.buffer_info()[0]))
		if not ioctl:
			error("plugin_netinfo: ioctl(IFCONF %s) failed" % (iface))
			self.visitor.SetResult(result, R_NUMBER, 0)
			return
		outbytes = struct.unpack('iL', ioctl)[0]
		namestr = names.tostring()
		if iface in [namestr[i:i+32].split('\0', 1)[0] for i in range(0, outbytes, 32)]:
			val = 1.0
		else:
			val = 0.0
		self.visitor.SetResult(result, R_NUMBER, val)

	def my_hwaddr(self, result, *argv):
		iface = self.visitor.R2S(argv[0])
		ioctl = fcntl.ioctl(self.fd, SIOCGIFHWADDR, struct.pack('256s', iface))
		if not ioctl:
			error("plugin_netinfo: ioctl(IFHWADDR %s) failed" % (iface))
			self.visitor.SetResult(result, R_STRING, "")
			return
		ioctl = ioctl[20:24]
		self.visitor.SetResult(result, R_STRING, socket.inet_ntop(socket.AF_INET, ioctl))

	def my_ipaddr(self, result, *argv):
		iface = self.visitor.R2S(argv[0])
		ioctl = fcntl.ioctl(self.fd, SIOCGIFADDR, struct.pack('256s', iface))
		if not ioctl:
			error("plugin_netinfo: ioctl(IFADDR %s) failed" % (iface))
			self.visitor.SetResult(result, R_STRING, "")
			return
		ioctl = ioctl[20:24]
		self.visitor.SetResult(result, R_STRING, socket.inet_ntop(socket.AF_INET, ioctl))

	def my_netmask(self, result, *argv):
		iface = self.visitor.R2S(argv[0])
		ioctl = fcntl.ioctl(self.fd, SIOCGIFNETMASK, struct.pack('256s', iface))
		if not ioctl:
			error("plugin_netinfo: ioctl(IFNETMASK %s) failed" % (iface))
			self.visitor.SetResult(result, R_STRING, "")
			return
			
		ioctl = ioctl[20:24]
		self.visitor.SetResult(result, R_STRING, socket.inet_ntop(socket.AF_INET, ioctl))

	def my_bcaddr(self, result, *argv):
		iface = self.visitor.R2S(argv[0])
		ioctl = fcntl.ioctl(self.fd, SIOCGIFBRDADDR, struct.pack('256s', iface))
		if not ioctl:
			error("plugin_netinfo: ioctl(IFBRDADDR %s) failed" % (iface))
			self.visitor.SetResult(result, R_STRING, "")
			return
		ioctl = ioctl[20:24]
		self.visitor.SetResult(result, R_STRING, socket.inet_ntop(socket.AF_INET, ioctl))
