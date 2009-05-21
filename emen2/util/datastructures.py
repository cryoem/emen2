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
		return 'AttributedDict(%s)' % dict.__repr__(self)

class Enum(set):
	'A class that maps names to numbers and allows the numbers to be referenced by name'
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
		result = set(self.values())
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

class Tree(object, UserDict.DictMixin):
	'processes and treeifies a dictionary'
	def __init__(self, table, root, app=lambda x:x):
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

	#def normalize_keys(self):
	#	for key, value in self.children.items():
	#		if key != value.key: value.key = key
	#		value.normalize_keys()
