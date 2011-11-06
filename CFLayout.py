import gtk
from CFLCD import LcdDisplay

class CFLayout:
	def __init__(self):
		self.set_window('layout', self.get_glade_xml("window_layout_configure"))
		self.windows['layout'].signal_autoconnect(self)
		vbox_lcd = self._('vbox_lcd')
		vbox_cgram = self._('vbox_cgram')
		lcd = gtk.DrawingArea()
		lcd.show()
		cgram = gtk.DrawingArea()
		cgram.show()
		vbox_lcd.pack_start(lcd, True, True, 0)
		vbox_cgram.pack_start(cgram, True, True, 0)
		self.lcd_view = LcdDisplay(lcd)
		self.lcd_view.CreateGraphics()
		self.chars_view = LcdDisplay(cgram)
		self.chars_view.rows = 4
		self.chars_view.cols = 2
		self.chars_view.CreateGraphics()

	def layout_configure_show(self):
		self.set_current_window('layout')
		self._("window_layout_configure").show()

	def on_window_layout_configure_delete_event(self, widget, data=None):
		widget.hide()
		return True


