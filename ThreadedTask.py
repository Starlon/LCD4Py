import threading
import gobject
import time

class ThreadedTask(object):

	def __init__(self, loop_callback, complete_callback=None, wait=10):
		self.loop_callback = loop_callback
		self.complete_callback = complete_callback
		self.wait = wait / 100.0
		self.thread = None
		self._stopped = True

	def _start(self, *args, **kwargs):
		self._stopped = False
		self.args = args
		self.kwargs = kwargs
		while True:
			if self._stopped:
				break
			gobject.idle_add(self._loop)
			time.sleep(self.wait)
		if self.complete_callback is not None:
			gobject.idle_add(self.complete_callback)

	def _loop(self):
		self.loop_callback(*self.args, **self.kwargs)

	def start(self, *args, **kwargs):
		if self.thread is None:
			self.thread = threading.Thread(target=self._start, args=args, kwargs=kwargs)
		if not self.thread.isAlive():
			self.thread.start()

	def stop(self):
		self._stopped = True
		#if self.thread is not None:
		#	self.thread.join()

	def stopped(self):
		return self._stopped
