import threading

def threaded(f):
	def wrapper(*args):
		t = threading.Thread(target=f, args=args)
		t.setDaemon(True)
		t.start()
		return True
	return wrapper

def threaded_false(f):
	def wrapper(*args):
		t = threading.Thread(target=f, args=args)
		t.setDaemon(True)
		t.start()
		return False
	return wrapper
