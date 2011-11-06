import gobject
import time

from Widget import *
from Property import Property
from RGBA import RGBA

from Constants import *
from Functions import *

from ThreadedTask import ThreadedTask

class WidgetIcon(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)

		if hasattr(visitor, "text_icon_draw"):
			self.draw = visitor.text_icon_draw
		elif hasattr(visitor, "graphic_icon_draw"):
			self.draw = visitor.graphic_icon_draw
		else:
			self.draw = None

		self.update = visitor.cfg_fetch_num(section, 'speed', 200)

		self.visible = Property(self.visitor, section, "visible", '1')

		self.layer = visitor.cfg_fetch_num(section, "layer", 0)

		self.fg_color = RGBA()
		self.fg_valid = self.widget_color(section, "foreground", self.fg_color)
		self.bg_color = RGBA()
		self.bg_valid = self.widget_color(section, "foreground", self.bg_color)

		bitmap = visitor.cfg_fetch_raw(section, 'bitmap')

		if bitmap is None:
			self.update = None
			return

		ch = []
		i = 0
		while True:
			key = 'row%g' % (i + 1)
			row = visitor.cfg_fetch_raw(bitmap, key)
			if row is None:
				break
			line = row.split('|')
			if line[len(line)-1] == '':
				line.pop(len(line)-1)
			for j in range(len(line)):
				segment = line[j]
				if j >= len(ch):
					ch.append([])
					for ii in range(visitor.YRES):
						ch[j].append(0)
				for c in range(len(segment)):
					if segment[c] == '*':
						ch[j][i] = ch[j][i] ^ 1<<c
			i = i + 1

		self.data = ch

		self.generator = self.gen()

		self.started = False
		self.source_id = None

		self.ch = None

		self.bitmap = None

		self.source_id = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def gen(self):
		i = 0
		while True:
			yield i
			if self.update is not None:
				i = i + 1
				if i >= len(self.data):
					i = 0

	def setup_chars(self):
		for key in self.visitor.widgets.keys():
			name = key
			pos1 = name.find(":")
			pos2 = name.rfind(":")
			name = name[pos1+1:pos2]
			if name == self.widget_base:
				if self.visitor.widgets[key].ch is not None:
					self.ch = self.visitor.widgets[key].ch
					return
		if len(self.visitor.chars) >= self.visitor.CHARS:
			error("Can not allot char for widget: %s" % self.name)
			self.update = None
			return
		self.visitor.chars.append(self.data[0])
		self.ch = len(self.visitor.chars) - 1

	def start(self, data=None):
		if self.update is None:
			return
		for key in self.visitor.widgets.keys():
			name = key
			pos1 = name.find(":")
			pos2 = name.rfind(":")
			name = name[pos1+1:pos2]
			# Only have one widget timer per widget definition
			if name == self.widget_base and self.visitor.widgets[key].source_id is not None \
				and self.visitor.TYPE == TYPE_TEXT:
				self.source_id = self.visitor.widgets[key].source_id
				break
		if self.source_id is None:
			self.source_id = gobject.timeout_add(self.update, self.icon_update)
		self.icon_update()

	def stop(self, data=None):
		if self.source_id is not None:
			gobject.source_remove(self.source_id)
			self.source_id = None
		self.ch = None

	def icon_update(self):

		i = self.generator.next()
							
		self.bitmap = self.data[i]

		if self.draw is not None:
			self.draw(self)

		return True
