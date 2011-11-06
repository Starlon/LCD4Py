import gobject
import time

from Widget import *
from Property import Property

from Constants import *
from Functions import *

class WidgetTimer(Widget):
	def __init__(self, visitor, name, section):
		Widget.__init__(self, visitor, name, 0, 0, WIDGET_TYPE_TIMER)

		self.expression = Property(self.visitor, section, 'expression', '')

		self.update = visitor.cfg_fetch_num(section, "update", 500)

		self.source_id = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def start(self, data=None):
		if self.update is None:
			return
		if self.source_id is None:
			self.source_id = gobject.timeout_add(self.update, self.timer_update)

	def stop(self, data=None):
		if self.source_id is not None:
			gobject.source_remove(self.source_id)
			self.source_id = None

	def timer_update(self):

		self.expression.eval()

		return True
