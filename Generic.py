import time
import gobject

from Widget import *
from WidgetText import WidgetText
from WidgetBar import WidgetBar
from WidgetHistogram import WidgetHistogram
from WidgetIcon import WidgetIcon
from WidgetBigNumbers import WidgetBigNumbers
from WidgetGif import WidgetGif
from WidgetKey import WidgetKey
from WidgetTimer import WidgetTimer

from Evaluator import Evaluator
from CFG import CFG

from Functions import *
from Constants import *

class Generic(gobject.GObject, CFG, Evaluator):
	
	def __init__ ( self, visitor, obj=None, config=None, type=TYPE_TEXT):
		"""___init___ () - Inits the driver
		"""
		self.__gobject_init__()
		self.visitor = visitor
		if obj == None:
			self.layouts = {}
			self.widgets = {}
			self.static_widgets = []
			self.fake = False
			self.ser = None
			self.display_name = ''
			self.serial_number = ''
		else:
			self.layouts = obj.layouts
			self.fake = obj.fake
			self.ser = obj.ser
			self.display_name = obj.display_name
			self.device_name = obj.device_name
			self.path = obj.path
			self.books = obj.books
			self.current_command = obj.current_command
			self.command_queue0 = obj.command_queue0
			self.command_queue1 = obj.command_queue1
			self.response_time_init = time.time()
		self.TYPE = type
		self.current_layout = None
		self.app = visitor
		#self.debug = visitor.debug
		self.layoutG = self.GetLayout()
		self.current_incr = 0
		self.layout_id = None
		self.transition_id = None
		CFG.__init__(self, config)
		Evaluator.__init__(self)
		self.connect("layout-transition-finished", self.StartLayout)
		self.AddFunction("transition", 1, self.my_transition)

	def my_transition(self, result, arg1):
		self.SetResult(result, R_STRING, "")
		val = self.R2N(arg1)
		self.layoutG = self.GetLayout(val)
		if self.layout_id is not None:
			gobject.source_remove(self.layout_id)
			self.layout_id = None
		self.change_layout()

	def CFGVariablesSetup(self):
		variables = self.cfg_fetch_raw(self.config, "variables")
		if variables is not None:
			for varKey in variables.keys():
				_type = self.cfg_fetch_raw(variables[varKey], "type")
				if _type == "number":
					val = self.cfg_fetch_num(variables, "value", 0)
					self.SetVariableNumeric(varKey, val)
				elif _type == "string":
					val = self.cfg_fetch(variables, "value", '')
					self.SetVariableString(varKey, val)
				else:
					error("Variable doesn't have a valid type - string or number allowed: %s" % (varKey))

	def CFGSetup(self, key=None):
		if key is None:
			key = self.key
		else:
			self.key = key
		layout = self.cfg_fetch_raw(self.config[key], 'layout', "default")
		self.layouts = {}
		self.layouts[layout] = []
		layout = self.cfg_fetch_raw(self.config[key], "layout0")
		i = 1
		while layout is not None:
			self.layouts[layout] = []
			layout = self.cfg_fetch_raw(self.config[key], "layout%g" % (i))
			i = i + 1

		widget = self.cfg_fetch_raw(self.config[key], "widget0")

		i = 1
		while widget is not None:
			self.static_widgets.append(widget)
			widget = self.cfg_fetch_raw(self.config[key], "widget%g" % i)
			i = i + 1

		for lkey in self.layouts.keys():
			layout = self.cfg_fetch_raw(self.config, lkey)
			if not layout: continue
			for row in range(self.rows+1):
				cfg_row = self.cfg_fetch_raw(layout, "row%d" % (row))
				if not cfg_row: continue
				for col in range(self.cols+1):
					cfg_col = self.cfg_fetch_raw(cfg_row, "col%d" % (col))
					if not cfg_col: continue
					self.layouts[lkey].append([cfg_col, row, col])


	def BuildLayouts(self, data=None):
		self.widgets = {}
		for key in self.layouts.keys():
			for w in self.layouts[key]:
				widget_template = self.cfg_fetch_raw(self.config, w[0])
				if not widget_template: 
					error("No widget named <%s>" % (w[0]))
					continue
				_type = self.cfg_fetch_raw(widget_template, "type")
				if not _type:
					error("Widget <%s> has no type!" % (w[0]))
					continue

				widget = None
				name = key + ':' + w[0]
				i = 0
				tmp = name + ":" + str(i)
				while tmp in self.widgets.keys():
					i = i + 1
					tmp = name + ":" + str(i)
				name = tmp
				if _type.lower() == 'text': 
					widget = WidgetText(self, name, widget_template, w[1]-1, w[2]-1)
				elif _type.lower() == 'bar':
					widget = WidgetBar(self, name, widget_template, w[1]-1, w[2]-1)
				elif _type.lower() == "histogram":
					widget = WidgetHistogram(self, name, widget_template, w[1]-1, w[2]-1)
				elif _type.lower() == "icon":
					widget = WidgetIcon(self, name, widget_template, w[1]-1, w[2]-1)
				elif _type[:6].lower() == "bignum":
					widget = WidgetBigNumbers(self, name, widget_template, w[1]-1, w[2]-1)
				elif _type.lower() == 'gif':
					widget = WidgetGif(self, name, widget_template, w[1]-1, w[2]-1)
				else:
					error("Unknown widget type: %s" % _type)
				if widget:
					self.widgets[name] = widget

		for widget in self.static_widgets:

			widget_template = self.cfg_fetch_raw(self.config, widget)
			if widget_template is None:
				error("No widget named <%s>" % widget)
				continue
			_type = self.cfg_fetch_raw(widget_template, "type")
			if _type is None:
				error("Widget <%s> has no type!" % widget)
				continue
			w = None
			if _type.lower() == 'key':
				w = WidgetKey(self, widget, widget_template)
			elif _type.lower() == 'timer':
				w = WidgetTimer(self, widget, widget_template)
			else:
				error("Unknown type <%s> for display widget <%s>" % (_type, widget))
			if w:
				self.widgets[widget] = w


	def StartLayout(self, data=None):
		if self.transition_id is not None:
			gobject.source_remove(self.transition_id)
			self.transition_id = None
		self.emit("layout-change-before")
		if hasattr(self, "text_clear"):
			self.text_clear()
		elif hasattr(self, "graphic_clear"):
			self.graphic_clear()
		key = self.current_layout = self.layoutG.next()
		while key is None:
			key = self.current_layout = self.layoutG.next()
		#self.chars = [[0 for i in range(self.YRES)] for j in range(self.CHARS)]
		#self.text_set_special_chars()
		for widget in self.widgets.keys():
			if self.widgets[widget].type == WIDGET_TYPE_RC:
				if strncmp(widget, key, len(key)) == 0:
					c = type(self.widgets[widget]).__name__
					if hasattr(self, "CHARS") and hasattr(self.widgets[widget], "setup_chars"):
						self.widgets[widget].setup_chars()
					self.widgets[widget].start() 
			elif self.widgets[widget].type == WIDGET_TYPE_TIMER \
				or self.widgets[widget].type == WIDGET_TYPE_KEYPAD:
				self.widgets[widget].start()
		layout = self.cfg_fetch_raw(self.config, key) 
		timeout = self.cfg_fetch_num(layout, "timeout", self.layout_timeout) or 0
		if timeout != 0 and len(self.layouts) > 1:
			self.layout_id = gobject.timeout_add(timeout, self.change_layout)
		self.emit("layout-change-after")

	def GetLayout(self, incr=None):
		keys = self.layouts.keys()
		keys.sort()
		if incr is not None:
			i = int(self.current_incr + incr)
			if i < 0:
				i = len(keys) - 1
			elif i >= len(keys):
				i = 0
		else:
			i = 0
		while True:
			while i < len(keys):
				self.current_incr = i
				yield keys[i]
				i = i + 1
				if i >= len(keys):
					i = 0

	def StopLayout(self):
		for key in self.widgets.keys():
			if strncmp(key, self.current_layout, len(self.current_layout)) == 0:
				self.widgets[key].stop()
				#self.disconnect(self.widgets[key].id_signal)	

	def change_layout(self, t=None):
		self.StopLayout()
		layout = self.cfg_fetch_raw(self.config, self.current_layout)
		if t is None:
			transition = self.cfg_fetch_raw(layout, "transition")
		else:
			transition = t
		if transition is None or self.TYPE == TYPE_GRAPHIC:
			self.StartLayout()
		else:
			self.StartTransition(transition.upper())

		self.layout_id = None

	def StartTransition(self, transition):
			if self.transition_id == None:
				self.transition_tick = 0
				self.transition_id = gobject.timeout_add(100, self.layout_transition, transition)
			self.layout_transition(transition)
				
	def SetupDevice(self):
		#print "Generic.SetupDevice"
		pass

	def TakeDown(self):
		#print "Generic.TakeDown"
		pass

		
