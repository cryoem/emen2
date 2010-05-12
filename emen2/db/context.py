import time
import operator
import hashlib
import random
import UserDict
import re
import weakref
import traceback

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import emen2.Database.subsystems.dbtime
import emen2.Database.subsystems.exceptions
import emen2.Database.DBProxy

# These do not use BaseDBObject since they are completely internal to the DB

class Context(object):
	"""Defines a database context (like a session). After a user is authenticated
	a Context is created, and used for subsequent access."""

	attr_user = set()
	attr_admin = set()
	attr_all = attr_user | attr_admin


	# ian: todo: put current txn in ctx?
	def __init__(self, db=None, username=None, user=None, groups=None, host=None, maxidle=604800, requirehost=False):


		t = emen2.Database.subsystems.dbtime.getctime()

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
			raise emen2.Database.subsystems.exceptions.SessionError, "username and host required to init context"


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
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		odict['db'] = None #_Context__db
		odict['user'] = None
		odict['groups'] = None
		odict['grouplevels'] = None
		return odict


	def setdb(self, db=None, dbproxy=False, txn=None):
		if not db: return
		self.__dbproxy = dbproxy
		self.db = db



	def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
		# Information the context needs to be usable

		if host != self.host:
			raise emen2.Database.subsystems.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.Database.subsystems.dbtime.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.Database.subsystems.exceptions.SessionError, "Session expired"


		self.time = t
		self.grouplevels = grouplevels or {}
		self.setdb(db=db, txn=txn)

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
		if not isinstance(self.db, emen2.Database.DBProxy.DBProxy):
			# g.log.msg("LOG_WARNING","DBProxy created in Context %s"%self.ctxid)
			self.db = emen2.Database.DBProxy.DBProxy(db=self.db, ctx=self, txn=txn)




class AnonymousContext(Context):
	def __init__(self, *args, **kwargs):
		Context.__init__(self, *args, username="anonymous", requirehost=False, **kwargs)
		self.__init_refresh()

	def __init_refresh(self):
		self.groups = set(["anon"])
		self.grouplevels = {"anon":0}


	def refresh(self, user=None, grouplevels=None, host=None, db=None, txn=None):
		#if host != self.host:
		#	raise emen2.Database.subsystems.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.Database.subsystems.dbtime.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.Database.subsystems.exceptions.SessionError, "Session expired"

		self.setdb(db=db, txn=txn)
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
			raise emen2.Database.subsystems.exceptions.SessionError, "Session host mismatch (%s != %s)"%(host, self.host)

		t = emen2.Database.subsystems.dbtime.getctime()
		if t > (self.time + self.maxidle):
			raise emen2.Database.subsystems.exceptions.SessionError, "Session expired"

		self.setdb(db=db, txn=txn)
		self.time = t
		self.__init_refresh()

