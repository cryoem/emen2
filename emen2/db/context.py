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

    name = property(lambda x:x.data['name'])
    username = property(lambda x:x.data['username'])
    groups = property(lambda x:x.data['groups'])
    grouplevels = property(lambda x:x.data['grouplevels'])
    host = property(lambda x:x.data['host'])
    time = property(lambda x:x.data['time'])
    utcnow = property(lambda x:x.data['utcnow'])
    maxidle = property(lambda x:x.data['maxidle'])

    def __init__(self, db=None, username=None, user=None, groups=None, grouplevels=None, host=None, maxidle=604800):
        self.db = None
        self.setdb(db)

        # Used for caching items
        self.cache = Cacher()
        self.user = user or {}

        # Data
        self.data = {}

        # Context UUID
        self.data['name'] = emen2.db.database.getrandomid()

        # Context user information
        self.data['username'] = username
        self.data['groups'] = groups or set()
        self.data['grouplevels'] = grouplevels or {}

        # Client IP
        self.data['host'] = host

        # Context time
        self.data['time'] = emen2.db.database.getctime()
        self.data['utcnow'] = emen2.db.database.utcnow()

        # Maximum idle time before context expires
        self.data['maxidle'] = maxidle
        
    def __getstate__(self):
        return {'data':self.data}

    def setdb(self, db=None):
        """Associate a DB connection with the context."""
        if not db:
            return
        if not isinstance(db, emen2.db.proxy.DBProxy):
            db = emen2.db.proxy.DBProxy(db=db, ctx=self)
        self.db = db

    def refresh(self, grouplevels=None, host=None, db=None):
        if host != self.host:
            raise emen2.db.exceptions.SessionError, "Session expired"

        t = emen2.db.database.getctime()
        if t > (self.time + self.maxidle):
            raise emen2.db.exceptions.SessionError, "Session expired"

        self.data['time'] = t
        self.data['utcnow'] = emen2.db.database.utcnow()
        self.data['grouplevels'] = grouplevels or {}

        self.cache = Cacher()
        self.setdb(db=db)
        
        self.user = {}
        self.data['grouplevels']["anon"] = 0
        self.data['grouplevels']["authenticated"] = self.data['grouplevels'].get('authenticated', 0)
        self.data['groups'] = set(self.grouplevels.keys())

    def checkadmin(self):
        return "admin" in self.groups

    def checkreadadmin(self):
        return 'admin' in self.groups or 'readadmin' in self.groups

    def checkcreate(self):
        return 'admin' in self.groups or 'create' in self.groups

class SpecialRootContext(Context):
    def refresh(self, user=None, grouplevels=None, host=None, username=None, db=None, txn=None):
        self.setdb(db=db)
        self.cache = Cacher()        
        data = {}
        data['name'] = None
        data['username'] = username or 'root'
        data['time'] = emen2.db.database.getctime()
        data['utcnow'] = emen2.db.database.utcnow()
        data['groups'] = set(["admin"])
        data['grouplevels'] = {"admin":3}
        self.data.update(data)

class AnonymousContext(Context):
    def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
        self.setdb(db=db)
        self.cache = Cacher()        
        data = {}
        data['name'] = None
        data['username'] = 'anonymous'
        data['time'] = emen2.db.database.getctime()
        data['utcnow'] = emen2.db.database.utcnow()
        data['groups'] = set(["anon"])
        data['grouplevels'] = {"anon":0}
        self.data.update(data)

