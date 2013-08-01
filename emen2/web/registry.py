import contextlib
import functools

class CallableGeneratorContextManager(contextlib.GeneratorContextManager):
    '''A subclass of :py:class:`contextlib.GeneratorContextManager` which can be called

    Basically, this exists to avoid unecessary hassles with object methods which need special treatment'''
    def __call__(self, *a, **kw):
        '''Enter self's context and call the object returned by __enter__'''
        with self as obj:
            return obj(*a, **kw)

#NOTE: (ed) this is literally ripped out of contextlib,
# but I've replaced contextlib.GeneratorContextManager with the previous class
def contextmanager(func):
    '''see documentation for :py:class:`contextlib.GeneratorContextManager`'''
    @functools.wraps(func)
    def helper(*args, **kwds):
        return CallableGeneratorContextManager(func(*args, **kwds))
        # ^^^ This is the only line diferent from contextlib.GeneratorContextManager
    return helper


class RegisteredObj(object):
    '''Interface definition for :py:attr:`Registry.child_class`'''
    def __init__(self, name, *args):
        self.name = name

    def update(self, other):
        '''override me'''
        pass

def make_ctxt_manager(name):
    '''create a factory method for making and registering objects suitable to be registered in
    the Registry.

    :param str name: The name of the factory method
    :return: A contextmanager
    '''
    @contextmanager
    def _inner(self, name, *args, **kwargs):
        obj = self.registry.get(name) if name in self.registry else self.child_class(name, *args, **kwargs)
        yield obj
        if obj.name not in self.registry:
            self.register(obj)

    _inner.__name__ = name
    return _inner

import threading
class Registry(object):
    #: The kind of object to be stored in the registry
    #: must, as a minimum implement the :py:class:`RegisteredObj` interface
    child_class = None

    def __setitem__(self, name, value):
        with self._lock:
            self.registry[name] = value

    def __getitem__(self, name):
        with self._lock:
            return self.registry[name]

    def __delitem__(self, name):
        with self._lock:
            del self.registry[name]

    @classmethod
    def reset(cls):
        with cls._lock:
            cls.registry.clear()

    @classmethod
    def get(cls, name, default=None):
        with cls._lock:
            return cls.registry.get(name, default)

    _init_lock = threading.RLock()
    @staticmethod
    def setup(cls):
        '''Decorate the registry with this, this sets the 'registry' attribute to an
        empty dictionary and a factory function for creating child objects.

        The name of the factory function is that of the class the registry registers,
        but lowercase'''

        with cls._init_lock:
            factory_name = cls.child_class.__name__.lower()
            setattr(cls, factory_name, make_ctxt_manager(factory_name))
            cls.registry = {}
            cls._lock = threading.RLock()
            return cls

    def register(self, obj):
        with self._lock:
            old_obj = self.registry.get(obj.name)
            result = obj

            if old_obj is not None:
                old_obj.update(obj)
                result = old_obj
            else:
                self.registry[obj.name] = obj

        return result

### DEMO, read this for a practical example of how the above works:

class DataObj(RegisteredObj):
    def __init__(self, name, a):
        RegisteredObj.__init__(self, name)
        self.a = a
        self.b = None
        self.c = None

@Registry.setup
class DataObjRegistry(Registry):
    child_class = DataObj

if __name__ == '__main__':
    #Demo code

    registry = DataObjRegistry()
    with registry.dataobj('first_obj', 1) as obj1:
        obj1.b = 2

    with registry.dataobj('second_obj', 2) as obj2:
        obj2.b = 3
        obj2.c = 4

    with registry.dataobj('third_obj', 3) as obj3:
        obj1.b = 4

    import random
    def shuffled(lis):
        lis = lis[:]
        random.shuffle(lis)
        return iter(lis)


    for obj_name in shuffled(['first_obj', 'second_obj', 'third_obj']):
        with registry.dataobj(obj_name) as obj:
            print '%s - a: %s, b: %s, c: %s' % (obj.name, obj.a, obj.b, obj.c)
