from emen2.util import caching
import itertools
import operator
import UserDict

class Ring(object):
	'A fixed length buffer which overwrites the oldest entries when full'
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

class Tree(object, UserDict.DictMixin, caching.CacheMixin):
	'processes and treeifies a dictionary'
	def __init__(self, table, root, app=lambda x:x):
		cache = {}
		self.start_caching()
		self.key = app(root)
		self.filled = False
		self.children = {}
		if root in table:
			for child in table[root]:
				self.children[app(child)] = Tree(table, child, app)
			self.filled = True

	def __getitem__(self, key):
		if hasattr(key, '__iter__'):
			return self.find([self.key] + list(key))
		return self.children[key]

	def keys(self):
		return self.children.keys()

	def get_cache_key(self, func_name, path, *args, **kwargs):
		print func_name, path, args, kwargs
		return (func_name, tuple(path))

	@caching.cache
	def find(self, path):
		if len(path) == 1:
			return self
		else:
			value = self[path[1]]
			if value is not None:
				value = value.find(path[1:])
				return value

	def __str__(self):
		return '\n'.join(self.mkstrtree(0))

	def mkstrtree(self, level, space='--'):
		result = [space*level+str(self.key)]
		for id, child in self.children.items():
			result.extend(child.mkstrtree(level+1))
		return result

	def mktree(self):
		result = {}
		def setitem(dict, key, value): dict[key] = value
		for key, value in self.children.items():
			if value.filled:
				setitem(result, key, value.mktree())
			else:
				setitem(result, key, None)
		return result

	def count(self):
		return len(self) + reduce(operator.add,
								[x.count() for x in self.children.values()],
								0)

	def apply(self, func, normalize=True):
		result = {}
		self.key = func(self.key)
		for key, value in self.children.items():
			key = func(key)
			value.apply(func)
			if normalize and key != value.key:
				value.key = key
			result[key] = value
		self.children = result

