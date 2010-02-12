from __future__ import with_statement
#basestring goes away in a later python version
basestring = (str, unicode)

import copy
import atexit
import hashlib
import operator
import os
import sys
import time
import traceback
import collections
import itertools
import random
import cPickle as pickle
import bsddb3
import demjson
import re
import shutil
import weakref

from functools import partial, wraps

import emen2
import emen2.util.utils
import emen2.util.ticker
import emen2.util.emailutil

import emen2.config.config
import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import DBProxy
import DBExt
import datatypes
import dataobjects
import extensions
import subsystems
import subsystems.dbtime
import subsystems.btrees
import subsystems.datatypes
import subsystems.exceptions

from emen2.Database.DBFlags import *


DBENV = None


# ian: todo: low: do this in a better way
# this is used by db.checkversion
VERSIONS = {
	"API": g.VERSION,
	"emen2client": 20100209
}


@atexit.register
def DB_Close():
	l = DB.opendbs.keys()
	for i in l:
		g.log.msg('LOG_DEBUG', i._DB__dbenv)
		i.close()


# ian: todo: low: does this need to be on?
def DB_syncall():
	"""This 'syncs' all open databases"""
	#for i in subsystems.btrees.BTree.alltrees.keys(): i.sync()
	pass



def DB_stat():

	global DBENV
	if not DBENV:
		return

	sys.stdout.flush()
	print >> sys.stderr, "DB has %d transactions left" % DB.txncounter

	tx_max = DBENV.get_tx_max()
	g.log.msg('LOG_DEBUG', "Open transactions: %s"%tx_max)

	txn_stat = DBENV.txn_stat()
	g.log.msg('LOG_DEBUG', "Transaction stats: ")
	for k,v in txn_stat.items():
		g.log.msg('LOG_DEBUG', "\t%s: %s"%(k,v))

	log_archive = DBENV.log_archive()
	g.log.msg('LOG_DEBUG', "Archive: %s"%log_archive)

	lock_stat = DBENV.lock_stat()
	g.log.msg('LOG_DEBUG', "Lock stats: ")
	for k,v in lock_stat.items():
		g.log.msg('LOG_DEBUG', "\t%s: %s"%(k,v))





class DB(object):
	"""Main database class"""
	opendbs = weakref.WeakKeyDictionary()

	@staticmethod
	def __init_vtm():
		import datatypes.core_vartypes
		import datatypes.core_macros
		import datatypes.core_properties


	inst = lambda x:x()
	@inst
	class bdbs(object):
		def init(self, db, dbenv, txn):
			old = set(self.__dict__)

			# Security items
			self.users = subsystems.btrees.BTree("users", keytype="s", filename=db.path+"/security/users.bdb", dbenv=dbenv, txn=txn)
			self.newuserqueue = subsystems.btrees.BTree("newusers", keytype="s", filename=db.path+"/security/newusers.bdb", dbenv=dbenv, txn=txn)
			self.groups = subsystems.btrees.BTree("groups", keytype="s", filename=db.path+"/security/groups.bdb", dbenv=dbenv, txn=txn)
			self.contexts_p = subsystems.btrees.BTree("contexts", keytype="s", filename=db.path+"/security/contexts.bdb", dbenv=dbenv, txn=txn)

			# Database items
			self.paramdefs = subsystems.btrees.RelateBTree("ParamDefs", keytype="s", filename=db.path+"/ParamDefs.bdb", dbenv=dbenv, txn=txn)
			self.bdocounter = subsystems.btrees.BTree("BinNames", keytype="s", filename=db.path+"/BinNames.bdb", dbenv=dbenv, txn=txn)
			self.recorddefs = subsystems.btrees.RelateBTree("RecordDefs", keytype="s", filename=db.path+"/RecordDefs.bdb", dbenv=dbenv, txn=txn)
			self.workflow = subsystems.btrees.BTree("workflow", keytype="d", filename=db.path+"/workflow.bdb", dbenv=dbenv, txn=txn)
			self.records = subsystems.btrees.RelateBTree("database", keytype="d_old", filename=db.path+"/database.bdb", dbenv=dbenv, txn=txn)

			# Indices
			self.secrindex = subsystems.btrees.FieldBTree("secrindex", filename=db.path+"/index/security/secrindex.bdb", keytype="s", datatype="d", dbenv=dbenv, txn=txn)
			self.secrindex_groups = subsystems.btrees.FieldBTree("secrindex_groups", filename=db.path+"/index/security/secrindex_groups.bdb", keytype="s", datatype="d", dbenv=dbenv, txn=txn)
			self.groupsbyuser = subsystems.btrees.FieldBTree("groupsbyuser", keytype="s", datatype="s", filename=db.path+"/index/security/groupsbyuser.bdb", dbenv=dbenv, txn=txn)
			self.recorddefindex = subsystems.btrees.FieldBTree("recorddef", filename=db.path+"/index/records/recorddefindex.bdb", keytype="s", datatype="d", dbenv=dbenv, txn=txn)
			self.indexkeys = subsystems.btrees.FieldBTree("indexkeys", keytype="s", filename=db.path+"/index/indexkeys.bdb", dbenv=dbenv, txn=txn)
			# timeindex now handled by modifytime param index
			# self.timeindex = subsystems.btrees.BTree("timeindex", keytype="d", datatype="s", filename=db.path+"/index/records/timeindex.bdb", dbenv=dbenv, txn=txn)

			self.bdbs = set(self.__dict__) - old
			self.contexts = {}
			self.fieldindex = {}

		def openparamindex(self, paramname, filename, keytype="s", datatype="d", dbenv=None, txn=None):
			self.fieldindex[paramname] = subsystems.btrees.FieldBTree(paramname, keytype=keytype, datatype=datatype, filename=filename, dbenv=dbenv, txn=txn)

		def closeparamindex(self, paramname):
			self.fieldindex.pop(paramname).close()

		def closeparamindexes(self):
			[self.__closeparamindex(x) for x in self.fieldindex.keys()]



	def __init__(self, path=".", logfile="db.log"):
		"""Init DB
		@keyparam path Path to DB (default=cwd)
		@keyparam logfile Log file (default=db.log)
		"""

		if g.USETXN:
			self.newtxn = self.newtxn1
		else:
			g.log.msg("LOG_INFO","Note: transaction support disabled")

		self.lastctxclean = time.time()
		self.opentime = self.__gettime()

		self.path = path or g.EMEN2DBPATH
		self.logfile = self.path + "/" + logfile

		self.txnid = 0
		self.txnlog = {}

		self.__init_vtm()
		self.vtm = subsystems.datatypes.VartypeManager()
		self.indexablevartypes = set([i.getvartype() for i in filter(lambda x:x.getindextype(), [self.vtm.getvartype(i) for i in self.vtm.getvartypes()])])

		self.__cache_vartype_indextype = {}
		for vt in self.vtm.getvartypes():
			self.__cache_vartype_indextype[vt] = self.vtm.getvartype(vt).getindextype()

		# This sets up a DB environment, which allows multithreaded access, transactions, etc.
		if not os.access(self.path + "/home", os.F_OK):
			os.makedirs(self.path + "/home")
			dbci = file(g.EMEN2ROOT+'/config/DB_CONFIG')
			dbco = file(self.path + '/home/DB_CONFIG', 'w')
			try:
				dbco.write(dbci.read())
			finally:
				[fil.close() for fil in (dbci, dbco)]


		for path in ["/security","/index","/index/security","/index/params","/index/records"]:
			if not os.access(self.path + path, os.F_OK):
				os.makedirs(self.path + path)


		# Open DB Env
		global DBENV
		DBENV = None

		if DBENV == None:
			g.log.msg("LOG_INFO","Opening Database Environment")
			DBENV = bsddb3.db.DBEnv()
			DBENV.set_data_dir(self.path)
			DBENV.open(self.path+"/home", g.ENVOPENFLAGS)
			DB.opendbs[self] = 1

		self.__dbenv = DBENV


		# Open Database
		txn = self.newtxn()
		try:
			self.bdbs.init(self, self.__dbenv, txn=txn)
		except Exception, inst:
			self.txnabort(txn=txn)
			raise
		else:
			self.txncommit(txn=txn)



		# Check if database is initialized
		txn = self.newtxn()
		try:
			# ian: todo: hard: continue evaluating how we will create new recids
			#			my best idea is to use the cursor.set(DB_LAST)...
			# self.__dbseq = self.bdbs.records.create_sequence()
			ctx = self.__makerootcontext(txn=txn, host="localhost")

			try:
				maxr = self.bdbs.records.sget(-1, txn=txn)
				g.log.msg("LOG_INFO","Opened database with %s records"%maxr)

			except KeyError:
				g.log.msg('LOG_INFO', "Initializing skeleton database ctx: %r txn: %r" % (ctx, txn))

				if raw_input('record counter not found in key -1, enter y to reinitialize: ').lower().startswith('y'):
					self.__createskeletondb(ctx=ctx, txn=txn)

		except Exception, inst:
			g.log.msg('LOG_ERROR', inst)
			self.txnabort(txn=txn)
			raise

		else:
			self.txncommit(txn=txn)


		g.log_init('DB logfile:', self.logfile)
		g.log.add_output('ALL', file(self.logfile, "a"), current_file=True)



	def __del__(self):
		g.debug('cleaning up DB instance')



	def __createskeletondb(self, ctx=None, txn=None):
		"""Creates a skeleton database; imports users/params/protocols/etc. from Database/skeleton/core_* """

		# typically uses SpecialRootContext
		import skeleton

		self.bdbs.records.set(-1, 0, txn=txn)

		for i in skeleton.core_users.items:
			self.adduser(i, ctx=ctx, txn=txn)

		for i in skeleton.core_paramdefs.items:
			self.putparamdef(i, ctx=ctx, txn=txn)

		for i in skeleton.core_recorddefs.items:
			self.putrecorddef(i, ctx=ctx, txn=txn)

		for i in skeleton.core_groups.items:
			self.putgroup(i, ctx=ctx, txn=txn)

		self.setpassword(g.ROOTPW, g.ROOTPW, username="root", ctx=ctx, txn=txn)



	# @DBProxy.publicmethod
	# def raise_exception(self, ctx=None, txn=None):
	# 	raise Exception, "Test! ctxid %s host %s txn %s"%(ctx.ctxid, ctx.host, txn)



	# ian: todo: simple: print more statistics; needs a txn?
	def __str__(self):
		#return "Database %d records\n( %s )"%(int(self.bdbs.records.get(-1,0)), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))
		return "<Database: %s>"%hex(id(self))


	def __del__(self):
		self.close()


	def close(self):
		"""Close DB"""
		g.log.msg('LOG_DEBUG', "Closing %d BDB databases"%(len(subsystems.btrees.BTree.alltrees)))
		try:
			for i in subsystems.btrees.BTree.alltrees.keys():
				g.log.msg('LOG_INFO', 'closing %s\n' % unicode(i))
				i.close()
		except Exception, inst:
			g.log.msg('LOG_ERROR', inst)

		self.__dbenv.close()



	def __flatten(self, l):
		ltypes=(set, list, tuple)
		out = []
		for item in l:
			if isinstance(item, ltypes): out.extend(self.__flatten(item))
			else:
				out.append(item)
		return out



	###############################
	# section: Transaction Management
	###############################


	txncounter = 0

	# one of these 2 methods (newtxn1/newtxn) is mapped to self.newtxn()
	def newtxn1(self, parent=None, ctx=None):
		"""New transaction (txns enabled). Accepts parent txn instance."""
		# g.log.msg('LOG_INFO', 'printing traceback')
		# g.log.print_traceback(steps=5)
		# g.log.msg("LOG_TXN","NEW TXN, PARENT --> %s"%parent)
		txn = self.__dbenv.txn_begin(parent=parent, flags=g.TXNFLAGS)
		try:
			type(self).txncounter += 1
			self.txnlog[id(txn)] = txn
		except:
			self.txnabort(ctx=ctx, txn=txn)
			raise
		return txn



	def newtxn(self, ctx=None, txn=None):
		"""New transaction (txns disabled)"""
		return None



	def txncheck(self, txnid=0, ctx=None, txn=None):
		"""Check a txn status; accepts txn instance"""
		txn = self.txnlog.get(txnid, txn)
		if not txn:
			txn = self.newtxn(ctx=ctx)
		return txn



	def txnabort(self, txnid=0, ctx=None, txn=None):
		"""Abort txn; accepts txn ID or instance"""
		# g.log.msg('LOG_TXN', "TXN ABORT --> %s"%txn)
		txn = self.txnlog.get(txnid, txn)

		if txn:
			txn.abort()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise ValueError, 'Transaction not found'



	def txncommit(self, txnid=0, ctx=None, txn=None):
		"""Commit txn; accepts txn ID or instance"""
		# g.log.msg("LOG_TXN","TXN COMMIT --> %s"%txn)
		txn = self.txnlog.get(txnid, txn)

		if txn != None:
			txn.commit()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1

		else:
			raise ValueError, 'Transaction not found'






	###############################
	# section: Time and Version Management
	###############################

	@DBProxy.publicmethod
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program"""
		return VERSIONS.get(program)



	@DBProxy.publicmethod
	def gettime(self, ctx=None, txn=None):
		"""DB Time
		@return DB time date string"""
		return subsystems.dbtime.gettime()



	def __gettime(self):
		"""(Internal) DB Time
		@return DB time date string"""
		return subsystems.dbtime.gettime()



	###############################
	# section: Login and Context Management
	###############################


	# ian: todo: complex: Is this only to be used from DBProxy? Resolve this..
	def _login(self, username="anonymous", password="", host=None, maxidle=None, ctx=None, txn=None):
		"""(DBProxy Only) Logs a given user in to the database and returns a ctxid, which can then be used for
		subsequent access. Returns ctxid, or fails with AuthenticationError or SessionError

		@keyparam username
		@keyparam password
		@keyparam host
		@keyparam maxidle

		@return Context key (ctxid)

		@exception AuthenticationError, KeyError
		"""

		if maxidle == None or maxidle > g.MAXIDLE:
			maxidle = g.MAXIDLE

		newcontext = None
		username = unicode(username)


		# Anonymous access
		if username == "anonymous":
			newcontext = self.__makecontext(host=host, ctx=ctx, txn=txn)
		else:
			user = self.__login_getuser(username, ctx=ctx, txn=txn)

			if user.checkpassword(password):
				newcontext = self.__makecontext(username=username, host=host, ctx=ctx, txn=txn)
			else:
				g.log.msg('LOG_ERROR', "Invalid password: %s (%s)" % (username, host))
				raise subsystems.exceptions.AuthenticationError, subsystems.exceptions.AuthenticationError.__doc__

		try:
			self.__setcontext(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
			g.log.msg('LOG_INFO', "Login succeeded %s (%s)" % (username, newcontext.ctxid))
		except:
			g.log.msg('LOG_ERROR', "Error writing login context")
			raise


		return newcontext.ctxid



	# Logout is the same as delete context
	@DBProxy.publicmethod
	def logout(self, ctx=None, txn=None):
		"""Logout"""
		if ctx: self.deletecontext(ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def deletecontext(self, ctx=None, txn=None):
		"""Logout"""
		if ctx:	self.__setcontext(ctx.ctxid, None, ctx=ctx, txn=txn)



	# ian: should always have a valid context, even if anon...
	@DBProxy.publicmethod
	def checkcontext(self, ctx=None, txn=None):
		"""This allows a client to test the validity of a context, and get basic information on the authorized user and his/her permissions.
		@return (username, groups)"""
		return ctx.username, ctx.groups



	@DBProxy.publicmethod
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.
		@return Bool."""
		return ctx.checkadmin()



	@DBProxy.publicmethod
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.
		@return Bool"""
		return ctx.checkreadadmin()



	@DBProxy.publicmethod
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.
		@return Bool"""
		return ctx.checkcreate()



	def __makecontext(self, username="anonymous", host=None, ctx=None, txn=None):
		"""Initializes a context; Avoid instantiating Contexts directly.

		@keyparam username Username (default "anonymous")
		@keyparam host Host

		@return Context instance
		"""
		if username == "anonymous":
			ctx = dataobjects.context.AnonymousContext(host=host)
		else:
			ctx = dataobjects.context.Context(username=username, host=host)

		return ctx


	def __makerootcontext(self, ctx=None, host=None, txn=None):
		ctx = dataobjects.context.SpecialRootContext()
		ctx.refresh(db=self, txn=txn)
		ctx._setDBProxy(txn=txn)
		return ctx



	# ian: todo: simple: finish
	def __login_getuser(self, username, ctx=None, txn=None):
		"""(Internal) Check password against stored hash value.

		@param username Username
		@return User instance

		@exception AuthenticationError
		"""

		try:
			user = self.bdbs.users.sget(username, txn=txn)
			user.setContext(ctx=ctx)
		except:
			raise
			raise subsystems.exceptions.AuthenticationError, 'no such user' #subsystems.exceptions.AuthenticationError.__doc__
		return user



	def __setcontext(self, ctxid, context, ctx=None, txn=None):
		"""(Internal) Manipulate cached and stored contexts.

		@param ctxid ctxid key
		@param context Context instance

		@exception KeyError, DBError
		"""

		#@begin

		# any time you set the context, delete the cached context
		# this will retrieve it from disk next time it's needed
		if self.bdbs.contexts.get(ctxid):
			del self.bdbs.contexts[ctxid]

		# set context
		if context != None:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts_p.set: %r"%context.ctxid)
				self.bdbs.contexts_p.set(ctxid, context, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst))
				raise


		# delete context
		else:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts_p.__delitem__: %r"%ctxid)
				self.bdbs.contexts_p.set(ctxid, None, txn=txn) #del ... [ctxid]

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Unable to delete persistent context %s (%s)"%(ctxid, inst))
				raise

		#@end



	# ian: todo: hard: flesh this out into a proper cron system, with a subscription model; right now just runs cleanupcontexts
	def __periodic_operations(self, ctx=None, txn=None):
		"""(Internal) Maintenance task scheduler."""

		t = subsystems.dbtime.getctime()
		# maybe not the perfect place to do this, but it will have to do
		if t > (self.lastctxclean + 600):
			self.__cleanupcontexts(ctx=ctx, txn=txn)



	# ian: todo: hard: finish
	def __cleanupcontexts(self, ctx=None, txn=None):
		"""(Internal) This should be run periodically to clean up sessions that have been idle too long."""

		g.log.msg("LOG_DEBUG","Clean up expired contexts: time %s -> %s"%(self.lastctxclean, time.time()))
		self.lastctxclean = time.time()

		return

		for ctxid, context in self.bdbs.contexts_p.items():
			# use the cached time if available
			try:
				c = self.bdbs.contexts.sget(ctxid, txn=txn) #[ctxid]
				context.time = c.time
			# ed: fix: should check for more specific exception
			except:
				pass

			if context.time + (context.maxidle or 0) < time.time():
				g.debug("Expire context (%s) %d" % (context.ctxid, time.time() - context.time))
				self.__setcontext(context.ctxid, None, ctx=ctx, txn=txn)



	# ian: todo: hard:
	#		how often should we refresh groups?
	#		right now, every publicmethod will reset user/groups
	#		timer based?
	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Semi-internal) Takes a ctxid key and returns a context. Note that both key and host must match.
		@param ctxid ctxid
		@param host host

		@return Context

		@exception SessionError
		"""

		self.__periodic_operations(ctx=ctx, txn=txn)

		context = None
		if ctxid:
			# g.log.msg("LOG_DEBUG", "local context cache: %s, cache db: %s"%(self.bdbs.contexts.get(ctxid), self.bdbs.contexts_p.get(ctxid, txn=txn)))
			context = self.bdbs.contexts.get(ctxid) or self.bdbs.contexts_p.get(ctxid, txn=txn)
		else:
			context = self.__makecontext(host=host, ctx=ctx, txn=txn)

		if not context:
			g.log.msg('LOG_ERROR', "Session expired: %s"%ctxid)
			raise subsystems.exceptions.SessionError, "Session expired: %s"%(ctxid)

		user = None
		grouplevels = {}

		# Update and cache
		if context.username not in ["anonymous"]:
			user = self.bdbs.users.get(context.username, None, txn=txn)
			groups = self.bdbs.groupsbyuser.get(context.username, set(), txn=txn)
			grouplevels = {}
			for group in [self.bdbs.groups.get(i, txn=txn) for i in groups]:
				grouplevels[group.name] = group.getlevel(context.username)


		# g.log.msg("LOG_DEBUG","kw host is %s, context host is %s"%(host, context.host))
		context.refresh(user=user, grouplevels=grouplevels, host=host, db=self, txn=txn)

		self.bdbs.contexts[ctxid] = context

		return context





	###############################
	# section: binaries
	###############################



	@DBProxy.publicmethod
	def newbinary(self, *args, **kwargs):
		raise Exception, "Deprecated; use putbinary"



	@DBProxy.publicmethod
	def getbinary(self, bdokeys, byrecid=False, filt=True, vts=None, params=None, ctx=None, txn=None):
		"""Get a storage path for an existing binary object.

		@param bdokeys A single BDO, an iterable of BDOs, a single record/recid, or an iterable of records/recids
		@keyparam byrec Key result by recid
		@keyparam filt Filter out invalid BDOs
		@keyparam vts For record search, limit to (iterable) param vartypes
		@keyparam params For record search, limit to (iterable) params

		@return A single Binary instance, or a {bdokey:Binary} dict

		@exception KeyError, SecurityError
		"""

		# process bdokeys argument for bids (into list bids) and then process bids
		ret = {}
		bids = []
		recs = []

		if not vts:
			vts = ["binary","binaryimage"]

		ol=0
		if isinstance(bdokeys,basestring): # or not hasattr(bdokeys,"__iter__"):
			ol=1
			bids = [bdokeys]
			bdokeys = bids
		if isinstance(bdokeys,(int,dataobjects.record.Record)):
			bdokeys = [bdokeys]


		bids.extend(filter(lambda x:isinstance(x,basestring), bdokeys))

		recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), bdokeys), filt=1, ctx=ctx, txn=txn))
		recs.extend(filter(lambda x:isinstance(x,dataobjects.record.Record), bdokeys))

		if recs:
			bids.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))

		# filtered list of bdokeys
		bids = filter(lambda x:isinstance(x, basestring), bids)

		# keyed by recid
		byrec = collections.defaultdict(list)

		for bdokey in bids:

			try:
				dkey = emen2.Database.dataobjects.binary.parse(bdokey)
				bdo = self.bdbs.bdocounter.sget(dkey["datekey"], txn=txn)[dkey["counter"]]

			except Exception, inst:
				if filt: continue
				else: raise KeyError, "Invalid identifier: %s: %s"%(bdokey, inst)

			recid = bdo.get('recid')
			byrec[recid].append(bdo)

			try:
				self.getrecord(recid, filt=False, ctx=ctx, txn=txn)
				bdo["filepath"] = dkey["filepath"]
				ret[bdo["name"]] = bdo

			#ed: fix: is this the right exception?
			except emen2.Database.subsystems.exceptions.SecurityError:
				if filt: continue
				else: raise subsystems.exceptions.SecurityError, "Not authorized to access %s (%s)"%(bid, recid)

		if len(ret)==1 and ol:
			return ret.values()[0]

		return ret
		#return byrec if byrecid else ret



	# ian: todo: medium: clean this up some more...
	# ian: todo: simple: implement uri kw
	@DBProxy.publicmethod
	def putbinary(self, filename, recid, bdokey=None, filedata=None, filehandle=None, param=None, uri=None, ctx=None, txn=None):
		"""Add binary object to database and attach to record. May specify record param to use and file data to write to storage area. Admins may modify existing binaries.

		@param filename Filename
		@param recid Target record
		@keyparam param Target record parameter.
		@keyparam uri Source URI of BDO
		@keyparam filedata Write filedata to disk
		@keyparam filehandle ... or a file handle to copy from
		@keyparam bdokey Modify existing BDO (Admin only)

		@return BDO

		@exception SecurityError, ValueError
		"""

		# Filename and recid required, unless root
		if not filename: raise ValueError, "Filename required"

		if (bdokey or recid == None) and not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only admins may manipulate binary tree directly"

		# ian: todo: medium: acquire RMW lock on record? (will need to not use self.getrecord.. hmm.)
		# ed: probably, we could abstract a private method (or just add a new argument to the current
		#     one which allows extra bsddb flags to be specified)
		if not bdokey:
			rec = self.getrecord(recid, filt=False, ctx=ctx, txn=txn)
			if not rec.writable():
				raise subsystems.exceptions.SecurityError, "Write permission needed on referenced record."


		bdoo = self.__putbinary(filename, recid, bdokey=bdokey, uri=uri, ctx=ctx, txn=txn)

		# If this not an edit, update the record..
		if not bdokey:
			if not param: param = "file_binary"

			param = self.getparamdef(param, ctx=ctx, txn=txn)

			if param.vartype == "binary":
				v = rec.get(param.name) or []
				v.append(bdoo.get("name"))
				rec[param.name]=v

			elif param.vartype == "binaryimage":
				rec[param.name]=bdoo.get("name")

			else:
				raise ValueError, "Error: invalid vartype for binary: parameter %s, vartype is %s"%(param.name, param.vartype)

			self.putrecord(rec, ctx=ctx, txn=txn)


		self.__putbinary_file(bdokey=bdoo.get("name"), filedata=filedata, filehandle=filehandle, ctx=ctx, txn=txn)


		return bdoo



	# ian: todo: hard: use duplicate key style for bdocounter... delayed for now.
	# ian: todo: medium: if any exceptions, clean up partial files?
	def __putbinary(self, filename, recid, bdokey=None, uri=None, ctx=None, txn=None):
		"""(Internal) putbinary action

		@param filename filename
		@param recid recid
		@param bdokey bdokey
		@keyparam uri

		@return Binary instance
		"""
		# fetch BDO day dict, add item, and commit

		dkey = emen2.Database.dataobjects.binary.parse(bdokey)

		# bdo items are stored one bdo per day
		# key is sequential item #, value is (filename, recid)
		# uri is for files copied from an external source, similar to records, paramdefs, etc.

		#@begin

		# acquire RMW lock to prevent others from editing...
		bdo = self.bdbs.bdocounter.get(dkey["datekey"], txn=txn, flags=g.RMWFLAGS) or {}

		if dkey["counter"] == 0:
			counter = max(bdo.keys() or [-1]) + 1
			dkey = emen2.Database.dataobjects.binary.parse(bdokey, counter=counter)


		if bdo.get(dkey["counter"]) and not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only admin may overwrite existing BDO"

		nb = dataobjects.binary.Binary()
		nb.update(
			uri=uri,
			filename=filename,
			recid=recid,
			creator=ctx.username,
			creationtime=self.gettime(),
			name=dkey["name"]
		)

		bdo[dkey["counter"]] = nb

		g.log.msg("LOG_COMMIT","self.bdbs.bdocounter.set: %s"%dkey["datekey"])
		self.bdbs.bdocounter.set(dkey["datekey"], bdo, txn=txn)

		#@end

		return nb



	def __putbinary_file(self, bdokey, filedata=None, filehandle=None, ctx=None, txn=None):
		"""(Internal) Write file data
		@param bdokey BDO
		@keyparam filedata File data

		@exception SecurityError
		"""

		# Write file to binary storage area

		dkey = emen2.Database.dataobjects.binary.parse(bdokey)

		#ed: fix: catch correct exception
		try:
			os.makedirs(dkey["basepath"])
		except:
			pass

		if os.access(dkey["filepath"], os.F_OK) and not ctx.checkadmin():
			# should be a different exception class, this particular one seems irrevelant as it is not really a security
			# but an integrity problem.
			raise subsystems.exceptions.SecurityError, "Error: Attempt to overwrite existing file: %s"%dkey["filepath"]


		with open(dkey["filepath"],"wb") as f:
			if filehandle == None:
				f.write(filedata)
			else:
				for line in filehandle:
					f.write(line)

 		g.log.msg('LOG_INFO', "Wrote %s bytes disk: %s"%(os.stat(dkey["filepath"]).st_size,dkey["filepath"]))


	# ian: todo: medium: reimplement properly, return actual BDO names instead of just counter.. [bdo:2010010100001, bdo:2010010100002, ...]
	# 			 ... and maybe key by recid
	# @DBProxy.publicmethod
	# def getbinarynames(self, ctx=None, txn=None):
	# 	"""Returns a list of tuples which can produce all binary object
	# 	keys in the database. Each 2-tuple has the date key and the nubmer
	# 	of objects under that key. A somewhat slow operation."""
	#
	# 	if ctx.username == None:
	# 		raise subsystems.exceptions.SecurityError, "getbinarynames not available to anonymous users"
	#
	# 	ret = self.bdbs.bdocounter.keys(txn=txn)
	# 	ret = [(i, len(self.bdbs.bdocounter.get(i, txn=txn))) for i in ret]
	# 	return ret





	###############################
	# section: query
	###############################



	@DBProxy.publicmethod
	def query(self, q=None, rectype=None, boolmode="AND", ignorecase=True, constraints=None, childof=None, parentof=None, recurse=False, subset=None, recs=None, returnrecs=False, byvalue=False, ctx=None, txn=None):
		"""Query. Specify one or more keyword arguments:

		@keyparam q					quick, full text query
		@keyparam rectype				limit records to rectype
		@keyparam boolmode			join operation for each search operation
		@keyparam ignorecase			case insensitive search
		@keyparam childof/parentof	limit results to branches
		@keyparam subset				limit to specified subset
		@keyparam returnrecs			return record instances instead of recids
		@keyparam byvalue				invert results; {value:[recids]}

		@keyparam constrants			Constraint format:
								[[param, comparator, value], ...]
							Comparators:
								==, !=, contains, !contains, <, >, <=, >=
								contains_w_empty (like contains, but also returns Nones)
								!None (any value)

		@return Set of recids or list of Record instances

		@exception SecurityError
		"""

		if boolmode == "AND":
			boolmode = set.intersection
		elif boolmode == "OR":
			boolmode = set.union
		else:
			raise Exception, "Invalid boolean mode: %s. Must be AND, OR"%boolmode

		if recurse:
			recurse = g.MAXRECURSE

		constraints = constraints or []
		if q:
			constraints.append(["*","contains_w_empty",unicode(q)])

		subsets = []
		if subset:
			subsets.append(set(subset))
		if childof:
			subsets.append(self.getchildren(childof, recurse=recurse, filt=False, flat=True, ctx=ctx, txn=txn))
		if parentof:
			subsets.append(self.getparents(parentof, recurse=recurse, filt=False, flat=True, ctx=ctx, txn=txn))
		if rectype:
			subsets.append(self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn))


		# makes life simpler...
		if not constraints:
			ret = reduce(boolmode, subsets)

			if returnrecs:
				return self.getrecord(ret, filt=True, ctx=ctx, txn=txn)

			return self.filterbypermissions(ret, ctx=ctx, txn=txn)


		# y is argument, x is record value
		cmps = {
			"==": lambda y,x:x == y,
			"!=": lambda y,x:x != y,
			"contains": lambda y,x:unicode(y) in unicode(x),
			"!contains": lambda y,x:unicode(y) not in unicode(x),
			">": lambda y,x: x > y,
			"<": lambda y,x: x < y,
			">=": lambda y,x: x >= y,
			"<=": lambda y,x: x <= y,
			'contains_w_empty': lambda y,x:unicode(y or '') in unicode(x),
			'!None': lambda y,x: x != None
			#"range": lambda x,y,z: y < x < z
		}

		if ignorecase:
			cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			cmps["!contains"] = lambda y,x:unicode(y).lower() not in unicode(x).lower()
			cmps['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

		# wildcard param searching only useful with the following comparators...
		globalsearchcmps = ["==","!=","contains","!contains"]


		# since we pass the DBProxy to validators, set it's txn
		if not ctx.db._gettxn():
			ctx.db._settxn(txn)

		#g.log.msg('LOG_DEBUG', "Query constraints:")
		#g.log.msg('LOG_DEBUG', constraints)

		if subset:
			s, subsets_by_value = self.__query_recs(constraints, cmps=cmps, subset=subset, ctx=ctx, txn=txn)
		else:
			s, subsets_by_value = self.__query_index(constraints, cmps=cmps, subset=subset, ctx=ctx, txn=txn)

		subsets.extend(s)

		ret = reduce(boolmode, subsets)


		#g.log.msg('LOG_DEBUG', "stage 3 results")
		#g.log.msg('LOG_DEBUG', ret)

		# ian: i'd prefer not to make a copy, but filtering dicts by value isn't awesome
		if byvalue:
			self.filterbypermissions(ret, ctx=ctx, txn=txn)
			retdict = {}
			for k,v in subsets_by_value.items():
				f = v & ret
				if f: retdict[k] = f
			return retdict


		if returnrecs:
			return self.getrecord(ret, filt=True, ctx=ctx, txn=txn)

		return self.filterbypermissions(ret, ctx=ctx, txn=txn)




	def __query_index(self, constraints, cmps=None, subset=None, ctx=None, txn=None):
		"""(Internal) index-based search. See DB.query()"""

		vtm = subsystems.datatypes.VartypeManager()
		subsets = []
		subsets_by_value = {}

		# nested dictionary, results[constraint position][param]
		results = collections.defaultdict(partial(collections.defaultdict, set))

		# stage 1: search __indexkeys
		for count,c in enumerate(constraints):
			if c[0] == "*":

				# ian: todo: hard: improve speed of FieldBTree.items
				for param, pkeys in self.bdbs.indexkeys.items(txn=txn):
					pd = self.bdbs.paramdefs.get(param, txn=txn) #datatype=self.__cache_vartype_indextype.get(pd.vartype),
					# validate for each param for correct vartype matching
					try:
						cargs = vtm.validate(pd, c[2], db=ctx.db)
					except (ValueError, KeyError):
						continue

					comp = partial(cmps[c[1]], cargs) #*cargs
					results[count][param] = set(filter(comp, pkeys)) or None

			else:
				param = c[0]
				pd = self.bdbs.paramdefs.get(param, txn=txn)
				pkeys = self.bdbs.indexkeys.get(param, txn=txn) #datatype=self.__cache_vartype_indextype.get(pd.vartype),
				cargs = vtm.validate(pd, c[2], db=ctx.db)
				comp = partial(cmps[c[1]], cargs) #*cargs
				results[count][param] = set(filter(comp, pkeys)) or None


		# g.log.msg('LOG_DEBUG', "stage 1 results")
		# g.log.msg('LOG_DEBUG', results)

		# stage 2: search individual param indexes
		for count, r in results.items():
			constraint_matches = set()

			for param, matchkeys in filter(lambda x:x[0] and x[1] != None, r.items()):
				ind = self.__getparamindex(param, ctx=ctx, txn=txn)
				for matchkey in matchkeys:
					m = ind.get(matchkey, txn=txn)
					if m:
						subsets_by_value[(param, matchkey)] = m
						constraint_matches |= m

			subsets.append(constraint_matches)

		# g.log.msg('LOG_DEBUG', "stage 2 results")
		# g.log.msg('LOG_DEBUG', subsets)
		# g.log.msg('LOG_DEBUG', subsets_by_value)

		return subsets, subsets_by_value



	def __query_recs(self, constraints, cmps=None, subset=None, ctx=None, txn=None):
		"""(Internal) record-based search. See DB.query()"""

		vtm = subsystems.datatypes.VartypeManager()
		subsets = []
		subsets_by_value = {}
		recs = self.getrecord(subset, filt=True, ctx=ctx, txn=txn)

		#allp = "*" in [c[0] for c in constraints]

		# this is ugly :(
		for count, c in enumerate(constraints):
			cresult = []

			if c[0] == "*":
				# cache
				allparams = set(reduce(operator.concat, [rec.getparamkeys() for rec in recs], []))
				for param in allparams:
					try:
						cargs = vtm.validate(self.bdbs.paramdefs.get(param, txn=txn), c[2], db=ctx.db)
					except (ValueError, KeyError):
						continue

					cc = cmps[c[1]]
					m = set([x.recid for x in filter(lambda rec:cc(cargs, rec.get(param)), recs)])
					if m:
						subsets_by_value[(param, cargs)] = m
						cresult.extend(m)

			else:
				param = c[0]
				cc = cmps[c[1]]
				cargs = vtm.validate(self.bdbs.paramdefs.get(param, txn=txn), c[2], db=ctx.db)
				m = set([x.recid for x in filter(lambda rec:cc(cargs, rec.get(param)), recs)])
				if m:
					subsets_by_value[(param, cargs)] = m
					cresult.extend(m)


			if cresult:
				subsets.append(cresult)

		#g.log(subsets)
		return subsets, subsets_by_value



	# ian: todo: hard: Plotting goes.. HERE. Working on it.
	@DBProxy.publicmethod
	def plot(self, ctx=None, txn=None):
		pass



	# class findrecorddef(View):
	# 	__metaclass__ = View.register_view
	# 	__matcher__ = r'^/find/recorddef/$'
	# 	def __init__(self,db=None,q=None,limit=None,timestamp=None):
	# 		self.q=q
	# 		View.__init__(self,db=db, js_files=emen2.TwistSupport_html.html.JSLibraries.admin.AdminJS)
	#
	# 	def get_data(self):
	# 		pass
	#
	#
	#
	#
	# class findparamdef(View):
	# 	__metaclass__ = View.register_view
	# 	__matcher__ = r'^/find/paramdef/$'
	# 	def __init__(self,db=None,q=None,limit=None,timestamp=None):
	# 		self.q=q
	# 		View.__init__(self,db=db, js_files=emen2.TwistSupport_html.html.JSLibraries.admin.AdminJS)
	#
	# 	def get_data(self):
	# 		pdn = self.db.getparamdefnames()
	# 		pds = self.db.getparamdefs(pdn)
	# 		ret = []
	# 		# search: desc_long, desc_short, name
	# 		# ian: todo: simple: search vartype, property, creator, etc. using opt args
	# 		search_keys = ["name","desc_long","desc_short"]
	#
	# 		for k, pd in pds.items():
	# 			if any([self.q in pd.get(search_key,"") for search_key in search_keys]):
	# 				ret.append("%s -- %s (%s)"%(pd.name, pd.desc_short, pd.vartype))
	#
	# 		return "\n".join(sorted(ret))
	#
	#
	#
	#
	#
	#
	#
	# class finduser(View):
	# 	__metaclass__ = View.register_view
	# 	__matcher__ = r'^/find/user/$'
	# 	def __init__(self, db=None, q=None, limit=None, timestamp=None):
	# 		self.q = q
	# 		View.__init__(self,db=db, js_files=emen2.TwistSupport_html.html.JSLibraries.admin.AdminJS)
	#
	# 	def get_data(self):
	#
	# 		#if len(self.q) <= 1: return demjson.encode([])
	#
	# 		q = self.db.query(
	# 			boolmode="OR",
	# 			ignorecase=True,
	# 			#rectype="person",
	# 			constraints=[
	# 				["name_first","contains",self.q],
	# 				["name_middle","contains",self.q],
	# 				["name_last","contains",self.q],
	# 				["username","contains_w_empty",self.q]
	# 				],
	# 			returnrecs=True
	# 			)
	#
	# 		#print q
	#
	# 		usernames = filter(None, map(lambda x:x.get("username"),filter(lambda x:x.rectype=="person", q)))
	# 		return "\n".join(sorted(usernames))
	#
	# 		#ret = self.db.getuserdisplayname(usernames, lnf=1) or {}
	# 		#return demjson.encode(ret.items())
	# 		# z = self.db.fulltextsearch(self.q,rectype="person",includeparams=["username"],params=["name_first","name_middle","name_last","username"])
	# 		# ret=self.db.getuserdisplayname([i.get("username") for i in z.values()],lnf=1)
	# 		#
	# 		# if ret: ret=ret.items()
	# 		# else: ret=[]
	# 		# return demjson.encode(ret)


	@DBProxy.publicmethod
	def finduser(self, query, limit=100, ctx=None, txn=None):
		q = self.query(
			boolmode="OR",
			ignorecase=True,
			constraints=[
				["name_first","contains",query],
				["name_middle","contains",query],
				["name_last","contains",query],
				["username","contains_w_empty",query]
				],
			returnrecs=True,
			ctx=ctx, txn=txn
		)

		usernames = filter(None, map(lambda x:x.get("username"),filter(lambda x:x.rectype=="person", q)))

		users = self.getuser(usernames, ctx=ctx, txn=txn)
		return [(user.username, user.displayname) for user in users.values()]


	# ian: make this a class method, e.g. Group.match or query?
	@DBProxy.publicmethod
	def findgroup(self, query, limit=100, ctx=None, txn=None):
		built_in = set(["anon","authenticated","create","readadmin","admin"])

		groups = self.getgroup(self.getgroupnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		search_keys = ["name", "displayname"]
		ret = []

		for k, v in groups.items():
			if any([query in v.get(search_key,"") for search_key in search_keys]):
				ret.append([k,v.get('displayname', k)])

		ret = sorted(ret, key=operator.itemgetter(1))

		if limit:
			ret = ret[:limit]

		return ret




	@DBProxy.publicmethod
	def findvalue(self, param, query, flat=False, limit=100, count=True, showchoices=True, ctx=None, txn=None):
		"""Convenience method for quick query for a single param. Sorted by number of matches.

		@param count Return count of matches, otherwise return recids
		@param limit Limit number of results
		@param showchoices ...
		@param flat Flatten return to just recids

		@return [[matching value, count], ...]
				if not count: [[matching value, [recid, ...]], ...]
				if flat and not count: [recid, recid, ...]
				if flat and count: Number of matching records
		"""


		q = self.query(ignorecase=True, constraints=[[param, "contains_w_empty", query]], byvalue=True, ctx=ctx, txn=txn)
		# >>> db.query(ignorecase=True, constraints=[["name_last","contains_w_empty", "rees"]], byvalue=True)
		# 			{('name_last', u'Rees'): set([271390])}

		q_sort = {}
		for i in q:
			q_sort[i[1]] = len(q[i])
		q_sort = sorted(q_sort.items(), key=operator.itemgetter(1), reverse=True)

		if flat and count:
			return sum([i[1] for i in q_sort])

		if flat:
			return reduce(set.union, q.values())

		if limit:
			q_sort = q_sort[:limit]

		if count:
			return q_sort

		return [(i, q[i]) for i in q_sort]




	#########################
	# section: Index Management
	#########################


	# ian: todo: medium: Enforce filt=True in config?
	@DBProxy.publicmethod
	def getindexbyrecorddef(self, recdef, filt=False, ctx=None, txn=None):
		"""Records by Record Def. This is currently non-secured information.

		@param recdef A single or iterable Record Def name
		@keyparam filt Filter by permissions

		@return
		"""
		# """Uses the recdefname keyed index to return all
		# records belonging to a particular RecordDef as a set. Currently this
		# is unsecured, but actual records cannot be retrieved, so it
		# shouldn't pose a security threat."""

		if not hasattr(recdef, "__iter__"):
			recdef = [recdef]

		ret = set()
		for i in recdef:
			ret |= self.bdbs.recorddefindex.get(i, txn=txn)

		if filt:
			return self.filterbypermissions(ret, ctx=ctx, txn=txn)

		return ret




	# ian todo: medium: add unit support.
	@DBProxy.publicmethod
	def getindexbyvalue(self, param, valrange=None, ctx=None, txn=None):
		"""Query an indexed parameter. Return all records that contain a value, with optional value range
		@param param parameter name
		@keyparam valrange tuple of (min, max) values to search
		"""

		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
		if paramindex == None:
			return None

		if valrange == None:
			ret = paramindex.values(txn=txn)

		else:
			if hasattr(valrange, '__iter__'):
				ret = set(paramindex.values(valrange[0], valrange[1], txn=txn))
			else:
				ret = paramindex.values(valrange, txn=txn)

		if ctx.checkreadadmin():
			return ret

		return self.filterbypermissions(ret, ctx=ctx, txn=txn) #ret & secure # intersection of the two search results




	@DBProxy.publicmethod
	def getindexdictbyvalue(self, param, valrange=None, subset=None, ctx=None, txn=None):
		"""Query an indexed parameter.

		@param param parameter name
		@keyparam valrange tuple of (min, max) values to search
		@keyparam subset restrict to record subset

		@return Return dict with param values as keys, matching recids as values.
		"""

		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
		if paramindex == None:
			return {}

		r = dict(paramindex.items(txn=txn))

		# ian: todo: medium/hard: reimplement key range with cursor.. solve slowness of comparison function.
		#else:
		#	r = dict(paramindex.items(valrange[0], valrange[1], txn=txn))
		#else:
		#	r = {valrange:ind[valrange]}

		# This takes the returned dictionary of value/list of recids
		# and makes a dictionary of recid/value pairs

		ret = {}
		reverse = {}

		# flip key/value of r into reverse
		for i,j in r.items():
			for k in j:
				reverse[k] = i

		if subset:
			for i in subset:
				ret[i] = reverse.get(i)
		else:
			ret = reverse

		if ctx.checkreadadmin():
			return ret

		secure = self.filterbypermissions(ret.keys(), ctx=ctx, txn=txn)

		# remove any recids the user cannot access
		for i in set(ret.keys()) - secure:
			del ret[i]

		return ret



	# ian: todo: simple: is this currently used anywhere? It was more or less replaced by filterpermissions. But may be useful to keep.
	@DBProxy.publicmethod
	def getindexbycontext(self, ctx=None, txn=None):
		"""Return all readable recids
		@return All readable recids"""

		if ctx.checkreadadmin():
			return set(range(self.bdbs.records.sget(-1, txn=txn))) #+1)) # Ed: Fixed an off by one error

		ret = set(self.bdbs.secrindex.get(ctx.username, set(), txn=txn)) #[ctx.username]

		for group in sorted(ctx.groups,reverse=True):
			ret |= set(self.bdbs.secrindex_groups.get(group, set(), txn=txn))#[group]

		return ret



	# ian: todo: low priority: finish; add more stats (->Ed)
	@DBProxy.publicmethod
	def getparamstatistics(self, param, ctx=None, txn=None):
		"""Return statistics about an (indexable) param
		@param param parameter

		@return (Count of keys, count of values)
		"""

		if ctx.username == None:
			raise subsystems.exceptions.SecurityError, "Not authorized to retrieve parameter statistics"

		try:
			paramindex = self.__getparamindex(param, create=0, ctx=ctx, txn=txn)
			return (len(paramindex.keys(txn=txn)), len(paramindex.values(txn=txn)))
		except:
			return (0,0)



	# ian: todo: simple: expose as offline admin method
	# ian: todo: hard: ... and make offline maintenance mechanism
	#@DBProxy.adminmethod
	def __rebuild_indexkeys(self, ctx=None, txn=None):
		"""(Internal) Rebuild index-of-indexes"""

		inds = dict(filter(lambda x:x[1]!=None, [(i,self.__getparamindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

		g.log.msg("LOG_COMMIT_INDEX","self.bdbs.indexkeys.truncate")
		self.bdbs.indexkeys.truncate(txn=txn)

		for k,v in inds.items():
			g.log.msg("LOG_COMMIT_INDEX", "self.bdbs.indexkeys: rebuilding params %s"%k)
			pd = self.bdbs.paramdefs.get(k, txn=txn)
			self.bdbs.indexkeys.addrefs(k, v.keys(), txn=txn) #datatype=self.__cache_vartype_indextype.get(pd.vartype),



	# @DBProxy.publicmethod
	# def getindexbyuser(self, username, ctx=None, txn=None):
	# 	"""This will use the user keyed record read-access index to return
	# 	a list of records the user can access. DOES NOT include that user's groups.
	# 	Use getindexbycontext if you want to see all recs you can read."""
	#
	# 	if username == None:
	# 		username = ctx.username
	#
	# 	if ctx.username != username and not ctx.checkreadadmin():
	# 		raise subsystems.exceptions.SecurityError, "Not authorized to get record access for %s" % username
	#
	# 	return self.bdbs.secrindex.get(username, set(), txn=txn)



	# @DBProxy.adminmethod
	# ian: disabled for security reasons (it returns all values with no security check...)
	# def getindexkeys(self, paramname, valrange=None, ctx=None, txn=None):
	# 	 """For numerical & simple string parameters, this will locate all
	# 	 parameter values in the specified range.
	# 	 valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""
	# 	 ind=self.__getparamindex(paramname,create=0)
	#
	# 	 if valrange==None : return ind.keys()
	# 	 elif isinstance(valrange,tuple) or isinstance(valrange,list) : return ind.keys(valrange[0],valrange[1])
	# 	 elif ind.has_key(valrange): return valrange
	# 	 return None


	# # ian: todo: return dictionary instead of list?
	# @DBProxy.publicmethod
	# def getrecordschangetime(self, recids, ctx=None, txn=None):
	# 	"""Returns a list of times for a list of recids. Times represent the last modification
	# 	of the specified records"""
	# 	raise Exception, "Temporarily deprecated"
	# 	recids = self.filterbypermissions(recids, ctx=ctx, txn=txn)
	#
	# 	if len(rid) > 0:
	# 		raise Exception, "Cannot access records %s" % unicode(rid)
	#
	# 	try:
	# 		ret = [self.__timeindex.sget(i, txn=txn) for i in recids]
	# 	except:
	# 		raise Exception, "unindexed time on one or more recids"
	#
	# 	return ret


	# @DBProxy.publicmethod
	# def searchindexkeys(self, q=None, ignorecase=1, params=None, ctx=None, txn=None):
	# 	"""Deprecated; use query"""
	# 	if not q:
	# 		return {}
	#
	# 	q = unicode(q)
	# 	if ignorecase:
	# 		q = q.lower()
	# 		matcher = lambda x:q in unicode(x).lower()
	# 	else:
	# 		matcher = lambda x:q in unicode(x)
	#
	# 	matches = {}
	#
	#
	# 	for k,v in self.bdbs.indexkeys.items(txn=txn):
	# 		r = filter(matcher, v)
	# 		if r: matches[k] = r
	#
	# 	matches2 = []
	#
	# 	for k,v in matches.items():
	# 		paramindex = self.__getparamindex(k, ctx=ctx, txn=txn)
	# 		for i in v:
	# 			j = paramindex.get(i, txn=txn)
	# 			for x in j:
	# 				matches2.append((x, k, i))


	# @DBProxy.publicmethod
	# def getparamvalue(self, paramname, recid):
	# 	paramname = str(paramname).lower()
	# 	paramindex = self.__getparamindex(paramname)
	#
	# 	if hasattr(recid, '__iter__'):
	# 		results = []
	# 		for key in paramindex.keys():
	# 			if set(paramindex[key]) & set(recid):
	# 				results.insert(0, key)
	# 		return results
	#
	# 	else:
	# 		for key in paramindex.keys():
	# 			if paramindex[key].pop() == recid:
	# 				return key





	#########################
	# section: Record Grouping Mechanisms
	#########################



	# ian: todo: medium: benchmark for new index system(01/10/2010)
	@DBProxy.publicmethod
	def groupbyrecorddef(self, recids, ctx=None, txn=None):
		"""This will take a set/list of record ids and return a dictionary of ids keyed
		by their recorddef"""

		optimize = True

		if not hasattr(recids,"__iter__"):
			recids=[recids]

		if len(recids) == 0:
			return {}

		if (optimize and len(recids) < 1000) or (isinstance(list(recids)[0],dataobjects.record.Record)):
			return self.__groupbyrecorddeffast(recids, ctx=ctx, txn=txn)

		# also converts to set..
		recids = self.filterbypermissions(recids, ctx=ctx, txn=txn)

		ret = {}
		while recids:
			rid = recids.pop()	# get a random record id

			try:
				r = self.getrecord(rid, ctx=ctx, txn=txn)	# get the record
			except:
				continue # if we can't, just skip it, pop already removed it

			ind = self.getindexbyrecorddef(r.rectype, ctx=ctx, txn=txn) # get the set of all records with this recorddef
			ret[r.rectype] = recids & ind # intersect our list with this recdef
			recids -= ret[r.rectype] # remove the results from our list since we have now classified them
			ret[r.rectype].add(rid) # add back the initial record to the set

		return ret



	# this one gets records directly
	def __groupbyrecorddeffast(self, records, ctx=None, txn=None):

		if not isinstance(list(records)[0],dataobjects.record.Record):
			records = self.getrecord(records, filt=1, ctx=ctx, txn=txn)

		ret={}
		for i in records:
			if not ret.has_key(i.rectype): ret[i.rectype]=set([i.recid])
			else: ret[i.rectype].add(i.recid)

		return ret



	# ian: todo: simple: is this unused? Decide if it's useful.
	# @DBProxy.publicmethod
	# def groupbyparentoftype(self, records, parenttype, recurse=3, ctx=None, txn=None):
	# 	"""This will group a list of record numbers based on the recordid of any parents of
	# 	type 'parenttype'. within the specified recursion depth. If records have multiple parents
	# 	of a particular type, they may be multiply classified. Note that due to large numbers of
	# 	recursive calls, this function may be quite slow in some cases. There may also be a
	# 	None category if the record has no appropriate parents. The default recursion level is 3."""
	#
	# 	r = {}
	# 	for i in records:
	# 		try:
	# 			p = self.getparents(i, recurse=recurse, ctx=ctx, txn=txn)
	# 		except:
	# 			continue
	# 		try:
	# 			k = [ii for ii in p if self.getrecord(ii, ctx=ctx, txn=txn).rectype == parenttype]
	# 		except:
	# 			k = [None]
	# 		if len(k) == 0:
	# 			k = [None]
	#
	# 		for j in k:
	# 			if r.has_key(j):
	# 				r[j].append(i)
	# 			else:
	# 				r[j] = [i]
	#
	# 	return r



	###############################
	# section: relationships
	###############################


	# ian: todo: low priority: instead of variable return format, make separate methods...
	@DBProxy.publicmethod
	def getchildren(self, key, keytype="record", recurse=1, rectype=None, filt=False, flat=False, tree=False, ctx=None, txn=None):
		"""Get child relationships. There are a number of convenience keyword arguments for speed/utility. Note flat/tree will affect return format.

		@param key Single or iterable key.
		@keyparam keytype ["record","paramdef","recorddef"]
		@keyparam rel ["children","parents"]
		@keyparam recurse Recursion level
		@keyparam tree Return full tree
		@keyparam flat Return flattened tree

		@keyparam rectype For Records, limit to a specific rectype
		@keyparam filt For Records, filter by permissions

		@return Default is to return a set of children for key.
				If tree, return dict-based graph. Useful with recursion.
				If key is iterable, return dict of dicts/sets as specified by tree
				If flat, return completely flattened set of all keys. Mutually exclusive with tree.
		"""
		return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", filt=filt, flat=flat, tree=tree, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def getparents(self, key, keytype="record", recurse=1, rectype=None, filt=False, flat=False, tree=False, ctx=None, txn=None):
		"""@see getchildren"""
		return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", filt=filt, flat=flat, tree=tree, ctx=ctx, txn=txn)



	# ian: todo: simple: raise Exception if rectype/filt on keytype=record
	def __getrel_wrapper(self, key, keytype="record", recurse=1, rectype=None, rel="children", filt=False, tree=False, flat=False, ctx=None, txn=None):
		"""(Internal) See getchildren/getparents."""
		ol = False
		if not hasattr(key,"__iter__"):
			ol = True
			key = [key]

		if recurse == False: recurse = True

		__keytypemap = dict(
			record=self.bdbs.records,
			paramdef=self.bdbs.paramdefs,
			recorddef=self.bdbs.recorddefs)

		if keytype in __keytypemap:
			reldb = __keytypemap[keytype]
		else:
			raise ValueError, "Invalid keytype"

		# result is a two-level dictionary
		# k1 = input recids
		# k2 = related recid and v2 = relations of k2
		result, ret_visited = {}, {}
		for i in key:
			result[i], ret_visited[i] = getattr(reldb, rel)(i, recurse=recurse, txn=txn)


		if rectype or filt or flat:
			# flatten, then filter by rectype and permissions.
			# if flat=True, then done, else filter the trees
			# ian: note: use a set() initializer for reduce to prevent exceptions when values is empty
			allr = reduce(set.union, ret_visited.values(), set())

			if rectype:
				allr &= self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn)

			if filt and keytype=="record":
				allr &= self.filterbypermissions(allr, ctx=ctx, txn=txn)

			if flat: result = allr
			else:
				# perform filtering on both levels, and removing any items that become empty
				# ret = dict( ( k, dict( (k2,v2 & allr) for k2, v2 in v.items() if bool(v2) is True ) )
				#					for k,v in ret.items() if bool(v) is True )
				# ^^^ this is neat but too hard to maintain.. syntax expanded a bit below
				# ^^^ ed: I rewrote it, is it any better?

				# if tree, we use ret_tree,
				if tree:
					for k, v in result.iteritems():
						for k2 in v:
							result[k][k2] &= allr

				# else, ret_visited
				else:
					for k in ret_visited:
						ret_visited[k] &= allr

		if not flat:
			if not tree:
				result = ret_visited

			if ol:
				result = result.get(key[0],set())

		return result



	@DBProxy.publicmethod
	def pclinks(self, links, keytype="record", ctx=None, txn=None):
		return self.__link("pclink", links, keytype=keytype, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def pcunlinks(self, links, keytype="record", ctx=None, txn=None):
		return self.__link("pcunlink", links, keytype=keytype, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def pclink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Establish a parent-child relationship between two keys.
		A context is required for record links, and the user must
		have write permission on at least one of the two."""
		return self.__link("pclink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def pcunlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Remove a parent-child relationship between two keys. Returns none if link doesn't exist."""
		return self.__link("pcunlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	def __link(self, mode, links, keytype="record", ctx=None, txn=None):

		if keytype not in ["record", "recorddef", "paramdef"]:
			raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

		if mode not in ["pclinks", "pclink","pcunlink","link","unlink"]:
			raise Exception, "Invalid relationship mode %s"%mode

		if not ctx.checkcreate():
			raise subsystems.exceptions.SecurityError, "linking mode %s requires record creation priveleges"%mode

		if filter(lambda x:x[0] == x[1], links):
			#g.log.msg("LOG_ERROR","Cannot link to self: keytype %s, key %s <-> %s"%(keytype, pkey, ckey))
			return

		if not links:
			return

		items = set(reduce(operator.concat, links, ()))

		# ian: circular reference detection.
		#if mode=="pclink":
		#	p = self.__getrel(key=pkey, keytype=keytype, recurse=self.MAXRECURSE, rel="parents")[0]
		#	c = self.__getrel(key=pkey, keytype=keytype, recurse=self.MAXRECURSE, rel="children")[0]
		#	if pkey in c or ckey in p or pkey == ckey:
		#		raise Exception, "Circular references are not allowed: parent %s, child %s"%(pkey,ckey)

		if keytype == "record":
			recs = dict([ (x.recid,x) for x in self.getrecord(items, ctx=ctx, txn=txn) ])
			for a,b in links:
				if not (recs[a].writable() or recs[b].writable()):
					raise subsystems.exceptions.SecurityError, "pclink requires partial write permission: %s <-> %s"%(a,b)

		else:
			links = [(unicode(x[0]).lower(),unicode(x[1]).lower()) for x in links]

		r = self.__commit_link(keytype, mode, links, ctx=ctx, txn=txn)
		return r



	#@write #self.bdbs.recorddefs, self.bdbs.records, self.bdbs.paramdefs
	def __commit_link(self, keytype, mode, links, ctx=None, txn=None):
		"""controls access to record/paramdef/recorddef relationships"""

		if mode not in ["pclink","pcunlink","link","unlink"]:
			raise Exception, "Invalid relationship mode"
		if keytype == "record":
			index = self.bdbs.records
		elif keytype == "recorddef":
			index = self.bdbs.recorddefs
		elif keytype == "paramdef":
			index = self.bdbs.paramdefs
		else:
			raise Exception, "Invalid keytype %s"%keytype

		linker = getattr(index, mode)

		#@begin

		if mode == "pclinks":
			linker(links, txn=txn)
		else:
			for pkey,ckey in links:
				g.log.msg("LOG_COMMIT","link: keytype %s, mode %s, pkey %s, ckey %s"%(keytype, mode, pkey, ckey))
				linker(pkey, ckey, txn=txn)

		#@end



	# ian: todo: low priority/hard: reimplement cousin relationships

	# @DBProxy.publicmethod
	# def getcousins(self, key, keytype="record", ctx=None, txn=None):
	# 	"""This will get the keys of the cousins of the referenced object
	# 	keytype is 'record', 'recorddef', or 'paramdef'"""
	#
	# 	if keytype == "record" :
	# 		#if not self.trygetrecord(key) : return set()
	# 		try:
	# 			self.getrecord(key, ctx=ctx, txn=txn)
	# 		except:
	# 			return set
	# 		return set(self.bdbs.records.cousins(key, txn=txn))
	#
	# 	if keytype == "recorddef":
	# 		return set(self.bdbs.recorddefs.cousins(key, txn=txn))
	#
	# 	if keytype == "paramdef":
	# 		return set(self.bdbs.paramdefs.cousins(key, txn=txn))
	#
	# 	raise Exception, "getcousins keytype must be 'record', 'recorddef' or 'paramdef'"



	# @DBProxy.publicmethod
	# def link(self, pkey, ckey, keytype="record", ctx=None, txn=None):
	# 	return self.__link("link", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	# @DBProxy.publicmethod
	# def unlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
	# 	return self.__link("unlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)


	# # ian: unused?
	# @DBProxy.publicmethod
	# def countchildren(self, key, recurse=1, ctx=None, txn=None):
	# 	"""Unlike getchildren, this works only for 'records'. Returns a count of children
	# 	of the specified record classified by recorddef as a dictionary. The special 'all'
	# 	key contains the sum of all different recorddefs"""
	#
	# 	c = self.getchildren(key, "record", recurse=recurse, ctx=ctx, txn=txn)
	# 	r = self.groupbyrecorddef(c, ctx=ctx, txn=txn)
	# 	for k in r.keys(): r[k] = len(r[k])
	# 	r["all"] = len(c)
	# 	return r



	###############################
	# section: Admin User Management
	###############################



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def disableuser(self, username, ctx=None, txn=None):
		"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
		a complete historical record is maintained. Only an administrator can do this."""
		return self.__setuserstate(username, True, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def enableuser(self, username, ctx=None, txn=None):
		return self.__setuserstate(username, False, ctx=ctx, txn=txn)



	def __setuserstate(self, username, state, ctx=None, txn=None):
		"""Set user enabled/disabled. 0 is enabled. 1 is disabled."""

		state = bool(state)

		if not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators can disable users"

		ol = False
		if not hasattr(username, "__iter__"):
			ol = True
			usernames = [username]

		commitusers = []
		for username in usernames:
			if username == ctx.username:
				g.warn('Warning: user %s tried to disable themself' % ctx.username)
				continue
				# raise subsystems.exceptions.SecurityError, "Even administrators cannot disable themselves"
			user = self.bdbs.users.sget(username, txn=txn) #[i]
			if user.disabled == state:
				continue

			user.disabled = bool(state)
			commitusers.append(user)


		ret = self.__commit_users(commitusers, ctx=ctx, txn=txn)
		g.log.msg('LOG_INFO', "Users %s disabled by %s"%([user.username for user in ret], ctx.username))

		if len(ret)==1 and ol: return ret[0].username
		return [user.username for user in ret]



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	@emen2.util.utils.return_list_or_single('usernames')
	def approveuser(self, usernames, secret=None, ctx=None, txn=None):
		"""approveuser -- Approve an account either because an administrator has reviewed the application, or the user has an authorization secret"""

		try:
			admin = ctx.checkadmin()
			if (secret == None) and (not admin):
				raise subsystems.exceptions.SecurityError, "Only administrators or users with self-authorization codes can approve new users"

		except subsystems.exceptions.SecurityError:
			raise

		except BaseException, e:
			admin = False
			if secret is None: raise
			else:
				g.log.msg('LOG_INFO', 'Ignored: (%s)' % e)


		ol=False
		if not hasattr(usernames,"__iter__"):
			ol=True
			usernames = [usernames]


		delusers, addusers, records, childstore = {}, {}, {}, {}

		# Need to commit users before records will validate
		for username in usernames:
			if not username in self.bdbs.newuserqueue.keys(txn=txn):
				raise KeyError, "User %s is not pending approval" % username

			if self.bdbs.users.get(username, txn=txn):
				delusers[username] = None
				g.log.msg("LOG_ERROR","User %s already exists, deleted pending record" % username)
				continue

			# ian: create record for user.
			user = self.bdbs.newuserqueue.sget(username, txn=txn) #[username]

			user.setContext(ctx)
			user.validate()

			if secret is not None and not user.validate_secret(secret):
				g.log.msg("LOG_ERROR","Incorrect secret for user %s; skipping"%username)
				time.sleep(2)

			else:
				# OK, add user
				# clear out the secret
				user._User__secret = None

				addusers[username] = user
				delusers[username] = None


		# Update user queue / users
		addusers = self.__commit_users(addusers.values(), ctx=ctx, txn=txn)
		delusers = self.__commit_newusers(delusers, ctx=ctx, txn=txn)

		# ian: todo: Do we need this root ctx? Probably...
		tmpctx = self.__makerootcontext(txn=txn)

		# Pass 2 to add records
		for user in addusers:

			if user.record == None and user.signupinfo:


				rec = self.newrecord("person", ctx=tmpctx, txn=txn)
				rec["username"] = username
				name = user.signupinfo.get('name', ['', '', ''])
				rec["name_first"], rec["name_middle"], rec["name_last"] = name[0], ' '.join(name[1:-1]) or None, name[1]
				rec["email"] = user.signupinfo.get('email')
				rec.adduser(username, level=3)

				for k,v in user.signupinfo.items():
					rec[k] = v

				#g.log.msg('LOG_DEBUG', "putting record...")
				rec = self.putrecord([rec], ctx=tmpctx, txn=txn)[0]

				# ian: todo: low priority: turning this off for now..
				#g.log.msg('LOG_DEBUG', "creating child records")
				#children = user.create_childrecords()
				#children = [(self.__putrecord([child], ctx=tmpctx, txn=txn)[0].recid, parents) for child, parents in children]

				#if children != []:
				#	self.__link('pclink', [(rec.recid, child) for child, _ in children], ctx=tmpctx, txn=txn)
				#	for links in children:
				#		child, parents = links
				#		self.__link('pclink', [(parent, child) for parent in parents], ctx=tmpctx, txn=txn)


				user.record = rec.recid
				user.signupinfo = None

		self.__commit_users(addusers, ctx=ctx, txn=txn)

		for group in g.GROUP_DEFAULTS:
			gr = self.getgroup(group, ctx=tmpctx, txn=txn)
			gr.adduser(user.username)
			self.putgroup(gr, ctx=tmpctx, txn=txn)

		approveusernames = [user.username for user in addusers]

		if ol and len(approveusernames)==1:
			return approveusernames[0]
		return approveusernames




	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def rejectuser(self, usernames, filt=True, ctx=None, txn=None):
		"""Remove a user from the pending new user queue - only an administrator can do this"""


		if not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators can approve new users"

		ol = 0
		if not hasattr(usernames,"__iter__"):
			ol = 1
			usernames = [usernames]

		delusers = {}

		for username in usernames:
			#if not username in self.bdbs.newuserqueue:
			if not self.bdbs.newuserqueue.get(username, txn=txn):
				if filt: pass
				else: raise KeyError, "User %s is not pending approval" % username

			delusers[username] = None


		self.__commit_newusers(delusers, ctx=ctx, txn=txn) # queue[username] = None

		if ol and len(delusers) == 1:
			return delusers.keys()[0]
		return delusers



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def getuserqueue(self, ctx=None, txn=None):
		"""Returns a list of names of unapproved users"""

		if not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators can approve new users"

		return self.bdbs.newuserqueue.keys(txn=txn)



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def getqueueduser(self, username, ctx=None, txn=None):
		"""retrieves a user's information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record"""

		if not ctx.checkreadadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators can access pending users"

		if hasattr(username,"__iter__"):
			ret={}
			for i in username:
				ret[i] = self.getqueueduser(i, ctx=ctx, txn=txn)
			return ret

		return self.bdbs.newuserqueue.sget(username, txn=txn) # [username]



	@DBProxy.publicmethod
	def putuser(self, user, ctx=None, txn=None):

		if not isinstance(user, dataobjects.user.User):
			try:
				user = dataobjects.user.User(user, ctx=ctx)
			except:
				raise ValueError, "User instance or dict required"

		if not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators may add/modify users with this method"

		user.validate()

		self.__commit_users([user], ctx=ctx, txn=txn)

		return user.username



	###############################
	# section: User Management
	###############################



	@DBProxy.publicmethod
	def setuserprivacy(self, usernames, state, ctx=None, txn=None):

		try:
			state=int(state)
			if state not in [0,1]:
				raise ValueError
		except ValueError, inst:
			raise Exception, "Invalid state. Must be 0 or 1."


		ol = 0
		if not hasattr(usernames,"__iter__"):
			ol = 1
			usernames = [usernames]

		commitusers = []
		for username in usernames:

			if username != ctx.username and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Cannot set another user's privacy"

			user = self.getuser(username, ctx=ctx, txn=txn)
			user.privacy = state
			commitusers.append(user)


		return self.__commit_users(commitusers, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def setpassword(self, oldpassword, newpassword, username=None, ctx=None, txn=None):

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Cannot attempt to set other user's passwords"
		else:
			username = ctx.username

		user = self.getuser(username, ctx=ctx, txn=txn)
		if not user:
			raise subsystems.exceptions.SecurityError, "Cannot change password for user '%s'"%username

		try:
			user.setpassword(oldpassword, newpassword)
		except:
			time.sleep(2)
			raise

		g.log.msg("LOG_INFO","Changing password for %s"%user.username)

		self.__commit_users([user], ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def setemail(self, email, username=None, ctx=None, txn=None):

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Cannot attempt to set other user's email"
		else:
			username = ctx.username

		user = self.getuser(username, ctx=ctx, txn=txn)
		user.email = email
		user.validate()

		g.log.msg("LOG_INFO","Changing email for %s"%user.username)

		self.__commit_users([user], ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def adduser(self, user, ctx=None, txn=None):
		"""adds a new user record. However, note that this only adds the record to the
		new user queue, which must be processed by an administrator before the record
		becomes active. This system prevents problems with securely assigning passwords
		and errors with data entry. Anyone can create one of these"""

		try:
			user = dataobjects.user.User(user, ctx=ctx)
		except Exception, inst:
			raise ValueError, "User instance or dict required (%s)"%inst


		if self.bdbs.users.get(user.username, txn=txn):
			raise KeyError, "User with username '%s' already exists" % user.username


		#if user.username in self.bdbs.newuserqueue:
		if self.bdbs.newuserqueue.get(user.username, txn=txn):
			raise KeyError, "User with username '%s' already pending approval" % user.username

		assert hasattr(user, '_User__secret')

		user.validate()

		self.__commit_newusers({user.username:user}, ctx=None, txn=txn)

		if ctx.checkadmin():
			#g.log.msg('LOG_DEBUG', "approving %s"%user.username)
			self.approveuser(user.username, ctx=ctx, txn=txn)

		return user.username



	#@write #self.bdbs.users
	def __commit_users(self, users, ctx=None, txn=None):
		"""Updates user. Takes User object (w/ validation.) Deprecated for non-administrators."""

		commitusers = []

		for user in users:

			if not isinstance(user, dataobjects.user.User):
				try:
					user = dataobjects.user.User(user, ctx=ctx)
				except:
					raise ValueError, "User instance or dict required"

			try:
				ouser = self.bdbs.users.sget(user.username, txn=txn) #[user.username]
			except:
				ouser = user
				#raise KeyError, "Putuser may only be used to update existing users"

			commitusers.append(user)

		#@begin

		for user in commitusers:
			self.bdbs.users.set(user.username, user, txn=txn)
			g.log.msg("LOG_COMMIT","self.bdbs.users.set: %r"%user.username)

		#@end

		return commitusers


	#@write #self.bdbs.newuserqueue
	def __commit_newusers(self, users, ctx=None, txn=None):
		"""write to newuserqueue; users is dict; set value to None to del"""

		#@begin

		for username, user in users.items():
			if user:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.set: %r"%username)
			else:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.set: %r, deleting"%username)

			self.bdbs.newuserqueue.set(username, user, txn=txn)

		#@end



	@DBProxy.publicmethod
	@emen2.util.utils.return_many_or_single('usernames', transform=lambda d: d[d.keys()[0]])
	def getuser(self, usernames, filt=True, lnf=False, getgroups=False, getrecord=True, ctx=None, txn=None):
		"""retrieves a user's information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record"""

		if not hasattr(usernames,"__iter__"):
			usernames = [usernames]

		recs = [x for x in usernames if isinstance(x, dataobjects.record.Record)]
		rec_ints = [x for x in usernames if isinstance(x, int)]
		if rec_ints:
			recs.extend(self.getrecord(rec_ints, filt=True, ctx=ctx, txn=txn))

		if recs:
			un2 = self.filtervartype(recs, vts=["user","userlist","acl"], flat=True, ctx=ctx, txn=txn)
			usernames.extend(un2)

		usernames = set(x for x in usernames if isinstance(x, basestring))

		ret={}
		for i in usernames:
			user = self.bdbs.users.get(i, None, txn=txn)

			if user == None:
				if filt: continue
				else:
					raise KeyError, "No such user: %s"%i

			user.setContext(ctx)

			# if the user has requested privacy, we return only basic info
			#if (user.privacy and ctx.username == None) or user.privacy >= 2:
			if user.privacy and not (ctx.checkreadadmin() or ctx.username == user.username):
				user2 = dataobjects.user.User()
				user2.username = user.username
				user = user2

			# Anonymous users cannot use this to extract email addresses
			#if ctx.username == None:
			#	user.groups = None

			if getgroups:
				user.groups = self.bdbs.groupsbyuser.get(user.username, set(), txn=txn)


			user.getuserrec(getrecord, lnf=lnf)

			ret[i] = user



		return ret





	@DBProxy.publicmethod
	def getuserdisplayname(self, username, lnf=False, perms=0, filt=True, ctx=None, txn=None):
		"""Return the full name of a user from the user record; include permissions param if perms=1"""

		namestoget = []
		ret = {}

		ol = 0
		if isinstance(username, basestring):
			ol = 1
		if isinstance(username, (basestring, int, dataobjects.record.Record)):
			username=[username]

		namestoget.extend(filter(lambda x:isinstance(x,basestring),username))

		vts=["user","userlist"]
		if perms:
			vts.append("acl")

		recs = []
		recs.extend(filter(lambda x:isinstance(x,dataobjects.record.Record), username))
		rec_ints = filter(lambda x:isinstance(x,int), username)
		if rec_ints:
			recs.extend(self.getrecord(rec_ints, filt=filt, ctx=ctx, txn=txn))

		if recs:
			namestoget.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))
			# ... need to parse comments since it's special
			namestoget.extend(reduce(operator.concat, [[i[0] for i in rec["comments"]] for rec in recs], []))

		namestoget = set(namestoget)

		users = self.getuser(namestoget, filt=filt, lnf=lnf, ctx=ctx, txn=txn)
		ret = {}

		for i in users.values():
			ret[i.username] = i.displayname

		if len(ret.keys())==0:
			return {}
		if ol:
			return ret.values()[0]

		return ret





	@DBProxy.publicmethod
	def getusernames(self, ctx=None, txn=None):
		"""Not clear if this is a security risk, but anyone can get a list of usernames
				This is likely needed for inter-database communications"""

		if ctx.username == None:
			return

		return set(self.bdbs.users.keys(txn=txn))



	# ian: todo: simple, high priority: this is currently implemented in TwistSupport_html/html/find.py
	# Move all those methods into main DB class

	# @DBProxy.publicmethod
	# def findusername(self, name, ctx=None, txn=None):
	# 	"""This will look for a username matching the provided name in a loose way"""
	#
	# 	if ctx.username == None: return
	#
	# 	if self.bdbs.users.get(name, txn=txn):
	# 		return name
	#
	# 	possible = filter(lambda x: name in x, self.bdbs.users.keys(txn=txn))
	# 	if len(possible) == 1:
	# 		return possible[0]
	# 	if len(possible) > 1:
	# 		return possible
	#
	# 	possible = []
	# 	for i in self.getusernames(ctx=ctx, txn=txn):
	# 		try:
	# 			u = self.getuser(name, ctx=ctx, txn=txn)
	# 		except:
	# 			continue
	#
	# 		for j in u.__dict__:
	# 			if isinstance(j, basestring) and name in j :
	# 				possible.append(i)
	# 				break
	#
	# 	if len(possible) == 1:
	# 		return possible[0]
	# 	if len(possible) > 1:
	# 		return possible
	#
	# 	return None



	##########################
	# section: Group Management
	##########################



	@DBProxy.publicmethod
	def getgroupnames(self, ctx=None, txn=None):
		return set(self.bdbs.groups.keys(txn=txn))



	@DBProxy.publicmethod
	@emen2.util.utils.return_many_or_single('groups', transform=lambda d:d.values()[0])
	def getgroup(self, groups, filt=1, ctx=None, txn=None):
		if not hasattr(groups,"__iter__"):
			groups = [groups]

		if filt: filt = None
		else: filt = lambda x:x.name
		ret = dict( [(x.name, x) for x in filter(filt, [self.bdbs.groups.get(i, txn=txn) for i in groups]) ] )

		# ian: todo: simple, high priority: include group display name, like user.displayname

		return ret



	#@write self.bdbs.groupsbyuser
	def __commit_groupsbyuser(self, addrefs=None, delrefs=None, ctx=None, txn=None):

		#@begin

		for user,groups in addrefs.items():
			try:
				if groups:
					g.log.msg("LOG_COMMIT_INDEX","__groupsbyuser key: %r, addrefs: %r"%(user, groups))
					self.bdbs.groupsbyuser.addrefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups))
				raise

		for user,groups in delrefs.items():
			try:
				if groups:
					g.log.msg("LOG_COMMIT_INDEX","__groupsbyuser key: %r, removerefs: %r"%(user, groups))
					self.bdbs.groupsbyuser.removerefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups))
				raise


		#@end



	#@write self.bdbs.groupsbyuser
	def __rebuild_groupsbyuser(self, ctx=None, txn=None):
		groups = self.getgroup(self.getgroupnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		users = collections.defaultdict(set)

		for k, group in groups.items():
			for user in group.members():
				#try:
				users[user].add(k)
				#except Exception, inst:
				#	g.log("unknown user %s (%s)"%(user, inst))


		#@begin

		g.log.msg("LOG_COMMIT_INDEX","self.bdbs.groupsbyuser: rebuilding index")

		self.bdbs.groupsbyuser.truncate(txn=txn)

		for k,v in users.items():
			self.bdbs.groupsbyuser.addrefs(k, v, txn=txn)

		#@end



	def __reindex_groupsbyuser(self, groups, ctx=None, txn=None):

		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)

		for group in groups:

			ngm = group.members()
			try: ogm = self.bdbs.groups.get(group.groupname, txn=txn).members()
			except: ogm = set()

			addusers = ngm - ogm
			delusers = ogm - ngm

			for user in addusers:
				addrefs[user].add(group.name)
			for user in delusers:
				delrefs[user].add(group.name)

		return addrefs, delrefs



	#@write self.bdbs.groups, self.bdbs.groupsbyuser
	@DBProxy.publicmethod
	def putgroup(self, groups, ctx=None, txn=None):

		if isinstance(groups, (dataobjects.group.Group, dict)): # or not hasattr(groups, "__iter__"):
			groups = [groups]

		groups2 = []
		groups2.extend(x for x in groups if isinstance(x, dataobjects.group.Group))
		groups2.extend(dataobjects.group.Group(x, ctx=ctx) for x in groups if isinstance(x, dict))

		for group in groups2:
			group.setContext(ctx)
			group.validate(txn=txn)

		self.__commit_groups(groups2, ctx=ctx, txn=txn)



	def __commit_groups(self, groups, ctx=None, txn=None):

		addrefs, delrefs = self.__reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

		#@begin
		for group in groups:
			g.log.msg("LOG_COMMIT","__groups.set: %r"%(group))
			self.bdbs.groups.set(group.name, group, txn=txn)

		self.__commit_groupsbyuser(addrefs=addrefs, delrefs=delrefs, ctx=ctx, txn=txn)
		#@end



	# merge with getuser?
	@DBProxy.publicmethod
	def getgroupdisplayname(self, groupname, ctx=None, txn=None):
		ol = 0
		if not hasattr(groupname,"__iter__"):
			groupname = [groupname]
			ol = 1

		groups = set(filter(lambda x:isinstance(x, basestring), groupname))
		gn_int = filter(lambda x:isinstance(x, int), groupname)
		if gn_int:
			groups |= reduce(set.union, [i.get("groups",set()) for i in self.getrecord(gn_int, filt=True, ctx=ctx, txn=txn)], set())

		groups = self.getgroup(groups, ctx=ctx, txn=txn)

		ret = {}

		for i in groups.values():
			ret[i.name]="Group: %s"%i.name

		if ol and len(ret)==1: return ret.values()[0]
		return ret




	#########################
	# section: workflow
	#########################

	# ian: todo: medium priority, medium difficulty:
	#	Workflows are currently turned off, need to be fixed.
	#	Do this soon.

	# @DBProxy.publicmethod
	# def getworkflow(self, ctx=None, txn=None):
	# 	"""This will return an (ordered) list of workflow objects for the given context (user).
	# 	it is an exceptionally bad idea to change a WorkFlow object's wfid."""
	#
	# 	if ctx.username == None:
	# 		raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"
	#
	# 	try:
	# 		return self.bdbs.workflow.sget(ctx.username, txn=txn) #[ctx.username]
	# 	except:
	# 		return []
	#
	#
	#
	# @DBProxy.publicmethod
	# def getworkflowitem(self, wfid, ctx=None, txn=None):
	# 	"""Return a workflow from wfid."""
	#
	# 	ret = None
	# 	wflist = self.getworkflow(ctx=ctx, txn=txn)
	# 	if len(wflist) == 0:
	# 		return None
	# 	else:
	# 		for thewf in wflist:
	# 			if thewf.wfid == wfid:
	# 				#ret = thewf.items_dict()
	# 				ret = dict(thewf)
	# 	return ret
	#
	#
	#
	# @DBProxy.publicmethod
	# def newworkflow(self, vals, ctx=None, txn=None):
	# 	"""Return an initialized workflow instance."""
	# 	return WorkFlow(vals)
	#
	#
	#
	#
	# #@write #self.bdbs.workflow
	# @DBProxy.publicmethod
	# def addworkflowitem(self, work, ctx=None, txn=None):
	# 	"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""
	#
	# 	if ctx.username == None:
	# 		raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"
	#
	# 	if not isinstance(work, WorkFlow):
	# 		try:
	# 			work = WorkFlow(work)
	# 		except:
	# 			raise ValueError, "WorkFlow instance or dict required"
	# 	#work=WorkFlow(work.__dict__.copy())
	# 	work.validate()
	#
	# 	#if not isinstance(work,WorkFlow):
	# 	#		 raise TypeError,"Only WorkFlow objects can be added to a user's workflow"
	#
	# 	work.wfid = self.bdbs.workflow.sget(-1, txn=txn)   #[-1]
	# 	self.bdbs.workflow[-1] = work.wfid + 1
	#
	# 	if self.bdbs.workflow.has_key(ctx.username):
	# 		wf = self.bdbs.workflow[ctx.username]
	# 	else:
	# 		wf = []
	#
	# 	wf.append(work)
	# 	self.bdbs.workflow[ctx.username] = wf
	#
	#
	# 	return work.wfid
	#
	#
	#
	#
	# #@write #self.bdbs.workflow
	# @DBProxy.publicmethod
	# def delworkflowitem(self, wfid, ctx=None, txn=None):
	# 	"""This will remove a single workflow object based on wfid"""
	# 	#self = db
	#
	# 	if ctx.username == None:
	# 		raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"
	#
	# 	wf = self.bdbs.workflow.sget(ctx.username, txn=txn) #[ctx.username]
	# 	for i, w in enumerate(wf):
	# 		if w.wfid == wfid :
	# 			del wf[i]
	# 			break
	# 	else:
	# 		raise KeyError, "Unknown workflow id"
	#
	# 	g.log.msg("LOG_COMMIT","self.bdbs.workflow.set: %r, deleting %s"%(ctx.username, wfid))
	# 	self.bdbs.workflow.set(ctx.username, wf, txn=txn)
	#
	#
	#
	#
	#
	# #@write #self.bdbs.workflow
	# @DBProxy.publicmethod
	# def setworkflow(self, wflist, ctx=None, txn=None):
	# 	"""This allows an authorized user to directly modify or clear his/her workflow. Note that
	# 	the external application should NEVER modify the wfid of the individual WorkFlow records.
	# 	Any wfid's that are None will be assigned new values in this call."""
	# 	#self = db
	#
	# 	if ctx.username == None:
	# 		raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"
	#
	# 	if wflist == None:
	# 		wflist = []
	# 	wflist = list(wflist)								 # this will (properly) raise an exception if wflist cannot be converted to a list
	#
	# 	for w in wflist:
	# 		w.validate()
	#
	# 		if not isinstance(w, WorkFlow):
	# 			self.txnabort(txn=txn) #txn.abort()
	# 			raise TypeError, "Only WorkFlow objects may be in the user's workflow"
	# 		if w.wfid == None:
	# 			w.wfid = self.bdbs.workflow.sget(-1, txn=txn) #[-1]
	# 			self.bdbs.workflow.set(-1, w.wfid + 1, txn=txn)
	#
	# 	g.log.msg("LOG_COMMIT","self.bdbs.workflow.set: %r"%ctx.username)
	# 	self.bdbs.workflow.set(ctx.username, wflist, txn=txn)
	#
	#
	#
	#
	# # ian: todo
	# #@write #self.bdbs.workflow
	# def __commit_workflow(self, wfs, ctx=None, txn=None):
	# 	pass




	#########################
	# section: paramdefs
	#########################


	@DBProxy.publicmethod
	def getvartypenames(self, ctx=None, txn=None):
		"""This returns a list of all valid variable types in the database. This is currently a
		fixed list"""
		return self.vtm.getvartypes()



	@DBProxy.publicmethod
	def getvartype(self, name, ctx=None, txn=None):
		"""This returns a list of all valid variable types in the database. This is currently a
		fixed list"""
		return self.vtm.getvartype(name)
		#return valid_vartypes[thekey][1]



	@DBProxy.publicmethod
	def getpropertynames(self, ctx=None, txn=None):
		"""This returns a list of all valid property types in the database. This is currently a
		fixed list"""
		return self.vtm.getproperties()



	@DBProxy.publicmethod
	def getpropertyunits(self, propname, ctx=None, txn=None):
		"""Returns a list of known units for a particular property"""
		# set(vtm.getproperty(propname).units) | set(vtm.getproperty(propname).equiv)
		return set(self.vtm.getproperty(propname).units)



	# ian: renamed addparamdef -> putparamdef for consistency
	@DBProxy.publicmethod
	def putparamdef(self, paramdef, parents=None, children=None, ctx=None, txn=None):
		"""adds a new ParamDef object, group 0 permission is required
		a p->c relationship will be added if parent is specified"""

		if not isinstance(paramdef, dataobjects.paramdef.ParamDef):
			try:
				paramdef = dataobjects.paramdef.ParamDef(paramdef, ctx=ctx)
			except ValueError, inst:
				raise ValueError, "ParamDef instance or dict required"


		#####################
		# ian: todo: medium: move this block to ParamDef.validate()

		if not ctx.checkcreate():
			raise subsystems.exceptions.SecurityError, "No permission to create new paramdefs (need record creation permission)"

		paramdef.name = unicode(paramdef.name).lower()

		try:
			pd = self.bdbs.paramdefs.sget(paramdef.name, txn=txn)

			# Root is permitted to force changes in parameters, though they are supposed to be static
			# This permits correcting typos, etc., but should not be used routinely
			# skip relinking if we're editing
			if not ctx.checkadmin():
				raise KeyError, "Only administrators can modify paramdefs: %s"%paramdef.name

			if pd.vartype != paramdef.vartype:
				g.log.msg("LOG_CRITICAL","WARNING! Changing paramdef %s vartype from %s to %s. This will REQUIRE database export/import and revalidation!!"%(paramdef.name, pd.vartype, paramdef.vartype))


		except:
			paramdef.creator = ctx.username
			paramdef.creationtime = self.gettime(ctx=ctx, txn=txn)


		#if not validate and not ctx.checkadmin():
		#	raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"
		#if validate:
		paramdef.validate()


		######### ^^^ ############

		self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)

		# create the index for later use
		paramindex = self.__getparamindex(paramdef.name, create=True, ctx=ctx, txn=txn)


		links = []
		if parents: links.append( map(lambda x:(x, paramdef.name), parents) )
		if children: links.append( map(lambda x:(paramdef.name, x), children) )
		if links:
			self.pclinks(links, keytype="paramdef", ctx=ctx, txn=txn)



	#@write #self.bdbs.paramdefs
	def __commit_paramdefs(self, paramdefs, ctx=None, txn=None):

		#@begin
		for paramdef in paramdefs:
			g.log.msg("LOG_COMMIT","self.bdbs.paramdefs.set: %r"%paramdef.name)
			self.bdbs.paramdefs.set(paramdef.name, paramdef, txn=txn)
		#@end



	# ian: todo: medium: Unify getparamdef, getparamdefs into -> getparamdef. Will require lots of 1 letter changes in other code.
	@DBProxy.publicmethod
	def getparamdefs(self, recs, filt=True, ctx=None, txn=None):
		"""Returns a list of ParamDef records.
		recs may be a single record, a list of records, or a list
		of paramdef names. This routine will
		retrieve the parameter definitions for all parameters with
		defined values in recs. The results are returned as a dictionary.
		It is much more efficient to use this on a list of records than to
		call it individually for each of a set of records."""

		# ian: rewrote this to include recdef keys and perhaps be a bit faster.
		params = set()
		if not hasattr(recs, "__iter__"):
			recs = (recs,)

		recs = list(recs)

		if len(recs) == 0:
			return {}

		if isinstance(recs[0], int):
			recs = self.getrecord(recs, ctx=ctx, txn=txn)

		if isinstance(recs[0], dataobjects.record.Record):
			q = set((i.rectype for i in recs))
			for i in q:
				params |= set(self.getrecorddef(i, ctx=ctx, txn=txn).paramsK)
			for i in recs:
				params |= set(i.getparamkeys())

		if isinstance(recs[0], basestring):
			params = set(recs)

		paramdefs = {}
		for i in params:
			try:
				pd = self.bdbs.paramdefs.sget(i, txn=txn) # [i]
				if pd.vartype not in self.indexablevartypes:
					pd.indexed = False
				paramdefs[i] = pd
			except:
				if filt:
					g.log.msg('LOG_WARNING', "WARNING: Invalid param: %s"%i)
					pass
				else:
					raise Exception, "Invalid param: %s"%i

		return paramdefs




	# ian todo: combine this and getparamdefs; alot of older places use this version. Keep the name 'singular' name, to match getrecord/getrecorddef/getuser
	@DBProxy.publicmethod
	def getparamdef(self, key, ctx=None, txn=None):
		"""gets an existing ParamDef object, anyone can get any field definition"""
		try:
			pd = self.bdbs.paramdefs.sget(key, txn=txn) #[key]
			if pd.vartype not in self.indexablevartypes:
				pd.indexed = False
			return pd
		except:
			raise KeyError, "Unknown ParamDef: %s" % key



	@DBProxy.publicmethod
	def getparamdefnames(self, ctx=None, txn=None):
		"""Returns a list of all ParamDef names"""
		return self.bdbs.paramdefs.keys(txn=txn)



	def __getparamindex(self, paramname, create=True, ctx=None, txn=None):

		try:
			return self.bdbs.fieldindex[paramname] # [paramname]				# Try to get the index for this key
		except Exception, inst:
			pass


		f = self.bdbs.paramdefs.sget(paramname, txn=txn) #[paramname]				 # Look up the definition of this field
		paramname = f.name

		if f.vartype not in self.indexablevartypes or not f.indexed:
			return None

		tp = self.vtm.getvartype(f.vartype).getindextype()

		if not create and not os.access("%s/index/params/%s.bdb" % (self.path, paramname), os.F_OK):
			raise KeyError, "No index for %s" % paramname

		# create/open index
		# datatype = d, record IDs
		#indexkeys=self.bdbs.indexkeys,
		txn2 = self.newtxn()
		try: self.bdbs.openparamindex(paramname, "%s/index/params/%s.bdb"%(self.path,paramname), keytype=tp, datatype="d", dbenv=self.__dbenv, txn=txn2)
		except:
			self.txnabort(txn=txn2)
			raise
		else: self.txncommit(txn=txn2)

		return self.bdbs.fieldindex[paramname]



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def __closeparamindex(self, paramname, ctx=None, txn=None):
		self.bdbs.closeparamindex(paramname)



	def __closeparamindexes(self, ctx=None, txn=None):
		self.bdbs.closeparamindexes()



	# ian: todo: simple: indexing deprecates this. You would modify param in the normal way now if you NEEDED to change choices.
	#
	# @DBProxy.publicmethod
	# def addparamchoice(self, paramdefname, choice, ctx=None, txn=None):
	# 	"""This will add a new choice to records of vartype=string. This is
	# 	the only modification permitted to a ParamDef record after creation"""
	#
	# 	paramdefname = unicode(paramdefname).lower()
	#
	# 	# ian: change to only allow logged in users to add param choices. silent return on failure.
	# 	if not ctx.checkcreate():
	# 		return
	#
	# 	d = self.bdbs.paramdefs.sget(paramdefname, txn=txn)  #[paramdefname]
	# 	if d.vartype != "string":
	# 		raise subsystems.exceptions.SecurityError, "choices may only be modified for 'string' parameters"
	#
	# 	d.choices = d.choices + (unicode(choice).title(),)
	#
	# 	d.setContext(ctx)
	# 	d.validate()
	#
	# 	self.__commit_paramdefs([d], ctx=ctx, txn=txn)



	#########################
	# section: recorddefs
	#########################





	@DBProxy.publicmethod
	def putrecorddef(self, recdef, parents=None, children=None, ctx=None, txn=None):
		"""Add or update RecordDef. The mainview should
		never be changed once used, since this will change the meaning of
		data already in the database, but sometimes changes of appearance
		are necessary, so this method is available."""

		if not isinstance(recdef, dataobjects.recorddef.RecordDef):
			try: recdef = dataobjects.recorddef.RecordDef(recdef, ctx=ctx)
			except: raise ValueError, "RecordDef instance or dict required"

		if not ctx.checkcreate():
			raise subsystems.exceptions.SecurityError, "No permission to create new RecordDefs"

		try:
			orec = self.bdbs.recorddefs.sget(recdef.name, txn=txn)
			orec.setContext(ctx)

		except:
			orec = dataobjects.recorddef.RecordDef(recdef, ctx=ctx)

		##################
		# ian: todo: medium: move this block to RecordDef.validate()

		if ctx.username != orec.owner and not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only the owner or administrator can modify RecordDefs"

		if recdef.mainview != orec.mainview and not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only the administrator can modify the mainview of a RecordDef"

		recdef.findparams()
		invalidparams = set(recdef.params) - set(self.getparamdefnames(ctx=ctx, txn=txn))

		if invalidparams:
			raise KeyError, "Invalid parameters: %s"%invalidparams

		# reset
		recdef.creator = orec.creator
		recdef.creationtime = orec.creationtime

		########## ^^^ ########

		recdef.validate()

		# commit
		self.__commit_recorddefs([recdef], ctx=ctx, txn=txn)

		links = []
		if parents: links.append( map(lambda x:(x, recdef.name), parents) )
		if children: links.append( map(lambda x:(recdef.name, x), children) )
		if links:
			self.pclinks(links, keytype="recorddef", ctx=ctx, txn=txn)

		return recdef.name



	#@write #self.bdbs.recorddefs
	def __commit_recorddefs(self, recorddefs, ctx=None, txn=None):

		#@begin
		for recorddef in recorddefs:
			g.log.msg("LOG_COMMIT","self.bdbs.recorddefs.set: %r"%recorddef.name)
			self.bdbs.recorddefs.set(recorddef.name, recorddef, txn=txn)
		#@end



	# ian: todo: why doesn't this accept multiple rectypes
	# ed: it does, what's wrong with it?
	# @g.log.debug_func
	@DBProxy.publicmethod
	@emen2.util.utils.return_list_or_single('rdids')
	def getrecorddef(self, rdids, filt=True, ctx=None, txn=None):
		"""Retrieves a RecordDef object. This will fail if the RecordDef is
		private, unless the user is an owner or	 in the context of a recid the
		user has permission to access"""

		if not hasattr(rdids,"__iter__"):
			rdids = [rdids]
			#return dict((x.name,x) for x in (self.getrecorddef(i, ctx=ctx, txn=txn) for i in rdid))
			#ed: note: ^^^ old behavior, breaks with return_list_or_single.... if you really want the old behavior,
			#              I will reimplement it later

		ret = []
		for rdid in rdids:
			if isinstance(rdid, int):
				try:
					recorddef = self.getrecord(rdid, filt=False, ctx=ctx, txn=txn).rectype
				except KeyError:
					if filt: continue
					else:
						raise KeyError, "No such Record '%s'" % rdid
			else: recorddef = str(rdid)
			recorddef = recorddef.lower()

			try: rd = self.bdbs.recorddefs.sget(recorddef, txn=txn)
			except KeyError:
				raise KeyError, "No such RecordDef '%s'"%recorddef

			rd.setContext(ctx)

			# if the RecordDef isn't private or if the owner is asking, just return it now
			if rd.private and not rd.accessible():
				raise subsystems.exceptions.SecurityError, "RecordDef %d not accessible" % (recid, recorddef)
			ret.append(rd)

		# success, the user has permission
		return dict((x.name, x) for x in ret).values()



	@DBProxy.publicmethod
	def getrecorddefnames(self, ctx=None, txn=None):
		"""This will retrieve a list of all existing RecordDef names,
		even those the user cannot access the contents of"""
		return self.bdbs.recorddefs.keys(txn=txn)



	# ian: todo: see findusername for notes
	#
	# @DBProxy.publicmethod
	# def findrecorddefname(self, name, ctx=None, txn=None):
	# 	"""Find a recorddef similar to the passed 'name'. Returns the actual RecordDef,
	# 	or None if no match is found."""
	#
	#
	# 	#if self.bdbs.recorddefs.has_key(name):
	# 	if self.bdbs.recorddefs.get(name, txn=txn):
	# 		return name
	#
	# 	if name[-1] == "s":
	# 			if self.bdbs.recorddefs.has_key(name[:-1], txn=txn):
	# 				return name[:-1]
	# 			if name[-2] == "e" and self.bdbs.recorddefs.has_key(name[:-2], txn=txn):
	# 				return name[:-2]
	# 	if name[-3:] == "ing" and self.bdbs.recorddefs.has_key(name[:-3], txn=txn):
	# 		return name[:-3]
	# 	return None



	#########################
	# section: records
	#########################



	# ian: improved!
	# ed: more improvments!
	@DBProxy.publicmethod
	@emen2.util.utils.return_list_or_single('recids')
	def getrecord(self, recids, filt=True, ctx=None, txn=None):
		"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
		if dbid is 0, the current database is used."""

		if not hasattr(recids, '__iter__'):
			recids = [recids]

		ret = []
		for i in sorted(recids):
			try:
				rec = self.bdbs.records.sget(i, txn=txn)
				rec.setContext(ctx)
				ret.append(rec)
			except (emen2.Database.subsystems.exceptions.SecurityError, KeyError, TypeError), e:
				if filt: pass
				else: raise
				# KeyError, "No such record %s"%(i)
			#except emen2.Database.subsystems.exceptions.SecurityError, e:
			#	if filt: pass
			#	else: raise e

		return ret



	# ian: todo: medium: allow to copy existing record
	# ian: todo: simple: fix init option -- breaks some units
	@DBProxy.publicmethod
	def newrecord(self, rectype, recid=None, init=False, inheritperms=None, ctx=None, txn=None):
		"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
		already exist)."""

		# ian: todo: hard: remove the recid option. it was a kludge to get things working in time.
		# if recid and not ctx.checkadmin():
		# 	raise emen2.Database.subsystems.exceptions.SecurityError, "Cannot set recid in this way"

		# try to get the RecordDef entry, this still may fail even if it exists, if the
		# RecordDef is private and the context doesn't permit access
		# t = dict(filter(lambda x:x[1]!=None, self.getrecorddef(rectype, ctx=ctx, txn=txn).params.items()))

		if not ctx.checkcreate():
			raise emen2.Database.subsystems.exceptions.SecurityError, "No permission to create new records"

		t = [ (x,y) for x,y in self.getrecorddef(rectype, ctx=ctx, txn=txn).params.items() if y != None]
		rec = dataobjects.record.Record(rectype=rectype, recid=recid, ctx=ctx)

		if init:
			rec.update(t)

		if inheritperms != None:
			try:
				if not hasattr(inheritperms, "__iter__"):
					inheritperms = [inheritperms]

				precs = self.getrecord(inheritperms, filt=False, ctx=ctx, txn=txn)

				for prec in precs:
					rec.addumask(prec["permissions"])
					rec.addgroup(prec["groups"])

			except Exception, inst:
				g.log.msg("LOG_ERROR","newrecord: Error setting inherited permissions from record %s (%s)"%(inheritperms, inst))

		return rec



	@DBProxy.publicmethod
	def getparamdefnamesbyvartype(self, vts, paramdefs=None, ctx=None, txn=None):
		if not hasattr(vts,"__iter__"): vts = [vts]

		if not paramdefs:
			paramdefs = self.getparamdefs(self.getparamdefnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)

		return [x.name for x in paramdefs.values() if x.vartype in vts]



	# ian: this might be helpful
	# e.g.: filtervartype(136, ["user","userlist"])
	@DBProxy.publicmethod
	def filtervartype(self, recs, vts, filt=True, flat=0, ctx=None, txn=None):

		if not recs:
			return [None]

		recs2 = []

		# process recs arg into recs2 records, process params by vartype, then return either a dict or list of values; ignore those specified
		ol = 0
		if isinstance(recs,(int,dataobjects.record.Record)):
			ol = 1
			recs = [recs]

		# get the records...
		recs2.extend(filter(lambda x:isinstance(x,dataobjects.record.Record),recs))
		recs2.extend(self.getrecord(filter(lambda x:isinstance(x,int),recs), filt=filt, ctx=ctx, txn=txn))

		params = self.getparamdefnamesbyvartype(vts, ctx=ctx, txn=txn)

		re = [[rec.get(pd) for pd in params if rec.get(pd)] for rec in recs2]

		if flat:
			# ian: todo: medium: replace with reduce - this is much slower and is a common operation.
			# the reason flatten is used because some vartypes are nested lists, e.g. permissions.
			re = self.__flatten(re)
			return set(re)-set([None])

		return re



	@DBProxy.publicmethod
	def checkorphans(self, recid, ctx=None, txn=None):
		"""Find orphaned records that would occur if recid was deleted."""

		srecid = set([recid])
		saved = set()

		# this is hard to calculate
		children = self.getchildren(recid, recurse=50, tree=1, ctx=ctx, txn=txn)
		orphaned = reduce(set.union, children.values(), set())
		orphaned.add(recid)
		parents = self.getparents(orphaned, ctx=ctx, txn=txn)

		# orphaned is records that will be orphaned if they are not rescued
		# find subtrees that will be rescued by links to other places
		for child in orphaned - srecid:
			if parents.get(child, set()) - orphaned:
				saved.add(child)

		children_saved = self.getchildren(saved, recurse=50, ctx=ctx, txn=txn)
		children_saved_set = reduce(set.union, children_saved.values()+[set(children_saved.keys())], set())

		orphaned -= children_saved_set

		return orphaned





		# For each recurse level, see if child has a parent that hasn't been seen yet.
		# visited = set([recid])
		# to_visit = children.get(recid, set())
		# while to_visit:
		# 	child = to_visit.pop()
		# 	if not parents.get(child set()) - orphaned:
		# 		orphaned.add(child)
		# 	else:
		# 		to_visit.add(child)



	@DBProxy.publicmethod
	def deleterecord(self, recid, ctx=None, txn=None):
		"""Unlink and hide a record; it is still accessible to owner and root. Records are never truly deleted, just hidden."""

		rec = self.getrecord(recid, ctx=ctx, txn=txn)
		if not rec.isowner():
			raise subsystems.exceptions.SecurityError, "No permission to delete record"

		parents = self.getparents(recid, ctx=ctx, txn=txn)
		children = self.getchildren(recid, ctx=ctx, txn=txn)

		if len(parents) > 0 and rec["deleted"] !=1 :
			rec.addcomment("Record marked for deletion and unlinked from parents: %s"%", ".join([unicode(x) for x in parents]))
		elif rec["deleted"] != 1:
			rec.addcomment("Record marked for deletion")

		rec["deleted"] = True

		self.putrecord(rec, ctx=ctx, txn=txn)

		for i in parents:
			self.pcunlink(i,recid, ctx=ctx, txn=txn)


		for i in children:
			self.pcunlink(recid, i, ctx=ctx, txn=txn)
			# ian: todo: not sure to do this or not.
			# c2 = self.getchildren(i, ctx=ctx, txn=txn)
			# c2 -= set([recid])
			# if child had more than one parent, make a note one parent was removed
			# if len(c2) > 0:
			#	rec2=self.getrecord(i, ctx=ctx, txn=txn)
			#	rec["comments"]="Parent record %s was deleted"%recid
			#	self.putrecord(rec2, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def addcomment(self, recid, comment, ctx=None, txn=None):
		rec = self.getrecord(recid, ctx=ctx, txn=txn)
		rec.addcomment(comment)
		self.putrecord(rec, ctx=ctx, txn=txn)
		return self.getrecord(recid, ctx=ctx, txn=txn)["comments"]




	#########################
	# section: Put Records
	#########################



	# ian todo: simple: redo these three methods to use the multiple putrecord
	@DBProxy.publicmethod
	def putrecordvalue(self, recid, param, value, ctx=None, txn=None):
		"""Convenience method to update a single value in a record
		@param recid Record ID
		@param param Parameter
		@param value New value

		@return Record instance

		"""
		rec = self.getrecord(recid, ctx=ctx, txn=txn)
		rec[param] = value
		self.putrecord(rec, ctx=ctx, txn=txn)
		return self.getrecord(recid, ctx=ctx, txn=txn)[param]



	@DBProxy.publicmethod
	def putrecordvalues(self, recid, values, ctx=None, txn=None):
		"""Dict.update()-like operation on a single record"""

		try:
			rec = self.getrecord(recid, ctx=ctx, txn=txn)
		except:
			return

		for k, v in values.items():
			if v == None:
				del rec[k]
			else:
				rec[k] = v

		self.putrecord(rec, ctx=ctx, txn=txn)
		return self.getrecord(recid, ctx=ctx, txn=txn)



	@DBProxy.publicmethod
	def putrecordsvalues(self, d, ctx=None, txn=None):
		"""dict.update()-like operation on a number of records"""

		ret = {}
		for k, v in d.items():
			ret[k] = self.putrecordvalues(k, v, ctx=ctx, txn=txn)
		return ret



	@DBProxy.publicmethod
	def putrecord(self, recs, filt=True, warning=0, log=True, ctx=None, txn=None):
		"""Commit records

		@param recs Single or iterable records to commit
		@keyparam filt Filter out records you cannot modify
		@keyparam warning Admin only: Bypass validation
		@keyparam log Admin only: Do not add to Record history

		@return Committed records

		@exception SecurityError, DBError, KeyError, ValueError, TypeError..
		"""

		if (warning or not log) and not ctx.checkadmin():
			raise subsystems.exceptions.SecurityError, "Only administrators may bypass logging or validation"

		# filter input for dicts/records
		ol = False
		if isinstance(recs,(dataobjects.record.Record,dict)):
			ol = True
			recs = [recs]
		elif not hasattr(recs, 'extend'):
			recs = list(recs)

		dictrecs = filter(lambda x:isinstance(x,dict), recs)
		recs.extend(map(lambda x:dataobjects.record.Record(x, ctx=ctx), dictrecs))
		recs = filter(lambda x:isinstance(x,dataobjects.record.Record), recs)

		ret = self.__putrecord(recs, warning=warning, log=log, ctx=ctx, txn=txn)

		if ol and len(ret) > 0:
			return ret[0]

		return ret



	# And now, a long parade of internal putrecord methods

	def __putrecord(self, updrecs, warning=0, log=True, ctx=None, txn=None):
		"""(Internal) Proess records for committing. If anything is wrong, raise an Exception, which will cancel the operation and usually the txn.
			If OK, then proceed to write records and all indexes. At that point, only really serious DB errors should ever occur."""

		if len(updrecs) == 0:
			return []

		crecs = []
		updrels = []

		# These are built-ins that we treat specially
		param_immutable = set(["recid","rectype","creator","creationtime","modifytime","modifyuser"])
		param_special = param_immutable | set(["comments","permissions","groups","history"])

		# Assign temp recids to new records
		# for offset,updrec in enumerate(filter(lambda x:x.recid < 0, updrecs)):
		# ian: changed to x.recid == None to preserve trees in uncommitted records

		for offset,updrec in enumerate(x for x in updrecs if x.recid == None):
			updrec.recid = -1 * (offset + 100)

		# Check 'parent' and 'children' special params
		updrels = self.__putrecord_getupdrels(updrecs, ctx=ctx, txn=txn)

		# Assign all changes the same time
		t = self.gettime(ctx=ctx, txn=txn)

		# preprocess: copy updated record into original record (updrec -> orec)
		for updrec in updrecs:

			recid = updrec.recid

			# ian: todo: I once got a weird error here where there was no txn,
			# 			 but after restart it was OK. weird.
			#         we need to acquire RMW lock here to prevent changes during commit


			# ian: put recid<0 check first, to keep issues with recid counter
			if recid < 0:
				orec = self.newrecord(updrec.rectype, recid=updrec.recid, ctx=ctx, txn=txn)

			elif self.bdbs.records.exists(updrec.recid, txn=txn, flags=g.RMWFLAGS):
				orec = self.bdbs.records.sget(updrec.recid, txn=txn)
				orec.setContext(ctx)

			else:
				raise KeyError, "Cannot update non-existent record %s"%recid


			# Set Context and Validate
			updrec.setContext(ctx)
			updrec.validate(orec=orec, warning=warning)

			# Compare to original record
			cp = orec.changedparams(updrec) - param_immutable

			# orec.recid < 0 because new records will always be committed, even if skeletal
			if not cp and orec.recid >= 0:
				g.log.msg("LOG_INFO","putrecord: No changes for record %s, skipping"%recid)
				continue


			# Copy values into fetched/new Record to prevent Users attempting funny things

			if "comments" in cp:
				for i in updrec["comments"]:
					if i not in orec._Record__comments:
						orec.addcomment(i[2])

			for param in cp - param_special:
				if log and orec.recid >= 0:
					orec.addhistory(param, orec[param])
				orec[param] = updrec[param]

			if "permissions" in cp:
				orec.setpermissions(updrec.get("permissions"))

			if "groups" in cp:
				orec.setgroups(updrec.get("groups"))

			if log:
				orec["modifytime"] = t
				orec["modifyuser"] = ctx.username

			# I don't think we need to re-validate..
			# if validate:
			# 	orec.validate(orec=orcp, warning=warning, params=cp)

			crecs.append(orec)

		return self.__commit_records(crecs, updrels, ctx=ctx, txn=txn)



	def __putrecord_getupdrels(self, updrecs, ctx=None, txn=None):
		# get parents/children to update relationships
		r = []
		for updrec in updrecs:
			_p = updrec.get("parents") or []
			_c = updrec.get("children") or []
			if _p:
				r.extend([(i, updrec.recid) for i in _p])
				del updrec["parents"]
			if _c:
				r.extend([(updrec.recid,i) for i in _c])
				del updrec["children"]
		return r



	# commit
	#@write	#self.bdbs.records, self.bdbs.recorddefbyrec, self.bdbs.recorddefindex
	# also, self.fieldindex* through __commit_paramindex(), self.bdbs.secrindex through __commit_secrindex
	def __commit_records(self, crecs, updrels=[], onlypermissions=False, reindex=False, ctx=None, txn=None):

		rectypes = collections.defaultdict(list)
		newrecs = filter(lambda x:x.recid < 0, crecs)
		recmap = {}

		# Fetch the old records for calculating index updates. Set RMW flags.
		# To force reindexing (e.g. to rebuild indexes) treat as new record
		cache = {}
		for i in crecs:
			if reindex or i.recid < 0:
				continue
			try:
				orec = self.bdbs.records.sget(i.recid, txn=txn, flags=g.RMWFLAGS) # [recid]
			except:
				orec = {}
			cache[i.recid] = orec


		# Calculate index updates. Shortcut if we're only modifying permissions. Use with caution.
		indexupdates = {}
		if not onlypermissions:
			indexupdates = self.__reindex_params(crecs, cache=cache, ctx=ctx, txn=txn)
		secr_addrefs, secr_removerefs = self.__reindex_security(crecs, cache=cache, ctx=ctx, txn=txn)
		secrg_addrefs, secrg_removerefs = self.__reindex_security_groups(crecs, cache=cache, ctx=ctx, txn=txn)


		# OK, all go to write records/indexes!

		#@begin

		# this needs a lock.
		if newrecs:
			baserecid = self.bdbs.records.sget(-1, txn=txn, flags=g.RMWFLAGS)
			g.log.msg("LOG_INFO","Setting recid counter: %s -> %s"%(baserecid, baserecid + len(newrecs)))
			self.bdbs.records.set(-1, baserecid + len(newrecs), txn=txn)


		# add recids to new records, create map from temp recid, setup index
		for offset, newrec in enumerate(newrecs):
			oldid = newrec.recid
			newrec.recid = offset + baserecid
			recmap[oldid] = newrec.recid
			rectypes[newrec.rectype].append(newrec.recid)


		# This actually stores the record in the database
		# ian: if we're just reindexing, no need to waste time writing records.
		if reindex:
			for crec in crecs:
				rectypes[crec.rectype].append(crec.recid)
		else:
			for crec in crecs:
				g.log.msg("LOG_COMMIT","self.bdbs.records.set: %r"%crec.recid)
				self.bdbs.records.set(crec.recid, crec, txn=txn)


		# Security index
		self.__commit_secrindex(secr_addrefs, secr_removerefs, recmap=recmap, ctx=ctx, txn=txn)
		self.__commit_secrindex_groups(secrg_addrefs, secrg_removerefs, recmap=recmap, ctx=ctx, txn=txn)

		# RecordDef index
		self.__commit_recorddefindex(rectypes, recmap=recmap, ctx=ctx, txn=txn)

		# Param index
		for param, updates in indexupdates.items():
			self.__commit_paramindex(param, updates[0], updates[1], recmap=recmap, ctx=ctx, txn=txn)

		print updrels
		print recmap

		# Create parent/child links
		for link in updrels:
			try:
				self.pclink( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), ctx=ctx, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst))
				raise


		g.log.msg("LOG_INFO", "Committed %s records"%(len(crecs)))
		#@end

		return crecs



	# The following methods write to the various indexes

	def __commit_recorddefindex(self, rectypes, recmap=None, ctx=None, txn=None):
		if not recmap: recmap = {}

		for rectype,recs in rectypes.items():
			try:
				g.log.msg("LOG_COMMIT_INDEX","self.bdbs.recorddefindex.addrefs: %r, %r"%(rectype, recs))
				self.bdbs.recorddefindex.addrefs(rectype, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype, recs, inst))
				raise



	#@write #self.bdbs.secrindex
	def __commit_secrindex(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):
		if not recmap: recmap = {}

		for user, recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				g.log.msg("LOG_COMMIT_INDEX","self.bdbs.secrindex.addrefs: %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex.addrefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))
				raise

		for user, recs in removerefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				g.log.msg("LOG_COMMIT_INDEX","secrindex.removerefs: user %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex.removerefs(user, recs, txn=txn)
			except bsddb3.db.DBError, inst:
				g.log.msg("LOG_CRITICAL", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
				raise
			except Exception, inst:
				g.log.msg("LOG_ERROR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
				raise



	#@write #self.bdbs.secrindex
	def __commit_secrindex_groups(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):

		if not recmap: recmap = {}

		for user, recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				g.log.msg("LOG_COMMIT_INDEX","self.bdbs.secrindex_groups.addrefs: %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex_groups.addrefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not add security index for group %s, records %s (%s)"%(user, recs, inst))
				raise

		for user, recs in removerefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				g.log.msg("LOG_COMMIT_INDEX","secrindex_groups.removerefs: user %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex_groups.removerefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not remove security index for group %s, records %s (%s)"%(user, recs, inst))
				raise



	#@write #self.bdbs.fieldindex*
	def __commit_paramindex(self, param, addrefs, delrefs, recmap=None, ctx=None, txn=None):
		"""commit param updates"""
		if not recmap: recmap = {}

		addindexkeys = []
		delindexkeys = []

		# addrefs = upds[0], delrefs = upds[1]
		if not addrefs and not delrefs:
			return


		try:
			paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
			if paramindex == None:
				raise Exception, "Index was None; unindexable?"
		except Exception, inst:
			g.log.msg("LOG_CRITICAL","Could not open param index: %s (%s)"% (param, inst))
			raise


		for newval,recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				if recs:
					g.log.msg("LOG_COMMIT_INDEX","param index %r.addrefs: %r '%r', %r"%(param, type(newval), newval, len(recs)))
					addindexkeys = paramindex.addrefs(newval, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))
				raise

		for oldval,recs in delrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				if recs:
					g.log.msg("LOG_COMMIT_INDEX","param index %r.removerefs: %r '%r', %r"%(param, type(oldval), oldval, len(recs)))
					delindexkeys = paramindex.removerefs(oldval, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))
				raise


		# Update index-index, a necessary evil..
		self.bdbs.indexkeys.addrefs(param, addindexkeys, txn=txn)
		self.bdbs.indexkeys.removerefs(param, delindexkeys, txn=txn)



	# These methods calculate what index updates to make

	def __reindex_params(self, updrecs, cache=None, ctx=None, txn=None):
		"""update param indices"""
		# g.log.msg('LOG_DEBUG', "Calculating param index updates...")

		if not cache: cache = {}
		ind = collections.defaultdict(list)
		indexupdates = {}
		unindexed = set(["recid","rectype","comments","permissions"])

		for updrec in updrecs:
			recid = updrec.recid
			orec = cache.get(recid, {})

			cp = updrec.changedparams(orec)

			if not cp:
				continue

			for param in set(cp) - unindexed:
				ind[param].append((recid,updrec.get(param),orec.get(param)))

		# Now update indices; filter because most param indexes have no changes
		for key,v in filter(lambda x:x[1],ind.items()):
			indexupdates[key] = self.__reindex_param(key, v, txn=txn)

		return indexupdates



	def __reindex_param(self, key, items, ctx=None, txn=None):

		# items format:
		# [recid, newval, oldval]
		pd = self.bdbs.paramdefs.sget(key, txn=txn) # [key]
		addrefs = {}
		delrefs = {}

		if pd.vartype not in self.indexablevartypes or not pd.indexed:
			return addrefs, delrefs

		# remove oldval=newval; strip out wrong keys
		items = filter(lambda x:x[1] != x[2], items)

		if pd.vartype == "text":
			return self.__reindex_paramtext(key, items, ctx=ctx, txn=txn)

		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)

		for i in items:
			addrefs[i[1]].add(i[0])
			delrefs[i[2]].add(i[0])

		if None in addrefs: del addrefs[None]
		if None in delrefs: del delrefs[None]

		return addrefs, delrefs



	def __reindex_paramtext(self, key, items, ctx=None, txn=None):
		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)

		for item in items:

			for i in self.__reindex_getindexwords(item[1], ctx=ctx, txn=txn):
				addrefs[i].append(item[0])

			for i in self.__reindex_getindexwords(item[2], ctx=ctx, txn=txn):
				delrefs[i].append(item[0])

		allwords = set(addrefs.keys() + delrefs.keys()) - set(g.UNINDEXED_WORDS)

		addrefs2 = {}
		delrefs2 = {}

		for i in allwords:
			# make set, remove unchanged items
			addrefs2[i] = set(addrefs.get(i,[]))
			delrefs2[i] = set(delrefs.get(i,[]))
			u = addrefs2[i] & delrefs2[i]
			addrefs2[i] -= u
			delrefs2[i] -= u

		# ian: todo: critical: doesn't seem to be returning any recs... check this out.
		return addrefs2, delrefs2



	__reindex_getindexwords_m = re.compile('([a-zA-Z]+)|([0-9][.0-9]+)')  #'[\s]([a-zA-Z]+)[\s]|([0-9][.0-9]+)'
	def __reindex_getindexwords(self, value, ctx=None, txn=None):
		if value == None: return []
		value = unicode(value).lower()
		return set((x[0] or x[1]) for x in self.__reindex_getindexwords_m.findall(value))



	def __reindex_security(self, updrecs, cache=None, ctx=None, txn=None):
		# g.log.msg('LOG_DEBUG', "Calculating security updates...")

		if not cache: cache = {}
		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)

		for updrec in updrecs:
			recid = updrec.recid

			# this is a fix for proper indexing of new records...
			# write lock acquire at beginning of txn
			orec = cache.get(recid, {})

			if updrec.get("permissions") == orec.get("permissions"):
				continue

			nperms = set(reduce(operator.concat, updrec.get("permissions", ()), () ))
			operms = set(reduce(operator.concat, orec.get("permissions",()), () ))

			for user in nperms - operms:
				addrefs[user].append(recid)
			for user in operms - nperms:
				delrefs[user].append(recid)

		return addrefs, delrefs



	def __reindex_security_groups(self, updrecs, cache=None, ctx=None, txn=None):
		# g.log.msg('LOG_DEBUG', "Calculating security updates...")

		if not cache: cache = {}
		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)

		for updrec in updrecs:
			recid = updrec.recid

			orec = cache.get(recid, {})

			if updrec.get("groups") == orec.get("groups"):
				continue

			for group in updrec.get("groups", set()) - orec.get("groups", set()):
				addrefs[group].append(recid)
			for group in orec.get("groups", set()) - updrec.get("groups", set()):
				delrefs[group].append(recid)

		return addrefs, delrefs



	# If the indexes blow up...

	# Stage 1
	def __rebuild_all(self, ctx=None, txn=None):
		g.log.msg("LOG_INFO","Rebuilding ALL indexes")

		ctx = self.__makerootcontext(txn=txn)

		self.bdbs.secrindex.truncate(txn=txn)
		self.bdbs.secrindex_groups.truncate(txn=txn)
		self.bdbs.recorddefindex.truncate(txn=txn)
		self.bdbs.groupsbyuser.truncate(txn=txn)

		allparams = self.bdbs.paramdefs.keys()
		paramindexes = {}
		for param in allparams:
			paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
			if paramindex != None:
				g.log.msg('LOG_DEBUG', paramindex)
				try:
					paramindex.truncate(txn=txn)
				except Exception, e:
					g.log.msg("LOG_INFO","Couldn't truncate %s: %s"%(param, e))
				paramindexes[param] = paramindex


		g.log.msg("LOG_INFO","Done truncating all indexes")

		self.__rebuild_groupsbyuser(ctx=ctx, txn=txn)

		maxrecords = self.bdbs.records.get(-1, txn=txn)
		g.log.msg('LOG_INFO',"Records in DB: %s"%(maxrecords-1))

		blocks = range(0, maxrecords, g.BLOCKLENGTH) + [maxrecords]
		blocks = zip(blocks, blocks[1:])


		for pos, pos2 in blocks:
			g.log.msg("LOG_INFO","Reindexing records %s -> %s"%(pos, pos2))

			#txn2 = self.newtxn(txn)

			crecs = []
			for i in range(pos, pos2):
				g.log.msg("LOG_INFO","... %s"%i)
				crecs.append(self.bdbs.records.sget(i, txn=txn))

			self.__commit_records(crecs, reindex=True, ctx=ctx, txn=txn)

			#txn2.commit()

		#self.__rebuild_indexkeys(ctx=ctx, txn=txn)

		g.log.msg("LOG_INFO","Done rebuilding all indexes")




	# Stage 2
	def __rebuild_secrindex(self, ctx=None, txn=None):


		g.log.msg("LOG_INFO","Rebuilding secrindex/secrindex_groups")

		g.log.msg("LOG_COMMIT_INDEX","self.bdbs.secrindex.truncate")
		self.bdbs.secrindex.truncate(txn=txn)
		g.log.msg("LOG_COMMIT_INDEX","self.bdbs.secrindex_groups.truncate")
		self.bdbs.secrindex_groups.truncate(txn=txn)

		pos = 0
		crecs = True
		recmap = {}
		maxrecords = self.bdbs.records.get(-1, txn=txn)

		while crecs:
			txn2 = self.newtxn(txn)

			pos2 = pos + g.BLOCKLENGTH
			if pos2 > maxrecords: pos2 = maxrecords

			g.log.msg("LOG_INFO","%s -> %s"%(pos, pos2))
			crecs = self.getrecord(range(pos, pos2), ctx=ctx, txn=txn2)
			pos = pos2

			# by omitting cache, will be treated as new recs...
			secr_addrefs, secr_removerefs = self.__reindex_security(crecs, ctx=ctx, txn=txn2)
			secrg_addrefs, secrg_removerefs = self.__reindex_security_groups(crecs, ctx=ctx, txn=txn2)

			# Security index
			self.__commit_secrindex(secr_addrefs, secr_removerefs, ctx=ctx, txn=txn2)
			self.__commit_secrindex_groups(secrg_addrefs, secrg_removerefs, ctx=ctx, txn=txn2)

			txn2.commit()
			#self.txncommit(txn2)




	###############################
	# section: Record Permissions View / Modify
	###############################



	# ian: I benchmarked with new index system; lowered the threshold for checking indexes. But maybe improve? 01/10/2010.
	@DBProxy.publicmethod
	def filterbypermissions(self, recids, ctx=None, txn=None):

		if not isinstance(recids, set):
			recids = set(recids)

		if ctx.checkreadadmin():
			return recids

		# ian: indexes are now faster, generally...
		if len(recids) < 100:
			return set([x.recid for x in self.getrecord(recids, filt=True, ctx=ctx, txn=txn)])

		find = set(recids)
		find -= self.bdbs.secrindex.get(ctx.username, set(), txn=txn)

		for group in sorted(ctx.groups):
			if find:
				find -= self.bdbs.secrindex_groups.get(group, set(), txn=txn)

		return recids - find

		# this is usually the fastest; it's the same as getindexbycontext basically...
		# method 2 (removed other methods that were obsolete)
		# ret = []
		#
		# if ctx.username != None and ctx.username != "anonymous":
		# 	ret.extend(recids & set(self.bdbs.secrindex.get(ctx.username, [], txn=txn)))
		#
		# for group in sorted(ctx.groups, reverse=True):
		# 	ret.extend(recids & set(self.bdbs.secrindex_groups.get(group, [], txn=txn)))
		#
		# return set(ret)



	@DBProxy.publicmethod
	def secrecordadduser_compat(self, umask, recid, recurse=0, reassign=False, delusers=None, addgroups=None, delgroups=None, ctx=None, txn=None):
		"""Maintain compat with older versions that require effort to update"""
		self.__putrecord_setsecurity(recid, umask=umask, addgroups=addgroups, recurse=recurse, reassign=reassign, delusers=delusers, delgroups=delgroups, ctx=ctx, txn=txn)


	@DBProxy.publicmethod
	def secrecordadduser(self, recids, users, level=0, recurse=0, reassign=False, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids, addusers=users, addlevel=level, recurse=recurse, reassign=reassign, ctx=ctx, txn=txn)


	@DBProxy.publicmethod
	def secrecordremoveuser(self, recids, users, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids, delusers=users, recurse=recurse, ctx=ctx, txn=txn)


	@DBProxy.publicmethod
	def secrecordaddgroup(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids, addgroups=groups, recurse=recurse, ctx=ctx, txn=txn)


	@DBProxy.publicmethod
	def secrecordremovegroup(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids, delgroups=groups, recurse=recurse, ctx=ctx, txn=txn)


	def __putrecord_setsecurity(self, recids=[], addusers=[], addlevel=0, addgroups=[], delusers=[], delgroups=[], umask=None, recurse=0, reassign=False, filt=True, ctx=None, txn=None):

		if not hasattr(recids,"__iter__"): recids = [recids]
		if not hasattr(addusers,"__iter__"): addusers = [addusers]
		if not hasattr(addgroups,"__iter__"): addgroups = [addgroups]
		if not hasattr(delusers,"__iter__"): delusers = [delusers]
		if not hasattr(delgroups,"__iter__"): delgroups = [delgroups]

		recids = set(recids)
		addusers = set(addusers)
		addgroups = set(addgroups)
		delusers = set(delusers)
		delgroups = set(delgroups)

		if not umask:
			umask = [[],[],[],[]]
			if addusers:
				umask[addlevel] = addusers

		addusers = set(reduce(operator.concat, umask, []))

		checkitems = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)

		if (addusers | addgroups | delusers | delgroups) - checkitems:
			raise subsystems.exceptions.SecurityError, "Invalid users/groups: %s"%((addusers | addgroups | delusers | delgroups) - checkitems)


		# change child perms
		if recurse:
			recids |= self.getchildren(recids, recurse=recurse, filt=True, flat=True, ctx=ctx, txn=txn)



		recs = self.getrecord(recids, filt=filt, ctx=ctx, txn=txn)
		if filt:
			recs = filter(lambda x:x.isowner(), recs)

		# g.log.msg('LOG_DEBUG', "setting permissions")

		for rec in recs:
			if addusers: rec.addumask(umask, reassign=reassign)
			if delusers: rec.removeuser(delusers)
			if addgroups: rec.addgroup(addgroups)
			if delgroups: rec.removegroup(delgroups)


		# Go ahead and directly commit here, since we know only permissions have changed...
		self.__commit_records(recs, [], onlypermissions=True, ctx=ctx, txn=txn)



	#############################
	# section: Rendering Record Views
	#############################


	@DBProxy.publicmethod
	def renderchildtree(self, recurse=None, recid=None, treedef=None, ctx=None, txn=None):
		"""Convenience method used by some clients to render a bunch of records and simple relationships"""
		
		if recurse:
			treedef = [None]*recurse

		init = set([recid])
		stack = [init]
		children = {}

		for x, rt in enumerate(treedef):
			current = stack[x]
			stack.append(set())
			for i in current:
				new = self.getchildren(i, rectype=rt, ctx=ctx, txn=txn)
				children[i] = new
				stack[x+1] |= new

		a = reduce(set.union, stack, set())
		rendered = self.renderview(a, viewtype="recname", ctx=ctx, txn=txn)
		rendered_path = {}
		
		for x, rt in enumerate(stack):
			for i in rt:
				tmp_path = rendered_path.get(i, [])
				for child in children.get(i, set()):
					rendered_path[child] = tmp_path + [child]

		return rendered, rendered_path, len(stack)
		
		


	# ian: todo: simple: deprecate: still used in a few places in the js. Convenience methods go outside core?
	@DBProxy.publicmethod
	def getrecordrecname(self, rec, returnsorted=0, showrectype=0, ctx=None, txn=None):
		"""Render the recname view for a record."""

		if not hasattr(rec, '__iter__'): rec = [rec]
		recs=self.getrecord(rec, filt=1, ctx=ctx, txn=txn)
		ret=self.renderview(recs,viewtype="recname", ctx=ctx, txn=txn)
		recs=dict([(i.recid,i) for i in recs])

		if showrectype:
			for k in ret.keys():
				ret[k]="%s: %s"%(recs[k].rectype,ret[k])

		if returnsorted:
			sl=[(k,recs[k].rectype+" "+v.lower()) for k,v in ret.items()]
			return [(k,ret[k]) for k,v in sorted(sl, key=operator.itemgetter(1))]

		return ret



	# ian: todo: hard: It is a cold, cold, cruel world... moved to VartypeManager. This should be refactored someday. Consider it a convenience method.
	# ed: ian, I think this should be moved back here.... it's not in the mission statement of the VartypeManager to do this kind of thing....
	@DBProxy.publicmethod
	def renderview(self, *args, **kwargs):
		"""Render views"""
		# calls out to places that expect DBProxy need a DBProxy...
		kwargs["db"] = kwargs["ctx"].db
		kwargs.pop("ctx",None)
		kwargs.pop("txn",None)
		vtm = subsystems.datatypes.VartypeManager()
		return vtm.renderview(*args, **kwargs)



	# ian: unused?
	# @DBProxy.publicmethod
	# def getrecordrenderedviews(self, recid, ctx=None, txn=None):
	# 	"""Render all views for a record."""
	#
	# 	rec = self.getrecord(recid, ctx=ctx, txn=txn)
	# 	recdef = self.getrecorddef(rec["rectype"], ctx=ctx, txn=txn)
	# 	views = recdef.views
	# 	views["mainview"] = recdef.mainview
	# 	for i in views:
	# 		views[i] = self.renderview(rec, viewdef=views[i], ctx=ctx, txn=txn)
	# 	return views



	###########################
	# section: backup / restore
	###########################



	# ian: ?
	def get_dbpath(self, tail):
		return os.path.join(self.path, tail)



	@DBProxy.publicmethod
	@DBProxy.adminmethod
	def archivelogs(self, ctx=None, txn=None):
		g.log.msg('LOG_INFO', "checkpointing")
		self.__dbenv.txn_checkpoint()
		archivefiles = self.__dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)
		archivepath = self.get_dbpath('archives')
		if not os.access(archivepath, os.F_OK):
			os.makedirs(archivepath)
		for file_ in archivefiles:
			# ian: changed to copy -- safer: it's better for it to be rename
			#shutil.copy(file_, os.path.join(archivepath, os.path.basename(file_)))
			os.rename(file_, os.path.join(archivepath, os.path.basename(file_)))

