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

	logger = None

	def log_init(self, done=False):
		if self.init_done:
			raise ValueError('already initialized')

		self.logger = emen2.db.debug.DebugState()

		# Write out WEB and SECURITY messages to dedicated log files
		self.init_done = done

log_init = Variables.log_init

import twisted.python.log

class EMEN2LogObserver(object):
	LOG_LEVEL = emen2.db.config.get('LOG_LEVEL', None, False)
	LOGPATH = emen2.db.config.get('paths.LOGPATH', None, False)

	log_levels = emen2.util.datastructures.Enum(dict(
			DEBUG=-1,
			TXN=1,
			INIT=2,
			INFO=3,
			INDEX=4,
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

	def process(self, event, *args, **kwargs):
		level = event.get('level')
		if 'level' in event:
			level = event['level']
			if level >= self.log_levels[self.LOG_LEVEL]:
				print self.log_levels.get_name(event['level']), '::', ' '.join(str(k) for k in event['message'])
		elif event['isError']:
			print 'ERROR', '::', ' '.join(str(k) for k in event['message'])
		else:
			pass

twisted.python.log.addObserver(EMEN2LogObserver.emen2_logs)

def msg(level='INFO', msg=''):
	twisted.python.log.msg(msg, level=EMEN2LogObserver.log_levels[level])

def flip(func):
	@functools.wraps(func)
	def _inner(self, *args, **kwargs):
		return func( *args[::-1], **kwargs)
	return _inner
# Argghgh..
msg_forwards = msg
msg_backwards = flip(msg_forwards)
#def msg_backwards(msg='', level='INFO'):
#	return msg_forwards(msg=msg, level=level)

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
