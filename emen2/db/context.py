"""Sessions / Contexts."""

import time
import operator
import hashlib
import random
import re
import weakref
import traceback

# EMEN2 imports
import emen2.db.database
import emen2.db.exceptions
import emen2.db.proxy
import emen2.db.config

# This is temporarily here. It may be moved.
class Cacher(object):
    """Help keep track of calculated values."""
    def __init__(self):
        self.cache = {}

    def reset_cache(self):
        self.cache = {}

    def store(self, key, result):
        self.cache[key] = result

    def check(self, key):
        # key = tuple(args)
        # print "cache check:", key
        if key in self.cache:
            # print '\tfound:', self.cache[key]
            return True, self.cache[key]
        # print '\tnot found'
        return False, None
        
class Context(emen2.db.dataobject.PrivateDBO):
    """Defines a database context (like a session). After a user is authenticated
    a Context is created, and used for subsequent access."""

    username = property(lambda self:self.data.get('user'))

    def setContext(self, ctx):
        self.ctx = self

    def init(self):
        super(Context, self).init()
        self.ctx = self
        self.db = None
        self.groups = set()
        self.time = time.time()
        self.maxidle = 100000
        self.data['user'] = None
        self.data['host'] = None
        self.data['disabled'] = False

    def _set_user(self, key, value):
        self.data['user'] = value

    def _set_host(self, key, value):
        self.data['host'] = value

    def _set_disabled(self, key, value):
        if value:
            self.disable()
        else:
            self.enable()

    def disable(self):
        self.data['disabled'] = True
    
    def enable(self):
        self.data['disabled'] = False        

    def setdb(self, db=None):
        """Associate a DB connection with the context."""
        if not db:
            return
        if not isinstance(db, emen2.db.proxy.DBProxy):
            db = emen2.db.proxy.DBProxy(db=db, ctx=self)
        self.db = db
      
    def refresh(self, groups=None, host=None, db=None):
        t = emen2.db.database.getctime()
        expired = False
        if self.data.get('disabled'):
            expired = True
        if host != self.host:
            expired = True
        if t > (self.time + self.maxidle):
            expired = True
        if expired:
            raise emen2.db.exceptions.SessionError("Session expired.")  
        self.time = t
        self.setdb(db=db)
        self.cache = Cacher()
        self.groups = set(groups or []) | set(['anon', 'authenticated'])
            
    def checkadmin(self):
        return 'admin' in self.groups

    def checkreadadmin(self):
        return 'admin' in self.groups or 'readadmin' in self.groups

    def checkcreate(self):
        return 'admin' in self.groups or 'create' in self.groups

class SpecialRootContext(Context):
    def refresh(self, groups=None, host=None, db=None):
        super(SpecialRootContext, self).refresh()
        self.user = 'root'
        self.groups = set(['admin', 'anon', 'authenticated'])

class AnonymousContext(Context):
    def refresh(self, groups=None, host=None, db=None):
        super(AnonymousContext, self).refresh()
        self.user = 'anon'
        self.groups = set(['anon'])
