import gtk
import gtk.glade
from DrvCrystalfontz import *

class CFDisplay:
	def __init__(self):
		self.dow_map =  []
		self.set_window('display', self.get_glade_xml("window_display_configure"))
		self.windows['display'].signal_autoconnect(self)
		speed = self._('combobox_speed')
		model = gtk.ListStore(gobject.TYPE_STRING)
		cell = gtk.CellRendererText()
		speed.pack_start(cell, True)
		speed.add_attribute(cell, 'text', 0)
		speed.set_model(model)
		speed.append_text('19200')
		speed.append_text('115200')
		speed.set_active(1)
		self.add_signal('display-connected', self.display_connected)
		self.add_signal('display-disconnected', self.display_disconnected)
		self.add_signal('dow-ready', self.dow_ready)
		self.add_func(self.setup_display)

		self.treeview_index = 0
		treeview = self._('treeview_temp_sensors')
		self.treestore_temp_sensors = gtk.TreeStore(str, str, str, str, str)
		treeview.set_model(self.treestore_temp_sensors)

		column =  gtk.TreeViewColumn('Index')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)

		column = gtk.TreeViewColumn('Unique ID')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 1)

		column = gtk.TreeViewColumn('Name')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		cell.set_property('editable', True)
		cell.connect('edited', self.name_edited, self.treestore_temp_sensors)
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 2)

		column = gtk.TreeViewColumn('Centigrade')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 3)

		column = gtk.TreeViewColumn('Fahrenheit')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 4)

		for i in range(0, 4):
			cb_ppr = self._('combobox_fan' + str(i+1) + '_ppr')
			cb_glitch = self._('combobox_fan' + str(i+1) + '_glitch')
			model = gtk.ListStore(gobject.TYPE_STRING)
			cell = gtk.CellRendererText()
			cb_ppr.pack_start(cell, True)
			cb_ppr.add_attribute(cell, 'text', 0)
			cb_ppr.set_model(model)
			model = gtk.ListStore(gobject.TYPE_STRING)
			cell = gtk.CellRendererText()
			cb_glitch.pack_start(cell, True)
			cb_glitch.add_attribute(cell, 'text', 0)
			cb_glitch.set_model(model)			
			for j in range(0, 32):
				cb_ppr.append_text(str(j+1))
			for j in range(0, 255):
				cb_glitch.append_text(str(j+1))
		
	def setup_display(self):
		pass
		#if not self.CF.Connected(): 
		#	self.CF.Connect(self.CF.port, self.CF.baud)
		#	self.CF.SetupDevice()

	def dow_ready(self, device, index):
		print "DOW ready - index:", index
		dow = self.CF.dallas[index]
		self.treestore_temp_sensors.append(None, [str(dow['i']), dow['id'], '', str(dow['degc']), str(dow['degf'])])
		self.dow_map.append(dow['i'])
		self.set_current_window('display')
		self._('window_display_configure').queue_draw()

	def name_edited(self, cell, path, new_text, liststore):
		self.CF.dallas[ord(liststore[path][0])]['name'] = new_text
		liststore[path][2] = new_text

	def handle_temperature_packet(self, device, index):
		if device != self.CF: return
		for i in range(0, len(self.dow_map)):
			if index == self.dow_map[i]:
				self.treestore_temp_sensors[i][3] = self.CF.dallas[index]['degc']
				self.treestore_temp_sensors[i][4] = self.CF.dallas[index]['degf']

		self.set_current_window('display')
		self._('window_display_configure').queue_draw()
			

        def handle_fan_packet(self, device, fan):
		#if device != self.CF: return
		rpm = self.CF.fans[fan]['rpm']
		self.set_current_window('display')
		self._('label_fan' + str(fan+1) + '_rpm').set_text(str(rpm))
		self._('progressbar_fan' + str(fan+1) + '_rpm').set_fraction(rpm/2000.0)
		self._('window_display_configure').queue_draw()
		return True

	def on_fans_ready(self, device):
		print "On fans ready------------------------", device
		self.set_current_window('display')
		for i in range(0, 4):
			cb_glitch = self._('combobox_fan' + str(i+1) + '_glitch')
			cb_ppr = self._('combobox_fan' + str(i+1) + '_ppr')
			vs_power = self._('vscale_fan' + str(i+1) + '_power')
			cb_glitch.set_active(self.CF.fans[i]['glitch']-1)
			cb_ppr.set_active(self.CF.fans[i]['ppr']-1)
			vs_power.set_value(self.CF.fans[i]['power'])
			
		self._('window_display_configure').queue_draw()
	
	def display_connected(self, data=None):
		self.execute_funcs()

	def display_disconnected(self, data=None):
		print "Display disconnected", data
		pass

	def display_configure_show(self):
		self.set_current_window('display')
		self._('window_display_configure').show()

	#def devices_cursor_changed(self, treeview):
	#	self.set_current_window('display')
	#	treeselection = treeview.get_selection()
	#	(model, iter) = treeselection.get_selected()
	#	model = treeview.get_model()
	#	path = model.get_path(iter)
		

	def on_checkbutton_enable_scab_toggled(self, widget):
		if not self.CF: return
		self.append = False
		print "click"
		#reconnect = False
		#tmp = self.CF
		reconnect = False
		if self.CF.Connected(): 
			self.CF.Disconnect() 
			reconnect = True
		self.CF.TakeDown()
		self.disconnect_signals()
		if widget.get_active():
			self.add_signal('fan-packet-ready', self.handle_fan_packet)
			self.add_signal('temperature-packet-ready', self.handle_temperature_packet)
			self.add_signal('fans-ready', self.on_fans_ready)
			self.CF = SCAB(self, self.CF)
		else:
			self.remove_signal('fan-packet-ready')
			self.remove_signal('temperature-packet-ready')
			self.remove_signal('fans-ready')
			self.CF = CF635(self, self.CF)
				
		self.connect_signals()
		if reconnect and not self.CF.Connect(self.CF.port, self.CF.baud):
			return
		self.CF.SetupDevice()

	def on_button_reboot_clicked(self, widget):
		if not self.CF: return
		self.CF.Reboot()

	def on_window_display_configure_delete_event(self, widget, data):
		widget.hide()
		return True

	def on_button_device_open_clicked(self, widget):
		self.set_current_window('display')
		speed = self._('combobox_speed')
		entry_device = self._('entry_serial_device')
		dialog = self.get_glade_xml('dialog_choose_device')
		window = dialog.get_widget('dialog_choose_device')
		treeview = dialog.get_widget('treeview_device_selection')
		filechooser = dialog.get_widget('filechooser_device')
		button_ok = dialog.get_widget('button_device_ok')
		button_cancel = dialog.get_widget('button_device_cancel')
		
		filechooser.set_current_folder('/dev')
		filter = gtk.FileFilter()
		filter.set_name("Serial Devices")
		filter.add_pattern("ttyS*")
		filter.add_pattern("ttyUSB*")
		filechooser.add_filter(filter)

		tree_store = gtk.TreeStore(str, str)
		treeview.set_model(tree_store)
		column =  gtk.TreeViewColumn('Serial Number')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
		column = gtk.TreeViewColumn('Serial Device')
		treeview.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 1)

		for i in range(0, len(self.hints_index)):
			number = self.hints[self.hints_index[i]]['serial_number']
			device = self.hints[self.hints_index[i]]['serial_device']
			tree_store.append(None, [number, device])

		def ok(widget):
			treeselection = treeview.get_selection()
			(model, iter) = treeselection.get_selected()
			if iter:
				model = treeview.get_model()
				path = model.get_path(iter)
				file = "/dev/" + self.hints[self.hints_index[path[0]]]['serial_device']
				serial_number = self.hints_index[path[0]]['serial_number']
			else:
				file = filechooser.get_filename()
				serial_number = ''
			window.destroy()
			self.CF.baud = (19200, 115200)[speed.get_active()]
			self.CF.port = file
			self.CF.serial_number = serial_number
			entry_device.set_text(file)
			self._('window_display_configure').queue_draw()

			def f(packet):
				self.set_current_window('display')
				context_id = self._('statusbar_device_status').get_context_id("version-response")
				self._('statusbar_device_status').push(context_id, "Connected to %s" % (packet.data))

			if self.CF.Connect(file, self.CF.baud):
				self.CF.SetupDevice()
				self.CF.GetVersion(f)
				context_id = self._('statusbar_device_status').get_context_id("connected")
				self._('statusbar_device_status').push(context_id, "Connected...")
			else:
				context_id = self._('statusbar_device_status').get_context_id("connection-failed")
				self._('statusbar_device_status').push(context_id, "Could not connect")

		def cancel(widget):
			window.destroy()

		button_ok.connect('clicked', ok)
		button_cancel.connect('clicked', cancel)

		dialog.get_widget('dialog_choose_device').show()

