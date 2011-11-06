import gtk
import gtk.glade
import subprocess

class CFSensors:
	lm = {}

	def __init__(self):
		_ = self._
		self.set_window('sensors', gtk.glade.XML ('CF635.glade', "window_sensors_view"))
		self.windows['sensors'].signal_autoconnect(self)
		self.list_store = gtk.TreeStore(str)
		self.get_sensors()
		for key in self.lm.keys():
			piter = self.list_store.append(None,[key])
			for k in self.lm[key].keys():
				self.list_store.append(piter, [('%s: %s' % (k, self.lm[key][k]))])
		_('sensors_treeview').set_model(self.list_store)

		self.tvcolumn1 = gtk.TreeViewColumn('Sensors')
		_('sensors_treeview').append_column(self.tvcolumn1)
		self.cell1 = gtk.CellRendererText()
		self.tvcolumn1.pack_start(self.cell1, True)
		self.tvcolumn1.add_attribute(self.cell1, 'text', 0)
		
	def sensors_show(self):
		self.set_current_window('sensors')
		self._('window_sensors_view').show()
		

	def get_sensors(self ):
		p = subprocess.Popen('/usr/bin/sensors',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		buffer, error = p.communicate()
		if buffer == '':
			print error
		buffer_lines = self.split_lines(buffer)
		self.lm = self.parse_lines(buffer_lines)

	def split_lines(self, buffer):
		lines = []
		while (buffer.rpartition('\n')[2] != buffer):
			buffer, _, tmp = buffer.rpartition('\n')
			lines.insert(0, tmp)
		lines.insert(0, buffer)
		return lines

	def parse_lines(self, lines):
		sensors = {}
		for c in range(0, len(lines)):
				
			if lines[c][:8] == "Adapter:":
				lbl = lines[c-1]
				sensors[lbl] = {}
				sensors[lbl]['Adapter'] = lines[c][9:]
				c=c+1
				while c<len(lines)-1 and lines[c]:
					key = lines[c][:lines[c].find(':')]
					val = lines[c][lines[c].find(':')+1:lines[c].find('(')].lstrip().rstrip().replace('\xc2\xb0', '\x80')
					sensors[lbl][key] = val
					c=c+1
		return sensors

	def on_window_sensors_view_delete_event(self, widget, data=None):
		self.set_current_window('sensors')
		self._('window_sensors_view').hide()
		return True

