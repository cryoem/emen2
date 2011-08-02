import functools

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
	def __init__(self, name):
		self.name = name
		self.callbacks = []
		self.observers = []

	def add_observer(self, cb, *args, **kwargs):
		self.observers.append(partial(cb, *args, **kwargs))
		return self

	def add_cb(self, cb, *args, **kwargs):
		self.callbacks.append(Callback(cb, *args, **kwargs))
		return self

	def add_cbs(self, cbs):
		for (cb, (a, kw)) in cbs.iteritems():
			self.add_cb(cb, *a, **kw)
		return self

	def __call__(self, *args, **kwargs):
		for cb in self.callbacks:
			result = cb(*args, **kwargs)
			for observer in self.observers:
				observer(result)
			yield result

class EventRegistry(object):
	events = {}
	nullevent = Event('')

	@classmethod
	def event(self, name):
		event = Event(name)
		return self.events.setdefault(name, event)

	def fire_event(self, name, *args, **kwargs):
		results = self.events.get(name, self.nullevent)(*args, **kwargs)
		return results

	def register_observer(self, cb, *args, **kwargs):
		self.event('sys.fire_event').add_cb(cb, *args, **kwargs)
		return self

	def observe_event(self, name, cb, *args, **kwargs):
		self.events[name].add_observer(cb, *args, **kwargs)
		return self
