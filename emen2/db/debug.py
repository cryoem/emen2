# $Id$

'''
classes:
	Output: represents an individual output stream which logs certain specified states
		- Headless: skips the header information and just logs the message
		- Min: represents one which logs everything greater than a specified state
		- stderr: logs to sys.stderr
		- Bounded: represents one which loges everything between two specified states
			- stdout: logs to sys.stdout

	DebugState (NOTE: this probably should be renamed): contains a bunch of logging and
					debugging utilities.

	debugDict: used by DebugState.instrument_class to log all attribute access of a class

	Filter: subclass of file, used to be use to strip headers off of access.log, unused
'''
from __future__ import with_statement

import functools
import code
import inspect
import os.path
import time
import datetime
import sys


import emen2.util.datastructures


__all__ = ['DebugState', 'Output', 'Bounded', 'Headless', 'Min']


def take(num, iter_):
	for _ in range(num): yield iter_.next()


################
# class Output #
################

class Output(object):
	'''Controls access to a paricular output stream

	Subclasses that will be used should be registered with register and created with factory
	'''

	subclasses = {}
	@classmethod
	def register_subclass(cls, subcls):
		'''A decorator for registering a subclass, uses subcls.__name__.lower() as a key in a lookup table

		:param class subcls: the class to be registered
		:returns: the class passed in as subclass'''

		if issubclass(subcls, cls):
			cls.subclasses[subcls.__name__.lower()] = subcls
		return subcls

	@classmethod
	def factory(cls, version=None, **kwargs):
		'''Create an particular kind of instance of Output

		:param str version: the lookup key for the subclass
		:param kwargs: the arguments for the constructor of the desired class
		'''

		cls = cls.subclasses.get(version.lower(), cls)
		return cls(**kwargs)


	def __init__(self, states=0, filename=None, file=None, modulename=None, **kwargs):
		'''Constructor: don't override this method, override _init'''
		self._states = states
		self._file = file or open(filename, 'a')
		self._state_checked = False
		self._modulename = modulename
		self._init(**kwargs)

	def _not_if_closed(func):
		'''decorator: turns methods on or off based on whether the underlying stream is closed'''
		@functools.wraps(func)
		def _inner(self, *args, **kwargs):
			result = None
			if not self.closed:
				result = func(self, *args, **kwargs)
			return result
		return _inner

	@_not_if_closed
	def send(self, module, state, header, msg):
		header, msg = self._preprocess(state, header, msg)

		if self._modulename is not None and self._modulename != module:
			pass

		elif self._state_checked or self.checkstate(state):
			self._file.write(header)
			self._file.write(msg.rstrip())
			self._file.write('\n')
			self.flush()
			self._state_checked = False

	@_not_if_closed
	def flush(self):
		'''flush()

		Flush the buffer'''
		if not self._file.closed:
			self._file.flush()

	@_not_if_closed
	def close(self):
		'''close()

		Close the buffer'''
		if not self._file.closed:
			self._file.close()

	# subclass behavior modification hooks
	@property
	def closed(self):
		'''Indicates whether the underlying stream is open or closed'''
		return self._file.closed

	def checkstate(self, state):
		'''Determine whether current message should be logged

		:param state: The current state of the Logger

		This method should set self._state_checked to True if the message is to be logged'''
		result = False
		if self._states is None: result = False
		elif self._states == DebugState.debugstates.ALL: result = True
		elif isinstance(self._states, (str, unicode)): result = False
		else: result = state in self._states
		self._state_checked = result
		return result

	def disable(self):
		"""called to disable the stream"""
		self._states = None

	def _init(self, **kwargs):
		'''Initialize the instance, override this instead of __init__'''
		pass

	def _preprocess(self, state, header, msg):
		'''Called before the message is logged, allows for the displayed message to be changed as one likes


		:param state: the current logging state
		:param str header: the header of the current message
		:param str msg: the text of the current message
		:returns: a tuple (header, msg) containing the desired values of each'''
		return header, msg

@Output.register_subclass
class Min(Output):
	'''prints any messages in a state higher than the one given'''
	def checkstate(self, state):
		if self._states is None: result = False
		else:
			result = self._states == DebugState.debugstates.ALL or state >= self._states
			self._state_checked = result
		return result


class Bounded(Output):
	'''prints any messages in a given range of states'''
	def _init(self, max, **kwargs):
		self._max = max
	def checkstate(self, state):
		if self._states is None: result = False
		else:
			result = self._states == DebugState.debugstates.ALL or (state >= self._states and state < self._max)
			self._state_checked = result
		return result

@Output.register_subclass
class Headless(Output):
	'''drops the header from messages'''
	def _preprocess(self, state, header, msg):
		return '', msg

def stdouts_handler(prefix,suffix):
	def _preprocess(self, state, header, msg):
		return '%s%s'%(prefix, header), '%s%s\n' % (msg.rstrip(),suffix)
		# header = header.split(' : ')
		# head = [header[0]]
		# head.append(header[1]+'\t\t')
		# head.extend(header[2:])
		# header = ' : '.join(head)
		# return state, ' '.join([prefix, header]), msg
	return _preprocess

@Output.register_subclass
class stdout(Bounded):
	_preprocess = stdouts_handler('  ','')

@Output.register_subclass
class stderr(Min):
	_preprocess = stdouts_handler('!!', '') # not sure why you need pre and postpend


class DebugState(object):
	'''Handles logging etc..'''
	debugstates = emen2.util.datastructures.Enum(dict(
		DEBUG=-1,
		TXN=1,
		INIT=2,
		INFO=3,
		INDEX=4,
		COMMIT=5,
		WEB=6,
		WARNING=8,
		SECURITY=9,
		ERROR=10,
		CRITICAL=11,
		ALL=0
		))
	last_debugged = emen2.util.datastructures.Ring()
	_clstate = {}

	@property
	def _state(self):
		return self._stdout._states
	@_state.setter
	def _state(self, value):
		self._stdout._states = value

	@property
	def _log_state(self):
		return self._output._states
	@_state.setter
	def _log_state(self, value):
		self._output._states = value


	def __init__(self, output_level='INFO', logfile=None, get_state=True, logfile_state=None, just_print=False, quiet=False):
		self._maxlength = max(map(len, self.debugstates))
		self.__dict__ = self._clstate
		if (not get_state) or (not self._clstate):
			self._timers = {}
			self.just_print = just_print
			self.quiet = quiet
			self._stdout = Output.factory('stdout', file=sys.stdout, max=self.debugstates.WARNING)
			self._stderr = Output.factory('stderr', file=sys.stderr, states=self.debugstates.WARNING)
			self._state = self.debugstates[output_level]
			self._state_stack = [self._state]
			if logfile is not None:
				self._output = Output.factory('min', file=logfile)
			else:
				self._output = self._stdout
			self._log_state = self.debugstates[logfile_state or self._state]
			self._outputs = [self._stdout, self._stderr, self._output]
			self._print_to_stdout = True
			self.stdout = sys.stdout
			self.stderr = sys.stderr


	def write(self, *args, **kwargs):
		args = [x.rstrip() for x in args if x.rstrip()]
		if args:
			self.msg('INFO', 'captured', *(x for x in args), join=': ')


	def capturestdout(self):
		self.msg('CRITICAL', 'Capturing stdoutput')
		self._print_to_stdout = False
		sys.stdout = self
		sys.stderr = self

	def restorestdout(self):
		self._print_to_stdout = True
		sys.stdout = self.stdout
		sys.stderr = self.stderr

	def swapstdout(self):
		self.msg('CRITICAL', 'Switching Outputs...')
		self._print_to_stdout = not self._print_to_stdout
		sys.stderr, self.stderr = self.stderr, sys.stderr
		sys.stdout, self.stdout = self.stdout, sys.stdout
		self.msg('INFO', '...Done')

	def closestdout(self):
		self.msg('CRITICAL', 'Closing old stdout/stderr')
		self._stdout.close()
		self._stderr.close()
		sys.stdin.close()
		print 'closing stdout'

	def __call__(self, *args, **k):
		'''log with a state of -1'''
		self.msg(-1, *args, **k)

	def start_timer(self, key=''):
		self.msg('DEBUG', 'timer %s started' % key)
		self._timers[key] = time.time()

	def stop_timer(self, key=''):
		stime = time.time()
		stime = (stime-self._timers.get(key, 0)) * 1000
		self.msg('DEBUG', 'timer %s stopped: %s milliseconds' % (key, stime))
		return stime

	def note_var(self, var):
		'''log the value of a variable and return the variable'''
		self.msg('INFO', 'NOTED VAR:::', var)
		return var

	def get_state_name(self, state):
		sn = self.debugstates.get_name(state)
		return lambda: sn



	# ian: simplified..
	# ed: not thanks....
	# def newmsg(self, msg='', level='INFO', tb=False, e=None):
	#	level = level.upper()
	#	state = self.debugstates[level]
	#	if tb:
	#		self.print_traceback()

	#	# outputs for the sake of lazy binding, outputs_l for caching
	#	outputs_l = []
	#	outputs = ((outputs_l.append(output), True)[1] for output in self._outputs if output.checkstate(state))

	#	if state < self._log_state and state < self._state:
	#		return
	#	elif not any(outputs):
	#		return

	#	# return func(state, sn, output, outputs_l, outputs, *args, **k)
	#	head = '%s:%s: '%(time.strftime('[%Y-%m-%d %H:%M:%S]'), level.ljust(8))
	#	for buf in outputs_l:
	#		buf.send(None, state, head, '%s\n'%(unicode(msg).encode('utf-8')))
	#		buf.flush()



	def msg(self, sn, *args, **k):
		state = self.debugstates[sn]
		tb = k.pop('tb', False)
		if tb: self.print_traceback()

		# outputs for the sake of lazy binding, outputs_l for caching
		outputs_l = []
		outputs = ( (outputs_l.append(output), True)[1] for output in self._outputs if output.checkstate(state) )

		if state < self._log_state and state < self._state: return
		# NOTE: ed 1/4/2009:: the big slowdown is not having a quick way to locate which output to
		# 								print to, we could fix this with a bloom filter--but it is not super
		# 								important for now	we just make sure we avoid checking twice
		elif not any(outputs): return # make sure at least one output is open for writing

		join_char = k.get('join', u' ')
		output = self.print_list(args, join=join_char)
		sn = self.get_state_name(state)()

		# choose code path
		func = self._old_msg
		if self.just_print:
			func = self._just_print_msg

		# pass outputs and outputs_l because outputs might need to be iterated through in order
		# to populate outputs_l completely
		return func(state, sn, output, outputs_l, outputs, *args, **k)

		return result

	newmsg = msg

	#def _just_print_msg(self, state, sn, output, *args, **k):
	def _just_print_msg(self, state, sn, output, outputs, output_gen, *args, **k):
		# finish the generator to make sure we get all the values in outputs there should be
		for x in output_gen: pass
		head = '%s %s '%(datetime.datetime.now(), sn)

		for buf in outputs:
			buf.send(None, state, '', '%s%s' % (output.encode('utf-8'), '\n') )
			buf.flush()


	def _old_msg(self, state, sn, output, outputs, output_gen, *args, **k):
		# finish the generator to make sure we get all the values in outputs there should be
		for x in output_gen: pass

		module = self._get_last_module()
		headerfields = [time.strftime('[%Y-%m-%d %H:%M:%S]'), sn]

		if self._state == -1: headerfields.append('%s:%s'%(module[0],module[1]))

		head = '%s %s' % (':'.join(str(x) for x in headerfields), ' :: ')

		for buf in outputs:
			buf.send(module[0], state, head, '%s\n'%(output.encode('utf-8')) )
			buf.flush()


	def loud_notify(self, *msgs):
		'Notifies and forces attention'
		self.msg('CRITICAL', *msgs)
		raw_input('hit enter to continue...')

	def interact(self, locals, *args):
		'''\
		start a interactive console in a given scope
		'''
		interp = code.InteractiveConsole(locals)
		interp.interact('Debugging')

	def __enter__(self):
		self.push_state(self.debugstates['DEBUG'])
		self.msg('DEBUG', 'entering debugging context')

	def __exit__(self, exc_type, exc_value, tb):
		self.msg('DEBUG', 'leaving debugging context')
		self.pop_state()


	def debug_func(self, func):
		'''\
		decorator to print info about a function whenever it is called
		'''
		@functools.wraps(func)
		def _inner(*args, **kwargs):
			self.msg('DEBUG', 'debugging state -> self._state: %r, self._log_state: %r' % (self._state, self._log_state) )
			self.msg('DEBUG', 'debugging callable: %s, args: %s, kwargs: %s'  % (func, args, kwargs))
			result = None
			try:
				result = func(*args, **kwargs)
			except BaseException, e:
				self.msg('DEBUG', 'the callable %(func)r failed with: (%(exc)r) - %(exc)s' % dict(func=func, exc=e))
				raise
			else:
				self.msg('DEBUG', 'the callable %r returned: %r\n---' % (func, result))
			finally:
				self.pop_state()
				self.last_debugged = (func, args, kwargs)
			return result
		_inner.func = func
		return (_inner if self.debugstates.DEBUG  in (self._state, self._log_state) else func)

	def instrument_class(self, name, bases, dict):
		for nm,meth in [ (nm,meth) for nm,meth in dict.items() if hasattr(meth, '__call__')]:
			self.msg(self.debugstates.INFO, 'Instrumenting class (%s) method (%s)' % (name, nm))
			dict[nm] = self.debug_func(meth)
		clss = type(name, bases, dict)
		return clss

	def print_traceback(self, level='DEBUG', steps=3):
		msg =  self._get_last_module(steps)
		self.msg(level, msg, tb=False)
		return msg

	def _get_last_module(self, num=1):
		modname = '%s.py' % __name__.split('.')[-1]
		try:
			result = take(num, (
				x for x in (
					(name[1].split(os.path.sep)[-1], name[0].f_lineno) for name in inspect.getouterframes(inspect.currentframe())
				) if not x[0]=='debug.py')
			)
		except:
			result = [('Unknown Output',-1)]
		result = [ [str(y) for y in x] for x in result]
		if num == 1:
			result = result[0]
		return result

	def indent(self, string):
		buf = string.split('\n')
		out = [buf.pop(0)]
		for line in buf:
			out.append('\t\t%s' % line)
		return '\n'.join(out)

	def print_list(self, lis, join=' '):
		#deal with Python's unicode brokenness :-{
		def get_right(mess):
			if type(mess) == unicode: pass
			elif type(mess) == str:
				mess = mess.decode('utf-8', 'replace')
			else:
				mess = get_right(str(mess))
			return mess
		return join.join(self.indent(get_right(i)) for i in lis)

	#state changing methods
	def get_state(self): return self._state
	def set_state(self, state):
		newstate = self.debugstates[state]
		self._state = newstate
	state = property(get_state, set_state)


	#manipulate the state stack
	def push_state(self, state):
		self._state_stack.append(self.debugstates[state])
		if self.quiet:
			self._log_state = state
		else:
			self.state = state

	def pop_state(self):
		if len(self._state_stack) > 1:
			self._state_stack.pop()
			self.state = self._state_stack[-1]

	#output buffer
	def get_buffer(self): return self._buffer
	buffer = property(get_buffer)

	def add_output(self, states, file, version='', current_file=False, **kwargs):
		if hasattr(states, '__iter__'):
			states = [self.debugstates[x] for x in states]
		else:
			states = self.debugstates[states]
		if current_file:
			kwargs['modulename'] = self._get_last_module()[0]
		output = Output.factory(version, states=states, file=file, **kwargs)
		self._outputs.append(output)
		return len(self._outputs)


class debugDict(dict):
	def __getitem__(self, name):
		result = dict.get(self, name)
		print name, result
		if not self.has_key(name):
			dict.__getitem__(self, name)
		return result
	def get(self, name, default=None):
		result = dict.get(self, name, default)
		print name, result
		return result


class Filter(file):
	def __init__(self, *args, **kwargs):
		self._splitter = kwargs.pop('sep', '::')
		self._num = kwargs.pop('items', 1)
		file.__init__(self, *args, **kwargs)

	def write(self, str_):
		str_ = str_.split(self._splitter, self._num)[-1]
		file.write(self, str_)


#def _get_last_module(debugstate):
#	try:
#		result = filter(lambda x:not x[0]=='debug.py',
#				( (name[1].split(os.path.sep)[-1], name[0].f_lineno)
#						for name in inspect.getouterframes(inspect.currentframe())
#				))[0]
#	except:
#		result = ('Unknown Output',-1)
#	return ':'.join(str(x) for x in result)


__version__ = "$Revision$".split(":")[1][:-1].strip()
