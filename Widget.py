from RGBA import RGBA

class Widget(object):
	def __init__(self, visitor, name, row, col, type):
		self.visitor = visitor
		self.name = name
		pos1 = name.find(":")
		pos2 = name.rfind(":")
		self.widget_base = name[pos1+1:pos2]
		self.row = row
		self.col = col
		self.type = type
		self.id_source = None
		self._buffer = []

	def widget_color(self, section, key, C):
		C.R = 0
		C.G = 0
		C.B = 0
		C.A = 0

		color = self.visitor.cfg_fetch_raw(section, key, None)

		if color is None:
			return 0

		if color == '':
			return 0

		if RGBA.color2RGBA(color, C) < 0:
			return 0
		return 1


WIDGET_TYPE_RC = 1
WIDGET_TYPE_XY = 2
WIDGET_TYPE_GPO = 3
WIDGET_TYPE_TIMER = 4
WIDGET_TYPE_KEYPAD = 5

