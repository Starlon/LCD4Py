import time
import re
import gtk
import gtk.glade
#from CFModule import *
#from CFBook import *
#from CFPage import *
from ThreadedTask import ThreadedTask

class CFMain:
	def __init__(self):
		self.set_window('main', self.get_glade_xml("window_main"))
		self.windows['main'].signal_autoconnect(self)
		self.lbl_firmware_version = self._('label_firmware_version')
		self.lbl_hardware_version = self._('label_hardware_version')
		self.adjust_backlight = gtk.Adjustment(upper=110, step_incr=1, page_incr=9, page_size=10)
		self.adjust_contrast = gtk.Adjustment(upper=265, step_incr=1, page_incr=9, page_size=10)

		self._('hscale_lcd_contrast').set_adjustment(self.adjust_contrast)
		self._('hscale_lcd_brightness').set_adjustment(self.adjust_backlight)
		
		self.menu_popup = self.get_glade_xml( 'menu_popup')
		self.menu_popup.signal_autoconnect(self)
		self.menu_popup = self.menu_popup.get_widget("menu_popup")
		self.icon = gtk.status_icon_new_from_file("icon.png")
		self.icon.connect('popup-menu', self.icon_popup_menu)
		self._('treeview_displays').set_headers_visible(False)
		self._('treeview_widgets').set_headers_visible(False)
		self._('treeview_layouts').set_headers_visible(False)

		#Modules
		self.displays_tree_store = gtk.TreeStore(str)
		self._('treeview_displays').set_model(self.displays_tree_store)
		column =  gtk.TreeViewColumn('')
		self._('treeview_displays').append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
		self._('treeview_displays').connect('cursor-changed', self.displays_cursor_changed)

		#Books
		self.widgets_tree_store = gtk.TreeStore(str)
		self._('treeview_widgets').set_model(self.widgets_tree_store)
		column = gtk.TreeViewColumn()
		self._('treeview_widgets').append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
		self._('treeview_widgets').connect('cursor-changed', self.widgets_cursor_changed)

		#Pages
		self.layouts_tree_store = gtk.TreeStore(str)
		self._('treeview_layouts').set_model(self.layouts_tree_store)
		column = gtk.TreeViewColumn()
		self._('treeview_layouts').append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
		self._('treeview_layouts').connect('cursor-changed', self.layouts_cursor_changed)

		#self.add_signal('version-ready', self.on_version_ready)
		#self.add_signal('contrast-backlight-ready', self.on_contrast_backlight_ready)
		#self.add_signal('display-changed', self.on_display_change)
		#self.add_signal('8byte-packet-ready', self.on_8byte_packet_ready)
		#self.add_signal('8byte-fill-start', self.on_8byte_fill_start)

	def on_8byte_fill_start(self, data=None):
		self.set_current_window('main')
		self._('entry_command_rate').set_text(str(self.CF.command_rate))
		self._('entry_response_timeout').set_text(str(self.CF.response_timeout))
		self._('window_main').queue_draw()

	def on_8byte_packet_ready(self, data=None):
		self.set_current_window('main')
		label_memory_ready = self._('label_memory_ready')
		progressbar_memory_ready = self._('progressbar_memory_ready')
		t = time.time()-self.CF.memory.initiation_time
		label_memory_ready.set_text("%.2f" % (t))
		val = self.CF.memory.accum/20.0
		progressbar_memory_ready.set_fraction(val)
		if val == 1: progressbar_memory_ready.set_text("Completed...")
		else: progressbar_memory_ready.set_text("Please wait...")
		self._('label_commands_resent').set_text(str(self.CF.commands_resent))
		self._('label_tossed_bytes').set_text(str(self.CF.tossed))
		self._("window_main").queue_draw()

	def on_display_change(self, data=None):
		self.on_version_ready()
		self.on_contrast_backlight_ready()		

	def on_version_ready(self, data=None):
		self.lbl_firmware_version.set_text( self.CF.firmware_version )
		self.lbl_hardware_version.set_text( self.CF.hardware_version )

	def on_contrast_backlight_ready(self, data=None):
		self.set_current_window('main')
		self._('hscale_lcd_contrast').set_value(self.CF.contrast)
		self._('hscale_lcd_brightness').set_value(self.CF.backlight)
		

	#def quit_cb(self, action):
	#	self.main_quit()
	
	#def open_cb(self, action):
	#	self.main_show()

	def main_show(self):
		self.set_current_window('main')
		self._('window_main').show()

	def displays_cursor_changed(self, treeview):
		self.set_current_window('main')
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		self.set_current_display(path[0])
		self.disconnect_signals()
		self.connect_signals()
		if self.CF and self.CF.widget: 
			self.set_current_widget(-1)
			if self.CF.widget.layout:
				self.set_current_layout(-1)

	def widgets_cursor_changed(self, treeview):
		self.set_current_window('main')
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		if not iter: return
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		self.set_current_widget(path[0])
		if self.CF and self.CF.widget and self.CF.widget.layout:
			self.set_current_layout(-1)

	def layouts_cursor_changed(self, treeview):
		self.set_current_window('main')
		treeselectionn = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		if not iter: return
		treeselection = treeview.get_selection()
		(model, iter) = treeselection.get_selected()
		path = model.get_path(iter)
		self.set_current_layout(path[0])

	def icon_popup_menu(self, status_icon, button, activate_time):
		self.menu_popup.popup(None, None, None, button, activate_time)

	def on_window_main_delete_event(self, widget, data=None):
		widget.hide()
		return True

	def on_button_display_new_clicked(self, widget):
		dialog_name = self.get_glade_xml("dialog_name")

		def ok(widget):
			name = dialog_name.get_widget("entry_name").get_text()
			dialog_name.get_widget('dialog_name').destroy()
			tmp = CF635(self)
			tmp.display_name = name
			self.add_display(tmp)
			iter = self.displays_tree_store.append(None,[name])
			selection = self._("treeview_displays").get_selection()
			selection.select_iter(iter)
			self.set_current_window('main')
			self._('window_main').queue_draw()

		dialog_name.get_widget('button_ok').connect('clicked', ok)
		dialog_name.get_widget('entry_name').set_activates_default(True)
		dialog_name.get_widget("label_name").set_text("Give the display a name")

		def cancel(widget):
			dialog_name.get_widget('dialog_name').destroy()

		dialog_name.get_widget('button_cancel').connect('clicked', cancel)
		dialog_name.get_widget('dialog_name').show()

	def on_button_display_configure_clicked(self, widget):
		self.set_current_window('main')
		treeselection = self._('treeview_displays').get_selection()
		(model, iter) = treeselection.get_selected()
		if not iter: return
		self.display_configure_show()

	def on_button_display_delete_clicked(self, widget):
		pass

	def on_button_widget_new_clicked(self, widget):
		if not self.CF: return
		dialog_name = self.get_glade_xml("dialog_name")

		def ok(widget):
			name = dialog_name.get_widget("entry_name").get_text()
			dialog_name.get_widget("dialog_name").destroy()
			self.add_widget(Book(self.CF))
			iter = self.widgets_tree_store.append(None, [name])
			self.set_current_window('main')
			selection = self._("treeview_widgets").get_selection()
			selection.select_iter(iter)
			self._("window_main").queue_draw()

		dialog_name.get_widget("button_ok").connect("clicked", ok)
		dialog_name.get_widget("entry_name").set_activates_default(True)
		dialog_name.get_widget("label_name").set_text("Give the widget a name")

		def cancel(widget):
			dialog_name.get_widget("dialog_name").destroy()

		dialog_name.get_widget("button_cancel").connect("clicked", cancel)
		dialog_name.get_widget("dialog_name").show()

	def on_button_widget_configure_clicked(self, widget):
		pass

	def on_button_widget_delete_clicked(self, widget):
		pass

	def on_button_layout_new_clicked(self, widget):
		if not self.CF or not self.CF.widget: return
		dialog_name = self.get_glade_xml("dialog_name")

		def ok(widget):
			name = dialog_name.get_widget("entry_name").get_text()
			dialog_name.get_widget("dialog_name").destroy()
			self.add_layout(Page(self.CF))
			iter = self.layouts_tree_store.append(None, [name])
			self.set_current_window("main")
			selection = self._("treeview_layouts").get_selection()
			selection.select_iter(iter)
			self._("window_main").queue_draw()

		dialog_name.get_widget("button_ok").connect("clicked", ok)
		dialog_name.get_widget("entry_name").set_activates_default(True)
		dialog_name.get_widget("label_name").set_text("Give the layout a name")

		def cancel(widget):
			dialog_name.get_widget("dialog_name").destroy()

		dialog_name.get_widget("button_cancel").connect("clicked", cancel)
		dialog_name.get_widget("dialog_name").show()
		

	def on_button_layout_configure_clicked(self, widget):
		self.set_current_window('main')
		self.layout_configure_show()

	def on_button_layout_delete_clicked(self, widget):
		pass

	def on_button_memory_read_view_clicked(self, widget):
		self.lcd_show()

	def on_button_memory_read_restart_clicked(self, widget):
		self.set_current_window('main')
		progressbar_memory_ready = self._('progressbar_memory_ready')
		progressbar_memory_ready.set_fraction(0)
		progressbar_memory_ready.set_text('Please wait...')
		self._("window_main").queue_draw()
		command_rate = self._("entry_command_rate").get_text()
		try:
			command_rate = int(command_rate)
			#gobject.source_remove(self.CF.timeout_command_rate_id)
			#self.CF.timeout_command_rate_id = gobject.timeout_add(self.CF.command_rate, self.CF.command_worker)
		except ValueError, e:
			print e
		else:
			self.CF.command_rate = command_rate
			self.CF.command_rate_thread.stop()
			self.CF.command_rate_thread = ThreadedTask(self.CF.command_worker, None, command_rate)
			self.CF.command_rate_thread.start()
		response_timeout = self._("entry_response_timeout").get_text()
		try:
			response_timeout = float(response_timeout)
		except ValueError, e:
			print e
		else:
			self.CF.response_timeout = response_timeout
		print type(command_rate).__name__, type(response_timeout).__name__
		self.CF.memory.restart()

	def on_hscale_lcd_brightness_value_changed(self, widget):
		if not self.CF: return
		self.CF.backlight = int(widget.get_value())

	def on_hscale_lcd_contrast_value_changed(self, widget):
		if not self.CF: return
		self.CF.contrast = int(widget.get_value())

	def on_menuitem_popup_open_manager_activate(self, widget, data=None):
		print "Open manager"
		self.main_show()

	def on_menuitem_popup_quit_activate(self, widget):
		self.main_quit()
	
	def on_imagemenuitem_about_activate(self, widget):
		w = self.get_glade_xml("dialog_about")
		dialog = w.get_widget('dialog_about')
		def ok(widget):
			dialog.destroy()
		w.get_widget('button_ok').connect('clicked', ok)
		dialog.show()

	#def on_menuitem_fans_activate(self, widget):
	#	self.fans_show()

	#def on_menuitem_dallas_activate(self, widget):
	#	self.dallas_show()

	#def on_menuitem_lines_activate(self, widget):
	#	self.lines_show()

	#def on_menuitem_keys_activate(self, widget):
	#	self.keys_show()

	def on_menuitem_sensors_activate(self, widget):
		self.sensors_show()

	#def on_menuitem_backlight_and_contrast_activate(self, widget):
	#	self.backlight_and_contrast_show()

	def on_imagemenuitem_preferences_activate(self, widget):
		self.preferences_show()

	def on_imagemenuitem_quit_activate(self, widget):
		self.main_quit()

	def on_menuitem_close_activate(self, widget):
		self.set_current_window('main')
		self._('window_main').hide()

	def on_menuitem_quit_activate(self, widget):
		self.main_quit()

	def on_entry_response_timeout_insert_at_cursor(self, text):
		print "Response timeout insert"
		return self.is_valid_value(text)

	def on_entry_command_rate_insert_at_cursor(self, text):
		print "Command rate insert"
		return self.is_valid_value(text)

	def is_valid_value(self, text):
		m = re.match('[0-9\.]*', text)
		if m: return True
		return False
