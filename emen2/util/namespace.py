# $Id$
'''\
Implements namespaces for method grouping
example use:

class DB(object):
    @instantiate
    class record(Namespace):
        @classmethod
        def _init(self):
            self._value = 1 # warning, this will be shared among all db instances -- not threadsafe
        def get(self, db):
            return self._value
        def set(self, db, value):
            self._value = value
        def checkparam(self, db):
            print db.param.get()
            return db.param.get() == self.get()
    @instantiate
    class param(Namespace):
        @classmethod
        def _init(self):
            self._value = 1 # warning, this will be shared among all db instances -- not threadsafe
        def get(self, db):
            db.othermethod(self._value)
            return self._value
        def set(self, db, value):
            db.othermethod(self._value)
            self._value = value
            db.othermethod(self._value)
    def othermethod(self, value): print self, value
    def recordget(self): return self.record.get()
    def recordset(self, value): return self.record.set(value)

'''
import functools
import collections
def instantiate(cls): return cls()

class Namespace(object):
    def namespace(name, bases, dict_):
        cls = type(name, bases, dict_)
        cls._dict = {}
        return cls
    __metaclass__ = namespace
    def __init__(self, instance=None):
        self.__dict__ = self._dict
        self._inst = instance
        self._init()
    def _init(self): pass
    def __get__(self, instance, owner):
        result = type(self)(instance)
        return result
    def _check_inst(self):
        if self._inst is None:
            raise AttributeError, 'this class is unbound, can\'t call methods'
    def __getattribute__(self, name):
        if not name.startswith('_'):
            self._check_inst()
        result = object.__getattribute__(self, name)
        if callable(result) and not name.startswith('_'):
            result = functools.partial(result, self._inst)
        return result
__version__ = "$Revision$".split(":")[1][:-1].strip()
