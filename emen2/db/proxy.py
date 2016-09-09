# $Id: proxy.py,v 1.82 2013/05/13 23:33:09 irees Exp $
"""Proxy for accessing EMEN2 API methods

Classes:
    DBProxy
"""

import os
import sys
import time
import collections
import traceback
import weakref
import functools
import inspect

# EMEN2 imports
from emen2.util import listops
import emen2.db.log

##### Warning: This module is very sensitive to changes. #####
##### Please test thoroughly before committing!!         #####

def publicmethod(*args, **kwargs):
    """Decorator for public admin API database method"""
    def _inner(func):
        # print "Registering ", func.func_name
        DBProxy._register_publicmethod(func, *args, **kwargs)
        return func
    return _inner


strht = lambda s, c: s.partition(c)[::2]
def fb():
    return 'hi'

def help(mt):
    def _inner(*a, **b):
        return dict(
            doc = getattr(mt, 'doc', None),
            methods = mt.children.keys()
        )
    return _inner


class MethodTree(object):
    '''Arranges the database methods into a tree so that they can be accessed as db.<a>.<b> (e.g. db.record.get)

    Used by DBProxy.
    '''

    def __init__(self, func=None):
        self.func = func
        if func: self.doc = func.__doc__ or ''
        else: self.doc = ''
        self.children = {}
        self.aliases = {}

    def alias(self, original_name, new_name):
        '''Define an alias for a certain method.

        :param new_name: the name to be replaced
        :param original_name: The replacement name
        '''

        if original_name in self.children:
            raise ValueError, "namespace conflict, cannot alias %r to %r" %(original_name, new_name)
        self.aliases[original_name] = new_name

    def get_alias(self, name):
        '''Check if the method sought has another name.'''
        return self.aliases.get(name,name)

    def __call__(self, *a, **kw):
        return self.func(*a, **kw)

    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        name = name.replace('_', '.')
        return self.get_method(name)

    def add_method(self, name, func):
        '''Add a method to the tree

        Overview of the algorithm:

        1. Split the method name at the first '.', the first part is the child to be found at present, the second is the 'tail'
        2. If the child does not exist, add it
        3. If tail is '', then insert 'func' as a method
        4. Otherwise, recurse on the tail

        :param name: the name of the method
        :param func: the function to be executed
        '''
        head, _, tail = name.partition('.') 
        # use partition and not split since it is guaranteed to return a 3-tuple

        self.children.setdefault(head, MethodTree())

        if tail == '':
            self.children[head].func = func
        else:
            self.children[head].add_method(tail, func)

    def get_method(self, name):
        '''Get a method by name, only resolves aliases once

        :param name: the name of the method
        '''
        name = self.get_alias(name)
        head, _, tail = name.partition('.')
        child = self.children.get(head)

        if child is None:
            if tail: raise AttributeError, "method %r not found"%name
            else:
                result = self
                if name == 'help':
                    result = MethodTree(help(self))
        else:
            result = child.get_method(tail)

        return result

class _Method(object):
    # Taken from XML-RPC lib to support nested methods
    def __init__(self, proxy, name):
        self._proxy = proxy
        self._name = name


    def __getattr__(self, name):
        func = self._proxy._publicmethods.get("%s.%s"%(self._name, name))
        if func:
            return self._proxy._wrap(func)
        return _Method(self._proxy, "%s.%s" % (self._name, name))


    def __call__(self, *args):
        raise AttributeError, "No public method %s"%self._name

class DBProxy(object):
    """A proxy that provides access to database public methods and handles low level details, such as Context and transactions.

    db = DBProxy()
    db._login(name, password)
    """

    _publicmethods = {}
    mt = MethodTree()

    @classmethod
    def _allmethods(cls):
        return set(cls._publicmethods)

    def _get_publicmethods(self):
        result = {}
        for x in self._publicmethods:
            cur = result
            for y in x.split('.'):
                ncur = cur.get(y, {})
                if ncur is not cur: cur[y] = ncur
                cur = ncur
        return result

    def __init__(self, db=None, ctx=None, txn=None):
        # it can cause circular imports if this is at the top level of the module
        import database
        db = db or database.DB()

        self._db = db
        self._ctx = ctx
        self._txn = txn

    # Implements "with" interface
    def __enter__(self):
        # print "--> ENTER"
        if self._txn:
            # raise Exception, "DBProxy: Existing open transaction."
            pass
        else:
            self._txn = self._db.dbenv.txncheck(txn=self._txn)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # print "--> EXIT:", exc_type
        if not self._txn:
            raise Exception, "DBProxy: No transaction to close."
        if exc_type is None:
            self._txn = self._db.dbenv.txncommit(txn=self._txn)
        else:
            self._txn = self._db.dbenv.txnabort(txn=self._txn)
        self._txn = None
    
    # Allow to start with write=true/false
    def _newtxn(self, write=False):
        self._txn = self._db.dbenv.txncheck(txn=self._txn, write=write)
        return self
        
    def _gettxn(self):
        return self._txn

    # Rebind a new Context
    def _setContext(self, ctxid=None, host=None):
        self._ctx = self._db._getcontext(ctxid=ctxid, host=host, txn=self._txn)
        self._ctx.setdb(db=self)
        return self

    def _clearcontext(self):
        self._ctx = None

    def _getctx(self):
        return self._ctx

    def _ismethod(self, name):
        if name in self._allmethods():
            return True
        return False

    @classmethod
    def _register_publicmethod(cls, func, apiname=None, write=False, admin=False, ext=False, compat=None):
        apiname = apiname or func.func_name.replace('_','.')
        setattr(func, 'apiname', apiname)
        setattr(func, 'write', write)
        setattr(func, 'admin', admin)
        setattr(func, 'ext', ext)
        setattr(func, 'compat', compat)

        cls._publicmethods[func.apiname] = func
        cls._publicmethods[func.func_name] = func
        if compat:
            cls._publicmethods[compat] = func

        cls.mt.add_method(apiname, func)
        cls.mt.add_method(func.func_name, func)

        if compat:
            cls.mt.add_method(compat, func)

    def _checkwrite(self, method):
        return getattr(self.mt.get_method(method).func, "write", False)

    ##### Wrap DB Public methods #####

    def _callmethod(self, method, args=(), kwargs={}):
        """Call a method by name with args and kwargs (e.g. RPC access)"""
        m = self.mt.get_method(method).func
        if m is not None:
            return self._wrap(m)(*args, **kwargs)

    def __getattr__(self, name):
        if not name.startswith('_'):
            func = self._publicmethods.get(name)
        else:
            func = self.__getattribute__(name)
            
        if func:
            return self._wrap(func)

        return _Method(self, name)

    def _login(self, username, password, host=None):
        ctxid = self.auth.login(username, password)
        self._setContext(ctxid, host)

    def _wrap(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t = time.time()

            # Remove these from the keyword arguments
            kwargs.pop('ctx', None)
            kwargs.pop('txn', None)

            # Pass the current bound Context
            kwargs['ctx'] = self._ctx
            kwargs['txn'] = self._txn

            emen2.db.log.debug("API: start: %s"%(func.func_name))
            # kwcopy = {}
            # for k,v in kwargs.items():
            #    if k not in ['ctx', 'txn']:
            #        kwcopy[k]=v
            # print "\t<-", args, kwcopy

            if getattr(func, 'admin', False) and not self._ctx.checkadmin():
                raise Exception, "This method requires administrator level access."

            # Make sure the DB is bound to the Context
            self._ctx.setdb(self)

            result = func(self._db, *args, **kwargs)
            ms = (time.time()-t)*1000
            
            emen2.db.log.debug("API: finished: %s in %0.2f ms"%(func.func_name, ms))
            # print "\t->", result
            return result

        return wrapper


__version__ = "$Revision: 1.82 $".split(":")[1][:-1].strip()
