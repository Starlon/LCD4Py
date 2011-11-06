import gobject

from Widget import *
from Property import Property
from Buffer import Buffer
from RGBA import RGBA

from Constants import *
from Functions import *

ALIGN_LEFT = 'L'
ALIGN_CENTER = 'C'
ALIGN_RIGHT = 'R'
ALIGN_MARQUEE = 'M'
ALIGN_AUTOMATIC = 'A'
ALIGN_PINGPONG = 'P'

PINGPONGWAIT = 2

class WidgetText(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)
		if hasattr(visitor, "text_draw"):
			self.draw = visitor.text_draw
		elif hasattr(visitor, "graphic_draw"):
			self.draw = visitor.graphic_draw
		else:
			self.draw = None

		self.row = row
		self.col = col

		self.string = ''
		self.prefix = Property(self.visitor, section, "prefix", '')
		self.postfix = Property(self.visitor, section, 'postfix', '')
		self.style = Property(self.visitor, section, 'style', '')
		self.value = Property(self.visitor, section, 'expression', '')
		self.width = visitor.cfg_fetch_num(section, 'width', 10)
		self.precision = visitor.cfg_fetch_num(section, 'precision', 0xDEAD)
		self.align = visitor.cfg_fetch_raw(section, 'align', 'L')
		self.update = visitor.cfg_fetch_num(section, 'update', 1000)
		self.scroll = visitor.cfg_fetch_num(section, 'scroll', 500)
		self.speed = visitor.cfg_fetch_num(section, 'speed', 500)
		self.fg_color = RGBA()
		self.bg_color = RGBA()
		self.fg_valid = self.widget_color(section, "foreground", self.fg_color)
		self.bg_valid = self.widget_color(section, "background", self.bg_color)
		self.layer = visitor.cfg_fetch_num(section, "layer", 0)
		
		self.id_source = None
		self.scroll_source = None
		self.buffer = ' ' * self.width
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def _get(self):
		return "".join(self._buffer)

	def _set(self, val):
		self._buffer = [x for x in val]

	def _del(self):
		del(self._buffer)
		self._buffer = []

	buffer = property(_get, _set, _del, "WidgetText buffer")

	def start(self, data=None):
		if self.id_source or self.scroll_source:
			self.stop()
		self.id_source = gobject.timeout_add(self.update, self.text_update)
		if self.align == ALIGN_MARQUEE or self.align == ALIGN_AUTOMATIC or self.align == ALIGN_PINGPONG:
			self.scroll_source = gobject.timeout_add(self.speed, self.text_scroll)
		self.text_update()

	def stop(self, data=None):
		if self.id_source: 
			gobject.source_remove(self.id_source)
		self.id_source = None
		if self.scroll_source:
			gobject.source_remove(self.scroll_source)
		self.scroll_source = None
		

	def text_update(self):
		update = 0
		update = update + self.prefix.eval()
		update = update + self.postfix.eval()
		update = update + self.style.eval()

		self.value.eval()

		if self.precision == 0xDEAD:
			string = self.value.P2S()
		else:
			number = self.value.P2N()
			precision = self.precision
			width = self.width - len(self.prefix.P2S()) - len(self.postfix.P2S())
			string = "%.*f" % (precision, number)
			size = len(string)
			if width < 0:
				width = 0
			if size > width and precision > 0:
				delta = size - width
				if delta > precision:
					delta = precision
				precision =  precision - delta
				size = size - delta

			if size > width:
				string = "*" * width

		if not self.string or strcmp(self.string, string) != 0:
			update = update + 1
			self.string = string

		if update:
			self.scroll = 0

		if self.align == ALIGN_PINGPONG:
			self.direction = 0
			self.delay = PINGPONGWAIT

		if self.align != ALIGN_MARQUEE or self.align != ALIGN_AUTOMATIC or self.align != ALIGN_PINGPONG:
			self.text_scroll()

		if self.update == 0:
			return False
		return True

	def text_scroll(self):
		prefix = self.prefix.P2S()
		postfix = self.postfix.P2S()

		string = self.string

		num = 0
		length = len(string)
		width = self.width - len(prefix) - len(postfix)
		if width < 0:
			width = 0

		if self.align == ALIGN_LEFT:
			pad = 0
		elif self.align == ALIGN_CENTER:
			pad = (width - length) / 2
			if pad < 0:
				pad = 0
		elif self.align == ALIGN_RIGHT:
			pad = width - length
			if pad < 0:
				pad = 0
		elif self.align == ALIGN_AUTOMATIC:
			if length <= width:
				pad = 0
		elif self.align == ALIGN_MARQUEE:
			pad = width - self.scroll
			self.scroll = self.scroll + 1
			if self.scroll >= width + length:
				self.scroll = 0
		elif self.align == ALIGN_PINGPONG:
			if length <= width:
				pad = (width - length) / 2
			else:
				if self.direction == 1:
					self.scroll = self.scroll + 1
				else:
					self.scroll = self.scroll - 1

			pad = 0 - self.scroll

			if pad < 0 - (length - width):
				if self.delay < 1:
					self.direction = 0
					self.delay = PINGPONGWAIT
					self.scroll = self.scroll - PINGPONGWAIT
				self.delay = self.delay - 1
				pad = 0 - (length - width)
			elif pad > 0:
				if self.delay < 1:
					self.direction = 1
					self.delay = PINGPONGWAIT
					self.scroll = self.scroll + PINGPONGWAIT
				self.delay = self.delay - 1
				pad = 0

			
		else:
			pad = 0

		dst = 0
		num = 0
		src = prefix
		for i in range(len(src)):
			if dst >= len(self.buffer):
				break
			self._buffer[dst] = src[i]
			dst = dst + 1
			num =  num + 1

		src = string

		while dst < len(self.buffer) and pad > 0 and num < self.width:
			self._buffer[dst] = ' '
			#print "num", num, "pad", pad, "width", self.width
			dst = dst + 1
			num = num + 1
			pad = pad - 1

		while pad < 0:
			src = src[1:] 
			pad = pad + 1

		i = 0
		while dst <  len(self.buffer) and i < len(src) and num < self.width:
			self._buffer[dst] = src[i]
			dst = dst + 1
			i = i + 1
			num = num + 1

		src = postfix
		length = len(src)

		while dst < len(self.buffer) and num < self.width - length:
			self._buffer[dst] = ' '
			dst = dst + 1
			num = num + 1

		i = 0
		while dst < len(self.buffer) and i < length and num < self.width:
			self._buffer[dst] = src[i]
			dst = dst + 1
			i = i + 1
			num = num + 1

		if self.draw is not None:
			self.draw(self)
		else:
			error("WidgetText: No draw method")

		return True

