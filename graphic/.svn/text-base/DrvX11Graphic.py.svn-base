import gtk, gtk.gdk, gobject

from Generic import Generic
from LCDDisplayGraphic import LCDDisplayGraphic

class DrvX11Graphic(LCDDisplayGraphic):
	def __init__(self, visitor, obj=None, config=None, key=None):
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
		LCDDisplayGraphic.__init__(self, visitor, darea, obj=obj, config=config, key=key)
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
		Generic.CFGSetup(self, key)
		self.CreateGraphics()

	def delete_event(self, widget, event=None):
		self.visitor.main_quit()


