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

    def setContext(self, ctx):
        self.ctx = self

    def init(self):
        super(Context, self).init()
        self.ctx = self
        self.db = None
        self.groups = []
        self.grouplevels = {}
        self.time = time.time()
        self.maxidle = 100000
        self.data['user'] = None
        self.data['host'] = None

    def _set_user(self, key, value):
        self.data['user'] = value

    def _set_host(self, key, value):
        self.data['host'] = value

    def setdb(self, db=None):
        """Associate a DB connection with the context."""
        if not db:
            return
        if not isinstance(db, emen2.db.proxy.DBProxy):
            db = emen2.db.proxy.DBProxy(db=db, ctx=self)
        self.db = db

    def checkhost(self, host):
        if host != self.host:
            raise emen2.db.exceptions.SessionError("Session expired.")
    
    def checktime(self, t):
        if t > (self.time + self.maxidle):
            raise emen2.db.exceptions.SessionError("Session expired")

    def refresh(self, grouplevels=None, host=None, db=None):
        t = emen2.db.database.getctime()
        self.checkhost(host)
        self.checktime(t)
        self.setdb(db=db)

        self.cache = Cacher()
        self.time = t

        self.grouplevels = grouplevels or {}
        self.grouplevels["anon"] = 0
        self.grouplevels["authenticated"] = self.grouplevels.get('authenticated', 0)
        self.groups = self.grouplevels.keys()
        
    def checkadmin(self):
        return 'admin' in self.groups

    def checkreadadmin(self):
        return 'admin' in self.groups or 'readadmin' in self.groups

    def checkcreate(self):
        return 'admin' in self.groups or 'create' in self.groups

class SpecialRootContext(Context):
    def refresh(self, grouplevels=None, host=None):
        super(SpecialRootContext, self).refresh()
        self.user = 'root'
        self.grouplevels = {'admin':3}
        self.groups = ['admin']

class AnonymousContext(Context):
    def refresh(self, grouplevels=None, host=None):
        super(SpecialRootContext, self).refresh()
        self.user = 'anon'
        self.grouplevels = {'anon':0}
        self.groups = ['anon']
