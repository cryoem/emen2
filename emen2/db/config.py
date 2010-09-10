import os
import sys
import functools
import optparse
import collections
import threading
import urlparse

import emen2.util.jsonutil

import emen2.db.debug
from emen2.db.globalns import GlobalNamespace




def get_filename(package, resource):
	d = os.path.dirname(sys.modules[package].__file__)
	d = os.path.abspath(d)
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
		gg.log_info(os.path.join(gg.EMEN2DBHOME, gg.getattr(pathname)))
		return os.path.join(gg.EMEN2DBHOME, gg.getattr(pathname))


	def load_config(self, **kw):

		g = GlobalNamespace()
		# Default settings
		default_config = get_filename('emen2', 'db/config.base.json')

		# Find EMEN2DBHOME and set to g.EMEN2DBHOME
		EMEN2DBHOME = os.getenv("EMEN2DBHOME")
		if self.values.home:
			EMEN2DBHOME = self.values.home
		if EMEN2DBHOME:
			g.EMEN2DBHOME = EMEN2DBHOME

		# Load the default config
		g.from_file(default_config)
		if os.path.exists('/etc/emen2config.json'):
			g.from_file('/etc/emen2config.json')

		# Load any additional config files specified
		if self.values.configfile:
			for fil in self.values.configfile:
				g.from_file(fil)
		EMEN2DBHOME = g.EMEN2DBHOME

		# Look for any EMEN2DBHOME-specific config files and load
		try:
			g.from_file(os.path.join(EMEN2DBHOME, "config.json"))
			g.EMEN2DBHOME = EMEN2DBHOME
		except:
			raise
			pass


		# Load view and template dirs
		# g.TEMPLATEDIRS.extend(self.values.templatedirs or [])
		# g.VIEWPATHS.extend(self.values.viewdirs or [])
		if g.getattr('TEMPLATEDIRS_DEFAULT', False):
			g.paths.TEMPLATEDIRS.append(get_filename('emen2','web/templates'))


		# print "td ", g.TEMPLATEDIRS
		#g.TEMPLATEDIRS.extend(self.values.templatedirs or [])

		# Set any overrides
		if self.values.configoverride:
			for val in self.values.configoverride:
				key, value = val.split('=')
				g.setattr(key, emen2.util.jsonutil.decode(value))


		if not g.getattr('EMEN2DBHOME', False):
			raise ValueError, "No EMEN2DBHOME / EMEN2DBHOME specified!"


		# Set default log levels
		if self.values.loglevel == None:
			self.values.loglevel = kw.get('loglevel', g.getattr('LOG_LEVEL', 'LOG_INFO'))
		# if self.values.logfile_level == None:
		# 	self.values.logfile_level = kw.get('logfile_level', 'LOG_DEBUG')
		# if self.values.log_print_only == None:
		# 	self.values.log_print_only = kw.get('log_print_only', False)

		if self.values.quiet == True:
			self.values.loglevel = kw.get('loglevel', 'LOG_ERROR')
			# self.values.logfile_level = kw.get('logfile_level', 'LOG_ERROR')


		# Make sure paths to log files exist
		if not os.path.exists(g.paths.LOGPATH):
			os.makedirs(g.paths.LOGPATH)


		g.LOG_CRITICAL = g.log.debugstates.LOG_CRITICAL
		g.LOG_ERROR = g.log.debugstates.LOG_ERROR
		g.LOG_WARNING = g.log.debugstates.LOG_WARNING
		g.LOG_WEB = g.log.debugstates.LOG_WEB
		g.LOG_INIT = g.log.debugstates.LOG_INIT
		g.LOG_INFO = g.log.debugstates.LOG_INFO
		g.LOG_DEBUG = g.log.debugstates.LOG_DEBUG

		g.log = emen2.db.debug.DebugState(output_level=self.values.loglevel,
											logfile=file(g.paths.LOGPATH + '/log.log', 'a', 0),
											get_state=False,
											quiet = self.values.quiet)

		g.log_critical = functools.partial(g.log.msg, 'LOG_CRITICAL')
		g.log_error = functools.partial(g.log.msg, 'LOG_ERROR')
		g.warn = functools.partial(g.log.msg, 'LOG_WARNING')
		g.log_security = functools.partial(g.log.msg, 'LOG_SECURITY')
		g.log_init = functools.partial(g.log.msg, 'LOG_INIT')
		g.log_info = functools.partial(g.log.msg, 'LOG_INFO')
		g.debug = functools.partial(g.log.msg, 'LOG_DEBUG')
		g.debug_func = g.log.debug_func


		g.log.add_output(['LOG_WEB'], emen2.db.debug.Filter(g.paths.LOGPATH + '/access.log', 'a', 0))
		g.log.add_output(['LOG_SECURITY'], emen2.db.debug.Filter(g.paths.LOGPATH + '/security.log', 'a', 0))
		# g.log_init("Loading config files: %s"%(self.values.configfile or [default_config]))
		# g.log_init('EMEN2DBHOME: %r' % EMEN2DBHOME)
		g.CONFIG_LOADED = True
		g.refresh()



gg = emen2.db.globalns.GlobalNamespace()
g = lambda: gg
