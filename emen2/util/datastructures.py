# $Id$
from emen2.util import caching
import itertools
import collections
import operator
import UserDict

class Ring(object):
	'A fixed length buffer which overwrites the oldest entries when full'
	def __init__(self, length=5): self._buf = collections.deque(maxlen=length)
	def __getitem__(self, key): return self._buf[key]
	def __get__(self, instance, owner): return self
	def __set__(self, instance, value): self._buf.append(value)
	def __repr__(self): return 'Ring Buffer:\n%s' % str.join('\n', [repr(x) for x in self._buf])
	def append(self, value): self._buf.append(value)

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


class doubledict(object):
	'''Used for datastructures.  Key, value store with two separate lists of values.
	the _l methods work on the left values, the _r ones on the right values'''

	def __init__(self, keys=None, values1=None, values2=None):
		if None in (keys, values1, values2):
			keys, values1, values2 = [],[],[]
		self._dict_l = dict(zip(keys, values1))
		self._dict_r = dict(zip(keys, values2))

	def __repr__(self):
		out = zip(self._dict_l.keys(), self._dict_l.values(), self._dict_r.values())
		return 'doubledict(%s)' % ','.join('{%r: (%r, %r)}' % (k, vl.pattern, getattr(vr, 'func', vr)) for k,vl, vr in out)

	def __str__(self):
		return '\n'.join('%(key)r: ("%(value_l)r", "%(value_r)r")' % dict(key=key, value_l=value_l.pattern, value_r=getattr(value_r, 'func', value_r)) for (key, value_l, value_r) in zip(self._dict_l.keys(), self._dict_l.values(), self._dict_r.values()))

	@classmethod
	def from_dict(cls, dct):
		self = cls.__new__(cls)
		self._dict_l, self._dict_r, self._vl_vr = {}, {}, {}
		for k, (v_l, v_r) in dct.iteritems():
			self._dict_l[k] = v_l
			self._dict_r[k] = v_r
		return self

	def get(self, name, default=None):
		return self.get_left(name, default), self.get_right(name, default)
	__getitem__ = get
	def get_left(self, name, default=None):
		return self._dict_l.get(name, default)
	def get_right(self, name, default=None):
		return self._dict_r.get(name, default)
	def set(self, name, value, right=True):
		if right:
			self._dict_r[name] = value
		else:
			self._dict_l[name] = value
	__setitem__ = set
	def add(self, k, v_l, v_r):
		self._dict_l[k] = v_l
		self._dict_r[k] = v_r
	def keys(self):
		assert set(self._dict_l) == set(self._dict_r)
		return self._dict_l.keys()
	def values(self):
		assert set(self._dict_l) == set(self._dict_r)
		return zip(self._dict_l.values(), self._dict_r.values())
	def items(self):
		assert set(self._dict_l) == set(self._dict_r)
		return zip(self._dict_l.iterkeys(), self._dict_l.itervalues(), self._dict_r.itervalues())
	def iteritems(self):
		assert set(self._dict_l) == set(self._dict_r)
		return izip(self._dict_l.iterkeys(), self._dict_l.itervalues(), self._dict_r.itervalues())
	def iteritems_l(self):
		return self._dict_l.iteritems()
	def iteritems_r(self):
		return self._dict_r.iteritems()
	def itervalues_l(self):
		return self._dict_l.itervalues()
	def itervalues_r(self):
		return self._dict_r.itervalues()

class IndexedListIterator(object):
	def __init__(self, lis):
		self.lis = tuple(lis)

		# public
		self.pos = 0

	def next(self, delta = 1):
		try:
			result = self.lis[self.pos]
			self.pos += delta
			self.pos %= len(self.lis)
		except IndexError:
			result = None
		return result

	def prev(self, delta = 1):
		self.pos -= delta
		return self.lis[self.pos]

	def __getitem__(self, arg):
		return self.lis[arg]





__version__ = "$Revision$".split(":")[1][:-1].strip()
