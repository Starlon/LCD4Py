import gobject

from Widget import *
from Property import Property
from RGBA import RGBA
from Constants import *
from Functions import *

STYLE_NORMAL = 0
STYLE_HOLLOW = 1

CHAR = {}
CHAR[0] = [31, 31, 31, 31, 31, 31, 31, 31]
CHAR[1] = [31, 16, 16, 16, 16, 16, 16, 31]
CHAR[2] = [31, 0, 0, 0, 0, 0, 0, 31]
CHAR[3] = [31, 1, 1, 1, 1, 1, 1, 31]
CHAR[4] = [31, 31, 31, 31, 0, 0, 0, 0]
CHAR[5] = [0, 0, 0, 0, 31, 31, 31, 31]

class WidgetBar(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)

		if hasattr(visitor, "text_bar_draw"):
			self.draw = visitor.text_bar_draw
		elif hasattr(visitor, "graphic_bar_draw"):
			self.draw = visitor.graphic_bar_draw
		else:
			self.draw = None

		self.min = 0
		self.max = 0
		self.string = ''
		self.expression = Property(self.visitor, section, 'expression', '')
		self.expression2 = Property(self.visitor, section, 'expression2', '')
		self.expr_min = Property(self.visitor, section, 'min', None)
		self.expr_max = Property(self.visitor, section, 'max', None)

		self.color_valid = resizeList([], 2, int)
		self.color = resizeList([], 2, RGBA)
		self.color_valid[0] = self.widget_color(section, "barcolor0", self.color[0])
		self.color_valid[1] = self.widget_color(section, "barcolor1", self.color[1])

		self.layer = visitor.cfg_fetch_num(section, 'layer', 0)

		self.length = visitor.cfg_fetch_num(section, 'length', 10)
		c = visitor.cfg_fetch_raw(section, "direction", "E")

		if c.upper() == "E":
			self.direction = DIR_EAST
		elif c.upper() == "W":
			self.direction = DIR_WEST
		else:
			error("widget %s has unknown direction '%s'; Use E(ast) or W(est). Using E." % (self.name, c))
			self.direction = DIR_EAST

		self.update = visitor.cfg_fetch_num(section, 'update', 1000)

		c = visitor.cfg_fetch_raw(section, "style", "O")

		if c.upper() == "H":
			self.style = STYLE_HOLLOW
		elif c.upper() == "N" or c.upper == "O":
			self.style = STYLE_NORMAL
		else:
			error("widget %s has unknown style '%s'; known styles 'N' or 'H'; using 'N'" % (self.name, c))
			self.style = STYLE_NORMAL

		self.ch = {}

		self.id_source = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def setup_chars(self):
		self.ch = {}
		if self.style == STYLE_HOLLOW and not self.expression2.valid():
			for i in range(4):
				for j in range(len(self.visitor.chars)):
					if self.visitor.chars[j] == CHAR[i]:
						self.ch[i] = j

			for i in range(6):
				if i not in self.ch.keys():
					if len(self.visitor.chars) >= self.visitor.CHARS:
						error("Can not allot char for widget: %s" % name)
						self.update = None
						return
					self.visitor.chars.append(CHAR[i])
					self.ch[i] = len(self.visitor.chars) - 1
		elif self.style == STYLE_NORMAL:
			for j in range(len(self.visitor.chars)):
				if self.visitor.chars[j] == CHAR[0]:
					self.ch[0] = j
				if self.visitor.chars[j] == CHAR[4]:
					self.ch[1] = j
				if self.visitor.chars[j] == CHAR[5]:
					self.ch[2] = j
			if 0 not in self.ch.keys():
				if len(self.visitor.chars) >= self.visitor.CHARS:
					error("Can not allot char for bar widget: %s" % self.widget_base)
					self.update = None
					return
				self.visitor.chars.append(CHAR[0])
				self.ch[0] = len(self.visitor.chars) - 1
			if 1 not in self.ch.keys() and self.expression2.valid():
				if len(self.visitor.chars) >= self.visitor.CHARS:
					error("Can not allot char for bar widget: %s" % self.widget_base)
					return
				self.visitor.chars.append(CHAR[4])
				self.ch[1] = len(self.visitor.chars) - 1
			if 2 not in self.ch.keys() and self.expression2.valid():
				if len(self.visitor.chars) >= self.visitor.CHARS:
					error("Can not allot char for bar widget: %s" % self.widget_base)
					return
				self.visitor.chars.append(CHAR[5])
				self.ch[2] = len(self.visitor.chars) - 1

		else:
			error("%s: Either choose style hollow or have a 2nd expression, not both" % self.widget_base)
			self.update = None

	def start(self, data=None):
		if self.update is None:
			return
		if self.id_source is not None:
			self.stop()
		self.id_source = gobject.timeout_add(self.update, self.bar_update)
		self.bar_update()

	def stop(self, data=None):
		if self.id_source is not None:
			gobject.source_remove(self.id_source)
		self.id_source = None

	def bar_update(self):
		self.expression.eval()
		val1 = self.expression.P2N()
		if self.expression2.valid():
			self.expression2.eval()
			val2 = self.expression2.P2N()
		else:
			val2 = val1

		if self.expr_min.valid():
			self.expr_min.eval()
			min = self.expr_min.P2N()
		else:
			min = self.min
			if val1 < min:
				min = val1
			if val2 < min:
				min = val2

		if self.expr_max.valid():
			self.expr_max.eval()
			max = self.expr_max.P2N()
		else:
			max = self.max
			if val1 > max:
				max = val1
			if val2 > max:
				max = val2

		self.min = min
		self.max = max
		if max > min:
			self.val1 = (val1 - min) / (max - min)
			self.val2 = (val2 - min) / (max - min)
		else:
			self.val1 = 0.0
			self.val2 = 0.0

		if self.draw is not None:
			self.draw(self)
		else:
			error( "WidgetBar: no draw method" )

		
		return True
