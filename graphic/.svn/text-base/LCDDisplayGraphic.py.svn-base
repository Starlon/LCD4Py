import gtk, gtk.gdk, gobject

from Generic import Generic
from Graphic import Graphic
from RGBA import RGBA

from Functions import *
from Constants import *

class LCDDisplayGraphic(Generic, Graphic):
	def __init__(self, visitor, darea, obj=None, config=None, key=None):
		Generic.__init__(self, self.visitor, obj, config, TYPE_GRAPHIC)
		section = self.cfg_fetch_raw(config, key, None)
		Graphic.__init__(self, section, rows=64, cols=256)
		self.dots = {'x': 6, 'y':8}
		self.pixels = {'x':4, 'y':4} # Resolution in crt pixels - scaled
		self.border = 5
		self.darea = darea
		self.darea.connect('expose-event', self.lcd_expose_event, self)
		self.bg_color = gtk.gdk.color_parse("#78a878")
		self.fg_color = gtk.gdk.color_parse("#113311")
		self.config = config
		self.rows = 8
		self.cols = 256/6
		self.lcd_gc = None
		if obj == None:
			self.name = 'noname'
			self.connected = False
			self.framebuffer = resizeList([], 256 * 64, list)
			self.clear_display()
		else:
			self.name = obj.name
			self.connected = obj.connected
			self.framebuffer = obj.framebuffer
		self.app = visitor

	def graphic_real_blit(self, row, col, height, width):
		for i in range(row, row+height):
			for j in range(col, col+width):
				self.framebuffer[i * self.DCOLS + j] = self.graphic_rgb(i, j)
				print self.graphic_rgb(i, j)
		self.darea.queue_draw()
		
	def CreateGraphics(self):
		border = self.get_border()

		self.darea.set_size_request(self.DCOLS + 2*border, self.DROWS + 2*border)

	def update(self, widget, new_width, new_height):
		drawable = widget.window

		if not self.lcd_gc: 
			self.lcd_gc = drawable.new_gc()
		
		self.w_width = new_width
		self.w_height = new_height

		self.lcd_gc.set_rgb_fg_color(self.bg_color)

		drawable.draw_rectangle(self.lcd_gc, True, 0, 0, self.w_width, self.w_height)

		cw = self.get_char_width()
		ch = self.get_char_height()
		border = self.get_border()

		for i in range(0, self.DROWS):
			for j in range(0, self.DCOLS):
				f = self.framebuffer[i * self.DCOLS + j]
				color = gtk.gdk.Color(red=f[0] * 256, green=f[1] * 256, blue=f[2] * 256)
				self.lcd_gc.set_rgb_fg_color(color)
				drawable.draw_point( self.lcd_gc, j+border, i+border)	

	def lcd_expose_event(self, widget, event, data=None):

		if not widget or type(widget).__name__ != "DrawingArea": return True

		rect = widget.get_allocation()
		self.update(widget, rect.width, rect.height)

		return True
	
	def SetSpecialChar(self, char, data):
		self.set_special_char(char, data)

	def set_special_char(self, char, data):
		for row in range(0, 8):
			self.lcd_fonts[char][row] = data[row]
		if self.fontP:
			self.fontP.update_font(char, self.lcd_fonts[char])
			self.darea.queue_draw()

	def set_pixel_resolution(self, x=5, y=7):
		self.dots['x'] = x
		self.dots['y'] = y
	
	def set_crt_resolution(self, x=3, y=3):
		self.pixels['x'] = x
		self.pixels['y'] = y

	def get_char_width(self):
		return 1 + self.dots['x'] * self.pixels['x']

	def get_char_height(self):
		return self.dots['y'] * self.pixels['y']

	def get_border(self):
		return self.border

	def clear_display(self):
		for i in range(0, self.DROWS):
			for j in range(0, self.DCOLS):
				self.framebuffer[i * self.DCOLS + j] = self.FG_COL
		self.darea.queue_draw()

