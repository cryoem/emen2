# $Author$ $Revision$
import os
import sys
import functools
import optparse
import yaml
import demjson
import pkgutil

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import emen2.subsystems.debug



def get_filename(package, resource):
	d = os.path.dirname(sys.modules[package].__file__)
	return os.path.join(d, resource)

default_config = get_filename('emen2', 'config/config.base.yml')


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
		self.add_option('-s', '--setvalue', action='append', dest='configoverride')
		self.add_option('-t', '--templatedir', action='append', dest='templatedirs')
		self.add_option('-v', '--viewdirs', action='append', dest='viewdirs')
		self.add_option('-p', '--port', action='store', dest='port')
		self.add_option('-l', '--log_level', action='store', dest='log_level')
		self.add_option('-q', '--quiet', action='store_true', dest='quiet', default=False)
		self.add_option('--logfile_level', action='store', dest='logfile_level')
		self.add_option('--logprintonly', action='store_true', dest='log_print_only', default=False)


	def parse_args(self, lc=True, *args, **kwargs):
		r1, r2 = optparse.OptionParser.parse_args(self,  *args, **kwargs)
		if lc:
			self.load_config()
		return r1, r2


	def load_config(self, **kw):

		DB_HOME = os.getenv("DB_HOME")
		g.EMEN2DBPATH = DB_HOME

		g.from_yaml(default_config)

		if self.values.home:
			DB_HOME = self.values.home

		if self.values.configfile:
			for fil in self.values.configfile:
				g.from_yaml(fil)

		if DB_HOME:
			try:
				g.from_yaml(os.path.join(DB_HOME, "config.yml"))	
			except:
				print "No config.yml in %s"%DB_HOME


		if DB_HOME:
			g.EMEN2DBPATH = DB_HOME
		elif not g.getattr('EMEN2DBPATH', False):
			raise ValueError, "No DB_HOME / EMEN2DBPATH specified!"


		g.TEMPLATEDIRS.extend(self.values.templatedirs or [])
		if g.getattr('TEMPLATEDIRS_DEFAULT',False):
			g.TEMPLATEDIRS.append(get_filename('emen2','TwistSupport_html/templates'))


		g.VIEWPATHS.extend(self.values.viewdirs or [])

		if self.values.log_level == None:
			self.values.log_level = kw.get('log_level', 'LOG_DEBUG')

		if self.values.logfile_level == None:
			self.values.logfile_level = kw.get('logfile_level', 'LOG_DEBUG')

		if self.values.log_print_only == None:
			self.values.log_print_only = kw.get('log_print_only', False)

		if self.values.quiet == True:
			self.values.log_level = kw.get('log_level', 'LOG_ERROR')
			self.values.logfile_level = kw.get('logfile_level', 'LOG_ERROR')


		if not os.path.exists(g.LOGPATH):
			os.makedirs(g.LOGPATH)

		if self.values.configoverride:
			for val in self.values.configoverride:
				key, value = val.split('=')
				g.setattr(key, demjson.decode(value))


		try:
			g.LOG_CRITICAL = g.log.debugstates.LOG_CRITICAL
			g.LOG_ERROR = g.log.debugstates.LOG_ERROR
			g.LOG_WARNING = g.log.debugstates.LOG_WARNING
			g.LOG_WEB = g.log.debugstates.LOG_WEB
			g.LOG_INIT = g.log.debugstates.LOG_INIT
			g.LOG_INFO = g.log.debugstates.LOG_INFO
			g.LOG_DEBUG = g.log.debugstates.LOG_DEBUG

			g.log = emen2.subsystems.debug.DebugState(output_level=self.values.log_level,
												logfile=file(g.LOGPATH + '/log.log', 'a', 0),
												get_state=False,
												logfile_state=self.values.logfile_level,
												just_print=self.values.log_print_only,
												quiet = self.values.quiet)

			g.log_critical = functools.partial(g.log.msg, 'LOG_CRITICAL')
			g.log_error = functools.partial(g.log.msg, 'LOG_ERROR')
			g.warn = functools.partial(g.log.msg, 'LOG_WARNING')
			g.log_init = functools.partial(g.log.msg, 'LOG_INIT')
			g.log_info = functools.partial(g.log.msg, 'LOG_INFO')
			g.debug = functools.partial(g.log.msg, 'LOG_DEBUG')
			g.debug_func = g.log.debug_func

			g.log.add_output(['LOG_WEB'], emen2.subsystems.debug.Filter(g.LOGPATH + '/access.log', 'a', 0))

			g.log_init("Loading config files: %s"%(self.values.configfile or [default_config]))

		except ImportError:
			raise ImportError, 'Debug not loaded!!!'


		g.CONFIG_LOADED = True
			
		g.refresh()


		print dict(g)


__version__ = "$Revision$".split(":")[1][:-1].strip()
