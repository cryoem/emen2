import cgi
try:
	from emen2.util.listops import adj_dict
except ImportError: pass

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

