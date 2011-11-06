from ctypes import *

LIBUSB_ENDPOINT_IN = 0x80
LIBUSB_ENDPOINT_OUT = 0x00

class EnumerationType(type(c_uint)):  
	def __new__(metacls, name, bases, dict):  
		if not "_members_" in dict:  
			_members_ = {}  
			for key,value in dict.items():  
				if not key.startswith("_"):  
					_members_[key] = value  
			dict["_members_"] = _members_  
		cls = type(c_uint).__new__(metacls, name, bases, dict)  
		for key,value in cls._members_.items():  
			globals()[key] = value  
		return cls  

	def __contains__(self, value):
		return value in self._members_.values()

	def __repr__(self):
		return "<Enumeration %s>" % self.__name__

class Enumeration(c_uint):
	__metaclass__ = EnumerationType
	_members_ = {}
	def __init__(self, value):
		for k,v in self._members_.items():
			if v == value:
				self.name = k
				break
		else:
			raise ValueError("No enumeration member with value %r" % value)
		c_uint.__init__(self, value)


	@classmethod
	def from_param(cls, param):
		if isinstance(param, Enumeration):
			if param.__class__ != cls:
				raise ValueError("Cannot mix enumeration members")
			else:
				return param
		else:
			return cls(param)

	def __repr__(self):
		return "<member %s=%d of %r>" % (self.name, self.value, self.__class__)

class OPENUSB_INIT_FLAG(Enumeration):
	_members_ = {'USB_INIT_DEFAULT':0,
		'USB_INIT_FAIL_FAST':1,
		'USB_INIT_REVERSIBLE':2,
		'USB_INIT_NON_REVERSIBLE':3}

class OPENUSB_TRANSFER_TYPE(Enumeration):
	_members_ = {'USB_TYPE_ALL':0,
		'USB_TYPE_CONTROL':1,
		'USB_TYPE_INTERRUPT':2,
		'USB_TYPE_BULK':3,
		'USB_TYPE_ISOCHRONOUS':4,
		'USB_TYPE_LAST':5}

OPENUSB_SUCCESS = 0

class OPENUSB_DEVID(c_uint64):
	pass

class OPENUSB_BUSID(c_uint64):
	pass

class OPENUSB_HANDLE(c_uint64):
	pass

class OPENUSB_DEV_HANDLE(c_uint64):
	pass

class USB_DEVICE_DESC(Structure):
	_fields_ = [('bLength', c_uint8),
		('bDescriptorType', c_uint8),
		('bcdUSB', c_uint16),
		('bDeviceClass', c_uint8),
		('bDeviceSubClass', c_uint8),
		('bDeviceProtocol', c_uint8),
		('bMaxPacketSize0', c_uint8),
		('idVendor', c_uint16),
		('idProduct', c_uint16),
		('bcdDevice', c_uint16),
		('iManufacturer', c_uint8),
		('iProduct', c_uint8),
		('iSerialNumber', c_uint8),
		('bNumConfigurations', c_uint8)]

class USB_CONFIG_DESC(Structure):
	_fields_ = [('bLength', c_uint8),
		('bDescriptorType', c_uint8),
		('wTotalLength', c_uint16),
		('bNumInterfaces', c_uint8),
		('bConfigurationValue', c_uint8),
		('iConfiguration', c_uint8),
		('bmAttributes', c_uint8),
		('bMaxPower', c_uint8)]

class USB_STRING_DESC(Structure):
	_fields_ = [('bLength', c_uint8),
		('bDescriptorType', c_uint8),
		('bString', POINTER(c_uint16))]

class OPENUSB_DEV_DATA(Structure):
	_fields_ = [("busid", OPENUSB_BUSID),
		('devid', OPENUSB_DEVID),
		('bus_address', c_uint8),
		('pdevid', OPENUSB_DEVID),
		('pport', c_uint8),
		('nports', c_uint8),
		('sys_path', c_char_p),
		('bus_path', c_char_p),
		('dev_desc', USB_DEVICE_DESC),
		('cfg_desc', USB_CONFIG_DESC),
		('raw_cfg_desc', POINTER(c_uint8)),
		('manufacturer', POINTER(USB_STRING_DESC)),
		('product', POINTER(USB_STRING_DESC)),
		('serialnumber', POINTER(USB_STRING_DESC)),
		('ctrl_max_xfer_size', c_uint32),
		('intr_max_xfer_size', c_uint32),
		('bulk_max_xfer_size', c_uint32),
		('isoc_max_xfer_size', c_uint32)]

class OPENUSB_REQUEST_RESULT(Structure):
	_fields_ = [('status', c_int32),
		('transferred_bytes', c_uint32)]

class OPENUSB_CTRL_SETUP(Structure):
	_fields_ = [('bmRequestType', c_uint8),
		('bRequest', c_uint8),
		('wValue', c_uint16),
		('wIndex', c_uint16)]

class OPENUSB_CTRL_REQUEST(Structure):
	pass

OPENUSB_CTRL_REQUEST._fields_ = [('setup', OPENUSB_CTRL_SETUP),
	('payload', POINTER(c_uint8)),
	('length', c_uint32),
	('timeout', c_uint32),
	('flags', c_uint32),
	('result', OPENUSB_REQUEST_RESULT),
	('next', POINTER(OPENUSB_CTRL_REQUEST))]

class OPENUSB_INTR_REQUEST(Structure):
	pass

OPENUSB_INTR_REQUEST._fields_ = [('interval', c_uint16),
		('payload', POINTER(c_uint8)),
		('length', c_uint32),
		('timeout', c_uint32),
		('flags', c_uint32),
		('result', OPENUSB_REQUEST_RESULT),
		('next', POINTER(OPENUSB_INTR_REQUEST))]

class OPENUSB_BULK_REQUEST(Structure):
	pass

OPENUSB_BULK_REQUEST._fields_ = [('payload', c_uint8),
	('length', c_uint32),
	('timeout', c_uint32),
	('flags', c_uint32),
	('result', OPENUSB_REQUEST_RESULT),
	('next', POINTER(OPENUSB_BULK_REQUEST))]

class OPENUSB_ISOC_PACKET(Structure):
	_fields_ = [('payload', POINTER(c_uint8)),
		('length', c_uint32)]

class OPENUSB_ISOC_PKTS(Structure):
	_fields_ = [('num_packets', c_uint32),
		('packets', POINTER(OPENUSB_ISOC_PACKET))]

class OPENUSB_ISOC_REQUEST(Structure):
	pass

OPENUSB_ISOC_REQUEST._fields_ = [('start_frame', c_uint32),
		('flags', c_uint32),
		('pkts', OPENUSB_ISOC_PKTS),
		('isoc_results', POINTER(OPENUSB_REQUEST_RESULT)),
		('isoc_status', c_uint32),
		('next', POINTER(OPENUSB_ISOC_REQUEST))]

class OPENUSB_REQUEST(Union):
	_fields_ = [('ctrl', POINTER(OPENUSB_CTRL_REQUEST)),
		('intr', POINTER(OPENUSB_INTR_REQUEST)),
		('bulk', POINTER(OPENUSB_BULK_REQUEST)),
		('isoc', POINTER(OPENUSB_ISOC_REQUEST))]


class OPENUSB_REQUEST_HANDLE(Structure):
	pass

REQUEST_CALLBACK = CFUNCTYPE(c_int32, POINTER(OPENUSB_REQUEST_HANDLE))

OPENUSB_REQUEST_HANDLE._fields_ = [('dev', OPENUSB_DEV_HANDLE),
		('interface', c_uint8),
		('endpoint', c_uint8),
		('type', OPENUSB_TRANSFER_TYPE),
		('req', OPENUSB_REQUEST),
		('cb', REQUEST_CALLBACK),
		('arg', c_void_p)]

lib = cdll.LoadLibrary("libopenusb.so")


