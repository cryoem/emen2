# $Id$
"""This module manages EMEN2 configurations and options.

Methods:
	get_filename(package, resource)
	defaults()
	get(key, default=None)
	set(key, value)

Classes:
	DBOptions

"""

import os
import sys
import glob
import functools
import operator
import optparse
import collections
import threading
import urlparse
import imp

import jsonrpc.jsonutil

basestring = (str, unicode)
# EMEN2 imports
# NOTHING else should import emen2.db.globalns.
# It is a PRIVATE module.
import emen2.db.globalns

# Note:
# 	Be very careful about importing EMEN2 modules here!
# 	This module is loaded by many others, it can create circular
# 	dependencies very easily!


##### Mako template lookup #####

# try:
import mako
import mako.lookup

class AddExtLookup(mako.lookup.TemplateLookup):
	"""This is a slightly modified TemplateLookup that
 	adds '.mako' extension to all template names.

	Extends TemplateLookup methods:
		get_template		Adds '.mako' to filenames
		render_template		""

	"""

	def get_template(self, uri):
		return super(AddExtLookup, self).get_template('%s.mako'%uri)

	def render_template(self, name, ctxt):
		tmpl = self.get_template(name)
		return tmpl.render(**ctxt)

# Mako Template Loader
templates = AddExtLookup(input_encoding='utf-8')



##### Module-level config methods #####

def get_filename(package, resource):
	"""Get the absolute path to a file inside a given Python package"""
	d = os.path.dirname(sys.modules[package].__file__)
	d = os.path.abspath(d)
	return os.path.join(d, resource)


def get(key, default=None, rv=True):
	"""Get a configuration value.

	:param key: Configuration key
	:keyword default: Default value if key is not found
	:return: Configuration value

	"""
	result = globalns.watch(key, default=default)
	if rv:
		result = result.get()
	return result


# This will eventually help lock
# the configuration for setting
def set(key, value):
	"""Set a configuration value.

	:param key: Configuration key
	:param value: Configuration value

	"""
	raise NotImplementedError, "Soon."



##### Extensions #####

def load_exts():
	for ext in globalns.extensions.EXTS:
		load_ext(ext)

def load_views():
	for ext in globalns.extensions.EXTS:
		load_view(ext)

def load_jsons(cb=None):
	for ext in globalns.extensions.EXTS:
		load_json(ext, cb=cb)

def load_ext(ext):
	modulename = 'emen2.exts.%s'%ext
	# print "Loading extension...", modulename
	if modulename in sys.modules:
		print "%s already loaded"%modulename
		return
	paths = list(globalns.paths.EXTPATHS)
	module = imp.find_module(ext, paths)
	ret = imp.load_module(ext, *module)
	# Extensions may have an optional "templates" directory,
	# which will be added to the template search path.
	templates.directories.insert(0, os.path.join(module[1], 'templates'))
	return ret

def load_view(ext):
	# Extensions may have an optional "views" module.
	modulename = 'emen2.exts.%s.views'%ext
	# print "Loading views...", modulename
	if modulename in sys.modules:
		print "%s already loaded"%modulename
		return
	paths = list(globalns.paths.EXTPATHS)
	module = imp.find_module(ext, paths)
	path = module[1]
	try:
		viewmodule = imp.find_module('views', [path])
	except ImportError, e:
		viewmodule = None
	if viewmodule:
		imp.load_module(modulename, *viewmodule)


def load_json(ext, cb=None):
	modulename = 'emen2.exts.%s.json'%ext
	# print "Loading json...", modulename
	path = resolve_ext(ext)
	if not cb:
		return
	for j in sorted(glob.glob(os.path.join(path, 'json', '*.json'))):
		cb(j)

def resolve_ext(ext):
	paths = list(globalns.paths.EXTPATHS)
	return imp.find_module(ext, paths)[1]


class Config(object):
	globalns = emen2.db.globalns.GlobalNamespace()

	def from_files(self, *files):
		'''Load several files

		:param files: a list of configuration file filenames to be loaded'''
		for file_ in files:
			self.load_file(file_)

	def __init__(self):
		default_config = get_filename('emen2', 'db/config.base.json')
		self.load_file(default_config)

	def load_file(self, fn):
		'''Load a single configuration file

		:param fn: the filename of the configuration file'''
		print 'Loading Configuration file: %s' % fn
		self.globalns.from_file(fn)

	def load_data(self, *args, **data):
		'''Load configuration variables into the namespace'''
		if args:
			for dct in args:
				self.load_data(**dct)

		for key, value in data.items():
			self.globalns.setattr(key, value)

	def require_variable(self, var_name, value=None, err_msg=None):
		'''Assert that a certain variable has been loaded

		:param var_name: the variable to be checked
		:param value: the value it should have, if this is None, the value is ignored
		:param err_msg: the error message to be displayed if the variable is not found
		:raises ValueError: if the variable is not found'''

		#NOTE: if we want None to be a valid config option, this must change
		if value is not None and self.globalns.getattr(var_name, value) != value:
			raise ValueError(err_msg)
		elif self.globalns.getattr(var_name) is None:
			raise ValueError(err_msg)
		else:
			return True

#temporary
globalns = Config.globalns

##### Default OptionParser #####

from twisted.python import usage

dbhomehelp = """EMEN2 Database Environment
[default: $EMEN2DBHOME, currently "%s"]"""%os.getenv('EMEN2DBHOME')

class DBOptions(usage.Options):
	optFlags = [
		['create', None, 'Create and initialize a new DB'],
		['quiet', None, 'Quiet'],
		['debug', None, 'Print debug'],
		['version', None, 'EMEN2 Version'],
		['nosnapshot', None, 'Disable Berkeley DB Multiversion Concurrency Control (Snapshot)']
	]

	optParameters = [
		['home', 'h', None, dbhomehelp],
		['ext', 'e', None, 'Add Extension; can be comma-separated.'],
		['loglevel', 'l', None, ''],
	]

	def opt_configfile(self, file_):
		self.setdefault('configfile', []).append(file_)
	opt_c = opt_configfile

	def postProcess(self):
		## note that for optFlags self[option_name] is 1 if the option is given and 0 otherwise
		## 	this converts those values into the appropriate bools

		# these ones default to True:
		for option_name in ['create', 'quiet', 'debug', 'version']:
			self[option_name] = bool(self[option_name])

		# these ones default to False:
		for option_name in ['nosnapshot']:
			self[option_name] = not bool(self[option_name])


class DBLoginOptions(DBOptions):
	optParameters = [
		['username', 'U', None, "Login with Account Name"],
		['password', 'P', None, "... and this password"]
	]

class CommandLineParser(object):
	#Note...
	def __init__(self, _, options, **kwargs):
		lc = kwargs.pop('lc', True)
		self.options = options
		self.kwargs = kwargs

		self.config = Config()
		if lc:
			self.load_config()


	def opendb(self, *args, **kwargs):
		import emen2.db.database
		db = emen2.db.database.DB.opendb(*args, **kwargs)
		return db


	def load_config(self, **kw):
		if self.config.globalns.getattr('CONFIG_LOADED', False): return

		# Eventually 'with' will unlock/lock the globalns
		# with globalns:
		self._load_config(self.config.globalns, **kw)

		self.config.globalns.CONFIG_LOADED = True


	def _load_config(self, g, **kw):
		# 'g' is the global GlobalNamespace instance

		## Default configuration
		#default_config = get_filename('emen2', 'db/config.base.json')

		## Load a JSON file into the GlobalNS
		#g.from_file(default_config)

		# Look for EMEN2DBHOME and set to g.EMEN2DBHOME

		self.config.load_data(
			EMEN2DBHOME = self.options.get('home', os.getenv("EMEN2DBHOME"))
		)

		# Load other specified config files
		print self.options.get('configfile', [])
		self.config.from_files(
			*self.options.get('configfile', [])
		)
		print self.config.globalns.EMEN2DBHOME

		# You must specify EMEN2DBHOME
		self.config.require_variable('EMEN2DBHOME', None,
			err_msg="No EMEN2DBHOME specified! You can either set the EMEN2DBHOME environment variable, or pass a directory with -h")

		# Load any config file in EMEN2DBHOME
		self.config.from_files(
			os.path.join(g.EMEN2DBHOME, "config.json"),
			os.path.join(g.EMEN2DBHOME, "config.yml")
		)

		# Set default log levels
		loglevel = g.getattr('LOG_LEVEL', 'INFO')
		if self.options['quiet']:
			loglevel = 'ERROR'
		elif self.options['debug']:
			loglevel = 'DEBUG'
		elif self.options['loglevel']:
			loglevel = self.options['loglevel']
		self.config.load_data(LOG_LEVEL=loglevel)

		# Make sure paths to log files exist
		if not os.path.exists(g.paths.LOGPATH):
			os.makedirs(g.paths.LOGPATH)

		# Extend the python module path
		if getattr(g.paths, 'PYTHONPATH', []):
			pp = g.paths.PYTHONPATH
			if not hasattr(pp, '__iter__'):
				pp = [pp]
			sys.path.extend(pp)

		# Add any specified extensions
		# EXTPATHS points to directories containing emen2 ext modules.
		# This will be used with imp.find_module(ext, g.paths.EXTPATHS)
		g.paths.EXTPATHS.append(get_filename('emen2', 'exts'))
		if os.getenv('EMEN2EXTPATHS'):
			for path in filter(None, os.getenv('EMEN2EXTPATHS','').split(":")):
				g.paths.EXTPATHS.append(path)

		# Load the default extensions
		# I plan to add a flag to disable automatic loading.
		exts = kw.get('exts', [])
		exts = ( i.split(",") for i in exts )
		exts = sum(exts, [])

		if 'base' not in exts:
			exts.insert(0,'base')
		exts.extend(g.extensions.EXTS)

		# Map the extensions back to their physical directories
		# Use an OrderedDict to preserve the order
		g.extensions.EXTS = exts

		# Enable/disable snapshot
		g.params.SNAPSHOT = self.options['nosnapshot']

		# Create new database?
		print self.options['create'], '<<<<<<<<<<<<<<<<<<<<<<<'
		#g.params.CREATE = self.options['create']

		# Enable root user?
		# g.ENABLEROOT = self.values.enableroot or False




__version__ = "$Revision$".split(":")[1][:-1].strip()

#class old_DBOptions(optparse.OptionParser):
#
#	def __init__(self, *args, **kwargs):
#		kwargs["add_help_option"] = False
#		loginopts = kwargs.pop('loginopts', False)
#
#		optparse.OptionParser.__init__(self, *args, **kwargs)
#		# super(DBOptions, self).__init__(*args, **kwargs)
#
#		dbhomehelp = """EMEN2 Database Environment
#		[default: $EMEN2DBHOME, currently "%s"]"""%os.getenv('EMEN2DBHOME')
#
#		if loginopts:
#			logingroup = optparse.OptionGroup(self, "Login Options")
#			logingroup.add_option('--username', '-U', type="string", help="Login with Account Name")
#			logingroup.add_option('--password', '-P', type="string", help="... and this password")
#			# logingroup.add_option('--admin', action="store_true", help="Open DB with an Admin (root) Context")
#			self.add_option_group(logingroup)
#
#		group = optparse.OptionGroup(self, "EMEN2 Base Options")
#		group.add_option('-h', dest='home', type="string", help=dbhomehelp)
#		group.add_option('-e', '--ext', action="append", dest='exts', help="Add Extension; can be comma-separated.")
#		group.add_option('-c', '--configfile', action='append', dest='configfile')
#		group.add_option('-l', '--loglevel', action='store', dest='loglevel')
#		group.add_option('--create', action="store_true", help="Create and initialize a new DB")
#		group.add_option('--quiet', action='store_true', default=False, help="Quiet")
#		group.add_option('--debug', action='store_true', default=False, help="Print debug information")
#		group.add_option('--version', action='store_true', help="EMEN2 Version")
#		group.add_option('--help', action="help", help="Print help message")
#		group.add_option('--nosnapshot', action="store_false", dest="snapshot", default=True, help="Disable Berkeley DB Multiversion Concurrency Control (Snapshot)")
#		# group.add_option('--enableroot', action="store_true", help="Enable root account. You will be prompted for an email and password.")
#		self.add_option_group(group)
#
#
#	def parse_args(self, lc=True, *args, **kwargs):
#		r1, r2 = optparse.OptionParser.parse_args(self, *args, **kwargs)
#		# r1, r2 = super(DBOptions, self).parse_args(*args, **kwargs)
#		if lc:
#			self.load_config()
#		return r1, r2
#
#
#	def opendb(self, *args, **kwargs):
#		import emen2.db.database
#		db = emen2.db.database.DB.opendb(*args, **kwargs)
#		return db
#
#
#	def load_config(self, **kw):
#		if globalns.getattr('CONFIG_LOADED', False):
#			return
#
#		# Eventually 'with' will unlock/lock the globalns
#		# with globalns:
#		self._load_config(globalns, **kw)
#		globalns.CONFIG_LOADED = True
#
#
#	def _load_config(self, g, **kw):
#		# 'g' is the global GlobalNamespace instance
#
#		## Default configuration
#		#default_config = get_filename('emen2', 'db/config.base.json')
#
#		## Load a JSON file into the GlobalNS
#		#g.from_file(default_config)
#
#		# Look for EMEN2DBHOME and set to g.EMEN2DBHOME
#		config = Config()
#
#		g.EMEN2DBHOME = self.values.home or os.getenv("EMEN2DBHOME")
#		config.load_data(
#			EMEN2DBHOME = self.values.home or os.getenv("EMEN2DBHOME")
#		)
#
#		# Load other specified config files
#		config.from_files( *(self.values.configfile or []) )
#
#		# You must specify EMEN2DBHOME
#		config.require_variable(EMEN2DBHOME, False,
#			err_msg="No EMEN2DBHOME specified! You can either set the EMEN2DBHOME environment variable, or pass a directory with -h")
#
#		# Load any config file in EMEN2DBHOME
#		config.from_files(
#			os.path.join(g.EMEN2DBHOME, "config.json"),
#			os.path.join(g.EMEN2DBHOME, "config.yml")
#		)
#
#		# Set default log levels
#		loglevel = g.getattr('LOG_LEVEL', 'INFO')
#		if self.values.quiet:
#			loglevel = 'ERROR'
#		elif self.values.debug:
#			loglevel = 'DEBUG'
#		elif self.values.loglevel:
#			loglevel = self.values.loglevel
#		config.load_data(LOG_LEVEL=loglevel)
#
#		# Make sure paths to log files exist
#		if not os.path.exists(g.paths.LOGPATH):
#			os.makedirs(g.paths.LOGPATH)
#
#		# Extend the python module path
#		if getattr(g.paths, 'PYTHONPATH', []):
#			pp = g.paths.PYTHONPATH
#			if not hasattr(pp, '__iter__'):
#				pp = [pp]
#			sys.path.extend(pp)
#
#		# Add any specified extensions
#		# EXTPATHS points to directories containing emen2 ext modules.
#		# This will be used with imp.find_module(ext, g.paths.EXTPATHS)
#		g.paths.EXTPATHS.append(get_filename('emen2', 'exts'))
#		if os.getenv('EMEN2EXTPATHS'):
#			for path in filter(None, os.getenv('EMEN2EXTPATHS','').split(":")):
#				g.paths.EXTPATHS.append(path)
#
#		# Load the default extensions
#		# I plan to add a flag to disable automatic loading.
#		exts = kw.get('exts', [])
#		exts = ( i.split(",") for i in exts )
#		exts = sum(exts, [])
#
#		if 'base' not in exts:
#			exts.insert(0,'base')
#		exts.extend(g.extensions.EXTS)
#
#		# Map the extensions back to their physical directories
#		# Use an OrderedDict to preserve the order
#		g.extensions.EXTS = exts
#
#		# Enable/disable snapshot
#		g.params.SNAPSHOT = self.values.snapshot
#
#		# Create new database?
#		g.params.CREATE = self.values.create or False
#
#		# Enable root user?
#		# g.ENABLEROOT = self.values.enableroot or False
#
