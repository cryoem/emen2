import emen2.globalns
g = emen2.globalns.GlobalNamespace()
import cgi
try:
	from emen2.util.listops import adj_dict
except ImportError: pass
import functools
import itertools

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
			# find value of controlling argument
			trig = None
			arg,kwarg = False,False
			if len(args) >= self.__argpos+1:
				trig = args[self.__argpos]
				arg = True
			elif self.__triggerarg in kwargs:
				trig = kwargs[self.__triggerarg]
				arg = False
				kwarg = True
			lst = not all(hasattr({}, x) for x in ['__iter__', 'keys'])

			# convert argument to a list
			if not lst:
				if arg:
					args = tuple(itertools.chain(args[:self.__argpos], [[trig]], args[self.__argpos+1:]))
				elif kwarg:
					kwargs[self.__triggerarg] = [trig]

			# get result of function
			result = func(*args, **kwargs)

			# get result
			if not lst:
				try:
					tmpresult = self.__transform(result)
				except Exception, e: pass #g.debug('__transform failed:',e)
				else:
					result = tmpresult

			return result
		return _inner
