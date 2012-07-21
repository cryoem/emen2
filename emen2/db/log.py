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

class EMEN2Logger(object):

	log_levels = dict(
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
	)
	
	def __init__(self):
		# print "EMEN2Logger: __init__"
		self.started = False
		self.logpath = None
		self.log_level = 0
		self.outfile = None
		
	def start(self):
		# print "EMEN2Logger: start"
		self.started = True
		self.logpath = emen2.db.config.get("paths.LOGPATH")
		self.log_level = self.log_levels.get(emen2.db.config.get('LOG_LEVEL', 0))
		self.outfile = open(os.path.join(self.logpath, "test.log"), "w")
		
	def stop(self):
		# print "EMEN2Logger: stop"
		self.outfile.close()
		self.outfile = None
		self.started = False

	def log(self, msg, level='INFO'):
		l = self.log_levels.get(level, 0)
		line = '%s: %s'%(level, msg)
		if l < self.log_level:
			return
		
		if not self.outfile:
			print line
			return
			
		self.outfile.write(line+"\n")
		self.outfile.flush()			

	def emit(self, e):
		return self.log(e)


# Create the logger
logger = EMEN2Logger()

def print_exception():
	traceback.print_exc()

def msg(msg='', level='INFO'):
	logger.log(msg, level)


# Aliases
info = functools.partial(msg, level='INFO')
init = functools.partial(msg, level='INIT')
error = functools.partial(msg, level='ERROR')
warn = functools.partial(msg, level='WARN')
debug = functools.partial(msg, level='DEBUG')
security = functools.partial(msg, level='SECURITY')
index = functools.partial(msg, level='INDEX')
commit = functools.partial(msg, level='COMMIT')
web = functools.partial(msg, level='WEB')
