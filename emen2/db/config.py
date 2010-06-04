import os
import sys
import functools
import optparse
import collections
import threading
import urlparse

import demjson
import yaml

import emen2.db.debug
from emen2.db.globalns import GlobalNamespace




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
		self.add_option('-h', '--home', type="string", help="EMEN2DBHOME")
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


	def getpath(self, pathname):
		# ian: todo: dynamically resolve pathnames for DB dirs
		pass


	def load_config(self, **kw):

		g = GlobalNamespace()
		# Default settings
		default_config = get_filename('emen2', 'db/config.base.yml')

		# Find EMEN2DBHOME and set to g.EMEN2DBHOME
		EMEN2DBHOME = os.getenv("EMEN2DBHOME")
		if self.values.home:
			EMEN2DBHOME = self.values.home
		print EMEN2DBHOME
		if EMEN2DBHOME:
			g.EMEN2DBHOME = EMEN2DBHOME

		# Load the default config
		g.from_yaml(default_config)
		if os.path.exists('/etc/emen2config.yml'):
			g.from_yaml('/etc/emen2config.yml')

# Load any additional config files specified
		if self.values.configfile:
			for fil in self.values.configfile:
				g.from_yaml(fil)
		print g.EMEN2DBHOME
		EMEN2DBHOME = g.EMEN2DBHOME
		def fix_paths():
			# Process relative/absolute path names in 'paths'
			for i in ["LOGPATH","ARCHIVEPATH","BACKUPPATH","TILEPATH", "TMPPATH", "SSLPATH"]:
				print g.getattr(i)
				if g.getattr(i, '') and not g.getattr(i, '').lower().startswith('/'):
					g.setattr(i, '/%s' % g.getattr(i))

		# Look for any EMEN2DBHOME-specific config files and load
		try:
			g.from_yaml(os.path.join(EMEN2DBHOME, "config.yml"))
			g.EMEN2DBHOME = EMEN2DBHOME
		except:
			pass


		# Load view and template dirs
		# g.TEMPLATEDIRS.extend(self.values.templatedirs or [])
		# g.VIEWPATHS.extend(self.values.viewdirs or [])
		if g.getattr('TEMPLATEDIRS_DEFAULT', False):
			g.TEMPLATEDIRS.append(get_filename('emen2','web/templates'))


		# print "td ", g.TEMPLATEDIRS
		#g.TEMPLATEDIRS.extend(self.values.templatedirs or [])

		# Set any overrides
		if self.values.configoverride:
			for val in self.values.configoverride:
				key, value = val.split('=')
				g.setattr(key, demjson.decode(value))


		if not g.getattr('EMEN2DBHOME', False):
			raise ValueError, "No EMEN2DBHOME / EMEN2DBHOME specified!"


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

		g.log = emen2.db.debug.DebugState(output_level=self.values.loglevel,
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


		g.log.add_output(['LOG_WEB'], emen2.db.debug.Filter(g.LOGPATH + '/access.log', 'a', 0))
		# g.log_init("Loading config files: %s"%(self.values.configfile or [default_config]))


		g.CONFIG_LOADED = True
		g.refresh()



gg = emen2.db.globalns.GlobalNamespace()
g = lambda: gg
