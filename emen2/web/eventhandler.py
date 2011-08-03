import functools
import threading

class Callback(object):
	def __init__(self, cb, *args, **kwargs):
		if args or kwargs:
			cb = functools.partial(cb, *args, **kwargs)
		self.cb = cb

	def __call__(self, *args, **kwargs):
		result = None
		if callable(self.cb):
			result = self.cb(*args, **kwargs)
		return result

class Event(object):
	_cb_lock = threading.RLock()
	_o_lock = threading.RLock()
	def __init__(self, name):
		self.name = name
		self.callbacks = []
		self.observers = []

	def add_observer(self, cb, *args, **kwargs):
		with self._o_lock:
			self.observers.append(partial(cb, *args, **kwargs))
		return self

	def add_cb(self, cb, *args, **kwargs):
		with self._cb_lock:
			self.callbacks.append(Callback(cb, *args, **kwargs))
		return self

	def add_cbs(self, cbs):
		for (cb, (a, kw)) in cbs.iteritems():
			self.add_cb(cb, *a, **kw)
		return self

	def __call__(self, *args, **kwargs):
		results = []
		with self._cb_lock:
			for cb in self.callbacks:
				result = cb(*args, **kwargs)
				with self._o_lock:
					for observer in self.observers:
						observer(result)
				results.append(result)
		return results

class EventRegistry(object):
	_lock = threading.RLock()
	events = {}
	nullevent = Event('')

	@classmethod
	def event(self, name):
		event = Event(name)
		with self._lock:
			return self.events.setdefault(name, event)

	def observe_event(self, name, cb, *args, **kwargs):
		self.events[name].add_observer(cb, *args, **kwargs)
		return self
