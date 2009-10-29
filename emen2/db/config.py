import sys
EMEN2CONFIG = "config/config.yml"
from emen2.globalns import GlobalNamespace #YAMLLoader, 
g = GlobalNamespace()

#YAMLLoader(EMEN2CONFIG)

g.from_yaml(EMEN2CONFIG)

try:
	from emen2.subsystems import debug
	g.LOG_CRITICAL = debug.DebugState.debugstates.LOG_CRITICAL
	g.LOG_ERR = debug.DebugState.debugstates.LOG_ERROR
	g.LOG_WARNING = debug.DebugState.debugstates.LOG_WARNING
	g.LOG_WEB = debug.DebugState.debugstates.LOG_WEB
	g.LOG_INIT = debug.DebugState.debugstates.LOG_INIT
	g.LOG_INFO = debug.DebugState.debugstates.LOG_INFO
	g.LOG_DEBUG = debug.DebugState.debugstates.LOG_DEBUG

	g.log = debug.DebugState(g.LOG_DEBUG, file(g.LOGROOT + '/log.log', 'a', 0), False, g.LOG_DEBUG)#, True)

	g.log.add_output(['LOG_WEB'], file(g.LOGROOT + '/access.log', 'a', 0))
except ImportError:
	print 'debug not loaded!!!'

g.refresh()
