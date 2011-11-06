from ctypes import resize, sizeof, addressof
from configobj import ConfigObj

def error(string):
	print "Error: " + string

def search(myList, key, objKey):
	return [x for x in myList if x[objKey] == key]

def strndup(source, len):
	return source[:len]

def strndup2(source, length):
	buffer = ''
	for i in range(length):
		if i >= len(source): break
		buffer = buffer + source[i]
	return buffer

def strcmp(s1, s2):
	if s1 < s2:
		return -1
	elif s1 == s2:
		return 0
	elif s1 > s2:
		return 1

def strncmp(s1, s2, n):
	return strcmp(s1[:n], s2)

def strcasecmp(s1, s2):
	return strcmp(s1.lower(), s2.lower())

def resizeArray(array, new_size):
	resize(array, sizeof(array._type_)*new_size)
	newarray = (array._type_*new_size).from_address(addressof(array))
	if hasattr(array,"original"):
		newarray.original = array.original
	else:
		newarray.original = array
	return newarray

def resizeList(list, new_size, type):
	if new_size < len(list):
		return list
	for i in range(new_size):
		if i >= len(list):
			if type.__name__ == "str":
				list.append(' ')
			else:
				list.append(type())
	return list

def is_space(c):
	if c == ' ' or c == '\t': return True
	return False

def is_digit(c):
	try:
		if int(c) >= 0 and int(c) <= 9: return True
	except:
		return False

def is_alpha(c):
	c = ord(c)
	if ( c >= ord('A') and c <= ord('Z') ) or (c >= ord('a') and c <= ord('z')) or (c == ord('_')): return True
	return False

def is_alnum(c):
	return is_digit(c) or is_alpha(c)

def value(buffer):
	tmp = ''
	for c in buffer:
		if c == '\0': break
		tmp = tmp + c
	return tmp
