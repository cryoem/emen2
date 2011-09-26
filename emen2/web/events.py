import functools
import threading
from emen2.util import registry

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
			self.observers.append(functools.partial(cb, *args, **kwargs))
		return self

	def add_cb(self, cb, *args, **kwargs):
		with self._cb_lock:
			cb = Callback(cb, *args, **kwargs)
			self.callbacks.append(cb)
			return cb

	def add_cbs(self, cbs):
		for (cb, (a, kw)) in cbs.iteritems():
			self.add_cb(cb, *a, **kw)
		return self

	def remove_cb(self, cb):
		self.callbacks = [x for x in self.callbacks if x is not cb]
		return self

	def __call__(self, *args, **kwargs):
		results = []
		#with self._cb_lock:
		for cb in self.callbacks:
			result = cb(*args, **kwargs)
			with self._o_lock:
				for observer in self.observers:
					observer(result)
			results.append(result)
		return results

@registry.Registry.setup
class EventRegistry(registry.Registry):
	child_class = Event

	events = {}
	nullevent = Event('')

	def observe_event(self, name, cb, *args, **kwargs):
		with self._lock:
			self.events[name].add_observer(cb, *args, **kwargs)
			return self
