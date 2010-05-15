import os
import sys
import functools
import optparse
import collections
import threading
import urlparse

import demjson
import yaml

import emen2.Database.debug


def get_filename(package, resource):
	d = os.path.dirname(sys.modules[package].__file__)
	return os.path.join(d, resource)


def defaults():
	parser = DBOptions()
	parser.parse_args()



class DBOptions(optparse.OptionParser):
	
	def __init__(self, *args, **kwargs):

		kwargs["add_help_option"] = False
		optparse.OptionParser.__init__(self, *args, **kwargs)

		self.add_option('--help', action="help", help="Print help message")
		self.add_option('-h', '--home', type="string", help="DB_HOME")
		self.add_option('-c', '--configfile', action='append', dest='configfile')
		self.add_option('-q', '--quiet', action='store_true', dest='quiet', default=False)
		self.add_option('-l', '--loglevel', action='store', dest='loglevel')
		self.add_option('-s', '--setvalue', action='append', dest='configoverride')
		
		#self.add_option('-t', '--templatedir', action='append', dest='templatedirs')
		#self.add_option('-v', '--viewdirs', action='append', dest='viewdirs')
		#self.add_option('-p', '--port', action='store', dest='port')
		#self.add_option('--logfile_level', action='store', dest='logfile_level')
		#self.add_option('--logprintonly', action='store_true', dest='log_print_only', default=False)


	def parse_args(self, lc=True, *args, **kwargs):
		r1, r2 = optparse.OptionParser.parse_args(self,  *args, **kwargs)
		if lc:
			self.load_config()
		return r1, r2


	def load_config(self, **kw):

		# Default settings
		default_config = get_filename('emen2', 'Database/config.base.yml')

		# Find DB_HOME and set to g.DB_HOME
		DB_HOME = os.getenv("DB_HOME")
		if self.values.home:
			DB_HOME = self.values.home

		# Load the default config
		g = GlobalNamespace()
		g.DB_HOME = DB_HOME
		g.from_yaml(default_config)

		# Load any additional config files specified
		if self.values.configfile:
			for fil in self.values.configfile:
				g.from_yaml(fil)
		
		# Look for any DB_HOME-specific config files and load
		try:
			g.from_yaml(os.path.join(DB_HOME, "config.yml"))
		except:
			pass


		# Load view and template dirs
		# g.TEMPLATEDIRS.extend(self.values.templatedirs or [])
		# g.VIEWPATHS.extend(self.values.viewdirs or [])
		if g.getattr('TEMPLATEDIRS_DEFAULT', False):
			g.TEMPLATEDIRS.append(get_filename('emen2','web/templates'))		


		# Set any overrides
		if self.values.configoverride:
			for val in self.values.configoverride:
				key, value = val.split('=')
				g.setattr(key, demjson.decode(value))
			

		if not g.getattr('DB_HOME', False):
			raise ValueError, "No DB_HOME / DB_HOME specified!"


		# Set default log levels
		if self.values.loglevel == None:
			self.values.loglevel = kw.get('loglevel', 'LOG_DEBUG')
		# if self.values.logfile_level == None:
		# 	self.values.logfile_level = kw.get('logfile_level', 'LOG_DEBUG')
		# if self.values.log_print_only == None:
		# 	self.values.log_print_only = kw.get('log_print_only', False)

		if self.values.quiet == True:
			self.values.loglevel = kw.get('loglevel', 'LOG_ERROR')
			# self.values.logfile_level = kw.get('logfile_level', 'LOG_ERROR')


		# Make sure paths to log files exist
		if not os.path.exists(g.LOGPATH):
			os.makedirs(g.LOGPATH)


		g.LOG_CRITICAL = g.log.debugstates.LOG_CRITICAL
		g.LOG_ERROR = g.log.debugstates.LOG_ERROR
		g.LOG_WARNING = g.log.debugstates.LOG_WARNING
		g.LOG_WEB = g.log.debugstates.LOG_WEB
		g.LOG_INIT = g.log.debugstates.LOG_INIT
		g.LOG_INFO = g.log.debugstates.LOG_INFO
		g.LOG_DEBUG = g.log.debugstates.LOG_DEBUG

		g.log = emen2.Database.debug.DebugState(output_level=self.values.loglevel,
											logfile=file(g.LOGPATH + '/log.log', 'a', 0),
											get_state=False,
											quiet = self.values.quiet)

		g.log_critical = functools.partial(g.log.msg, 'LOG_CRITICAL')
		g.log_error = functools.partial(g.log.msg, 'LOG_ERROR')
		g.warn = functools.partial(g.log.msg, 'LOG_WARNING')
		g.log_init = functools.partial(g.log.msg, 'LOG_INIT')
		g.log_info = functools.partial(g.log.msg, 'LOG_INFO')
		g.debug = functools.partial(g.log.msg, 'LOG_DEBUG')
		g.debug_func = g.log.debug_func


		g.log.add_output(['LOG_WEB'], emen2.Database.debug.Filter(g.LOGPATH + '/access.log', 'a', 0))
		# g.log_init("Loading config files: %s"%(self.values.configfile or [default_config]))


		g.CONFIG_LOADED = True			
		g.refresh()





# Brought in from emen2.globalns

'''NOTE: locking is unnecessary when accessing globals, as they will automatically lock when necessary

NOTE: access globals this way:
import emen2.Database.config
g = emen2.Database.config.g()
g.<varname> accesses the variable
g.<varname> = <value> sets a variable in a threadsafe manner.

'''


class GlobalNamespace(object):
	
	
	class LoggerStub(emen2.Database.debug.DebugState):
		def __init__(self, *args):
			emen2.Database.debug.DebugState.__init__(self, output_level='LOG_DEBUG', logfile=None, get_state=False, just_print=True)
			
		def swapstdout(self):
			pass

		def closestdout(self):
			pass

		def msg(self, sn, *args):
			sn = self.debugstates.get_name(self.debugstates[sn])
			print u'StubLogger: %s :: %s :: %s' % (self, sn, self.print_list(args))


	__yaml_keys = collections.defaultdict(list)
	__yaml_files = collections.defaultdict(list)
	__vardict = {'log': LoggerStub()}
	__modlock = threading.RLock()
	__options = collections.defaultdict(set)
	__all__ = []

	def __init__(self,_=None):
		pass


	def fixpath(self, v):
		if not v: return
		if not v.startswith("/"): return os.path.join(self.DB_HOME, v)
		return v
		

	@classmethod
	def from_yaml(cls, fn=None, data=None):
		'''Alternate constructor which initializes a GlobalNamespace instance from a YAML file'''
		
		if not (fn or data):
			raise ValueError, 'Either a filename or yaml data must be supplied'

		if not yaml:
			raise NotImplementedError, "No YAML loader found"

		fn = os.path.abspath(fn)

		# load data
		self = cls()
		if fn:
			with file(fn) as a: data = yaml.safe_load(a)

		if not data:
			return
		
		print "Loading config: %s"%fn

		
		# Process relative/absolute path names in 'paths'
		for i in ["LOGPATH","ARCHIVEPATH","BACKUPPATH","TILEPATH", "TMPPATH", "SSLPATH"]:
			v = data.get('paths',dict()).get(i)
			if v:
				data['paths'][i] = self.fixpath(v)
		
		cf = map(self.fixpath, data.get('paths',dict()).get('configfiles'))
		if cf:
			data['paths']['configfiles'] = cf

		bf = data.get('paths',dict()).get('BINARYPATH', dict())	
		if bf:
			bf = [(k,self.fixpath(v)) for k,v in bf.items()]
			data['paths']['BINARYPATH'] = dict(bf)


		# process URL
		if data.get('network'):
			data['network']['EMEN2WEBROOT'] = ''


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
					value = [pref+item for item in value]
				elif isinstance(value, (str, unicode)):
					value = pref+value
				self.__addattr(key2, value, options)
		
				
		# load alternate config files
		for fn in data.get('paths',dict().get('configfiles',[])):
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



g = GlobalNamespace
__version__ = "$Revision$".split(':')[1][:-1].strip()
