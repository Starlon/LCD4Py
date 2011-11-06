import gobject
import pickle
from PIL import Image

from Widget import *
from Property import Property
from RGBA import RGBA

from Constants import *
from Functions import *

class WidgetGif(Widget):
	def __init__(self, visitor, name, section, row, col):
		Widget.__init__(self, visitor, name, row, col, WIDGET_TYPE_RC)

		if hasattr(visitor, "text_gif_draw"):
			self.draw = visitor.text_gif_draw
		elif hasattr(visitor, "graphic_gif_draw"):
			self.draw = visitor.graphic_gif_draw
		else:
			self.draw = None

		self.file = visitor.cfg_fetch_raw(section, "file")

		self.image = Image.open(self.file)
		lut = self.image.resize((256, 1))
		lut.putdata(range(256))
		self.palette = lut.convert("RGB").getdata()
		
		if "background" in self.image.info.keys():
			self.bg = self.image.info['background']
		else:
			self.bg = -1

		if "transparency" in self.image.info.keys():
			self.tp = self.image.info['transparency']
		else:
			self.tp = -1

		self.update = visitor.cfg_fetch_num(section, 'update', 500)

		self.frameStart = visitor.cfg_fetch_num(section, "start", 0)
		self.frameEnd = visitor.cfg_fetch_num(section, "end", -1)

		self.xpoint = visitor.cfg_fetch_num(section, "xpoint", 0)
		self.ypoint = visitor.cfg_fetch_num(section, "ypoint", 0)

		self.width = visitor.cfg_fetch_num(section, "width", -1)
		self.height = visitor.cfg_fetch_num(section, "height", -1)

		self.layer = visitor.cfg_fetch_num(section, 'layer', 0)

		if self.width == -1:
			self.width = self.image.size[0]

		if self.height == -1:
			self.height = self.image.size[1]

		pixels = self.image.load()

		self.pixels = resizeList([], self.width * self.height, RGBA)

		try:
			pixels[self.xpoint+self.width-1, self.ypoint+self.height-1]
		except IndexError:
			error("WidgetGif: Index out of image range: %s" % self.widget_base)
			self.update = None

		self.rows = self.height / self.visitor.YRES

		self.cols = self.width / self.visitor.XRES

		self.frames = 0

		while True:
			try:
				self.image.seek(self.frames)
				self.frames = self.frames + 1
			except EOFError:
				break

		#if self.frames > 0:
		#	self.frames = self.frames - 1

		self.ch = {}

		self.has_chars = False

		self.framesG = self.generator()

		self.id_source = None
		self.id_signal = visitor.connect("display-disconnected-before", self.stop)

	def generator(self):
		i = 0
		while True:
			if i >= self.frames:
				i = 0
			if self.frameEnd != -1 and i > self.frameEnd:
				while i < self.frames:
					self.image.seek(i)
					i = i + 1
				i = 0
			if i == 0:
				self.image.seek(0)
	
			while i < self.frameStart:
				self.image.seek(i)
				i = i + 1

			yield i
			i = i + 1

	def setup_chars(self):
		for key in self.visitor.widgets.keys():
			if self.visitor.widgets[key].widget_base == self.widget_base \
				and self.visitor.widgets[key].has_chars:
				for i in range(self.rows * self.cols):
					if i >= self.visitor.CHARS:
						error("Gif too large. %s " % self.widget_base)
						self.update = False
						return
					self.ch[i] = self.visitor.widgets[key].ch[i]
				self.has_chars = True
				return

		for i in range(self.rows * self.cols):
			if len(self.visitor.chars) > self.visitor.CHARS:
				error("Can not allot char for widget: %s" % self.name)
				self.update = None
				return
			self.visitor.chars.append([0 for x in range(8)])
			self.ch[i] = len(self.visitor.chars) - 1
		self.has_chars = True

	def start(self, data=None):
		if self.update is None:
			return
		for key in self.visitor.widgets.keys():
			if self.visitor.widgets[key].widget_base == self.widget_base \
				and self.visitor.widgets[key].id_source is not None \
				and self.visitor.TYPE == TYPE_TEXT:
				self.id_source = self.visitor.widgets[key].id_source
				self.gif_update()
				return
		if self.id_source is not None:
			self.stop()
		self.id_source = gobject.timeout_add(self.update, self.gif_update)
		self.gif_update()

	def stop(self, data=None):
		if self.id_source is not None:
			gobject.source_remove(self.id_source)
		self.id_source = None
		self.ch = {}
		self.has_chars = False

	def gif_update(self):

		self.image.seek(self.framesG.next())

		pixels = self.image.load()

		for row in range(self.height):
			for col in range(self.width):
				pxl = pixels[col + self.xpoint, row + self.ypoint]
				n = row * self.width + col
				self.pixels[n].R = self.palette[pxl][0]
				self.pixels[n].G = self.palette[pxl][1]
				self.pixels[n].B = self.palette[pxl][2]
				self.pixels[n].A = (255, 0)[pxl == self.tp]
				self.pixels[n].pxl = pxl

		if self.draw is not None:
			self.draw(self)
		else:
			error( "WidgetGif: no draw method" )
		
		return True
