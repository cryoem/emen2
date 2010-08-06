# $Author$ $Revision$
from __future__ import with_statement
'''NOTE: locking is unnecessary when accessing globals, as they will automatically lock when necessary

NOTE: access globals this way:
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')
g.<varname> accesses the variable
g.<varname> = <value> sets a variable in a threadsafe manner.'''

import collections
import threading
import os
import os.path
import UserDict
try: import yaml
except ImportError:
	try: import syck as yaml
	except ImportError:
		yaml = False

from . import debug
class dictWrapper(object, UserDict.DictMixin):
	def __init__(self, dict_, prefix):
		self.__dict = dict_
		self.__prefix = prefix
	def __repr__(self):
		return '<dictWrapper dict: %r>' % self.__dict
	def keys(self): return self.__dict.keys()
	def __getitem__(self, name):
		v = self.__dict[name]
		if not v.startswith('/'):
			v = os.path.join(self.__prefix, v)
		return v
	def __setitem__(self, name, value):
		if isinstance(value, (str, unicode)):
			if value.startswith(self.__prefix):
				del value[len(self.__prefix):]
		self.__dict[name] = value
	def __delitem__(self, name):
		del self.__dict[name]

class listWrapper(object):
	def __init__(self, list_, prefix):
		self.__list = list_
		self.__prefix = prefix
	def __repr__(self):
		return '<listWrapper list: %r>' % self.__list
	def check_item(self, item):
		if isinstance(item, (str, unicode)):
			item = os.path.join(self.__prefix, item)
		return item
	def __iter__(self):
		for item in self.__list:
			yield self.check_item(item)
	def __getitem__(self, k):
		return self.check_item(self.__list[k])
	def chopitem(self, item):
		if isinstance(item, (str, unicode)):
			if item.startswith(self.__prefix):
				item = item[len(self.__prefix):]
		return item
	def __setitem__(self, key, value):
		value = self.chopitem(value)
		self.__list[key] = value
	def __delitem__(self, idx):
		del self.__list[idx]
	def append(self, item):
		item = self.chopitem(item)
		self.__list.append(item)
	def extend(self, items):
		self.__list.extend(self.chopitem(item) for item in items)
	def pop(self, idx):
		res = self[idx]
		del self[idx]
		return res
	def count(self, item):
		return self.__list.count(self.chopitem(item))
	def insert(self, idx, item):
		self.__list.insert(idx, self.chopitem(item))
	def __len__(self): return len(self.__list)

class LockedNamespaceError(TypeError): pass

inst = lambda x:x()
class GlobalNamespace(object):
	class LoggerStub(debug.DebugState):
		def __init__(self, *args):
			debug.DebugState.__init__(self, output_level='LOG_DEBUG', logfile=None, get_state=False, logfile_state=None, just_print=True)
		def swapstdout(self): pass
		def closestdout(self): pass
		def msg(self, sn, *args):
			sn = self.debugstates.get_name(self.debugstates[sn])
			print u'StubLogger: %s :: %s :: %s' % (self, sn, self.print_list(args))

	@inst
	class paths(object):
		__root = ['']
		@property
		def root(self): return self.__root[0]
		@root.setter
		def root(self, v):
			self.__root.insert(0, v)
		def update(self, path):
			self.root = path
		def __getattribute__(self, name):
			value = object.__getattribute__(self, name)
			if name != 'root' and not name.startswith('_'):
				if isinstance(value, (str, unicode)):
					if value.startswith('/'): pass
					else:
						value = os.path.join(self.root, value)
				elif hasattr(value, '__iter__'):
					if hasattr(value, 'items'):
						value = dictWrapper(value, self.root)
					else:
						value = listWrapper(value, self.root)
			return value

	__yaml_keys = collections.defaultdict(list)
	__yaml_files = collections.defaultdict(list)
	__vardict = {'log': LoggerStub()}
	__modlock = threading.RLock()
	__options = collections.defaultdict(set)
	__all__ = []

	@classmethod
	def check_locked(cls):
		try:
			cls.__locked
			#print 'ns __locked 0', cls.__locked
		except AttributeError: cls.__locked = False
		#print 'ns __locked 1', cls.__locked

	@property
	def _locked(self):
		self.check_locked()
		return self.__locked
	@_locked.setter
	def _locked(self, value):
		if not self.__locked:
			#print 'hi'
			self.__class__.__locked = bool(value)
			#print 'ns __locked 2', self.__locked
		elif bool(value) == False:
			raise LockedNamespaceError, 'cannot unlock %s' % self.__class__.__name__

	def __unlock(self):
		'''unlock namespace (for internal/debug use only)'''
		self.__locked = False

	def __init__(self,_=None): pass

	def fixpath(self, v):
		if not v: return
		if not v.startswith("/"): return os.path.join(self.EMEN2DBHOME, v)
		return v



	@classmethod
	def from_yaml(cls, fn=None, data=None):
		'''Alternate constructor which initializes a GlobalNamespace instance from a YAML file'''

		if not (fn or data):
			raise ValueError, 'Either a filename or yaml data must be supplied'

		if not yaml: raise NotImplementedError, "No YAML loader found"

		fn = os.path.abspath(fn)

		# load data
		self = cls()
		if fn and os.path.exists(fn):
			with file(fn) as a: data = yaml.safe_load(a)

		if not data:
			return

		self.log.msg('LOG_INIT', "Loading config: %s"%fn)
		self.EMEN2DBHOME = data.pop('EMEN2DBHOME', self.getattr('EMEN2DBHOME', ''))
		self.log.msg('LOG_INIT', 'EMEN2DBHOME %r' % self.EMEN2DBHOME)
		self.paths.root = self.EMEN2DBHOME

		paths = data.pop('paths', {})
		for k,v in paths.items(): setattr(self.paths, k, v)


		# process data
		for key in data:
			b = data[key]
			pref = ''.join(b.pop('prefix',[])) # get the prefix for the current toplevel dictionary
			options = b.pop('options', {})     # get options for the dictionary
			self.__yaml_files[fn].append(key)

			for key2, value in b.iteritems():
				self.__yaml_keys[key].append(key2)
				# apply the prefix to entries
				if isinstance(value, dict): pass
				elif hasattr(value, '__iter__'):
					value = [os.path.join(pref,item) for item in value]
				elif isinstance(value, (str, unicode)):
					value = os.path.join(pref,value)
				self.__addattr(key2, value, options)


		# load alternate config files
		for fn in paths.get('configfiles', []):
			if os.path.exists(fn):
				cls.from_yaml(fn=fn)


		return self

	# @classmethod
	# def from_yaml(cls, fn=None, data=None):
	# 	'''Alternate constructor which initializes a GlobalNamespace instance from a YAML file'''
	# 	if not (fn or data): raise ValueError, 'either a filename or yaml data must be supplied'
	# 	if not yaml: raise NotImplementedError, 'yaml not found'
	# 	fn = os.path.abspath(fn)
	#
	# 	# load data
	# 	self = cls()
	# 	if fn:
	# 		with file(fn) as a: data = yaml.safe_load(a)
	#
	# 	# process data
	# 	if data:
	# 		for key in data:
	# 			if key != 'root': # a toplevel dictionary named 'root' holds things which are not loaded into the new instance
	# 				b = data[key]
	# 				pref = ''.join(b.pop('prefix',[])) # get the prefix for the current toplevel dictionary
	# 				options = b.pop('options', {})     # get options for the dictionary
	# 				self.__yaml_files[fn].append(key)
	#
	# 				for key2, value in b.iteritems():
	# 					self.__yaml_keys[key].append(key2)
	# 					# apply the prefix to entries
	# 					if isinstance(value, dict): pass
	# 					elif hasattr(value, '__iter__'):
	# 						value = [pref+item for item in value]
	# 					elif isinstance(value, (str, unicode)):
	# 						value = pref+value
	# 					self.__addattr(key2, value, options)
	#
	#
	# 		# load alternate config files
	# 		root = data.get('root', {})
	# 		if root.has_key('configfiles'):
	# 			for fn in root['configfiles']:
	# 				if os.path.exists(fn):
	# 					cls.from_yaml(fn=fn)
	#
	# 	return self

	def to_yaml(self, keys=None, kg=None, file=None, fs=0):
		'''store state as YAML'''
		if keys is not None:
			keys = keys
		elif kg is not None:
			keys = dict( (k, self.__yaml_keys[k]) for k in kg)
		elif file is not None:
			keys = dict( (k, self.__yaml_keys[k]) for k in self.__yaml_files[file] )
		else:
			keys = self.__yaml_keys
		# file = __builtins__['file']

		_dict = collections.defaultdict(dict)
		for key, value in keys.iteritems():
			for k2 in value:
				_dict[key][k2] = self.getattr(k2)
		return yaml.safe_dump(dict(_dict), default_flow_style=fs)

	@classmethod
	def setattr(self, name, value):
		#if name == 'paths': raise AttributeError, 'cannot set attribute paths of %r' % self
		self.__modlock.acquire(1)
		try:
			self.__addattr(name, value)
		finally:
			self.__modlock.release()
	def __setattr__(self, name, value):
		if hasattr(getattr(self.__class__, name, None), '__set__'):
			object.__setattr__(self, name, value)
		else:
			self.setattr(name, value)
	__setitem__ = __setattr__

	@classmethod
	def __addattr(cls, name, value, options=None):
		if not name in cls.__all__:
			cls.__all__.append(name)
		cls.check_locked()
		if name.startswith('_') or not cls.__locked:
			if options is not None:
				for option in options:
					cls.__options[option].add(name)
			cls.__vardict[name] = value
		else: raise LockedNamespaceError, 'cannot change locked namespace'

	@classmethod
	def refresh(cls):
		cls.__all__ = [x for x in cls.__vardict.keys() if x[0] != '_']
		cls.__all__.append('refresh')

	@classmethod
	def getattr(cls, name, default=None):
		if name.startswith('___'):
			name = name.partition('___')[-1]
		if cls.__options.has_key('private'):
			if name in cls.__options['private']:
				return default
		if name.startswith('_'): result = object.__getattr__(cls, name, default)
		else: result = cls.__vardict.get(name, default)
		return result
	@classmethod
	def keys(cls):
		private = cls.__options['private']
		return [k for k in cls.__vardict.keys() if k not in private]

	@classmethod
	def getprivate(cls, name):
		if name.startswith('___'):
			name = name.partition('___')[-1]
		result = cls.__vardict.get(name)
		return result


	def __getattribute__(self, name):
		result = None
		try:
			result = object.__getattribute__(self, name)
		except AttributeError:
			result = object.__getattribute__(self, 'getattr')(name)
			if result == None:
				try:
					result = object.__getattribute__(self, name)
				except AttributeError:
					pass

		if result == None:
			raise AttributeError('Attribute Not Found: %s' % name)

		else:
			return result
	__getitem__ = __getattribute__

	def update(self, dict):
		self.__vardict.update(dict)

	def reset(self):
		self.__class__.__vardict = {}





def test():
	a = GlobalNamespace('one instance')
	b = GlobalNamespace('two instance')
	try:
		a.a
	except AttributeError:
		pass
	else:
		assert False

	#test 1 attribute access
	a.a = 1
	assert (a.a == a.a)
	assert (a.a == b.a)
	assert (a.a == a.___a)
	print "test 1 passed"

	#test 2
	a.reset()
	try:
		print a.a
	except AttributeError:
		pass
	else:
		assert False
	print "test 2 passed"

	#test 3
	tempdict = dict(a=1, b=2, c=3)
	a.update(tempdict)
	assert tempdict['a'] == a.a
	assert tempdict['a'] == b.a
	assert tempdict['a'] == a.___a
	print "test 3 passed"
	a.reset()

if __name__ == '__main__':
	test()
__version__ = "$Revision$".split(':')[1][:-1].strip()
