#NOTE: locking is unnecessary when accessing globals, as they will automatically lock when necessary

#NOTE: access globals this way:
#  import emen2.globalns
#  g = emen2.globalns.GlobalNamespace('')
#  g.<varname> accesses the variable
#  g.<varname> = <value> sets a variable in a threadsafe manner.

import threading
from new import module

#class ConstError(Exception): pass
#class Descriptor(object):
#    def __init__(self, value):
#        self._value = value
#    def __get__(self, *args):
#        return self._value
#    def __set__(self, value):
#        return self._value
#  
#class ConstDict(Descriptor):
#    '''WARNING: __get__ returns a copy of the dict'''
#    def __get__(self, *args):
#        result = {}
#        result.update(self._value)
#        return result
#
#class Const(Descriptor):
#    def __set__(self, owner, value):
#        raise ConstError('constants are unmodifiable')
#    
#class Var(Descriptor):
#    def __set__(self, owner, value):
#        print 'Var Change'
#        self.__value = value
        
class GlobalNamespace(module):
    __vardict = {}
    __modlock = threading.RLock()
    __all__ = []
    def __setattr__(self, name, value):
        self.__modlock.acquire(1)
        try:
            self.__addattr(name, value)
        finally:
            self.__modlock.release()
    __setitem__ = __setattr__
    
    @classmethod
    def __addattr(cls, name, value):
        if not name in cls.__all__: 
            cls.__all__.append(name)
        cls.__vardict[name] = value
            
    @classmethod
    def refresh(self): 
        self.__all__ = [x for x in self.__vardict.keys() if x[0] != '_']
        self.__all__.append('refresh')
        
    @classmethod
    def getattr(cls, name):
        if name.startswith('___'):
            name = name.partition('___')[-1]
        result = cls.__vardict.get(name)
        return result
    
    def __getattribute__(self, name):
        result = None
        try:
            result = object.__getattribute__(self, name)
        except AttributeError:
            result = object.__getattribute__(self, 'getattr')(name)
            if result == None:
                try: 
                    result = module.__getattribute__(self, name)
                except AttributeError:
                    pass
        if result == None:
            raise AttributeError('Attribute Not Found: %s' % name)
        else:
            return result
    __getitem__ = __getattribute__
    
    def update(self, dict):
        self.__vardict.update(dict)
    
    def reset(self):
        self.__class__.__vardict = {}

def test():
    a = GlobalNamespace('one instance')
    b = GlobalNamespace('two instance')
    try:
        a.a
    except AttributeError:
        pass
    else:
        assert False

    #test 1 attribute access
    a.a = 1
    assert (a.a == a.a)
    assert (a.a == b.a)
    assert (a.a == a.___a)
    
    #test 2
    a.reset()
    try:
        print a.a
    except AttributeError:
        pass
    else:
        assert False
        
    #test 3
    tempdict = dict(a=1, b=2, c=3)
    a.update(tempdict)
    assert tempdict['a'] == a.a
    assert tempdict['a'] == b.a
    assert tempdict['a'] == a.___a
    a.reset()
    
if __name__ == '__main__':
    test()
