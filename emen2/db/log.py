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

logger = None
IGNORE = ['DEBUG', 'INDEX']

def msg(level='INFO', msg=''):
	if level in IGNORE:
		return
	# if logger:
	# 	return logger.msg(msg)
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

def print_exception():
	traceback.print_exc()
