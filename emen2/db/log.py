# $Id$
"""EMEN2 logging

Functions:
	msg
	info
	init
	error
	warn
	debug
	security
	index
	commit
"""


import traceback
import functools

import emen2.db.config
import emen2.db.debug
import os.path
logger = None
IGNORE = ['DEBUG', 'INDEX']

inst = lambda x:x()

@inst
class Variables:
	# set this to true when the configuration is fully loaded
	_init_done = False
	@property
	def init_done(self):
		return self._init_done
	@init_done.setter
	def init_done(self, value):
		self._init_done = bool(value)

	LOG_LEVEL = emen2.db.config.get('LOG_LEVEL', None, False)
	LOGPATH = emen2.db.config.get('paths.LOGPATH', None, False)
	logger = None

	def log_init(self, done=False):
		if self.init_done:
			raise ValueError('already initialized')

		self.logger = emen2.db.debug.DebugState(
			output_level=self.LOG_LEVEL,
			logfile=file(os.path.join(self.LOGPATH, 'log.log'), 'a', 0),
			get_state=False,
			quiet = False #self.values.quiet
		)

		# Write out WEB and SECURITY messages to dedicated log files
		self.logger.add_output(['WEB'], emen2.db.debug.Filter(os.path.join(self.LOGPATH, 'access.log'), 'a', 0))
		self.logger.add_output(['SECURITY'], emen2.db.debug.Filter(os.path.join(self.LOGPATH, 'security.log'), 'a', 0))
		self.init_done = done

log_init = Variables.log_init


def msg(level='INFO', msg=''):
	#if level in IGNORE:
	#	return
	if Variables.logger:
		Variables.logger.msg(level, msg)
	else:
		print '%s: %s'%(level, msg)

# Argghgh..
msg_forwards = msg
def msg_backwards(msg='', level='INFO'):
	return msg_forwards(msg=msg, level=level)

def nothing(*args, **kwargs):
	pass

# Aliases
info = functools.partial(msg_backwards, level='INFO')
init = functools.partial(msg_backwards, level='INIT')
error = functools.partial(msg_backwards, level='ERROR')
warn = functools.partial(msg_backwards, level='WARN')
debug = functools.partial(msg_backwards, level='DEBUG')
security = functools.partial(msg_backwards, level='SECURITY')
index = nothing # functools.partial(msg_backwards, level='INDEX')
commit = functools.partial(msg_backwards, level='COMMIT')

def detach():
	Variables.logger.capturestdout()
	Variables.logger.closestdout()

def print_exception():
	traceback.print_exc()
