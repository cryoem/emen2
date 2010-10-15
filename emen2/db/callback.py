# $Id$
import collections
import emen2.db.config
g = emen2.db.config.g()

class Message(object):
	modes = set(['enter', 'exit', 'other'])
	def __init__(self, name, mode, *data, **kwdata):
		self.name = name
		if mode not in self.modes: mode = 'other'
		self.mode = mode
		self.data = data
		self.kwdata = kwdata

class MessageQueue(object):
	g.__callbacks = collections.defaultdict(lambda: collections.defaultdict(list))
	__callbacks = g.__callbacks

	@classmethod
	def register(cls, message, mode):
		def _inner(func):
			cls.__callbacks[message][mode] = func
			return func
		return _inner

	@classmethod
	def send(cls, message, mode, *data, **kwdata):
		result = None
		if message in cls.__callbacks and mode in cls.__callbacks[message]:
			result = cls.__callbacks[message][mode](Message(message, mode, *data, **kwdata))
		return result
__version__ = "$Revision$".split(":")[1][:-1].strip()
