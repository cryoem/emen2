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

def return_jpg(name, bases, dict):
    cls = type(name, bases, dict)
    cls.mime_type = 'image/jpg'
    return cls

class ReturnAsJPG(ReturnWithMimeType):
    __metaclass__ = return_jpg

def return_png(name, bases, dict):
    cls = type(name, bases, dict)
    cls.mime_type = 'image/png'
    return cls

class ReturnAsPNG(ReturnWithMimeType):
    __metaclass__ = return_png

def return_html(name, bases, dict):
    cls = type(name, bases, dict)
    cls.mime_type = "text/html"
    return cls

class ReturnAsHTML(ReturnWithMimeType):
    __metaclass__ = return_html

class PreformattedOutp(ReturnAsHTML):
    def __call__(self, *args, **kwargs):
        result = ReturnAsHTML.__call__(self, *args, **kwargs)
        return '<pre>' + result[0].encode('utf-8') + '</pre>', result[1]

class MultiDecorate(BaseDecorator):
    def __init__(self, decs=[]):
        self.decorators = decs[:]
    def __call__(self, func):
        for i in self.decorators:
            func = i(func)
        return func

class ReturnString(BaseDecorator):
    def __call__(self, *args, **kwargs):
        result = BaseDecorator.__call__(self, *args, **kwargs)
        return str(result).encode('utf-8')

def get_slice(str, start, end):
    if end > len(str) - 1:
        return str[start:]
    if start < 0:
        start = 0
    return str[start:end]

def slugify(string):
    result = string.lower().expandtabs().split()
    return str.join('-', result)

def common_keys(dict1, dict2): return set(dict1) & set(dict2)
    
def dict_set(dict, key, val): dict[key] = val
    
def merge_dict(srcdict, targetdict, updfunc=dict_set):
    '''copy values from srcdict to targetdict where they share keys'''
    [updfunc(targetdict, key, srcdict[key]) for key in common_keys(srcdict, targetdict) ]
    

def both(a, b): return ( a and b )
def either(a, b): return ( a or b )
