import emen2.globalns
g = emen2.globalns.GlobalNamespace()
import cgi
try:
	from emen2.util.listops import adj_dict
except ImportError: pass
import functools

class prop(property):
    '''apply prop.init to a function that returns a dictionary with keys
    fget, fset, and/or fdel in order to create a property'''
    @classmethod
    def init(cls, func):
        result = cls(**func())
        return result



class BaseDecorator(object):
    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
    def before_hook(self):
        pass
    def after_hook(self):
        pass
    def __call__(self, *args, **kwargs):
        self.before_hook()
        result = self.func(*args, **kwargs)
        self.after_hook()
        return result

class EscapedFun(BaseDecorator):
    def __call__(self, *args, **kwargs):
        return cgi.escape(self.func(*args, **kwargs))

class ReturnWithMimeType(BaseDecorator):
    "DO NOT USE!!! subclass and use a metaclass to declare the mime type to return as"
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs), self.mime_type

class MultiDecorate(BaseDecorator):
    def __init__(self, decs=[]):
        self.decorators = decs[:]
    def __call__(self, func):
        for i in self.decorators:
            func = i(func)
        return func

def get_slice(str, start, end):
    if end > len(str) - 1:
        return str[start:]
    if start < 0:
        start = 0
    return str[start:end]


class return_many_or_single(object):
	def __init__(self, argname=1, transform=lambda x: x[0]):
		self.__triggerarg = argname
		self.__transform = transform

	def __call__(self, func):
		func_argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
		if isinstance(self.__triggerarg, int):
			self.__argpos = self.__triggerarg
			self.__triggerarg = func_argnames[self.__triggerarg]
		else:
			self.__argpos = func_argnames.index(self.__triggerarg)

		@functools.wraps(func)
		def _inner(*args, **kwargs):
			trig = None
			if len(args) >= self.__argpos+1:
				trig = args[self.__argpos]
			if self.__triggerarg in kwargs:
				trig = kwargs[self.__triggerarg]
			lst = hasattr(trig, '__iter__')
			result = func(*args, **kwargs)
			if not lst:
				try:
					tmpresult = self.__transform(result)
				except Exception, e: pass #g.debug('__transform failed:',e)
				else:
					result = tmpresult

			return result
		return _inner

return_list_or_single = return_many_or_single
