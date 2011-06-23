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
		group.add_option('--ext', action="append", dest='ext', help="Add Extension")
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
		if os.path.exists('/etc/emen2config.yml'):
			g.from_file('/etc/emen2config.yml')
		if os.path.exists('/etc/emen2config.json'):
			g.from_file('/etc/emen2config.json')
		if self.values.configfile:
			for fil in self.values.configfile:
				g.from_file(fil)


		# Find EMEN2DBHOME and set to g.EMEN2DBHOME
		EMEN2DBHOME = os.getenv("EMEN2DBHOME") or g.getattr('EMEN2DBHOME', '')
		if self.values.home:
			EMEN2DBHOME = self.values.home
		if EMEN2DBHOME:
			g.EMEN2DBHOME = EMEN2DBHOME

		# Load the default config
		# Look for any EMEN2DBHOME-specific config files and load
		g.from_file(os.path.join(EMEN2DBHOME, "config.json"))
		g.from_file(os.path.join(EMEN2DBHOME, "config.yml"))
		g.EMEN2DBHOME = EMEN2DBHOME

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
			print 'Creating logpath: %r' % g.paths.LOGPATH
			os.makedirs(g.paths.LOGPATH)
		g.log = emen2.db.debug.DebugState(output_level=loglevel,
											logfile=file(g.paths.LOGPATH + '/log.log', 'a', 0),
											get_state=False,
											quiet = self.values.quiet)

		g.info = functools.partial(g.log.msg, 'INFO')
		g.error = functools.partial(g.log.msg, 'ERROR')
		g.warn = functools.partial(g.log.msg, 'WARNING')
		g.debug = functools.partial(g.log.msg, 'DEBUG')

		# Load web extensions
		for p in self.values.ext or []:
			g.paths.TEMPLATEPATHS.append(os.path.join(p, 'templates'))
			g.paths.VIEWPATHS.append(os.path.join(p, 'views'))

		# Load view and template dirs
		if g.getattr('TEMPLATEPATHS_DEFAULT', False):
			g.error('LOADING DEFAULT TEMPLATEPATHS !!!')
			g.paths.TEMPLATEPATHS.append(get_filename('emen2','templates'))

		if getattr(g.paths, 'PYTHONPATH', []):
			pp = g.paths.PYTHONPATH
			if not hasattr(pp, '__iter__'): pp = [pp]
			sys.path.extend(pp)

		# Enable/disable snapshot
		g.SNAPSHOT = self.values.snapshot

		g.log.add_output(['WEB'], emen2.db.debug.Filter(g.paths.LOGPATH + '/access.log', 'a', 0))
		g.log.add_output(['SECURITY'], emen2.db.debug.Filter(g.paths.LOGPATH + '/security.log', 'a', 0))

		g.CONFIG_LOADED = True
		g.refresh()




g = lambda: gg


__version__ = "$Revision$".split(":")[1][:-1].strip()
