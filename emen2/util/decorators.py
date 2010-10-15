# $Id$
import itertools
import functools

class callonget(object):
	def __init__(self, cls):
		self.__class = cls
	def __get__(self, instance, owner):
		try:
			result = object.__getattr__(instance, self.__class.__name__)
		except AttributeError:
			result = self.__class
		if instance != None and result is self.__class:
			result = self.__class()
			setattr(instance, self.__class.__name__, result)
		return result
instonget = callonget


class _Null: pass
def cast_arguments(*postypes, **kwtypes):
	def _func(func):
		@functools.wraps(func)
		def _inner(*args, **kwargs):
			out = []
			for typ, arg in itertools.izip_longest(postypes, args, fillvalue=_Null):
				if arg != _Null:
					if typ != _Null and typ != None:
						arg = typ(arg)
					out.append(arg)
			for k,v in kwargs.iteritems():
				typ = kwtypes.get(k, _Null)
				if typ != _Null and typ != None:
					kwargs[k] = typ(kwargs[k])
			return func(*args, **kwargs)
		return _inner
	return _func



def make_decorator(func):
	def _inner1(_func):
		@functools.wraps(_func)
		def _inner(*a, **kw):
			return func(_func(*a, **kw))
		_inner.func = _func
		return _inner
	return _inner1

__version__ = "$Revision$".split(":")[1][:-1].strip()
