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
try: import yaml
except ImportError:
	try: import syck as yaml
	except ImportError:
		yaml = False

from . import debug
class GlobalNamespace(object):
	class LoggerStub(debug.DebugState):
		def __init__(self, *args):
			debug.DebugState.__init__(self, output_level='LOG_DEBUG', logfile=None, get_state=False, logfile_state=None, just_print=True)
		def swapstdout(self): pass
		def closestdout(self): pass
		def msg(self, sn, *args):
			sn = self.debugstates.get_name(self.debugstates[sn])
			print u'StubLogger: %s :: %s :: %s' % (self, sn, self.print_list(args))

	__yaml_keys = collections.defaultdict(list)
	__yaml_files = collections.defaultdict(list)
	__vardict = {'log': LoggerStub()}
	__modlock = threading.RLock()
	__options = collections.defaultdict(set)
	__all__ = []
	def __init__(self,_=None):pass


	@classmethod
	def from_yaml(cls, fn=None, data=None):
		'''Alternate constructor which initializes a GlobalNamespace instance from a YAML file'''
		if not (fn or data): raise ValueError, 'either a filename or yaml data must be supplied'
		if not yaml: raise NotImplementedError, 'yaml not found'
		fn = os.path.abspath(fn)

		# load data
		self = cls()
		if fn:
			with file(fn) as a: data = yaml.safe_load(a)

		# process data
		if data:
			for key in data:
				if key != 'root': # a toplevel dictionary named 'root' holds things which are not loaded into the new instance
					b = data[key]
					pref = ''.join(b.pop('prefix',[])) # get the prefix for the current toplevel dictionary
					options = b.pop('options', {})     # get options for the dictionary
					self.__yaml_files[fn].append(key)

					for key2, value in b.iteritems():
						self.__yaml_keys[key].append(key2)
						# apply the prefix to entries
						if isinstance(value, dict): pass
						elif hasattr(value, '__iter__'):
							value = [pref+item for item in value]
						elif isinstance(value, (str, unicode)):
							value = pref+value
						self.__addattr(key2, value, options)


			# load alternate config files
			root = data.get('root', {})
			if root.has_key('configfiles'):
				for fn in root['configfiles']:
					if os.path.exists(fn):
						cls.from_yaml(fn=fn)

		return self

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
		self.__modlock.acquire(1)
		try:
			self.__addattr(name, value)
		finally:
			self.__modlock.release()
	__setattr__ = setattr
	__setitem__ = __setattr__

	@classmethod
	def __addattr(cls, name, value, options=None):
		if not name in cls.__all__:
			cls.__all__.append(name)
		if options is not None:
			for option in options:
				cls.__options[option].add(name)
		cls.__vardict[name] = value

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
		result = cls.__vardict.get(name, default)
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
