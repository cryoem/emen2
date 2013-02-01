# $Id$
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
import emen2.db.btrees
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

    def get_cache_key(self, *args, **kwargs):
        return (args, tuple(kwargs.items()))

    def store(self, key, result):
        self.cache[key] = result

    def check_cache(self, key):
        if self.cache.has_key(key):
            return True, self.cache[key]
        return False, None
    


# Contexts do not use BaseDBObject since they are completely internal to the DB
class Context(object):
    """Defines a database context (like a session). After a user is authenticated
    a Context is created, and used for subsequent access."""

    attr_user = set()

    # ian: todo: put current txn in ctx?
    def __init__(self, db=None, username=None, user=None, groups=None, host=None, maxidle=604800, requirehost=False):
        # Points to DBO for this context
        self.db = None
        self.setdb(db)

        # Context UUID
        self.name = emen2.db.database.getrandomid()

        # Context user information
        self.user = user or {}
        self.groups = groups or set()
        self.grouplevels = {}

        # Login name, fall back if user.username does not exist
        self.username = username

        # Client IP
        self.host = host

        # Context time
        self.time = emen2.db.database.getctime()
        self.utcnow = emen2.db.database.gettime()

        # Maximum idle time before context expires
        self.maxidle = maxidle
        
        # Used for caching items
        self.cache = Cacher()


        if requirehost and (not self.username or not self.host):
            raise emen2.db.exceptions.SessionError, "username and host required to init context"


    def json_equivalent(self):
        return dict(
            name = self.name,
            user = self.user,
            groups = self.groups,
            grouplevels = self.grouplevels,
            username = self.username,
            time = self.time,
            maxidle = self.maxidle
        )


    def __getstate__(self):
        # copy the dict since we change it
        # return self.json_equivalent()
        odict = self.__dict__.copy()
        for i in ['db', 'user', 'groups', 'grouplevels']:
            odict.pop(i, None)
        return odict


    def setdb(self, db=None):
        if not db:
            return

        if not isinstance(db, emen2.db.proxy.DBProxy):
            db = emen2.db.proxy.DBProxy(db=db, ctx=self)

        self.db = db


    def refresh(self, grouplevels=None, host=None, db=None):
        # Information the context needs to be usable

        if host != self.host:
            raise emen2.db.exceptions.SessionError, "Session expired"

        t = emen2.db.database.getctime()
        if t > (self.time + self.maxidle):
            raise emen2.db.exceptions.SessionError, "Session expired"

        self.time = t
        self.utcnow = emen2.db.database.gettime()
        self.cache = Cacher()
        self.grouplevels = grouplevels or {}
        self.setdb(db=db)

        self.user = {} # self.db.user.get(self.username)
        self.grouplevels["anon"] = 0
        self.grouplevels["authenticated"] = self.grouplevels.get('authenticated', 0)
        self.groups = set(self.grouplevels.keys())


    def checkadmin(self):
        return "admin" in self.groups


    def checkreadadmin(self):
        return set(["admin","readadmin"]) & self.groups or False


    def checkcreate(self):
        return set(["admin","create"]) & self.groups or False



class AnonymousContext(Context):
    def __init__(self, *args, **kwargs):
        Context.__init__(self, *args, username="anonymous", requirehost=False, **kwargs)
        self._init_refresh()

    def _init_refresh(self):
        self.groups = set(["anon"])
        self.grouplevels = {"anon":0}


    def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
        #if host != self.host:
        #    raise emen2.db.exceptions.SessionError, "Session expired"

        t = emen2.db.database.getctime()
        if t > (self.time + self.maxidle):
            raise emen2.db.exceptions.SessionError, "Session expired"

        self.setdb(db=db)
        self.time = t
        self.utcnow = emen2.db.database.gettime()
        self.cache = Cacher()
        self._init_refresh()



class SpecialRootContext(Context):
    def __init__(self, *args, **kwargs):
        Context.__init__(self, *args, requirehost=False, **kwargs)
        self.name = None
        self.host = None
        self.username = u"root"
        self._init_refresh()


    def _init_refresh(self):
        self.groups = set(["admin"])
        self.grouplevels = {"admin":3}


    def refresh(self, user=None, grouplevels=None, host=None, username=None, db=None, txn=None):
        if host != self.host:
            raise emen2.db.exceptions.SessionError, "Session expired"

        t = emen2.db.database.getctime()
        if t > (self.time + self.maxidle):
            raise emen2.db.exceptions.SessionError, "Session expired"

        self.username = username or u'root'
        self.setdb(db=db)
        self.time = t
        self.utcnow = emen2.db.database.gettime()
        self.cache = Cacher()        
        self._init_refresh()



class ContextDB(emen2.db.btrees.DBODB):
    dataclass = Context



__version__ = "$Revision$".split(":")[1][:-1].strip()
