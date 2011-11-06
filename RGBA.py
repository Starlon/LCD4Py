
class RGBA:
	def __init__(self, r=0, g=0, b=0, a=0):
		self.R = r
		self.G = g
		self.B = b
		self.A = a

	@classmethod
	def color2RGBA(cls, color, C):
		if color == '':
			return -1

		try:
			l = eval("0x" + color)
		except SyntaxError:
			return -1

		if l >= (1 << 24):
			C[0] = (l >> 24) & 0xff
			C[1] = (l >> 16) & 0xff
			C[2] = (l >> 8) & 0xff
			C[3] = (l >> 0) & 0xff
		else:
			C[0] = (l >> 16) & 0xff
			C[1] = (l >> 8) & 0xff
			C[2] = (l >> 0) & 0xff
			C[3] = 0xff
			
		return 0

	
