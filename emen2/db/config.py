import sys
from optparse import OptionParser
EMEN2CONFIG = "/Users/edwlan/Programming/emen2/emen2/config/config.yml"
from emen2.globalns import GlobalNamespace
g = GlobalNamespace()
g.from_yaml(EMEN2CONFIG)

parser = OptionParser()
parser.add_option('-c', '--configfile', action='append', dest='configfile')
parser.add_option('-t', '--templatedir', action='append', dest='templatedirs')
parser.add_option('-v', '--viewdirs', action='append', dest='viewdirs')
parser.add_option('-p', '--port', action='store', dest='port')
parser.add_option('-l', '--log_level', action='store', dest='log_level')
parser.add_option('--log_state', action='store', dest='log_state')

options, args = parser.parse_args()
map(g.from_yaml, options.configfile or [])
g.TEMPLATEDIRS.extend(options.templatedirs or [])
g.VIEWPATHS.extend(options.viewdirs or [])
if options.log_level == None: options.log_level = 'LOG_INFO'
if options.log_state == None: options.log_state = 'LOG_DEBUG'

print options, args
print options.log_level

try:
	from emen2.subsystems import debug
	g.LOG_CRITICAL = debug.DebugState.debugstates.LOG_CRITICAL
	g.LOG_ERR = debug.DebugState.debugstates.LOG_ERROR
	g.LOG_WARNING = debug.DebugState.debugstates.LOG_WARNING
	g.LOG_WEB = debug.DebugState.debugstates.LOG_WEB
	g.LOG_INIT = debug.DebugState.debugstates.LOG_INIT
	g.LOG_INFO = debug.DebugState.debugstates.LOG_INFO
	g.LOG_DEBUG = debug.DebugState.debugstates.LOG_DEBUG

	g.log = debug.DebugState(options.log_level, file(g.LOGROOT + '/log.log', 'a', 0), False, g.LOG_DEBUG or options.log_level)#, True)

	g.log.add_output(['LOG_WEB'], file(g.LOGROOT + '/access.log', 'a', 0))
except ImportError:
	print 'debug not loaded!!!'

g.refresh()
