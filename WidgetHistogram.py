import gobject

from Widget import *
from Property import Property

from Constants import *
from Functions import *

class WidgetHistogram(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)

		if hasattr(visitor, "text_histogram_draw"):
			self.draw = visitor.text_histogram_draw
		elif hasattr(visitor, "graphic_histogram_draw"):
			self.draw = visitor.graphic_histogram_draw
		else:
			self.draw = None

		
		self.min = 0
		self.max = 0
		self.string = ''
		self.expression = Property(self.visitor, section, 'expression', '')
		self.expr_min = Property(self.visitor, section, 'min', None)
		self.expr_max = Property(self.visitor, section, 'max', None)

		self.length = visitor.cfg_fetch_num(section, 'length', 10)

		self.height = visitor.cfg_fetch_num(section, 'height', 1)

		self.gap = visitor.cfg_fetch_num(section, "gap", 0)

		self.layer = visitor.cfg_fetch_num(section, "layer", 0)

		self.history = resizeList([], self.length, int)

		c = visitor.cfg_fetch_raw(section, "direction", "E")

		if c.upper() == "E":
			self.direction = DIR_EAST
		elif c.upper() == "W":
			self.direction = DIR_WEST
		else:
			error("widget %s has unknown direction '%s'; Use E(ast) or W(est). Using E." % (self.name, c))
			self.direction = DIR_EAST

		self.update = visitor.cfg_fetch_num(section, 'update', 1000)

		self.fg_color = RGBA()
		self.fg_valid = self.widget_color(section, "foreground", self.fg_color)
		self.bg_color = RGBA()
		self.bg_valid = self.widget_color(section, "background", self.bg_color)

		self.ch = {}

		self.id_source = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def setup_chars(self):
		self.ch = {}

		for char in range(self.visitor.YRES):
			buffer = []
			i = self.visitor.YRES - 1
			while i >= 0:  
				buffer.append( [0, 2**(self.visitor.XRES-self.gap)-1][i < char] )
				i = i - 1

			reused = False

			for i in range(len(self.visitor.chars)):
				if buffer == self.visitor.chars[i]:
					self.ch[char] = i
					reused = True
					break

			if char not in self.ch.keys():	
				if self.visitor.CHARS - len(self.visitor.chars) < self.visitor.YRES-char:
					self.update = None
					error("widget %s unable to allocate special chars" % self.name)
					return

			if reused: continue
			self.visitor.chars.append(buffer)
			self.ch[char] = len(self.visitor.chars)-1

	def start(self, data=None):
		if self.update is None:
			return
		if self.id_source is not None:
			self.stop()
		self.id_source = gobject.timeout_add(self.update, self.histogram_update)
		self.histogram_update()

	def stop(self, data=None):
		if self.id_source is not None:
			gobject.source_remove(self.id_source)
		self.id_source = None

	def histogram_update(self):

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
			val = (val - min) / (max - min)
		else:
			val = 0.0

		if self.direction == DIR_EAST:
			self.history[1:] = self.history[:-1]
			self.history[0] = val
		elif self.direction == DIR_WEST:
			self.history[:-1] = self.history[1:]
			self.history[self.length-1] = val

		if self.draw is not None:
			self.draw(self)
		else:
			error( "WidgetHistogram: no draw method" )

		
		return True
