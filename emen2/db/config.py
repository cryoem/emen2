# $Id$
'''This module manages EMEN2 configurations and options.

Methods:
	get_filename(package, resource)
	defaults()
	get(key, default=None)
	set(key, value)

Classes:
	DBOptions
		
'''

import os
import sys
import functools
import optparse
import collections
import threading
import urlparse

import jsonrpc.jsonutil

# EMEN2 imports
# NOTHING else should import emen2.db.globalns.
# It is a PRIVATE module.
import emen2.db.globalns
globalns = emen2.db.globalns.GlobalNamespace()

# Note:
# 	Be very careful about importing EMEN2 modules here!
# 	This module is loaded by many others, it can create circular
# 	dependencies very easily!

# import emen2.db.debug


##### Mako template lookup #####

# try:
import mako
import mako.lookup

class AddExtLookup(mako.lookup.TemplateLookup):
	"""This is a slightly modified TemplateLookup that
 	adds '.mako' extension to all template names"""

	def get_template(self, uri):
		return super(AddExtLookup, self).get_template('%s.mako'%uri)

	def render_template(self, name, ctxt):
		tmpl = self.get_template(name)
		return tmpl.render(**ctxt)

# Mako Template Loader
templates = AddExtLookup(input_encoding='utf-8')

# ian: todo:
# Module level 'get_template' and 'render_template' that
# check if the Mako module is available before calling
# templates.get_template/render_template


##### Get filename relative to a Python module #####

def get_filename(package, resource):
	'''Get the absolute path to a file inside a given Python package'''
	d = os.path.dirname(sys.modules[package].__file__)
	d = os.path.abspath(d)
	return os.path.join(d, resource)


##### Get and set configuration values #####

def defaults():
	parser = DBOptions()
	parser.parse_args()
	return parser


# "g." makes for hard to maintain code.
# Use: 
# 	import emen2.db.config
# 	emen2.db.config.get(key)

def get(key, default=None):
	return globalns.watch(key, default=default).get()


# This will eventually help lock 
# the configuration for setting	
def set(key, value):
	pass



##### Default OptionParser #####

class DBOptions(optparse.OptionParser):

	def __init__(self, *args, **kwargs):
		kwargs["add_help_option"] = False
		loginopts = kwargs.pop('loginopts', False)

		optparse.OptionParser.__init__(self, *args, **kwargs)
		# super(DBOptions, self).__init__(*args, **kwargs)

		dbhomehelp = """EMEN2 Database Environment
		[default: $EMEN2DBHOME, currently "%s"]"""%os.getenv('EMEN2DBHOME')

		if loginopts:
			logingroup = optparse.OptionGroup(self, "Login Options")
			logingroup.add_option('--username', '-U', type="string", help="Login with Account Name")
			logingroup.add_option('--password', '-P', type="string", help="... and this password")
			# logingroup.add_option('--admin', action="store_true", help="Open DB with an Admin (root) Context")
			self.add_option_group(logingroup)

		group = optparse.OptionGroup(self, "EMEN2 Base Options")
		group.add_option('-h', dest='home', type="string", help=dbhomehelp)
		group.add_option('-c', '--configfile', action='append', dest='configfile')
		group.add_option('-l', '--loglevel', action='store', dest='loglevel')
		group.add_option('--create', action="store_true", help="Create and initialize a new DB")
		group.add_option('--ext', action="append", dest='exts', help="Add Extension")
		group.add_option('--quiet', action='store_true', default=False, help="Quiet")
		group.add_option('--debug', action='store_true', default=False, help="Print debug information")
		group.add_option('--version', action='store_true', help="EMEN2 Version")
		group.add_option('--help', action="help", help="Print help message")
		group.add_option('--nosnapshot', action="store_false", dest="snapshot", default=True, help="Disable Berkeley DB Multiversion Concurrency Control (Snapshot)")
		# group.add_option('--enableroot', action="store_true", help="Enable root account. You will be prompted for an email and password.")
		self.add_option_group(group)


	def parse_args(self, lc=True, *args, **kwargs):
		r1, r2 = optparse.OptionParser.parse_args(self, *args, **kwargs)
		# r1, r2 = super(DBOptions, self).parse_args(*args, **kwargs)
		if lc:
			self.load_config()
		return r1, r2


	def opendb(self, *args, **kwargs):
		import emen2.db.database
		db = emen2.db.database.DB.opendb(*args, **kwargs)
		return db


	def resolve_ext(self, ext, extpaths):
		# Find the path to the extension
		path, name = os.path.split(ext)

		# Absolute paths are loaded directly
		if path:
			paths = filter(os.path.isdir, [ext])
		else:
			# Search EXTPATHS for a directory matching the ext name
			paths = []
			for p in filter(os.path.isdir, extpaths):
				for sp in os.listdir(p):
					if os.path.isdir(os.path.join(p, sp)) and ext == sp:
						paths.append(os.path.join(p, sp))

		if not paths:
			globalns.info('Couldn\'t find extension %s'%ext)
			return '', ''
			# continue

		# If a suitable ext was found, load..
		path = paths.pop()
		return name, path


	def load_config(self, **kw):
		if globalns.getattr('CONFIG_LOADED', False):
			return

		# Eventually 'with' will unlock/lock the globalns
		# with globalns:
		self._load_config(globalns, **kw)
		globalns.CONFIG_LOADED = True


	def _load_config(self, g, **kw):
		# 'g' is the global GlobalNamespace instance
		
		# Default configuration
		default_config = get_filename('emen2', 'db/config.base.json')

		# Load a JSON file into the GlobalNS
		g.from_file(default_config)

		# Look for EMEN2DBHOME and set to g.EMEN2DBHOME
		g.EMEN2DBHOME = self.values.home or os.getenv("EMEN2DBHOME")

		# Load other specified config files
		for f in self.values.configfile or []:
			g.from_file(f)

		# Load any config file in EMEN2DBHOME
		g.from_file(os.path.join(g.EMEN2DBHOME, "config.json"))
		g.from_file(os.path.join(g.EMEN2DBHOME, "config.yml"))

		# You must specify EMEN2DBHOME
		if not g.getattr('EMEN2DBHOME', False):
			raise ValueError, "No EMEN2DBHOME specified! You can either set the EMEN2DBHOME environment variable, or pass a directory with -h"

		# Set default log levels
		loglevel = g.getattr('LOG_LEVEL', 'INFO')
		if self.values.quiet:
			loglevel = 'ERROR'
		elif self.values.debug:
			loglevel = 'DEBUG'
		elif self.values.loglevel:
			loglevel = self.values.loglevel

		# Make sure paths to log files exist
		if not os.path.exists(g.paths.LOGPATH):
			os.makedirs(g.paths.LOGPATH)

		# todo: see emen2.db.log
		# Bind main logging method
		# logger = emen2.db.debug.DebugState(
		# 	output_level=loglevel,
		# 	logfile=file(os.path.join(g.paths.LOGPATH, 'log.log'), 'a', 0),
		# 	get_state=False,
		# 	quiet = self.values.quiet)
		# Write out WEB and SECURITY messages to dedicated log files
		# logger.add_output(['WEB'], emen2.db.debug.Filter(os.path.join(g.paths.LOGPATH, 'access.log'), 'a', 0))
		# logger.add_output(['SECURITY'], emen2.db.debug.Filter(os.path.join(g.paths.LOGPATH, 'security.log'), 'a', 0))
		# emen2.db.log.logger = logger

		# Extend the python module path
		if getattr(g.paths, 'PYTHONPATH', []):
			pp = g.paths.PYTHONPATH
			if not hasattr(pp, '__iter__'):
				pp = [pp]
			sys.path.extend(pp)

		# Add any specified extensions
		g.paths.EXTPATHS.append(get_filename('emen2', 'exts'))
		if os.getenv('EMEN2EXTPATHS'):
			for path in filter(None, os.getenv('EMEN2EXTPATHS','').split(":")):
				print '... adding path %s'%path
				g.paths.EXTPATHS.append(path)
				


		# Load the default extensions
		# I plan to add a flag to disable automatic loading.
		exts = self.values.exts or []
		if 'base' not in exts:
			exts.insert(0,'base')
		exts.extend(g.extensions.EXTS)

		# Map the extensions back to their physical directories
		# Use an OrderedDict to preserve the order
		g.extensions.EXTS = collections.OrderedDict()
		for ext in exts:
			name, path = self.resolve_ext(ext, g.paths.EXTPATHS)
			g.extensions.EXTS[name] = path
			templates.directories.insert(0, os.path.join(path, 'templates'))

		# Enable/disable snapshot
		g.params.SNAPSHOT = self.values.snapshot

		# Create new database?
		g.params.CREATE = self.values.create or False

		# Enable root user?
		# g.ENABLEROOT = self.values.enableroot or False



__version__ = "$Revision$".split(":")[1][:-1].strip()
