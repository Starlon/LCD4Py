import time
import threading

from Buffer import Buffer
from WidgetBar import STYLE_NORMAL, STYLE_HOLLOW

from Functions import error
from Constants import *

class Text:
	def __init__(self, rows, cols, yres, xres, goto, chars, char0):
		self.LayoutFB = Buffer()
		self.DisplayFB = Buffer()
		self.text_init(rows, cols)
		self.YRES = yres
		self.XRES = xres
		self.GOTO_COST = goto
		self.CHARS = chars
		self.CHAR0 = char0
		self.chars = []
		self.update_chars = False
		self.transition_tick = 0
		self.transitioning = False
		self.connect("layout-change-before", self.layout_change_before)
		self.connect("layout-change-after", self.text_set_special_chars)
		self.connect("special-char-changed", self.text_special_char_changed)
		#self.L2D = []
		#self.text_resizeFB(self.DROWS, self.DCOLS)
	
	#def text_resizeFB(self, rows, cols):
	#	n = rows * cols
	#	if n < len(self.LayoutFB.buffer):
	#		return
	#	for x in range(len(self.LayoutFB.buffer)-1, n):
	#		self.LayoutFB.append(' ')
	#		#self.L2D.append(' ')
	#	self.LROWS = rows
	#	self.LCOLS = cols
	def text_init(self, rows, cols):
		self.LROWS = self.DROWS = rows
		self.LCOLS = self.DCOLS = cols
		self.LayoutFB.buffer = ' ' * rows * cols
		self.DisplayFB.buffer = ' ' * rows * cols

	def layout_change_before(self, data=None):
		self.chars = []

	def layout_change_after(self, data=None):
		self.text_set_special_chars()

	def text_set_special_chars(self, data=None):
		for i in range(len(self.chars)):
			if i >= self.CHARS:
				error("Too many chars to process. Expected %g, got %g" % (self.CHARS, len(self.chars)))
				break
			self.SetSpecialChar(i, self.chars[i])
		self.emit("special-chars-set")

	def layout_transition(self, direction):
		self.transitioning = True
		for row in range(self.LROWS):
			n = row * self.LCOLS
			if direction == 'W' or (direction == 'B' and row % 2 == 0):
				col = self.LCOLS-self.transition_tick - 1
			elif direction == 'E' or direction == 'B':
				col = self.transition_tick
			else:
				error("Unknown transition <%s>: Use W(est), E(ast) or B(oth)" % direction)
				col = 0
			self.LayoutFB[n + col:n + self.LCOLS] = ' ' + self.LayoutFB[n + col + 1:n + self.LCOLS]

		self.transition_tick = self.transition_tick + 1
		if self.transition_tick > self.LCOLS:
			self.transition_tick = 0
			self.transitioning = False
			self.emit('layout-transition-finished')
			return None

		self.text_blit(0, 0, self.LROWS, self.LCOLS)
		return True
				

	def text_special_char_changed(self, obj, ch):
		if ch >= self.CHARS:
			return
		self.SetSpecialChar(ch, self.chars[ch])

	def text_blit(self, row, col, height, width):
		lr = row
		while lr < self.LROWS and lr < row + height:
			dr = lr
			if dr < 0 or dr >= self.DROWS:
				lr = lr + 1
				continue
			lc = col
			while lc < self.LCOLS and lc < col + width:
				dc = lc
				if dc < 0 or dc >= self.DCOLS:
					lc = lc + 1
					continue
				if self.DisplayFB[dr * self.DCOLS + dc] == self.LayoutFB[lr * self.LCOLS + lc]:
					lc = lc + 1
					continue
				p1 = dc
				p2 = p1
				eq = 0
				lc = lc + 1
				while lc < self.LCOLS and lc < col + width:
					dc = lc
					if dc < 0 or dc >= self.DCOLS: 
						lc = lc + 1
						continue
					if self.DisplayFB[dr * self.DCOLS + dc] == self.LayoutFB[lr * self.LCOLS + lc]:
						eq = eq + 1
						if eq > self.GOTO_COST: break
					else:
						p2 = dc
						eq = 0
					lc = lc + 1
				self.DisplayFB[dr * self.DCOLS + p1: dr * self.DCOLS + p1 + p2 - p1 + 1] = self.LayoutFB[lr * self.LCOLS + p1: lr * self.LCOLS + p1 + p2 - p1 + 1]
				if hasattr(self, 'real_write'):
					self.real_write(dr, p1, dr * self.DCOLS + p1, p2 - p1 + 1)
				lc = lc + 1
			lr = lr + 1 
		
	def text_clear(self):
		for i in range(self.LCOLS * self.LROWS):
			self.LayoutFB[i] = ' '
		self.text_blit(0, 0, self.LROWS, self.LCOLS);

	def text_greet(self, msg1, msg2):
		pass

	def text_draw(self, widget):
		
		if self.transitioning:
			return 0

		row = widget.row
		col = widget.col
		txt = widget.buffer
		length = len(txt)

		self.LayoutFB[row * self.LCOLS + col:row * self.LCOLS + col + length] = txt

		self.text_blit(row, col, 1, length)

		return 0

	def text_bar_draw(self, widget):
		if self.transitioning:
			return 0
		val1 = widget.val1
		val2 = widget.val2
		row = widget.row
		col = widget.col
		length = widget.length

		val1 = int(round(val1 * length))
		val2 = int(round(val2 * length))

		n = row * self.LCOLS + col
		for i in range(n, n + length):
			self.LayoutFB[i] = ' '
		if widget.direction == DIR_EAST:
			if val1 > val2:
				end = n + val1
			else:
				end = n + val2
			for i in range(n, end):
				if val1 == val2 or i < n + min(val1, val2):
					self.LayoutFB[i] = chr(widget.ch[0] + self.CHAR0)
				elif i < n + val2:
					self.LayoutFB[i] = chr(widget.ch[1] + self.CHAR0)
				else:
					self.LayoutFB[i] = chr(widget.ch[2] + self.CHAR0)
			if widget.style == STYLE_HOLLOW and val1 == val2:
				for i in range(end, n + length + 1):
					if i == n:
						self.LayoutFB[i] = chr(widget.ch[1] + self.CHAR0)
					elif i < n + length:
						self.LayoutFB[i] = chr(widget.ch[2] + self.CHAR0)
					elif i == n + length:
						self.LayoutFB[i] = chr(widget.ch[3] + self.CHAR0)
		elif widget.direction == DIR_WEST:
			if val1 > val2:
				end = n - val1
			else:
				end = n - val2
			i = n
			while i > end:
				if val1 == val2 or i > n - min(val1, val2):
					self.LayoutFB[i] = chr(widget.ch[0] + self.CHAR0)
				elif i > n - val2:
					self.LayoutFB[i] = chr(widget.ch[1] + self.CHAR0)
				else:
					self.LayoutFB[i] = chr(widget.ch[2] + self.CHAR0)
				i = i - 1
			if widget.style == STYLE_HOLLOW and val1 == val2:
				i = end
				while i > n - length:
					if i == n:
						self.LayoutFB[i] = chr(widget.ch[3] + self.CHAR0)
					elif i > n - length - 1:
						self.LayoutFB[i] = chr(widget.ch[2] + self.CHAR0)
					elif i == n - length - 1:
						self.LayoutFB[i] = chr(widget.ch[1] + self.CHAR0)
					i = i - 1	
			
		self.text_blit(row, col, 1, length)

	def text_histogram_draw(self, widget):
		txt = ''
		for val in widget.history:
			val = int(round(val * self.YRES))
			if val >= self.YRES:
				val = self.YRES - 1
			if val < 0:
				val = 0
			txt += chr(widget.ch[val] + self.CHAR0)

		n = widget.row * self.LCOLS + widget.col
		self.LayoutFB[n:n + widget.length] = txt

		self.text_blit(widget.row, widget.col, 1, widget.length)
		
	def text_icon_draw(self, widget):

		if self.chars[widget.ch] != widget.bitmap:
			self.chars[widget.ch] = widget.bitmap
			self.emit('special-char-changed', widget.ch)

		n = widget.row * self.LCOLS + widget.col
		self.LayoutFB[n] = chr(widget.ch + self.CHAR0)
		self.text_blit(widget.row, widget.col, 1, 1)

	def text_bignums_draw(self, widget):

		tmp = [[0 for i in range(8)] for j in range(8)]

		for row in range(16):
			i = row / 8
			rr = row % 8
			for col in range(24):
				j = col / 6
				cc = col % 6
				n = i * 4 + j
		
				if widget.FB[row * 24 + col] == '.':
					tmp[n][rr] = tmp[n][rr] ^ (1<<5-cc)

		for i in range(8):
			if tmp[i] != self.chars[widget.ch[i]]:
				self.chars[widget.ch[i]] = tmp[i]
				self.emit('special-char-changed', widget.ch[i])
		n = 0

		for i in range(2):
			for j in range(4):
				self.LayoutFB[(widget.row + i) * self.LCOLS + widget.col + j] = chr(n + widget.ch[0] + self.CHAR0)
				n = n + 1

		self.text_blit(widget.row, widget.col, 2, 4)


	def text_gif_draw(self, widget):

		tmp = [[0 for i in range(self.YRES)] for j in range(widget.rows * widget.cols)]

		for row in range(widget.height):
			i = row / self.YRES
			rr = row % self.YRES
			for col in range(widget.width):
				j = col / self.XRES
				cc = col % self.XRES
				n = i * widget.cols + j
				#print len(widget.pixels), ((widget.xpoint+col) * widget.width + widget.ypoint + row)
				if (widget.xpoint+col) * widget.width + widget.ypoint + row >= len(widget.pixels):
					continue
				pxl = widget.pixels[(widget.xpoint+col) * widget.width + widget.ypoint+row - 1]
				if pxl.pxl != widget.bg and pxl.pxl != widget.tp:
					tmp[n][rr] = tmp[n][rr] ^ (1<<self.XRES-1-cc)

		for i in range(widget.rows * widget.cols):
			if tmp[i] != self.chars[widget.ch[i]]:
				self.chars[widget.ch[i]] = tmp[i]
				self.emit('special-char-changed', widget.ch[i])

		n = 0

		for i in range(widget.rows):
			for j in range(widget.cols):
				self.LayoutFB[(widget.row + i) * self.LCOLS + widget.col + j] = chr(n + widget.ch[0] + self.CHAR0)
				n = n + 1

		self.text_blit(widget.row, widget.col, widget.rows, widget.cols)
