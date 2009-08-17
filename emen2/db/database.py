import bsddb3
from bsddb3 import db
from cPickle import load, dump

from emen2.Database.btrees2 import *
from emen2.Database.datastorage import *
from emen2.Database.exceptions import *
from emen2.Database.user import *
import copy
import emen2.Database.subsystems

from functools import partial, wraps

import copy
import atexit
import emen2
import emen2.util.utils
import hashlib
import operator
import operator
import os
import sys
import time
import traceback
import operator
import collections


from emen2.util.utils import prop


import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


regex_pattern = 	 u"(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"		 \
"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
								"|(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
regex = re.compile(regex_pattern, re.UNICODE) # re.UNICODE


regex_pattern2 = 	u"(\$\$(?P<var>(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"		\
								"|(\$\@(?P<macro>(?P<macro1>\w*)(?:\((?P<macro2>[\w\s,]+)\))?))(?P<macrosep>[\s<]?)" \
								"|(\$\#(?P<name>(?P<name1>\w*)))(?P<namesep>[\s<:]?)"
regex2 = re.compile(regex_pattern2, re.UNICODE) # re.UNICODE



recommentsregex = "\n"
pcomments = re.compile(recommentsregex) # re.UNICODE




TIMESTR = "%Y/%m/%d %H:%M:%S"
MAXIDLE = 604800


usetxn = True

envopenflags = db.DB_CREATE | db.DB_THREAD | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_LOG |  db.DB_INIT_TXN | db.DB_MULTIVERSION
txnflags_read = db.DB_TXN_SNAPSHOT
#txnflags_rmw = db.DB_TXN_SNAPSHOT


#| db.DB_READ_UNCOMMITTED
# | db.DB_INIT_TXN
DEBUG = 0 #TODO consolidate debug flag



# def txn_decorator(func):
# 	def _inner(self, *args, **kwargs):
# 		txn = kwargs.get('txn')
# 		txn_started = False
# 		if txn is None:
# 			txn = self.newtxn()
# 			txn_started = True
# 		kwargs['txn'] = txn
# 		try:
# 			func(self,*args, **kwargs)
# 		except:
# 			if txn_started:
# 				txn.discard()
# 			raise
# 		else:
# 			txn.commit()

#class extract_recid(object):
#	def __init__(self, argno):
#		self.argno = argno-1
#	def __call__(self, func):
#		check = partial(any, lambda rec: isinstance(rec, Record))
#		def _inner(*args, **kwargs):
#			if check(args[self.argno]):
#				args = (list(args[:self.argno]),
#						[rec.rectype if isinstance(x, datastorage.Record) else rec for rec in args[self.argno]],
#						args[self.argno+1:])
#				args[0].extend(args[1])
#				args[0].extend(args[2])
#				args = args[0]
#			return func(*args, *kwargs)









class DBProxy(object):

	__publicmethods = {}
	__extmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls.__publicmethods) | set(cls.__extmethods)



	def __init__(self, db=None, dbpath=None, importmode=False, ctxid=None, host=None):
		self.__txn = None
		self.__bound = False
		if not db:
			self.__db = Database(dbpath, importmode=importmode)
		else:
			self.__db = db
		self.__ctx = None
		#self._setcontext(ctxid, host)


	def _starttxn(self):
		self.__txn = self.__db.newtxn()
		#self.__txn = self.__db.newtxn()

	def _committxn(self):
		self.__db.txncommit(txn=self.__txn)
		#if self.__txn is not None:
		#	self.__txn.commit()

	def _aborttxn(self):
		self.__db.txnabort(txn=self.__txn)
		#if self.__txn is not None:
		#	self.__txn.abort()


	def _login(self, username="anonymous", password="", host=None):
		ctxid, host = self.__db._login(username, password, host=host)
		self._setcontext(ctxid, host)
		return ctxid, host


	def _setcontext(self, ctxid=None, host=None):
		g.debug("dbproxy: setcontext %s %s"%(ctxid,host))
		self.__ctx = self.__db._getcontext(ctxid, host)
		print "dbproxy _getcontext"
		print self.__ctx
		
		self.__bound = True



	def _clearcontext(self):
		g.debug("dbproxy: clearcontext")
		if self.__bound:
			self.__ctx = None
			self.__bound = False



	@prop.init
	def _bound():
		def fget(self): return self.__bound
		def fdel(self): self._clearcontext()
		return dict(fget=fget, fdel=fdel)



	def _ismethod(self, name):
		if name in self._allmethods(): return True
		return False



	@classmethod
	def _register_publicmethod(cls, name, func):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.debug.msg('LOG_INIT', "REGISTERING PUBLICMETHOD (%s)" % name)
		cls.__publicmethods[name] = func



	@classmethod
	def _register_extmethod(cls, name, refcl):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.debug.msg('LOG_INIT', "REGISTERING EXTENSION (%s)" % name)
		cls.__extmethods[name] = refcl



	def _callmethod(self, method, args, kwargs):
		args=list(args)
		return getattr(self, method)(*args, **kwargs)


	def _getctx(self):
		return self.__ctx

	def __getattribute__(self, name):

		if name.startswith('__') and name.endswith('__'):
			result = getattr(self.__db, name)()
		elif name.startswith('_'):
			return object.__getattribute__(self, name)

		db = self.__db
		kwargs = {}

		kwargs["ctx"] = self.__ctx
		kwargs["txn"] = self.__txn

		result = None
		if name in self._allmethods():

			#g.debug("DB: %s, kwargs: %s"%(name,kwargs))

			result = self.__publicmethods.get(name) # or self.__extmethods.get(name)()

			if result:
				result = wraps(result)(partial(result, db, **kwargs))
			else:
				result = self.__extmethods.get(name)()

				kwargs['db'] = db
				if result: result = partial(result.execute, **kwargs)

			result = wraps(result.func)(result)
		else:
			raise AttributeError('No such attribute %s of %r' % (name, db))

		return result





class DBExt(object):
	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls
	@classmethod
	def register(cls):
		DBProxy._register_extmethod(cls.__methodname__, cls) #cls.__name__, cls.__methodname__, cls





def DB_syncall():
	"""This 'syncs' all open databases"""
	#if DEBUG > 2:
	#	print "sync %d BDB databases" % (len(BTree.alltrees) + len(IntBTree.alltrees) + len(FieldBTree.alltrees))
	#t = time.time()
	for i in BTree.alltrees.keys(): i.sync()
	for i in RelateBTree.alltrees.keys(): i.sync()
	for i in FieldBTree.alltrees.keys(): i.sync()
	# print "%f sec to sync"%(time.time()-t)


def publicmethod(func):
	DBProxy._register_publicmethod(func.func_name, func)

	@wraps(func)
	def _inner(self, *args, **kwargs):
		result = None
		txn = kwargs.get('txn')
		commit = False
		if txn is None:
			txn = self.newtxn()
			commit = True
		kwargs['txn'] = txn


		try:
			#g.debug('calling func: %r' %  func)
			result = func(self, *args, **kwargs)
			#g.debug('finished func: %r' %  func)
		except Exception, e:
			g.debug('aborting %r if we started the txn -- Exception raised: %r, %s !!!' % (func, e, e))
			traceback.print_exc(e)
			if commit is True:
				g.debug('aborting !!!!!')
				txn.abort()
			raise
		else:
			#g.debug('checking whether to commit???')
			if commit is True:
				g.debug('committing')
				txn and txn.commit()

		return result

	return _inner

def adminmethod(func):
	@wraps(func)
	def _inner(*args, **kwargs):
		ctx = kwargs.get('ctx')
		if ctx is None:
			ctx = [c for x in args is isinstance(x, User)] or None
			if ctx is not None:
				ctx = ctx.pop()
		if ctx.checkadmin():
			return func(*args, **kwargs)
		else:
			raise SecurityError, 'No Admin Priviliges'
	return _inner







#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()
class Database(object):
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





		def __init__(self, path=".", cachesize=32000000, logfile="db.log", importmode=0, rootpw=None, recover=0, allowclose=True, more_flags=0):
			"""path - The path to the database files, this is the root of a tree of directories for the database
			cachesize - default is 64M, in bytes
			logfile - defualt "db.log"
			importmode - DANGEROUS, makes certain changes to allow bulk data import. Should be opened by only a single thread in importmode.
			recover - Only one thread should call this. Will run recovery on the environment before opening."""

			global envopenflags, usetxn

			if usetxn:
				self.newtxn = self.newtxn1
				envopenflags |= db.DB_INIT_TXN
			else:
				self.LOG("LOG_INFO","Note: transaction support disabled")
				self.newtxn = self.newtxn2

			self.path = path
			self.logfile = path + "/" + logfile
			self.lastctxclean = time.time()
			self.__importmode = importmode

			# ian: this helps render and validate vartypes and convert between properties/units
			self.vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			self.indexablevartypes = set([i.getvartype() for i in filter(lambda x:x.getindextype(), [self.vtm.getvartype(i) for i in self.vtm.getvartypes()])])
			self.unindexed_words = set(["in", "of", "for", "this", "the", "at", "to", "from", "at", "for", "and", "it", "or"])

			self.maxrecurse = 50

			#xtraflags = 0
			if recover:
				envopenflags |= db.DB_RECOVER

			# This sets up a DB environment, which allows multithreaded access, transactions, etc.
			if not os.access(path + "/home", os.F_OK):
				os.makedirs(path + "/home")

			if not os.access(path + "/security", os.F_OK):
				os.makedirs(path + "/security")

			if not os.access(path + "/index", os.F_OK):
				os.makedirs(path + "/index")

			self.__allowclose = bool(allowclose)




		#def __opendbenv(self):

			self.LOG(4, "Database initialization started")

			dbci = file(g.EMEN2ROOT+'/DB_CONFIG')
			dbco = file(self.path + '/home/DB_CONFIG', 'w')
			try:
				dbco.write(dbci.read())
			finally:
				[fil.close() for fil in (dbci, dbco)]

			self.__dbenv = bsddb3.db.DBEnv() #db.DBEnv()
			self.__dbenv.set_data_dir(self.path)

			#self.__dbenv.set_cachesize(0, cachesize, 4) # gbytes, bytes, ncache (splits into groups)
			self.__dbenv.set_lg_bsize(1024*1024)
			self.__dbenv.set_lg_max(1024*1024*8)
			
			
			self.__dbenv.set_lk_detect(db.DB_LOCK_DEFAULT) # internal deadlock detection
			self.__dbenv.set_lk_max_locks(100000)
			self.__dbenv.set_lk_max_lockers(100000)
			self.__dbenv.set_lk_max_objects(100000)
			#set_lk_max_lockers
			#set_lk_max_locks

			#if self.__dbenv.DBfailchk(flags=0):
				#self.LOG(1,"Database recovery required")
				#sys.exit(1)

			self.__dbenv.open(self.path + "/home", envopenflags)

			global globalenv
			globalenv = self.__dbenv



		#def __opencoredb(self):
		
			txn = self.newtxn()
			#print "txn is %s"%txn


			# Users
			# active database users / groups
			self.__users = BTree("users", keytype="s", filename=path+"/security/users.bdb", dbenv=self.__dbenv, txn=txn)

			self.__groupsbyuser = IndexKeyBTree("groupsbyuser", keytype="s", filename=path+"/security/groupsbyuser", dbenv=self.__dbenv, txn=txn)

			self.__groups = BTree("groups", keytype="ds", filename=path+"/security/groups.bdb", dbenv=self.__dbenv, txn=txn)
			#self.__updatecontexts = False

			# new users pending approval
			self.__newuserqueue = BTree("newusers", keytype="s", filename=path+"/security/newusers.bdb", dbenv=self.__dbenv, txn=txn)

			# multisession persistent contexts
			self.__contexts_p = BTree("contexts", keytype="s", filename=path+"/security/contexts.bdb", dbenv=self.__dbenv, txn=txn)

			# local cache dictionary of valid contexts
			self.__contexts = {}




			# Binary data names indexed by date
			self.__bdocounter = BTree("BinNames", keytype="s", filename=path+"/BinNames.bdb", dbenv=self.__dbenv, txn=txn)

			# Defined ParamDefs
			# ParamDef objects indexed by name
			self.__paramdefs = RelateBTree("ParamDefs", keytype="s", filename=path+"/ParamDefs.bdb", dbenv=self.__dbenv, txn=txn)

			# Defined RecordDefs
			# RecordDef objects indexed by name
			self.__recorddefs = RelateBTree("RecordDefs", keytype="s", filename=path+"/RecordDefs.bdb", dbenv=self.__dbenv, txn=txn)



			# The actual database, keyed by recid, a positive integer unique in this DB instance
			# ian todo: check this statement:
			# 2 special keys exist, the record counter is stored with key -1
			# and database information is stored with key=0

			# The actual database, containing id referenced Records
			self.__records = RelateBTree("database", keytype="d", filename=path+"/database.bdb", dbenv=self.__dbenv, txn=txn)

			# Indices

			# index of records each user can read
			self.__secrindex = FieldBTree("secrindex", filename=path+"/security/roindex.bdb", keytype="ds", dbenv=self.__dbenv, txn=txn)

			# index of records belonging to each RecordDef
			self.__recorddefindex = FieldBTree("RecordDefindex", filename=path+"/RecordDefindex.bdb", keytype="s", dbenv=self.__dbenv, txn=txn)

			# key=record id, value=last time record was changed
			self.__timeindex = BTree("TimeChangedindex", keytype="d", filename=path+"/TimeChangedindex.bdb", dbenv=self.__dbenv, txn=txn)

			# dictionary of FieldBTrees, 1 per ParamDef, not opened until needed
			self.__fieldindex = {}


			self.__indexkeys = IndexKeyBTree("IndexKeys", keytype="s", filename=path+"/IndexKeys.bdb", dbenv=self.__dbenv, txn=txn)




			# Workflow database, user indexed btree of lists of things to do
			# again, key -1 is used to store the wfid counter
			self.__workflow = BTree("workflow", keytype="d", filename=path+"/workflow.bdb", dbenv=self.__dbenv, txn=txn)


			# USE OF SEQUENCES DISABLED DUE TO DATABASE LOCKUPS
			#db sequence
			# self.__dbseq = self.__records.create_sequence()

			#self.__recorddefbyrec = IntBTree("RecordDefByRec", path + "/RecordDefByRec.bdb", dbenv=self.__dbenv, relate=0)

			# The mirror database for storing offsite records
			#self.__mirrorrecords = BTree("mirrordatabase", filename=path+"/mirrordatabase.bdb", dbenv=self.__dbenv)


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
					self.__createskeletondb(txn=txn)


				g.debug.add_output(self.log_levels.values(), file(self.logfile, "a"))
				#self.__anonymouscontext = self._login(txn=txn)
				_actxid, _ahost = self._login(txn=txn)
				
			except:
				txn and self.txnabort(txn=txn)
				raise
			finally:
				self.txncommit(txn=txn)



			self.__anonymouscontext = self._getcontext(_actxid, _ahost)






		def __createskeletondb(self, ctx=None, txn=None):

			# Create an initial administrative user for the database
			u = User()
			u.username = u"root"
			u.password = hashlib.sha1(g.ROOTPW).hexdigest()

			#u.groups = [-1]
			#u.creationtime = self.gettime()
			#self.__users.set(u"root", u, txn)

			self.__commit_users([u], ctx=ctx, txn=txn)



			#pd = ParamDef("owner", "string", "Record Owner", "This is the user-id of the 'owner' of the record")
			basepds = [
				ParamDef("creator", "user", "Record Creator", "The user-id that initially created the record"),
				ParamDef("modifyuser", "user", "Modified by", "The user-id that last changed the record"),
				ParamDef("creationtime", "datetime", "Creation time", "The date/time the record was originally created"),
				ParamDef("modifytime", "datetime", "Modification time", "The date/time the record was last modified"),
				ParamDef("comments", "comments", "Record comments", "Record comments"),
				ParamDef("rectype", "string", "Record type", "Record type (RecordDef)"),
				ParamDef("permissions", "acl", "Permissions", "Permissions"),
				ParamDef("parents","links","Parents", "Parents"),
				ParamDef("children","links","Children", "Children"),
				ParamDef("publish","boolean","Publish", "Publish"),
				ParamDef("deleted","boolean","Deleted", "Deleted"),
				ParamDef("recid","int","Record ID","Record ID"),
				ParamDef("uri","string","Resource Location", "Resource Location")
			]

			self.__commit_paramdefs(basepds, ctx=ctx, txn=txn)


			folder = RecordDef()
			folder.name = "folder"
			folder.desc_long = "Folder"
			folder.desc_short = "Folder"
			folder.mainview = "Folder!"

			self.__commit_recorddefs([folder], ctx=ctx, txn=txn)



			_admin = Group()
			_admin.name = "admin"
			_admin.adduser(3, "root")

			_readadmin = Group()
			_readadmin.name = "readadmin"

			_create = Group()
			_create.name = "create"
			_create.adduser(3, "root")

			_anon = Group()
			_anon.name = "anon"

			self.__commit_groups([_admin, _readadmin, _create, _anon], ctx=ctx, txn=txn)



		###############################
		# section: txn
		###############################



		# one of these 2 methods is mapped to self.newtxn()
		def newtxn1(self, parent=None, ctx=None):
			txn = self.__dbenv.txn_begin(parent=parent)
			g.debug("NEW TXN --> %s    PARENT IS %s"%(txn,parent))
			return txn


		def newtxn(self, ctx=None, txn=None):
			return None


		def newtxn2(self, ctx=None, txn=None):
			return None


		def txncheck(self, ctx=None, txn=None):
			if not txn:
				txn = self.newtxn(ctx=ctx)
			return txn


		def txnabort(self, ctx=None, txn=None):
			g.debug('LOG_ERROR', "TXN ABORT --> %s\n\n"%txn)
			if txn:
				txn.abort()


		def txncommit(self, ctx=None, txn=None):
			g.debug("TXN COMMIT --> %s\n\n"%txn)
			if txn:
				txn.commit()
			elif not self.__importmode:
				DB_syncall()




		###############################
		# section: utility
		###############################


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
				g.debug.msg(self.log_levels.get(level, level), "%s: (%s) %s" % (self.gettime(ctx=ctx,txn=txn), self.log_levels.get(level, level), message))
			except:
				traceback.print_exc(file=sys.stdout)
				print("Critical error!!! Cannot write log message to '%s'\n")


		# needs txn?
		def __str__(self):
			"""Try to print something useful"""
			return "Database %d records\n( %s )"%(int(self.__records.get(-1,0)), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))


		# needs txn?
		def __del__(self):
			self.close()


		# ian: todo: wtf.
		def closedb(self, ctx=None, txn=None):
			self.LOG('LOG_DEBUG', 'closing dbs')
			if self.__allowclose == True:
				for btree in self.__dict__.values():
					if getattr(btree, '__class__', object).__name__.endswith('BTree'):
						try: btree.close()
						except db.InvalidArgError, e: print e
					for btree in self.__fieldindex.values(): btree.close()
		def close(self, ctx=None, txn=None):
			self.closedb(ctx, txn=txn)
			self.__dbenv.close()

#				 pass
#				 print self.__btreelist
#				 self.__btreelist.extend(self.__fieldindex.values())
#				 print self.__btreelist
#				 for bt in self.__btreelist:
#						 print '--', bt ; sys.stdout.flush()
#						 bt.close()


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




		@publicmethod
		def gettime(self, ctx=None, txn=None):
			return time.strftime(TIMESTR)




		###############################
		# section: login / passwords
		###############################

		def __makecontext(self, username="anonymous", host=None):
			'''so we can simulate a context for approveuser'''
			newcontext = Context(db=self, username=username, host=host)
			# ian: todo: add a well-seeded random number here
			s = hashlib.sha1(username + unicode(host) + unicode(time.time()))
			newcontext.ctxid = s.hexdigest()
			return newcontext


		#@txn
		#@publicmethod
		# No longer public method; only through DBProxy to force host=...
		def _login(self, username="anonymous", password="", host=None, maxidle=MAXIDLE, ctx=None, txn=None):
			"""Logs a given user in to the database and returns a ctxid, which can then be used for
			subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""
			# ctx will typically be None here

			newcontext = None
			username = unicode(username)

			# Anonymous access
			if username == "anonymous": # or username == ""
				newcontext = self.__makecontext()
				g.debug('Anonymous Login!!!')

			else:
				g.debug('Authentication Login!!!')
				checkpass = self.__checkpassword(username, password, ctx=ctx, txn=txn)

				# Admins can "su"
				if checkpass or self.checkadmin(ctx=ctx, txn=txn):
					g.debug('new context: %r' %newcontext)
					newcontext = self.__makecontext(username, host)
					g.debug('new context: %r' %newcontext)

				else:
					self.LOG(0, "Invalid password: %s (%s)" % (username, host), ctx=ctx, txn=txn)
					raise AuthenticationError, AuthenticationError.__doc__



			#if ctx.user != None:
			#	ctx.groups.append(-3)
			#ctx.groups.append(-4)
			#ctx.groups=list(set(ctx.groups))

			# ian: todo: add parent=
			#txn2 = self.newtxn(parent=txn)

			try:
				self.__setcontext(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
				self.LOG(4, "Login succeeded %s (%s)" % (username, newcontext.ctxid), ctx=ctx, txn=txn)
				#self.txncommit(txn=txn2)

			except:
				self.LOG(4, "Error writing login context, txn aborting!", ctx=ctx, txn=txn)
				raise
				#self.txnabort(txn=txn2)


			return newcontext.ctxid, newcontext.host
			#result = self._getcontext(newcontext.ctxid, newcontext.host, ctx=ctx, txn=txn)
			#return result




		# Logout is the same as delete context
		@publicmethod
		def logout(self, ctx=None, txn=None):
			self.deletecontext(ctx=ctx, txn=txn)



		def __checkpassword(self, username, password, ctx=None, txn=None):
			"""Check password against stored hash value"""
			s = hashlib.sha1(password)

			try:
				user = self.__users.sget(username, txn=txn)
			except:
				raise AuthenticationError, AuthenticationError.__doc__

			if user.disabled:
				raise DisabledUserError, DisabledUserError.__doc__ % username

			if s.hexdigest() == user.password:
				return True

			#raise AuthenticationError, "Invalid password"



		###############################
		# section: contexts
		###############################


		#@txn
		@publicmethod
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
					self.LOG("LOG_COMMIT","Commit: self.__contexts_p.set: %s"%context.ctxid, ctx=ctx, txn=txn)
				
				# except ValueError, inst:
				# 	self.LOG("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst), ctx=ctx, txn=txn)
				# 	
				# except db.DBError, inst:
				except Exception, inst:
					self.LOG("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst), ctx=ctx, txn=txn)
					raise


			# delete context
			else:
				try:
					del self.__contexts[ctxid]
				except Exception, inst:
					pass

				try:
					self.__contexts_p.set(ctxid, None, txn=txn) #del ... [ctxid]
					self.LOG("LOG_COMMIT","Commit: self.__contexts_p.__delitem__: %s"%ctxid, ctx=ctx, txn=txn)

				except Exception, inst:
					self.LOG("LOG_CRITICAL","Unable to delete persistent context %s (%s)"%(ctxid, inst), ctx=ctx, txn=txn)
					raise

			#@end



		def __init_context(self, context, user=None, txn=None):
			context.db = self
			context._user = user or self.getuser(context._username, ctx=context, txn=txn)


		def _getcontext(self, key, host, ctx=None, txn=None):
			"""Takes a ctxid key and returns a context (for internal use only)
			Note that both key and host must match. Returns context instance."""

			if key in set([None, 'None']):
				return self.__anonymouscontext

			key = unicode(key)

			if (time.time() > self.lastctxclean + 30): # or self.__updatecontexts):
				# maybe not the perfect place to do this, but it will have to do
				self.__cleanupcontexts(ctx=ctx, txn=txn)

			try:
				context = self.__contexts[key]

			except:
				try:
					context = self.__contexts_p.sget(key, txn=txn) #[key]
				except:
					self.LOG(4, "Session expired %s" % key, ctx=ctx, txn=txn)
					raise SessionError, "Session expired: %s"%key


			if host and host != context.host :
				self.LOG(0, "Hacker alert! Attempt to spoof context (%s != %s)" % (host, context.host), ctx=ctx, txn=txn)
				raise SessionError, "Bad address match, login sessions cannot be shared"


			# this sets up db handle ref, users, groups for context...
			self.__init_context(context, txn=txn)

			self.__contexts[key] = context		# cache result from database

			context.time = time.time()

			#g.debug('!!!!!!!!!!!!!!!!!!!!!!******************************!!!!!!!!!!!!!!!!!!!!!!!!!')
			return context



		@publicmethod
		def checkcontext(self, ctx=None, txn=None):
			"""This allows a client to test the validity of a context, and
			get basic information on the authorized user and his/her permissions"""
			try:
				return (ctx.username, ctx.groups)
			except:
				return None, None


		@publicmethod
		def checkadmin(self, ctx=None, txn=None):
			"""Checks if the user has global write access. Returns bool."""
			return ctx.checkadmin()



		@publicmethod
		def checkreadadmin(self, ctx=None, txn=None):
			"""Checks if the user has global read access. Returns bool."""
			return ctx.checkreadadmin()



		@publicmethod
		def checkcreate(self, ctx=None, txn=None):
			"""Check for permission to create records. Returns bool."""
			return ctx.checkcreate()



		def loginuser(self, ctx=None, txn=None):
			"""Who am I?"""
			return ctx.username




		###############################
		# section: binaries
		###############################


		#@txn
		#@write #self.__bdocounter
		@publicmethod
		def newbinary(self, date, name, recid, key=None, filedata=None, paramname=None, ctx=None, txn=None):
				"""Get a storage path for a new binary object. Must have a
				recordid that references this binary, used for permissions. Returns a tuple
				with the identifier for later retrieval and the absolute path"""


				if name == None or unicode(name) == "":
					raise ValueError, "BDO name may not be 'None'"

				if key and not ctx.checkadmin():
					raise SecurityError, "Only admins may manipulate binary tree directly"

				if date == None:
					date = self.gettime(ctx=ctx, txn=txn)

				if not key:
					year = int(date[:4])
					mon = int(date[5:7])
					day = int(date[8:10])
					newid = 0
				else:
					date=unicode(key)
					year=int(date[:4])
					mon=int(date[4:6])
					day=int(date[6:8])
					newid=int(date[9:13],16)


				key = "%04d%02d%02d" % (year, mon, day)

				# ian: check for permissions because actual operations are performed.
				rec = self.getrecord(recid, ctx=ctx, txn=txn)
				if not rec.writable():
					raise SecurityError, "Write permission needed on referenced record."


				for i in g.BINARYPATH:
					if key >= i[0] and key < i[1]:
						# actual storage path
						path = "%s/%04d/%02d/%02d" % (i[2], year, mon, day)
						break
				else:
					raise KeyError, "No storage specified for date %s" % key


				# try to make sure the directory exists
				try:
					os.makedirs(path)
				except:
					pass


				# Now we need a filespec within the directory
				# dictionary keyed by date, 1 directory per day
				#if usetxn:
				#	txn = self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
				#else:

				#@begin

				try:
					itm = self.__bdocounter.get(key, txn=txn)
					newid = max(itm.keys()) + 1
				except:
					itm = {}

				itm[newid] = (name, recid)
				self.__bdocounter.set(key, itm, txn=txn)
				self.LOG("LOG_COMMIT","Commit: self.__bdocounter.set: %s"%key, ctx=ctx, txn=txn)


				#@end

				filename = path + "/%05X"%newid
				bdo = key + "%05X"%newid

				#todo: ian: raise exception if overwriting existing file (but this should never happen unless the file was pre-existing?)
				if os.access(path + "/%05X" % newid, os.F_OK) and not ctx.checkadmin():
					raise SecurityError, "Error: Binary data storage, attempt to overwrite existing file '%s'"
					#self.LOG(2, "Binary data storage: overwriting existing file '%s'" % (path + "/%05X" % newid))


				# if a filedata is supplied, write it out...
				# todo: use only this mechanism for putting files on disk
				if filedata:
					print "Writing %s bytes disk: %s"%(len(filedata),filename)
					f=open(filename,"wb")
					f.write(filedata)
					f.close()
					print "...done"


				if paramname:
					param = self.getparamdef(paramname, ctx=ctx, txn=txn)
					if param.vartype == "binary":
						v = rec.get(paramname,[])
						v.append("bdo:"+bdo)
						rec[paramname]=v

					elif param.vartype == "binaryimage":
						rec[paramname]="bdo:"+bdo

					else:
						raise Exception, "Error: invalid vartype for binary: parameter %s, vartype is %s"%(paramname, param.vartype)

					self.putrecord(rec, ctx=ctx, txn=txn)


				return (bdo, filename)
				#return (key + "%05X" % newid, path + "/%05X" % newid)





		@publicmethod
		def getbinary(self, idents, filt=True, vts=None, params=None, ctx=None, txn=None):
				"""Get a storage path for an existing binary object. Returns the
				object name and the absolute path"""

				# process idents argument for bids (into list bids) and then process bids
				ret={}
				bids=[]
				recs=[]

				if not vts:
					vts=["binary","binaryimage"]

				ol=0
				if isinstance(idents,basestring):# or not hasattr(idents,"__iter__"):
					ol=1
					bids=[idents]
					idents=bids
				if isinstance(idents,(int,Record)):
					idents=[idents]

				bids.extend(filter(lambda x:isinstance(x,basestring), idents))

				recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), idents), filt=1, ctx=ctx, txn=txn))
				recs.extend(filter(lambda x:isinstance(x,Record), idents))
				bids.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))

				bids=filter(lambda x:isinstance(x, basestring), bids)

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
							name, recid = self.__bdocounter.sget(key, txn=txn)[bid] #[key][bid]
					except:
							if filt:
								continue
							else:
								raise KeyError, "Unknown identifier %s" % ident


					try:
						self.getrecord(recid, ctx=ctx, txn=txn)
						ret[ident] = (name, path + "/%05X" % bid, recid)

					except:
						if filt:
							continue
						else:
							raise SecurityError, "Not authorized to access %s(%0d)" % (ident, recid)


				#if ol: return ret.values()[0]
				return ret



		@publicmethod
		def getbinarynames(self, ctx=None, txn=None):
			"""Returns a list of tuples which can produce all binary object
			keys in the database. Each 2-tuple has the date key and the nubmer
			of objects under that key. A somewhat slow operation."""

			if ctx.username == None:
					raise SecurityError, "getbinarynames not available to anonymous users"

			ret = self.__bdocounter.keys(txn=txn)
			ret = [(i, len(self.__bdocounter.get(txn=txn))) for i in ret]
			return ret





		###############################
		# section: query
		###############################




		@publicmethod
		def query(self, q=None, rectype=None, boolmode="AND", ignorecase=True, constraints=None, childof=None, parentof=None, recurse=False, subset=None, returndict=False, includeparams=None, ctx=None, txn=None):

			if boolmode not in ["AND","OR"]:
				raise Exception, "Invalid boolean mode: %s. Must be AND, OR"%boolmode

			constraints = constraints or []
			subset = set(subset or [])
			includeparams = set(includeparams or [])

			if q:
				constraints.append(["*","contains",unicode(q)])

			if recurse:
				recurse = self.maxrecurse


			# include these methods to make life easier...
			if not constraints:
				recs = []
				if childof:
					recs.append(self.getchildren(childof, recurse=recurse, ctx=ctx, txn=txn))
				if parentof:
					recs.append(self.getparents(parentof, recurse=recurse, ctx=ctx, txn=txn))
				if rectype:
					recs.append(self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn))
				if boolmode=="AND":
					return reduce(set.intersection, recs)
				return reduce(set.union, recs)



			vtm = emen2.Database.subsystems.datatypes.VartypeManager()

			# x is argument, y is record value
			cmps = {
				"==": lambda y,x:x == y,
				"!=": lambda y,x:x != y,
				"contains": lambda y,x:unicode(x) in unicode(y),
				"!contains": lambda y,x:unicode(x) not in unicode(y),
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

			# check that constraints are sane, then partition into wildcard and normal
			# vtm.validate(self.__paramdefs[i[0]], i[1], db=self, ctx=ctx, txn=txn)

			# ok, new approach: name each constraint, search and store result, then join at the end if bool=AND
			constraints = dict(enumerate(map(lambda i:(unicode(i[0]), str(i[1]), i[2]), constraints)))
			c_results_paramkeys = dict((i,{}) for i in constraints.keys())  # {}
			c_results_recs = dict((i,set()) for i in constraints.keys()) # {}
			inds = set()

			for param, pkeys in self.__indexkeys.items(txn=txn):
				# ian todo: find a way to reduce number of lookups/validations needed..
				for name, c in constraints.items():
					if c[0] != param and c[0] != "*":
						continue

					try:
						cargs = vtm.validate(self.__paramdefs.get(param, txn=txn), c[2], db=self, ctx=ctx, txn=txn)
					except Exception, inst:
						if c[0] != "*":
							raise Exception, "Unable to satisfy constraint..."
						continue

					comp = partial(cmps[c[1]], cargs) #*cargs
					r = filter(comp, pkeys)
					# print "filtered %s: %s -> %s"%(param, cargs, r)
					if r:
						c_results_paramkeys[name][param] = r    #.append((param, r))
						inds.add(param)

			matches = {}

			for param in inds:
				ind = self.__getparamindex(param, ctx=ctx, txn=txn)

				for name, paramkeys in c_results_paramkeys.items():

					paramkeys = paramkeys.get(param, [])
					for key in paramkeys:

						recids = ind.get(key)

						if not c_results_recs.has_key(name):
							c_results_recs[name] = set()
						c_results_recs[name] |= recids

						for recid in recids:
							if not matches.has_key(recid):
								matches[recid] = set()
							matches[recid].add(param)


			#recs = set(matches.keys())

			# if boolmode is "AND", filter for records that do not satisfy all named constraints
			subsets = c_results_recs.values()

			subsets.append(set(matches.keys()))

			if subset:
				subsets.append(subset)
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


			if not returndict:
				return recs

			#print "getrecords... len %s"%len(recs)
			recs = self.getrecord(recs, filt=1, ctx=ctx, txn=txn)
			#if rectype:
			#	recs = filter(lambda x:x.rectype == rectype, recs)

			#print "preparing results..."
			ret = {}
			for i in recs:
				ret[i.recid] = {}
				for param in matches.get(i.recid, set()) | includeparams:
					#print "i.recid %s param %s value %s"%(i.recid, param, i.get(param))
					ret[i.recid][param] = i.get(param)

			return ret




		# ian todo: deprecate
		@publicmethod
		#def fulltextsearch(self, q, rectype=None, indexsearch=True, params=set(), recparams=0, builtinparam=0, ignorecase=True, subset=[], tokenize=0, single=0, includeparams=set()):
		def fulltextsearch(self, q, rectype=None, params=None, ignorecase=True, subset=None, includeparams=None, bool_and=False, bool_or=False, ctx=None, txn=None):


			# search these params
			subset = set(subset or [])
			params = set(params or [])
			includeparams = set(includeparams or [])

			builtin = set(["creator", "creationtime", "modifyuser", "modifytime", "permissions", "comments"])



			q = unicode(q)

			if ignorecase:
				q = q.lower()
				matcher = lambda x:qitem in unicode(x).lower()
			else:
				matcher = lambda x:qitem in unicode(x)

			q = set(q.split())



			indexmatches = {}
			#indexkeysitems = self.__indexkeys.items()


			for param,paramvalues in self.__indexkeys.items(txn=txn):
				for qitem in q:
					r = filter(matcher, paramvalues)
					if r:
						if (not params) or (params and param in params):
							if not indexmatches.has_key(param):
								indexmatches[param] = set()
							indexmatches[param] |= set(r)


			matches2 = {}

			for param,matchkeys in indexmatches.items():
				ind = self.__getparamindex(param, ctx=ctx, txn=txn)
				for key in matchkeys:
					for recid in ind.get(key):
						if not matches2.has_key(recid):
							 matches2[recid] = set()
						matches2[recid].add(param)



			recs = set(matches2.keys())
			if subset:
				recs &= subset

			recs = self.getrecord(recs, filt=1, ctx=ctx, txn=txn)
			if rectype:
				recs = filter(lambda x:x.rectype == rectype, recs)


			ret = {}

			for i in recs:
				ret[i.recid] = {}
				for param in matches2.get(i.recid, set()):# | includeparams:
					#print "i.recid %s param %s value %s"%(i.recid, param, i.get(param))
					ret[i.recid][param] = i.get(param)



			return ret




		#@publicmethod
		#def buildindexkeys(self, txn=None):
		def __rebuild_indexkeys(self, ctx=None, txn=None):

			inds = dict(filter(lambda x:x[1]!=None, [(i,self.__getparamindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

			self.__indexkeys.truncate(txn=txn)

			for k,v in inds.items():
					print "indexkeys: %s, len keys %s"%(k, len(v.keys(txn=txn)))
					self.__indexkeys.set(k, set(v.keys()), txn=txn)



		@publicmethod
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
				# print "searching %s"%k
				r = filter(matcher, v)
				if r: matches[k] = r

			#print matches
			matches2 = []

			for k,v in matches.items():
				paramindex = self.__getparamindex(k, ctx=ctx, txn=txn)
				for i in v:
					j = paramindex.get(i, txn=txn)
					for x in j:
						matches2.append((x, k, i))

			for i in matches2:
				print i




		#########################
		# section: indexes
		#########################



		@publicmethod
		def getindexbyrecorddef(self, recdefname, ctx=None, txn=None):
			"""Uses the recdefname keyed index to return all
			records belonging to a particular RecordDef as a set. Currently this
			is unsecured, but actual records cannot be retrieved, so it
			shouldn't pose a security threat."""
			return self.__recorddefindex.get(recdefname, txn=txn) or set()
			#[recdefname]
			#return self.__recorddefindex[unicode(recdefname).lower()]



		@publicmethod
		def getindexbyuser(self, username, ctx=None, txn=None):
			"""This will use the user keyed record read-access index to return
			a list of records the user can access. DOES NOT include that user's groups.
			Use getindexbycontext if you want to see all recs you can read."""

			if username == None:
				username = ctx.username

			if ctx.username != username and not ctx.checkreadadmin():
				raise SecurityError, "Not authorized to get record access for %s" % username

			return set(self.__secrindex.sget(username, txn=txn)) #[username]



		# @publicmethod
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
		@publicmethod
		def getparamstatistics(self, paramname, ctx=None, txn=None):

			if ctx.username == None:
				raise SecurityError, "Not authorized to retrieve parameter statistics"

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
		@publicmethod
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




		@publicmethod
		def getindexdictbyvalue(self, paramname, valrange=None, subset=None, ctx=None, txn=None):
			"""For numerical & simple string parameters, this will locate all records
			with the specified paramdef in the specified range.
			valrange may be a None (matches all), a single value, or a (min,max) tuple/list.
			This method returns a dictionary of all matching recid/value pairs
			if subset is provided, will only return values for specified recids"""

			print "getindexdictbyvalue"


			paramindex = self.__getparamindex(paramname, ctx=ctx, txn=txn)
			if paramindex == None:
				print "No such index %s"%paramname
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




		@publicmethod
		def getindexbycontext(self, ctx=None, txn=None):
			"""This will return the ids of all records a context has permission to access as a set. Does include groups."""


			if ctx.checkreadadmin():
				return set(range(self.__records.sget(-1, txn=txn))) #+1)) # Ed: Fixed an off by one error

			ret = set(self.__secrindex.sget(ctx.username, txn=txn)) #[ctx.username]
			for group in sorted(ctx.groups,reverse=True):
				ret |= set(self.__secrindex.sget(group, txn=txn))#[group]


			return ret




		# ian: todo: return dictionary instead of list?
		@publicmethod
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
		@publicmethod
		def groupbyrecorddef(self, recids, optimize=True, ctx=None, txn=None):
			"""This will take a set/list of record ids and return a dictionary of ids keyed
			by their recorddef"""

			if not hasattr(recids,"__iter__"):
				recids=[recids]

			if len(recids) == 0:
				return {}

			if (optimize and len(recids) < 1000) or (isinstance(list(recids)[0],Record)):
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

			if not isinstance(list(records)[0],Record):
				recs = self.getrecord(records, filt=1, ctx=ctx, txn=txn)

			ret={}
			for i in recs:
				if not ret.has_key(i.rectype): ret[i.rectype]=set([i.recid])
				else: ret[i.rectype].add(i.recid)

			return ret




		# ian: unused?
		@publicmethod
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
		@publicmethod
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
		@publicmethod
		def countchildren(self, key, recurse=0, ctx=None, txn=None):
			"""Unlike getchildren, this works only for 'records'. Returns a count of children
			of the specified record classified by recorddef as a dictionary. The special 'all'
			key contains the sum of all different recorddefs"""

			c = self.getchildren(key, "record", recurse=recurse, ctx=ctx, txn=txn)
			r = self.groupbyrecorddef(c, ctx=ctx, txn=txn)
			for k in r.keys(): r[k] = len(r[k])
			r["all"] = len(c)
			return r



		@publicmethod
		def getchildren(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctx=None, txn=None):
			"""Get children;
			keytype: record, paramdef, recorddef
			recurse: recursion depth
			rectype: for records, return only children of type rectype
			filt: filt by permissions
			tree: return results in graph format; default is set format
			"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", filt=filt, tree=tree, ctx=ctx, txn=txn)



		@publicmethod
		def getparents(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctx=None, txn=None):
			"""see: getchildren"""
			return self.__getrel_wrapper(key=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", filt=filt, tree=tree, ctx=ctx, txn=txn)





		# wraps getrel / works as both getchildren/getparents
		@publicmethod
		def __getrel_wrapper(self, key, keytype="record", recurse=0, rectype=None, rel="children", filt=0, tree=0, ctx=None, txn=None):
			#print "getchildren: %s, recurse=%s, rectype=%s, filter=%s, tree=%s"%(key,recurse,rectype,filter,tree)
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
				if x >= self.maxrecurse-1:
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






		@publicmethod
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




		@publicmethod
		def pclinks(self, links, keytype="record", ctx=None, txn=None):
			return self.__link("pclink", links, keytype=keytype, ctx=ctx, txn=txn)


		@publicmethod
		def pcunlinks(self, links, keytype="record", ctx=None, txn=None):
			return self.__link("pcunlink", links, keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@publicmethod
		def pclink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			"""Establish a parent-child relationship between two keys.
			A context is required for record links, and the user must
			have write permission on at least one of the two."""
			return self.__link("pclink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@publicmethod
		def pcunlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			"""Remove a parent-child relationship between two keys. Returns none if link doesn't exist."""
			return self.__link("pcunlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)


		#@txn
		@publicmethod
		def link(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			return self.__link("link", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)

		#@txn
		@publicmethod
		def unlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
			return self.__link("unlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



		def __link(self, mode, links, keytype="record", ctx=None, txn=None):

			if keytype not in ["record", "recorddef", "paramdef"]:
				raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

			if mode not in ["pclink","pcunlink","link","unlink"]:
				raise Exception, "Invalid relationship mode %s"%mode

			if not ctx.checkcreate():
				raise SecurityError, "linking mode %s requires record creation priveleges"%mode

			if filter(lambda x:x[0] == x[1], links):
				#self.LOG("LOG_ERROR","Cannot link to self: keytype %s, key %s <-> %s"%(keytype, pkey, ckey), ctx=ctx, txn=txn)
				return

			if not links:
				return

			items = set(reduce(operator.concat, links))

			# ian: circular reference detection.
			#if mode=="pclink" and not self.__importmode:
			#	p = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="parents")[0]
			#	c = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="children")[0]
			#	if pkey in c or ckey in p or pkey == ckey:
			#		raise Exception, "Circular references are not allowed: parent %s, child %s"%(pkey,ckey)


			if keytype == "record":
				recs = dict([ (x.recid,x) for x in self.getrecord(items, ctx=ctx, txn=txn) ])
				for a,b in links:
					if not (recs[a].writable() or recs[b].writable()):
						raise SecurityError, "pclink requires partial write permission: %s <-> %s"%(a,b)

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
				g.debug("LOG_COMMIT","Commit: link: keytype %s, mode %s, pkey %s, ckey %s"%(keytype, mode, pkey, ckey), ctx=ctx, txn=txn)

			#@end




		###############################
		# section: user management
		###############################



		#@txn
		@publicmethod
		def disableuser(self, username, ctx=None, txn=None):
			"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
			a complete historical record is maintained. Only an administrator can do this."""
			return self.__setuserstate(username, 1, ctx=ctx, txn=txn)



		#@txn
		@publicmethod
		def enableuser(self, username, ctx=None, txn=None):
			return self.__setuserstate(username, 0, ctx=ctx, txn=txn)



		def __setuserstate(self, username, state, ctx=None, txn=None):
			"""Set user enabled/disabled. 0 is enabled. 1 is disabled."""

			state = int(state)

			if state not in [0,1]:
				raise Exception, "Invalid state. Must be 0 or 1."

			if not ctx.checkadmin():
					raise SecurityError, "Only administrators can disable users"

			ol = 0
			if not hasattr(username, "__iter__"):
				ol = 1
				username = [username]

			commitusers = []
			for i in username:
				if i == ctx.username:
					continue
					# raise SecurityError, "Even administrators cannot disable themselves"
				user = self.__users.sget(i, txn=txn) #[i]
				if user.disabled == state:
					continue

				user.disabled = int(state)
				commitusers.append(i)


			ret = self.__commit_users(commitusers, ctx=ctx, txn=txn)
			self.LOG(0, "Users %s disabled by %s"%([user.username for user in ret], ctx.username), ctx=ctx, txn=txn)

			if len(ret)==1 and ol: return ret[0].username
			return [user.username for user in ret]

		@publicmethod
		@adminmethod
		def getsecret(self, username, ctx=None, txn=None):
			return self.__newuserqueue.get(username, txn=txn).get_secret()


		#@txn
		@publicmethod
		@emen2.util.utils.return_list_or_single(1)
		def approveuser(self, usernames, secret=None, ctx=None, txn=None):
			"""approveuser -- Approve an account either because an administrator has reviewed the application, or the user has an authorization secret
			
			adduser creates a secret, should work hear
			"""

			try:
				admin = ctx.checkadmin()
				g.debug('admin is : %r, secret is : %r, secret == None is : %r, not admin is : %r' % (admin, secret, secret == None, not admin))
				if (secret == None) and (not admin):
					raise SecurityError, "Only administrators or users with self-authorization codes can approve new users"

			except SecurityError:
				raise

			except BaseException, e:
				admin = False
				if secret is None: raise
				else:
					g.debug.msg('LOG_DEBUG', 'Ignored: (%s)' % e)


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
					self.LOG("LOG_ERROR","User %s already exists, deleted pending record" % username, ctx=ctx, txn=txn)


				# ian: create record for user.
				user = self.__newuserqueue.sget(username, txn=txn) #[username]
				user.validate()

				if secret is not None and not user.validate_secret(secret):
					self.LOG("LOG_ERROR","Incorrect secret for user %s; skipping"%username, ctx=ctx, txn=txn)
					time.sleep(2)


				else:
					if user.record == None:
						tmpctx = ctx
						if ctx.username == None:
							tmpctx = self.__makecontext(username=username, host=ctx.host)
							self.__init_context(tmpctx, user, txn=txn)

						rec = self.newrecord("person", init=1, ctx=tmpctx, txn=txn)
						rec["username"] = username
						name = user.signupinfo.get('name', ['', '', ''])
						rec["name_first"], rec["name_middle"], rec["name_last"] = name[0], ' '.join(name[1:-1]) or None, name[1]
						rec["email"] = user.signupinfo.get('email')
						rec.adduser(3,username)

						for k,v in user.signupinfo.items():
							rec[k]=v

						g.debug('rec == %r'%rec)
						rec = self.__putrecord([rec], ctx=tmpctx, txn=txn)[0]

						children = user.create_childrecords(ctx=tmpctx, txn=txn)
						children = self.__putrecord(children, ctx=tmpctx, txn=txn)
						g.debug('children:- %r' % (children,))
						if children != []:
							self.__link('pclink', [(rec.recid, child.recid) for child in children], ctx=tmpctx, txn=txn)
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

		@publicmethod
		@adminmethod
		def getpendinguser(self, username, ctx=None, txn=None):
			return self.__newuserqueue.get(username, txn=txn)



		#@txn
		@publicmethod
		def rejectuser(self, usernames, ctx=None, txn=None):
			"""Remove a user from the pending new user queue - only an administrator can do this"""


			if not ctx.checkadmin():
				raise SecurityError, "Only administrators can approve new users"

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



		@publicmethod
		def getuserqueue(self, ctx=None, txn=None):
			"""Returns a list of names of unapproved users"""

			if not ctx.checkadmin():
				raise SecurityError, "Only administrators can approve new users"

			return self.__newuserqueue.keys(txn=txn)



		@publicmethod
		def getqueueduser(self, username, ctx=None, txn=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			if not ctx.checkreadadmin():
				raise SecurityError, "Only administrators can access pending users"

			if hasattr(username,"__iter__"):
				ret={}
				for i in username:
					ret[i] = self.getqueueduser(i, ctx=ctx, txn=txn)
				return ret

			return self.__newuserqueue.sget(username, txn=txn) # [username]


		#@txn
		@publicmethod
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
		@publicmethod
		def setpassword(self, username, oldpassword, newpassword, ctx=None, txn=None):

			user = self.getuser(username, ctx=ctx, txn=txn)

			s = hashlib.sha1(oldpassword)

			if s.hexdigest() != user.password and not ctx.checkadmin():
				time.sleep(2)
				raise SecurityError, "Original password incorrect"

			# we disallow bad passwords here, right now we just make sure that it
			# is at least 6 characters long

			if len(newpassword) < 6:
				raise SecurityError, "Passwords must be at least 6 characters long"

			t = hashlib.sha1(newpassword)
			user.password = t.hexdigest()

			self.__commit_users([user], ctx=ctx, txn=txn)

			return 1






		##########################
		# section: group
		##########################


		@publicmethod
		def getgroupnames(self, ctx=None, txn=None):
			return set(self.__groups.keys(txn=txn))



		@publicmethod
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
						self.LOG("LOG_COMMIT","Commit: __groupsbyuser key: %s, addrefs: %s"%(user, groups), ctx=ctx, txn=txn)
						self.__groupsbyuser.addrefs(user, groups, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups), ctx=ctx, txn=txn)
					raise
					
				except ValueError, inst:
					self.LOG("LOG_ERROR", "Could not update __groupsbyuser key: %s, addrefs %s"%(user, groups), ctx=ctx, txn=txn)


			for user,groups in delrefs.items():
				try:
					if groups:
						self.LOG("LOG_COMMIT","Commit: __groupsbyuser key: %s, removerefs: %s"%(user, groups), ctx=ctx, txn=txn)
						self.__groupsbyuser.removerefs(user, groups, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups), ctx=ctx, txn=txn)
					raise

				except ValueError, inst:
					self.LOG("LOG_ERROR", "Could not update __groupsbyuser key: %s, removerefs %s"%(user, groups), ctx=ctx, txn=txn)


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
					#	print "unknown user %s (%s)"%(user, inst)


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
		@publicmethod
		def putgroup(self, groups, ctx=None, txn=None):

			if isinstance(groups, (Group, dict)): # or not hasattr(groups, "__iter__"):
				groups = [groups]

			groups2 = []
			groups2.extend(filter(lambda x:isinstance(x, Group), groups))
			groups2.extend(map(lambda x:Group(x), filter(lambda x:isinstance(x, dict), groups)))

			allusernames = self.getusernames(ctx=ctx, txn=txn)

			for group in groups2:
				group.validate()
				if group.members() - allusernames:
					raise Exception, "Invalid user names: %s"%(group.members() - allusernames)


			self.__commit_groups(groups2, ctx=ctx, txn=txn)




		def __commit_groups(self, groups, ctx=None, txn=None):

			addrefs, delrefs = self.__reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

			#@begin

			for group in groups:
				g.debug(group)
				g.debug(txn)
				self.__groups.set(group.name, group, txn=txn)

			self.__commit_groupsbyuser(addrefs=addrefs, delrefs=delrefs, ctx=ctx, txn=txn)

			#@end



		# merge with getuser?
		@publicmethod
		def getgroupdisplayname(self, groupname, ctx=None, txn=None):
			ol = 0
			if not hasattr(groupname,"__iter__"):
				groupname = [groupname]
				ol = 1

			groups = self.getgroup(groupname, ctx=ctx, txn=txn)
			print "got groups %s"%groups

			ret = {}

			for i in groups.values():
				ret[i.name]="Test: %s"%i.name

			if ol and len(ret)==1: return ret.values()[0]
			return ret



		###############################
		# users
		###############################


		#@txn
		@publicmethod
		def adduser(self, inuser, ctx=None, txn=None):
			"""adds a new user record. However, note that this only adds the record to the
			new user queue, which must be processed by an administrator before the record
			becomes active. This system prevents problems with securely assigning passwords
			and errors with data entry. Anyone can create one of these"""
			secret = hashlib.sha1(str(id(inuser)) + str(time.time()) + file('/dev/urandom').read(5))
			try:
				user = User(inuser, secret=secret.hexdigest())
			except:
				raise ValueError, "User instance or dict required"

			if user.username == None or len(user.username) < 3:
				if self.__importmode: pass
				else:
					raise KeyError, "Attempt to add user with invalid name"

			#if user.username in self.__users:
			if self.__users.get(user.username, txn=txn):
				if self.__importmode: pass
				else:
					raise KeyError, "User with username %s already exists" % user.username


			#if user.username in self.__newuserqueue:
			if self.__newuserqueue.get(user.username, txn=txn):
				raise KeyError, "User with username %s already pending approval" % user.username


			# 40 = lenght of hex digest
			# we disallow bad passwords here, right now we just make sure that it
			# is at least 6 characters long
			if len(user.password) < 6:
					raise SecurityError, "Passwords must be at least 6 characters long"

			s = hashlib.sha1(user.password)
			user.password = s.hexdigest()

			if not self.__importmode:
				user.creationtime = self.gettime(ctx=ctx, txn=txn)
				user.modifytime = self.gettime(ctx=ctx, txn=txn)

			assert hasattr(user, '_User__secret')
			user.validate()

			self.__commit_newusers({user.username:user}, ctx=None, txn=txn)

			return inuser



		@publicmethod
		def putuser(self, user, validate=True, ctx=None, txn=None):

			if not isinstance(user, User):
				try:
					user = User(user)
				except:
					raise ValueError, "User instance or dict required"

			if not ctx.checkadmin():
				raise SecurityError, "Only administrators may add/modify users with this method"


			if validate:
				user.validate()

			self.__commit_users([user], ctx=ctx, txn=txn)
			#try:
			#	user = self.getuser(user.username, filt=0)
			#except:
			#	pass



		#@write #self.__users
		def __commit_users(self, users, ctx=None, txn=None):
			"""Updates user. Takes User object (w/ validation.) Deprecated for non-administrators."""

			commitusers = []

			for user in users:

				if not isinstance(user, User):
					try:
						user = User(user)
					except:
						raise ValueError, "User instance or dict required"

				try:
					ouser = self.__users.sget(user.username, txn=txn) #[user.username]
				except:
					ouser = user
					#raise KeyError, "Putuser may only be used to update existing users"


				#if user.creator != ouser.creator or user.creationtime != ouser.creationtime:
				#	raise SecurityError, "Creation information may not be changed"

				# user.validate()

				commitusers.append(user)

			#@begin

			for user in commitusers:
				self.__users.set(user.username, user, txn=txn)
				self.LOG("LOG_COMMIT","Commit: self.__users.set: %s"%user.username, ctx=ctx, txn=txn)

			#@end

			return commitusers


		#@write #self.__newuserqueue
		def __commit_newusers(self, users, ctx=None, txn=None):
			"""write to newuserqueue; users is dict; set value to None to del"""

			#@begin

			for username, user in users.items():
				self.__newuserqueue.set(username, user, txn=txn)
				self.LOG("LOG_COMMIT","Commit: self.__newuserqueue.set: %s"%username, ctx=ctx, txn=txn)

			#@end



		@publicmethod
		def getuser(self, usernames, filt=True, lnf=False, ctx=None, txn=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			ol=0
			if not hasattr(usernames,"__iter__"):
				ol=1
				usernames = [usernames]

			#ret = self.__getuser(usernames, filt=filt, lnf=lnf, ctx=ctx, txn=txn)
			#def __getuser(self, usernames, filt=True, lnf=False, ctx=None, txn=None):

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
					user2 = User()
					user2.username = user.username
					user = user2

				# Anonymous users cannot use this to extract email addresses
				#if ctx.username == None:
				#	user.groups = None


				try:
					if user.record:
						user._userrec = self.getrecord(user.record, filt=0, ctx=ctx, txn=txn)
					else:
						raise Exception
				except:
					user._userrec = {}

				user.displayname = self.__formatusername(user.username, user._userrec, lnf=lnf, ctx=ctx, txn=txn)

				# print "setting email: %s -> %s"%(user.get("email"), user.userrec.get("email"))
				user.email = user._userrec.get("email")

				ret[i] = user



			if len(ret)==1 and ol:
				return ret[ret.keys()[0]]
			return ret





		@publicmethod
		def getuserdisplayname(self, username, lnf=1, perms=0, filt=True, ctx=None, txn=None):
			"""Return the full name of a user from the user record; include permissions param if perms=1"""

			namestoget = []
			ret = {}

			ol = 0
			if isinstance(username, basestring):
				ol = 1
			if isinstance(username, (basestring, int, Record)):
				username=[username]

			namestoget=[]
			namestoget.extend(filter(lambda x:isinstance(x,basestring),username))

			vts=["user","userlist"]
			if perms:
				vts.append("acl")

			recs = []
			recs.extend(filter(lambda x:isinstance(x,Record), username))
			recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), username), filt=filt, ctx=ctx, txn=txn))

			if recs:
				namestoget.extend(self.filtervartype(recs, vts, flat=1, ctx=ctx, txn=txn))
				# ... need to parse comments since it's special
				namestoget.extend(reduce(lambda x,y: x+y, [[i[0] for i in rec["comments"]] for rec in recs]))

			namestoget=set(namestoget)

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




		@publicmethod
		def getusernames(self, ctx=None, txn=None):
			"""Not clear if this is a security risk, but anyone can get a list of usernames
					This is likely needed for inter-database communications"""

			if ctx.username == None:
				return
			return self.__users.keys(txn=txn)




		@publicmethod
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



		@publicmethod
		def getworkflow(self, ctx=None, txn=None):
			"""This will return an (ordered) list of workflow objects for the given context (user).
			it is an exceptionally bad idea to change a WorkFlow object's wfid."""

			if ctx.username == None:
				raise SecurityError, "Anonymous users have no workflow"

			try:
				return self.__workflow.sget(ctx.username, txn=txn) #[ctx.username]
			except:
				return []



		@publicmethod
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



		@publicmethod
		def newworkflow(self, vals, ctx=None, txn=None):
			"""Return an initialized workflow instance."""
			return WorkFlow(vals)



		#@txn
		#@write #self.__workflow
		@publicmethod
		def addworkflowitem(self, work, ctx=None, txn=None):
			"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""

			if ctx.username == None:
				raise SecurityError, "Anonymous users have no workflow"

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
		@publicmethod
		def delworkflowitem(self, wfid, ctx=None, txn=None):
			"""This will remove a single workflow object based on wfid"""
			#self = db

			if ctx.username == None:
				raise SecurityError, "Anonymous users have no workflow"

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
		@publicmethod
		def setworkflow(self, wflist, ctx=None, txn=None):
			"""This allows an authorized user to directly modify or clear his/her workflow. Note that
			the external application should NEVER modify the wfid of the individual WorkFlow records.
			Any wfid's that are None will be assigned new values in this call."""
			#self = db

			if ctx.username == None:
				raise SecurityError, "Anonymous users have no workflow"

			if wflist == None:
				wflist = []
			wflist = list(wflist)								 # this will (properly) raise an exception if wflist cannot be converted to a list

			for w in wflist:
				if not self.__importmode:
					#w=WorkFlow(w.__dict__.copy())
					w.validate()

				if not isinstance(w, WorkFlow):
					txn.abort()
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


		@publicmethod
		def getvartypenames(self, ctx=None, txn=None):
			"""This returns a list of all valid variable types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getvartypes()



		@publicmethod
		def getvartype(self, name, ctx=None, txn=None):
			"""This returns a list of all valid variable types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getvartype(name)
			#return valid_vartypes[thekey][1]



		@publicmethod
		def getpropertynames(self, ctx=None, txn=None):
			"""This returns a list of all valid property types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getproperties()



		@publicmethod
		def getpropertyunits(self, propname, ctx=None, txn=None):
			"""Returns a list of known units for a particular property"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			# set(vtm.getproperty(propname).units) | set(vtm.getproperty(propname).equiv)
			return set(vtm.getproperty(propname).units)



		#@txn
		# ian: renamed addparamdef -> putparamdef for consistency
		@publicmethod
		def putparamdef(self, paramdef, parents=None, children=None, ctx=None, txn=None):
			"""adds a new ParamDef object, group 0 permission is required
			a p->c relationship will be added if parent is specified"""

			if not isinstance(paramdef, ParamDef):
				try:
					paramdef = ParamDef(paramdef)
				except ValueError, inst:
					raise ValueError, "ParamDef instance or dict required"


			if not ctx.checkcreate():
				raise SecurityError, "No permission to create new paramdefs (need record creation permission)"

			paramdef.name = unicode(paramdef.name).lower()

			try:
				pd = self.__paramdefs.sget(paramdef.name, txn=txn) #[paramdef.name]
				# Root is permitted to force changes in parameters, though they are supposed to be static
				# This permits correcting typos, etc., but should not be used routinely
				# skip relinking if we're editing
				if not ctx.checkadmin():
					raise KeyError, "Only administrators can modify paramdefs: %s"%paramdef.name

				if pd.vartype != paramdef.vartype:
					self.LOG("LOG_INFO","WARNING! Changing paramdef %s vartype from %s to %s. This will REQUIRE database export/import and revalidation!!"%(paramdef.name, pd.vartype, paramdef.vartype), ctx=ctx, txn=txn)

			except:
				paramdef.creator = ctx.username
				paramdef.creationtime = self.gettime(ctx=ctx, txn=txn)


			# if not self.__importmode:
			# 	paramdef.validate()

			# this actually stores in the database

			self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)

			links = []
			if parents: links.append( map(lambda x:(x, paramdef.name), parents) )
			if children: links.append( map(lambda x:(paramdef.name, x), children) )
			if links:
				self.pclinks(links, keytype="paramdef", ctx=ctx, txn=txn)





		#@txn
		@publicmethod
		def addparamchoice(self, paramdefname, choice, ctx=None, txn=None):
			"""This will add a new choice to records of vartype=string. This is
			the only modification permitted to a ParamDef record after creation"""

			paramdefname = unicode(paramdefname).lower()

			# ian: change to only allow logged in users to add param choices. silent return on failure.
			if not ctx.checkcreate():
				return

			d = self.__paramdefs.sget(paramdefname, txn=txn)  #[paramdefname]
			if d.vartype != "string":
				raise SecurityError, "choices may only be modified for 'string' parameters"

			d.choices = d.choices + (unicode(choice).title(),)

			self.__commit_paramdefs([d], ctx=ctx, txn=txn)



		#ian: todo
		#@write #self.__paramdefs
		def __commit_paramdefs(self, paramdefs, ctx=None, txn=None):

			for i in paramdefs:
				i.validate()

			#@begin

			for paramdef in paramdefs:
				self.__paramdefs.set(paramdef.name, paramdef, txn=txn)
				self.LOG("LOG_COMMIT","Commit: self.__paramdefs.set: %s"%paramdef.name, ctx=ctx, txn=txn)

			#@end



		# # ian: remove this method
		# def findparamdefname(self, name):
		# 	"""Find a paramdef similar to the passed 'name'. Returns the actual ParamDef, or None if no match is found."""
		# 	name = str(name).lower()
		# 	if self.__paramdefs.has_key(name):
		# 		return name
		# 	if name[-1] == "s":
		# 		if self.__paramdefs.has_key(name[:-1]):
		# 			return name[:-1]
		# 		if name[ - 2] == "e" and self.__paramdefs.has_key(name[:-2]):
		# 			return name[: - 2]
		# 	if name[-3:] == "ing" and self.__paramdefs.has_key(name[:-3]):
		# 		return name[: - 3]
		# 	return None



		@publicmethod
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

			if isinstance(recs[0], Record):
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
						print "WARNING: Invalid param: %s"%i
						pass
					else:
						raise Exception, "Invalid param: %s"%i

			return paramdefs




		# ian todo: combine this and getparamdefs; alot of older places use this version
		@publicmethod
		def getparamdef(self, key, ctx=None, txn=None):
			"""gets an existing ParamDef object, anyone can get any field definition"""
			try:
				return self.__paramdefs.sget(key, txn=txn) #[key]
			except:
				raise KeyError, "Unknown ParamDef: %s" % key



		@publicmethod
		def getparamdefnames(self, ctx=None, txn=None):
			"""Returns a list of all ParamDef names"""
			return self.__paramdefs.keys(txn=txn)



		def __getparamindex(self, paramname, create=True, ctx=None, txn=None):
			"""Internal function to open the parameter indices at need.
			Later this may implement some sort of caching mechanism.
			If create is not set and index doesn't exist, raises
			KeyError. Returns "link" or "child" for this type of indexing"""



			try:
				return self.__fieldindex.sget(paramname, txn=txn) # [paramname]				# Try to get the index for this key
			except Exception, inst:
				pass


			#paramname = self.__paramdefs.typekey(paramname)
			f = self.__paramdefs.sget(paramname, txn=txn) #[paramname]				 # Look up the definition of this field
			paramname = f.name

			if f.vartype not in self.indexablevartypes:
				#print "\tunindexable vartype ",f.vartype
				return None

			tp = self.vtm.getvartype(f.vartype).getindextype()

			if not create and not os.access("%s/index/%s.bdb" % (self.path, paramname), os.F_OK):
				raise KeyError, "No index for %s" % paramname

			# create/open index
			self.__fieldindex[paramname] = FieldBTree(paramname, keytype=tp, indexkeys=self.__indexkeys, filename="%s/index/%s.bdb"%(self.path, paramname), dbenv=self.__dbenv, txn=txn)

			return self.__fieldindex[paramname]




		#########################
		# section: recorddefs
		#########################



		# #@txn
		# @publicmethod
		# def addrecorddef(self, recdef, parent=None, ctx=ctx, txn=None):
		# 	"""adds a new RecordDef object. The user must be an administrator or a member of group 0"""
		#
		# 	if not isinstance(recdef, RecordDef):
		# 		try:
		# 			recdef = RecordDef(recdef)
		# 		except:
		# 			raise ValueError, "RecordDef instance or dict required"
		#
		# 	ctx = self.__getcontext()
		#
		# 	recdef.validate()
		#
		# 	if not ctx.checkcreate():
		# 		raise SecurityError, "No permission to create new RecordDefs"
		#
		# 	if self.__recorddefs.has_key(str(recdef.name).lower()):
		# 		raise KeyError, "RecordDef %s already exists" % str(recdef.name).lower()
		#
		# 	recdef.findparams()
		# 	pdn = self.getparamdefnames()
		# 	for i in recdef.params:
		# 		if i not in pdn:
		# 			raise KeyError, "No such parameter %s" % i
		#
		#
		# 	# force these values
		# 	if (recdef.owner == None) : recdef.owner = ctx.user
		# 	recdef.name = str(recdef.name).lower()
		# 	recdef.creator = ctx.user
		# 	recdef.creationtime = self.gettime()
		#
		#
		# 	if not self.__importmode:
		# 		recdef=RecordDef(recdef.__dict__.copy())
		# 		recdef.validate()
		#
		# 	# commit
		# 	txn = self.txncheck(txn)
		# 	self.__commit_recorddefs([recdef], ctx=ctx, txn=txn)
		#
		# 	if parent:
		# 		self.pclink(parent, recdef.name, "recorddef", txn=txn)
		#
		# 	self.txncommit(txn)
		#
		# 	return recdef.name


		#@txn
		@publicmethod
		def putrecorddef(self, recdef, parents=None, children=None, ctx=None, txn=None):
			"""Add or update RecordDef. The mainview should
			never be changed once used, since this will change the meaning of
			data already in the database, but sometimes changes of appearance
			are necessary, so this method is available."""
			#self = db

			if not isinstance(recdef, RecordDef):
				try:
					recdef = RecordDef(recdef)
				except:
					raise ValueError, "RecordDef instance or dict required"

			recdef.validate()

			if not ctx.checkcreate():
				raise SecurityError, "No permission to create new RecordDefs"


			try:
				rd = self.__recorddefs.sget(recdef.name, txn=txn) #[recdef.name]
			except:
				rd = RecordDef(recdef, ctx=ctx)
				#raise Exception, "No such recorddef %s"%recdef.name

			if ctx.username != rd.owner and not ctx.checkadmin():
				raise SecurityError, "Only the owner or administrator can modify RecordDefs"

			if recdef.mainview != rd.mainview and not ctx.checkadmin():
				raise SecurityError, "Only the administrator can modify the mainview of a RecordDef"


			recdef.findparams()
			invalidparams = set(recdef.params) - set(self.getparamdefnames(ctx=ctx, txn=txn))
			if invalidparams:
				raise KeyError, "Invalid parameters: %s"%invalidparams

			# reset
			recdef.creator = rd.creator
			recdef.creationtime = rd.creationtime


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
				self.LOG("LOG_COMMIT","Commit: self.__recorddefs.set: %s"%recorddef.name, ctx=ctx, txn=txn)

			#@end




		@publicmethod
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
			if (ret.private and (ret.owner == ctx.username or ret.owner in ctx.groups or ctx.checkreadadmin())):
				return ret

			# ian todo: make sure all calls to getrecorddef pass recid they are requesting

			# ok, now we need to do a little more work.
			if recid == None:
				raise SecurityError, "User doesn't have permission to access private RecordDef '%s'" % rectypename

			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			# try to get the record, may (and should sometimes) raise an exception

			if rec.rectype != rectypename:
				raise SecurityError, "Record %d doesn't belong to RecordDef %s" % (recid, rectypename)

			# success, the user has permission
			return ret



		@publicmethod
		def getrecorddefnames(self, ctx=None, txn=None):
			"""This will retrieve a list of all existing RecordDef names,
			even those the user cannot access the contents of"""
			return self.__recorddefs.keys(txn=txn)



		@publicmethod
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
		@publicmethod
		def getrecord(self, recids, filt=True, ctx=None, txn=None):
			"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
			if dbid is 0, the current database is used."""


			#if (dbid != 0):
			#	raise NotImplementedError("External database support not yet available")
			#	#Ed Changed to NotimplementedError

			ol=0
			if not hasattr(recids,"__iter__"):
				ol=1
				recids=[recids]

			#print "-> recids"
			#print recids
			#recids = map(int, recids)

			# if filt: filt = None
			# else: filt = lambda x:x.rectype
			# recs = map(self.__records.get, recid)

			ret=[]
			for i in recids:
				try:
					rec = self.__records.sget(i, txn=txn) # [i]
					rec.setContext(ctx)
					ret.append(rec)
				except SecurityError, e:
					# if filtering, skip record; else bubble (SecurityError) exception
					if filt: pass
					else: raise e
				except (KeyError, TypeError), e:
					if filt: pass
					else: raise KeyError, "No such record %s"%i

			if len(ret)==1 and ol:
				return ret[0]
			return ret


		# does not setContext!!
		def __getrecord(self, recids, filt=True, ctx=None, txn=None):
			pass




		# ian: todo: improve newrecord/putrecord
		# ian: todo: allow to copy existing record
		@publicmethod
		def newrecord(self, rectype, init=0, inheritperms=None, ctx=None, txn=None):
			"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
			already exist)."""


			rec = Record(ctx=ctx)
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
					self.LOG("LOG_ERROR","newrecord: Error setting inherited permissions from record %s (%s)"%(inheritperms, inst), ctx=ctx, txn=txn)


			if ctx.username != "root":
				rec.adduser(3, ctx._user)

			return rec


		# ian: this might be helpful
		# e.g.: __filtervartype(136, ["user","userlist"])
		@publicmethod
		def filtervartype(self, recs, vts, params=None, paramdefs=None, filt=True, flat=0, returndict=0, ignore=None, ctx=None, txn=None):

			if not recs:
				return [None]

			if not paramdefs: paramdefs={}
			recs2 = []

			# process recs arg into recs2 records, process params by vartype, then return either a dict or list of values; ignore those specified
			ol = 0
			if isinstance(recs,(int,Record)):
				ol = 1
				recs=[recs]

			if not hasattr(vts,"__iter__"):
				vts = [vts]

			if not hasattr(ignore,"__iter__"):
				ignore = [ignore]
			ignore = set(ignore)

			recs2.extend(filter(lambda x:isinstance(x,Record),recs))
			recs2.extend(self.getrecord(filter(lambda x:isinstance(x,int),recs), filt=filt, ctx=ctx, txn=txn))

			if params:
				paramdefs = self.getparamdefs(params, ctx=ctx, txn=txn)

			if not paramdefs:
				pds = set(reduce(lambda x,y:x+y,map(lambda x:x.keys(),recs2)))
				paramdefs.update(self.getparamdefs(pds, ctx=ctx, txn=txn))

			l = set([pd.name for pd in paramdefs.values() if pd.vartype in vts]) - ignore
			#l = set(map(lambda x:x.name, filter(lambda x:x.vartype in vts, paramdefs.values()))) - ignore
			##l = set(filter(lambda x:x.vartype in vts, paramdefs.values())) - ignore

			if returndict or ol:
				ret = {}
				for rec in recs2:
					re = [rec.get(pd) or None for pd in l]
					if flat:
						re = set(self.__flatten(re))-set([None])
					ret[rec.recid]=re

				if ol: return ret.values()[0]
				return ret

			# if not returndict
			re = [[rec.get(pd) for pd in l if rec.get(pd)] for rec in recs2]
			#re=filter(lambda x:x,map(lambda x:[x.get(pd) or None for pd in l],a))
			if flat:
				return set(self.__flatten(re))-set([None])
			return re









		#@txn
		@publicmethod
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
		@publicmethod
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
		@publicmethod
		def putrecordvalue(self, recid, param, value, ctx=None, txn=None):
			"""Make a single change to a single record"""
			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			rec[param] = value
			self.putrecord(rec, ctx=ctx, txn=txn)
			return self.getrecord(recid, ctx=ctx, txn=txn)[param]



		#@txn
		@publicmethod
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
		@publicmethod
		def putrecordsvalues(self, d, ctx=None, txn=None):
			"""Make multiple changes to multiple records"""

			ret = {}
			for k, v in d.items():
				ret[k] = self.putrecordvalues(k, v, ctx=ctx, txn=txn)
			return ret



		#@txn
		@publicmethod
		def putrecord(self, recs, filt=True, warning=0, log=True, importmode=True, ctx=None, txn=None):
			"""commits a record"""
			# input validation for __putrecord

			if not ctx.checkadmin():
				if warning:
					raise SecurityError, "Only administrators may bypass record validation"
				if not log:
					raise SecurityError, "Only administrators may bypass logging"
				if not importmode:
					raise SecurityError, "Only administrators may use importmode"


			# filter input for dicts/records
			ol = 0
			if isinstance(recs,(Record,dict)):
				ol = 1
				recs = [recs]


			dictrecs = filter(lambda x:isinstance(x,dict), recs)
			recs.extend(map(lambda x:Record(x, ctx=ctx), dictrecs))
			recs = filter(lambda x:isinstance(x,Record), recs)

			# new records and updated records
			updrecs = filter(lambda x:x.recid >= 0, recs)
			newrecs = filter(lambda x:x.recid < 0, recs)


			# check original records for write permission
			orecs = self.getrecord([rec.recid for rec in updrecs], filt=0, ctx=ctx, txn=txn)
			orecs = set(map(lambda x:x.recid, filter(lambda x:x.commentable(), orecs)))


			permerror = set([rec.recid for rec in updrecs]) - orecs
			if permerror:
				raise SecurityError, "No permission to write to records: %s"%permerror


			if newrecs and not ctx.checkcreate():
				raise SecurityError, "No permission to create records"

			ret = self.__putrecord(recs, warning=warning, importmode=importmode, log=log, ctx=ctx, txn=txn)

			if ol and len(ret) > 0:
				return ret[0]
			return ret






		def __putrecord(self, updrecs, warning=0, validate=True, importmode=0, log=True, ctx=None, txn=None):
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

				t = self.gettime(ctx=ctx, txn=txn)
				recid = updrec.recid

				try:
					# we need to acquire RMW lock here to prevent changes during commit
					orec = self.__records.sget(updrec.recid, txn=txn, flags=db.DB_RMW) # [updrec.recid] #, flags=db.DB_RMW
					orec.setContext(ctx)


				except (KeyError, TypeError), inst:
					orec = self.newrecord(updrec.rectype, ctx=ctx, txn=txn)
					orec.recid = updrec.recid

					if importmode:
						orec._Record__creator = updrec["creator"]
						orec._Record__creationtime = updrec["creationtime"]

					if recid > 0:
						raise Exception, "Cannot update non-existent record %s"%recid


				if validate:
					updrec.validate(warning=warning, txn=txn)

				# compare to original record
				cp = orec.changedparams(updrec) - param_immutable


				# orec.recid < 0 because new records will always be committed, even if skeletal
				if not cp and not orec.recid < 0:
					self.LOG("LOG_INFO","putrecord: No changes for record %s, skipping"%recid, ctx=ctx, txn=txn)
					continue

				#print "%s cp: %s"%(orec.recid, cp)


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

			print "commiting %s recs"%(len(crecs))

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
				baserecid = self.__records.get(-1, flags=db.DB_RMW, txn=txn) or 0
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
				self.LOG("LOG_COMMIT","Commit: self.__records.set: %s"%crec.recid, ctx=ctx, txn=txn)



			# # New record RecordDef indexes

			#txn2 = self.newtxn(parent=txn)

			for rectype,recs in rectypes.items():
				try:
					self.__recorddefindex.addrefs(rectype, recs, txn=txn)
					self.LOG("LOG_COMMIT","Commit: self.__recorddefindex.addrefs: %s, %s"%(rectype,recs), ctx=ctx, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst), ctx=ctx, txn=txn)
					raise

				except ValueError, inst:
					self.LOG("LOG_ERROR", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst), ctx=ctx, txn=txn)
					

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
					#self.LOG("LOG_COMMIT","Commit: self.__timeindex.set: %s, %s"%(recmap.get(recid,recid), time))

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst), ctx=ctx, txn=txn)
					raise
					
				except ValueError, inst:
					self.LOG("LOG_ERROR", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst), ctx=ctx, txn=txn)


			# Create pc links
			for link in updrels:
				try:
					self.pclink( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), ctx=ctx, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst), ctx=ctx, txn=txn)
					raise

				except Exception, inst:
					self.LOG("LOG_ERROR", "Could not link %s to %s (%s)"%( recmap.get(link[0],link[0]), recmap.get(link[1],link[1]), inst), ctx=ctx, txn=txn)


			#if txn2:
			#	self.txncommit(txn2)

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
						self.LOG("LOG_COMMIT","Commit: self.__secrindex.addrefs: %s, len %s"%(user, len(recs)), ctx=ctx, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst), ctx=ctx, txn=txn)
					raise

				except Exception, inst:
					self.LOG("LOG_ERROR", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst), ctx=ctx, txn=txn)

					

			for user, recs in removerefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.__secrindex.removerefs(user, recs, txn=txn)
						self.LOG("LOG_COMMIT","Commit: secrindex.removerefs: user %s, len %s"%(user, len(recs)), ctx=ctx, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst), ctx=ctx, txn=txn)
					raise

				except Exception, inst:
					self.LOG("LOG_ERROR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst), ctx=ctx, txn=txn)
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

			except db.DBError, inst:
				self.LOG("LOG_CRITICAL","Could not open param index: %s (%s)"% (param, inst), ctx=ctx, txn=txn)
				raise

			except Exception, inst:
				self.LOG("LOG_ERROR","Could not open param index: %s (%s)"% (param, inst), ctx=ctx, txn=txn)
				raise




			for newval,recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.LOG("LOG_COMMIT","Commit: param index %s.addrefs: %s '%s', %s"%(param, type(newval), newval, len(recs)), ctx=ctx, txn=txn)
						paramindex.addrefs(newval, recs, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst), ctx=ctx, txn=txn)
					raise

				except Exception, inst:
					self.LOG("LOG_ERROR", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst), ctx=ctx, txn=txn)



			for oldval,recs in delrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.LOG("LOG_COMMIT","Commit: param index %s.removerefs: %s '%s', %s"%(param, type(oldval), oldval, len(recs)), ctx=ctx, txn=txn)
						paramindex.removerefs(oldval, recs, txn=txn)

				except db.DBError, inst:
					self.LOG("LOG_CRITICAL", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst), ctx=ctx, txn=txn)
					raise

				except Exception, inst:
					self.LOG("LOG_ERROR", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst), ctx=ctx, txn=txn)




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

				#self.LOG("LOG_INFO","__reindex_security: record %s, add %s, delete %s"%(updrec.recid, nperms - operms, operms - nperms))

				for user in nperms - operms:
					addrefs[user].append(recid)
				for user in operms - nperms:
					delrefs[user].append(recid)

			return addrefs, delrefs






		###############################
		# section: permissions
		###############################




		# ian: todo: benchmark these again
		@publicmethod
		def filterbypermissions(self, recids, ctx=None, txn=None):

			
			if ctx.checkreadadmin():
				return set(recids)

			recids = set(recids)

			# this is usually the fastest
			# method 2
			#ret=set()

			ret = []

			if ctx.username != None:
				ret.extend(recids & set(self.__secrindex.sget(ctx.username, txn=txn)))

			#ret |= recids & set(self.__secrindex[ctx.user])
			#recids -= ret

			for group in sorted(ctx.groups, reverse=True):
				#if recids:
				#print "searching group %s"%group
				#ret |= recids & set(self.__secrindex[group])
				#recids -= ret
				ret.extend(recids & set(self.__secrindex.sget(group, txn=txn)))

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



		@publicmethod
		def secrecordadduser2(self, recids, level, users, reassign=0, ctx=None, txn=None):

				if not hasattr(recids,"__iter__"):
					recids = [recids]
				recids = set(recids)

				if not hasattr(users,"__iter__"):
					users = [users]
				users = set(users)

				checkitems = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)
				if users - checkitems:
					raise SecurityError, "Invalid users/groups: %s"%(users-checkitems)

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
		@publicmethod
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
							try:
								usertuple[i][j] = int(usertuple[i][j])
							except ValueError:
								usertuple[i][j] = unicode(usertuple[i][j])
							except:
								raise ValueError, "Invalid permissions format; must be 4-tuple/list of tuple/list/string/int"


				# all users
				userset = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, tcxn=txn)


				# get a list of records we need to update
				if recurse > 0:
						trgt = self.getchildren(recid, recurse=recurse-1, ctx=ctx, txn=txn)
						trgt.add(recid)
				else:
					trgt = set((recid,))


				if ctx.checkadmin():
						isroot = 1
				else:
						isroot = 0


				rec=self.getrecord(recid, ctx=ctx, txn=txn)
				if ctx.username not in rec["permissions"][3] and not isroot:
					raise SecurityError,"Insufficient permissions for record %s"%recid

				# this will be a dictionary keyed by user of all records the user has
				# just gained access to. Used for fast index updating
				secrupd = {}

				#print trgt
				#recs = self.getrecord(trgt, ctx=ctx, txn=txn)

				for i in trgt:
						#try:
						rec = self.getrecord(i, ctx=ctx, txn=txn)						 # get the record to modify
						#except:
						#		 print "skipping %s"%i
						#		 continue

						# if the context does not have administrative permission on the record
						# then we just skip this record and leave the permissions alone
						# TODO: probably we should also check for groups in [3]

						if ctx.username not in rec["permissions"][3] and not ctx.checkadmin(): continue

						#print "rec: %s" % i

						cur = [set(v) for v in rec["permissions"]]				# make a list of sets out of the current permissions
						xcur = [set(v) for v in rec["permissions"]]				 # copy of cur that will be changed
						# l=[len(v) for v in cur]
						#length test not sufficient # length of each tuple so we can decide if we need to commit changes
						newv = [set(v) for v in usertuple]								# similar list of sets for the new users to add

						# check for valid user names
						newv[0] &= userset
						newv[1] &= userset
						newv[2] &= userset
						newv[3] &= userset

						# if we allow level change, remove all changed users then add back..
						if reassign:
							#print "reassign"
							allnew = newv[0] | newv[1] | newv[2] | newv[3]
							#print allnew
							xcur[0] -= allnew
							xcur[1] -= allnew
							xcur[2] -= allnew
							xcur[3] -= allnew
							#print xcur

						# update the permissions for each group
						xcur[0] |= newv[0]
						xcur[1] |= newv[1]
						xcur[2] |= newv[2]
						xcur[3] |= newv[3]
						#print "updated"
						#print xcur
						# if the user already has more permission than we are trying
						# to assign, we don't do anything. This also cleans things up
						# so a user cannot have more than one security level
						# -- assign higher permissions or lower permissions
						xcur[0] -= xcur[1]
						xcur[0] -= xcur[2]
						xcur[0] -= xcur[3]
						xcur[1] -= xcur[2]
						xcur[1] -= xcur[3]
						xcur[2] -= xcur[3]
						#print "pruned"
						#print xcur

#						 l2=[len(v) for v in cur]	 # length test not sufficient

						# update if necessary
#						 if l!=l2 :
						if xcur[0] != cur[0] or xcur[1] != cur[1] \
							 or xcur[2] != cur[2] or xcur[3] != cur[3]:
								old = rec["permissions"]
								rec["permissions"] = (tuple(xcur[0]), tuple(xcur[1]), tuple(xcur[2]), tuple(xcur[3]))
								#print "new permissions:"
								#print (tuple(xcur[0]), tuple(xcur[1]), tuple(xcur[2]), tuple(xcur[3]))
								#print rec["permissions"]
# SHOULD do it this way, but too slow
#								 rec.commit()

								# commit is slow because of the extensive checks for changes
								# in this case we know only the security changed. We also don't
								# update the modification time. In fact, we build up a list of changes
								# then do it all at once.
#								 self.__reindexsec(reduce(operator.concat,old),
#										 reduce(operator.concat,rec["permissions"]),rec.recid)

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
		@publicmethod
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
						#if DEBUG: print "Del user recursive..."
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

# SHOULD do it this way, but too slow
#								 rec.commit()

								# commit is slow because of the extensive checks for changes
								# in this case we know only the security changed. We also don't
								# update the modification time
#								 print reduce(operator.concat,old)
#								 print reduce(operator.concat,rec["permissions"])
#								 self.__reindexsec(reduce(operator.concat,old),
#										 reduce(operator.concat,rec["permissions"]),rec.recid)

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
		@publicmethod
		def getrecordrecname(self, rec, returnsorted=0, showrectype=0, ctx=None, txn=None):
			"""Render the recname view for a record."""

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




		@publicmethod
		def getrecordrenderedviews(self, recid, ctx=None, txn=None):
			"""Render all views for a record."""

			rec = self.getrecord(recid, ctx=ctx, txn=txn)
			recdef = self.getrecorddef(rec["rectype"], ctx=ctx, txn=txn)
			views = recdef.views
			views["mainview"] = recdef.mainview
			for i in views:
				views[i] = self.renderview(rec, viewdef=views[i], ctx=ctx, txn=txn)
			return views





		def __dicttable_view(self, params, paramdefs={}, mode="unicode", ctx=None, txn=None):
			"""generate html table of params"""

			if mode=="html":
				dt = ["<table><tr><td><h6>Key</h6></td><td><h6>Value</h6></td></tr>"]
				for i in params:
					dt.append("<tr><td>$#%s</td><td>$$%s</td></tr>"%(i,i))
				dt.append("</table>")
			else:
				dt = []
				for i in params:
					dt.append("$#%s:\t$$%s\n"%(i,i))
			return "".join(dt)






		@publicmethod
		def renderview(self, recs, viewdef=None, viewtype="dicttable", paramdefs={}, showmacro=True, mode="unicode", outband=0, ctx=None, txn=None):
			"""Render views"""

			# viewtype "dicttable" is builtin now.
			# ian: todo: remove.
			if recs != 0 and not recs:
				return


			ol = 0
			if not hasattr(recs,"__iter__") or isinstance(recs,Record):
				ol = 1
				recs = [recs]


			if not isinstance(list(recs)[0],Record):
				recs = self.getrecord(recs,filt=1, ctx=ctx, txn=txn)


			builtinparams=["recid","rectype","comments","creator","creationtime","permissions"]
			builtinparamsshow=["recid","rectype","comments","creator","creationtime"]

			groupviews={}
			groups=set([rec.rectype for rec in recs])
			recdefs=self.getrecorddef(groups, ctx=ctx, txn=txn)

			if not viewdef:
				for i in groups:
					rd=recdefs.get(i)

					if viewtype=="mainview":
						groupviews[i]=rd.mainview

					elif viewtype=="dicttable":
						# move built in params to end of table
						par=[p for p in rd.paramsK if p not in builtinparams]
						par+=builtinparamsshow
						groupviews[i]=self.__dicttable_view(par, mode=mode, ctx=ctx, txn=txn)

					else:
						groupviews[i]=rd.views.get(viewtype, rd.name)

			else:
				groupviews[None]=viewdef


			if outband:
				for rec in recs:
					obparams=[i for i in rec.keys() if i not in recdefs[rec.rectype].paramsK and i not in builtinparams and rec.get(i) != None]
					if obparams:
						groupviews[rec.recid]=groupviews[rec.rectype] + self.__dicttable_view(obparams, mode=mode, ctx=ctx, txn=txn)
					# switching to record-specific views; no need to parse group views
					#del groupviews[rec.rectype]


			vtm = emen2.Database.subsystems.datatypes.VartypeManager()

			names={}
			values={}
			macros={}
			pd=[]
			for g1,vd in groupviews.items():
				n=[]
				v=[]
				m=[]

				vd = vd.encode('utf-8', "ignore")
				iterator = regex2.finditer(vd)

				for match in iterator:
						if match.group("name"):
								n.append((match.group("name"),match.group("namesep"),match.group("name1")))
								pd.append(match.group("name1"))
						elif match.group("var"):
								v.append((match.group("var"),match.group("varsep"),match.group("var1")))
								pd.append(match.group("var1"))
						#elif match.group("reqvar"):
						#		v.append((match.group("reqvar"),match.group("reqvarsep"),match.group("reqvar1")))
						#		pd.append(match.group("reqvar1"))
						elif match.group("macro"):
								m.append((match.group("macro"),match.group("macrosep"),match.group("macro1"), match.group("macro2")))
				g.debug("macro stuff -> %r" %m)

				paramdefs.update(self.getparamdefs(pd, ctx=ctx, txn=txn))
				#print "PD:%s"%paramdefs.keys()

				# invariant to recid
				if n:
					for i in n:
						vrend = vtm.name_render(paramdefs.get(i[2]), mode=mode, db=self, ctx=ctx, txn=txn)
						vd = vd.replace(u"$#" + i[0] + i[1], vrend + i[1])
					groupviews[g1] = vd

				names[g1] = n
				values[g1] = v
				macros[g1] = m


			ret={}


			for rec in recs:
				if groupviews.get(rec.recid):
					key = rec.recid
				else:
					key = rec.rectype
				if viewdef: key = None
				a = groupviews.get(key)

				for i in values[key]:
					v = vtm.param_render(paramdefs[i[2]], rec.get(i[2]), mode=mode, db=self, ctx=ctx, txn=txn)
					a = a.replace(u"$$" + i[0] + i[1], v + i[1])

				if showmacro:
					for i in macros[key]:
						v=vtm.macro_render(i[2], i[3], rec, mode=mode, db=self, ctx=ctx, txn=txn) #macro, params, rec, mode="unicode", db=None, , ctx=ctx, txn=txn
						a=a.replace(u"$@" + i[0], v + i[1])

				ret[rec.recid]=a

			#g.debug('ol ->', ol)
			if ol:
				return ret.values()[0]
			return ret






		###########################
		# section: backup / restore
		###########################



		def _backup(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""

				#if user!="root" :
				if not ctx.checkadmin():
						raise SecurityError, "Only root may backup the database"


				print 'backup has begun'
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

				print 'backup file opened'
				# dump users
				for i in users: dump(self.__users.sget(i, txn=txn), out)
				print 'users dumped'

				# dump workflow
				for i in workflows: dump(self.__workflow.sget(i, txn=txn), out)
				print 'workflows dumped'

				# dump binary data objects
				dump("bdos", out)
				bd = {}
				for i in bdos: bd[i] = self.__bdocounter.sget(i, txn=txn)
				dump(bd, out)
				bd = None
				print 'bdos dumped'

				# dump paramdefs and tree
				for i in paramdefs: dump(self.__paramdefs.sget(i, txn=txn), out)
				ch = []
				for i in paramdefs:
						c = set(self.__paramdefs.children(i, txn=txn))
#						 c=set([i[0] for i in c])
						c &= paramdefs
						c = tuple(c)
						ch += ((i, c),)
				dump("pdchildren", out)
				dump(ch, out)
				print 'paramdefs dumped'

				ch = []
				for i in paramdefs:
						c = set(self.__paramdefs.cousins(i, txn=txn))
						c &= paramdefs
						c = tuple(c)
						ch += ((i, c),)
				dump("pdcousins", out)
				dump(ch, out)
				print 'pdcousins dumped'

				# dump recorddefs and tree
				for i in recorddefs: dump(self.__recorddefs.sget(i, txn=txn), out)
				ch = []
				for i in recorddefs:
						c = set(self.__recorddefs.children(i, txn=txn))
#						 c=set([i[0] for i in c])
						c &= recorddefs
						c = tuple(c)
						ch += ((i, c),)
				dump("rdchildren", out)
				dump(ch, out)
				print 'rdchildren dumped'

				ch = []
				for i in recorddefs:
						c = set(self.__recorddefs.cousins(i, txn=txn))
						c &= recorddefs
						c = tuple(c)
						ch += ((i, c),)
				dump("rdcousins", out)
				dump(ch, out)
				print 'rdcousins dumped'

				# dump actual database records
				print "Backing up %d/%d records" % (len(records), self.__records.sget(-1, txn=txn))
				for i in records:
						dump(self.__records.sget(i, txn=txn), out)
				print 'records dumped'

				ch = []
				for i in records:
						c = [x for x in self.__records.children(i, txn=txn) if x in records]
						c = tuple(c)
						ch += ((i, c),)
				dump("recchildren", out)
				dump(ch, out)
				print 'rec children dumped'

				ch = []
				for i in records:
						c = set(self.__records.cousins(i, txn=txn))
						c &= records
						c = tuple(c)
						ch += ((i, c),)
				dump("reccousins", out)
				dump(ch, out)
				print 'rec cousins dumped'

				out.close()



		def _backup2(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctx=None, txn=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""
				import demjson

				#if user!="root" :
				if not self.checkadmin(ctx):
						raise SecurityError, "Only root may backup the database"


				print 'backup has begun'
				#user,groups=self.checkcontext(ctx=ctx, txn=txn)
				user = ctx.username
				groups = ctx.groups

				return demjson.encode(self.__users.values(txn=txn))



		#@txn
		#@write #everything...
		@publicmethod
		def restore(self, restorefile=None, types=None, ctx=None, txn=None):
				"""This will restore the database from a backup file. It is nondestructive, in that new items are
				added to the existing database. Naming conflicts will be reported, and the new version
				will take precedence, except for Records, which are always appended to the end of the database
				regardless of their original id numbers. If maintaining record id numbers is important, then a full
				backup of the database must be performed, and the restore must be performed on an empty database."""
				if not txn: txn = None

				if not self.__importmode:
					self.LOG(3, "WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
					return

				self.LOG(4, "Begin restore operation", ctx=ctx, txn=txn)

				user = ctx.username
				groups = ctx.groups

				if not ctx.checkadmin():
					raise SecurityError, "Database restore requires admin access"

				if type(restorefile) == file:
					fin = restorefile

				elif os.access(str(restorefile), os.R_OK):
					fin = open(restorefile, "r")

				elif os.access(self.path + "/backup.pkl", os.R_OK):
					fin = open(self.path + "/backup.pkl", "r")

				elif os.access(self.path + "/backup.pkl.bz2", os.R_OK) :
					fin = os.popen("bzcat " + self.path + "/backup.pkl.bz2", "r")

				elif os.access(self.path + "/../backup.pkl.bz2", os.R_OK) :
					fin = os.popen("bzcat " + self.path + "/../backup.pkl.bz2", "r")

				else:
					raise IOError, "Restore file (e.g. backup.pkl) not present"


				recmap = {}
				nrec = 0
				t0 = time.time()
				tmpindex = {}
				nel = 0


				recblock = []
				recblocklength = 50000
				commitrecs = 0
				committed = 0


				#types = ["record","user","recorddef","paramdef"]

				if not types:
					types = [
						"record",
						"user",
						"workflow",
						"recorddef",
						"paramdef",
						"bdos",
						"pdchildren",
						"pdcousins",
						"rdcousins",
						"recchildren",
						"reccousins"
						]

				# backup types =
				# [
				#	"record","user","recorddef","paramdef",
				#	"bdos","pdchildren","pdcousins","rdcousins","recchildren","reccousins"
				#]
				#print "begin restore"


				iteration = 0
				while (1):

					try:
						r = load(fin)
					except EOFError, inst:
						self.LOG('LOG_INFO', inst)


					commitrecs = 0

					# insert and renumber record
					if isinstance(r, Record) and "record" in types:
						recblock.append(r)
						if len(recblock) >= recblocklength:
							commitrecs = 1
					else:
						commitrecs = 1


					txn = self.newtxn()
					print "txn is %s"%txn, "iteration is %d" % iteration
					iteration += 1

					try:
						if commitrecs and recblock:
							oldids = [rec.recid for rec in recblock]
							for i in recblock:
								i.recid = None


							#try:
							newrecs = self.__putrecord(recblock, warning=1, validate=0, ctx=ctx, txn=txn)
							#except:
							#	self.txnabort(txn=newrectxn)
							#else:




							committed += len(newrecs)
							print "Committed total: %s"%committed

							for oldid,newrec in zip(oldids,newrecs):
								recmap[oldid] = newrec.recid
								if oldid != newrec.recid:
									print "Warning: recid %s changed to %s"%(oldid,newrec.recid)

							recblock = []
							#sys.exit(0)


						# insert User
						if isinstance(r, User) and "user" in types:
							#print "user: %s"%r.username
							self.putuser(r, validate=0, ctx=ctx, txn=txn)



						# insert Workflow
						elif isinstance(r, WorkFlow) and "workflow" in types:
							#print "workflow: %s"%r.wfid
							self.__workflow.set(r.wfid, r, txn=txn)



						# insert paramdef
						elif isinstance(r, ParamDef) and "paramdef" in types:
							#print "paramdef: %s"%r.name
							self.putparamdef(r, ctx=ctx, txn=txn)


						# insert recorddef
						elif isinstance(r, RecordDef) and "recorddef" in types:
							#print "recorddef: %s"%r.name
							self.putrecorddef(r, ctx=ctx, txn=txn)



						elif isinstance(r, str):
							print "btree type: %s"%r
							rr = load(fin)

							if r not in types:
								continue

							if r == "bdos":
								print "bdo"
								# read the dictionary of bdos
								for i, d in rr.items():
									self.__bdocounter.set(i, d, txn=txn)

							elif r == "pdchildren":
								print "pdchildren"
								# read the dictionary of ParamDef PC links
								for p, cl in rr:
									for c in cl:
										self.__paramdefs.pclink(p, c, txn=txn)

							elif r == "pdcousins":
								print "pdcousins"
								# read the dictionary of ParamDef PC links
								for a, bl in rr:
									for b in bl:
										self.__paramdefs.link(a, b, txn=txn)

							elif r == "rdchildren":
								print "rdchildren"
								# read the dictionary of ParamDef PC links
								for p, cl in rr:
									for c in cl:
										self.__recorddefs.pclink(p, c, txn=txn)

							elif r == "rdcousins":
								print "rdcousins"
								# read the dictionary of ParamDef PC links
								for a, bl in rr:
									for b in bl:
										self.__recorddefs.link(a, b, txn=txn)

							elif r == "recchildren":
								print "recchildren"
								# read the dictionary of ParamDef PC links
								for p, cl in rr:
									for c in cl:
										if isinstance(c, tuple):
											print "Invalid (deprecated) named PC link, database restore will be incomplete"
										else:
											self.__records.pclink(recmap[p], recmap[c], txn=txn)


							elif r == "reccousins":
								print "reccousins"
								# read the dictionary of ParamDef PC links
								for a, bl in rr:
									for b in bl:
										self.__records.link(recmap[a], recmap[b], txn=txn)

							else:
								print "Unknown category: ", r

					finally:
						self.txncommit(txn=txn)
						print "checkpointing"
						self.__dbenv.txn_checkpoint()
						self.__dbenv.log_archive(db.DB_ARCH_REMOVE)
						DB_syncall()


				print "Done!"

				if txn:
					#txn.commit()
					self.LOG(4, "Import Complete, checkpointing", ctx=ctx, txn=txn)
					self.__dbenv.txn_checkpoint()





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
			# 		raise SecurityError, "Only root may restore the database"
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
			# 				r = load(fin)
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
			# 				if (nr < 20) : print r["identifier"]
			# 				nr += 1
			#
			# 		elif isinstance(r, str) :
			# 				if r == "pdchildren" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "pdcousins" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "rdchildren" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "rdcousins" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "recchildren" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				elif r == "reccousins" :
			# 						rr = load(fin)						# read the dictionary of ParamDef PC links
			# 						np += len(rr)
			# 				else : print "Unknown category ", r
			#
			# print "Users=", nu, "	 ParamDef=", npd, "	 RecDef=", nrd, "	 Records=", nr, "	 Links=", np






def DB_cleanup():
	"""This does at_exit cleanup. It would be nice if this were always called, but if python is killed
	with a signal, it isn't. This tries to nicely close everything in the database so no recovery is
	necessary at the next restart"""
	sys.stdout.flush()
	print >> sys.stderr, "Closing %d BDB databases" % (len(BTree.alltrees) + len(RelateBTree.alltrees) + len(FieldBTree.alltrees))
	if DEBUG > 2: print >> sys.stderr, len(BTree.alltrees), 'BTrees'
	for i in BTree.alltrees.keys():
		if DEBUG > 2: sys.stderr.write('closing %s\n' % unicode(i))
		i.close()
		if DEBUG > 2: sys.stderr.write('%s closed\n' % unicode(i))
		if DEBUG > 2: print >> sys.stderr, '\n', len(RelateBTree.alltrees), 'RelateBTrees'
		for i in RelateBTree.alltrees.keys(): i.close()
		if DEBUG > 2: sys.stderr.write('.')
		if DEBUG > 2: print >> sys.stderr, '\n', len(FieldBTree.alltrees), 'FieldBTrees'
		for i in FieldBTree.alltrees.keys(): i.close()
		if DEBUG > 2: sys.stderr.write('.')
		if DEBUG > 2: sys.stderr.write('\n')

# This rmakes sure the database gets closed properly at exit
atexit.register(DB_cleanup)
