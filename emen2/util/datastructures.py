# $Id$
from emen2.util import caching
import itertools
import collections
import operator
import UserDict

class Ring(object):
	'A fixed length buffer which overwrites the oldest entries when full'
	def __init__(self, length=5): self.__buf = collections.deque(maxlen=length)
	def __getitem__(self, key): return self.__buf[key]
	def __get__(self, instance, owner): return self
	def __set__(self, instance, value): self.__buf.append(value)
	def __repr__(self): return 'Ring Buffer:\n%s' % str.join('\n', [repr(x) for x in self.__buf])
	def append(self, value): self.__buf.append(value)

class AttributeDict(dict):
	def __getattribute__(self, name):
		try: result = dict.__getattribute__(self, name)
		except AttributeError: result = self[name]
		return result
	def __setattr__(self, key, value): self[key] = value


class Enum(set):
	'A class that maps names to numbers and allows the numbers to be referenced by name'
	def __init__(self, dct):
		set.__init__(self, (x.upper() for x in dct))
		self.values = dict((x.upper(), int(y)) for (x,y) in dct.iteritems())

	def __getattribute__(self, name):
		'returns the value associated with an state name'
		result = None
		try:
			result = set.__getattribute__(self, name)
		except AttributeError,a:
			try:
				result = object.__getattribute__(self, 'values')[name.upper()]
			except KeyError:
				raise a
		return result

	def __getitem__(self, name):
		'gets the value associated with the state name'
		try:
			name = int(name)
			return (x for x in self.values.values() if x == name).next()
		except ValueError: pass
		try:
			return self.values[name.upper()]
		except (AttributeError, KeyError):
			raise KeyError('no value %s' % name)

	def add(self, value):
		'add a state'
		val = value[0].upper()
		set.add(self, val)
		self.values.update((val, int(value[1])))

	def get_name(self, value):
		'get the name of a state'
		return (x for x,y in self.values.items() if y == value).next()

	def get_names(self):
		return self.values.keys()
__version__ = "$Revision$".split(":")[1][:-1].strip()
