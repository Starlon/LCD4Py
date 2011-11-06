import gtk, gtk.gdk, gobject

from Generic import Generic
from LCDDisplay import LCDDisplay

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

class DrvX11(LCDDisplay):
	def __init__(self, visitor, obj=None, config=None):
		self.visitor = visitor
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.set_default_size(1,1)
		window.show()
		window.connect("delete_event", self.delete_event)
		darea = gtk.DrawingArea()
		darea.show()
		hbox = gtk.HBox()
		hbox.show()
		window.add(hbox)
		hbox.pack_start(darea, False, False, 0)

		vbox = gtk.VBox()
		vbox.show()
		hbox.pack_start(vbox, False, False, 0)
		
		up = gtk.Button("Up")
		up.show()
		up.connect("clicked", self.button_up)
		down = gtk.Button("Down")
		down.show()
		down.connect("clicked", self.button_down)
		vbox.pack_start(up, True, True, 0)
		vbox.pack_start(down, True, True, 0)

		self.window = window
		LCDDisplay.__init__(self, darea, obj=obj, config=config)
		self.layout_timeout = 0

	def button_up(self, widget):
		self.emit('key-packet-ready', 1)

	def button_down(self, widget):
		self.emit('key-packet-ready', 2)

	def Connect(self):
		pass

	def Connected(self):
		return False

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		self.CFGVariablesSetup()
		self.rows = self.cfg_fetch_num(self.config[key], 'rows', 4)
		self.cols = self.cfg_fetch_num(self.config[key], 'cols', 20)
		self.text_init(self.rows, self.cols)
		self.CreateGraphics()
		Generic.CFGSetup(self, key)

	def delete_event(self, widget, event=None):
		self.visitor.main_quit()

