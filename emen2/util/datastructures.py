import itertools
class Ring(object):
	def __init__(self, length=5):
		self.__buf = []
		self.__length = length
	def __getitem__(self, key):
		return self.__buf[key]
	def __get__(self, instance, owner):
		return self
	def __set__(self, instance, value):
		self.append(value)
	def __repr__(self):
		return 'Ring Buffer:\n%s' % str.join('\n', [repr(x) for x in self.__buf])
	def append(self, value):
		if len(self.__buf) > self.__length:
			self.__buf = self.__buf[-(self.__length-1):]
		self.__buf.append(value)

class AttributedDict(dict):
	def __getattribute__(self, name):
		result = None
		try:
			result = dict.__getattribute__(self, name)
		except AttributeError, a:
			try:
				result = dict.__getitem__(self, name)
			except KeyError, k:
				raise a
		return result
	def __setattr__(self, name, value):
		self[name] = value
	def __repr__(self):
		print 'AttributedDict(%s)' % dict.__repr__(self)

class Enum(set):
	def __init__(self, dct):
		set.__init__(self, (x.upper() for x in dct))
		self.values = dict(( (x.upper(), int(dct[x])) for x in dct))
		
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
		return (x[0] for x in self.values.items() if x[1] == value).next()

import UserDict
class MultiKeyDict(object, UserDict.DictMixin):
	def __init__(self):
		self._values = {}
	def _iterify(self, key):
		if not hasattr(key, '__iter__'): key = set([key])
		return key
	def __setitem__(self, key, value):
		key = self._iterify(key)
		self._values[frozenset(key)] = value
	def __getitem__(self, key):
		key = self._iterify(key)
		return set((self._values[x] for x in self._values if x.issuperset(key)))
	def filterbypred(self, key, pred, type=int):
		result = set()
		for x in (k for k in self.keys() if pred(key,k)): result &= self[x]
		return set(filter(lambda x: isinstance(x,type), result))
	def keys(self):
		a = set()
		for x in self._values.keys(): a |= x
		return a
	def values(self):
		return self._values.values()
	def as_dict(self): return dict(self.items())
	def __repr__(self): return str(self.as_dict())
