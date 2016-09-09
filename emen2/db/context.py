# $Id: context.py,v 1.40 2013/05/01 23:38:40 irees Exp $
"""Security and authentication

Classes:
    Context: DBO for storing a login
    AnonymousContext: Special Context for anonymous users
    SpecialRootContext: Special Context for root
    ContextDB: BTree subclass for storing Contexts

"""

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
        
    

# Contexts do not use BaseDBObject since they are completely internal to the DB
class Context(object):
    """Defines a database context (like a session). After a user is authenticated
    a Context is created, and used for subsequent access."""

    attr_user = set()

    def __init__(self, db=None, username=None, user=None, groups=None, grouplevels=None, host=None, maxidle=604800):
        self.db = None
        self.setdb(db)

        # Context UUID
        self.name = emen2.db.database.getrandomid()

        # Context user information
        self.user = user or {}
        self.username = username
        self.groups = groups or set()
        self.grouplevels = grouplevels or {}


        # Client IP
        self.host = host

        # Context time
        self.time = emen2.db.database.getctime()
        self.utcnow = emen2.db.database.utcnow()

        # Maximum idle time before context expires
        self.maxidle = maxidle
        
        # Used for caching items
        self.cache = Cacher()

    def __getstate__(self):
        # copy the dict since we change it
        odict = self.__dict__.copy()
        for i in ['db', 'user', 'groups', 'grouplevels']:
            odict.pop(i, None)
        return odict

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

        self.time = t
        self.utcnow = emen2.db.database.utcnow()
        self.cache = Cacher()
        self.grouplevels = grouplevels or {}
        self.setdb(db=db)

        self.user = {}
        self.grouplevels["anon"] = 0
        self.grouplevels["authenticated"] = self.grouplevels.get('authenticated', 0)
        self.groups = set(self.grouplevels.keys())

    def checkadmin(self):
        return "admin" in self.groups

    def checkreadadmin(self):
        return set(["admin", "readadmin"]) & self.groups

    def checkcreate(self):
        return set(["admin", "create"]) & self.groups


class SpecialRootContext(Context):
    def refresh(self, user=None, grouplevels=None, host=None, username=None, db=None, txn=None):
        self.name = None
        self.setdb(db=db)
        self.username = username or u'root'
        self.time = emen2.db.database.getctime()
        self.utcnow = emen2.db.database.utcnow()
        self.cache = Cacher()        
        self.groups = set(["admin"])
        self.grouplevels = {"admin":3}


class AnonymousContext(Context):
    def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
        self.name = None
        self.setdb(db=db)
        self.username = 'anonymous'
        self.time = emen2.db.database.getctime()
        self.utcnow = emen2.db.database.utcnow()
        self.cache = Cacher()
        self.groups = set(["anon"])
        self.grouplevels = {"anon":0}

__version__ = "$Revision: 1.40 $".split(":")[1][:-1].strip()