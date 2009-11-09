import sys
from optparse import OptionParser
EMEN2CONFIG = "config/config.yml"
from emen2.globalns import GlobalNamespace
g = GlobalNamespace()
g.from_yaml(EMEN2CONFIG)

parser = OptionParser()
parser.add_option('-c', '--configfile', action='append', dest='configfile')
parser.add_option('-t', '--templatedir', action='append', dest='templatedirs')
parser.add_option('-v', '--viewdirs', action='append', dest='viewdirs')
parser.add_option('-p', '--port', action='store', dest='port')
parser.add_option('-l', '--log_level', action='store', dest='log_level')
parser.add_option('--logfile_level', action='store', dest='logfile_level')

options, args = parser.parse_args()
map(g.from_yaml, options.configfile or [])
g.TEMPLATEDIRS.extend(options.templatedirs or [])
g.VIEWPATHS.extend(options.viewdirs or [])
if options.log_level == None: options.log_level = 'LOG_INFO'
if options.logfile_level == None: options.logfile_level = 'LOG_DEBUG'

try:
	from emen2.subsystems import debug
	g.LOG_CRITICAL = debug.DebugState.debugstates.LOG_CRITICAL
	g.LOG_ERR = debug.DebugState.debugstates.LOG_ERROR
	g.LOG_WARNING = debug.DebugState.debugstates.LOG_WARNING
	g.LOG_WEB = debug.DebugState.debugstates.LOG_WEB
	g.LOG_INIT = debug.DebugState.debugstates.LOG_INIT
	g.LOG_INFO = debug.DebugState.debugstates.LOG_INFO
	g.LOG_DEBUG = debug.DebugState.debugstates.LOG_DEBUG

	g.log = debug.DebugState(output_level=options.log_level,
										logfile=file(g.LOGROOT + '/log.log', 'a', 0),
										get_state=False,
										logfile_state=options.logfile_level)

	g.log.add_output(['LOG_WEB'], file(g.LOGROOT + '/access.log', 'a', 0))
except ImportError:
	raise ImportError, 'Debug not loaded!!!'

g.refresh()
