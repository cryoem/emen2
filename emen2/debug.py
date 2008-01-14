import time, sys

__all__ = ['LOG_INIT', 'LOG_INFO', 'LOG_DEBUG', 'LOG_ERR', 'DebugState', 'DEBUG', 'log']

LOG_ERR = 7
LOG_INIT = 6
LOG_INFO = 5
LOG_DEBUG = -1
DEBUG = 0
log = file ('log.log', 'a')


class DebugState(object):
  '''Handles logging etc..'''
  _clstate = {}

  def startctxt(self, targ_state):
	  self.push_state(targ_state)
	  return self

  def __enter__(self, *args):
	  pass

  def __exit__(self, *args):
	  self.pop_state()
	  #if args[0]:
	   #   raise
  def __init__(self, value=None, buf=None, oldstdout=None, get_state=True):
	self.__dict__ = self._clstate
	if (not get_state) or (not self._clstate):
		self.__state = value
		self.__buffer = buf
		self.oldstdout = (oldstdout if oldstdout is not None else sys.stdout)
		self.__state_stack = [value]
		self.msg(LOG_INIT, 'init state: %s' % value)

  def write(self, value):
	  value = value.strip()
	  if value is not str():
		  self.msg(LOG_INFO, value)

  def flush(self, *args):
	  self.__buffer.flush()
	  self.oldstdout.flush()
  def get_state(self):
	return self.__state

  def set_state(self, state):
	self('entering: %s--leaving : %s' % (state, self.state))
	self.__state = state
  state = property(get_state, set_state)
  def push_state(self, state):
	  self.__state_stack.append(state)
	  self.state = state

  def pop_state(self):
	  if len(self.__state_stack) > 1:
		  self.__state_stack.pop()
	  self.state = self.__state_stack[-1]
  def get_buffer(self):
	  return self.__buffer
  buffer = property(get_buffer)
  def msg(self, state, *args):
	'''general purpose logging function
	logs to disk all messages whose state is
	greater than -1'''
	if self.__buffer and state > -1:
	  print >>self.__buffer, time.ctime(), '<%03d>:' % state, self.print_list(args), '\n---'
	  self.__buffer.flush()
	if state >= self.__state:
	  print >>self.oldstdout, '<%02d>' % state, self.print_list(args)

  def note_var(self, var):
	'''log the value of a variable and return the variable'''
	self.msg(0, 'NOTED VAR:::', var)
	return var

  def __call__(self, *args):
	'''log with a state of -1'''
	self.msg(-1, *args)

  def print_list(self, lis):
	result = []
	for i in lis: result.append(str(i))
	return str.join(' ', result)

  def debug_func(self, func):
	  def result(*args, **kwargs):
		  self.push_state(-1)
		  return func(*args, **kwargs)
		  self.pop_state()
	  result.__doc__ = func.__doc__
	  result.__name__ = func.__name__
	  return result 