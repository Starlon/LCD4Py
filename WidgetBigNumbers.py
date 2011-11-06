import gobject
import pickle

from Widget import *
from Property import Property

from Constants import *
from Functions import *

from Buffer import Buffer

STYLE_NORMAL = 0
STYLE_HOLLOW = 1

fd = open("bignums.dat")
CHAR = pickle.load(fd)
fd.close()

class WidgetBigNumbers(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)

		if hasattr(visitor, "text_bignums_draw"):
			self.draw = visitor.text_bignums_draw
		elif hasattr(visitor, "graphic_bignums_draw"):
			self.draw = visitor.graphic_bignums_draw
		else:
			self.draw = None

		self.FB = Buffer()
		self.FB.buffer = ' ' * 16 * 24

		self.min = 0
		self.max = 0
		self.string = ''
		self.expression = Property(self.visitor, section, 'expression', '')
		self.expr_min = Property(self.visitor, section, 'min', None)
		self.expr_max = Property(self.visitor, section, 'max', None)

		self.length = visitor.cfg_fetch_num(section, 'length', 10)

		self.update = visitor.cfg_fetch_num(section, 'update', 500)

		self.fg_color = RGBA()
		self.fg_valid = self.widget_color(section, "foreground", self.fg_color)
		self.bg_color = RGBA()
		self.bg_valid = self.widget_color(section, "background", self.bg_color)

		self.layer = visitor.cfg_fetch_num(section, "layer", 0)
		
		self.ch = {}

		self.id_source = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def setup_chars(self):
		for i in range(8):
			if len(self.visitor.chars) >= self.visitor.CHARS:
				error("Can not allot char for widget: %s" % name)
				self.update = None
				return
			self.visitor.chars.append(CHAR[i])
			self.ch[i] = len(self.visitor.chars) - 1

	def start(self, data=None):
		if self.update is None:
			return
		if self.id_source is not None:
			self.stop()
		self.id_source = gobject.timeout_add(self.update, self.bignums_update)
		self.bignums_update()

	def stop(self, data=None):
		if self.id_source is not None:
			gobject.source_remove(self.id_source)
		self.id_source = None

	def bignums_update(self):

		self.expression.eval()
		val = self.expression.P2N()

		if self.expr_min.valid():
			self.expr_min.eval()
			min = self.expr_min.P2N()
		else:
			min = self.min
			if val < min:
				min = val

		if self.expr_max.valid():
			self.expr_max.eval()
			max = self.expr_max.P2N()
		else:
			max = self.max
			if val > max:
				max = val	

		self.min = min
		self.max = max
		if max > min:
			self.val = int((val - min) / (max - min) * 100)
		else:
			self.val = 0

		
		text = str(self.val)
		pad = 3 - len(text)
		self.FB.buffer = ' ' * 16 * 24
		for i in range(len(text)):
			c = ord(text[i]) - ord('0')
			for row in range(16):
				for col in range(8):
					if (CHAR[c][row] & 1<<7-col) != 0:
						self.FB[row * 24 + (i + pad) * 8 + col] = '.'

		if self.draw is not None:
			self.draw(self)
		else:
			error( "WidgetBigNumbers: no draw method" )

		
		return True
