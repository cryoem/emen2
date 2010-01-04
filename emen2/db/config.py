import sys
import functools
import optparse
import emen2.globalns
import emen2.subsystems.debug
import yaml

defaultconfig = "config/config.yml"

g = emen2.globalns.GlobalNamespace()


class DBOptions(optparse.OptionParser):
	def __init__(self, *args, **kwargs):
		#super(DBOptions, self).__init__()
		optparse.OptionParser.__init__(self, *args, **kwargs)

		self.add_option('-c', '--configfile', action='append', dest='configfile')
		self.add_option('-t', '--templatedir', action='append', dest='templatedirs')
		self.add_option('-v', '--viewdirs', action='append', dest='viewdirs')
		self.add_option('-p', '--port', action='store', dest='port')
		self.add_option('-l', '--log_level', action='store', dest='log_level')
		self.add_option('--logfile_level', action='store', dest='logfile_level')
		self.add_option('--logprintonly', action='store_true', dest='log_print_only', default=False)


	def parse_args(self, *args, **kwargs):
		r1, r2 = optparse.OptionParser.parse_args(self,  *args, **kwargs)
		self.load_config()
		return r1, r2


	def load_config(self):

		print "Loading config files: %s"%(self.values.configfile or [defaultconfig])

		map(g.from_yaml, self.values.configfile or [defaultconfig])

		g.TEMPLATEDIRS.extend(self.values.templatedirs or [])
		g.VIEWPATHS.extend(self.values.viewdirs or [])

		if self.values.log_level == None:
			self.values.log_level = 'LOG_DEBUG'
		if self.values.logfile_level == None:
			self.values.logfile_level = 'LOG_DEBUG'
		if self.values.log_print_only == None:
			self.values.log_print_only = False

		try:
			g.LOG_CRITICAL = emen2.subsystems.debug.DebugState.debugstates.LOG_CRITICAL
			g.LOG_ERROR = emen2.subsystems.debug.DebugState.debugstates.LOG_ERROR
			g.LOG_WARNING = emen2.subsystems.debug.DebugState.debugstates.LOG_WARNING
			g.LOG_WEB = emen2.subsystems.debug.DebugState.debugstates.LOG_WEB
			g.LOG_INIT = emen2.subsystems.debug.DebugState.debugstates.LOG_INIT
			g.LOG_INFO = emen2.subsystems.debug.DebugState.debugstates.LOG_INFO
			g.LOG_DEBUG = emen2.subsystems.debug.DebugState.debugstates.LOG_DEBUG

			g.log = emen2.subsystems.debug.DebugState(output_level=self.values.log_level,
												logfile=file(g.LOGROOT + '/log.log', 'a', 0),
												get_state=False,
												logfile_state=self.values.logfile_level)
			g.log_critical = functools.partial(g.log.msg, 'LOG_CRITICAL')
			g.log_error = functools.partial(g.log.msg, 'LOG_ERROR')
			g.warn = functools.partial(g.log.msg, 'LOG_WARNING')
			g.log_init = functools.partial(g.log.msg, 'LOG_INIT')
			g.log_info = functools.partial(g.log.msg, 'LOG_INFO')
			g.debug = functools.partial(g.log.msg, 'LOG_DEBUG')

			g.log.add_output(['LOG_WEB'], emen2.subsystems.debug.Filter(g.LOGROOT + '/access.log', 'a', 0))

		except ImportError:
			raise ImportError, 'Debug not loaded!!!'

		g.refresh()


#loader = DBOptions()
#loader.parse_args()
