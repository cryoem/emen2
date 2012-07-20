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

import twisted.python.log

import emen2.db.config
import emen2.db.debug
import os.path
logger = None
IGNORE = ['DEBUG', 'INDEX']


inst = lambda x:x()

class EMEN2Logger(object):
	LOG_LEVEL = emen2.db.config.get('LOG_LEVEL', None, False)
	LOGPATH = emen2.db.config.get('paths.LOGPATH', None, False)

	log_levels = emen2.util.datastructures.Enum(dict(
			DEBUG=-1,
			TXN=1,
			INIT=2,
			INDEX=3,
			INFO=4,
			COMMIT=5,
			WEB=6,
			WARN=8,
			SECURITY=9,
			ERROR=10,
			CRITICAL=11,
			ALL=0
	))


	@classmethod
	def emen2_logs(cls, event): # *args, **kwargs):
		self = cls()
		self.process(event)

	def log(self, level, *args, **kwargs):
		level = self.log_levels[level]
		if level >= self.log_levels[self.LOG_LEVEL]:
			message = '%s: %s' % (self.log_levels.get_name(level), ' '.join(args))
			twisted.python.log.msg(message, system=self.log_levels.get_name(level))
			# print message
		else:
			pass


@inst
class Variables:
	'''Namespace for module-level variables'''

	logger = EMEN2Logger()
	debug_state = emen2.db.debug.DebugState()



import twisted.python.log

def msg(level='INFO', msg=''):
	#print msg
	Variables.logger.log(level, msg)

def flip(func):
	@functools.wraps(func)
	def _inner(self, *args, **kwargs):
		return func( *args[::-1], **kwargs)
	return _inner

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

#def detach():
#	Variables.logger.capturestdout()
#	Variables.logger.closestdout()

def print_exception():
	traceback.print_exc()
