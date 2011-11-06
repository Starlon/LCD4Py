
class Buffer(object):
	def __init__(self, size=0):
		self._buffer = ['' for x in range(size)]

	def _get(self):
		return "".join(self._buffer)

	def _set(self, val):
		self._buffer = [x for x in val]

	def _del(self, val):
		del(self._buffer)
		self._buffer = []

	buffer = property(_get, _set, _del, "Buffer")

	def __getitem__(self, key):
		if type(key).__name__ == "slice":
			start = key.start
			stop = key.stop
		else:
			start = key
			stop = key + 1
		return "".join(self._buffer[start:stop])

	def __setitem__(self, key, val):
		if type(key).__name__ == "slice":
			start = key.start
			stop = key.stop
		else:
			start = key
			stop = key + 1
		self._buffer[start:stop] = [x for x in val]

	def append(self, val):
		self._buffer.append(val)
			
