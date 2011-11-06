import gobject
import time

from Widget import *
from Property import Property

from Constants import *
from Functions import *

class WidgetKey(Widget):
	def __init__(self, visitor, name, section):
		Widget.__init__(self, visitor, name, 0, 0, WIDGET_TYPE_KEYPAD)

		self.expression = Property(self.visitor, section, 'expression', '')

		self.key = visitor.cfg_fetch_num(section, "key", 0)

		self.signal_id = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def start(self, data=None):
		if self.signal_id is None:
			self.signal_id = self.visitor.connect("key-packet-ready", self.key_packet_ready)

	def stop(self, data=None):
		if self.signal_id is not None:
			self.visitor.disconnect(self.signal_id)
			self.signal_id = None

	def key_packet_ready(self, device, key):
		if key == self.key and self.expression.valid():
			self.expression.eval()

		return True
