import pickle

from RGBA import RGBA
from Buffer import Buffer

from Functions import *
from Constants import *


class Graphic:
	def __init__(self, section, rows=0, cols=0):
		self.INVERTED = 0
		self.YRES = 8
		self.XRES = 6
		self.FG_COL = [0x00, 0xff, 0x00, 0xff]
		self.BG_COL = [0xff, 0xff, 0xff, 0xff]
		self.BL_COL = [0xff, 0xff, 0xff, 0x00]
		self.NO_COL = [0x00, 0x00, 0x00, 0x00]
		res = self.cfg_fetch_raw(section, "resolution", None)
		if res is None:
			self.DCOLS = cols
			self.DROWS = rows
		else:
			res = [int(x) for x in res.lower().split("x")]
			self.DCOLS = res[0] - res[0] % self.XRES
			self.DROWS = res[1] - res[1] % self.YRES
		self.cols = self.DCOLS / self.XRES
		self.rows = self.DROWS / self.YRES
		self.LCOLS = 0
		self.LROWS = 0
		#self.CHARS = self.cols * self.rows # unused here, but effects the gif size limit
		self.graphic_FB = resizeList([], LAYERS, list) 
		self.graphic_resizeFB(rows, cols)
		color = self.cfg_fetch_raw(section, "foreground", "000000ff")
		if RGBA.color2RGBA(color, self.FG_COL) < 0:
			error("%s: ignoring illegal color '%s'", self.name, color)
		color = self.cfg_fetch_raw(section, "background", "ffffff00")
		if RGBA.color2RGBA(color, self.BG_COL) < 0:
			error("%s: ignoring illegal color '%s'", self.name, color)
		color = self.cfg_fetch_raw(section, "basecolor", "ffffff")
		if RGBA.color2RGBA(color, self.BL_COL) < 0:
			error("%s: ignoring illegal color '%s'", self.name, color)
		self.INVERTED = self.cfg_fetch_num(section, "inverted", 0)
		fd = open("cfa635_fonts.dat", "r")
		self.fonts = pickle.load(fd)
		fd.close()

	def layout_transition(self, direction):
		print "layout_transition", self.transition_tick
		self.transitioning = True
		for l in range(LAYERS):
			for row in range(self.LROWS):
				n = row * self.LCOLS
				if direction == 'W' or (direction == 'B' and row % 2 == 0):
					col = self.LCOLS-self.transition_tick - 1
				elif direction == 'E' or direction == 'B':
					col = self.transition_tick
				else:
					error("Unknown transition <%s>: Use W(est), E(ast) or B(oth)" % direction)
					col = 0
				cell = []
				for x in range(self.XRES):
					p = self.NO_COL
					cell.append(p)
				self.graphic_FB[l][n + col:n + self.LCOLS] = cell + self.graphic_FB[l][n + col + self.XRES:n + self.LCOLS]

		self.transition_tick = self.transition_tick + self.XRES
		if self.transition_tick > self.LCOLS:
			self.transition_tick = 0
			self.transitioning = False
			self.emit('layout-transition-finished')
			return None

		self.graphic_blit(0, 0, self.LROWS, self.LCOLS)
		return True

	def graphic_resizeFB(self, rows, cols):
		if( rows <= self.LROWS and cols <= self.LCOLS ):
			return

		if rows < self.LROWS: rows = self.LROWS
		if cols < self.LCOLS: cols = self.LCOLS

		for l in range(LAYERS):
			self.graphic_FB[l] = resizeList(self.graphic_FB[l], rows * cols, list)

		self.LCOLS = cols
		self.LROWS = rows

	def graphic_window(self, pos, size, max):
		p1 = pos
		p2 = pos + size
		wpos = 0
		wsize = 0
		if p1 > max or p2 < 0 or size < 1:
			return wpos, wsize
		if p1 < 0:
			p1 = 0

		if p2 > max:
			p2 = max

		wpos = p1
		wsize = p2 - p1

		return wpos, wsize

	def graphic_blit(self, row, col, height, width):
		r, h = self.graphic_window(row, height, self.DROWS)
		c, w = self.graphic_window(col, width, self.DCOLS)
		if h > 0 and w > 0:
			self.graphic_real_blit(r, c, h, w)

	def graphic_blend(self, row, col):
		ret = self.BL_COL
		ret[3] = 0x00

		o = LAYERS - 1

		for l in range(LAYERS):
			p = self.graphic_FB[l][row * self.LCOLS + col]
			if p[3] == 255:
				o = l
				break

		for l in range(o, -1, -1):
			p = self.graphic_FB[l][row * self.LCOLS + col]
			if p[3] == 255:
				ret[0] = p[0]
				ret[1] = p[1]
				ret[2] = p[2]
				ret[3] = 0xff
			elif p[3] != 0:
				ret[0] = (p[0] * p[3] + ret[0] * (255 - p[3]))/ 255
				ret[1] = (p[1] * p[3] + ret[1] * (255 - p[3]))/ 255
				ret[2] = (p[2] * p[3] + ret[1] * (255 - p[3]))/ 255
				ret[3] = 0xff

			if self.INVERTED:
				ret[0] = 255 - ret[0]
				ret[1] = 255 - ret[1]
				ret[2] = 255 - ret[2]

		return ret

	def graphic_render(self, layer, row, col, fg, bg, txt):
		if layer < 0 or layer >= LAYERS:
			error("%s: layer %d out of bounds (0..%d)" % ( self.name, layer, LAYERS - 1))

		length = len(txt)

		self.graphic_resizeFB(row + self.YRES, col + self.XRES * length)

		r = row
		c = col

		for char in txt:
			font = self.fonts[ord(char)]

			for y in range(self.YRES):
				mask = 1 << self.XRES
				for x in range(self.XRES):
					mask >>= 1
					if font[y] & mask:
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][0] = fg[0]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][1] = fg[1]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][2] = fg[2]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][3] = fg[3]
						
					else:
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][0] = bg[0]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][1] = bg[1]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][2] = bg[2]
						self.graphic_FB[layer][(r + y) * self.LCOLS + c + x][3] = bg[3]
			c += self.XRES

		self.graphic_blit(row, col, self.YRES, self.XRES * length)

	def graphic_draw(self, W):
		fg = (self.FG_COL, W.fg_color)[W.fg_valid]
		bg = (self.BG_COL, W.bg_color)[W.bg_valid]

		self.graphic_render(W.layer, self.YRES * W.row, self.XRES * W.col, fg, bg, W.buffer)

		return 0


	def graphic_icon_draw(self, W):
		bitmap = W.bitmap

		layer = W.layer
		row = self.YRES * W.row
		col = self.XRES * W.col

		if layer < 0 or layer >= LAYERS:
			error("%s: layer %d out of bounds (0..%d)" % (self.name, layer, LAYERS - 1))
			return -1

		self.graphic_resizeFB(row + self.YRES, col + self.XRES)

		W.visible.eval()

		visible = W.visible.P2N()

		fg = (self.FG_COL, W.fg_color)[W.fg_valid]
		bg = (self.BG_COL, W.bg_color)[W.bg_valid]

		for y in range(self.YRES):
			mask = 1 << self.XRES

			for x in range(self.XRES):
				i = (row + y) * self.LCOLS + col + x
				mask >>= 1
				if visible:
					if bitmap[y] & mask:
						self.graphic_FB[layer][i][0] = fg[0]
						self.graphic_FB[layer][i][1] = fg[1]
						self.graphic_FB[layer][i][2] = fg[2]
						self.graphic_FB[layer][i][3] = fg[3]
					else:
						self.graphic_FB[layer][i][0] = bg[0]
						self.graphic_FB[layer][i][1] = bg[1]
						self.graphic_FB[layer][i][2] = bg[2]
						self.graphic_FB[layer][i][3] = bg[3]
				else:
					self.graphic_FB[layer][i][0] = self.BG_COL[0]
					self.graphic_FB[layer][i][1] = self.BG_COL[1]
					self.graphic_FB[layer][i][2] = self.BG_COL[2]
					self.graphic_FB[layer][i][3] = self.BG_COL[3]

		self.graphic_blit(row, col, self.YRES, self.XRES)

		return 0

	def graphic_bar_draw(self, W):
		layer = W.layer
		row = self.YRES * W.row
		col = self.XRES * W.col
		dir = W.direction
		style = W.style
		length = W.length

		fg = self.FG_COL
		bg = self.BG_COL

		bar = [x for x in range(2)]

		bar[0] = (fg, W.color[0])[W.color_valid[0]]
		bar[1] = (fg, W.color[1])[W.color_valid[1]]

		if dir & (DIR_EAST | DIR_WEST):
			self.graphic_resizeFB(row + self.YRES, col + self.XRES * length)
		else:
			self.graphic_resizeFB(row + self.YRES * length, col + self.XRES)

		res = (self.YRES, self.XRES)[dir & (DIR_EAST | DIR_WEST) == 0]

		max = length * res
		val1 = W.val1 * max
		val2 = W.val2 * max

		if val1 < 1:
			val1 = 1
		elif val1 > max:
			val1 = max

		if val2 < 1:
			val2 = 1
		elif val2 > max:
			val2 = max

		rev = 0
		if dir == DIR_WEST or dir == DIR_EAST:
			if dir == DIR_WEST:
				val1 = max - val1
				val2 = max - val2
				rev = 1
			for y in range(self.YRES):
				val = (val1, val2)[y >= self.YRES / 2]
				bc = (bar[0], bar[1])[y >= self.YRES / 2]

				for x in range(max):
					if x < val:
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x][0] = (bc.R, bg.R)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x][1] = (bc.G, bg.G)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x][2] = (bc.B, bg.B)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x][3] = (bc.A, bg.A)[rev]
					else:
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x[0]] = (bg.R, bc.R)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x[1]] = (bg.G, bc.G)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x[2]] = (bg.B, bc.B)[rev]
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x[3]] = (bg.A, bc.A)[rev]

					if style:
						self.graphic_FB[layer][row * self.LCOLS + col + x] = fg
						self.graphic_FB[layer][(row + self.YRES - 1) * self.LCOLS + col + x] = fg
				if style:
					self.graphic_FB[layer][(row + y) * self.LCOLS + col] = fg
					self.graphic_FB[layer][(row + y) * self.LCOLS + col + max - 1] = fg

		elif dir == DIR_NORTH or dir == DIR_SOUTH:
			if dir == DIR_NORTH:
				val1 = max - val1
				val2 = max - val2
				rev = 1
			for x in range(self.XRES):
				val = (val1, val2)[x >= self.XRES / 2]
				bc = (bar[0], bar[1])[x >= self.XRES / 2]
				for y in range(max):
					if y < val:
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x] = (bc, bg)[rev]
					else:
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + x] = (bg, bc)[rev]
					if style:
						self.graphic_FB[layer][(row + y) * self.LCOLS + col] = fg
						self.graphic_FB[layer][(row + y) * self.LCOLS + col + self.XRES - 1] = fg
				if style:
					self.graphic_FB[layer][row * self.LCOLS + col + x] = fg
					self.graphic_FB[layer][(row + max - 1) * self.LCOLS + col + x] = fg


		if dir & (DIR_EAST | DIR_WEST) == 0:
			self.graphic_blit(row, col, self.YRES, self.XRES * length)
		else:
			self.graphic_blit(row, col, self.YRES * length, self.XRES)


	def graphic_histogram_draw(self, W):
		layer = W.layer
		row = self.YRES * W.row
		col = self.XRES * W.col
		dir = W.direction
		length = W.length

		fg = self.FG_COL
		bg = self.BG_COL

		bar = (fg, W.fg_color)[W.fg_valid]

		if dir & (DIR_EAST | DIR_WEST):
			self.graphic_resizeFB(row + self.YRES, col + self.XRES * length)
		else:
			self.graphic_resizeFB(row + self.YRES * length, col + self.XRES)

		rev = 0
		if dir == DIR_WEST or dir == DIR_EAST:
			if dir == DIR_WEST:
				rev = 1
			for i in range(length):
				val = W.history[i] * 100 % self.YRES
				if val >= self.YRES:
					val = self.YRES - 1
				if val < 0:
					val = 0
				for y in range(self.YRES):
					for x in range(self.XRES):
						if rev:
							if val > y:
								self.graphic_FB[layer][(row + self.YRES - y - 1) * self.LCOLS + col - x - i * self.XRES - 1 + length * self.XRES] = bar
							else:
								self.graphic_FB[layer][(row + self.YRES - y - 1) * self.LCOLS + col - x - i * self.XRES - 1 + length * self.XRES] = bg
						else:
							if val > y:
								self.graphic_FB[layer][(row + self.YRES - y - 1) * self.LCOLS + col + i * self.XRES + x] = bar
							else:
								self.graphic_FB[layer][(row + self.YRES - y - 1) * self.LCOLS + col + i * self.XRES + x] = bg

		if dir == DIR_NORTH or dir == DIR_SOUTH:
			if dir == DIR_NORTH:
				rev = 1
			for i in range(length):
				val = W.history[i] * 100 % self.XRES
				for y in range(self.YRES):
					for x in range(self.XRES):
						if val >= self.XRES:
							val = self.XRES - 1
						if val < 0:
							val = 0
						if rev:
							if val > x:
								self.graphic_FB[layer][(row - i * self.YRES - 1 + length * self.YRES) * self.LCOLS + col + x] = bar
							else:
								self.graphic_FB[layer][(row - i * self.YRES - 1 + length * self.YRES) * self.LCOLS + col + x] = bg
						else:
							if val > x:
								self.graphic_FB[layer][(row + i * self.YRES) * self.LCOLS + col + x] = bar
							else:
								self.graphic_FB[layer][(row + i * self.YRES) * self.LCOLS + col + x] = bg
							
							

		if dir & (DIR_WEST | DIR_EAST) == 0:
			self.graphic_blit(row, col, self.YRES, self.XRES * length)
		else:
			self.graphic_blit(row, col, self.YRES * length, self.XRES)
							
					

	def graphic_gif_draw(self, W):
		r = W.row * self.YRES
		c = W.col * self.XRES
		l = W.layer

		for row in range(W.height):
			for col in range(W.width):
				n = (r + row) * self.LCOLS + c + col
				nn = row * W.width + col
				self.graphic_FB[l][n][0] = W.pixels[nn].R
				self.graphic_FB[l][n][1] = W.pixels[nn].G
				self.graphic_FB[l][n][2] = W.pixels[nn].B
				self.graphic_FB[l][n][3] = W.pixels[nn].A

		self.graphic_blit(r, c, W.height, W.width)

	def graphic_bignums_draw(self, W):
		r = W.row * self.YRES
		c = W.col * self.XRES
		l = W.layer

		fg = (self.FG_COL, W.fg_color)[W.fg_valid]
		bg = (self.BG_COL, W.bg_color)[W.bg_valid]

		for row in range(16):
			for col in range(24):
				n = (r + row) * self.LCOLS + c + col
				if W.FB[row * 24 + col] == '.':
					self.graphic_FB[l][n] = fg
				else:
					self.graphic_FB[l][n] = bg

		self.graphic_blit(r, c, 16, 24)
				

	def graphic_clear(self):
		for l in range(LAYERS):
			for i in range(self.LROWS * self.LCOLS):
				self.graphic_FB[l][i][0] = self.NO_COL[0]
				self.graphic_FB[l][i][1] = self.NO_COL[1]
				self.graphic_FB[l][i][2] = self.NO_COL[2]
				self.graphic_FB[l][i][3] = self.NO_COL[3]

		self.graphic_blit(0, 0, self.LROWS, self.LCOLS)

	def graphic_rgb(self, row, col):
		return self.graphic_blend(row, col)

	def graphic_gray(self, row, col):
		p = self.graphic_blend(row, col)
		return (77 * p[0] + 150 * p[1] + 28 * p[2]) / 255

	def graphic_black(self, row, col):
		return self.graphic_gray(row, col) < 127

