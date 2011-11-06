import gtk, gtk.gdk, gobject
import pickle

from Generic import Generic
from Text import Text

_8BIT_MODE_FLAG=1<<0
LARGE_FONT_MODE_FLAG=1<<1
_2LINE_MODE_FLAG=1<<2
DISPLAY_ON_FLAG=1<<3
CURSOR_ON_FLAG=1<<4
BLINK_ON_FLAG=1<<5

TWO_ROWS_IN_ONE=1

FONT_LEN = 256

CGRAM=[[0, 8,12,14,15,14,12, 8],  #right arrow
[0, 1, 3, 7,15, 7, 3, 1],  #left arrow  
[0, 4, 4,14,14,31,31, 0],  #up arrow  
[0,31,31,14,14, 4, 4, 0],  #down arrow  
[0, 0,14,31,31,31,14, 0],  #circle  
[0, 1, 3, 3, 6,22,28,12],  #check  
[0,17,27,14, 4,14,27,17],  #cancel  
[4,14,63, 4, 4,63,14, 4]] #Up/Dn Arrow

		
class LCDFont:
	def __init__(self, characters, parent_window, lcdP):
		self.num_elements = characters
		self.parent_window = parent_window
		self.lcdP = lcdP
		self.setup()

	def setup(self):
		self.pixmaps = []
		for i in range(0, self.num_elements):
			self.pixmaps.append(CreatePixmapFromLCDdata(self.lcdP, self.lcdP.lcd_fonts[i]))

	def update_font(self, char, data):
		self.pixmaps[char] = CreatePixmapFromLCDdata(self.lcdP, self.lcdP.lcd_fonts[char])
			


class LCDDisplay(Generic, Text):
	def __init__(self, darea, rows=4, cols=20, obj=None, config=None):
		file = open('cfa635_fonts.dat', 'r')
		self.lcd_fonts = pickle.load(file)
		file.close()
		self.ch_data = []
		self.fontP = None
		self.interface = None
		self.current_state = None
		self.previous_state = None
		self.mode_flag = 0
		self.data_latch = None
		self.data_latch_phase = None
		self.debug = False
		self.cursor = {'row':0, 'col':0}
		self.lcd_gc = None
		self.rows = rows
		self.cols = cols
		self.dots = {'x':6, 'y':8} # Resolution in lcd pixels. e.g. 5x7
		self.pixels = {'x':4, 'y':4} # Resolution in crt pixels - scaled
		self.contrast = None
		self.dot_color = None
		self.title = None
		self.window = None
		self.darea = None
		self.w_width = None
		self.w_height = None
		self.disp_type = 0
		self.border = 0
		self.darea = darea
		self.darea.connect('expose-event', self.lcd_expose_event, self)
		self.darea.connect('button-press-event', self.cursor_event)
		self.bg_color = gtk.gdk.color_parse("#78a878")
		self.fg_color = gtk.gdk.color_parse("#113311")
		self.config = config
		Generic.__init__(self, self.visitor, obj, config)
		Text.__init__(self, rows=rows, cols=cols, yres=8, xres=6, goto=0, chars=8, char0=0)

	def real_write(self, row, col, data_start, len):
		if len == 0: return
		self.write_data2(row, col, self.DisplayFB[data_start:data_start+len])
		
	def CreateGraphics(self):
		for i in range(0, self.rows):
			self.ch_data.append([])
			for j in range(0, self.cols):
				self.ch_data[i].append([])
				self.ch_data[i][j] = ord(' ')

		cw = self.get_char_width()
		ch = self.get_char_height()
		border = self.get_border()

		self.darea.set_size_request(self.cols*cw + 2*border, self.rows*ch + 2*border)

	def update(self, widget, new_width, new_height):
		drawable = widget.window
		if not self.lcd_gc: 
			self.lcd_gc = drawable.new_gc()
		
		self.w_width = new_width
		self.w_height = new_height

		if not self.fontP: self.fontP = LCDFont(FONT_LEN, widget, self)

		self.lcd_gc.set_rgb_fg_color(self.bg_color)

		drawable.draw_rectangle(self.lcd_gc, True, 0, 0, self.w_width, self.w_height)

		cw = self.get_char_width()
		ch = self.get_char_height()
		border = self.get_border()

		if not (self.disp_type & TWO_ROWS_IN_ONE):
			for j in range(0, self.rows):
				for i in range(0, self.cols):
					widget.window.draw_drawable(self.lcd_gc, self.get_pixmap(j,i), 0, 0, border+i*cw, border+j*(ch+border), cw, ch)
	
		else:
			for j in range(0, self.rows):
				for i in range(0, self.cols):
					widget.window.draw_drawable( self.lcd_gc, self.get_pixmap(j, i), 0, 0, border+j*cw, border, cw, ch)	

	def lcd_expose_event(self, widget, event, data=None):
		lcdP = None

		if not widget or type(widget).__name__ != "DrawingArea": return True

		self.lcdP = data

		rect = widget.get_allocation()
		self.lcdP.update(widget, rect.width, rect.height)

		return True
	
	def cursor_event(self, widget, event, data=None):
		pass
	
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
	
	def set_contrast(self, contrast = 1.0):
		self.contrast = contrast

	def get_char_width(self):
		return 1 + self.dots['x'] * self.pixels['x']

	def get_char_height(self):
		return self.dots['y'] * self.pixels['y']

	def get_border(self):
		return self.border

	def get_pixmap(self, row, col):
		if self.fontP:
			if self.fontP.pixmaps[self.ch_data[row][col]]:
				return self.fontP.pixmaps[self.ch_data[row][col]]
			else:
				return self.fontP.pixmaps[0]

	def move_cursor(self, new_row, new_column):
		if (new_row >= 0 and new_row < self.rows) and (new_column >= 0 and new_column < self.cols):
			self.cursor['row'] = new_row
			self.cursor['col'] = new_column

	def clear_display(self):
		if not self.ch_data: return

		for i in range(0, self.rows):
			for j in range(0, self.cols):
				self.ch_data[i][j] = ord(' ')
		self.move_cursor(0,0)
		self.darea.queue_draw()

	def write_data(self, data):
		if self.cursor['col'] < self.cols:
			self.ch_data[self.cursor['row']][self.cursor['col']]= data
			self.cursor['col'] = self.cursor['col'] + 1

	def write_ddram_address(self, data):
		data = data & 0x7F
		self.cursor['col'] = (data & 0x3F) % 40
		self.cursor['row'] = [1,0](data & 0x40)
		pass
	
	def write_data2(self, row, col, data):
		self.cursor['row'] = row
		self.cursor['col'] = col
		for i in range(0, len(data)):
			self.write_data(ord(data[i]))
		self.darea.queue_draw()
		#self.lcd_expose_event(self.darea, None, self.lcdP)

	def set_2line_mode(self):
		self.mode_flag = self.mode_flag | _2LINE_MODE_FLAG

	def set_1line_mode(self):
		self.mode_flag = self.mode_flag & _2LINE_MODE_FLAG

	def set_large_font_mode(self):
		self.mode_flag = self.mode_flag | LARGE_FONT_MODE_FLAG

	def set_small_font_mode(self):
		self.mode_flag = self.mode_flag & LARGE_FONT_MODE_FLAG

	def set_display_on(self):
		self.mode_flag = self.mode_flag | DISPLAY_ON_FLAG

	def set_display_off(self):
		self.mode_flag = self.mode_flag & DISPLAY_ON_FLAG

	def set_blink_on(self):
		self.mode_flag = self.mode_flag | BLINK_ON_FLAG

	def set_blink_off(self):
		self.mode_flag = self.mode_flag & BLINK_ON_FLAG

	def set_cursor_on(self):
		self.mode_flag = self.mode_flag | CURSOR_ON_FLAG

	def set_cursor_off(self):
		self.mode_flag = self.mode_flag & CURSOR_ON_FLAG

	def in_2line_mode(self):
		return (self.mode_flag & _2LINE_MODE_FLAG) != 0

	def in_1line_mode(self):
		return (self.mode_flag & _2LINE_MODE_FLAG) == 0

	def in_large_font_mode(self):
		return (self.mode_flag & LARGE_FONT_MODE_FLAG) != 0

	def in_small_font_mode(self):
		return (self.mode_flag & LARGE_FONT_MODE_FLAG) == 0

	def display_is_on(self):
		return (self.mode_flag & DISPLAY_ON_FLAG) != 0

	def display_is_off(self):
		return (self.mode_flag & DISPLAY_ON_FLAG) == 0

def CreatePixmapFromLCDdata(lcdP, ch):
	width = lcdP.get_char_width()
	height = lcdP.get_char_height()
	pixmap = gtk.gdk.Pixmap(lcdP.darea.window, width, height)

	lcdP.lcd_gc.set_rgb_fg_color(lcdP.bg_color)

	pixmap.draw_rectangle(lcdP.lcd_gc, True, 0, 0, width, height)

	lcdP.lcd_gc.set_rgb_fg_color(lcdP.fg_color)
	for j in range(lcdP.dots['y']):
		k = j * lcdP.pixels['y']
		for i in range(lcdP.dots['x']):
			if 1<<(lcdP.dots['x']-1-i) & ch[j] == 0: continue

			m = i * lcdP.pixels['y']

			for jj in range(k, k+lcdP.pixels['y']-1):
				for ii in range(m+1, m+lcdP.pixels['x']):
					pixmap.draw_point(lcdP.lcd_gc, ii, jj)
	return pixmap
		

