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

from functools import partial, wraps

import emen2
import emen2.util.utils
import emen2.util.ticker

import emen2config
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


import DBProxy
import DBExt
import datatypes
import extensions
import subsystems


#print "\n\nIMPORT DB\n\n"
#traceback.print_stack()


from DBFlags import *

# Constants... move these to config file
TIMESTR = "%Y/%m/%d %H:%M:%S"
MAXIDLE = 604800
DEBUG = 0



def gettime():
	"""Return database local time in format %s"""%TIMESTR
	return time.strftime(TIMESTR)


def DB_syncall():
	"""This 'syncs' all open databases"""
	#if DEBUG > 2:
	#	g.debug("sync %d BDB databases" % (len(BTree.alltrees) + len(IntBTree.alltrees) + len(FieldBTree.alltrees)))
	#t = time.time()
	for i in subsystems.btrees2.BTree.alltrees.keys():
		i.sync()
	# for i in subsystems.btrees2.RelateBTree.alltrees.keys(): i.sync()
	# for i in subsystems.btrees2.FieldBTree.alltrees.keys(): i.sync()
	# g.debug("%f sec to sync"%(time.time()-t))



def DB_cleanup():
	"""This does at_exit cleanup. It would be nice if this were always called, but if python is killed
	with a signal, it isn't. This tries to nicely close everything in the database so no recovery is
	necessary at the next restart"""
	sys.stdout.flush()
	print >> sys.stderr, "DB has %d transactions left" % DB.txncounter
	
	tx_max = dbenv.get_tx_max()
	print "Open transactions: %s"%tx_max
	
	txn_stat = dbenv.txn_stat()
	print "Transaction stats: "
	for k,v in txn_stat.items():
		print "\t%s: %s"%(k,v)
	
	log_archive = dbenv.log_archive()
	print "Archive: %s"%log_archive
	
	lock_stat = dbenv.lock_stat()
	print "Lock stats: "
	for k,v in lock_stat.items():
		print "\t%s: %s"%(k,v)

	print "Mutex stats: "
	# print dir(dbenv)
	print dbenv.mutex_get_max()
	#print dbenv.mutex_stat_print()
	
	
	
	print >> sys.stderr, "Closing %d BDB databases"%(len(subsystems.btrees2.BTree.alltrees) + len(subsystems.btrees2.RelateBTree.alltrees) + len(subsystems.btrees2.FieldBTree.alltrees))

	if DEBUG > 2:
		print >> sys.stderr, len(subsystems.btrees2.BTree.alltrees), 'BTrees'

	for i in subsystems.btrees2.BTree.alltrees.keys():
		#if DEBUG > 2:
		sys.stderr.write('closing %s\n' % unicode(i))
		i.close()
		if DEBUG > 2: sys.stderr.write('%s closed\n' % unicode(i))
		if DEBUG > 2: print >> sys.stderr, '\n', len(subsystems.btrees2.RelateBTree.alltrees), 'RelateBTrees'

	dbenv.close()

	# for i in subsystems.btrees2.RelateBTree.alltrees.keys():
	# 	i.close()
	# 	if DEBUG > 2: sys.stderr.write('.')
	# 	if DEBUG > 2: print >> sys.stderr, '\n', len(subsystems.btrees2.FieldBTree.alltrees), 'FieldBTrees'
	# 
	# for i in subsystems.btrees2.FieldBTree.alltrees.keys():
	# 	i.close()
	# 	if DEBUG > 2: sys.stderr.write('.')
	# 	if DEBUG > 2: sys.stderr.write('\n')
	# 
	# for i in subsystems.btrees2.IndexKeyBTree.alltrees.keys():
	# 	i.close()
	# 	if DEBUG > 2: sys.stderr.write('.')
	# 	if DEBUG > 2: sys.stderr.write('\n')


# This rmakes sure the database gets closed properly at exit
atexit.register(DB_cleanup)















#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()
class DB(object):
		"""This class represents the database as a whole. There are 3 primary identifiers used in the database:
		dbid - Database id, a unique identifier for this database server
		recid - Record id, a unique (32 bit int) identifier for a particular record
		ctxid - A key for a database 'context' (also called a session), allows access for pre-authenticated user

		TODO : Probably should make more of the member variables private for slightly better security"""

		log_levels = {
			0: 'LOG_CRITICAL',
			1: 'LOG_CRITICAL',
			2: 'LOG_ERROR',
			3: 'LOG_WARNING',
			4: 'LOG_INFO',
			5: 'LOG_DEBUG',
			6: 'LOG_DEBUG',
			7: 'LOG_COMMIT'
			}



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
				g.debug.msg("LOG_INFO","Note: transaction support disabled")
				self.newtxn = self.newtxn2


			
			self.path = path or g.EMEN2DBPATH
			self.logfile = self.path + "/" + logfile
			self.lastctxclean = time.time()
			self.__importmode = importmode
			self.txnid = 0
			self.txnlog = {}

			self.vtm = datatypes.datatypes.VartypeManager()			
			self.indexablevartypes = set([i.getvartype() for i in filter(lambda x:x.getindextype(), [self.vtm.getvartype(i) for i in self.vtm.getvartypes()])])
			self.unindexed_words = set(["in", "of", "for", "this", "the", "at", "to", "from", "at", "for", "and", "it", "or"])

			self.MAXRECURSE = 50

			if recover:
				ENVOPENFLAGS |= bsddb3.db.DB_RECOVER

			# This sets up a DB environment, which allows multithreaded access, transactions, etc.
			if not os.access(self.path + "/home", os.F_OK):
				os.makedirs(self.path + "/home")
				print "Copying DB_CONFIG"
				dbci = file(g.EMEN2ROOT+'/DB_CONFIG')
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


			self.LOG(4, "Database opening...")


			self.__dbenv = bsddb3.db.DBEnv() #db.DBEnv()
			self.__dbenv.set_data_dir(self.path)
			global dbenv
			dbenv = self.__dbenv

			# # #self.__dbenv.set_cachesize(0, cachesize, 4) # gbytes, bytes, ncache (splits into groups)
			# self.__dbenv.set_cachesize(*CACHESIZE)
			# self.__dbenv.set_lg_bsize(LG_BSIZE)
			# self.__dbenv.set_lg_max(LG_MAX)
			# self.__dbenv.set_lk_detect(bsddb3.db.DB_LOCK_DEFAULT) # internal deadlock detection
			# self.__dbenv.set_lk_max_locks(MAX_LOCKS)
			# self.__dbenv.set_lk_max_lockers(MAX_LOCKERS)
			# self.__dbenv.set_lk_max_objects(MAX_OBJECTS)
			# set_lg_regionmax
			
			
			# ian: todo: is this method no longer in the bsddb3 API?
			#if self.__dbenv.failchk(flags=0):
			#	self.LOG(1,"Database recovery required")
			#	sys.exit(1)

			self.__dbenv.open(self.path + "/home", ENVOPENFLAGS)


			# Open Database
			
			txn = self.newtxn()
			ctx = self.__makerootcontext(txn=txn, dbproxy=True)


			# Users
			# active database users / groups
			self.__users = subsystems.btrees2.BTree("users", keytype="s", filename=self.path+"/security/users.bdb", dbenv=self.__dbenv, txn=txn)

			self.__groupsbyuser = subsystems.btrees2.IndexKeyBTree("groupsbyuser", keytype="s", filename=self.path+"/security/groupsbyuser", dbenv=self.__dbenv, txn=txn)

			self.__groups = subsystems.btrees2.BTree("groups", keytype="ds", filename=self.path+"/security/groups.bdb", dbenv=self.__dbenv, txn=txn)
			#self.__updatecontexts = False

			# new users pending approval
			self.__newuserqueue = subsystems.btrees2.BTree("newusers", keytype="s", filename=self.path+"/security/newusers.bdb", dbenv=self.__dbenv, txn=txn)

			# multisession persistent contexts
			self.__contexts_p = subsystems.btrees2.BTree("contexts", keytype="s", filename=self.path+"/security/contexts.bdb", dbenv=self.__dbenv, txn=txn)

			# local cache dictionary of valid contexts
			self.__contexts = {}




			# Binary data names indexed by date
			self.__bdocounter = subsystems.btrees2.BTree("BinNames", keytype="s", filename=self.path+"/BinNames.bdb", dbenv=self.__dbenv, txn=txn)

			# Defined ParamDefs
			# ParamDef objects indexed by name
			self.__paramdefs = subsystems.btrees2.RelateBTree("ParamDefs", keytype="s", filename=self.path+"/ParamDefs.bdb", dbenv=self.__dbenv, txn=txn)

			# Defined RecordDefs
			# RecordDef objects indexed by name
			self.__recorddefs = subsystems.btrees2.RelateBTree("RecordDefs", keytype="s", filename=self.path+"/RecordDefs.bdb", dbenv=self.__dbenv, txn=txn)



			# The actual database, keyed by recid, a positive integer unique in this DB instance
			# ian todo: check this statement:
			# 2 special keys exist, the record counter is stored with key -1
			# and database information is stored with key=0

			# The actual database, containing id referenced Records
			self.__records = subsystems.btrees2.RelateBTree("database", keytype="d", filename=self.path+"/database.bdb", dbenv=self.__dbenv, txn=txn)

			# Indices

			# index of records each user can read
			self.__secrindex = subsystems.btrees2.FieldBTree("secrindex", filename=self.path+"/security/roindex.bdb", keytype="ds", dbenv=self.__dbenv, txn=txn)

			# index of records belonging to each RecordDef
			self.__recorddefindex = subsystems.btrees2.FieldBTree("RecordDefindex", filename=self.path+"/RecordDefindex.bdb", keytype="s", dbenv=self.__dbenv, txn=txn)

			# key=record id, value=last time record was changed
			self.__timeindex = subsystems.btrees2.BTree("TimeChangedindex", keytype="d", filename=self.path+"/TimeChangedindex.bdb", dbenv=self.__dbenv, txn=txn)

			# dictionary of FieldBTrees, 1 per ParamDef, not opened until needed
			self.__fieldindex = {}


			self.__indexkeys = subsystems.btrees2.IndexKeyBTree("IndexKeys", keytype="s", filename=self.path+"/IndexKeys.bdb", dbenv=self.__dbenv, txn=txn)




			# Workflow database, user indexed btree of lists of things to do
			# again, key -1 is used to store the wfid counter
			self.__workflow = subsystems.btrees2.BTree("workflow", keytype="d", filename=self.path+"/workflow.bdb", dbenv=self.__dbenv, txn=txn)


			# USE OF SEQUENCES DISABLED DUE TO DATABASE LOCKUPS
			#db sequence
			# self.__dbseq = self.__records.create_sequence()

			#self.__recorddefbyrec = IntBTree("RecordDefByRec", self.path + "/RecordDefByRec.bdb", dbenv=self.__dbenv, relate=0)

			# The mirror database for storing offsite records
			#self.__mirrorrecords = BTree("mirrordatabase", filename=self.path+"/mirrordatabase.bdb", dbenv=self.__dbenv)


			#try:
			#	max = self.__workflow[-1]
			#
			#except:
			#	self.__workflow[-1] = 1
			#	self.LOG(3, "New workflow database created")


			#txn = self.newtxn()

			try:
				
				try:
					maxr = self.__records.sget(-1, txn=txn)
				except:
					self.__records.set(-1, 0, txn=txn)
					self.LOG(3, "New records database created")
					self.__createskeletondb(ctx=ctx, txn=txn)


				g.debug.add_output(self.log_levels.values(), file(self.logfile, "a"))
				self.__anonymouscontext = self.__makecontext(dbproxy=True)


			except:
				txn and self.txnabort(txn=txn)
				raise
			else:
				self.txncommit(txn=txn)


			#self.__anonymouscontext = self._getcontext(_actxid, None)






		def __createskeletondb(self, ctx=None, txn=None):
			# typically uses SpecialRootContext
			
			import skeleton
						
			for i in skeleton.core_paramdefs.items:
				self.putparamdef(i, ctx=ctx, txn=txn)
			
			for i in skeleton.core_recorddefs.items:
				self.putrecorddef(i, ctx=ctx, txn=txn)			

			for i in skeleton.core_users.items:
				self.adduser(i, ctx=ctx, txn=txn)
			
			for i in skeleton.core_groups.items:
				self.putgroup(i, ctx=ctx, txn=txn)
			
			self.setpassword("root", g.ROOTPW, g.ROOTPW, ctx=ctx, txn=txn)

			# pds = [datatypes.datastorage.ParamDef(i) for i in skeleton.core_paramdefs.items]
			# rds = [datatypes.datastorage.RecordDef(i) for i in skeleton.core_recorddefs.items]
			# users = [datatypes.user.User(i) for i in skeleton.core_users.items]
			# groups = [datatypes.user.Group(i) for i in skeleton.core_groups.items]

			#[i.validate() for i in pds]
			#[i.validate() for i in rds]
			#[i.validate() for i in users]
			#[i.validate() for i in groups]

			#self.__commit_paramdefs(pds, ctx=ctx, txn=txn)
			#self.__commit_recorddefs(rds, ctx=ctx, txn=txn)
			#self.__commit_users(users, ctx=ctx, txn=txn)
			#self.__commit_groups(groups, ctx=ctx, txn=txn)
			
			# ctx.getuser(txn=txn)
			
			



		###############################
		# section: txn
		###############################



		txncounter = 0
		# one of these 2 methods is mapped to self.newtxn()
		def newtxn1(self, parent=None, ctx=None):
			g.debug.msg("LOG_INFO","NEW TXN, PARENT --> %s"%parent)
			#traceback.print_stack()

			txn = self.__dbenv.txn_begin(parent=parent)
			try:
				type(self).txncounter += 1
				self.txnlog[id(txn)] = txn
			except:
				self.txnabort(ctx=ctx, txn=txn)
				raise
			return txn


		def newtxn(self, ctx=None, txn=None):
			return None


		def newtxn2(self, ctx=None, txn=None):
			return None


		def txncheck(self, ctx=None, txn=None):
			if not txn:
				txn = self.newtxn(ctx=ctx)
			return txn


		def txnabort(self, txnid=0, ctx=None, txn=None):
			g.debug.msg('LOG_ERROR', "TXN ABORT --> %s"%txn)
			#traceback.print_stack()

			txn = self.txnlog.get(txnid, txn)
			if txn:
				txn.abort()
				if id(txn) in self.txnlog:
					del self.txnlog[id(txn)]
				type(self).txncounter -= 1
			else:
				raise ValueError, 'transaction not found'


		def txncommit(self, txnid=0, ctx=None, txn=None):
			g.debug.msg("LOG_INFO","TXN COMMIT --> %s"%txn)
			#traceback.print_stack()
			
			txn = self.txnlog.get(txnid, txn)
			if txn != None:
				txn.commit()
				if id(txn) in self.txnlog:
					del self.txnlog[id(txn)]
				type(self).txncounter -= 1
			#else:
			#	raise ValueError, 'transaction not found'
			#if not self.__importmode:
			#	DB_syncall()




		###############################
		# section: utility
		###############################


		@DBProxy.publicmethod
		def raise_exception(self, ctx=None, txn=None):
			raise Exception, "Test! ctxid %s host %s txn %s"%(ctx.ctxid, ctx.host, txn)


		def LOG(self, level, message, ctx=None, txn=None):
			"""level is an integer describing the seriousness of the error:
			0 - security, security-related messages
			1 - critical, likely to cause a crash
			2 - serious, user will experience problems
			3 - minor, likely to cause minor annoyances
			4 - info, informational only
			5 - verbose, verbose logging
			6 - debug only"""

			txn = txn or 1
			if type(level) is int and (level < 0 or level > 7):
				level = 6
			try:
				g.debug.msg(self.log_levels.get(level, level), "%s: (%s) %s" % (self.__gettime(ctx=ctx,txn=txn), self.log_levels.get(level, level), message))
			except:
				traceback.print_exc(file=sys.stdout)
				g.debug.msg('LOG_CRITICAL', "Critical error!!! Cannot write log message to '%s'")


		# needs txn?
		def __str__(self):
			"""Try to print something useful"""
			return "Database %d records\n( %s )"%(int(self.__records.get(-1,0)), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))


		# needs txn?
		def __del__(self):
			self.close()


		# ian: todo
		def closedb(self, ctx=None, txn=None):
			g.debug.msg('LOG_INFO', 'closing dbs')
			if self.__allowclose == True:
				for btree in self.__dict__.values():
					if getattr(btree, '__class__', object).__name__.endswith('BTree'):
						try: btree.close()
						except bsddb3.db.InvalidArgError, e: g.debug.msg('LOG_ERROR', e)
					for btree in self.__fieldindex.values(): btree.close()


		def close(self, ctx=None, txn=None):
			self.closedb(ctx, txn=txn)
			self.__dbenv.close()
			# pass
			# g.debug.msg('LOG_DEBUG', self.__btreelist)
			# self.__btreelist.extend(self.__fieldindex.values())
			# g.debug.msg('LOG_DEBUG', self.__btreelist)
			# for bt in self.__btreelist:
			# 	 g.debug('--', bt ; sys.stdout.flush())
			# 	 bt.close()




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
			return gettime()


		def __gettime(self, ctx=None, txn=None):
			return gettime()



		###############################
		# section: login / passwords
		###############################

		def __makecontext(self, username="anonymous", host=None, ctx=None, txn=None, dbproxy=False):
			'''so we can simulate a context for approveuser'''
			ctx = datatypes.user.Context(username=username, host=host)
			if dbproxy:
				ctx.db = DBProxy.DBProxy(db=self, ctx=ctx, txn=txn)
			else:
				ctx.db = self
			return ctx
				
				
		def __makerootcontext(self, ctx=None, txn=None, dbproxy=False):
			ctx = datatypes.user.SpecialRootContext()
			ctx.db = DBProxy.DBProxy(db=self, ctx=ctx, txn=txn)
			if dbproxy:
				ctx.db = DBProxy.DBProxy(db=self, ctx=ctx, txn=txn)
			else:
				ctx.db = self
			
			return ctx



		# No longer public method; only through DBProxy to force host=...
		def _login(self, username="anonymous", password="", host=None, maxidle=MAXIDLE, ctx=None, txn=None):
			"""Logs a given user in to the database and returns a ctxid, which can then be used for
			subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""

			newcontext = None
			username = unicode(username)

			# Anonymous access
			if username == "anonymous":
				newcontext = self.__anonymouscontext

			else:
				checkpass = self.__checkpassword(username, password, ctx=ctx, txn=txn)

				# Admins can "su"
				if checkpass or self.checkadmin(ctx=ctx, txn=txn):
					newcontext = self.__makecontext(username, host, dbproxy=False)

				else:
					self.LOG(0, "Invalid password: %s (%s)" % (username, host), ctx=ctx, txn=txn)
					raise subsystems.exceptions.AuthenticationError, subsystems.exceptions.AuthenticationError.__doc__


			try:
				self.__setcontext(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
				self.LOG(4, "Login succeeded %s (%s)" % (username, newcontext.ctxid), ctx=ctx, txn=txn)

			except:
				self.LOG(4, "Error writing login context, txn aborting!", ctx=ctx, txn=txn)
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
			try:
				self.__setcontext(ctx.ctxid, None, ctx=ctx, txn=txn)
			except:
				pass



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
					self.LOG(4, "Expire context (%s) %d" % (context.ctxid, time.time() - context.time), ctx=ctx, txn=txn)
					self.__setcontext(context.ctxid, None, ctx=ctx, txn=txn)



		#@write #self.__contexts_p
		def __setcontext(self, ctxid, context, ctx=None, txn=None):
			"""Add or delete context"""

			#@begin

			# set context
			if context != None:

				# any time you set the context, delete the cached context
				# this will retrieve it from disk next time it's needed

				try:
					del self.__contexts[ctxid]
				except Exception, inst:
					pass

				try:
					context.db = None
					context._user = None
					self.__contexts_p.set(ctxid, context, txn=txn)
					g.debug.msg("LOG_COMMIT","Commit: self.__contexts_p.set: %r"%context.ctxid)

				# except ValueError, inst:
				# 	g.debug.msg("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst))
				#
				# except db.DBError, inst:
				except Exception, inst:
					g.debug.msg("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst))
					raise


			# delete context
			else:
				try:
					del self.__contexts[ctxid]
				except Exception, inst:
					pass

				try:
					self.__contexts_p.set(ctxid, None, txn=txn) #del ... [ctxid]
					g.debug.msg("LOG_COMMIT","Commit: self.__contexts_p.__delitem__: %r"%ctxid)

				except Exception, inst:
					g.debug.msg("LOG_CRITICAL","Unable to delete persistent context %s (%s)"%(ctxid, inst))
					raise

			#@end



		#def __init_context(self, context, user=None, txn=None):
		#	g.debug("setting context user")
		#	context.db = self
		#	context._user = user or self.getuser(context.__username, ctx=context, txn=txn)


		def _getcontext(self, ctxid, host, ctx=None, txn=None):
			"""Takes a ctxid key and returns a context (for internal use only)
			Note that both key and host must match. Returns context instance."""

			if not ctxid:
				return self.__anonymouscontext

			if (time.time() > self.lastctxclean + 30): # or self.__updatecontexts):
				# maybe not the perfect place to do this, but it will have to do
				self.__cleanupcontexts(ctx=ctx, txn=txn)


			try:
				context = self.__contexts[ctxid]
				return context

			except:
				try:
					context = self.__contexts_p.sget(ctxid, txn=txn) #[key]
				except Exception, inst:
					self.LOG(4, "Session expired %s (%s)" %(ctxid, inst), ctx=ctx, txn=txn)
					raise subsystems.exceptions.SessionError, "Session expired: %s (%s)"%(ctxid, inst)


			if host and host != context.host :
				self.LOG(0, "Hacker alert! Attempt to spoof context (%s != %s)" % (host, context.host), ctx=ctx, txn=txn)
				raise subsystems.exceptions.SessionError, "Bad address match, login sessions cannot be shared"


			# this sets up db handle ref, users, groups for context...
			context.db = self
			context.getuser()

			self.__contexts[ctxid] = context		# cache result from database

			context.time = time.time()

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
			return ctx.checkadmin()



		@DBProxy.publicmethod
		def checkreadadmin(self, ctx=None, txn=None):
			"""Checks if the user has global read access. Returns bool."""
			return ctx.checkreadadmin()



		@DBProxy.publicmethod
		def checkcreate(self, ctx=None, txn=None):
			"""Check for permission to create records. Returns bool."""
			return ctx.checkcreate()



		def loginuser(self, ctx=None, txn=None):
			"""Who am I?"""
			return ctx.username




		###############################
		# section: binaries
		###############################

		@DBProxy.publicmethod
		def newbinary(self, *args, **kwargs):
			raise Exception, "Use putbinary"




		#@txn
		#@write #self.__bdocounter
		@DBProxy.publicmethod
		def putbinary(self, filename, recid, validate=True, key=None, filedata=None, param=None, uri=None, ctx=None, txn=None):
			"""Get a storage path for a new binary object. Must have a
			recordid that references this binary, used for permissions. Returns a tuple
			with the identifier for later retrieval and the absolute path"""


			#if filename == None or unicode(filename) == "":
			if not filename:
				raise ValueError, "Filename may not be 'None'"

			if key and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admins may manipulate binary tree directly"

			if not validate and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"
							

			# ian: todo: acquire lock?
			rec = self.getrecord(recid, ctx=ctx, txn=txn)

			if not rec.writable():
				raise subsystems.exceptions.SecurityError, "Write permission needed on referenced record."


			bdoo = self.__putbinary(filename, recid, key=key, uri=uri, ctx=ctx, txn=txn)


			#g.debug("Writing to record")

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


			nb = datatypes.datastorage.Binary()
			nb["uri"] = uri
			nb["filename"] = filename
			nb["recid"] = recid
			nb["creator"] = ctx.username
			nb["creationtime"] = self.gettime()
			nb["name"] = datekey + "%05X"%newid

			bdo[newid] = nb #(filename, recid, uri)
			self.__bdocounter.set(datekey, bdo, txn=txn)

			g.debug.msg("LOG_COMMIT","Commit: self.__bdocounter.set: %s"%datekey)
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

			datekey = "%04d%02d%02d" % (year, mon, day)

			for i in g.BINARYPATH:
				if datekey >= i[0] and datekey < i[1]:
					# actual storage path
					filepath = "%s/%04d/%02d/%02d" % (i[2], year, mon, day)
					g.debug.msg("LOG_DEBUG","Filepath for binary bdokey %s is %s"%(bdokey, filepath))
					break
			else:
				raise KeyError, "No storage specified for date %s" % key


			# try to make sure the directory exists
			try:
				os.makedirs(filepath)
			except:
				pass


			filename = filepath + "/%05X"%newid
			g.debug.msg("LOG_DEBUG","filename is %s"%filename)

			#todo: ian: raise exception if overwriting existing file (but this should never happen unless the file was pre-existing?)
			if os.access(filename, os.F_OK) and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Error: Binary data storage, attempt to overwrite existing file '%s'"
				#self.LOG(2, "Binary data storage: overwriting existing file '%s'" % (path + "/%05X" % newid))


			# if a filedata is supplied, write it out...
			# todo: use only this mechanism for putting files on disk
			self.LOG(4, "Writing %s bytes disk: %s"%(len(filedata),filename))
			f=open(filename,"wb")
			f.write(filedata)
			f.close()

			return True








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
			if isinstance(idents,(int,datatypes.datastorage.Record)):
				idents = [idents]


			bids.extend(filter(lambda x:isinstance(x,basestring), idents))

			recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), idents), filt=1, ctx=ctx, txn=txn))
			recs.extend(filter(lambda x:isinstance(x,datatypes.datastorage.Record), idents))

			# ian: todo: speed this up some..
			bids.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))

			bids = filter(lambda x:isinstance(x, basestring), bids)


			for ident in bids:
				prot, _, key = ident.rpartition(":")
				if prot == "": prot = "bdo"
				if prot not in ["bdo"]:
					if filt:
						continue
					else:
						raise Exception, "Invalid binary storage protocol: %s"%prot

				# for bdo: protocol
				# validate key
				year = int(key[:4])
				mon = int(key[4:6])
				day = int(key[6:8])
				bid = int(key[8:], 16)
				key = "%04d%02d%02d" % (year, mon, day)

				for i in g.BINARYPATH:
						if key >= i[0] and key < i[1] :
								# actual storage path
								path = "%s/%04d/%02d/%02d" % (i[2], year, mon, day)
								break
				else:
						raise KeyError, "No storage specified for date %s" % key


				try:
						name = self.__bdocounter.sget(key, txn=txn)[bid] #[key][bid]
				except:
						if filt:
							continue
						else:
							raise KeyError, "Unknown identifier %s" % ident


				try:
					self.getrecord(name["recid"], ctx=ctx, txn=txn, filt=0)
					name["filepath"] = path+"/%05X"%bid
					ret[ident] = name
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
			ret = [(i, len(self.__bdocounter.get(txn=txn))) for i in ret]
			return ret





		###############################
		# section: query
		###############################


		@DBProxy.publicmethod
		def query(self, q=None, rectype=None, boolmode="AND", ignorecase=True, constraints=None, childof=None, parentof=None, recurse=False, subset=None, recs=None, filt=True, returnrecs=True, ctx=None, txn=None):
			#includeparams=None,


			if boolmode not in ["AND","OR"]:
				raise Exception, "Invalid boolean mode: %s. Must be AND, OR"%boolmode

			constraints = constraints or []
			recs = recs or []
			subsets = []
			if subset:
				subsets.append(set(subset))

			#includeparams = set(includeparams or [])

			if q:
				constraints.append(["*","contains",unicode(q)])

			if recurse:
				recurse = self.MAXRECURSE



			# makes life simpler...
			if not constraints:

				if childof:
					subsets.append(self.getchildren(childof, recurse=recurse, ctx=ctx, txn=txn))
				if parentof:
					subsets.append(self.getparents(parentof, recurse=recurse, ctx=ctx, txn=txn))
				if rectype:
					subsets.append(self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn))

				if boolmode=="AND":
					ret = reduce(set.intersection, subsets)
				else:
				 	ret = reduce(set.union, subsets)

				if recs:
					ret = set([x.recid for x in recs]) & ret

				ret = self.getrecord(subsets, filt=filt, ctx=ctx, txn=txn)

				if returnrecs:
					return ret
				return set([x.recid for x in ret])





			# x is argument, y is record value
			cmps = {
				"==": lambda y,x:x == y,
				"!=": lambda y,x:x != y,
				"contains": lambda y,x:unicode(y) in unicode(x),
				"!contains": lambda y,x:unicode(y) not in unicode(x),
				">": lambda y,x: x > y,
				"<": lambda y,x: x < y,
				">=": lambda y,x: x >= y,
				"<=": lambda y,x: x <= y #,
				#"range": lambda x,y,z: y < x < z
			}

			if ignorecase:
				cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
				cmps["!contains"] = lambda y,x:unicode(y).lower() not in unicode(x).lower()

			# wildcard param searching only useful with the following comparators...
			globalsearchcmps = ["==","!=","contains","!contains"]



			# db.getrecord(reduce(set.union, [ind.get(x) for x in filter(lambda x:"Nan" in x, ddb._Database__indexkeys.get("name_project"))]), filt=True)
			# ok, new approach: name each constraint, search and store result, then join at the end if bool=AND

			#g.debug("******** query constraints")
			#g.debug(constraints)



			if recs:
				s = self.__query_recs(constraints, cmps=cmps, recs=recs, ctx=ctx, txn=txn)
			else:
				s = self.__query_index(constraints, cmps=cmps, recs=recs, ctx=ctx, txn=txn)


			subsets.extend(s)

			# if boolmode is "AND", filter for records that do not satisfy all named constraints
			if childof:
				subsets.append(self.getchildren(childof, recurse=recurse, ctx=ctx, txn=txn))
			if parentof:
				subsets.append(self.getparents(parentof, recurse=recurse, ctx=ctx, txn=txn))
			if rectype:
				subsets.append(self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn))


			if boolmode=="AND":
				recs = reduce(set.intersection, subsets)
			else:
				recs = reduce(set.union, subsets)


			if returnrecs:
				return self.getrecord(recs, filt=filt, ctx=ctx, txn=txn)
			return recs




		def __query_index(self, constraints, cmps=None, recs=None, ctx=None, txn=None):
			subsets = []
			
			# nested dictionary, results[constraint position][param]
			results = collections.defaultdict(partial(collections.defaultdict, set))

			# stage 1: search __indexkeys
			for count,c in enumerate(constraints):
				if c[0] == "*":
					for param, pkeys in self.__indexkeys.items(txn=txn):
						try:
							cargs = self.vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
						except (ValueError, KeyError):
							continue

						comp = partial(cmps[c[1]], cargs) #*cargs
						r = set(filter(comp, pkeys))
						if r:
							results[count][param] = r
							#g.debug("param %s reults %s"%(param, results[count][param]))

				else:
					param = c[0]
					pkeys = self.__indexkeys.get(param, txn=txn) or []
					cargs = self.vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
					comp = partial(cmps[c[1]], cargs) #*cargs
					results[count][param] = set(filter(comp, pkeys))


			# stage 2: search individual param indexes
			for count, r in results.items():
				constraint_matches = set()

				for param, matchkeys in r.items():
					ind = self.__getparamindex(param, ctx=ctx, txn=txn)
					for matchkey in matchkeys:
						constraint_matches |= ind.get(matchkey, txn=txn)

				subsets.append(constraint_matches)

			return subsets




		def __query_recs(self, constraints, cmps=None, recs=None, ctx=None, txn=None):
			subsets = []
			#allp = "*" in [c[0] for c in constraints]

			# this is ugly :(
			for count, c in enumerate(constraints):
				cresult = []

				if c[0] == "*":
					# cache
					allparams = set(reduce(operator.concat, [rec.getparamkeys() for rec in recs]))
					for param in allparams:
						try:
							cargs = self.vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
						except (ValueError, KeyError):
							continue

						cc = cmps[c[1]]
						cresult.extend([x.recid for x in filter(lambda rec:cc(cargs, rec.get(param)), recs)])




				else:
					param = c[0]
					cc = cmps[c[1]]
					cargs = self.vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=ctx.db)
					cresult.extend([x.recid for x in filter(lambda rec:cc(cargs, rec.get(param)), recs)])


				if cresult:
					subsets.append(cresult)

			#g.debug(subsets)
			return subsets





		#@DBProxy.publicmethod
		#def buildindexkeys(self, txn=None):
		def __rebuild_indexkeys(self, ctx=None, txn=None):

			inds = dict(filter(lambda x:x[1]!=None, [(i,self.__getparamindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

			self.LOG("truncating indexkeys")
			self.__indexkeys.truncate(txn=txn)

			self.LOG("rebuilding indexkeys")
			for k,v in inds.items():
					self.__indexkeys.set(k, set(v.keys()), txn=txn)



		@DBProxy.publicmethod
		def searchindexkeys(self, q=None, ignorecase=1, ctx=None, txn=None):
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
			return self.__recorddefindex.get(recdefname, txn=txn) or set()
			#[recdefname]
			#return self.__recorddefindex[unicode(recdefname).lower()]



		@DBProxy.publicmethod
		def getindexbyuser(self, username, ctx=None, txn=None):
			"""This will use the user keyed record read-access index to return
			a list of records the user can access. DOES NOT include that user's groups.
			Use getindexbycontext if you want to see all recs you can read."""

			if username == None:
				username = ctx.username

			if ctx.username != username and not ctx.checkreadadmin():
				raise subsystems.exceptions.SecurityError, "Not authorized to get record access for %s" % username

			return set(self.__secrindex.sget(username, txn=txn)) #[username]



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

			ret = set(self.__secrindex.sget(ctx.username, txn=txn)) #[ctx.username]
			for group in sorted(ctx.groups,reverse=True):
				ret |= set(self.__secrindex.sget(group, txn=txn))#[group]


			return ret




		# ian: todo: return dictionary instead of list?
		@DBProxy.publicmethod
		def getrecordschangetime(self, recids, ctx=None, txn=None):
			"""Returns a list of times for a list of recids. Times represent the last modification
			of the specified records"""
			#secure = set(self.getindexbycontext())
			#rid = set(recids)
			#rid -= secure
			recids = self.filterbypermissions(recids, ctx=ctx, txn=txn)

			if len(rid) > 0:
				raise Exception, "Cannot access records %s" % unicode(rid)

			try:
				ret = [self.__timeindex.sget(i, txn=txn) for i in recids]
			except:
				raise Exception, "unindexed time on one or more recids"

			return ret




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

			if (optimize and len(recids) < 1000) or (isinstance(list(recids)[0],datatypes.datastorage.Record)):
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

			if not isinstance(list(records)[0],datatypes.datastorage.Record):
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
		def countchildren(self, key, recurse=0, ctx=None, txn=None):
			"""Unlike getchildren, this works only for 'records'. Returns a count of children
			of the specified record classified by recorddef as a dictionary. The special 'all'
			key contains the sum of all different recorddefs"""

			c = self.getchildren(key, "record", recurse=recurse, ctx=ctx, txn=txn)
			r = self.groupbyrecorddef(c, ctx=ctx, txn=txn)
			for k in r.keys(): r[k] = len(r[k])
			r["all"] = len(c)
			return r



		@DBProxy.publicmethod
		def getchildren(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctx=None, txn=None):
			"""Get children;
			keytype: record, paramdef, recorddef
			recurse: recursion depth
			rectype: for records, return only children of type rectype
			filt: filt by permissions
			tree: return results in graph format; default is set format
			"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", filt=filt, tree=tree, ctx=ctx, txn=txn)



		@DBProxy.publicmethod
		def getparents(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctx=None, txn=None):
			"""see: getchildren"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", filt=filt, tree=tree, ctx=ctx, txn=txn)





		# wraps getrel / works as both getchildren/getparents
		@DBProxy.publicmethod
		def __getrel_wrapper(self, key, keytype="record", recurse=0, rectype=None, rel="children", filt=0, tree=0, ctx=None, txn=None):
			"""Add some extra features to __getrel"""

			ol=0
			if not hasattr(key,"__iter__"):
				ol=1
				key=[key]

			if tree and rectype:
				raise Exception,"tree and rectype are mutually exclusive"

			ret={}
			allr=set()

			for i in key:
				r = self.__getrel(key=i, keytype=keytype, recurse=recurse, rel=rel, ctx=ctx, txn=txn)
				ret[i] = r[tree]
				allr |= r[0]


			# ian: think about doing this a better way
			if filt and keytype=="record":

				allr = self.filterbypermissions(allr, ctx=ctx, txn=txn)

				if not tree:
					for k,v in ret.items():
						ret[k] = ret[k] & allr

				else:
					for k,v in ret.items():
						for k2,v2 in v.items():
							ret[k][k2] = set(v2) & set(allr)


			if rectype:
				r=self.groupbyrecorddef(self.__flatten(ret.values()), ctx=ctx, txn=txn).get(rectype,set())
				for k,v in ret.items():
					ret[k]=ret[k]&r
					if not ret[k]: del ret[k]

			if ol and tree==0:
				return ret.get(key[0],set())
			if ol and tree==1:
				return ret.get(key[0],{})

			return ret






		def __getrel(self, key, keytype="record", recurse=0, indc=None, rel="children", ctx=None, txn=None):
			# indc is restricted subset (e.g. getindexbycontext)
			"""get parent/child relationships; see: getchildren"""

			if (recurse < 0):
				return set(),{}

			if keytype == "record":
				trg = self.__records
				key = int(key)
				# read permission required
				try:
					self.getrecord(key, ctx=ctx, txn=txn)
				except:
					return set(),{}

			elif keytype == "recorddef":
				trg = self.__recorddefs
				try: a = self.getrecorddef(key, ctx=ctx, txn=txn)
				except: return set(),{}

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

			stack = [ret]
			result = {key: ret}
			for x in xrange(recurse):
				if len(stack[x])==0:
					break
				if x >= self.MAXRECURSE-1:
					raise Exception, "Recurse limit reached; check for circular relationships?"
				stack.append(set())

				for k in stack[x] - set(result.keys()):
					new = rel(k, txn=txn) or set()
					stack[x+1] |= new #.extend(new)
					result[k] = set(new)


			# flatten
			allr = []
			for i in stack:
				allr.extend(i)
			allr = set(allr)


			if indc:
				allr &= indc
				for k,v in result.items():
					result[k] = result[k] & allr


			return allr, result






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

			if mode not in ["pclink","pcunlink","link","unlink"]:
				raise Exception, "Invalid relationship mode %s"%mode

			if not ctx.checkcreate():
				raise subsystems.exceptions.SecurityError, "linking mode %s requires record creation priveleges"%mode

			if filter(lambda x:x[0] == x[1], links):
				#g.debug.msg("LOG_ERROR","Cannot link to self: keytype %s, key %s <-> %s"%(keytype, pkey, ckey))
				return

			if not links:
				return

			items = set(reduce(operator.concat, links))

			# ian: circular reference detection.
			#if mode=="pclink" and not self.__importmode:
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

			for pkey,ckey in links:
				linker(pkey, ckey, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: link: keytype %s, mode %s, pkey %s, ckey %s"%(keytype, mode, pkey, ckey))

			#@end




		###############################
		# section: user management
		###############################



		#@txn
		@DBProxy.publicmethod
		def disableuser(self, username, ctx=None, txn=None):
			"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
			a complete historical record is maintained. Only an administrator can do this."""
			return self.__setuserstate(username, 1, ctx=ctx, txn=txn)



		#@txn
		@DBProxy.publicmethod
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
			self.LOG(0, "Users %s disabled by %s"%([user.username for user in ret], ctx.username), ctx=ctx, txn=txn)

			if len(ret)==1 and ol: return ret[0].username
			return [user.username for user in ret]


		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def getsecret(self, username, ctx=None, txn=None):
			return self.__newuserqueue.get(username, txn=txn).get_secret()


		#@txn
		@DBProxy.publicmethod
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
					g.debug.msg('LOG_INFO', 'Ignored: (%s)' % e)


			#ol=False
			if not hasattr(usernames,"__iter__"):
				#ol=True
				usernames = [usernames]


			delusers, addusers, records, childstore = {}, {}, {}, {}

			for username in usernames:
				if not username in self.__newuserqueue.keys(txn=txn):
					raise KeyError, "User %s is not pending approval" % username

				#if username in self.__users:
				if self.__users.get(username, txn=txn):
					delusers[username] = None
					g.debug.msg("LOG_ERROR","User %s already exists, deleted pending record" % username)


				# ian: create record for user.
				user = self.__newuserqueue.sget(username, txn=txn) #[username]
				
				user.setContext(ctx)
				user.validate()

				if secret is not None and not user.validate_secret(secret):
					g.debug.msg("LOG_ERROR","Incorrect secret for user %s; skipping"%username)
					time.sleep(2)


				else:
					if user.record == None:
						#tmpctx = ctx
						#if ctx.username == None:
						#	tmpctx = self.__makecontext(username=username, host=ctx.host)
						#	#self.__init_context(tmpctx, user, txn=txn)

						tmpctx = self.__makerootcontext(txn=txn, dbproxy=True)

						rec = self.newrecord("person", ctx=tmpctx, txn=txn)
						rec["username"] = username
						name = user.signupinfo.get('name', ['', '', ''])
						rec["name_first"], rec["name_middle"], rec["name_last"] = name[0], ' '.join(name[1:-1]) or None, name[1]
						rec["email"] = user.signupinfo.get('email')
						rec.adduser(3,username)

						for k,v in user.signupinfo.items():
							rec[k] = v
						
						#print "putting record..."
						rec = self.__putrecord([rec], ctx=tmpctx, txn=txn)[0]

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

			self.__commit_users(addusers.values(), ctx=ctx, txn=txn)
			self.__commit_newusers(delusers, ctx=ctx, txn=txn)

			#@end

			ret = addusers.keys()
			# if ol and len(ret)==1:
			# 	return ret[0]
			return ret




		@DBProxy.publicmethod
		@DBProxy.adminmethod
		def getpendinguser(self, username, ctx=None, txn=None):
			return self.__newuserqueue.get(username, txn=txn)



		#@txn
		@DBProxy.publicmethod
		def rejectuser(self, usernames, ctx=None, txn=None):
			"""Remove a user from the pending new user queue - only an administrator can do this"""


			if not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators can approve new users"

			ol = 0
			if not hasattr(username,"__iter__"):
				ol = 1
				usernames = [usernames]

			delusers = {}

			for username in usernames:
				#if not username in self.__newuserqueue:
				if not self.__newuserqueue.get(username, txn=txn):
					raise KeyError, "User %s is not pending approval" % username

				delusers[username] = None


			self.__commit_newusers(delusers, ctx=ctx, txn=txn) # queue[username] = None

			if ol and len(delusers) == 1:
				return delusers.keys()[0]
			return delusers



		@DBProxy.publicmethod
		def getuserqueue(self, ctx=None, txn=None):
			"""Returns a list of names of unapproved users"""

			if not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators can approve new users"

			return self.__newuserqueue.keys(txn=txn)



		@DBProxy.publicmethod
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

			g.debug.msg("LOG_INFO","Changing password for %s"%user.username)

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
						g.debug.msg("LOG_COMMIT","Commit: __groupsbyuser key: %r, addrefs: %r"%(user, groups))
						self.__groupsbyuser.addrefs(user, groups, txn=txn)

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups))
					raise

				except ValueError, inst:
					g.debug.msg("LOG_ERROR", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups))


			for user,groups in delrefs.items():
				try:
					if groups:
						g.debug.msg("LOG_COMMIT","Commit: __groupsbyuser key: %r, removerefs: %r"%(user, groups))
						self.__groupsbyuser.removerefs(user, groups, txn=txn)

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups))
					raise

				except ValueError, inst:
					g.debug.msg("LOG_ERROR", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups))


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
					#	g.debug("unknown user %s (%s)"%(user, inst))


			#@begin

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
		def putgroup(self, groups, validate=True, ctx=None, txn=None):

			if isinstance(groups, (datatypes.user.Group, dict)): # or not hasattr(groups, "__iter__"):
				groups = [groups]

			groups2 = []
			groups2.extend(filter(lambda x:isinstance(x, datatypes.user.Group), groups))
			groups2.extend(map(lambda x:datatypes.user.Group(x), filter(lambda x:isinstance(x, dict), groups)))

			allusernames = self.getusernames(ctx=ctx, txn=txn)

			if not validate and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"

			for group in groups2:
			
				group.setContext(ctx)
				
				if validate:
					group.validate()

				if group.members() - allusernames:
					raise Exception, "Invalid user names: %s"%(group.members() - allusernames)


			self.__commit_groups(groups2, ctx=ctx, txn=txn)




		def __commit_groups(self, groups, ctx=None, txn=None):

			addrefs, delrefs = self.__reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

			#@begin

			for group in groups:
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

			groups = self.getgroup(groupname, ctx=ctx, txn=txn)

			ret = {}

			for i in groups.values():
				ret[i.name]="Test: %s"%i.name

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
				user = datatypes.user.User(inuser, secret=secret.hexdigest(), ctx=ctx)
			except Exception, inst:
				raise ValueError, "User instance or dict required (%s)"%inst


			#if user.username in self.__users:
			if self.__users.get(user.username, txn=txn):
				if self.__importmode:
					pass
				else:
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
		def putuser(self, user, validate=True, ctx=None, txn=None):

			if not isinstance(user, datatypes.user.User):
				try:
					user = datatypes.user.User(user, ctx=ctx)
				except:
					raise ValueError, "User instance or dict required"

			if not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only administrators may add/modify users with this method"

			if not validate and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"
			
			if validate:	
				user.validate()
				
			self.__commit_users([user], ctx=ctx, txn=txn)




		#@write #self.__users
		def __commit_users(self, users, ctx=None, txn=None):
			"""Updates user. Takes User object (w/ validation.) Deprecated for non-administrators."""

			commitusers = []

			for user in users:

				if not isinstance(user, datatypes.user.User):
					try:
						user = datatypes.user.User(user, ctx=ctx)
					except:
						raise ValueError, "User instance or dict required"

				try:
					ouser = self.__users.sget(user.username, txn=txn) #[user.username]
				except:
					ouser = user
					#raise KeyError, "Putuser may only be used to update existing users"

				# user.validate()

				commitusers.append(user)

			#@begin

			for user in commitusers:
				self.__users.set(user.username, user, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: self.__users.set: %r"%user.username)

			#@end

			return commitusers


		#@write #self.__newuserqueue
		def __commit_newusers(self, users, ctx=None, txn=None):
			"""write to newuserqueue; users is dict; set value to None to del"""

			#@begin

			for username, user in users.items():
				self.__newuserqueue.set(username, user, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: self.__newuserqueue.set: %r"%username)

			#@end



		@DBProxy.publicmethod
		def getuser(self, usernames, filt=True, lnf=False, getrecord=True, ctx=None, txn=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			ol=0
			if not hasattr(usernames,"__iter__"):
				ol=1
				usernames = [usernames]

			ret={}

			for i in usernames:

				user = self.__users.get(i, None, txn=txn)

				if user == None:
					if filt:
						continue
					else:
						raise KeyError, "No such user: %s"%i

				user.groups = self.__groupsbyuser.get(user.username, set(), txn=txn)

				# if the user has requested privacy, we return only basic info
				#if (user.privacy and ctx.username == None) or user.privacy >= 2:
				if user.privacy and not (ctx.checkreadadmin() or ctx.username == user.username):
					user2 = datatypes.user.User()
					user2.username = user.username
					user = user2

				# Anonymous users cannot use this to extract email addresses
				#if ctx.username == None:
				#	user.groups = None


				# ian: todo: it's easier if we get record directly here....
				#user._userrec = self.__records.sget(user.record, txn=txn)
				if getrecord:
					try:
						user._userrec = self.getrecord(user.record, filt=False, ctx=ctx, txn=txn)
					except Exception, inst:
						#self.LOG(4, "problem getting record user %s record %s: %s"%(user.username, user.record, inst))
						user._userrec = {}

					user.displayname = self.__formatusername(user.username, user._userrec, lnf=lnf, ctx=ctx, txn=txn)
					user.email = user._userrec.get("email")


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
			if isinstance(username, (basestring, int, datatypes.datastorage.Record)):
				username=[username]

			namestoget=[]
			namestoget.extend(filter(lambda x:isinstance(x,basestring),username))

			vts=["user","userlist"]
			if perms:
				vts.append("acl")

			recs = []
			recs.extend(filter(lambda x:isinstance(x,datatypes.datastorage.Record), username))
			recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), username), filt=filt, ctx=ctx, txn=txn))

			if recs:
				namestoget.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))
				# ... need to parse comments since it's special
				namestoget.extend(reduce(lambda x,y: x+y, [[i[0] for i in rec["comments"]] for rec in recs]))

			namestoget = set(namestoget)

			# users = self.getuser(namestoget, filt=filt, ctx=ctx, txn=txn).items()#txn=txn)
			# users = filter(lambda x:x[1].record != None, users)
			# users = dict(users)
			#
			# recs = self.getrecord([user.record for user in users.values()], filt=filt, ctx=ctx, txn=txn)
			# recs = dict([(i.recid,i) for i in recs])
			#
			# for k,v in users.items():
			# 	ret[k] = self.__formatusername(k, recs.get(v.record, {}), lnf=lnf, ctx=ctx, txn=txn)

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

			if self.__users.get(name, txn=txn) : return name

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



		#@txn
		# ian: renamed addparamdef -> putparamdef for consistency
		@DBProxy.publicmethod
		def putparamdef(self, paramdef, validate=True, parents=None, children=None, ctx=None, txn=None):
			"""adds a new ParamDef object, group 0 permission is required
			a p->c relationship will be added if parent is specified"""

			if not isinstance(paramdef, datatypes.datastorage.ParamDef):
				try:
					paramdef = datatypes.datastorage.ParamDef(paramdef, ctx=ctx)
				except ValueError, inst:
					raise ValueError, "ParamDef instance or dict required"


			if not ctx.checkcreate():
				raise subsystems.exceptions.SecurityError, "No permission to create new paramdefs (need record creation permission)"

			paramdef.name = unicode(paramdef.name).lower()

			try:
				pd = self.__paramdefs.sget(paramdef.name, txn=txn) #[paramdef.name]
				# Root is permitted to force changes in parameters, though they are supposed to be static
				# This permits correcting typos, etc., but should not be used routinely
				# skip relinking if we're editing
				if not ctx.checkadmin():
					raise KeyError, "Only administrators can modify paramdefs: %s"%paramdef.name

				if pd.vartype != paramdef.vartype:
					g.debug.msg("LOG_INFO","WARNING! Changing paramdef %s vartype from %s to %s. This will REQUIRE database export/import and revalidation!!"%(paramdef.name, pd.vartype, paramdef.vartype))


			except:
				paramdef.creator = ctx.username
				paramdef.creationtime = self.__gettime(ctx=ctx, txn=txn)


			if not validate and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"
			
			if validate:
				paramdef.validate()
				
			# this actually stores in the database

			self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)

			links = []
			if parents: links.append( map(lambda x:(x, paramdef.name), parents) )
			if children: links.append( map(lambda x:(paramdef.name, x), children) )
			if links:
				self.pclinks(links, keytype="paramdef", ctx=ctx, txn=txn)





		#@txn
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
				self.__paramdefs.set(paramdef.name, paramdef, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: self.__paramdefs.set: %r"%paramdef.name)

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

			if isinstance(recs[0], datatypes.datastorage.Record):
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
						g.debug.msg('LOG_WARNING', "WARNING: Invalid param: %s"%i)
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

			if f.vartype not in self.indexablevartypes:
				return None

			tp = self.vtm.getvartype(f.vartype).getindextype()

			if not create and not os.access("%s/index/%s.bdb" % (self.path, paramname), os.F_OK):
				raise KeyError, "No index for %s" % paramname

			# create/open index
			self.__fieldindex[paramname] = subsystems.btrees2.FieldBTree(paramname, keytype=tp, indexkeys=self.__indexkeys, filename="%s/index/%s.bdb"%(self.path, paramname), dbenv=self.__dbenv, txn=txn)

			return self.__fieldindex[paramname]

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
		def putrecorddef(self, recdef, validate=True, parents=None, children=None, ctx=None, txn=None):
			"""Add or update RecordDef. The mainview should
			never be changed once used, since this will change the meaning of
			data already in the database, but sometimes changes of appearance
			are necessary, so this method is available."""
			#self = db

			if not isinstance(recdef, datatypes.datastorage.RecordDef):
				try:
					recdef = datatypes.datastorage.RecordDef(recdef)
				except:
					raise ValueError, "RecordDef instance or dict required"

			if not ctx.checkcreate():
				raise subsystems.exceptions.SecurityError, "No permission to create new RecordDefs"

			if not validate and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only admin users may bypass validation"
			


			try:
				rd = self.__recorddefs.sget(recdef.name, txn=txn) #[recdef.name]
				rd.setContext(ctx)
				
			except:
				rd = datatypes.datastorage.RecordDef(recdef, ctx=ctx)
				#raise Exception, "No such recorddef %s"%recdef.name

			if ctx.username != rd.owner and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only the owner or administrator can modify RecordDefs"

			if recdef.mainview != rd.mainview and not ctx.checkadmin():
				raise subsystems.exceptions.SecurityError, "Only the administrator can modify the mainview of a RecordDef"


			recdef.findparams()
			invalidparams = set(recdef.params) - set(self.getparamdefnames(ctx=ctx, txn=txn))
			if invalidparams:
				raise KeyError, "Invalid parameters: %s"%invalidparams

			# reset
			recdef.creator = rd.creator
			recdef.creationtime = rd.creationtime

			if validate:	
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
				self.__recorddefs.set(recorddef.name, recorddef, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: self.__recorddefs.set: %r"%recorddef.name)

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
		@DBProxy.publicmethod
		#@g.debug.debug_func
		def getrecord(self, recids, filt=True, ctx=None, txn=None):
			"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
			if dbid is 0, the current database is used."""
			ol=False
			if not hasattr(recids,"__iter__"):
				ol=True
				recids=[recids]

			#traceback.print_stack()

			ret=[]
			for i in recids:				
				try:
					rec = self.__records.sget(i, txn=txn) # [i]
					rec.setContext(ctx=ctx)
					ret.append(rec)
				except subsystems.exceptions.SecurityError, e:
					if filt: pass
					else:
						traceback.print_stack()
						raise e
				except (KeyError, TypeError), e:
					if filt:
						pass
					else:
						raise KeyError, "No such record %s"%i

			if len(ret)==1 and ol:
				return ret[0]
			return ret


		# does not setContext!!
		def __getrecord(self, recids, filt=True, ctx=None, txn=None):
			pass




		# ian: todo: improve newrecord/putrecord
		# ian: todo: allow to copy existing record
		@DBProxy.publicmethod
		def newrecord(self, rectype, init=0, inheritperms=None, ctx=None, txn=None):
			"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
			already exist)."""


			rec = datatypes.datastorage.Record(ctx=ctx)
			#rec.setContext(ctx)

			# try to get the RecordDef entry, this still may fail even if it exists, if the
			# RecordDef is private and the context doesn't permit access
			t = self.getrecorddef(rectype, ctx=ctx, txn=txn)

			rec.recid = None
			rec.rectype = rectype # if we found it, go ahead and set up

			if init:
				rec.update(t.params)

			# ian
			if inheritperms != None:
				try:
					prec = self.getrecord(inheritperms, filt=0, ctx=ctx, txn=txn)
					for level, users in enumerate(prec["permissions"]):
						rec.adduser(level, users)

				except Exception, inst:
					g.debug.msg("LOG_ERROR","newrecord: Error setting inherited permissions from record %s (%s)"%(inheritperms, inst))


			if ctx.username != "root":
				rec.adduser(3, ctx._user)

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
			if isinstance(recs,(int,datatypes.datastorage.Record)):
				ol = 1
				recs = [recs]


			# get the records...
			recs2.extend(filter(lambda x:isinstance(x,datatypes.datastorage.Record),recs))
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
			# 						re = set(self.__flatten(re))-set([None])
			# 					ret[rec.recid]=re
			#
			# 				if ol: return ret.values()[0]
			# 				return ret

			# if not returndict

			re = [[rec.get(pd) for pd in params if rec.get(pd)] for rec in recs2]

			if flat:
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
		def putrecord(self, recs, filt=True, validate=True, warning=0, log=True, importmode=True, ctx=None, txn=None):
			"""commits a record"""
			# input validation for __putrecord

			if not ctx.checkadmin():
				if not validate or warning:
					raise subsystems.exceptions.SecurityError, "Only administrators may bypass record validation"					
				if not log:
					raise subsystems.exceptions.SecurityError, "Only administrators may bypass logging"
				if not importmode:
					raise subsystems.exceptions.SecurityError, "Only administrators may use importmode"


			# filter input for dicts/records
			ol = 0
			if isinstance(recs,(datatypes.datastorage.Record,dict)):
				ol = 1
				recs = [recs]
			elif not hasattr(recs, 'extend'):
				recs = list(recs)


			dictrecs = filter(lambda x:isinstance(x,dict), recs)
			recs.extend(map(lambda x:datatypes.datastorage.Record(x, ctx=ctx), dictrecs))
			recs = filter(lambda x:isinstance(x,datatypes.datastorage.Record), recs)

			# new records and updated records
			updrecs = filter(lambda x:x.recid >= 0, recs)
			newrecs = filter(lambda x:x.recid < 0, recs)


			# check original records for write permission
			orecs = self.getrecord([rec.recid for rec in updrecs], filt=0, ctx=ctx, txn=txn)
			orecs = set(map(lambda x:x.recid, filter(lambda x:x.commentable(), orecs)))


			permerror = set([rec.recid for rec in updrecs]) - orecs
			if permerror:
				raise subsystems.exceptions.SecurityError, "No permission to write to records: %s"%permerror


			if newrecs and not ctx.checkcreate():
				raise subsystems.exceptions.SecurityError, "No permission to create records"

			ret = self.__putrecord(recs, validate=validate, warning=warning, importmode=importmode, log=log, ctx=ctx, txn=txn)


			if ol and len(ret) > 0:
				return ret[0]
			return ret






		def __putrecord(self, updrecs, validate=True, warning=0, importmode=0, log=True, ctx=None, txn=None):
			# process before committing
			# extended validation...

			if len(updrecs) == 0:
				return []

			if self.__importmode:
				importmode = 1

			crecs = []
			updrels = []

			param_immutable = set(["recid","rectype","creator","creationtime","modifytime","modifyuser"])
			param_special = param_immutable | set(["comments","permissions"])


			# assign temp recids to new records
			for offset,updrec in enumerate(filter(lambda x:x.recid < 0, updrecs)):
				updrec.recid = -1 * (offset + 100)


			updrels = self.__putrecord_getupdrels(updrecs, ctx=ctx, txn=txn)

			# preprocess: copy updated record into original record (updrec -> orec)
			for updrec in updrecs:

				t = self.__gettime(ctx=ctx, txn=txn)
				recid = updrec.recid


				if self.__records.exists(updrec.recid, txn=txn, flags=RMWFLAGS):
					# we need to acquire RMW lock here to prevent changes during commit
					orec = self.__records.sget(updrec.recid, txn=txn)
					orec.setContext(ctx)


				else:
					orec = self.newrecord(updrec.rectype, ctx=ctx, txn=txn)
					orec.recid = updrec.recid

					if importmode:
						orec._Record__creator = updrec["creator"]
						orec._Record__creationtime = updrec["creationtime"]

					#if recid > 0:
					#	raise Exception, "Cannot update non-existent record %s"%recid



				if validate:
					updrec.validate(warning=warning)

				# compare to original record
				cp = orec.changedparams(updrec) - param_immutable


				# orec.recid < 0 because new records will always be committed, even if skeletal
				if not cp and not orec.recid < 0:
					g.debug.msg("LOG_INFO","putrecord: No changes for record %s, skipping"%recid)
					continue



				# add new comments; already checked for comment level security...
				for i in updrec["comments"]:
					if i not in orec._Record__comments:
						#orec.addcomment(i[2])
						orec._Record__comments.append(i)
						# ian todo: need to check for param updates from comments here...


				for param in cp - param_special:
					if log and orec.recid >= 0:
						orec.addcomment(u"LOG: %s updated. was: %s" % (param, orec[param]))
						#orec._Record__comments.append((ctx.user, t, u"LOG: %s updated. was: %s" % (recid, orec[param])))
						#% (param, orec[param]), param, orec[param]))
					orec[param] = updrec[param]


				if "permissions" in cp:
					orec["permissions"] = updrec["permissions"]


				if log:
					orec["modifytime"] = t
					orec["modifyuser"] = ctx.username

				if importmode:
					orec["modifytime"] = updrec["modifytime"]
					orec["modifyuser"] = updrec["modifyuser"]


				#if validate:
				#	orec.validate(warning=warning, params=cp)


				crecs.append(orec)

			# return records to commit, copies of the originals for indexing, and any relationships to update
			#return crecs, updrels

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
		def __commit_records(self, crecs, updrels=[], ctx=None, txn=None):

			recmap = {}
			rectypes = collections.defaultdict(list) # {}
			timeupdate = {}
			newrecs = filter(lambda x:x.recid < 0, crecs)


			# acquire write locks on records at this point
			# first, get index updates
			indexupdates = self.__reindex_params(crecs, ctx=ctx, txn=txn)
			secr_addrefs, secr_removerefs = self.__reindex_security(crecs, ctx=ctx, txn=txn)
			timeupdate = self.__reindex_time(crecs, ctx=ctx, txn=txn)


			#@begin

			# ntxn = self.newtxn(txn=txn)

			# this needs a lock.
			if newrecs:
				baserecid = self.__records.sget(-1, txn=txn, flags=RMWFLAGS)
				g.debug.msg("LOG_INFO","Setting recid counter: %s -> %s"%(baserecid, baserecid + len(newrecs)))
				self.__records.set(-1, baserecid + len(newrecs), txn=txn)



			# add recids to new records, create map from temp recid, setup index
			for offset, newrec in enumerate(newrecs):
				oldid = newrec.recid
				newrec.recid = offset + baserecid
				recmap[oldid] = newrec.recid
				rectypes[newrec.rectype].append(newrec.recid)


			#if filter(lambda x:x.recid < 0, crecs):
			#	raise ValueError, "Some new records were not given real recids; giving up"


			# This actually stores the record in the database
			for crec in crecs:
				self.__records.set(crec.recid, crec, txn=txn)
				g.debug.msg("LOG_COMMIT","Commit: self.__records.set: %r"%crec.recid)



			# # New record RecordDef indexes

			#txn2 = self.newtxn(parent=txn)

			for rectype,recs in rectypes.items():
				try:
					self.__recorddefindex.addrefs(rectype, recs, txn=txn)
					g.debug.msg("LOG_COMMIT","Commit: self.__recorddefindex.addrefs: %r, %r"%(rectype,recs))

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst))
					raise

				except ValueError, inst:
					g.debug.msg("LOG_ERROR", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst))


			# Param index
			for param, updates in indexupdates.items():
				self.__commit_paramindex(param, updates[0], updates[1], recmap=recmap, ctx=ctx, txn=txn)


			# Security index
			self.__commit_secrindex(secr_addrefs, secr_removerefs, recmap=recmap, ctx=ctx, txn=txn)


			# Time index
			for recid,time in timeupdate.items():
				try:
					recid = recmap.get(recid,recid)
					if not isinstance(recid, basestring):
						recid = unicode(recid).encode('utf-8')
					self.__timeindex.set(recid, time, txn=txn)
					#g.debug.msg("LOG_COMMIT","Commit: self.__timeindex.set: %r, %r"%(recmap.get(recid,recid), time))

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst))
					raise

				except ValueError, inst:
					g.debug.msg("LOG_ERROR", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst))


			# Create pc links
			for link in updrels:
				try:
					self.pclink( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), ctx=ctx, txn=txn)

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst))
					raise

				except Exception, inst:
					g.debug.msg("LOG_ERROR", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst))



			#@end

			return crecs


		#@write #self.__secrindex
		def __commit_secrindex(self, addrefs, removerefs, recmap={}, ctx=None, txn=None):

			# Security index
			for user, recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.__secrindex.addrefs(user, recs, txn=txn)
						g.debug.msg("LOG_COMMIT","Commit: self.__secrindex.addrefs: %r, len %r"%(user, len(recs)))

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))
					raise

				except Exception, inst:
					g.debug.msg("LOG_ERROR", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))



			for user, recs in removerefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.__secrindex.removerefs(user, recs, txn=txn)
						g.debug.msg("LOG_COMMIT","Commit: secrindex.removerefs: user %r, len %r"%(user, len(recs)))

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
					raise

				except Exception, inst:
					g.debug.msg("LOG_ERROR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
					raise



		#@write #self.__fieldindex*
		def __commit_paramindex(self, param, addrefs, delrefs, recmap={}, ctx=None, txn=None):
			"""commit param updates"""

			# addrefs = upds[0], delrefs = upds[1]
			if not addrefs and not delrefs:
				return
				#continue

			try:
				paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
				if paramindex == None:
					raise Exception, "Index was None; unindexable?"

			except bsddb3.db.DBError, inst:
				g.debug.msg("LOG_CRITICAL","Could not open param index: %s (%s)"% (param, inst))
				raise

			except Exception, inst:
				g.debug.msg("LOG_ERROR","Could not open param index: %s (%s)"% (param, inst))
				raise




			for newval,recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.debug.msg("LOG_COMMIT","Commit: param index %r.addrefs: %r '%r', %r"%(param, type(newval), newval, len(recs)))
						paramindex.addrefs(newval, recs, txn=txn)

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))
					raise

				except Exception, inst:
					g.debug.msg("LOG_ERROR", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))



			for oldval,recs in delrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						g.debug.msg("LOG_COMMIT","Commit: param index %r.removerefs: %r '%r', %r"%(param, type(oldval), oldval, len(recs)))
						paramindex.removerefs(oldval, recs, txn=txn)

				except bsddb3.db.DBError, inst:
					g.debug.msg("LOG_CRITICAL", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))
					raise

				except Exception, inst:
					g.debug.msg("LOG_ERROR", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))




		# index update methods
		def __reindex_params(self, updrecs, ctx=None, txn=None):
			"""update param indices"""

			#ind = dict([(i,[]) for i in self.__paramdefs.keys(txn=txn)])
			ind = collections.defaultdict(list)
			indexupdates = {}
			unindexed = set(["recid","rectype","comments","permissions"])

			for updrec in updrecs:
				recid = updrec.recid

				# this is a fix for proper indexing of new records...
				# if existing record, RMW lock already placed at beginning of txn
				try: orec = self.__records.sget(recid, txn=txn) # [recid]
				except:	orec = {}

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
			if pd.name in ["recid","comments","permissions"]:
				return addrefs, delrefs

			if pd.vartype not in self.indexablevartypes:
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




		def __reindex_time(self, updrecs, ctx=None, txn=None):
			timeupdate = {}

			for updrec in updrecs:
				timeupdate[updrec.recid] = updrec.get("modifytime") or updrec.get("creationtime")

			return timeupdate



		def __reindex_security(self, updrecs, ctx=None, txn=None):

			secrupdate = []
			addrefs = collections.defaultdict(list)
			delrefs = collections.defaultdict(list)

			for updrec in updrecs:
				recid = updrec.recid

				# this is a fix for proper indexing of new records...
				# write lock acquire at beginning of txn
				try: orec = self.__records.sget(recid, txn=txn) # [recid]
				except:	orec = {}

				if updrec.get("permissions") == orec.get("permissions"):
					continue

				nperms = set(reduce(operator.concat, updrec["permissions"]))
				operms = set(reduce(operator.concat, orec.get("permissions",[[]])))

				#g.debug.msg("LOG_INFO","__reindex_security: record %s, add %s, delete %s"%(updrec.recid, nperms - operms, operms - nperms))

				for user in nperms - operms:
					addrefs[user].append(recid)
				for user in operms - nperms:
					delrefs[user].append(recid)

			return addrefs, delrefs






		###############################
		# section: permissions
		###############################




		# ian: todo: benchmark these again
		@DBProxy.publicmethod
		def filterbypermissions(self, recids, ctx=None, txn=None):


			if ctx.checkreadadmin():
				return set(recids)

			recids = set(recids)

			# this is usually the fastest
			# method 2
			#ret=set()

			ret = []

			if ctx.username != None and ctx.username != "anonymous":
				ret.extend(recids & set(self.__secrindex.get(ctx.username, [], txn=txn)))

			#ret |= recids & set(self.__secrindex[ctx.user])
			#recids -= ret

			for group in sorted(ctx.groups, reverse=True):
				#if recids:
				#ret |= recids & set(self.__secrindex[group])
				#recids -= ret
				ret.extend(recids & set(self.__secrindex.get(group, [], txn=txn)))

			return set(ret)

			# # method 3
			# ret=[]
			# for i in recids:
			# 	try:
			# 		self.getrecord(i, ctx=ctx, txn=txn)
			# 		ret.append(i)
			# 	except:
			# 		pass
			# return ret
			#
			#
			# # method 4 (same as getindexbycontext)
			# ret=set(self.__secrindex[ctx.user])
			# for group in sorted(ctx.groups,reverse=True):
			# 	ret |= set(self.__secrindex[group])
			# return ret & recids
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
		def secrecordadduser2(self, recids, level, users, reassign=0, ctx=None, txn=None):

				if not hasattr(recids,"__iter__"):
					recids = [recids]
				recids = set(recids)

				if not hasattr(users,"__iter__"):
					users = [users]
				users = set(users)

				checkitems = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)
				if users - checkitems:
					raise subsystems.exceptions.SecurityError, "Invalid users/groups: %s"%(users-checkitems)

				# change child perms
				if recurse:
					recids |= self.getchildren(recids, recurse=recurse, filt=1, ctx=ctx, txn=txn)

				recs = self.getrecord(recids, filt=1, ctx=ctx, txn=txn)

				for rec in recs:
					rec.adduser(level, users, reassign=reassign)

				self.putrecord(recs, ctx=ctx, txn=txn)



		# ian todo: check this thoroughly; probably rewrite
		#@txn
		#@write #self.__records, self.__secrindex
		@DBProxy.publicmethod
		def secrecordadduser(self, usertuple, recid, recurse=0, reassign=0, mode="union", ctx=None, txn=None):
				"""This adds permissions to a record. usertuple is a 4-tuple containing users
				to have read, comment, write and administrativepermission. Each value in the tuple is either
				a string (username) or a tuple/list of usernames. If recurse>0, the
				operation will be performed recursively on the specified record's children
				to a limited recursion depth. Note that this ADDS permissions to existing
				permissions on the record. If addition of a lesser permission than the
				existing permission is requested, no change will be made. ie - giving a
				user read access to a record they already have write access to will
				have no effect. Any children the user doesn't have permission to
				update will be silently ignored."""

				if not isinstance(usertuple, tuple) and not isinstance(usertuple, list) :
						raise ValueError, "permissions must be a 4-tuple/list of tuples,strings,ints"

				usertuple = list(usertuple)[:4]

				for i in range(4):
					if not hasattr(usertuple[i], "__iter__"):
						usertuple[i] = [list(usertuple[i])]

					for j, k in enumerate(usertuple[i]):
						if not isinstance(usertuple[i][j], int):
							# sometimes group ints will be sent as str.
							try: usertuple[i][j] = int(usertuple[i][j])
							except ValueError: usertuple[i][j] = unicode(usertuple[i][j])
							except: raise ValueError, "Invalid permissions format; must be 4-tuple/list of tuple/list/string/int"


				# all users
				userset = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)


				# get a list of records we need to update
				if recurse > 0:
						trgt = self.getchildren(recid, recurse=recurse-1, ctx=ctx, txn=txn)
						trgt.add(recid)
				else:
					trgt = set((recid,))


				if ctx.checkadmin(): isroot = True
				else: isroot = False


				rec=self.getrecord(recid, ctx=ctx, txn=txn)
				if ctx.username not in rec["permissions"][3] and not isroot:
					raise subsystems.exceptions.SecurityError,"Insufficient permissions for record %s"%recid

				# this will be a dictionary keyed by user of all records the user has
				# just gained access to. Used for fast index updating
				secrupd = {}

				for i in trgt:
						rec = self.getrecord(i, ctx=ctx, txn=txn)						 # get the record to modify

						# if the context does not have administrative permission on the record
						# then we just skip this record and leave the permissions alone
						# TODO: probably we should also check for groups in [3]

						if ctx.username not in rec["permissions"][3] and not ctx.checkadmin(): continue


						cur = [set(v) for v in rec["permissions"]]				# make a list of sets out of the current permissions
						xcur = [set(v) for v in rec["permissions"]]				 # copy of cur that will be changed
						#length test not sufficient # length of each tuple so we can decide if we need to commit changes
						newv = [set(v) for v in usertuple]								# similar list of sets for the new users to add

						# check for valid user names
						newv[0] &= userset
						newv[1] &= userset
						newv[2] &= userset
						newv[3] &= userset

						# if we allow level change, remove all changed users then add back..
						if reassign:
							allnew = newv[0] | newv[1] | newv[2] | newv[3]
							xcur[0] -= allnew
							xcur[1] -= allnew
							xcur[2] -= allnew
							xcur[3] -= allnew

						# update the permissions for each group
						xcur[0] |= newv[0]
						xcur[1] |= newv[1]
						xcur[2] |= newv[2]
						xcur[3] |= newv[3]
						# if the user already has more permission than we are trying
						# to assign, we don't do anything. This also cleans things up
						# so a user cannot have more than one security level
						# -- assign higher permissions or lower permissions
						xcur[0] -= xcur[1] | xcur[2] | xcur[3]
						xcur[1] -= xcur[2] | xcur[3]
						xcur[2] -= xcur[3]

						if xcur[0] != cur[0] or xcur[1] != cur[1] \
							or xcur[2] != cur[2] or xcur[3] != cur[3]:
								old = rec["permissions"]
								rec["permissions"] = (tuple(xcur[0]), tuple(xcur[1]), tuple(xcur[2]), tuple(xcur[3]))

								stu = (xcur[0] | xcur[1] | xcur[2] | xcur[3]) - set(old[0] + old[1] + old[2] + old[3])
								for i in stu:
										try: secrupd[i].append(rec.recid)
										except: secrupd[i] = [rec.recid]

								# put the updated record back
								self.__records.set(rec.recid, rec, txn=txn)

				for i in secrupd.keys() :
						self.__secrindex.addrefs(i, secrupd[i], txn=txn)

				return rec["permissions"]


		# ian todo: see above
		#@txn
		#@write	#self.__records, self.__secrindex
		@DBProxy.publicmethod
		def secrecorddeluser(self, users, recid, recurse=0, ctx=None, txn=None):
				"""This removes permissions from a record. users is a username or tuple/list of
				of usernames to have no access to the record at all (will not affect group
				access). If recurse>0, the operation will be performed recursively
				on the specified record's children to a limited recursion depth. Note that
				this REMOVES all access permissions for the specified users on the specified
				record."""
				#self = db


				if isinstance(users, basestring) or isinstance(users, int):
						users = set([users])
				else:
						users = set(users)

				# get a list of records we need to update
				if recurse > 0:
						#if DEBUG: g.debug("Del user recursive...")
						trgt = self.getchildren(recid, recurse=recurse-1, ctx=ctx, txn=txn)
						trgt.add(recid)
				else : trgt = set((recid,))


				users.discard(ctx.username)								 # user cannot remove his own permissions
				#if ctx.user=="root" or -1 in ctx.groups : isroot=1
				if ctx.checkadmin(): isroot = 1
				else: isroot = 0

				# this will be a dictionary keyed by user of all records the user has
				# just gained access to. Used for fast index updating
				secrupd = {}

				# update each record as necessary
				for i in trgt:
						try:
								rec = self.getrecord(i, ctx=ctx, txn=txn)						 # get the record to modify
						except: continue

						# if the user does not have administrative permission on the record
						# then we just skip this record and leave the permissions alone
						# TODO: probably we should also check for groups in [3]
						if (not isroot) and (ctx.username not in rec["permissions"][3]) : continue

						cur = [set(v) for v in rec["permissions"]]				# make a list of Sets out of the current permissions
						l = [len(v) for v in cur]														 # length of each tuple so we can decide if we need to commit changes

						cur[0] -= users
						cur[1] -= users
						cur[2] -= users
						cur[3] -= users

						l2 = [len(v) for v in cur]

						# update if necessary
						if l != l2 :
								old = rec["permissions"]
								rec["permissions"] = (tuple(cur[0]), tuple(cur[1]), tuple(cur[2]), tuple(cur[3]))

								for i in users:
										try: secrupd[i].append(rec.recid)
										except: secrupd[i] = [rec.recid]


								# put the updated record back
								self.__records.set(rec.recid, rec, txn=txn)

				for i in secrupd.keys() :
						self.__secrindex.removerefs(i, secrupd[i], txn=txn)






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









		# It is a cold, cold, cruel world... moved to VartypeManager
		@DBProxy.publicmethod
		def renderview(self, *args, **kwargs):
			"""Render views"""
			# calls out to places that expect DBProxy need a DBProxy...
			kwargs["db"] = kwargs["ctx"].db
			if kwargs.get("ctx"): del kwargs["ctx"]
			if kwargs.get("txn"): del kwargs["txn"]
			print "Calling out to renderview..."
			traceback.print_stack()
			print args
			print kwargs
			return self.vtm.renderview(*args, **kwargs)



		###########################
		# section: backup / restore
		###########################



		def _backup(self, encode_func=pickle.dump, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""

				#if user!="root" :
				if not ctx.checkadmin():
					raise subsystems.exceptions.SecurityError, "Only root may backup the database"


				g.debug.msg('LOG_INFO', 'backup has begun')
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

				g.debug.msg('LOG_INFO', 'backup file opened')
				# dump users
				for i in users: encode_func(self.__users.sget(i, txn=txn), out)
				g.debug.msg('LOG_INFO', 'users dumped')

				# dump workflow
				for i in workflows: encode_func(self.__workflow.sget(i, txn=txn), out)
				g.debug.msg('LOG_INFO', 'workflows dumped')

				# dump binary data objects
				encode_func("bdos", out)
				bd = {}
				for i in bdos: bd[i] = self.__bdocounter.sget(i, txn=txn)
				encode_func(bd, out)
				bd = None
				g.debug.msg('LOG_INFO', 'bdos dumped')

				# dump paramdefs and tree
				def encode_relations(recordtree, records, dump_method, outfile, txn=txn):
					ch = []
					for i in records:
							c = tuple(set(dump_method(i, txn=txn)) & records)
							ch += ((i, c),)
					encode_func("pdchildren", out)
					encode_func(ch, out)

				for i in paramdefs: encode_func(self.__paramdefs.sget(i, txn=txn), out)
				g.debug.msg('LOG_INFO', 'paramdefs dumped')
				encode_relations(self.__paramdefs, paramdefs, self.__paramdefs.children, out)
				g.debug.msg('LOG_INFO', 'paramchildren dumped')
				encode_relations(self.__paramdefs, paramdefs, self.__paramdefs.cousins, out)
				g.debug.msg('LOG_INFO', 'paramcousins dumped')

				# dump recorddefs and tree
				for i in recorddefs: encode_func(self.__recorddefs.sget(i, txn=txn), out)
				g.debug.msg('LOG_INFO', 'recorddefs dumped')
				encode_relations(self.__recorddefs, recorddefs, self.__recorddefs.children, out)
				g.debug.msg('LOG_INFO', 'recdefchildren dumped')
				encode_relations(self.__recorddefs, recorddefs, self.__recorddefs.cousins, out)
				g.debug.msg('LOG_INFO', 'recdefcousins dumped')

				# dump actual database records
				g.debug.msg('LOG_INFO', "Backing up %d/%d records" % (len(records), self.__records.sget(-1, txn=txn)))
				for i in records: encode_func(self.__records.sget(i, txn=txn), out)
				g.debug.msg('LOG_INFO', 'records dumped')

				ch = []
				for i in records:
						c = [x for x in self.__records.children(i, txn=txn) if x in records]
						c = tuple(c)
						ch += ((i, c),)
				encode_func("recchildren", out)
				encode_func(ch, out)
				g.debug.msg('LOG_INFO', 'rec children dumped')

				ch = []
				for i in records:
						c = set(self.__records.cousins(i, txn=txn))
						c &= records
						c = tuple(c)
						ch += ((i, c),)
				encode_func("reccousins", out)
				encode_func(ch, out)
				g.debug.msg('LOG_INFO', 'rec cousins dumped')

				out.close()



		def _backup2(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""
				def enc(value, fil):
					if type(value) == dict:
						for x in value.items():
							#g.debug(x)
							demjson.encode(x)
					value = {'type': type(value).__name__, 'data': demjson.encode(value, encoding='utf-8')}
					fil.write('\n')
				self._backup(enc,users, paramdefs, recorddefs, records, workflows, bdos, outfile, ctx=ctx, txn=txn)

		def get_dbpath(self, tail):
			return os.path.join(self.path, tail)

		@DBProxy.adminmethod
		def archivelogs(self, ctx=None, txn=None):
			g.debug.msg('LOG_INFO', "checkpointing")
			self.__dbenv.txn_checkpoint()
			archivefiles = self.__dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)
			archivepath = self.get_dbpath('archives')
			if not os.access(archivepath, os.F_OK):
				os.makedirs(archivepath)
			for file_ in archivefiles:
				os.rename(file_, os.path.join(archivepath, os.path.basename(file_)))



		def __restore_rec(self, recblock,  recmap, ctx=None, txn=None):
			def swapin(obj, key, value):
				result = getattr(obj, key)
				setattr(obj, key, value)
				return result

			oldids = map(lambda rec: swapin(rec, 'recid', None), recblock)

			newrecs = self.__putrecord(recblock, warning=1, validate=0, ctx=ctx, txn=txn)

			for oldid,newrec in itertools.izip(oldids,newrecs):
				recmap[oldid] = newrec.recid
				if oldid != newrec.recid:
					self.LOG("Warning: recid %s changed to %s"%(oldid,newrec.recid))
			return len(newrecs)

		def __restore_commitblocks(self, *blocks, **kwargs):
			ctx, txn = kwargs.get('ctx'), kwargs.get('txn')
			mp = kwargs.get('map')
			changesmade = False
			if any(blocks):
				to_commit = filter(None, blocks)
				commit_funcs = {
					datatypes.datastorage.ParamDef: lambda r: self.putparamdef(r, ctx=ctx, txn=txn),
					datatypes.datastorage.RecordDef: lambda r: self.putrecorddef(r, ctx=ctx, txn=txn),
					datatypes.user.User: lambda r: self.putuser(r, validate=0, ctx=ctx, txn=txn),
				}
				for block in to_commit:
					if isinstance(block[0], datatypes.datastorage.Record):
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
						link_func(a,b, txn=txn)

			simple_choices = dict(
				pdchildren=self.__paramdefs.pclink,
				pdcousins=self.__paramdefs.link,
				rdchildren=self.__recorddefs.pclink,
				rdcousins=self.__recorddefs.link,
				reccousins=self.__records.link
			)

			if r == "bdos":
				g.debug.msg('LOG_INFO', "bdo")
				# read the dictionary of bdos
				for i, d in rr.items():
					self.__bdocounter.set(i, d, txn=txn)

			elif r == "recchildren":
				g.debug.msg('LOG_INFO', "recchildren")
				# read the dictionary of ParamDef PC links
				for p, cl in rr:
					for c in cl:
						if isinstance(c, tuple):
							g.debug.msg('LOG_WARNING', "Invalid (deprecated) named PC link, database restore will be incomplete")
						else:
							self.__records.pclink(recmap[p], recmap[c], txn=txn)

			elif r in simple_choices:
				g.debug.msg('LOG_INFO', r)
				link(rr, simple_choices[r])

			else:
				g.debug.msg('LOG_ERROR', "Unknown category: ", r)
			return True


		@DBProxy.publicmethod
		def restore(self, restorefile=None, types=None, ctx=None, txn=None):
				"""This will restore the database from a backup file. It is nondestructive, in that new items are
				added to the existing database. Naming conflicts will be reported, and the new version
				will take precedence, except for Records, which are always appended to the end of the database
				regardless of their original id numbers. If maintaining record id numbers is important, then a full
				backup of the database must be performed, and the restore must be performed on an empty database."""
				if not txn: txn = None
				self.LOG(4, "Begin restore operation", ctx=ctx, txn=txn)

				if not self.__importmode:
					self.LOG(3, "WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
					return

				user, groups = ctx.username, ctx.groups

				if not ctx.checkadmin():
					raise subsystems.exceptions.SecurityError, "Database restore requires admin access"

				recmap = {}
				nrec = 0

				t0 = time.time()
				tmpindex = {}
				nel = 0


				recblock, paramblock, recdefblock, userblock = [],[],[],[]
				blocklength = 5000
				commitrecs = False
				changesmade = False


				if not types:
					types = set(["record", "user", "workflow",
						"recorddef", "paramdef", "bdos",
						"pdchildren", "pdcousins", "rdcousins",
						"recchildren", "reccousins"])


				iteration = 0
				cleanup_needed = False

				fin = self.__restore_openfile(restorefile)
				running = True
				try:
					with emen2.util.ticker.spinning_distraction():
						while running:
							r = pickle.load(fin)
							commitrecs = False

							# insert and renumber record
							if isinstance(r, datatypes.datastorage.Record) and "record" in types:
								recblock.append(r)
							elif isinstance(r, datatypes.datastorage.RecordDef) and "recorddef" in types:
								recdefblock.append(r)
							elif isinstance(r, datatypes.datastorage.ParamDef) and "paramdef" in types:
								paramblock.append(r)
							elif isinstance(r, datatypes.user.User) and "user" in types:
								userblock.append(r)

							if sum(len(block) for block in [recblock, userblock, paramblock, recdefblock]) >= blocklength:
								commitrecs = True

							restoreblocks = lambda: self.__restore_commitblocks(userblock, paramblock, recdefblock, recblock, ctx=ctx, txn=txn, map=recmap)

							if commitrecs: txn = txn or self.newtxn()
							elif txn is None: txn = self.newtxn()

							iteration += 1

							try:
								if commitrecs: changesmade = restoreblocks()
								# insert Workflow
								elif isinstance(r, WorkFlow) and "workflow" in types:
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
					g.debug.msg('LOG_DEBUG', 'EOF')
					g.debug.msg('LOG_INFO', 'Import Done')
					running = False

				g.debug.msg('LOG_INFO', "Done!")
				if txn: self.txncommit(txn=txn)

				txn = self.newtxn()
				changesmade = restoreblocks()

				if txn:
					self.txncommit(txn=txn)
					self.LOG(4, "Import Complete, checkpointing", ctx=ctx, txn=txn)
					self.__dbenv.txn_checkpoint()

				assert len(self.txnlog) == 0
				g.debug.msg('LOG_DEBUG', 'restore done')





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
			# 				if (nr < 20) : g.debug(r["identifier"])
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
			# 				else : g.debug("Unknown category ", r)
			#
			# g.debug("Users=", nu, "	 ParamDef=", npd, "	 RecDef=", nrd, "	 Records=", nr, "	 Links=", np)
