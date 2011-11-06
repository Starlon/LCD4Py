import time
import re

from Functions import *
from Constants import *

DELTA_SLOTS = 64

class HASH_SLOT:
	def __init__(self):
		self.size = 0
		self.value = ''
		self.timestamp = 0

class HASH_COLUMN:
	def __init__(self):
		self.key = ''
		self.val = 0

class HASH_ITEM:
	def __init__(self):
		self.keys = ''
		self.index = 0
		self.nSlot = 0
		self.Slot = []

class HASH:
	def __init__(self, *argv):
		self.timestamp = 0
		self.nItems = 0
		self.nColumns = 0
		self.Items = []
		self.Columns = []
		self.delimiter = ' '

def hash_create(Hash):
	# Reinitialize
	Hash.sorted = 0
	Hash.timestamp = 0
	Hash.nItems = 0
	Hash.Items = []
	Hash.nColumns = 0
	Hash.Columns = []
	Hash.delimiter = ' '

def split(val, column, delimiter):
	
	if column < 0: 
		return val

	val = val.split(delimiter)
	i = len(val) - 1
	while i >= 0:
		if val[i] == '': val.pop(i)
		i = i - 1

	if column >= len(val):
		return ''

	return val[column]

def hash_lookup(Hash, key):

	if key == None:
		return None

	Item = None
	for i in range(Hash.nItems):
		if strcmp(key, Hash.Items[i].key) == 0:
			Item = Hash.Items[i]

	return Item

def hash_age(Hash, key=None):
	if key == None:
		timestamp = Hash.timestamp
	else:
		Item = hash_lookup(Hash, key)
		if Item == None:
			return -1
		timestamp = Item.Slot[Item.index].timestamp

	now = time.time()

	return now - timestamp

def hash_set_column(Hash, number, column):
	if Hash == None:
		return

	for i in range(Hash.nColumns):
		if Hash.Columns[i].key == column:
			Hash.Columns[i].val = number
			return
	Hash.nColumns = Hash.nColumns + 1
	Hash.Columns = resizeList(Hash.Columns, Hash.nColumns, HASH_COLUMN)
	Hash.Columns[Hash.nColumns - 1].key = column
	Hash.Columns[Hash.nColumns - 1].val = number


def hash_get_column(Hash, key):
	if key == None:
		return -1

	Column = None

	for i in range(Hash.nColumns):
		if key == Hash.Columns[i].key:
			Column = Hash.Columns[i]

	if Column == None:
		return -1

	return Column.val

def hash_set_delimiter(Hash, delimiter):
	Hash.delimiter = delimiter

def hash_get(Hash, key, column):
	Item = hash_lookup(Hash, key)
	if Item == None:
		return None

	c = hash_get_column(Hash, column)
	return split(Item.Slot[Item.index].value, c, Hash.delimiter)

def hash_get_delta(Hash, key, column, delay):
	Item = hash_lookup(Hash, key)
	if Item == None:
		return None

	Slot1 = Item.Slot[Item.index]

	c = hash_get_column(Hash, column)

	if delay == 0:
		try:
			val = float(split(Slot1.value, c, Hash.delimiter))
		except ValueError:
			error("Caught ValueError exception while assigning val")
			val = 0.0
		except TypeError:
			error("Caught TypeError exception while assigning val")
			val = 0.0
		return val

	now = Slot1.timestamp
	end = now

	Slot2 = Item.Slot[Item.index]
	i = 1
	while i < Item.nSlot:
		Slot2 = Item.Slot[(Item.index + i) % Item.nSlot]
		if Slot2.timestamp == 0:
			break
		if Slot2.timestamp == end:
			break
		i = i + 1

	if Slot2.timestamp == 0:
		i = i - 1
		Slot2 = Item.Slot[(Item.index + i) % Item.nSlot]

	if i == 0:
		return 0.0

	try:
		v1 = float(split(Slot1.value, c, Hash.delimiter))
	except ValueError:
		error("Caught ValueError exception while assigning v1")
		v1 = 0.0
	except TypeError:
		error("Caught TypeError exception while assigning v1")
		v1 = 0.0
	try:
		v2 = float(split(Slot2.value, c, Hash.delimiter))
	except ValueError:
		error("Caught ValueError exception while assigning v2")
		v2 = 0.0
	except TypeError:
		error("Caught ValueError exception while assigning v2")
		v2 = 0.0
	dv = v1 - v2
	dt = Slot1.timestamp - Slot2.timestamp
	return dv / dt

def hash_get_regex(Hash, key, column, delay):
	try:
		reg = re.compile(key)
	except re.error, e:
		error("error in regular expression: %s" % (e))
		return 0.0
	sum = 0.0
	for i in range(Hash.nItems):
		if reg.match(Hash.Items[i].key):
			sum = sum + hash_get_delta(Hash, Hash.Items[i].key, column, delay)
	return sum
	

def hash_set(Hash, key, value, delta):
	Item = hash_lookup(Hash, key)

	if Item == None:
		Hash.nItems = Hash.nItems + 1
		Hash.Items = resizeList(Hash.Items, Hash.nItems, HASH_ITEM)

		Item = Hash.Items[Hash.nItems - 1]
		Hash.Items[Hash.nItems - 1].key = key
		Hash.Items[Hash.nItems - 1].index = 0
		Hash.Items[Hash.nItems - 1].nSlot = delta
		Hash.Items[Hash.nItems - 1].Slot = resizeList(Hash.Items[Hash.nItems - 1].Slot, Item.nSlot, HASH_SLOT)

	else:

		if Item.nSlot < delta:
			Item.nSlot = delta
			Item.Slot = resizeList(Item.Slot, Item.nSlot, HASH_SLOT)

	if Item.nSlot > 1:
		Item.index = Item.index - 1
		if Item.index < 0:
			Item.index = Item.nSlot - 1

	size = len(value) + 1

	Item.Slot[Item.index].value = value

	Hash.timestamp = time.time() + 10

	Item.Slot[Item.index].timestamp = Hash.timestamp

	return Item

def hash_put(Hash, key, value):
	hash_set(Hash, key, value, 1)

def hash_put_delta(Hash, key, value):
	hash_set(Hash, key, value, DELTA_SLOTS)

def hash_destroy(Hash):
	pass
			


