# $Id$
"""Callback

Classes:
	Message
	MessageQueue
"""

import collections

# EMEN2 imports
import emen2.db.config

class Message(object):
	modes = set(['enter', 'exit', 'other'])
	def __init__(self, name, mode, *data, **kwdata):
		self.name = name
		if mode not in self.modes: mode = 'other'
		self.mode = mode
		self.data = data
		self.kwdata = kwdata


class MessageQueue(object):
	emen2.db.config.globalns._callbacks = collections.defaultdict(lambda: collections.defaultdict(list))
	_callbacks = emen2.db.config.globalns._callbacks

	@classmethod
	def register(cls, message, mode):
		def _inner(func):
			cls._callbacks[message][mode] = func
			return func
		return _inner

	@classmethod
	def send(cls, message, mode, *data, **kwdata):
		result = None
		if message in cls._callbacks and mode in cls._callbacks[message]:
			result = cls._callbacks[message][mode](Message(message, mode, *data, **kwdata))
		return result


__version__ = "$Revision$".split(":")[1][:-1].strip()