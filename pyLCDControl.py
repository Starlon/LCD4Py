#!/usr/bin/python
import pygtk
pygtk.require("2.0")
import gtk
import gtk.gdk
import gtk.glade
import gobject
import cProfile
import pickle
import serial
import re
import os, sys
import threading
from configobj import ConfigObj

from DrvCrystalfontz import *
from DrvX11 import DrvX11
from DrvPertelian import DrvPertelian

from CFSensors import CFSensors
from CFDmesg import CFDmesg
from CFMain import CFMain
from CFPreferences import CFPreferences
from CFLCD import CFLCD
from Generic import Generic
from Threaded import *
from CFDisplay import CFDisplay
from CFWidget import CFWidget
from CFLayout import CFLayout
from WidgetText import WidgetText
from CFG import CFG

from Functions import *

windows = ['sensors', 'main', 'preferences', 'lcd', 'display', 'widget', 'layout']

gtk.gdk.threads_init()

class App(gobject.GObject, CFSensors, CFDmesg, CFMain, CFPreferences, CFLCD, CFDisplay, CFWidget, CFLayout, CFG):
	def __init__( self ):
		self.__gobject_init__()
		self.alive = True
		self.debugging = True
		self.displays = [] # List of devices
		self.current_display = -1 # Current device, -1 means no devices
		self.append = True
		self.modules = {}
		self.signals = []
		self.funcs = []
		self.windows = {}
		self.widget_template = {}
		for window in windows:
			self.windows[window] = False
		self.widgets = []
		self.current_window = ''
		self.special_chars_set_signal = gobject.signal_new("special-chars-set", Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.layout_transition_finished_signal = gobject.signal_new("layout-transition-finished", Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.special_char_changed_signal = gobject.signal_new("special-char-changed", Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
		self.layout_change_before_signal = gobject.signal_new("layout-change-before", Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.layout_change_after_signal = gobject.signal_new("layout-change-after", Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.display_disconnected_signal = gobject.signal_new('display-disconnected', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.display_disconnected_before_signal = gobject.signal_new('display-disconnected-before', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.display_connected_signal = gobject.signal_new('display-connected', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.display_changed_signal = gobject.signal_new('display-changed', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.book_changed_signal = gobject.signal_new('book-changed', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.page_changed_signal = gobject.signal_new('page-changed', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.version_ready_signal = gobject.signal_new('version-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.contrast_backlight_ready_signal = gobject.signal_new('contrast-backlight-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.packet_ready_signal = gobject.signal_new('packet-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
		self.temp_packet_ready_signal = gobject.signal_new('temperature-packet-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
		self.fan_packet_ready_signal = gobject.signal_new('fan-packet-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT])
		self.key_packet_ready_signal = gobject.signal_new('key-packet-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT])
		#self.devices_ready_signal = gobject.signal_new('devices-ready', App, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
		self.dow_ready_signal = gobject.signal_new('dow-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT])
		self.lcd_memory_ready_signal = gobject.signal_new('lcd-memory-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
		self._8bytes_packet_ready_signal = gobject.signal_new('8byte-packet-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self._8bytes_fill_start_signal = gobject.signal_new('8byte-fill-start', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		self.fans_ready_signal = gobject.signal_new('fans-ready', Generic, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		CFDmesg.__init__(self)
		CFSensors.__init__(self)
		CFMain.__init__(self)
		CFPreferences.__init__(self)
		CFLCD.__init__(self)
		CFDisplay.__init__(self)
		CFWidget.__init__(self)
		CFLayout.__init__(self)
		#self.config = cfg_get()
		CFG.__init__(self)
		self.config_setup()

	def config_setup(self):
		self.append = True
		for key in self.config.keys():

			pos = key.find('_')
			if key[:pos].lower() == 'display':
				driver = self.cfg_fetch_raw(self.config[key], 'driver', '').lower()
				model = self.cfg_fetch_raw(self.config[key], 'model', '').lower()
				if driver == 'crystalfontz':
					self.CF = DrvCrystalfontz.get(model, self, config=self.config)
				elif driver == 'x11':
					self.CF = DrvX11(self, config=self.config)
				elif driver == "pertelian":
					self.CF = DrvPertelian(self, config=self.config)
				else:
					continue
				self.CF.name  = key[pos+1:]
				self.modules[key] = self.current_display

		for key in self.modules.keys():
			device = self.displays[self.modules[key]]
			device.CFGSetup(key)
			device.Connect()
			device.SetupDevice()
			device.BuildLayouts()
			device.StartLayout()

	def find_display(self, name):
		name = 'display_' + name
		if name in self.modules:
			return self.displays[self.modules[name]]
		return None
				
	def get_display(self):
		if self.current_display < 0 or self.current_display >= len(self.displays): return None
		return self.displays[self.current_display]

	def set_display(self, val):
		if self.current_display >= len(self.displays): return None
		self.disconnect_signals()
		if self.append or self.current_display < 0:
			self.displays.append(val)
			self.current_display = self.current_display + 1
		else:
			del(self.displays[self.current_display])
			self.displays.insert(self.current_display, val)
		self.connect_signals()
		self.CF.emit('display-changed')

	def del_display(self):
		if self.current_display < 0 or self.current_display >= len(self.displays): return
		self.disconnect_signals()
		self.displays[self.current_display].TakeDown()
		if self.displays[self.current_display].Connected(): self.displays[self.current_display].Disconnect()
		del(self.displays[self.current_display])
		self.current_display = [-1, 0][len(self.displays) > 0]
		if self.CF: self.connect_signals(); self.CF.emit('display-changed')
		
	CF = property(get_display, set_display, del_display, "Displays encapsulated - use set_current_display to change the pointer.")

	def _(self, key):
		if self.current_window not in self.windows.keys(): self.debug("No window in _ : " + self.current_window); return None
		return self.windows[self.current_window].get_widget(key)

	def get_glade_xml(self, id):
		return gtk.glade.XML ( 'CF635.glade', id)

	def set_current_display(self, index):
		self.disconnect_signals()
		self.current_display = index
		self.connect_signals()
		self.CF.emit('display_changed')
	
	def add_display(self, display):
		self.disconnect_signals()
		self.displays.append(display)
		self.current_display = len(self.displays)-1
		self.connect_signals()
		self.execute_funcs()
		self.CF.emit('display_changed')

	def set_current_book(self, index):
		if not self.CF: return
		self.CF.current_book = index
		self.CF.emit('book-changed')

	def add_book(self, book):
		if not self.CF: return
		self.CF.books.append(book)
		self.CF.current_book = len(self.CF.books)-1
		self.CF.emit('book-changed')

	def set_current_page(self, index):
		if not self.CF or not self.CF.book: return
		self.CF.book.current_page = index
		self.CF.emit('page-changed')

	def add_page(self, page):
		if not self.CF or not self.CF.book: return
		self.CF.book.pages.append(page)
		self.CF.book.current_page = len(self.CF.book.pages)-1
		self.CF.emit('page-changed')

	def connect_signals(self):
		for i in range(0, len(self.signals)):
			self.signals[i][2] = self.CF.connect(self.signals[i][0], self.signals[i][1])

	def disconnect_signals(self):
		for i in range(0, len(self.signals)):
			if self.signals[i][2] != None and self.CF.handler_is_connected(self.signals[i][2]):
				self.CF.handler_disconnect(self.signals[i][2])

	def execute_funcs(self):
		for i in range(0, len(self.funcs)):
			self.funcs[i][0](*self.funcs[i][1])
					

	def add_signal(self, signal, func):
		self.signals.append([signal, func, None]) # signal, func, memory, signal object

	def remove_signal(self, signal):
		i = len(self.signals) - 1 
		while i > 0:
			if self.signals[i][0] == signal:
				self.CF.handler_disconnect(self.signals[i][2])
				del(self.signals[i])
			i = i - 1
				

	def add_func(self, func, *args):
		self.funcs.append([func, args])

	def set_current_window(self, key):
		self.current_window = key

	def set_window(self, key, window):
		self.current_window = key
		self.windows[key] = window

	def main_quit(self):
		while self.CF: del(self.CF)
		gtk.main_quit()

	def start( self, withGtk=True):
		if withGtk:
			gtk.gdk.threads_enter()
			gtk.main()
			gtk.gdk.threads_leave()
		else:
			loop = gobject.MainLoop()
			loop.run()

	def debug( self, txt ):
		if self.debugging: print txt

import gc
#gc.set_debug(gc.DEBUG_LEAK)
app = App()
#sys.setcheckinterval(100)
try: cProfile.run('app.start()')
except:
	while app.CF:
		del(app.CF)

