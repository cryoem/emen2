from __future__ import with_statement

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

from DBFlags import *

DBENV = None


# Constants... move these to config file
MAXIDLE = 604800
DEBUG = 0


@atexit.register
def DB_Close():
	l = DB.opendbs.keys()
	for i in l:
		print i._DB__dbenv
		i.close()
	
	


def DB_syncall():
	"""This 'syncs' all open databases"""
	pass
	#for i in subsystems.btrees.BTree.alltrees.keys(): i.sync()



def DB_stat():

	global DBENV
	if not DBENV:
		return
		
	sys.stdout.flush()
	print >> sys.stderr, "DB has %d transactions left" % DB.txncounter

	tx_max = DBENV.get_tx_max()
	print "Open transactions: %s"%tx_max

	txn_stat = DBENV.txn_stat()
	print "Transaction stats: "
	for k,v in txn_stat.items():
		print "\t%s: %s"%(k,v)

	log_archive = DBENV.log_archive()
	print "Archive: %s"%log_archive

	lock_stat = DBENV.lock_stat()
	print "Lock stats: "
	for k,v in lock_stat.items():
		print "\t%s: %s"%(k,v)

	#print "Mutex max: "
	#print DBENV.mutex_get_max()






# This rmakes sure the database gets closed properly at exit
# atexit.register(DB_cleanup)









#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()
class DB(object):
		"""This class represents the database as a whole. There are 3 primary identifiers used in the database:
		4650 - Database id, a unique identifier for this database server
		recid - Record id, a unique (32 bit int) identifier for a particular record
		ctxid - A key for a database 'context' (also called a session), allows access for pre-authenticated user

		TODO : Probably should make more of the member variables private for slightly better security"""

		opendbs = weakref.WeakKeyDictionary()

		log_levels = {
			0: 'LOG_CRITICAL',
			1: 'LOG_CRITICAL',
			2: 'LOG_ERROR',
			3: 'LOG_WARNING',
			4: 'LOG_INFO',
			5: 'LOG_DEBUG',
			6: 'LOG_DEBUG',
			7: 'LOG_COMMIT',
			8: 'LOG_COMMIT_INDEX'
			}

		@staticmethod
		def init_vtm():
			import datatypes.core_vartypes
			import datatypes.core_macros
			import datatypes.core_properties


		def __init__(self, path=".", logfile="db.log", importmode=0, rootpw=None, recover=0, allowclose=True, more_flags=0):
			"""path - The path to the database files, this is the root of a tree of directories for the database
			cachesize - default is 64M, in bytes
			logfile - defualt "db.log"
			importmode - DANGEROUS, makes certain changes to allow bulk data import. Should be opened by only a single thread in importmode.
			recover - Only one thread should call this. Will run recovery on the environment before opening."""

			global ENVOPENFLAGS, USETXN

			if USETXN:
				self.newtxn = self.newtxn1
				ENVOPENFLAGS |= bsddb3.db.DB_INIT_TXN
			else:
				g.log.msg("LOG_INFO","Note: transaction support disabled")
				self.newtxn = self.newtxn2
			

			self.path = path or g.EMEN2DBPATH
			self.logfile = self.path + "/" + logfile
			self.lastctxclean = time.time()
			self.__importmode = importmode
			self.txnid = 0
			self.txnlog = {}

			self.init_vtm()
			self.vtm = subsystems.datatypes.VartypeManager()
			self.indexablevartypes = set([i.getvartype() for i in filter(lambda x:x.getindextype(), [self.vtm.getvartype(i) for i in self.vtm.getvartypes()])])
			self.unindexed_words = set(["in", "of", "for", "this", "the", "at", "to", "from", "at", "for", "and", "it", "or"])

			self.MAXRECURSE = 50
			self.BLOCKLENGTH = 100000
			
			if recover:
				ENVOPENFLAGS |= bsddb3.db.DB_RECOVER


			# This sets up a DB environment, which allows multithreaded access, transactions, etc.
			if not os.access(self.path + "/home", os.F_OK):
				os.makedirs(self.path + "/home")
				dbci = file(g.EMEN2ROOT+'/config/DB_CONFIG')
				dbco = file(self.path + '/home/DB_CONFIG', 'w')
				try:
					dbco.write(dbci.read())
				finally:
					[fil.close() for fil in (dbci, dbco)]


			if not os.access(self.path + "/security", os.F_OK):
				os.makedirs(self.path + "/security")

			if not os.access(self.path + "/index", os.F_OK):
				os.makedirs(self.path + "/index")

			self.__allowclose = bool(allowclose)


			# g.log.msg('LOG_INIT', "Database initialization started")

			global DBENV

			if DBENV == None:
				g.log.msg("LOG_INFO","Opening Database Environment")
				DBENV = bsddb3.db.DBEnv()
				DBENV.set_data_dir(self.path)
				DBENV.open(self.path+"/home", ENVOPENFLAGS)
				DB.opendbs[self] = 1

			self.__dbenv = DBENV

			print "cachemax"
			print self.__dbenv.get_cachesize()

			# ian: todo: is this method no longer in the bsddb3 API?
			#if self.__dbenv.failchk(flags=0):
			#	g.log.msg(1,"Database recovery required")
			#	sys.exit(1)

			# Open Database

			# Users
			# active database users / groups
			self.__users = subsystems.btrees.BTree("users", keytype="s", filename="security/users.bdb", dbenv=self.__dbenv)

			self.__groupsbyuser = subsystems.btrees.IndexKeyBTree("groupsbyuser", keytype="s", filename="security/groupsbyuser", dbenv=self.__dbenv)

			self.__groups = subsystems.btrees.BTree("groups", keytype="s", filename="security/groups.bdb", dbenv=self.__dbenv)
			#self.__updatecontexts = False

			# new users pending approval
			self.__newuserqueue = subsystems.btrees.BTree("newusers", keytype="s", filename="security/newusers.bdb", dbenv=self.__dbenv)

			# multisession persistent contexts
			self.__contexts_p = subsystems.btrees.BTree("contexts", keytype="s", filename="security/contexts.bdb", dbenv=self.__dbenv)

			# local cache dictionary of valid contexts
			self.__contexts = {}




			# Binary data names indexed by date
			self.__bdocounter = subsystems.btrees.BTree("BinNames", keytype="s", filename="BinNames.bdb", dbenv=self.__dbenv)

			# Defined ParamDefs
			# ParamDef objects indexed by name
			self.__paramdefs = subsystems.btrees.RelateBTree("ParamDefs", keytype="s", filename="ParamDefs.bdb", dbenv=self.__dbenv)

			# Defined RecordDefs
			# RecordDef objects indexed by name
			self.__recorddefs = subsystems.btrees.RelateBTree("RecordDefs", keytype="s", filename="RecordDefs.bdb", dbenv=self.__dbenv)



			# The actual database, keyed by recid, a positive integer unique in this DB instance
			# ian todo: check this statement:
			# 2 special keys exist, the record counter is stored with key -1
			# and database information is stored with key=0

			# The actual database, containing id referenced Records
			self.__records = subsystems.btrees.RelateBTree("database", keytype="d", filename="database.bdb", dbenv=self.__dbenv)

			# Indices

			# index of records each user can read
			self.__secrindex = subsystems.btrees.FieldBTree("secrindex", filename="security/roindex.bdb", keytype="s", dbenv=self.__dbenv)
			self.__secrindex_groups = subsystems.btrees.FieldBTree("secrindex", filename="security/groindex.bdb", keytype="s", dbenv=self.__dbenv)

			# index of records belonging to each RecordDef
			self.__recorddefindex = subsystems.btrees.FieldBTree("RecordDefindex", filename="RecordDefindex.bdb", keytype="s", dbenv=self.__dbenv)

			# key=record id, value=last time record was changed
			# ian: todo: to simplify, just handle this through modifytime param...
			self.__timeindex = subsystems.btrees.BTree("TimeChangedindex", keytype="d", filename="TimeChangedindex.bdb", dbenv=self.__dbenv)

			# dictionary of FieldBTrees, 1 per ParamDef, not opened until needed
			self.__fieldindex = {}


			# This should be rebuilt after restore
			self.__indexkeys = None
			if not self.__importmode:
				_rebuild = False
				if not os.path.exists(self.path+"/IndexKeys.bdb"):
					_rebuild = True
				self.__indexkeys = subsystems.btrees.IndexKeyBTree("IndexKeys", keytype="s", filename="IndexKeys.bdb", dbenv=self.__dbenv)




			# Workflow database, user indexed btree of lists of things to do
			# again, key -1 is used to store the wfid counter
			self.__workflow = subsystems.btrees.BTree("workflow", keytype="d", filename="workflow.bdb", dbenv=self.__dbenv)


			# USE OF SEQUENCES DISABLED DUE TO DATABASE LOCKUPS
			#db sequence
			# self.__dbseq = self.__records.create_sequence()


			txn = self.newtxn()
			ctx = self.__makerootcontext(txn=txn)

			try:

				try:
					maxr = self.__records.sget(-1, txn=txn)
					# g.log.msg("LOG_INFO","Opened database with %s records"%maxr)
				except KeyError:
					g.log.msg('LOG_INFO', "Initializing skeleton database")
					self.__createskeletondb(ctx=ctx, txn=txn)

				#if _rebuild:
				#	self.__rebuild_indexkeys(txn=txn)


			except Exception, inst:
				print inst					
				self.txnabort(txn=txn)
			
			self.txncommit(txn=txn)

			g.log.add_output(self.log_levels.values(), file(self.logfile, "a"))








		def __createskeletondb(self, ctx=None, txn=None):
			# typically uses SpecialRootContext

			self.__records.set(-1, 0, txn=txn)
			
			import skeleton

			for i in skeleton.core_paramdefs.items:
				self.putparamdef(i, ctx=ctx, txn=txn)

			for i in skeleton.core_recorddefs.items:
				self.putrecorddef(i, ctx=ctx, txn=txn)

			for i in skeleton.core_users.items:
				if self.__importmode:
					i["signupinfo"] = None
				self.adduser(i, ctx=ctx, txn=txn)

			for i in skeleton.core_groups.items:
				self.putgroup(i, ctx=ctx, txn=txn)

			self.setpassword("root", g.ROOTPW, g.ROOTPW, ctx=ctx, txn=txn)






		###############################
		# section: txn
		###############################



		txncounter = 0
		# one of these 2 methods (newtxn1/newtxn2) is mapped to self.newtxn()
		def newtxn1(self, parent=None, ctx=None):
			g.log.msg("LOG_INFO","\n\nNEW TXN, PARENT --> %s"%parent)
			txn = self.__dbenv.txn_begin(parent=parent)
			try:
				type(self).txncounter += 1
				self.txnlog[id(txn)] = txn
			except:
				self.txnabort(ctx=ctx, txn=txn)
				raise
			return txn


		def newtxn2(self, ctx=None, txn=None):
			return None


		def newtxn(self, ctx=None, txn=None):
			return None




		def txncheck(self, ctx=None, txn=None):
			if not txn:
				txn = self.newtxn(ctx=ctx)
			return txn


		def txnabort(self, txnid=0, ctx=None, txn=None):
			g.log.msg('LOG_ERROR', "TXN ABORT --> %s\n\n"%txn)
			txn = self.txnlog.get(txnid, txn)

			if txn:
				txn.abort()
				if id(txn) in self.txnlog:
					del self.txnlog[id(txn)]
				type(self).txncounter -= 1
			else:
				raise ValueError, 'transaction not found'


		def txncommit(self, txnid=0, ctx=None, txn=None):
			g.log.msg("LOG_INFO","TXN COMMIT --> %s\n\n"%txn)
			txn = self.txnlog.get(txnid, txn)

			if txn != None:
				txn.commit()
				if id(txn) in self.txnlog:
					del self.txnlog[id(txn)]
				type(self).txncounter -= 1
								
			else:
				raise ValueError, 'transaction not found'




		###############################
		# section: utility
		###############################


		@DBProxy.publicmethod
		def raise_exception(self, ctx=None, txn=None):
			raise Exception, "Test! ctxid %s host %s txn %s"%(ctx.ctxid, ctx.host, txn)


		def LOG(self, level, message, ctx=None, txn=None):
			txn = txn or 1
			if type(level) is int and (level < 0 or level > 7):
				level = 6
			try:
				g.log.msg(self.log_levels.get(level, level), "%s: (%s) %s" % (self.gettime(ctx=ctx,txn=txn), self.log_levels.get(level, level), message))
			except:
				traceback.print_exc(file=sys.stdout)
				g.log.msg('LOG_CRITICAL', "Critical error!!! Cannot write log message to '%s'")


		# needs txn?
		def __str__(self):
			"""Try to print something useful"""
			return "Database %d records\n( %s )"%(int(self.__records.get(-1,0)), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))


		# needs txn?
		def __del__(self):
			print "del!"
			self.close()


		# ian: todo
		def close(self):
			print "Closing %d BDB databases"%(len(subsystems.btrees.BTree.alltrees))
			try:
				for i in subsystems.btrees.BTree.alltrees.keys():
					sys.stderr.write('closing %s\n' % unicode(i))
					i.close()
			except Exception, inst:
				print inst

			self.__dbenv.close()

			# if self.__allowclose == True:
			# 	for btree in self.__dict__.values():
			# 		if getattr(btree, '__class__', object).__name__.endswith('BTree'):
			# 			try: btree.close()
			# 			except bsddb3.db.InvalidArgError, e: g.log.msg('LOG_ERROR', e)
			# 		for btree in self.__fieldindex.values(): btree.close()



		# ian: this can be slow; reconsider use
		# from: http://basicproperty.sourceforge.net
		# ian: remove this sometime... reduce(operator.concat) works better
		def __flatten(self, l, ltypes=(set, list, tuple)):
			ltype = type(l)
			l = list(l)
			i = 0
			while i < len(l):
				while isinstance(l[i], ltypes):
					if not l[i]:
						l.pop(i)
						i -= 1
						break
					else:
						l[i:i + 1] = l[i]
				i += 1
			return ltype(l)




		@DBProxy.publicmethod
		def gettime(self, ctx=None, txn=None):
			return subsystems.dbtime.gettime()




		###############################
		# section: login / passwords
		###############################

		def __makecontext(self, username="anonymous", host=None, ctx=None, txn=None):
			'''so we can simulate a context for approveuser'''

			if username == "anonymous":
				ctx = dataobjects.context.AnonymousContext(host=host)
			else:
				ctx = dataobjects.context.Context(username=username, host=host)

			#def refresh(self, user=None, groups=None, db=None, txn=None):
			#context.refresh(user=user, groups=groups, db=self, txn=txn)
			#ctx.setdb(db=self, txn=txn)
			#ctx.refresh(db=self, txn=txn)
			return ctx


		def __makerootcontext(self, ctx=None, txn=None):
			ctx = dataobjects.context.SpecialRootContext()
			ctx.refresh(db=self, txn=txn)

			return ctx



		# No longer public method; only through DBProxy to force host=...
		def _login(self, username="anonymous", password="", host=None, maxidle=MAXIDLE, ctx=None, txn=None):
			"""Logs a given user in to the database and returns a ctxid, which can then be used for
			subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""

			newcontext = None
			username = unicode(username)

			# Anonymous access
			if username == "anonymous":
				newcontext = self.__makecontext(host=host, ctx=ctx, txn=txn)

			else:
				checkpass = self.__checkpassword(username, password, ctx=ctx, txn=txn)

				# Admins can "su"
				if checkpass:
					newcontext = self.__makecontext(username=username, host=host, ctx=ctx, txn=txn)

				else:
					g.log.msg('LOG_ERROR', "Invalid password: %s (%s)" % (username, host))
					raise subsystems.exceptions.AuthenticationError, subsystems.exceptions.AuthenticationError.__doc__

			try:
				self.__setcontext(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
				g.log.msg('LOG_INFO', "Login succeeded %s (%s)" % (username, newcontext.ctxid))

			except:
				g.log.msg('LOG_ERROR', "Error writing login context, txn aborting!")
				raise


			return newcontext.ctxid




		# Logout is the same as delete context
		@DBProxy.publicmethod
		def logout(self, ctx=None, txn=None):
			self.deletecontext(ctx=ctx, txn=txn)



		def __checkpassword(self, username, password, ctx=None, txn=None):
			"""Check password against stored hash value"""

			s = hashlib.sha1(password)

			try:
				user = self.__users.sget(username, txn=txn)
			except:
				raise subsystems.exceptions.AuthenticationError, subsystems.exceptions.AuthenticationError.__doc__

			if user.disabled:
				raise subsystems.exceptions.DisabledUserError, subsystems.exceptions.DisabledUserError.__doc__ % username

			return s.hexdigest() == user.password



		###############################
		# section: contexts
		###############################


		#@txn
		@DBProxy.publicmethod
		def deletecontext(self, ctx=None, txn=None):
			"""Delete a context/Logout user. Returns None."""
			if ctx:	self.__setcontext(ctx.ctxid, None, ctx=ctx, txn=txn)



		# ian: change so all __setcontext calls go through same txn
		def __cleanupcontexts(self, ctx=None, txn=None):
			"""This should be run periodically to clean up sessions that have been idle too long. Returns None."""
			self.lastctxclean = time.time()

			# ian: todo: fix!!!!!!
			return

			for ctxid, context in self.__contexts_p.items():
				# use the cached time if available
				try:
					c = self.__contexts.sget(ctxid, txn=txn) #[ctxid]
					context.time = c.time
				except:
					pass

				if context.time + (context.maxidle or 0) < time.time():
					g.log("Expire context (%s) %d" % (context.ctxid, time.time() - context.time))
					self.__setcontext(context.ctxid, None, ctx=ctx, txn=txn)



		#@write #self.__contexts_p
		def __setcontext(self, ctxid, context, ctx=None, txn=None):
			"""Add or delete context"""

			#@begin
			
			# any time you set the context, delete the cached context
			# this will retrieve it from disk next time it's needed			
			if self.__contexts.get(ctxid):
				del self.__contexts[ctxid]			

			# set context
			if context != None:

				try:
					g.log.msg("LOG_COMMIT","self.__contexts_p.set: %r"%context.ctxid)
					self.__contexts_p.set(ctxid, context, txn=txn)

				except Exception, inst:
					g.log.msg("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst))
					raise


			# delete context
			else:

				try:
					g.log.msg("LOG_COMMIT","self.__contexts_p.__delitem__: %r"%ctxid)
					self.__contexts_p.set(ctxid, None, txn=txn) #del ... [ctxid]

				except Exception, inst:
					g.log.msg("LOG_CRITICAL","Unable to delete persistent context %s (%s)"%(ctxid, inst))
					raise

			#@end



		def __periodic_operations(self, ctx=None, txn=None):
			t = subsystems.dbtime.gettime()
			
			# maybe not the perfect place to do this, but it will have to do
			if (t > self.lastctxclean + 600):
				self.__cleanupcontexts(ctx=ctx, txn=txn)


		def _getcontext(self, ctxid, host, ctx=None, txn=None):
			"""Takes a ctxid key and returns a context (for internal use only)
			Note that both key and host must match. Returns context instance."""

			self.__periodic_operations(ctx=ctx, txn=txn)

			if ctxid:
				context = self.__contexts.get(ctxid) or self.__contexts_p.get(ctxid, txn=txn)
			else:
				context = self.__makecontext(host=host, ctx=ctx, txn=txn)
			
			if not context:
				g.log.msg('LOG_ERROR', "Session expired: %s"%ctxid)
				raise subsystems.exceptions.SessionError, "Session expired: %s"%(ctxid)
							

			# ian: todo: this is a kindof circular problem, think about better ways to solve it. 
			user = self.__users.get(context.username, None, txn=txn)
			groups = self.__groupsbyuser.get(context.username, set(), txn=txn)
			context.refresh(user=user, groups=groups, db=self, txn=txn)

			self.__contexts[ctxid] = context
			
			return context



		@DBProxy.publicmethod
		def checkcontext(self, ctx=None, txn=None):
			"""This allows a client to test the validity of a context, and
			get basic information on the authorized user and his/her permissions"""
			try:
				return (ctx.username, ctx.groups)
			except:
				return None, None


		@DBProxy.publicmethod
		def checkadmin(self, ctx=None, txn=None):
			"""Checks if the user has global write access. Returns bool."""
			if ctx: return ctx.checkadmin()



		@DBProxy.publicmethod
		def checkreadadmin(self, ctx=None, txn=None):
			"""Checks if the user has global read access. Returns bool."""
			if ctx: return ctx.checkreadadmin()



		@DBProxy.publicmethod
		def checkcreate(self, ctx=None, txn=None):
			"""Check for permission to create records. Returns bool."""
			if ctx: return ctx.checkcreate()





		###############################
		# section: binaries
		###############################

		@DBProxy.publicmethod
		def newbinary(self, *args, **kwargs):
			raise Exception, "Deprecated; use putbinary"




		#@txn
		#@write #self.__bdocounter
		@DBProxy.publicmethod
		def putbinary(self, filename, recid, key=None, filedata=None, param=None, uri=None, ctx=None, txn=None):
			"""Get a storage path for a new binary object. Must have a
			recordid that references this binary, used for permissions. Returns a tuple
			with the identifier for later retrieval and the absolute path"""


			if not filename:
				raise ValueError, "Filename may not be 'None'"

			if key and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admins may manipulate binary tree directly"

			#if not validate and not ctx.checkadmin():
			#	raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"

			# ian: todo: acquire lock?
			rec = self.getrecord(recid, ctx=ctx, txn=txn)

			if not rec.writable():
				raise subsystems.exceptions.SecurityError, "Write permission needed on referenced record."


			bdoo = self.__putbinary(filename, recid, key=key, uri=uri, ctx=ctx, txn=txn)


			if not param:
				param = "file_binary"

			param = self.getparamdef(param, ctx=ctx, txn=txn)

			if param.vartype == "binary":
				v = rec.get(param.name) or []
				v.append("bdo:"+bdoo.get("name"))
				rec[param.name]=v

			elif param.vartype == "binaryimage":
				rec[param.name]="bdo:"+bdoo.get("name")

			else:
				raise Exception, "Error: invalid vartype for binary: parameter %s, vartype is %s"%(param.name, param.vartype)

			self.putrecord(rec, warning=1, ctx=ctx, txn=txn)



			if filedata != None:
				self.__putbinary_file(bdoo.get("name"), filedata, ctx=ctx, txn=txn)


			return bdoo



		def __putbinary(self, filename, recid, key=None, uri=None, ctx=None, txn=None):
			# fetch BDO day dict, add item, and commit

			date = self.gettime(ctx=ctx, txn=txn)

			if not key:
				year = int(date[:4])
				mon = int(date[5:7])
				day = int(date[8:10])
				newid = None
			else:
				date=unicode(key)
				year=int(date[:4])
				mon=int(date[4:6])
				day=int(date[6:8])
				newid=int(date[9:13],16)

			datekey = "%04d%02d%02d" % (year, mon, day)


			# uri is for files copied from an external source, similar to records, paramdefs, etc.


			#@begin

			# bdo items are stored one bdo per day
			# key is sequential item #, value is (filename, recid)

			# ian: todo: will this lock prevent others from overwriting new items?
			# acquire RMW lock to prevent others from editing...
			bdo = self.__bdocounter.get(datekey, txn=txn, flags=RMWFLAGS) or {}

			if newid == None:
				newid = max(bdo.keys() or [-1]) + 1


			if bdo.get(newid) and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin may overwrite existing BDO"


			nb = dataobjects.binary.Binary()
			nb["uri"] = uri
			nb["filename"] = filename
			nb["recid"] = recid
			nb["creator"] = ctx.username
			nb["creationtime"] = self.gettime()
			nb["name"] = datekey + "%05X"%newid

			bdo[newid] = nb #(filename, recid, uri)

			g.log.msg("LOG_COMMIT","self.__bdocounter.set: %s"%datekey)
			self.__bdocounter.set(datekey, bdo, txn=txn)

			#@end

			#return (bdo, filename)
			#return (key + "%05X" % newid, path + "/%05X" % newid)

			#return datekey + "%05X"%newid
			return nb



		def __putbinary_file(self, bdokey, filedata="", ctx=None, txn=None):

			date = unicode(bdokey)
			year = int(date[:4])
			mon = int(date[4:6])
			day = int(date[6:8])
			newid = int(date[9:13],16)

			datekey = "%04d%02d%02d"% (year, mon, day)

			bp = dict(zip(g.BINARYPATH_KEYS, g.BINARYPATH_VALUES))
			basepath = bp[filter(lambda x:x<=datekey, sorted(bp.keys()))[-1]]

			filepath = "%s/%04d/%02d/%02d" % (basepath, year, mon, day)
			g.log.msg("LOG_DEBUG","Filepath for binary bdokey %s is %s"%(bdokey, filepath))

			#for i in /BINARYPATH:
			#	if datekey >= i[0] and datekey < i[1]:
			#		# actual storage path
			#		filepath = "%s/%04d/%02d/%02d" % (i[2], year, mon, day)
			#		g.log.msg("LOG_DEBUG","Filepath for binary bdokey %s is %s"%(bdokey, filepath))
			#		break
			#else:
			#	raise KeyError, "No storage specified for date %s" % key


			# try to make sure the directory exists
			try:
				os.makedirs(filepath)
			except:
				pass


			filename = filepath + "/%05X"%newid
			g.log.msg("LOG_DEBUG","filename is %s"%filename)

			#todo: ian: raise exception if overwriting existing file (but this should never happen unless the file was pre-existing?)
			if os.access(filename, os.F_OK) and not ctx.checkadmin():
				# should be a different exception class, this particular one seems irrevelant as it is not really a security
				# but an integrity problem.
				raise subsystems.exceptions.SecurityError, "Error: Binary data storage, attempt to overwrite existing file '%s'"
				#g.log.msg('LOG_INFO', "Binary data storage: overwriting existing file '%s'" % (path + "/%05X" % newid))


			# if a filedata is supplied, write it out...
			# todo: use only this mechanism for putting files on disk
			g.log.msg('LOG_INFO', "Writing %s bytes disk: %s"%(len(filedata),filename))
			f=open(filename,"wb")
			f.write(filedata)
			f.close()

			return True




		def __parsebdokey(self, key):
			# for bdo: protocol
			# validate key
			year = int(key[:4])
			mon = int(key[4:6])
			day = int(key[6:8])
			bid = int(key[8:], 16)
			key = "%04d%02d%02d" % (year, mon, day)			
			return [year, mon, day, bid], key


		@DBProxy.publicmethod
		def getbinary(self, idents, filt=True, vts=None, params=None, ctx=None, txn=None):
			"""Get a storage path for an existing binary object. Returns the
			object name and the absolute path"""

			# process idents argument for bids (into list bids) and then process bids
			ret = {}
			bids = []
			recs = []

			if not vts:
				vts = ["binary","binaryimage"]

			ol=0
			if isinstance(idents,basestring):# or not hasattr(idents,"__iter__"):
				ol=1
				bids = [idents]
				idents = bids
			if isinstance(idents,(int,dataobjects.record.Record)):
				idents = [idents]


			bids.extend(filter(lambda x:isinstance(x,basestring), idents))

			recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), idents), filt=1, ctx=ctx, txn=txn))
			recs.extend(filter(lambda x:isinstance(x,dataobjects.record.Record), idents))

			# ian: todo: speed this up some..
			if recs:
				bids.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))

			bids = filter(lambda x:isinstance(x, basestring), bids)

			# keyed by recid
			byrec = collections.defaultdict(set)

			for ident in bids:
				prot, _, key = ident.rpartition(":")
				if prot == "":
					prot = "bdo"
					
				# ian: todo: implement other BDO protocols, e.g. references to uris	
				if prot not in ["bdo"]:
					if filt:
						continue
					else:
						raise Exception, "Invalid binary storage protocol: %s"%prot

				# validate key
				(year, mon, day, bid), key = self.__parsebdokey(key)

				try:
					# ian: todo: clean this up... see also putbinary
					bp = dict(zip(g.BINARYPATH_KEYS, g.BINARYPATH_VALUES))
					basepath = bp[filter(lambda x:x<=key, sorted(bp.keys()))[-1]]

					path = "%s/%04d/%02d/%02d" % (basepath, year, mon, day)
					g.log.msg("LOG_DEBUG","Filepath for binary bdokey %s is %s"%(key, path))

				except:
					raise KeyError, "No storage specified for date %s"%key



				try:
						bdo = self.__bdocounter.sget(key, txn=txn)[bid] #[key][bid]
				except:
						if filt:
							continue
						else:
							raise KeyError, "Unknown identifier %s" % ident
						
						
				# ian: finish this filtering...
				byrec[bdo.get("recid")].add(bdo)


				try:
					self.getrecord(bdo.get("recid"), filt=False, ctx=ctx, txn=txn)
					bdo["filepath"] = path+"/%05X"%bid
					ret[ident] = bdo
					#(name, path + "/%05X" % bid, recid)

				except:
					if filt:
						continue
					else:
						raise subsystems.exceptions.SecurityError, "Not authorized to access %s(%0d)" % (ident, recid)


			if len(ret)==1 and ol:
				return ret.values()[0]
			return ret



		@DBProxy.publicmethod
		def getbinarynames(self, ctx=None, txn=None):
			"""Returns a list of tuples which can produce all binary object
			keys in the database. Each 2-tuple has the date key and the nubmer
			of objects under that key. A somewhat slow operation."""

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "getbinarynames not available to anonymous users"

			ret = self.__bdocounter.keys(txn=txn)
			ret = [(i, len(self.__bdocounter.get(i, txn=txn))) for i in ret]
			return ret





		###############################
		# section: query
		###############################


		@DBProxy.publicmethod
		def query(self, q=None, rectype=None, boolmode="AND", ignorecase=True, constraints=None, childof=None, parentof=None, recurse=False, subset=None, recs=None, returnrecs=False, byvalue=False, ctx=None, txn=None):
			
			if boolmode == "AND":
				boolmode = set.intersection
			elif boolmode == "OR":
				boolmode = set.union
			else:
				raise Exception, "Invalid boolean mode: %s. Must be AND, OR"%boolmode
				
			if recurse:
				recurse = self.MAXRECURSE

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
			
			#print "Query constraints:"
			#print constraints

			if subset:
				s, subsets_by_value = self.__query_recs(constraints, cmps=cmps, subset=subset, ctx=ctx, txn=txn)
			else:
				s, subsets_by_value = self.__query_index(constraints, cmps=cmps, subset=subset, ctx=ctx, txn=txn)

			subsets.extend(s)

			ret = reduce(boolmode, subsets)


			#print "stage 3 results"
			#print ret

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

			vtm = subsystems.datatypes.VartypeManager()
			subsets = []
			subsets_by_value = {}

			# nested dictionary, results[constraint position][param]
			results = collections.defaultdict(partial(collections.defaultdict, set))

			# stage 1: search __indexkeys
			for count,c in enumerate(constraints):
				if c[0] == "*":
					for param, pkeys in self.__indexkeys.items(txn=txn):

						# validate for each param for correct vartype matching
						try:
							cargs = vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
						except (ValueError, KeyError):
							continue

						comp = partial(cmps[c[1]], cargs) #*cargs
						results[count][param] = set(filter(comp, pkeys))

				else:
					param = c[0]
					pkeys = self.__indexkeys.get(param, txn=txn) or []
					cargs = vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
					comp = partial(cmps[c[1]], cargs) #*cargs
					results[count][param] = set(filter(comp, pkeys))


			#print "stage 1 results"
			#print results

			# stage 2: search individual param indexes
			for count, r in results.items():
				constraint_matches = set()

				for param, matchkeys in filter(lambda x:x[0] and x[1] != None, r.items()):
					#print "======="
					#print param
					#print matchkeys
					ind = self.__getparamindex(param, ctx=ctx, txn=txn)
					for matchkey in matchkeys:
						m = ind.get(matchkey, txn=txn)
						if m:
							subsets_by_value[(param, matchkey)] = m
							constraint_matches |= m
					
				subsets.append(constraint_matches)

			#print "stage 2 results"
			#print subsets
			#print subsets_by_value

			return subsets, subsets_by_value
		


		def __query_recs(self, constraints, cmps=None, subset=None, ctx=None, txn=None):

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
					allparams = set(reduce(operator.concat, [rec.getparamkeys() for rec in recs]))
					for param in allparams:
						try:
							cargs = vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
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
					cargs = vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
					m = set([x.recid for x in filter(lambda rec:cc(cargs, rec.get(param)), recs)])
					if m:
						subsets_by_value[(param, cargs)] = m
						cresult.extend(m)


				if cresult:
					subsets.append(cresult)

			#g.log(subsets)
			return subsets, subsets_by_value





		#@DBProxy.publicmethod
		#def buildindexkeys(self, txn=None):
		def __rebuild_indexkeys(self, ctx=None, txn=None):

			inds = dict(filter(lambda x:x[1]!=None, [(i,self.__getparamindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

			g.log.msg("LOG_COMMIT_INDEX","self.__indexkeys.truncate")
			self.__indexkeys.truncate(txn=txn)

			for k,v in inds.items():
				g.log.msg("LOG_COMMIT_INDEX", "self.__indexkeys: rebuilding params %s"%k)
				self.__indexkeys.set(k, set(v.keys()), txn=txn)



		@DBProxy.publicmethod
		def searchindexkeys(self, q=None, ignorecase=1, params=None, ctx=None, txn=None):
			"""Deprecated; use query"""
			if not q:
				return {}

			q = unicode(q)
			if ignorecase:
				q = q.lower()
				matcher = lambda x:q in unicode(x).lower()
			else:
				matcher = lambda x:q in unicode(x)

			matches = {}


			for k,v in self.__indexkeys.items(txn=txn):
				r = filter(matcher, v)
				if r: matches[k] = r

			matches2 = []

			for k,v in matches.items():
				paramindex = self.__getparamindex(k, ctx=ctx, txn=txn)
				for i in v:
					j = paramindex.get(i, txn=txn)
					for x in j:
						matches2.append((x, k, i))





		#########################
		# section: indexes
		#########################



		@DBProxy.publicmethod
		def getindexbyrecorddef(self, recdefname, ctx=None, txn=None):
			"""Uses the recdefname keyed index to return all
			records belonging to a particular RecordDef as a set. Currently this
			is unsecured, but actual records cannot be retrieved, so it
			shouldn't pose a security threat."""
			if isinstance(recdefname, basestring):
				recdefname = [recdefname]
			ret = set()
			for i in recdefname:	
			 	ret |= self.__recorddefindex.get(i, txn=txn) or set()
			return ret



		@DBProxy.publicmethod
		def getindexbyuser(self, username, ctx=None, txn=None):
			"""This will use the user keyed record read-access index to return
			a list of records the user can access. DOES NOT include that user's groups.
			Use getindexbycontext if you want to see all recs you can read."""

			if username == None:
				username = ctx.username

			if ctx.username != username and not ctx.checkreadadmin():
				raise subsystems.exceptions.SecurityError, "Not authorized to get record access for %s" % username

			return self.__secrindex.get(username, set(), txn=txn)



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




		# ian: todo: finish..
		@DBProxy.publicmethod
		def getparamstatistics(self, paramname, ctx=None, txn=None):

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "Not authorized to retrieve parameter statistics"

			try:
				paramindex = self.__getparamindex(paramname, create=0, ctx=ctx, txn=txn)
				return (len(paramindex.keys(txn=txn)), len(paramindex.values(txn=txn)))
			except:
				return (0,0)


		# @DBProxy.adminmethod
		# ian: disabled for security reasons (it returns all values with no security check...)
		def getindexkeys(self, paramname, valrange=None, ctx=None, txn=None):
			return None
			#		 """For numerical & simple string parameters, this will locate all
			#		 parameter values in the specified range.
			#		 valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""
			#		 ind=self.__getparamindex(paramname,create=0)
			#
			#		 if valrange==None : return ind.keys()
			#		 elif isinstance(valrange,tuple) or isinstance(valrange,list) : return ind.keys(valrange[0],valrange[1])
			#		 elif ind.has_key(valrange): return valrange
			#		 return None




		# ian todo: add unit support.
		@DBProxy.publicmethod
		def getindexbyvalue(self, paramname, valrange=None, ctx=None, txn=None):
			"""For numerical & simple string parameters, this will locate all records
			with the specified paramdef in the specified range.
			valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""

			paramindex = self.__getparamindex(paramname, ctx=ctx, txn=txn)
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
		def getindexdictbyvalue(self, paramname, valrange=None, subset=None, ctx=None, txn=None):
			"""For numerical & simple string parameters, this will locate all records
			with the specified paramdef in the specified range.
			valrange may be a None (matches all), a single value, or a (min,max) tuple/list.
			This method returns a dictionary of all matching recid/value pairs
			if subset is provided, will only return values for specified recids"""



			paramindex = self.__getparamindex(paramname, ctx=ctx, txn=txn)
			if paramindex == None:
				return {}

			if valrange == None:
				r = dict(paramindex.items(txn=txn))
			else:
				r = dict(paramindex.items(valrange[0], valrange[1], txn=txn))
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




		@DBProxy.publicmethod
		def getindexbycontext(self, ctx=None, txn=None):
			"""This will return the ids of all records a context has permission to access as a set. Does include groups."""


			if ctx.checkreadadmin():
				return set(range(self.__records.sget(-1, txn=txn))) #+1)) # Ed: Fixed an off by one error

			ret = set(self.__secrindex.get(ctx.username, set(), txn=txn)) #[ctx.username]

			for group in sorted(ctx.groups,reverse=True):
				ret |= set(self.__secrindex_groups.get(group, set(), txn=txn))#[group]

			return ret




		# ian: todo: return dictionary instead of list?
		@DBProxy.publicmethod
		def getrecordschangetime(self, recids, ctx=None, txn=None):
			"""Returns a list of times for a list of recids. Times represent the last modification
			of the specified records"""
			raise Exception, "Temporarily deprecated"
			# recids = self.filterbypermissions(recids, ctx=ctx, txn=txn)
			# 
			# if len(rid) > 0:
			# 	raise Exception, "Cannot access records %s" % unicode(rid)
			# 
			# try:
			# 	ret = [self.__timeindex.sget(i, txn=txn) for i in recids]
			# except:
			# 	raise Exception, "unindexed time on one or more recids"
			# 
			# return ret




		#########################
		# section: groupby
		#########################


		# ian: todo: better way to decide which grouping mechanism to use
		@DBProxy.publicmethod
		def groupbyrecorddef(self, recids, optimize=True, ctx=None, txn=None):
			"""This will take a set/list of record ids and return a dictionary of ids keyed
			by their recorddef"""

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




		# ian: unused?
		@DBProxy.publicmethod
		def groupby(self, records, param, ctx=None, txn=None):
			"""This will group a list of record numbers based on the value of 'param' in each record.
			Records with no defined value will be grouped under the special key None. It would be a bad idea
			to, for example, groupby 500,000 records by a float parameter with a different value for each
			record. It will do it, but you may regret asking.

			We really need 2 implementations here (as above), one using indices for large numbers of records and
			another using record retrieval for small numbers of records"""
			r = {}
			for i in records:
				try:
					j = self.getrecord(i, ctx=ctx, txn=txn)
				except:
					continue
				#try:
				k = j[param]
				#except: k=None
				if r.has_key(k):
					r[k].append(i)
				else:
					r[k] = [i]
			return r



		# ian: unused?
		@DBProxy.publicmethod
		def groupbyparentoftype(self, records, parenttype, recurse=3, ctx=None, txn=None):
			"""This will group a list of record numbers based on the recordid of any parents of
			type 'parenttype'. within the specified recursion depth. If records have multiple parents
			of a particular type, they may be multiply classified. Note that due to large numbers of
			recursive calls, this function may be quite slow in some cases. There may also be a
			None category if the record has no appropriate parents. The default recursion level is 3."""

			r = {}
			for i in records:
				try:
					p = self.getparents(i, recurse=recurse, ctx=ctx, txn=txn)
				except:
					continue
				try:
					k = [ii for ii in p if self.getrecord(ii, ctx=ctx, txn=txn).rectype == parenttype]
				except:
					k = [None]
				if len(k) == 0:
					k = [None]

				for j in k:
					if r.has_key(j):
						r[j].append(i)
					else:
						r[j] = [i]

			return r




		###############################
		# section: relationships
		###############################


		# ian: unused?
		@DBProxy.publicmethod
		def countchildren(self, key, recurse=1, ctx=None, txn=None):
			"""Unlike getchildren, this works only for 'records'. Returns a count of children
			of the specified record classified by recorddef as a dictionary. The special 'all'
			key contains the sum of all different recorddefs"""

			c = self.getchildren(key, "record", recurse=recurse, ctx=ctx, txn=txn)
			r = self.groupbyrecorddef(c, ctx=ctx, txn=txn)
			for k in r.keys(): r[k] = len(r[k])
			r["all"] = len(c)
			return r



		@DBProxy.publicmethod
		def getchildren(self, key, keytype="record", recurse=1, rectype=None, filt=False, flat=False, tree=False, ctx=None, txn=None):
			"""Get children;
			keytype: record, paramdef, recorddef
			recurse: recursion depth
			rectype: for records, return only children of type rectype
			filt: filt by permissions
			tree: return results in graph format; default is set format
			"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", filt=filt, flat=flat, tree=tree, ctx=ctx, txn=txn)



		@DBProxy.publicmethod
		def getparents(self, key, keytype="record", recurse=1, rectype=None, filt=False, flat=False, tree=False, ctx=None, txn=None):
			"""see: getchildren"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", filt=filt, flat=flat, tree=tree, ctx=ctx, txn=txn)



		# wraps getrel / works as both getchildren/getparents
		@DBProxy.publicmethod
		def __getrel_wrapper(self, key, keytype="record", recurse=1, rectype=None, rel="children", filt=False, tree=False, flat=False, ctx=None, txn=None):
			"""Add some extra features to __getrel"""

			ol = 0
			if not hasattr(key,"__iter__"):
				ol = 1
				key = [key]
			
			# ian: todo: fix everything else to make recurse=1 by default..
			if recurse == 0:
				recurse = 1
			
			# ret is a two-level dictionary
			# k1 = input recids
			# k2 = recid and v2 = children of k2
			ret = {}
			ret_visited = {}

			for i in key:
				ret[i], ret_visited[i] = self.__getrel(key=i, keytype=keytype, recurse=recurse, rel=rel, ctx=ctx, txn=txn)
			

			if rectype or filt or flat:
				# ian: note: use a [] initializer for reduce to prevent exceptions when values is empty
				allr = reduce(set.union, ret_visited.values())

				if rectype:
					allr &= self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn)
		
				if filt and keytype=="record":
					allr &= self.filterbypermissions(allr, ctx=ctx, txn=txn)

				if flat:
					return allr

				# perform filtering on both levels, and removing any items that become empty
				# ret = dict(filter(lambda x:x[1], [ ( k, dict(filter(lambda x:x[1], [ (k2,v2 & allr) for k2, v2 in v.items() ] ) ) ) for k,v in ret.items() ]))
				# ^^^ this is neat but too hard to maintain.. syntax expanded a bit below
				if tree:
					for k in ret:
						for k2 in ret[k]:
							ret[k][k2] &= allr

				else:
					for k in ret_visited:
						ret_visited[k] &= allr
					ret = ret_visited

			if ol:
				return ret.get(key[0],set())
				
			return ret


		def __getrel(self, key, keytype="record", recurse=1, rel="children", ctx=None, txn=None):
			# indc is restricted subset (e.g. getindexbycontext)
			"""get parent/child relationships; see: getchildren"""


			if (recurse < 0):
				return {}, set()

			if keytype == "record":
				trg = self.__records
				key = int(key)
				# read permission required
				try: self.getrecord(key, ctx=ctx, txn=txn)
				except:	return {}, set()

			elif keytype == "recorddef":
				trg = self.__recorddefs
				try: a = self.getrecorddef(key, ctx=ctx, txn=txn)
				except: return {}, set()

			elif keytype == "paramdef":
				trg = self.__paramdefs

			else:
				raise Exception, "getchildren keytype must be 'record', 'recorddef' or 'paramdef'"


			if rel=="children":
				rel = trg.children
			elif rel=="parents":
				rel = trg.parents
			else:
				raise Exception, "Unknown relationship mode"

			# base result
			ret = rel(key, txn=txn) or set()

			# ian: todo: use collections.queue
			stack = [ret]
			result = {key: ret}
			visited = set()
			
			for x in xrange(recurse):
				
				if not stack[x]:
					break
				if x > self.MAXRECURSE:
					raise Exception, "Recurse limit reached; check for circular relationships"
				
				stack.append(set())
				
				# print "%s lookups to make this level"%(len(stack[x]-visited))
				for k in stack[x] - visited:
					new = rel(k, txn=txn) #or set()
					if new:
						stack[x+1] |= new #.extend(new)
						result[k] = new

				visited |= stack[x]

			return result, visited






		@DBProxy.publicmethod
		def getcousins(self, key, keytype="record", ctx=None, txn=None):
			"""This will get the keys of the cousins of the referenced object
			keytype is 'record', 'recorddef', or 'paramdef'"""

			if keytype == "record" :
				#if not self.trygetrecord(key) : return set()
				try:
					self.getrecord(key, ctx=ctx, txn=txn)
				except:
					return set
				return set(self.__records.cousins(key, txn=txn))

			if keytype == "recorddef":
				return set(self.__recorddefs.cousins(key, txn=txn))

			if keytype == "paramdef":
				return set(self.__paramdefs.cousins(key, txn=txn))

			raise Exception, "getcousins keytype must be 'record', 'recorddef' or 'paramdef'"




		@DBProxy.publicmethod
		def pclinks(self, links, keytype="record", ctx=None, txn=None):
			return self.__link("pclink", links, keytype=keytype, ctx=ctx, txn=txn)


		@DBProxy.publicmethod
		def pcunlinks(self, links, keytype="record", ctx=None, txn=None):
			return self.__link("pcunlink", links, keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@DBProxy.publicmethod
		def pclink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			"""Establish a parent-child relationship between two keys.
			A context is required for record links, and the user must
			have write permission on at least one of the two."""
			return self.__link("pclink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@DBProxy.publicmethod
		def pcunlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			"""Remove a parent-child relationship between two keys. Returns none if link doesn't exist."""
			return self.__link("pcunlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@DBProxy.publicmethod
		def link(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			return self.__link("link", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)

		#@txn
		@DBProxy.publicmethod
		def unlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			return self.__link("unlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



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

			items = set(reduce(operator.concat, links))

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



		#@write #self.__recorddefs, self.__records, self.__paramdefs
		def __commit_link(self, keytype, mode, links, ctx=None, txn=None):
			"""controls access to record/paramdef/recorddef relationships"""

			if mode not in ["pclink","pcunlink","link","unlink"]:
				raise Exception, "Invalid relationship mode"
			if keytype == "record":
				index = self.__records
			elif keytype == "recorddef":
				index = self.__recorddefs
			elif keytype == "paramdef":
				index = self.__paramdefs
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




		###############################
		# section: user management
		###############################



		#@txn
		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def disableuser(self, username, ctx=None, txn=None):
			"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
			a complete historical record is maintained. Only an administrator can do this."""
			return self.__setuserstate(username, 1, ctx=ctx, txn=txn)



		#@txn
		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def enableuser(self, username, ctx=None, txn=None):
			return self.__setuserstate(username, 0, ctx=ctx, txn=txn)



		def __setuserstate(self, username, state, ctx=None, txn=None):
			"""Set user enabled/disabled. 0 is enabled. 1 is disabled."""

			state = int(state)

			if state not in [0,1]:
				raise Exception, "Invalid state. Must be 0 or 1."

			if not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators can disable users"

			ol = 0
			if not hasattr(username, "__iter__"):
				ol = 1
				username = [username]

			commitusers = []
			for i in username:
				if i == ctx.username:
					continue
					# raise subsystems.exceptions.SecurityError, "Even administrators cannot disable themselves"
				user = self.__users.sget(i, txn=txn) #[i]
				if user.disabled == state:
					continue

				user.disabled = int(state)
				commitusers.append(i)


			ret = self.__commit_users(commitusers, ctx=ctx, txn=txn)
			g.log.msg('LOG_INFO', "Users %s disabled by %s"%([user.username for user in ret], ctx.username))

			if len(ret)==1 and ol: return ret[0].username
			return [user.username for user in ret]


		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def getsecret(self, username, ctx=None, txn=None):
			return self.__newuserqueue.get(username, txn=txn).get_secret()


		#@txn
		@DBProxy.publicmethod
		@DBProxy.adminmethod
		@emen2.util.utils.return_list_or_single(1)
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


			#ol=False
			if not hasattr(usernames,"__iter__"):
				#ol=True
				usernames = [usernames]


			delusers, addusers, records, childstore = {}, {}, {}, {}

			for username in usernames:
				if not username in self.__newuserqueue.keys(txn=txn):
					raise KeyError, "User %s is not pending approval" % username

				if self.__users.get(username, txn=txn):
					delusers[username] = None
					g.log.msg("LOG_ERROR","User %s already exists, deleted pending record" % username)


				# ian: create record for user.
				user = self.__newuserqueue.sget(username, txn=txn) #[username]

				user.setContext(ctx)
				user.validate()

				if secret is not None and not user.validate_secret(secret):
					g.log.msg("LOG_ERROR","Incorrect secret for user %s; skipping"%username)
					time.sleep(2)


				else:
					if user.record == None and user.signupinfo:

						tmpctx = self.__makerootcontext(txn=txn)

						rec = self.newrecord("person", ctx=tmpctx, txn=txn)
						rec["username"] = username
						name = user.signupinfo.get('name', ['', '', ''])
						rec["name_first"], rec["name_middle"], rec["name_last"] = name[0], ' '.join(name[1:-1]) or None, name[1]
						rec["email"] = user.signupinfo.get('email')
						rec.adduser(username, level=3)

						for k,v in user.signupinfo.items():
							rec[k] = v

						#print "putting record..."
						rec = self.putrecord([rec], ctx=tmpctx, txn=txn)[0]

						# ian: todo: turning this off for now..
						#print "creating child records"
						#children = user.create_childrecords()
						#children = [(self.__putrecord([child], ctx=tmpctx, txn=txn)[0].recid, parents) for child, parents in children]

						#if children != []:
						#	self.__link('pclink', [(rec.recid, child) for child, _ in children], ctx=tmpctx, txn=txn)
						#	for links in children:
						#		child, parents = links
						#		self.__link('pclink', [(parent, child) for parent in parents], ctx=tmpctx, txn=txn)


						user.record = rec.recid

					user.signupinfo = None
					addusers[username] = user
					delusers[username] = None

			self.__commit_users(addusers.values(), ctx=ctx, txn=txn)
			self.__commit_newusers(delusers, ctx=ctx, txn=txn)

			#@end

			ret = addusers.keys()
			# if ol and len(ret)==1:
			# 	return ret[0]
			return ret




		# @DBProxy.publicmethod
		# @DBProxy.adminmethod
		# def getpendinguser(self, username, ctx=None, txn=None):
		# 	return self.__newuserqueue.get(username, txn=txn)



		#@txn
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
				#if not username in self.__newuserqueue:
				if not self.__newuserqueue.get(username, txn=txn):
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

			return self.__newuserqueue.keys(txn=txn)



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

			return self.__newuserqueue.sget(username, txn=txn) # [username]


		#@txn
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


		#@txn
		@DBProxy.publicmethod
		def setpassword(self, username, oldpassword, newpassword, ctx=None, txn=None):

			user = self.getuser(username, ctx=ctx, txn=txn)

			s = hashlib.sha1(oldpassword)

			if s.hexdigest() != user.password and not ctx.checkadmin():
				time.sleep(2)
				raise subsystems.exceptions.SecurityError, "Original password incorrect"

			# we disallow bad passwords here, right now we just make sure that it
			# is at least 6 characters long

			if len(newpassword) < 6:
				raise subsystems.exceptions.SecurityError, "Passwords must be at least 6 characters long"

			t = hashlib.sha1(newpassword)
			user.password = t.hexdigest()

			g.log.msg("LOG_INFO","Changing password for %s"%user.username)

			self.__commit_users([user], ctx=ctx, txn=txn)

			return 1






		##########################
		# section: group
		##########################


		@DBProxy.publicmethod
		def getgroupnames(self, ctx=None, txn=None):
			return set(self.__groups.keys(txn=txn))



		@DBProxy.publicmethod
		def getgroup(self, groups, filt=1, ctx=None, txn=None):
			ol=0
			if not hasattr(groups,"__iter__"):
				ol=1
				groups = [groups]


			if filt: filt = None
			else: filt = lambda x:x.name
			ret = dict( [(x.name, x) for x in filter(filt, [self.__groups.get(i, txn=txn) for i in groups]) ] )

			if ol==1 and len(ret) == 1:
				return ret.values()[0]

			return ret




		#@write self.__groupsbyuser
		def __commit_groupsbyuser(self, addrefs=None, delrefs=None, ctx=None, txn=None):

			#@begin

			for user,groups in addrefs.items():
				try:
					if groups:
						g.log.msg("LOG_COMMIT_INDEX","__groupsbyuser key: %r, addrefs: %r"%(user, groups))
						self.__groupsbyuser.addrefs(user, groups, txn=txn)

				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups))
					raise

				except ValueError, inst:
					g.log.msg("LOG_ERROR", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups))


			for user,groups in delrefs.items():
				try:
					if groups:
						g.log.msg("LOG_COMMIT_INDEX","__groupsbyuser key: %r, removerefs: %r"%(user, groups))
						self.__groupsbyuser.removerefs(user, groups, txn=txn)

				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups))
					raise

				except ValueError, inst:
					g.log.msg("LOG_ERROR", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups))


			#@end




		#@write self.__groupsbyuser
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

			g.log.msg("LOG_COMMIT_INDEX","self.__groupsbyuser: rebuilding index")

			self.__groupsbyuser.truncate(txn=txn)

			for k,v in users.items():
				self.__groupsbyuser.addrefs(k, v, txn=txn)

			#@end





		def __reindex_groupsbyuser(self, groups, ctx=None, txn=None):

			addrefs = collections.defaultdict(set)
			delrefs = collections.defaultdict(set)

			for group in groups:

				ngm = group.members()
				try: ogm = self.__groups.get(group.groupname, txn=txn).members()
				except: ogm = set()

				addusers = ngm - ogm
				delusers = ogm - ngm

				for user in addusers:
					addrefs[user].add(group.name)
				for user in delusers:
					delrefs[user].add(group.name)

			return addrefs, delrefs



		#@write self.__groups, self.__groupsbyuser
		@DBProxy.publicmethod
		def putgroup(self, groups, ctx=None, txn=None):

			if isinstance(groups, (dataobjects.group.Group, dict)): # or not hasattr(groups, "__iter__"):
				groups = [groups]

			groups2 = []
			groups2.extend(filter(lambda x:isinstance(x, dataobjects.group.Group), groups))
			groups2.extend(map(lambda x:dataobjects.group.Group(x, ctx=ctx), filter(lambda x:isinstance(x, dict), groups)))

			for group in groups2:
				group.setContext(ctx)
				group.validate()

			self.__commit_groups(groups2, ctx=ctx, txn=txn)


		def __commit_groups(self, groups, ctx=None, txn=None):

			addrefs, delrefs = self.__reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

			#@begin
			for group in groups:
				g.log.msg("LOG_COMMIT","__groups.set: %r"%(group))
				self.__groups.set(group.name, group, txn=txn)

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
				groups |= reduce(set.union, [i.get("groups",set()) for i in self.getrecord(gn_int, filt=True, ctx=ctx, txn=txn)])

			groups = self.getgroup(groups, ctx=ctx, txn=txn)

			ret = {}

			for i in groups.values():
				ret[i.name]="Group: %s"%i.name

			if ol and len(ret)==1: return ret.values()[0]
			return ret



		###############################
		# users
		###############################


		#@txn
		@DBProxy.publicmethod
		def adduser(self, inuser, ctx=None, txn=None):
			"""adds a new user record. However, note that this only adds the record to the
			new user queue, which must be processed by an administrator before the record
			becomes active. This system prevents problems with securely assigning passwords
			and errors with data entry. Anyone can create one of these"""

			secret = hashlib.sha1(str(id(inuser)) + str(time.time()) + str(random.random()))

			try:
				user = dataobjects.user.User(inuser, secret=secret.hexdigest(), ctx=ctx)
			except Exception, inst:
				raise ValueError, "User instance or dict required (%s)"%inst


			if self.__users.get(user.username, txn=txn):
				raise KeyError, "User with username '%s' already exists" % user.username


			#if user.username in self.__newuserqueue:
			if self.__newuserqueue.get(user.username, txn=txn):
				raise KeyError, "User with username '%s' already pending approval" % user.username

			assert hasattr(user, '_User__secret')

			user.validate()

			self.__commit_newusers({user.username:user}, ctx=None, txn=txn)

			if ctx.checkadmin():
				#print "approving %s"%user.username
				self.approveuser(user.username, ctx=ctx, txn=txn)

			return inuser



		@DBProxy.publicmethod
		def putuser(self, user, ctx=None, txn=None):

			if not isinstance(user, dataobjects.user.User):
				try:
					user = dataobjects.user.User(user, ctx=ctx)
				except:
					raise ValueError, "User instance or dict required"

			if not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators may add/modify users with this method"

			if self.__importmode:
				user.validate(warning=True)
			else:
				user.validate()

			self.__commit_users([user], ctx=ctx, txn=txn)




		#@write #self.__users
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
					ouser = self.__users.sget(user.username, txn=txn) #[user.username]
				except:
					ouser = user
					#raise KeyError, "Putuser may only be used to update existing users"

				commitusers.append(user)

			#@begin

			for user in commitusers:
				self.__users.set(user.username, user, txn=txn)
				g.log.msg("LOG_COMMIT","self.__users.set: %r"%user.username)

			#@end

			return commitusers


		#@write #self.__newuserqueue
		def __commit_newusers(self, users, ctx=None, txn=None):
			"""write to newuserqueue; users is dict; set value to None to del"""

			#@begin

			for username, user in users.items():
				if user == None:
					g.log.msg("LOG_COMMIT","self.__newuserqueue.set: %r"%username)
				else:
					g.log.msg("LOG_COMMIT","self.__newuserqueue.set: %r, deleting"%username)

				self.__newuserqueue.set(username, user, txn=txn)

			#@end



		@DBProxy.publicmethod
		def getuser(self, usernames, filt=True, lnf=False, getgroups=False, getrecord=True, ctx=None, txn=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			ol=0
			if not hasattr(usernames,"__iter__"):
				ol=1
				usernames = [usernames]

			recs = filter(lambda x:isinstance(x, dataobjects.record.Record), usernames)
			rec_ints = filter(lambda x:isinstance(x, int), usernames)
			if rec_ints:
				recs.extend(self.getrecord(rec_ints, filt=True, ctx=ctx, txn=txn))

			if recs:
				un2 = self.filtervartype(recs, vts=["user","userlist","acl"], flat=True, ctx=ctx, txn=txn)
				usernames.extend(un2)

			usernames = set(filter(lambda x:isinstance(x, basestring), usernames))

			ret={}

			for i in usernames:

				user = self.__users.get(i, None, txn=txn)

				if user == None:
					if filt:
						continue
					else:
						raise KeyError, "No such user: %s"%i


				# if the user has requested privacy, we return only basic info
				#if (user.privacy and ctx.username == None) or user.privacy >= 2:
				if user.privacy and not (ctx.checkreadadmin() or ctx.username == user.username):
					user2 = dataobjects.user.User()
					user2.username = user.username
					user = user2

				# Anonymous users cannot use this to extract email addresses
				#if ctx.username == None:
				#	user.groups = None

				#if getgroups:
				#	user.groups = self.__groupsbyuser.get(user.username, set(), txn=txn)

				# ian: todo: it's easier if we get record directly here....
				#user.userrec = self.__records.sget(user.record, txn=txn)
				if getrecord and user.record is not None:
					try:
						user.userrec = self.getrecord(user.record, filt=False, ctx=ctx, txn=txn)
					except Exception, inst:
						#g.log.msg('LOG_ERROR', "problem getting record user %s record %s: %s"%(user.username, user.record, inst))
						user.userrec = {}

					user.displayname = self.__formatusername(user.username, user.userrec, lnf=lnf, ctx=ctx, txn=txn)
					user.email = user.userrec.get("email")

				else:
					user.userrec = {}
					user.displayname = user.username
					user.email = None


				ret[i] = user



			if len(ret)==1 and ol:
				return ret[ret.keys()[0]]

			return ret





		@DBProxy.publicmethod
		def getuserdisplayname(self, username, lnf=1, perms=0, filt=True, ctx=None, txn=None):
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
				namestoget.extend(reduce(lambda x,y: x+y, [[i[0] for i in rec["comments"]] for rec in recs]))

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




		def __formatusername(self, username, u={}, lnf=True, ctx=None, txn=None):
			nf = u.get("name_first")
			nm = u.get("name_middle")
			nl = u.get("name_last")

			#if u["name_first"] and u["name_middle"] and u["name_last"]:
			if nf and nm and nl:
				if lnf:
					uname = "%s, %s %s" % (nl, nf, nm)
				else:
					uname = "%s %s %s" % (nf, nm, nl)

			elif nf and nl:
				if lnf:
					uname = "%s, %s" % (nl, nf)
				else:
					uname = "%s %s" % (nf, nl)

			elif nl:
				uname = nl

			elif nf:
				uname = nf

			else:
				return username

			return uname




		@DBProxy.publicmethod
		def getusernames(self, ctx=None, txn=None):
			"""Not clear if this is a security risk, but anyone can get a list of usernames
					This is likely needed for inter-database communications"""

			if ctx.username == None:
				return

			return set(self.__users.keys(txn=txn))




		@DBProxy.publicmethod
		def findusername(self, name, ctx=None, txn=None):
			"""This will look for a username matching the provided name in a loose way"""

			if ctx.username == None: return

			if self.__users.get(name, txn=txn):
				return name

			possible = filter(lambda x: name in x, self.__users.keys(txn=txn))
			if len(possible) == 1:
				return possible[0]
			if len(possible) > 1:
				return possible

			possible = []
			for i in self.getusernames(ctx=ctx, txn=txn):
				try:
					u = self.getuser(name, ctx=ctx, txn=txn)
				except:
					continue

				for j in u.__dict__:
					if isinstance(j, basestring) and name in j :
						possible.append(i)
						break

			if len(possible) == 1:
				return possible[0]
			if len(possible) > 1:
				return possible

			return None




		#########################
		# section: workflow
		#########################



		@DBProxy.publicmethod
		def getworkflow(self, ctx=None, txn=None):
			"""This will return an (ordered) list of workflow objects for the given context (user).
			it is an exceptionally bad idea to change a WorkFlow object's wfid."""

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"

			try:
				return self.__workflow.sget(ctx.username, txn=txn) #[ctx.username]
			except:
				return []



		@DBProxy.publicmethod
		def getworkflowitem(self, wfid, ctx=None, txn=None):
			"""Return a workflow from wfid."""

			ret = None
			wflist = self.getworkflow(ctx=ctx, txn=txn)
			if len(wflist) == 0:
				return None
			else:
				for thewf in wflist:
					if thewf.wfid == wfid:
						#ret = thewf.items_dict()
						ret = dict(thewf)
			return ret



		@DBProxy.publicmethod
		def newworkflow(self, vals, ctx=None, txn=None):
			"""Return an initialized workflow instance."""
			return WorkFlow(vals)



		#@txn
		#@write #self.__workflow
		@DBProxy.publicmethod
		def addworkflowitem(self, work, ctx=None, txn=None):
			"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"

			if not isinstance(work, WorkFlow):
				try:
					work = WorkFlow(work)
				except:
					raise ValueError, "WorkFlow instance or dict required"
			#work=WorkFlow(work.__dict__.copy())
			work.validate()

			#if not isinstance(work,WorkFlow):
			#		 raise TypeError,"Only WorkFlow objects can be added to a user's workflow"

			work.wfid = self.__workflow.sget(-1, txn=txn)   #[-1]
			self.__workflow[-1] = work.wfid + 1

			if self.__workflow.has_key(ctx.username):
				wf = self.__workflow[ctx.username]
			else:
				wf = []

			wf.append(work)
			self.__workflow[ctx.username] = wf


			return work.wfid



		#@txn
		#@write #self.__workflow
		@DBProxy.publicmethod
		def delworkflowitem(self, wfid, ctx=None, txn=None):
			"""This will remove a single workflow object based on wfid"""
			#self = db

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"

			wf = self.__workflow.sget(ctx.username, txn=txn) #[ctx.username]
			for i, w in enumerate(wf):
				if w.wfid == wfid :
					del wf[i]
					break
			else:
				raise KeyError, "Unknown workflow id"

			g.log.msg("LOG_COMMIT","self.__workflow.set: %r, deleting %s"%(ctx.username, wfid))
			self.__workflow.set(ctx.username, wf, txn=txn)




		#@txn
		#@write #self.__workflow
		@DBProxy.publicmethod
		def setworkflow(self, wflist, ctx=None, txn=None):
			"""This allows an authorized user to directly modify or clear his/her workflow. Note that
			the external application should NEVER modify the wfid of the individual WorkFlow records.
			Any wfid's that are None will be assigned new values in this call."""
			#self = db

			if ctx.username == None:
				raise subsystems.exceptions.SecurityError, "Anonymous users have no workflow"

			if wflist == None:
				wflist = []
			wflist = list(wflist)								 # this will (properly) raise an exception if wflist cannot be converted to a list

			for w in wflist:
				if not self.__importmode:
					#w=WorkFlow(w.__dict__.copy())
					w.validate()

				if not isinstance(w, WorkFlow):
					self.txnabort(txn=txn) #txn.abort()
					raise TypeError, "Only WorkFlow objects may be in the user's workflow"
				if w.wfid == None:
					w.wfid = self.__workflow.sget(-1, txn=txn) #[-1]
					self.__workflow.set(-1, w.wfid + 1, txn=txn)

			g.log.msg("LOG_COMMIT","self.__workflow.set: %r"%ctx.username)
			self.__workflow.set(ctx.username, wflist, txn=txn)




		# ian: todo
		#@write #self.__workflow
		def __commit_workflow(self, wfs, ctx=None, txn=None):
			pass




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
			# ian: todo: move this block to ParamDef.validate()
			
			if not ctx.checkcreate():
				raise subsystems.exceptions.SecurityError, "No permission to create new paramdefs (need record creation permission)"

			paramdef.name = unicode(paramdef.name).lower()

			try:
				pd = self.__paramdefs.sget(paramdef.name, txn=txn)

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

			#####################

			self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)

			links = []
			if parents: links.append( map(lambda x:(x, paramdef.name), parents) )
			if children: links.append( map(lambda x:(paramdef.name, x), children) )
			if links:
				self.pclinks(links, keytype="paramdef", ctx=ctx, txn=txn)





		@DBProxy.publicmethod
		def addparamchoice(self, paramdefname, choice, ctx=None, txn=None):
			"""This will add a new choice to records of vartype=string. This is
			the only modification permitted to a ParamDef record after creation"""

			paramdefname = unicode(paramdefname).lower()

			# ian: change to only allow logged in users to add param choices. silent return on failure.
			if not ctx.checkcreate():
				return

			d = self.__paramdefs.sget(paramdefname, txn=txn)  #[paramdefname]
			if d.vartype != "string":
				raise subsystems.exceptions.SecurityError, "choices may only be modified for 'string' parameters"

			d.choices = d.choices + (unicode(choice).title(),)

			d.setContext(ctx)
			d.validate()

			self.__commit_paramdefs([d], ctx=ctx, txn=txn)



		#ian: todo
		#@write #self.__paramdefs
		def __commit_paramdefs(self, paramdefs, ctx=None, txn=None):

			#@begin
			for paramdef in paramdefs:
				g.log.msg("LOG_COMMIT","self.__paramdefs.set: %r"%paramdef.name)
				self.__paramdefs.set(paramdef.name, paramdef, txn=txn)
			#@end





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
					paramdefs[i] = self.__paramdefs.sget(i, txn=txn) # [i]
				except:
					if filt:
						g.log.msg('LOG_WARNING', "WARNING: Invalid param: %s"%i)
						pass
					else:
						raise Exception, "Invalid param: %s"%i

			return paramdefs




		# ian todo: combine this and getparamdefs; alot of older places use this version
		@DBProxy.publicmethod
		def getparamdef(self, key, ctx=None, txn=None):
			"""gets an existing ParamDef object, anyone can get any field definition"""
			try:
				return self.__paramdefs.sget(key, txn=txn) #[key]
			except:
				raise KeyError, "Unknown ParamDef: %s" % key



		@DBProxy.publicmethod
		def getparamdefnames(self, ctx=None, txn=None):
			"""Returns a list of all ParamDef names"""
			return self.__paramdefs.keys(txn=txn)



		def __getparamindex(self, paramname, create=True, ctx=None, txn=None):
			"""Internal function to open the parameter indices at need.
			Later this may implement some sort of caching mechanism.
			If create is not set and index doesn't exist, raises
			KeyError. Returns "link" or "child" for this type of indexing"""



			try:
				return self.__fieldindex[paramname] # [paramname]				# Try to get the index for this key
			except Exception, inst:
				pass


			#paramname = self.__paramdefs.typekey(paramname)
			f = self.__paramdefs.sget(paramname, txn=txn) #[paramname]				 # Look up the definition of this field
			paramname = f.name

			if f.vartype not in self.indexablevartypes or not f.indexed:
				return None

			tp = self.vtm.getvartype(f.vartype).getindextype()

			if not create and not os.access("%s/index/%s.bdb" % (self.path, paramname), os.F_OK):
				raise KeyError, "No index for %s" % paramname

			# create/open index
			self.__fieldindex[paramname] = subsystems.btrees.FieldBTree(paramname, keytype=tp, indexkeys=self.__indexkeys, filename="%s/index/%s.bdb"%(self.path,paramname), dbenv=self.__dbenv, txn=txn)

			return self.__fieldindex[paramname]



		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def __closeparamindex(self, paramname, ctx=None, txn=None):
			self.__fieldindex.pop(paramname).close()

		def __closeparamindexes(self, ctx=None, txn=None):
			map(lambda x: self.__closeparamindex(x, ctx=ctx, txn=txn), self.__fieldindex.keys())



		#########################
		# section: recorddefs
		#########################




		#@txn
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
				orec = self.__recorddefs.sget(recdef.name, txn=txn)
				orec.setContext(ctx)

			except:
				orec = dataobjects.recorddef.RecordDef(recdef, ctx=ctx)

			##################
			# ian: todo: move this block to RecordDef.validate()

			#if not validate and not ctx.checkadmin():
			#	raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"

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

			##################

			recdef.validate()

			# commit
			self.__commit_recorddefs([recdef], ctx=ctx, txn=txn)

			links = []
			if parents: links.append( map(lambda x:(x, recdef.name), parents) )
			if children: links.append( map(lambda x:(recdef.name, x), children) )
			if links:
				self.pclinks(links, keytype="recorddef", ctx=ctx, txn=txn)

			return recdef.name



		#@write #self.__recorddefs
		def __commit_recorddefs(self, recorddefs, ctx=None, txn=None):

			#@begin
			for recorddef in recorddefs:
				g.log.msg("LOG_COMMIT","self.__recorddefs.set: %r"%recorddef.name)
				self.__recorddefs.set(recorddef.name, recorddef, txn=txn)
			#@end




		@DBProxy.publicmethod
		def getrecorddef(self, rectypename, recid=None, ctx=None, txn=None):
			"""Retrieves a RecordDef object. This will fail if the RecordDef is
			private, unless the user is an owner or	 in the context of a recid the
			user has permission to access"""

			if hasattr(rectypename,"__iter__"):
				ret = {}
				for i in rectypename:
					ret[i] = self.getrecorddef(i, recid=recid, ctx=ctx, txn=txn)
				return ret


			try:
				#ret = self.__recorddefs[rectypename]
				ret = self.__recorddefs.sget(rectypename, txn=txn) # [rectypename]
			except:
				raise KeyError, "No such RecordDef %s" % rectypename

			if not ret.private:
				return ret

			# if the RecordDef isn't private or if the owner is asking, just return it now
			if (ret.private and (ret.owner == ctx.username or ctx.checkreadadmin())): #ret.owner in ctx.groups
				return ret

			# ian todo: make sure all calls to getrecorddef pass recid they are requesting

			# ok, now we need to do a little more work.
			if recid == None:
				raise subsystems.exceptions.SecurityError, "User doesn't have permission to access private RecordDef '%s'" % rectypename

			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			# try to get the record, may (and should sometimes) raise an exception

			if rec.rectype != rectypename:
				raise subsystems.exceptions.SecurityError, "Record %d doesn't belong to RecordDef %s" % (recid, rectypename)

			# success, the user has permission
			return ret



		@DBProxy.publicmethod
		def getrecorddefnames(self, ctx=None, txn=None):
			"""This will retrieve a list of all existing RecordDef names,
			even those the user cannot access the contents of"""
			return self.__recorddefs.keys(txn=txn)



		@DBProxy.publicmethod
		def findrecorddefname(self, name, ctx=None, txn=None):
			"""Find a recorddef similar to the passed 'name'. Returns the actual RecordDef,
			or None if no match is found."""


			#if self.__recorddefs.has_key(name):
			if self.__recorddefs.get(name, txn=txn):
				return name

			if name[-1] == "s":
					if self.__recorddefs.has_key(name[:-1], txn=txn):
						return name[:-1]
					if name[-2] == "e" and self.__recorddefs.has_key(name[:-2], txn=txn):
						return name[:-2]
			if name[-3:] == "ing" and self.__recorddefs.has_key(name[:-3], txn=txn):
				return name[:-3]
			return None





		#########################
		# section: records
		#########################


		# ian: improved!
		# ed: more improvments!
		#@emen2.util.utils.return_list_or_single(1)
		@DBProxy.publicmethod
		def getrecord(self, recids, filt=True, ctx=None, txn=None):
			"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
			if dbid is 0, the current database is used."""
			
			ol = False
			if not hasattr(recids, '__iter__'): 
				ol = True
				recids = [recids]

			ret = []
			for i in sorted(recids):
				try:
					rec = self.__records.sget(i, txn=txn)
					rec.setContext(ctx)
					ret.append(rec)
				except emen2.Database.subsystems.exceptions.SecurityError, e:
					if filt: pass
					else: raise e
				except (KeyError, TypeError), e:
					raise
					if filt: pass
					else: raise KeyError, "No such record %s"%(i) #, e)
		
		
			if ol and not ret:
				return None
			if ol:	
				return ret.pop()
			return ret





		# ian: todo: improve newrecord/putrecord
		# ian: todo: allow to copy existing record
		@DBProxy.publicmethod
		def newrecord(self, rectype, recid=None, init=False, inheritperms=None, ctx=None, txn=None):
			"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
			already exist)."""

			# try to get the RecordDef entry, this still may fail even if it exists, if the
			# RecordDef is private and the context doesn't permit access
			# t = dict(filter(lambda x:x[1]!=None, self.getrecorddef(rectype, ctx=ctx, txn=txn).params.items()))
			t = filter(lambda x:x[1] != None, self.getrecorddef(rectype, ctx=ctx, txn=txn).params.items())
			rec = dataobjects.record.Record(rectype=rectype, recid=recid, ctx=ctx)

			if init:
				rec.update(t)

			if inheritperms != None:
				try:
					prec = self.getrecord(inheritperms, filt=0, ctx=ctx, txn=txn)
					#for level, users in enumerate(prec["permissions"]):
					#	rec.adduser(users, level=level)
					#print prec["permissions"]
					#print prec["groups"]
					rec.addumask(prec["permissions"])
					rec.addgroup(prec["groups"])

				except Exception, inst:
					g.log.msg("LOG_ERROR","newrecord: Error setting inherited permissions from record %s (%s)"%(inheritperms, inst))


			return rec



		@DBProxy.publicmethod
		def getparamdefnamesbyvartype(self, vts, paramdefs=None, ctx=None, txn=None):
			if not hasattr(vts,"__iter__"):
				vts = [vts]

			if not paramdefs:
				paramdefs = self.getparamdefs(self.getparamdefnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)

			return [y.name for y in filter(lambda x:x.vartype in vts, paramdefs.values())]



		# ian: this might be helpful
		# e.g.: __filtervartype(136, ["user","userlist"])
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

			# get the params...
			#if params:
			#	paramdefs = self.getparamdefs(params, ctx=ctx, txn=txn)
			#if not paramdefs:
			#	pds = set(reduce(lambda x,y:x+y,map(lambda x:x.keys(),recs2)))
			#	paramdefs.update(self.getparamdefs(pds, ctx=ctx, txn=txn))

			# l = set([pd.name for pd in paramdefs.values() if pd.vartype in vts]) - ignore
			#l = set(map(lambda x:x.name, filter(lambda x:x.vartype in vts, paramdefs.values()))) - ignore
			##l = set(filter(lambda x:x.vartype in vts, paramdefs.values())) - ignore

			# if returndict or ol:
			# 				ret = {}
			# 				for rec in recs2:
			# 					re = [rec.get(pd) or None for pd in l]
			# 					if flat:
			#TODO: replace with reduce
			# 						re = set(self.__flatten(re))-set([None])
			# 					ret[rec.recid]=re
			#
			# 				if ol: return ret.values()[0]
			# 				return ret

			# if not returndict

			re = [[rec.get(pd) for pd in params if rec.get(pd)] for rec in recs2]

			if flat:
				#TODO: replace with reduce
				return set(self.__flatten(re))-set([None])

			return re









		#@txn
		@DBProxy.publicmethod
		def deleterecord(self, recid, ctx=None, txn=None):
			"""Unlink and hide a record; it is still accessible to owner and root. Records are never truly deleted, just hidden."""

			rec=self.getrecord(recid, ctx=ctx, txn=txn)
			if not rec.isowner():
				raise Exception,"No permission to delete record"

			parents=self.getparents(recid, ctx=ctx, txn=txn)
			children=self.getchildren(recid, ctx=ctx, txn=txn)

			if len(parents) > 0 and rec["deleted"] !=1 :
				#rec["comments"]=
				rec.addcomment("Record marked for deletion and unlinked from parents: %s"%", ".join([unicode(x) for x in parents]))
			elif rec["deleted"] != 1:
				#rec["comments"]="Record marked for deletion"
				rec.addcomment("Record marked for deletion")

			rec["deleted"] = 1
			self.putrecord(rec, ctx=ctx, txn=txn)

			for i in parents:
				self.pcunlink(i,recid, ctx=ctx, txn=txn)

			for i in children:
				c2=self.getchildren(i, ctx=ctx, txn=txn)
				#c2.remove(recid)
				c2 -= set([recid])
				# if child had more than one parent, make a note one parent was removed
				if len(c2) > 0:
					rec2=self.getrecord(i, ctx=ctx, txn=txn)
					rec["comments"]="Parent record %s was deleted"%recid
					self.putrecord(rec2, ctx=ctx, txn=txn)
					self.pcunlink(recid, i, ctx=ctx, txn=txn)



		# ian: todo: should be extension
		#@txn
		@DBProxy.publicmethod
		def addcomment(self, recid, comment, ctx=None, txn=None):
			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			rec.addcomment(comment)
			self.putrecord(rec, ctx=ctx, txn=txn)
			return self.getrecord(recid, ctx=ctx, txn=txn)["comments"]




		#########################
		# section: putrecord
		#########################


		# ian todo: redo these three methods
		#@txn
		@DBProxy.publicmethod
		def putrecordvalue(self, recid, param, value, ctx=None, txn=None):
			"""Make a single change to a single record"""
			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			rec[param] = value
			self.putrecord(rec, ctx=ctx, txn=txn)
			return self.getrecord(recid, ctx=ctx, txn=txn)[param]



		#@txn
		@DBProxy.publicmethod
		def putrecordvalues(self, recid, values, ctx=None, txn=None):
			"""Make multiple changes to a single record"""

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



		#@txn
		@DBProxy.publicmethod
		def putrecordsvalues(self, d, ctx=None, txn=None):
			"""Make multiple changes to multiple records"""

			ret = {}
			for k, v in d.items():
				ret[k] = self.putrecordvalues(k, v, ctx=ctx, txn=txn)
			return ret



		#@txn
		@DBProxy.publicmethod
		def putrecord(self, recs, filt=True, warning=0, log=True, ctx=None, txn=None):
			"""commits a record"""
			# input validation for __putrecord

			if not log and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators may bypass logging"

			# filter input for dicts/records
			ol = 0
			if isinstance(recs,(dataobjects.record.Record,dict)):
				ol = 1
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





		def __putrecord(self, updrecs, warning=0, log=True, ctx=None, txn=None):
			# process before committing

			if len(updrecs) == 0:
				return []

			crecs = []
			updrels = []

			param_immutable = set(["recid","rectype","creator","creationtime","modifytime","modifyuser"])
			param_special = param_immutable | set(["comments","permissions","groups","history"])

			# assign temp recids to new records
			for offset,updrec in enumerate(filter(lambda x:x.recid < 0, updrecs)):
				updrec.recid = -1 * (offset + 100)

			updrels = self.__putrecord_getupdrels(updrecs, ctx=ctx, txn=txn)

			# preprocess: copy updated record into original record (updrec -> orec)

			for updrec in updrecs:


				if self.__importmode:
					crecs.append(updrec)
					continue

				t = self.gettime(ctx=ctx, txn=txn)
				recid = updrec.recid

				# we need to acquire RMW lock here to prevent changes during commit
				if self.__records.exists(updrec.recid, txn=txn, flags=RMWFLAGS):
					orec = self.__records.sget(updrec.recid, txn=txn)
					orec.setContext(ctx)

				elif recid < 0:
					orec = self.newrecord(updrec.rectype, recid=updrec.recid, ctx=ctx, txn=txn)

				else:
					raise Exception, "Cannot update non-existent record %s"%recid



				updrec.validate(orec=orec, warning=warning)


				# compare to original record
				cp = orec.changedparams(updrec) - param_immutable


				# orec.recid < 0 because new records will always be committed, even if skeletal
				if not cp and orec.recid >= 0:
					g.log.msg("LOG_INFO","putrecord: No changes for record %s, skipping"%recid)
					continue


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
		#@write	#self.__records, self.__recorddefbyrec, self.__recorddefindex, self.__timeindex
		# also, self.fieldindex* through __commit_paramindex(), self.__secrindex through __commit_secrindex
		def __commit_records(self, crecs, updrels=[], onlypermissions=False, ctx=None, txn=None):

			rectypes = collections.defaultdict(list) # {}
			newrecs = filter(lambda x:x.recid < 0, crecs)
			recmap = {}
			timeupdate = {}


			cache = {}
			for i in crecs:
				if i.recid < 0: continue
				try: orec = self.__records.sget(i.recid, txn=txn, flags=RMWFLAGS) # [recid]
				except: orec = {}
				cache[i.recid] = orec


			# acquire write locks on records at this point
			# first, get index updates

			indexupdates = {}
			timeupdate = {}
			if not onlypermissions:
				indexupdates = self.__reindex_params(crecs, cache=cache, ctx=ctx, txn=txn)
				timeupdate = self.__reindex_time(crecs, cache=cache, ctx=ctx, txn=txn)
			secr_addrefs, secr_removerefs = self.__reindex_security(crecs, cache=cache, ctx=ctx, txn=txn)
			secrg_addrefs, secrg_removerefs = self.__reindex_security_groups(crecs, cache=cache, ctx=ctx, txn=txn)


			#@begin

			# this needs a lock.
			if newrecs:
				baserecid = self.__records.sget(-1, txn=txn, flags=RMWFLAGS)
				g.log.msg("LOG_INFO","Setting recid counter: %s -> %s"%(baserecid, baserecid + len(newrecs)))
				self.__records.set(-1, baserecid + len(newrecs), txn=txn)


			# add recids to new records, create map from temp recid, setup index
			for offset, newrec in enumerate(newrecs):
				oldid = newrec.recid
				newrec.recid = offset + baserecid
				recmap[oldid] = newrec.recid
				rectypes[newrec.rectype].append(newrec.recid)


			# This actually stores the record in the database
			for crec in crecs:
				# g.log.msg("LOG_COMMIT","self.__records.set: %r"%crec.recid)
				self.__records.set(crec.recid, crec, txn=txn)



			# Security index
			self.__commit_secrindex(secr_addrefs, secr_removerefs, recmap=recmap, ctx=ctx, txn=txn)
			self.__commit_secrindex_groups(secrg_addrefs, secrg_removerefs, recmap=recmap, ctx=ctx, txn=txn)

			# RecordDef index
			self.__commit_recorddefindex(rectypes, recmap=recmap, ctx=ctx, txn=txn)

			# Time index
			self.__commit_timeindex(timeupdate, recmap=recmap, ctx=ctx, txn=txn)

			# Param index
			for param, updates in indexupdates.items():
				self.__commit_paramindex(param, updates[0], updates[1], recmap=recmap, ctx=ctx, txn=txn)


			# Create pc links
			for link in updrels:
				try:
					self.pclink( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), ctx=ctx, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst))


			g.log.msg("LOG_INFO", "Committed %s records"%(len(crecs)))
			#@end

			return crecs
			
			
		def __commit_recorddefindex(self, rectypes, recmap=None, ctx=None, txn=None):	
			if not recmap: recmap = {}

			for rectype,recs in rectypes.items():
				try:
					g.log.msg("LOG_COMMIT_INDEX","self.__recorddefindex.addrefs: %r, %r"%(rectype,recs))
					self.__recorddefindex.addrefs(rectype, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst))
					raise
				except ValueError, inst:
					g.log.msg("LOG_ERROR", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst))			


		def __commit_timeindex(self, timeupdate, recmap=None, ctx=None, txn=None):
			if not recmap: recmap = {}

			for recid,time in timeupdate.items():
				try:
					recid = recmap.get(recid,recid)
					if not isinstance(recid, basestring):
						recid = unicode(recid).encode('utf-8')
					g.log.msg("LOG_COMMIT_INDEX","self.__timeindex.set: %r, %r"%(recmap.get(recid,recid), time))
					self.__timeindex.set(recid, time, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst))
					raise
				except ValueError, inst:
					g.log.msg("LOG_ERROR", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst))		


		#@write #self.__secrindex
		def __commit_secrindex(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):
			if not recmap: recmap = {}

			# print "...updating secrindex"
			# Security index
			for user, recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","self.__secrindex.addrefs: %r, len %r"%(user, len(recs)))
						self.__secrindex.addrefs(user, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))

			for user, recs in removerefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","secrindex.removerefs: user %r, len %r"%(user, len(recs)))
						self.__secrindex.removerefs(user, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
					raise



		#@write #self.__secrindex
		def __commit_secrindex_groups(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):
			# print "...updating secrindex"
			if not recmap: recmap = {}
			# Security Group index
			for user, recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","self.__secrindex_groups.addrefs: %r, len %r"%(user, len(recs)))
						self.__secrindex_groups.addrefs(user, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not add security index for group %s, records %s (%s)"%(user, recs, inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not add security index for group %s, records %s (%s)"%(user, recs, inst))

			for user, recs in removerefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","secrindex_groups.removerefs: user %r, len %r"%(user, len(recs)))
						self.__secrindex_groups.removerefs(user, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not remove security index for group %s, records %s (%s)"%(user, recs, inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not remove security index for group %s, records %s (%s)"%(user, recs, inst))
					raise




		#@write #self.__fieldindex*
		def __commit_paramindex(self, param, addrefs, delrefs, recmap=None, ctx=None, txn=None):
			"""commit param updates"""
			if not recmap: recmap = {}

			# addrefs = upds[0], delrefs = upds[1]
			if not addrefs and not delrefs:
				return
				#continue

			try:
				paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
				if paramindex == None:
					raise Exception, "Index was None; unindexable?"
			except bsddb3.db.DBError, inst:
				g.log.msg("LOG_CRITICAL","Could not open param index: %s (%s)"% (param, inst))
				raise
			except Exception, inst:
				g.log.msg("LOG_ERROR","Could not open param index: %s (%s)"% (param, inst))
				raise

			for newval,recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","param index %r.addrefs: %r '%r', %r"%(param, type(newval), newval, len(recs)))
						paramindex.addrefs(newval, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))

			for oldval,recs in delrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.log.msg("LOG_COMMIT_INDEX","param index %r.removerefs: %r '%r', %r"%(param, type(oldval), oldval, len(recs)))
						paramindex.removerefs(oldval, recs, txn=txn)
				except bsddb3.db.DBError, inst:
					g.log.msg("LOG_CRITICAL", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))
					raise
				except Exception, inst:
					g.log.msg("LOG_ERROR", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))




		# index update methods
		def __reindex_params(self, updrecs, cache=None, ctx=None, txn=None):
			"""update param indices"""
			# print "Calculating param index updates..."

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
			pd = self.__paramdefs.sget(key, txn=txn) # [key]
			addrefs = {}
			delrefs = {}

			# not indexable params/vartypes
			# if pd.name in ["recid","comments","permissions"]:
			#	return addrefs, delrefs

			if pd.vartype not in self.indexablevartypes or not pd.indexed:
				return addrefs, delrefs

			# remove oldval=newval; strip out wrong keys
			items = filter(lambda x:x[1] != x[2], items)

			if pd.vartype == "text":
				return self.__reindex_paramtext(key, items, ctx=ctx, txn=txn)

			#addrefs = dict([[i,set()] for i in set([i[1] for i in items])])
			#delrefs = dict([[i,set()] for i in set([i[2] for i in items])])
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

			allwords = set(addrefs.keys() + delrefs.keys()) - self.unindexed_words

			addrefs2 = {}
			delrefs2 = {}
			for i in allwords:
				# make set, remove unchanged items
				addrefs2[i] = set(addrefs.get(i,[]))
				delrefs2[i] = set(delrefs.get(i,[]))
				u = addrefs2[i] & delrefs2[i]
				addrefs2[i] -= u
				delrefs2[i] -= u


			return addrefs2, delrefs2



		# ian: todo: is re.compile expensive?
		def __reindex_getindexwords(self, value, ctx=None, txn=None):
			if value == None:
				return []
			m = re.compile('[\s]([a-zA-Z]+)[\s]|([0-9][.0-9]+)')
			return set(map(lambda x:x[0] or x[1], m.findall(unicode(value).lower())))




		def __reindex_time(self, updrecs, cache=None, ctx=None, txn=None):
			# print "Calculating time updates..."

			timeupdate = {}

			for updrec in updrecs:
				timeupdate[updrec.recid] = updrec.get("modifytime") or updrec.get("creationtime")

			return timeupdate



		def __reindex_security(self, updrecs, cache=None, ctx=None, txn=None):
			# print "Calculating security updates..."

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

				nperms = set(reduce(operator.concat, updrec["permissions"]))
				operms = set(reduce(operator.concat, orec.get("permissions",[[]])))

				#g.log.msg("LOG_INFO","__reindex_security: record %s, add %s, delete %s"%(updrec.recid, nperms - operms, operms - nperms))

				for user in nperms - operms:
					addrefs[user].append(recid)
				for user in operms - nperms:
					delrefs[user].append(recid)

			return addrefs, delrefs



		def __reindex_security_groups(self, updrecs, cache=None, ctx=None, txn=None):
			# print "Calculating security updates..."

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




		def __rebuild_secrindex(self, ctx=None, txn=None):


			g.log.msg("LOG_INFO","Rebuilding secrindex/secrindex_groups")
			
			g.log.msg("LOG_COMMIT_INDEX","self.__secrindex.truncate")
			self.__secrindex.truncate(txn=txn)
			g.log.msg("LOG_COMMIT_INDEX","self.__secrindex_groups.truncate")
			self.__secrindex_groups.truncate(txn=txn)
			
			pos = 0
			crecs = True
			recmap = {}
			
			while crecs:
				txn2 = self.newtxn(txn)
				
				crecs = self.getrecord(range(pos, pos+self.BLOCKLENGTH), filt=True, ctx=ctx, txn=txn2)
				pos += len(crecs)
						
				# by omitting cache, will be treated as new recs...		
				secr_addrefs, secr_removerefs = self.__reindex_security(crecs, ctx=ctx, txn=txn2)
				secrg_addrefs, secrg_removerefs = self.__reindex_security_groups(crecs, ctx=ctx, txn=txn2)

				# Security index
				self.__commit_secrindex(secr_addrefs, secr_removerefs, ctx=ctx, txn=txn2)
				self.__commit_secrindex_groups(secrg_addrefs, secrg_removerefs, ctx=ctx, txn=txn2)
				
				txn2.commit()
				#self.txncommit(txn2)


		###############################
		# section: permissions
		###############################




		# ian: todo: benchmark these again
		@DBProxy.publicmethod
		def filterbypermissions(self, recids, ctx=None, txn=None):

			# print "filterbypermissions: %s"%(len(recids))
			if not isinstance(recids, set):
				recids = set(recids)

			if ctx.checkreadadmin():
				return recids

			if len(recids) < 1000:
				return set([x.recid for x in self.getrecord(recids, filt=True, ctx=ctx, txn=txn)])
				
			find = set(recids)
			find -= self.__secrindex.get(ctx.username, set(), txn=txn)
			
			for group in sorted(ctx.groups):
				if find:
					find -= self.__secrindex_groups.get(group, set(), txn=txn)
			
			return recids - find

			# this is usually the fastest; it's the same as getindexbycontext basically...
			# method 2

			# ret = []
			# 
			# if ctx.username != None and ctx.username != "anonymous":
			# 	ret.extend(recids & set(self.__secrindex.get(ctx.username, [], txn=txn)))
			# 
			# for group in sorted(ctx.groups, reverse=True):
			# 	ret.extend(recids & set(self.__secrindex_groups.get(group, [], txn=txn)))
			# 
			# return set(ret)
			
			#ret=set()
			#ret |= recids & set(self.__secrindex[ctx.user])
			#recids -= ret

			# for group in sorted(ctx.groups, reverse=True):
			# 	#if recids:
			# 	#ret |= recids & set(self.__secrindex[group])
			# 	#recids -= ret
			# 	ret.extend(recids & set(self.__secrindex_groups.get(group, [], txn=txn)))
			#
			#
			# # method 1
			# ret=[]
			# for recid in recids:
			# 	if self.__secrindex.testref(ctx.user, recid):
			# 		ret.append(recid)
			# 		continue
			# 	if self.__secrindex.testref(-3, recid):
			# 		ret.append(recid)
			# 		continue
			# 	if self.__secrindex.testref(-4, recid):
			# 		ret.append(recid)
			# 		continue
			# 	for group in ctx.groups:
			# 		if self.__secrindex.testref(group, recid):
			# 			ret.append(recid)
			# 			continue
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
			
			addusers = set(reduce(operator.concat, umask))
			
			checkitems = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)

			if (addusers | addgroups | delusers | delgroups) - checkitems:
				raise subsystems.exceptions.SecurityError, "Invalid users/groups: %s"%((addusers | addgroups | delusers | delgroups) - checkitems)


			# change child perms
			if recurse:
				recids |= self.getchildren(recids, recurse=recurse, filt=True, flat=True, ctx=ctx, txn=txn)


				
			recs = self.getrecord(recids, filt=filt, ctx=ctx, txn=txn)
			if filt:
				recs = filter(lambda x:x.isowner(), recs)
			
			# print "setting permissions"
			
			for rec in recs:
				if addusers: rec.addumask(umask, reassign=reassign)
				if delusers: rec.removeuser(delusers)
				if addgroups: rec.addgroup(addgroups)
				if delgroups: rec.removegroup(delgroups)
				
				
			# Go ahead and directly commit here, since we know only permissions have changed...
			self.__commit_records(recs, [], onlypermissions=True, ctx=ctx, txn=txn)



		#############################
		# section: record views
		#############################


		# ian: todo: deprecate
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




		@DBProxy.publicmethod
		def getrecordrenderedviews(self, recid, ctx=None, txn=None):
			"""Render all views for a record."""

			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			recdef = self.getrecorddef(rec["rectype"], ctx=ctx, txn=txn)
			views = recdef.views
			views["mainview"] = recdef.mainview
			for i in views:
				views[i] = self.renderview(rec, viewdef=views[i], ctx=ctx, txn=txn)
			return views









		# It is a cold, cold, cruel world... moved to VartypeManager. This should be refactored someday.
		@DBProxy.publicmethod
		def renderview(self, *args, **kwargs):
			"""Render views"""
			# calls out to places that expect DBProxy need a DBProxy...
			kwargs["db"] = kwargs["ctx"].db
			kwargs.pop("ctx",None)
			kwargs.pop("txn",None)
			vtm = subsystems.datatypes.VartypeManager()
			return vtm.renderview(*args, **kwargs)



		###########################
		# section: backup / restore
		###########################



		def _backup(self, encode_func=pickle.dump, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""

				#if user!="root" :
				if not ctx.checkadmin():
					raise subsystems.exceptions.SecurityError, "Only root may backup the database"


				g.log.msg('LOG_INFO', 'backup has begun')
				#user,groups=self.checkcontext(ctx=ctx, txn=txn)
				user = ctx.username
				groups = ctx.groups

				if users == None: users = self.__users.keys(txn=txn)
				if paramdefs == None: paramdefs = set(self.__paramdefs.keys(txn=txn))
				if recorddefs == None: recorddefs = set(self.__recorddefs.keys(txn=txn))
				if records == None: records = set(range(0, self.__records.sget(-1, txn=txn)))#[ - 1]
				if workflows == None: workflows = set(self.__workflow.keys(txn=txn))
				if bdos == None: bdos = set(self.__bdocounter.keys(txn=txn))
				if isinstance(records, list) or isinstance(records, tuple): records = set(records)

				if outfile == None:
						out = open(self.path + "/backup.pkl", "w")
				else:
						out = open(outfile, "w")

				g.log.msg('LOG_INFO', 'backup file opened')
				# dump users
				for i in users: encode_func(self.__users.sget(i, txn=txn), out)
				g.log.msg('LOG_INFO', 'users dumped')

				# dump workflow
				for i in workflows: encode_func(self.__workflow.sget(i, txn=txn), out)
				g.log.msg('LOG_INFO', 'workflows dumped')

				# dump binary data objects
				encode_func("bdos", out)
				bd = {}
				for i in bdos: bd[i] = self.__bdocounter.sget(i, txn=txn)
				encode_func(bd, out)
				bd = None
				g.log.msg('LOG_INFO', 'bdos dumped')

				# dump paramdefs and tree
				def encode_relations(recordtree, records, dump_method, outfile, txn=txn):
					ch = []
					for i in records:
							c = tuple(set(dump_method(i, txn=txn)) & records)
							ch += ((i, c),)
					encode_func("pdchildren", out)
					encode_func(ch, out)

				for i in paramdefs: encode_func(self.__paramdefs.sget(i, txn=txn), out)
				g.log.msg('LOG_INFO', 'paramdefs dumped')
				encode_relations(self.__paramdefs, paramdefs, self.__paramdefs.children, out)
				g.log.msg('LOG_INFO', 'paramchildren dumped')
				encode_relations(self.__paramdefs, paramdefs, self.__paramdefs.cousins, out)
				g.log.msg('LOG_INFO', 'paramcousins dumped')

				# dump recorddefs and tree
				for i in recorddefs: encode_func(self.__recorddefs.sget(i, txn=txn), out)
				g.log.msg('LOG_INFO', 'recorddefs dumped')
				encode_relations(self.__recorddefs, recorddefs, self.__recorddefs.children, out)
				g.log.msg('LOG_INFO', 'recdefchildren dumped')
				encode_relations(self.__recorddefs, recorddefs, self.__recorddefs.cousins, out)
				g.log.msg('LOG_INFO', 'recdefcousins dumped')

				# dump actual database records
				g.log.msg('LOG_INFO', "Backing up %d/%d records" % (len(records), self.__records.sget(-1, txn=txn)))
				for i in records: encode_func(self.__records.sget(i, txn=txn), out)
				g.log.msg('LOG_INFO', 'records dumped')

				ch = []
				for i in records:
						c = [x for x in self.__records.children(i, txn=txn) if x in records]
						c = tuple(c)
						ch += ((i, c),)
				encode_func("recchildren", out)
				encode_func(ch, out)
				g.log.msg('LOG_INFO', 'rec children dumped')

				ch = []
				for i in records:
						c = set(self.__records.cousins(i, txn=txn))
						c &= records
						c = tuple(c)
						ch += ((i, c),)
				encode_func("reccousins", out)
				encode_func(ch, out)
				g.log.msg('LOG_INFO', 'rec cousins dumped')

				out.close()



		def _backup2(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""
				def enc(value, fil):
					if type(value) == dict:
						for x in value.items():
							#g.log(x)
							demjson.encode(x)
					value = {'type': type(value).__name__, 'data': demjson.encode(value, encoding='utf-8')}
					fil.write('\n')
				self._backup(enc,users, paramdefs, recorddefs, records, workflows, bdos, outfile, ctx=ctx, txn=txn)


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
				# ian: changed to copy -- safer.
				shutil.copy(file_, os.path.join(archivepath, os.path.basename(file_)))
				# os.rename(file_, os.path.join(archivepath, os.path.basename(file_)))



		def __restore_rec(self, recblock,  recmap, ctx=None, txn=None):
			def swapin(obj, key, value):
				result = getattr(obj, key)
				setattr(obj, key, value)
				return result

			oldids = map(lambda rec: swapin(rec, 'recid', None), recblock)

			newrecs = self.putrecord(recblock, warning=1, ctx=ctx, txn=txn)

			for oldid,newrec in itertools.izip(oldids,newrecs):
				recmap[oldid] = newrec.recid
				if oldid != newrec.recid:
					g.log.msg("LOG_WARNING", "Warning: recid %s changed to %s"%(oldid,newrec.recid))
			return len(newrecs)


		def __restore_commitblocks(self, *blocks, **kwargs):
			ctx, txn = kwargs.get('ctx'), kwargs.get('txn')
			mp = kwargs.get('map')
			changesmade = False
			if any(blocks):

				to_commit = filter(None, blocks)

				commit_funcs = {
					dataobjects.paramdef.ParamDef: lambda r: self.putparamdef(r, ctx=ctx, txn=txn),
					dataobjects.recorddef.RecordDef: lambda r: self.putrecorddef(r, ctx=ctx, txn=txn),
					dataobjects.user.User: lambda r: self.putuser(r, ctx=ctx, txn=txn)
				}

				for block in to_commit:

					for item in block:
						emen2.migrate.upgrade(item, ctx=ctx, txn=txn)

					if isinstance(block[0], dataobjects.record.Record):
						self.__restore_rec(block, mp, ctx=ctx, txn=txn)
					else:
						map(commit_funcs[type(block[0])], block)

					del block[:]

				changesmade = True

			return changesmade


		def __restore_openfile(self, restorefile):
				if type(restorefile) == file:
					fin = restorefile

				elif os.access(str(restorefile), os.R_OK):
					if restorefile.endswith('.bz2'):
						fin = os.popen("bzcat %s" % restorefile, "r")
					else:
						fin = open(restorefile, "r")

				elif os.access(self.path + "/backup.pkl", os.R_OK):
					fin = open(self.path + "/backup.pkl", "r")

				elif os.access(self.path + "/backup.pkl.bz2", os.R_OK) :
					fin = os.popen("bzcat " + self.path + "/backup.pkl.bz2", "r")

				elif os.access(self.path + "/../backup.pkl.bz2", os.R_OK) :
					fin = os.popen("bzcat " + self.path + "/../backup.pkl.bz2", "r")

				else:
					raise IOError, "Restore file (e.g. backup.pkl) not present"
				return fin


		def __restore_relate(self, r, fin, types, recmap, txn=None):
			rr = pickle.load(fin)
			if r not in types: return False

			def link(lis, link_func, txn=txn):
				for a,bl in lis:
					for b in bl:
						try:
							link_func(a,b, txn=txn)
						except Exception, e:
							self.LOG("LOG_ERROR","Error linking during restore: %s <-> %s (%s)"%(a,b,e))

			simple_choices = dict(
				pdchildren=self.__paramdefs.pclink,
				pdcousins=self.__paramdefs.link,
				rdchildren=self.__recorddefs.pclink,
				rdcousins=self.__recorddefs.link,
				reccousins=self.__records.link
			)

			if r == "bdos":
				g.log.msg('LOG_INFO', "bdo")
				# read the dictionary of bdos
				for i, d in rr.items():
					self.__bdocounter.set(i, d, txn=txn)

			elif r == "recchildren":
				g.log.msg('LOG_INFO', "recchildren")

				links = []
				for p, cl in rr:
					for c in cl:
						links.append((recmap[p], recmap[c]))

				self.__records.pclinks(links, txn=txn)


			elif r in simple_choices:
				g.log.msg('LOG_INFO', r)
				link(rr, simple_choices[r])

			else:
				g.log.msg('LOG_ERROR', "Unknown category: ", r)
			return True


		@DBProxy.publicmethod
		def restore(self, restorefile=None, types=None, restoreversion=None, ctx=None, txn=None):
				"""This will restore the database from a backup file. It is nondestructive, in that new items are
				added to the existing database. Naming conflicts will be reported, and the new version
				will take precedence, except for Records, which are always appended to the end of the database
				regardless of their original id numbers. If maintaining record id numbers is important, then a full
				backup of the database must be performed, and the restore must be performed on an empty database."""

				import emen2.migrate

				if not txn: txn = None
				g.log.msg('LOG_INFO', "Begin restore operation")

				if not self.__importmode:
					g.log.msg('LOG_WARNING', "WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
					return



				# ian: todo: this will be better implemented in a flexible way when restore is moved into a standalone module


				# ian: todo: change this to some other mechanism...
				ctx = self.__makerootcontext()
				user, groups = ctx.username, ctx.groups

				if not ctx.checkadmin():
					raise subsystems.exceptions.SecurityError, "Database restore requires admin access"

				recmap = {}
				nrec = 0

				t0 = time.time()
				tmpindex = {}
				nel = 0


				recblock, paramblock, recdefblock, userblock = [],[],[],[]
				#blocklength = 100000
				commitrecs = False
				changesmade = False
				OVERWRITE = False

				if not types:
					types = set(["record", "user", "workflow",
						"recorddef", "paramdef", "bdos",
						"pdchildren", "pdcousins", "rdcousins",
						"recchildren", "reccousins"])


				iteration = 0
				cleanup_needed = False


				if OVERWRITE:
					existing_users = set()
					existing_paramdefs = set()
					existing_recorddefs = set()
					existing_groups = set()
				else:
					existing_users = self.getusernames(ctx=ctx, txn=txn)
					existing_paramdefs = self.getparamdefnames(ctx=ctx, txn=txn)
					existing_recorddefs = self.getrecorddefnames(ctx=ctx, txn=txn)
					existing_groups = self.getgroupnames(ctx=ctx, txn=txn)


				# Record = dataobjects.record.Record
				# RecordDef = dataobjects.recorddef.RecordDef
				# ParamDef = dataobjects.paramdef.ParamDef
				# User = dataobjects.user.User

				fin = self.__restore_openfile(restorefile)
				running = True
				try:
					with emen2.util.ticker.spinning_distraction():
						while running:

							try:
								r = pickle.load(fin)
							except Exception, e:
								#print "Pickle load error: %s"%e
								self.LOG("LOG_WARNING","Pickle load error (eof?) %s"%e)
								raise EOFError

							commitrecs = False

							# insert and renumber record
							if isinstance(r, dataobjects.record.Record) and "record" in types:
								recblock.append(r)
							elif isinstance(r, dataobjects.recorddef.RecordDef) and "recorddef" in types and r.name not in existing_recorddefs:
								recdefblock.append(r)
							elif isinstance(r, dataobjects.paramdef.ParamDef) and "paramdef" in types and r.name not in existing_paramdefs:
								paramblock.append(r)
							elif isinstance(r, dataobjects.user.User) and "user" in types and r.username not in existing_users:
								userblock.append(r)

							if  sum(len(block) for block in [recblock, userblock, paramblock, recdefblock]) >= self.BLOCKLENGTH:
								commitrecs = True

							restoreblocks = lambda: self.__restore_commitblocks(userblock, paramblock, recdefblock, recblock, ctx=ctx, txn=txn, map=recmap)

							if commitrecs:
								txn = txn or self.newtxn()
							elif txn is None:
								txn = self.newtxn()

							iteration += 1

							try:
								if commitrecs:
									changesmade = restoreblocks()

								# insert Workflow
								elif isinstance(r, dataobjects.workflow.WorkFlow) and "workflow" in types:
									self.__workflow.set(r.wfid, r, txn=txn)
									changesmade = True

								elif isinstance(r, str):
									changesmade = restoreblocks()
									changesmade = self.__restore_relate(r, fin, types, recmap, txn=txn)

							finally:
								if changesmade:
									self.__closeparamindexes(ctx=ctx, txn=txn)
									self.txncommit(txn=txn)
									self.archivelogs(ctx=ctx, txn=txn)
									DB_syncall()
									txn = None
									changesmade = False


				except EOFError:
					g.log.msg('LOG_DEBUG', 'EOF')
					g.log.msg('LOG_INFO', 'Import Done')
					running = False

				g.log.msg('LOG_INFO', "Done!")
				if txn: self.txncommit(txn=txn)

				txn = self.newtxn()
				changesmade = restoreblocks()

				if txn:
					self.txncommit(txn=txn)
					g.log.msg('LOG_INFO', "Import Complete, checkpointing")
					self.__dbenv.txn_checkpoint()

				assert len(self.txnlog) == 0
				g.log.msg('LOG_DEBUG', 'restore done')


		def restoretest(self, ctx=None, txn=None):
			pass
			# NOT UPDATED...?
			# """This method will check a database backup and produce some statistics without modifying the current database."""
			#
			# if not self.__importmode: print("WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
			#
			# #user,groups=self.checkcontext(ctx=ctx, txn=txn)
			# ctx = self.__getcontext(, ctx=ctx, txn=txn)
			# user = ctx.user
			# groups = ctx.groups
			# #if user!="root" :
			# if not ctx.checkadmin():
			# 		raise subsystems.exceptions., "Only root may restore the database"
			#
			# if os.access(self.path + "/backup.pkl", R_OK) : fin = open(self.path + "/backup.pkl", "r")
			# elif os.access(self.path + "/backup.pkl.bz2", R_OK) : fin = os.popen("bzcat " + self.path + "/backup.pkl.bz2", "r")
			# elif os.access(self.path + "/../backup.pkl.bz2", R_OK) : fin = os.popen("bzcat " + self.path + "/../backup.pkl.bz2", "r")
			# else: raise IOError, "backup.pkl not present"
			#
			# recmap = {}
			# nrec = 0
			# t0 = time.time()
			# tmpindex = {}
			#
			# nu, npd, nrd, nr, np = 0, 0, 0, 0, 0
			#
			# while (1):
			# 		try:
			# 				r = pickle.load(fin)
			# 		except:
			# 				break
			#
			# 		# insert User
			# 		if isinstance(r, User) :
			# 				nu += 1
			#
			# 		# insert paramdef
			# 		elif isinstance(r, ParamDef) :
			# 				npd += 1
			#
			# 		# insert recorddef
			# 		elif isinstance(r, RecordDef) :
			# 				nrd += 1
			#
			# 		# insert and renumber record
			# 		elif isinstance(r, Record) :
			# 				r.setContext(ctx)
			# 				try:
			# 						o = r._Record__owner
			# 						a = r._Record__permissions
			# 						r._Record__permissions = (a[0], a[1], a[2], (o,))
			# 						del r._Record__owner
			# 				except:
			# 						pass
			# 				if (nr < 20) : g.log(r["identifier"])
			# 				nr += 1
			#
			# 		elif isinstance(r, str) :
			# 				if r == "pdchildren" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "pdcousins" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "rdchildren" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "rdcousins" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "recchildren" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "reccousins" :
			# 						rr = pickle.load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				else : g.log("Unknown category ", r)
			#
			# g.log("Users=", nu, "	 ParamDef=", npd, "	 RecDef=", nrd, "	 Records=", nr, "	 Links=", np)
