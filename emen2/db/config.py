# $Id$

import os
import sys
import functools
import optparse
import collections
import threading
import urlparse

import jsonrpc.jsonutil
import emen2.db.debug
import emen2.db.globalns
gg = emen2.db.globalns.GlobalNamespace()


def get_filename(package, resource):
	d = os.path.dirname(sys.modules[package].__file__)
	d = os.path.abspath(d)
	return os.path.join(d, resource)


def defaults():
	parser = DBOptions()
	parser.parse_args()
	return parser






class DBOptions(optparse.OptionParser):

	def __init__(self, *args, **kwargs):
		kwargs["add_help_option"] = False
		loginopts = kwargs.pop('loginopts', False)
		optparse.OptionParser.__init__(self, *args, **kwargs)

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
		group.add_option('--ext', action="append", dest='exts', help="Add Extension")
		group.add_option('--quiet', action='store_true', default=False, help="Quiet")
		group.add_option('--debug', action='store_true', default=False, help="Print debug information")
		group.add_option('--nosnapshot', action="store_false", dest="snapshot", default=True, help="Disable Berkeley DB Multiversion Concurrency Control (Snapshot)")
		group.add_option('--version', action='store_true', help="EMEN2 Version")
		group.add_option('--help', action="help", help="Print help message")
		self.add_option_group(group)


	def parse_args(self, lc=True, *args, **kwargs):
		r1, r2 = optparse.OptionParser.parse_args(self,  *args, **kwargs)
		if lc:
			self.load_config()
		return r1, r2


	def opendb(self, name=None, password=None):
		import emen2.db.proxy
		g = emen2.db.globalns.GlobalNamespace()

		name = name or getattr(self.values, 'name', None)
		password = password or getattr(self.values, 'password', None)
		# admin = admin or getattr(self.values, 'admin', None)

		if not g.CONFIG_LOADED:
			self.load_config()

		db = emen2.db.proxy.DBProxy()
		ctx = emen2.db.context.SpecialRootContext()
		ctx.refresh(db=db)
		db._ctx = ctx
		if name:
			db._login(name, password)
		return db


	def getpath(self, pathname):
		# ian: todo: dynamically resolve pathnames for DB dirs
		return os.path.join(gg.EMEN2DBHOME, gg.getattr(pathname))

		

	def resolve_ext(self, ext, extpaths):
		# Find the path to the extension
		path, name = os.path.split(ext)

		# Absolute paths are loaded directly
		if path:
			paths = filter(os.path.isdir, [ext])
		else:
			# Search g.EXTPATHS for a directory matching the ext name
			paths = []
			for p in filter(os.path.isdir, extpaths):
				for sp in os.listdir(p):
					if os.path.isdir(os.path.join(p, sp)) and ext == sp:
						paths.append(os.path.join(p, sp))

		if not paths:
			config.info('Couldn\'t find extension %s'%ext)
			return
			# continue

		# If a suitable ext was found, load..
		path = paths.pop()
		return name, path




	def load_config(self, **kw):
		g = emen2.db.globalns.GlobalNamespace()
		if g.getattr('CONFIG_LOADED', False):
			return
		else:
			return self.load_config_force(g, **kw)


	def load_config_force(self, g, **kw):
		# Default settings
		default_config = get_filename('emen2', 'db/config.base.json')
		g.from_file(default_config)

		# Find EMEN2DBHOME and set to g.EMEN2DBHOME
		g.EMEN2DBHOME = self.values.home or os.getenv("EMEN2DBHOME")
		
		# Load other specified config files
		for fil in self.values.configfile or []:
			g.from_file(fil)

		# Load any config file in EMEN2DBHOME
		g.from_file(os.path.join(g.EMEN2DBHOME, "config.json"))
		g.from_file(os.path.join(g.EMEN2DBHOME, "config.yml"))

		if not g.getattr('EMEN2DBHOME', False):
			raise ValueError, "No EMEN2DBHOME specified! You can either set the EMEN2DBHOME environment variable, or pass a directory with -h"

		if not os.path.exists(g.EMEN2DBHOME):
			raise ValueError, "EMEN2DBHOME directory %s does not exist"%g.EMEN2DBHOME

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

		# Bind main logging method
		g.log = emen2.db.debug.DebugState(output_level=loglevel,
											logfile=file(os.path.join(g.paths.LOGPATH, 'log.log'), 'a', 0),
											get_state=False,
											quiet = self.values.quiet)

		# Bind other logging methods
		g.info = functools.partial(g.log.msg, 'INFO')
		g.init = functools.partial(g.log.msg, 'INIT')
		g.error = functools.partial(g.log.msg, 'ERROR')
		g.warn = functools.partial(g.log.msg, 'WARNING')
		g.debug = functools.partial(g.log.msg, 'DEBUG')

		# Extend the python module path
		if getattr(g.paths, 'PYTHONPATH', []):
			pp = g.paths.PYTHONPATH
			if not hasattr(pp, '__iter__'):
				pp = [pp]
			sys.path.extend(pp)

		# Add any specified extensions
		g.paths.EXTPATHS.append(get_filename('emen2', 'web/exts'))

		# Load the default extensions
		# I plan to add a flag to disable automatic loading.
		exts = self.values.exts or []
		#if 'default' not in exts:
		#	exts.insert(0,'default')	
		if 'base' not in exts:
			exts.insert(0,'base')		
			
		# Map the extensions back to their physical directories
		# Use an OrderedDict to preserve the order
		g.EXTS = collections.OrderedDict()
		for ext in exts:
			name, path = self.resolve_ext(ext, g.paths.EXTPATHS)
			g.EXTS[name] = path
		
		# Enable/disable snapshot
		g.SNAPSHOT = self.values.snapshot

		# Write out WEB and SECURITY messages to dedicated log files
		g.log.add_output(['WEB'], emen2.db.debug.Filter(os.path.join(g.paths.LOGPATH, 'access.log'), 'a', 0))
		g.log.add_output(['SECURITY'], emen2.db.debug.Filter(os.path.join(g.paths.LOGPATH, 'security.log'), 'a', 0))

		g.CONFIG_LOADED = True
		g.refresh()




g = lambda: gg


__version__ = "$Revision$".split(":")[1][:-1].strip()
