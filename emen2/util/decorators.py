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
					if typ != _Null:
						arg = typ(arg)
					out.append(arg)
			for k,v in kwargs.iteritems():
				typ = kwtypes.get(k, _Null)
				if typ != _Null:
					kwargs[k] = typ(kwargs[k])
			g.debug( args, kwargs )
			return func(*args, **kwargs)
		return _inner
	return _func




