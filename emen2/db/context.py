# $Id: context.py,v 1.36 2012/07/28 06:31:17 irees Exp $
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


# Contexts do not use BaseDBObject since they are completely internal to the DB
class Context(object):
    """Defines a database context (like a session). After a user is authenticated
    a Context is created, and used for subsequent access."""

    attr_user = set()
    # ctxid = property(lambda x:x.name)

    # ian: todo: put current txn in ctx?
    def __init__(self, db=None, username=None, user=None, groups=None, host=None, maxidle=604800, requirehost=False):
        t = emen2.db.database.getctime()

        # Points to DBO for this context
        self.db = None
        self.setdb(db)

        self.name = emen2.db.database.getrandomid()

        # validated user instance, w/ user record, displayname, groups
        self.user = user or {}
        self.groups = groups or set()
        self.grouplevels = {}

        # login name, fall back if user.username does not exist
        self.username = username

        # ip of validated host for this context
        self.host = host

        # last access time for this context
        self.time = t

        self.maxidle = maxidle

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
        self._init_refresh()



class ContextDB(emen2.db.btrees.DBODB):
    dataclass = Context



__version__ = "$Revision: 1.36 $".split(":")[1][:-1].strip()
