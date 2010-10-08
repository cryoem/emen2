import time
import operator
import hashlib
import random
import re
import weakref
import traceback

import emen2.db.config
g = emen2.db.config.g()

import emen2.db
import emen2.db.exceptions
import emen2.db.proxy


# These do not use BaseDBObject since they are completely internal to the DB

class Context(object):
	"""Defines a database context (like a session). After a user is authenticated
	a Context is created, and used for subsequent access."""

	attr_user = set()

	# ian: todo: put current txn in ctx?
	def __init__(self, db=None, username=None, user=None, groups=None, host=None, maxidle=604800, requirehost=False):
		t = emen2.db.database.getctime()

		# Points to Database object for this context
		self.db = None
		self.setdb(db)

		self.ctxid = hashlib.sha1(unicode(username) + unicode(host) + unicode(t) + unicode(random.random())).hexdigest()

		# validated user instance, w/ user record, displayname, groups
		self.user = user
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
			ctxid=self.ctxid,
			user=self.user,
			groups=self.groups,
			grouplevels=self.grouplevels,
			username=self.username,
			time=self.time,
			maxidle=self.maxidle
		)



	def __getstate__(self):
		odict = self.__dict__.copy() # copy the dict since we change it
		for i in ['db', 'user', 'groups', 'grouplevels']:
			odict.pop(i, None)
		return odict


	def setdb(self, db=None, dbproxy=False):
		if not db: return
		self.__dbproxy = dbproxy
		self.db = db


	def refresh(self, user=None, grouplevels=None, host=None, db=None):
		# Information the context needs to be usable
		
		if host != self.host:
			raise emen2.db.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.db.database.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.db.exceptions.SessionError, "Session expired"

		self.time = t
		self.grouplevels = grouplevels or {}
		self.setdb(db=db)

		# userrec not used for now...
		self.user = user

		self.grouplevels["anon"] = 0
		self.grouplevels["authenticated"] = 0
		self.groups = set(self.grouplevels.keys())


	def checkadmin(self):
		return "admin" in self.groups


	def checkreadadmin(self):
		return set(["admin","readadmin"]) & self.groups or False


	def checkcreate(self):
		return set(["admin","create"]) & self.groups or False


	def _setDBProxy(self, txn=None):
		if not isinstance(self.db, emen2.db.proxy.DBProxy):
			g.log.msg("LOG_WARNING","DBProxy created in Context %s"%self.ctxid)
			self.db = emen2.db.proxy.DBProxy(db=self.db, ctx=self, txn=txn)




class TestContext(Context):
	def __init__(self, db=None, username=None, user=None, groups=None, host=None, maxidle=604800, requirehost=False):	
		t = emen2.db.database.getctime()

		# Points to Database object for this context
		self.db = None
		# self.setdb(db)

		username = "root"
		host = "127.0.0.1"
		# self.ctxid = hashlib.sha1(unicode(username) + unicode(host) + unicode(t) + unicode(random.random())).hexdigest()
		# self.ctxid = username+host+unicode(random.random())
		self.ctxid = unicode(random.random())
		self.username = username
		
		# validated user instance, w/ user record, displayname, groups
		self.user = user
		self.groups = groups or set()
		self.grouplevels = {}
		
		# login name, fall back if user.username does not exist

		# ip of validated host for this context
		self.host = host

		# last access time for this context
		self.time = t

		self.maxidle = maxidle

		if requirehost and (not self.username or not self.host):
			raise emen2.db.exceptions.SessionError, "username and host required to init context"


	def refresh(self, *args, **kwargs):
		pass

	def setdb(self, *args, **kwargs):
		pass
		
		



class AnonymousContext(Context):
	def __init__(self, *args, **kwargs):
		Context.__init__(self, *args, username="anonymous", requirehost=False, **kwargs)
		self.__init_refresh()

	def __init_refresh(self):
		self.groups = set(["anon"])
		self.grouplevels = {"anon":0}


	def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
		#if host != self.host:
		#	raise emen2.db.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.db.database.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.db.exceptions.SessionError, "Session expired"

		self.setdb(db=db)
		self.time = t
		self.__init_refresh()





class SpecialRootContext(Context):
	def __init__(self, *args, **kwargs):
		Context.__init__(self, *args, requirehost=False, **kwargs)
		self.ctxid = None
		self.host = None
		self.username = u"root"
		self.__init_refresh()

	def __init_refresh(self):
		self.groups = set(["admin"])
		self.grouplevels = {"admin":3}


	def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
		if host != self.host:
			raise emen2.db.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.db.database.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.db.exceptions.SessionError, "Session expired"

		self.setdb(db=db)
		self.time = t
		self.__init_refresh()

