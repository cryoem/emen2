# This includes 'globals' for the package

# This should point to where emen2 is installed (should also be in the python path)

#NOTE: importing this like: 'from emen2.emen2config import *' or 'from g import *' is deprecated, use 'import g'
#If these instructions are followed setting g.<symbol> will update/create that symbol globally. 
#NOTE: locking is unnecessary when accessing globals, as they will automatically lock when necessary
import threading
from new import module
import sys

class loglevels:
    LOG_ERR = 7
    LOG_INIT = 6
    LOG_INFO = 5
    LOG_DEBUG = -1

sys.modules['loglevels'] = loglevels

class ConstError(Exception): pass
class Descriptor(module):
    def __init__(self, value):
        self._value = value
    def __get__(self, *args):
        return self._value
    def __int__(self):
        return int(self._value)
    def __str__(self):
        return str(self._value)
    def __len__(self):
        return len(self._value)
    
class ConstDict(Descriptor):
    '''WARNING: __get__ returns a copy of the dict'''
    def __get__(self, *args):
        result = {}
        result.update(self._value)
        return result

class Const(Descriptor):
    def __set__(self, owner, value):
        raise ConstError('constants are unmodifiable')
    
class Var(Descriptor):
    def __set__(self, owner, value):
        print 'Var Change'
        self.__value = value
        
class GlobalNamespace(module):
    __modlock = threading.RLock()
    def __setattr__(self, name, value):
        print "settattr: %s = %s" % (name, value)
        self.__modlock.acquire(1)
        try:
            object.__setattr__(self, name, value)
            self.__all__.append(name)
        finally:
            self.__modlock.release()
    __setitem__ = __setattr__
    
    @classmethod
    def refresh(self): 
        self.__all__ = [x for x in self.__dict__.keys() if x[0] != '_']
        self.__all__.append('refresh')
    
    def __getattribute__(self, name):
        if name == '__all__':
            try: object.__getattribute__(self, name)
            except AttributeError:
                lis = []
                object.__setattr__(self, '__all__', lis)
                return lis
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return module.__getattribute__(self, name)
    __getitem__ = __getattribute__
