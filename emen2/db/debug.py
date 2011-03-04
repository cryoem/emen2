# $Id$
from __future__ import with_statement

import functools
import code
import inspect
import os.path
import time
import datetime
import sys

import emen2.util.datastructures

__all__ = ['DebugState']


'''
classes:
	Output: represents an individual output stream which logs certain specified states
		| - Headless: skips the header information and just logs the message
		| - Min: represents one which logs everything greater than a specified state
		| | - stderr: logs to sys.stderr
		| - Bounded: represents one which loges everything between two specified states
		| | - stdout: logs to sys.stdout

	DebugState (NOTE: this probably should be renamed): contains a bunch of logging and
					debugging utilities.

	debugDict: used by DebugState.instrument_class to log all attribute access of a class

	Filter: subclass of file, used to be use to strip headers off of access.log, unused
'''



def take(num, iter_):
	for _ in range(num): yield iter_.next()


################
# class Output #
################

class Output(object):
	'''Controls access to a paricular output stream
	- New subclasses should be registered with register_subclass and created with factory
	- public interface:
		check_state, disable, _init, _preprocess
		- check_state: should check to see if output should happen and set self._state_checked appropriately
		- disable: should cause the stream to be disabled
		- _init: should do stream initialization
		- _preprocess: receives data before it is outputed and can mangle it as it wants to
		- closed: a property which indicates whether the underlying stream is open or closed
	'''

	subclasses = {}
	@classmethod
	def register_subclass(cls, incls):
		if issubclass(incls, cls):
			cls.subclasses[incls.__name__.lower()] = incls
		return incls
	@classmethod
	def factory(cls, version=None, **kwargs):
		if version == None: version = ''
		cls = cls.subclasses.get(version.lower(), cls)
		return cls(**kwargs)


	def __init__(self, states=0, filename=None, file=None, modulename=None, **kwargs):
		'''Constructor: don't override this method, override _init'''
		self._states = states
		self.__file = file or open(filename, 'a')
		self._state_checked = False
		self.__modulename = modulename
		self._init(**kwargs)

	def __not_if_closed(func):
		'''decorator: turns methods on or off based on whether the underlying stream is closed'''
		@functools.wraps(func)
		def _inner(self, *args, **kwargs):
			result = None
			if not self.closed:
				result = func(self, *args, **kwargs)
			return result
		return _inner

	@__not_if_closed
	def send(self, module, state, header, msg):
		state, header, msg = self._preprocess(state, header, msg)

		if self.__modulename is not None and self.__modulename != module:
			pass

		elif self._state_checked or self.checkstate(state):
			self.__file.write(header)
			self.__file.write(msg.rstrip())
			self.__file.write('\n')
			self.flush()
			self._state_checked = False

	@__not_if_closed
	def flush(self):
		if not self.__file.closed:
			self.__file.flush()

	@__not_if_closed
	def close(self):
		if not self.__file.closed:
			self.__file.close()

	# subclass behavior modification hooks
	@property
	def closed(self):
		return self.__file.closed

	def checkstate(self, state):
		result = False
		if self._states is None: result = False
		elif self._states == DebugState.debugstates.ALL: result = True
		elif isinstance(self._states, (str, unicode)): result = False
		else: result = state in self._states
		self._state_checked = result
		return result

	def disable(self):
		self._states = None

	def _init(self, **kwargs): pass
	def _preprocess(self, state, header, msg): return state, header, msg

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
	def _init(self, max):
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
		return state, '', msg

def stdouts_handler(prefix,suffix):
	def _preprocess(self, state, header, msg):
		return state, '%s%s'%(prefix, header), '%s%s\n' % (msg.rstrip(),suffix)
		# header = header.split(' : ')
		# head = [header[0]]
		# head.append(header[1]+'\t\t')
		# head.extend(header[2:])
		# header = ' : '.join(head)
		# return state, ' '.join([prefix, header]), msg
	return _preprocess

@Output.register_subclass
class stdout(Bounded):
	_preprocess = stdouts_handler('   ','')

@Output.register_subclass
class stderr(Min):
	_preprocess = stdouts_handler('!! ', '') # not sure why you need pre and postpend
	#_preprocess = stdouts_handler('!! ', ' *******')


class DebugState(object):
	'''Handles logging etc..'''
	debugstates = emen2.util.datastructures.Enum(dict(LOG_DEBUG=-1, LOG_INFO=3, LOG_TXN=2,
											LOG_COMMIT=5, LOG_INDEX=12,
											LOG_INIT=4, LOG_WEB=6,
											LOG_WARNING=8, LOG_SECURITY=9,
											LOG_ERROR=10, LOG_CRITICAL=11,
											ALL=0))
	last_debugged = emen2.util.datastructures.Ring()
	_clstate = {}

	@property
	def __state(self):
		return self.__stdout._states
	@__state.setter
	def __state(self, value):
		self.__stdout._states = value

	@property
	def __log_state(self):
		return self.__output._states
	@__state.setter
	def __log_state(self, value):
		self.__output._states = value


	def __init__(self, output_level='LOG_INIT', logfile=None, get_state=True, logfile_state=None, just_print=False, quiet=False):
		self.__maxlength = max(map(len, self.debugstates))
		self.__dict__ = self._clstate
		if (not get_state) or (not self._clstate):
			self.__timers = {}
			self.just_print = just_print
			self.quiet = quiet
			self.__stdout = Output.factory('stdout', file=sys.stdout, max=self.debugstates.LOG_WARNING)
			self.__stderr = Output.factory('stderr', file=sys.stderr, states=self.debugstates.LOG_WARNING)
			self.__state = self.debugstates[output_level]
			self.__state_stack = [self.__state]
			if logfile is not None:
				self.__output = Output.factory('min', file=logfile)
			else:
				self.__output = self.__stdout
			self.__log_state = self.debugstates[logfile_state or self.__state]
			self.__outputs = [self.__stdout, self.__stderr, self.__output]
			self.__print_to_stdout = True
			self.stdout = sys.stdout
			self.stderr = sys.stderr


	def write(self, *args, **kwargs):
		args = [x.rstrip() for x in args if x.rstrip()]
		if args:
			self.msg('LOG_INFO', 'captured', *(x for x in args), join=': ')


	def capturestdout(self):
		self.msg('LOG_CRITICAL', 'Capturing stdoutput')
		self.__print_to_stdout = False
		sys.stdout = self
		sys.stderr = self

	def restorestdout(self):
		self.__print_to_stdout = True
		sys.stdout = self.stdout
		sys.stderr = self.stderr

	def swapstdout(self):
		self.msg('LOG_CRITICAL', 'Switching Outputs...')
		self.__print_to_stdout = not self.__print_to_stdout
		sys.stderr, self.stderr = self.stderr, sys.stderr
		sys.stdout, self.stdout = self.stdout, sys.stdout
		self.msg('LOG_INFO', '...Done')

	def closestdout(self):
		self.msg('LOG_CRITICAL', 'Closing old stdout/stderr')
		self.__stdout.close()
		self.__stderr.close()
		sys.stdin.close()

	def __call__(self, *args, **k):
		'''log with a state of -1'''
		self.msg(-1, *args, **k)

	def start_timer(self, key=''):
		self.msg('LOG_DEBUG', 'timer %s started' % key)
		self.__timers[key] = time.time()

	def stop_timer(self, key=''):
		stime = time.time()
		stime = (stime-self.__timers.get(key, 0)) * 1000
		self.msg('LOG_DEBUG', 'timer %s stopped: %s milliseconds' % (key, stime))
		return stime

	def note_var(self, var):
		'''log the value of a variable and return the variable'''
		self.msg('LOG_INFO', 'NOTED VAR:::', var)
		return var

	def get_state_name(self, state):
		sn = self.debugstates.get_name(state)
		return lambda: sn

	def msg(self, sn, *args, **k):
		state = self.debugstates[sn]
		tb = k.pop('m', False)
		if tb: self.print_traceback()

		# outputs for the sake of lazy binding, outputs_l for caching
		outputs_l = []
		outputs = ( (outputs_l.append(output), True)[1] for output in self.__outputs if output.checkstate(state) )

		if state < self.__log_state and state < self.__state: return
		# NOTE: ed 1/4/2009:: the big slowdown is not having a quick way to locate which output to
		# 								print to, we could fix this with a bloom filter--but it is not super
		# 								important for now	we just make sure we avoid checking twice
		elif not any(outputs): return # make sure at least one output is open for writing

		join_char = k.get('join', u' ')
		output = self.print_list(args, join=join_char)
		sn = self.get_state_name(state)()

		# choose code path
		func = self.__old_msg
		if self.just_print: func = self.__just_print_msg

		# pass outputs and outputs_l because outputs might need to be iterated through in order
		# to populate outputs_l completely
		return func(state, sn, output, outputs_l, outputs, *args, **k)

		return result

	#def __just_print_msg(self, state, sn, output, *args, **k):
	def __just_print_msg(self, state, sn, output, outputs, output_gen, *args, **k):
		# finish the generator to make sure we get all the values in outputs there should be
		for x in output_gen: pass
		head = '%s %s '%(datetime.datetime.now(), sn)

		for buf in outputs:
			buf.send(None, state, '', '%s%s' % (output.encode('utf-8'), '\n') )
			buf.flush()


	def __old_msg(self, state, sn, output, outputs, output_gen, *args, **k):
		# finish the generator to make sure we get all the values in outputs there should be
		for x in output_gen: pass

		module = self.__get_last_module()
		module[0] = module[0]
		module = '%s:%s'%(module[0],module[1])

		head = '%s %s' % (':'.join(str(x) for x in (time.strftime('[%Y-%m-%d %H:%M:%S]'), sn, module)), ' :: ')

		for buf in outputs:
			buf.send(module[0], state, head, '%s\n'%(output.encode('utf-8')) )
			buf.flush()


	def loud_notify(self, *msgs):
		'Notifies and forces attention'
		self.msg('LOG_CRITICAL', *msgs)
		raw_input('hit enter to continue...')

	def interact(self, locals, *args):
		'''\
		start a interactive console in a given scope
		'''
		interp = code.InteractiveConsole(locals)
		interp.interact('Debugging')

	def __enter__(self):
		self.push_state(self.debugstates['LOG_DEBUG'])
		self.msg('LOG_DEBUG', 'entering debugging context')

	def __exit__(self, exc_type, exc_value, tb):
		self.msg('LOG_DEBUG', 'leaving debugging context')
		self.pop_state()


	def debug_func(self, func):
		'''\
		decorator to print info about a function whenever it is called
		'''
		@functools.wraps(func)
		def _inner(*args, **kwargs):
			self.msg('LOG_INFO', 'debugging state -> %r, %r' % (self.__state, self.__log_state) )
			self.msg('LOG_DEBUG', 'debugging callable: %s, args: %s, kwargs: %s'  % (func, args, kwargs))
			result = None
			try:
				result = func(*args, **kwargs)
			except BaseException, e:
				self.msg('LOG_DEBUG', 'the callable %(func)r failed with: (%(exc)r) - %(exc)s' % dict(func=func, exc=e))
				raise
			else:
				self.msg('LOG_DEBUG', 'the callable %r returned: %r\n---' % (func, result))
			finally:
				self.pop_state()
				self.last_debugged = (func, args, kwargs)
			return result
		_inner.func = func
		return _inner

	def instrument_class(self, name, bases, dict):
		for nm,meth in [ (nm,meth) for nm,meth in dict.items() if hasattr(meth, '__call__')]:
			self.msg(self.debugstates.LOG_INFO, 'Instrumenting class (%s) method (%s)' % (name, nm))
			dict[nm] = self.debug_func(meth)
		clss = type(name, bases, dict)
		return clss

	def print_traceback(self, level='LOG_DEBUG', steps=3):
		msg =  self.__get_last_module(steps)
		self.msg(level, msg, tb=False)

	def __get_last_module(self, num=1):
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
	def get_state(self): return self.__state
	def set_state(self, state):
		newstate = self.debugstates[state]
		self.__state = newstate
	state = property(get_state, set_state)


	#manipulate the state stack
	def push_state(self, state):
		self.__state_stack.append(self.debugstates[state])
		if self.quiet:
			self.__log_state = state
		else:
			self.state = state

	def pop_state(self):
		if len(self.__state_stack) > 1:
			self.__state_stack.pop()
			self.state = self.__state_stack[-1]

	#output buffer
	def get_buffer(self): return self.__buffer
	buffer = property(get_buffer)

	def add_output(self, states, file, version='', current_file=False, **kwargs):
		if hasattr(states, '__iter__'):
			states = [self.debugstates[x] for x in states]
		else:
			states = self.debugstates[states]
		if current_file:
			kwargs['modulename'] = self.__get_last_module()[0]
		output = Output.factory(version, states=states, file=file, **kwargs)
		self.__outputs.append(output)
		return len(self.__outputs)


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
		self.__splitter = kwargs.pop('sep', '::')
		self.__num = kwargs.pop('items', 1)
		file.__init__(self, *args, **kwargs)

	def write(self, str_):
		str_ = str_.split(self.__splitter, self.__num)[-1]
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
