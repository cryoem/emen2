from bsddb3 import db
from cPickle import load, dump

from emen2.Database.btrees import *
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


import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


regex_pattern = 	 u"(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"		 \
"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
								"|(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
regex = re.compile(regex_pattern, re.UNICODE) # re.UNICODE


regex_pattern2 = 	u"(\$\$(?P<var>(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"		\
								"|(\$\@(?P<macro>(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
								"|(\$\#(?P<name>(?P<name1>\w*)))(?P<namesep>[\s<:]?)"
regex2 = re.compile(regex_pattern2, re.UNICODE) # re.UNICODE

recommentsregex = "\n"
pcomments = re.compile(recommentsregex) # re.UNICODE

TIMESTR = "%Y/%m/%d %H:%M:%S"
MAXIDLE = 604800


usetxn = False
envopenflags = db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_LOG | db.DB_THREAD
LOGSTRINGS = ["SECURITY", "CRITICAL", "ERROR", "WARNING ", "INFO", "VERBOSE ", "DEBUG"]
DEBUG = 0 #TODO consolidate debug flag



from emen2.util.utils import prop
class DBProxy(object):

	__publicmethods = {}
	__extmethods = {}

	@classmethod
	def _allmethods(cls):
		return set(cls.__publicmethods) | set(cls.__extmethods)

	def __init__(self, db=None, dbpath=None, ctxid=None, host=None):
		self.__bound = False
		self._setcontext(ctxid, host)
		if not db:
			self.__db = Database(dbpath)
		else:
			self.__db=db


	def _login(self, username, password, host=None):
		ctxid = self.__db.login(username, password)
		self._setcontext(ctxid, host)
		return self.__ctxid

	def _setcontext(self, ctxid=None, host=None):
		g.debug("dbproxy: setcontext %s %s"%(ctxid,host))
		#self._bound = True

		self.__ctxid=ctxid
		self.__host=host
		if ctxid is not None:
			self.__bound = True

	def _clearcontext(self):
		g.debug("dbproxy: clearcontext")
		if self.__bound:
			self.__ctxid=None
			self.__host=None
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



#	def __call__(self, *args, **kwargs):
	def __getattribute__(self, name):

		if name.startswith('__') and name.endswith('__'):
			result = getattr(self.__db, name)()
		elif name.startswith('_'): return object.__getattribute__(self, name)

		db = self.__db
		kwargs = {}

		ctxid = self.__ctxid
		host = self.__host
		if ctxid and not kwargs.get('ctxid'):
			kwargs["ctxid"]=ctxid
		if host and not kwargs.get('host'):
			kwargs["host"]=host


		result = None
		if name in self._allmethods():

			g.debug("DB: %s, kwargs: %s"%(name,kwargs))

			result = self.__publicmethods.get(name) # or self.__extmethods.get(name)()

			if result:
				result = partial(result, db, **kwargs)
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
	if DEBUG > 2:
		print "sync %d BDB databases" % (len(BTree.alltrees) + len(IntBTree.alltrees) + len(FieldBTree.alltrees))
	t = time.time()
	for i in BTree.alltrees.keys(): i.sync()
	for i in IntBTree.alltrees.keys(): i.sync()
	for i in FieldBTree.alltrees.keys(): i.sync()
	# print "%f sec to sync"%(time.time()-t)






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


		def publicmethod(func):
			DBProxy._register_publicmethod(func.func_name, func)
			return func



		def __init__(self, path=".", cachesize=32000000, logfile="db.log", importmode=0, rootpw=None, recover=0, allowclose=True):
			"""path - The path to the database files, this is the root of a tree of directories for the database
			cachesize - default is 64M, in bytes
			logfile - defualt "db.log"
			importmode - DANGEROUS, makes certain changes to allow bulk data import. Should be opened by only a single thread in importmode.
			recover - Only one thread should call this. Will run recovery on the environment before opening."""

			global envopenflags, usetxn

			if usetxn:
				self.newtxn = self.newtxn1
			else:
				g.debug("LOG_INFO","Note: transaction support disabled")
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

			xtraflags = 0
			if recover:
				xtraflags = db.DB_RECOVER

			# This sets up a DB environment, which allows multithreaded access, transactions, etc.
			if not os.access(path + "/home", os.F_OK):
				os.makedirs(path + "/home")

			self.LOG(4, "Database initialization started")
			self.__allowclose = bool(allowclose)
			self.__dbenv = db.DBEnv()
			self.__dbenv.set_cachesize(0, cachesize, 4) # gbytes, bytes, ncache (splits into groups)
			self.__dbenv.set_data_dir(path)
			self.__dbenv.set_lk_detect(db.DB_LOCK_DEFAULT) # internal deadlock detection
			self.__dbenv.set_lk_max_locks(20000)
			self.__dbenv.set_lk_max_lockers(20000)

			#if self.__dbenv.DBfailchk(flags=0):
					#self.LOG(1,"Database recovery required")
					#sys.exit(1)

			self.__dbenv.open(path + "/home", envopenflags | xtraflags)

			global globalenv
			globalenv = self.__dbenv


			if not os.access(path + "/security", os.F_OK):
				os.makedirs(path + "/security")
			if not os.access(path + "/index", os.F_OK):
				os.makedirs(path + "/index")

			# Users
			self.__users = BTree("users", path + "/security/users.bdb", dbenv=self.__dbenv)	# active database users
			self.__newuserqueue = BTree("newusers", path + "/security/newusers.bdb", dbenv=self.__dbenv) # new users pending approval
			self.__contexts_p = BTree("contexts", path + "/security/contexts.bdb", dbenv=self.__dbenv) # multisession persistent contexts
			self.__contexts = {} # local cache dictionary of valid contexts

			txn = self.newtxn()

			# Create an initial administrative user for the database
			if (not self.__users.has_key("root")):
				self.LOG(0, "Warning, root user recreated")
				u = User()
				u.username = "root"
				if rootpw:
					p = hashlib.sha1(rootpw)
				else:
					p = hashlib.sha1(g.ROOTPW)
				u.password = p.hexdigest()
				u.groups = [-1]
				u.creationtime = self.gettime()
				u.name = ('','','Admin')
				self.__users.set("root", u, txn)

			# Binary data names indexed by date
			self.__bdocounter = BTree("BinNames", path + "/BinNames.bdb", dbenv=self.__dbenv, relate=0)

			# Defined ParamDefs
			self.__paramdefs = BTree("ParamDefs", path + "/ParamDefs.bdb", dbenv=self.__dbenv, relate=1) # ParamDef objects indexed by name

			# Defined RecordDefs
			self.__recorddefs = BTree("RecordDefs", path + "/RecordDefs.bdb", dbenv=self.__dbenv, relate=1)	# RecordDef objects indexed by name

			# The actual database, keyed by recid, a positive integer unique in this DB instance
			# ian todo: check this statement:
			# 2 special keys exist, the record counter is stored with key -1
			# and database information is stored with key=0
			self.__records = IntBTree("database", path + "/database.bdb", dbenv=self.__dbenv, relate=1)	# The actual database, containing id referenced Records

			try:
				maxr = self.__records.get(-1, txn)
			except:
				self.__records.set(-1, 0, txn)
				self.LOG(3, "New database created")

			# Indices
			if self.__importmode:
				self.__secrindex = MemBTree("secrindex", path + "/security/roindex.bdb", "s", dbenv=self.__dbenv) # index of records each user can read
				self.__recorddefindex = MemBTree("RecordDefindex", path + "/RecordDefindex.bdb", "s", dbenv=self.__dbenv) # index of records belonging to each RecordDef
			else:
				self.__secrindex = FieldBTree("secrindex", path + "/security/roindex.bdb", "s", dbenv=self.__dbenv)	# index of records each user can read
				self.__recorddefindex = FieldBTree("RecordDefindex", path + "/RecordDefindex.bdb", "s", dbenv=self.__dbenv)	# index of records belonging to each RecordDef

			self.__timeindex = BTree("TimeChangedindex", path + "/TimeChangedindex.bdb", dbenv=self.__dbenv) # key=record id, value=last time record was changed
			self.__recorddefbyrec = IntBTree("RecordDefByRec", path + "/RecordDefByRec.bdb", dbenv=self.__dbenv, relate=0)
			self.__fieldindex = {} # dictionary of FieldBTrees, 1 per ParamDef, not opened until needed


			# USE OF SEQUENCES DISABLED DUE TO DATABASE LOCKUPS
			#db sequence
			# self.__dbseq = self.__records.create_sequence()


			# The mirror database for storing offsite records
			self.__mirrorrecords = BTree("mirrordatabase", path + "/mirrordatabase.bdb", dbenv=self.__dbenv)


			# Workflow database, user indexed btree of lists of things to do
			# again, key -1 is used to store the wfid counter
			self.__workflow = BTree("workflow", path + "/workflow.bdb", dbenv=self.__dbenv)

			try:
				max = self.__workflow[ - 1]

			except:
				self.__workflow[ - 1] = 1
				self.LOG(3, "New workflow database created")


			# This sets up a few standard ParamDefs common to all records
			if not self.__paramdefs.has_key("creator"):
				self.__paramdefs.set_txn(txn)

				#pd = ParamDef("owner", "string", "Record Owner", "This is the user-id of the 'owner' of the record")
				#self.__paramdefs["owner"] = pd

				pd = ParamDef("creator", "user", "Record Creator", "The user-id that initially created the record")
				self.__paramdefs["creator"] = pd

				pd = ParamDef("modifyuser", "user", "Modified by", "The user-id that last changed the record")
				self.__paramdefs["modifyuser"] = pd

				pd = ParamDef("creationtime", "datetime", "Creation time", "The date/time the record was originally created")
				self.__paramdefs["creationtime"] = pd

				pd = ParamDef("modifytime", "datetime", "Modification time", "The date/time the record was last modified")
				self.__paramdefs["modifytime"] = pd

				pd = ParamDef("comments", "comments", "Record comments", "Record comments")
				self.__paramdefs["comments"] = pd

				pd = ParamDef("rectype", "string", "Record type", "Record type (RecordDef)")
				self.__paramdefs["rectype"] = pd

				pd = ParamDef("permissions", "acl", "Permissions", "Permissions")
				self.__paramdefs["permissions"] = pd

				pd = ParamDef("parents","links","Parents", "Parents")
				self.__paramdefs["parents"] = pd

				pd = ParamDef("children","links","Children", "Children")
				self.__paramdefs["children"] = pd

				pd = ParamDef("publish","boolean","Publish", "Publish")
				self.__paramdefs["publish"] = pd

				pd = ParamDef("deleted","boolean","Deleted", "Deleted")
				self.__paramdefs["deleted"] = pd

				self.__paramdefs.set_txn(None)

			if txn:
				txn.commit()
			elif not self.__importmode:
				DB_syncall()

			self.LOG(4, "Database initialized")
			g.debug.add_output(self.log_levels.values(), file(self.logfile, "a"))
			self.__anonymouscontext = self.__getcontext(self.login(), None)



		# one of these 2 methods is mapped to self.newtxn()
		def newtxn1(self):
			return self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)


		def newtxn2(self):
			return None


		def txncheck(self, txn=None):
			if not txn:
				txn = self.newtxn()
			return txn


		def txncommit(self, txn=None):
			txn = self.txncheck(txn)
			if txn:
				txn.commit()
			elif not self.__importmode:
				DB_syncall()


		def LOG(self, level, message):
			"""level is an integer describing the seriousness of the error:
			0 - security, security-related messages
			1 - critical, likely to cause a crash
			2 - serious, user will experience problems
			3 - minor, likely to cause minor annoyances
			4 - info, informational only
			5 - verbose, verbose logging
			6 - debug only"""
			global LOGSTRINGS

			if (level < 0 or level > 6):
				level = 6
			try:
				g.debug.msg(self.log_levels.get(level, level), "%s: (%s) %s" % (self.gettime(), LOGSTRINGS[level], message))
				#if level < 4 : print "%s: (%s)	%s" % (time.strftime(TIMESTR), LOGSTRINGS[level], message)
			except:
				traceback.print_exc(file=sys.stdout)
				print("Critical error!!! Cannot write log message to '%s'\n" % self.logfile)



		def __str__(self):
			"""Try to print something useful"""
			return "Database %d records\n( %s )"%(int(self.__records[-1]), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))



		def __checkpassword(self, username, password, ctxid=None, host=None):
			"""Check password against stored hash value; Returns bool"""
			s = hashlib.sha1(password)

			try:
				user = self.__users[username]
			except TypeError:
				raise AuthenticationError, AuthenticationError.__doc__

			if user.disabled:
				raise DisabledUserError, DisabledUserError.__doc__ % username

			return s.hexdigest() == user.password, user


		#@txn
		@publicmethod
		def login(self, username="anonymous", password="", maxidle=MAXIDLE, ctxid=None, host=None):
			"""Logs a given user in to the database and returns a ctxid, which can then be used for
			subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""

			ctx = None
			username = str(username)

			# Anonymous access
			if (username == "anonymous"): # or username == ""
				ctx = Context(None, self, None, [-4], host, maxidle)

			else:
				auth_result, user = self.__checkpassword(username, password, ctxid=ctxid, host=host)

				# Admins can "su"

				if (user) or self.checkadmin(ctxid,host):
					ctx = Context(None, self, username, user.groups, host, maxidle)
				else:
					self.LOG(0, "Invalid password: %s (%s)" % (username, host))
					raise AuthenticationError, AuthenticationError.__doc__


			# This shouldn't happen
			if ctx == None:
				self.LOG(1, "System error, login: %s (%s)" % (username, host))
				raise Exception, "System error, login: %s (%s)" % (username, host)

			# we use sha to make a key for the context as well
			s = hashlib.sha1(username + str(host) + str(time.time()))

			ctx.ctxid = s.hexdigest()
			self.__setcontext(ctx.ctxid, ctx=ctx)

			self.LOG(4, "Login succeeded %s (%s)" % (username, ctx.ctxid))
			return ctx.ctxid



		#@txn
		@publicmethod
		def deletecontext(self, ctxid=None, host=None):
			"""Delete a context/Logout user. Returns None."""

			if not hasattr(ctxid,"__iter__"):
				ctxid=[ctxid]

			txn = self.newtxn()

			for c in ctxid:
				# check we have access to this context
				ctx = self.__getcontext(c, host)
				self.__setcontext(ctxid, ctx=None)



		# Logout is the same as delete context
		@publicmethod
		def logout(self, ctxid=None, host=None):
			self.deletecontext(ctxid, host)




		# ian: change so all __setcontext calls go through same txn
		def __cleanupcontexts(self):
			"""This should be run periodically to clean up sessions that have been idle too long. Returns None."""
			self.lastctxclean = time.time()

			for ctxid, ctx in self.__contexts_p.items():
				# use the cached time if available
				try:
					c = self.__contexts[ctxid]
					ctx.time = c.time
				except:
					pass

				if ctx.time + (ctx.maxidle or 0) < time.time():
					self.LOG(4, "Expire context (%s) %d" % (ctx.ctxid, time.time() - ctx.time))
					self.__setcontext(ctx.ctxid, ctx=None)



		#@write #self.__contexts_p
		def __setcontext(self, ctxid, ctx=None, txn=None):
			"""Add or delete context"""

			#@begin
			if not txn:
				txn = self.newtxn()

			self.__contexts_p.set_txn(txn)

			# set context
			if ctx != None:
				try:
					self.__contexts[ctx.ctxid] = ctx
				except Exception, inst:
					self.LOG("LOG_ERROR","Unable to add local context %s (%s)"%(ctxid, inst))

				try:
					ctx.db = None
					self.__contexts_p.set(ctx.ctxid, ctx)
					g.debug("LOG_COMMIT","Commit: self.__contexts_p.set: %s"%ctx.ctxid)

					ctx.db = self
				except Exception, inst:
					self.LOG("LOG_ERROR","Unable to add persistent context %s (%s)"%(ctxid, inst))

			# delete context
			else:
				try:
					del self.__contexts[k[0]]
				except Exception, inst:
					self.LOG("LOG_ERROR","Unable to delete local context %s (%s)"%(ctxid, inst))

				try:
					del self.__contexts_p[ctxid]
					g.debug("LOG_COMMIT","Commit: self.__contexts_p.__delitem__: %s"%ctxid)

				except Exception, inst:
					self.LOG("LOG_ERROR","Unable to delete persistent context %s (%s)"%(ctxid, inst))

			self.__contexts_p.set_txn(None)

			if txn:
				txn.commit()
			elif not self.__importmode:
				DB_syncall()
			#@end


		def __getcontext(self, key, host):
			"""Takes a ctxid key and returns a context (for internal use only)
			Note that both key and host must match. Returns context instance."""

			if key in set([None, 'None']):
				return self.__anonymouscontext
			key = str(key)

			if (time.time() > self.lastctxclean + 30):
				# maybe not the perfect place to do this, but it will have to do
				self.__cleanupcontexts()

			try:
				ctx = self.__contexts[key]

			except:
				try:
					ctx = self.__contexts_p[key]
					ctx.db = self
					self.__contexts[key] = ctx		# cache result from database
				except:
					self.LOG(4, "Session expired %s" % key)
					raise SessionError, "Session expired"

			if host and host != ctx.host :
				self.LOG(0, "Hacker alert! Attempt to spoof context (%s != %s)" % (host, ctx.host))
				raise SessionError, "Bad address match, login sessions cannot be shared"

			ctx.time = time.time()

			if ctx.user != None:
				ctx.groups.append(-3)
			ctx.groups.append(-4)
			ctx.groups=list(set(ctx.groups))

			return ctx


		#@txn
		#@write #self.__bdocounter
		@publicmethod
		def newbinary(self, date, name, recid, key=None, filedata=None, paramname=None, ctxid=None, host=None):
				"""Get a storage path for a new binary object. Must have a
				recordid that references this binary, used for permissions. Returns a tuple
				with the identifier for later retrieval and the absolute path"""

				ctx = self.__getcontext(ctxid, host)

				if name == None or str(name) == "":
					raise ValueError, "BDO name may not be 'None'"

				if key and not ctx.checkadmin():
					raise SecurityError, "Only admins may manipulate binary tree directly"

				if date == None:
					date = self.gettime()

				if not key:
					year = int(date[:4])
					mon = int(date[5:7])
					day = int(date[8:10])
					newid = 0
				else:
					date=str(key)
					year=int(date[:4])
					mon=int(date[4:6])
					day=int(date[6:8])
					newid=int(date[9:13],16)


				key = "%04d%02d%02d" % (year, mon, day)

				# ian: check for permissions because actual operations are performed.
				rec = self.getrecord(recid, ctxid=ctxid, host=host)
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
				if not txn:
					txn = self.newtxn()

				try:
					itm = self.__bdocounter.get(key,txn)
					newid = max(itm.keys()) + 1
				except:
					itm = {}

				itm[newid] = (name, recid)
				self.__bdocounter.set(key, itm, txn)
				g.debug("LOG_COMMIT","Commit: self.__bdocounter.set: %s"%key)


				if txn:
					txn.commit()
				elif not self.__importmode:
					DB_syncall()
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
					param=self.getparamdef(paramname,ctxid=ctxid,host=host)
					if param.vartype == "binary":
						v=rec.get(paramname,[])
						v.append("bdo:"+bdo)
						rec[paramname]=v
					elif param.vartype == "binaryimage":
						rec[paramname]="bdo:"+bdo
					else:
						raise Exception, "Error: invalid vartype for binary: parameter %s, vartype is %s"%(paramname, param.vartype)
					self.putrecord(rec,ctxid=ctxid,host=host)


				return (key + "%05X" % newid, path + "/%05X" % newid)





		@publicmethod
		def getbinary(self, idents, filt=1, vts=None, params=None, ctxid=None, host=None):
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

				recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), idents), ctxid=ctxid, host=host, filt=1))
				recs.extend(filter(lambda x:isinstance(x,Record), idents))
				bids.extend(self.filtervartype(recs, vts, ctxid=ctxid, host=host, flat=1))

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
							name, recid = self.__bdocounter[key][bid]
					except:
							if filt:
								continue
							else:
								raise KeyError, "Unknown identifier %s" % ident


					try:
						self.getrecord(recid, ctxid=ctxid, host=host)
						ret[ident] = (name, path + "/%05X" % bid, recid)

					except:
						if filt:
							continue
						else:
							raise SecurityError, "Not authorized to access %s(%0d)" % (ident, recid)


				#if ol: return ret.values()[0]
				return ret



		@publicmethod
		def checkcontext(self, ctxid=None, host=None):
			"""This allows a client to test the validity of a context, and
			get basic information on the authorized user and his/her permissions"""

			a = self.__getcontext(ctxid, host)
			return (a.user, a.groups)



		@publicmethod
		def getindexbyrecorddef(self, recdefname, ctxid=None, host=None):
			"""Uses the recdefname keyed index to return all
			records belonging to a particular RecordDef as a set. Currently this
			is unsecured, but actual records cannot be retrieved, so it
			shouldn't pose a security threat."""

			return set(self.__recorddefindex[str(recdefname).lower()])



		@publicmethod
		def checkadmin(self, ctxid=None, host=None):
			"""Checks if the user has global write access. Returns bool."""
			try: return self.__getcontext(ctxid, host).checkadmin()
			except: return False



		@publicmethod
		def checkreadadmin(self, ctxid=None, host=None):
			"""Checks if the user has global read access. Returns bool."""
			try: return self.__getcontext(ctxid, host).checkreadadmin()
			except: return False



		@publicmethod
		def checkcreate(self, ctxid=None, host=None):
			"""Check for permission to create records. Returns bool."""
			try: return self.__getcontext(ctxid, host).checkcreate()
			except: return False



		def loginuser(self, ctxid=None, host=None):
			"""Who am I?"""
			ctx = self.__getcontext(ctxid, host)
			return ctx.user



		@publicmethod
		def getbinarynames(self, ctxid=None, host=None):
			"""Returns a list of tuples which can produce all binary object
			keys in the database. Each 2-tuple has the date key and the nubmer
			of objects under that key. A somewhat slow operation."""

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
					raise SecurityError, "getbinarynames not available to anonymous users"

			ret = self.__bdocounter.keys()
			ret = [(i, len(self.__bdocounter[i])) for i in ret]
			return ret





		@publicmethod
		def fulltextsearch(self, q, rectype=None, indexsearch=1, params=set(), recparams=0, builtinparam=0, ignorecase=1, subset=[], tokenize=0, single=0, includeparams=set(), ctxid=None, host=None):
			"""
			q: query
			rectype: use all of rectype as subset
			indexsearch: use indexes; otherwise interrogate each record
			params: set of params to search, can be used instead of subset
			recparams: include in-line param values
			builtinparam: include creator, creationtime, modifyuser, modifytime, permissions, and comments
			subset: provide a subset of records to search (useful)
			tokenize: boolean AND for multiple space-separated search terms
			single: stop at first match for each param
			includeparams: include these values w/ all results
			"""

			subset = set(subset)
			# search these params
			params = set(params)

			builtin = set(["creator", "creationtime", "modifyuser", "modifytime", "permissions", "comments"])

			oq = unicode(q)
			q = oq.lower()


			if rectype and not subset:
				subset = self.getindexbyrecorddef(rectype, ctxid=ctxid, host=host)

			if rectype and not params:
				pd = self.getrecorddef(rectype, ctxid=ctxid, host=host)
				params = set(pd.paramsK)

			if not params:
				params = set(self.getparamdefnames(ctxid=ctxid,host=host))

			if builtinparam:
				params |= builtin
			else:
				params -= builtin


			ret = {}

			g.debug(params)

			if not indexsearch or recparams: # and not params and ... and len(subset) < 1000
				g.debug("rec search: %s, subset %s"%(q,len(subset)))

				for rec in self.getrecord(subset,filt=1,ctxid=ctxid,host=host):

					for k in params:
						if ignorecase:
							if q in unicode(rec[k]).lower():
								if not ret.has_key(rec.recid): ret[rec.recid] = {}
								ret[rec.recid][k] = rec[k]
						else:
							if q in unicode(rec[k]):
								if not ret.has_key(rec.recid): ret[rec.recid] = {}
								ret[rec.recid][k] = rec[k]


					if ret.has_key(rec.recid) and includeparams:
						for i in includeparams:
							ret[rec.recid][i] = rec[i]


			else:
				g.debug("index search: %s, subset %s"%(q,len(subset)))
				#subset = self.filterbypermissions(subset,ctxid=ctxid,host=host)

				for param in params:
					g.debug("searching %s" % param)
					try:
						r = self.__getparamindex(str(param).lower(), ctxid=ctxid, host=host)
						#if not q in r:
						#	print "\tskipping"
						#	continue
						s = filter(lambda x:q in x, r.keys())
					except:
						continue

					recs = set()
					for i in s: recs |= r[i]
					for rec in self.getrecord(recs,filt=1,ctxid=ctxid,host=host): #&subset; add security back...?

						if not ret.has_key(rec.recid): ret[rec.recid]={}
						if not ignorecase:
							if oq in rec[param]:
								ret[rec.recid][param]=rec[param]
						else:
							ret[rec.recid][param]=rec[param]

						for i in includeparams:
							ret[rec.recid][i]=rec[i]

			for k,v in ret.items():
				g.debug(k,v)
			return ret





		# ian: finish..
		@publicmethod
		def getparamstatistics(self, paramname, ctxid=None, host=None):
			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
				raise SecurityError, "Not authorized to retrieve parameter statistics"

			try:
				ind = self.__getparamindex(paramname, create=0, ctxid=ctxid, host=host)
				# number of values, number of records
				return (len(ind.keys()), len(ind.values()))
			except:
				return (0,0)




		@publicmethod
		def getindexbyuser(self, username, ctxid=None, host=None):
			"""This will use the user keyed record read-access index to return
			a list of records the user can access. DOES NOT include that user's groups.
			Use getindexbycontext if you want to see all recs you can read."""

			ctx = self.__getcontext(ctxid, host)

			if username == None:
				username = ctx.user

			if ctx.user != username and not ctx.checkreadadmin():
				raise SecurityError, "Not authorized to get record access for %s" % username


			return set(self.__secrindex[username])




		# ian: disabled for security reasons (it returns all values with no security check...)
		def getindexkeys(self, paramname, valrange=None, ctxid=None, host=None):
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
		def getindexbyvalue(self, paramname, valrange, ctxid=None, host=None):
			"""For numerical & simple string parameters, this will locate all records
			with the specified paramdef in the specified range.
			valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""

			ctx = self.__getcontext(ctxid, host)

			paramname = str(paramname).lower()

			ind = self.__getparamindex(paramname, create=0, ctxid=ctxid, host=host)

			if valrange == None:
				ret = set(ind.values())

			elif isinstance(valrange, (tuple, list)):
				ret = set(ind.values(valrange[0], valrange[1]))

			else:
				ret = set(ind[valrange] or [])

			#u,g=self.checkcontext(ctxid,host)
			#ctx=self.__getcontext(ctxid,host)
			if ctx.checkreadadmin():
				return ret

			#secure = set(self.getindexbycontext(ctxid=ctxid, host=host)) # all records the user can access
			return self.filterbypermissions(ret,ctxid=ctxid,host=host) #ret & secure # intersection of the two search results






		@publicmethod
		def getindexdictbyvalue(self, paramname, valrange, subset=None, ctxid=None, host=None):
			"""For numerical & simple string parameters, this will locate all records
			with the specified paramdef in the specified range.
			valrange may be a None (matches all), a single value, or a (min,max) tuple/list.
			This method returns a dictionary of all matching recid/value pairs
			if subset is provided, will only return values for specified recids"""

			paramname = str(paramname).lower()

			ind = self.__getparamindex(paramname, create=1, ctxid=ctxid, host=host)

			if valrange == None:
				r = dict(ind.items())
			elif isinstance(valrange, tuple) or isinstance(valrange, list):
				r = dict(ind.items(valrange[0], valrange[1]))
			else:
				r = {valrange:ind[valrange]}

			# This takes the returned dictionary of value/list of recids
			# and makes a dictionary of recid/value pairs
			ret = {}
			all = {}

			for i,j in r.items():
				for k in j:
					all[k] = i
			if subset:
				for i in subset:
					ret[i]=all.get(i)
			else:
				ret = all

			ctx = self.__getcontext(ctxid, host)
			#if (-1 in ctx.groups) or (-2 in ctx.groups) : return ret
			if ctx.checkreadadmin():
				return ret

			secure = self.filterbypermissions(ret.keys(),ctxid=ctxid,host=host)

			# remove any recids the user cannot access
			for i in set(ret.keys()) - secure:
				del ret[i]

			return ret



		# ian: remove?
		@publicmethod
		def getindexdictbyvaluefast(self, subset, param, valrange=None, ctxid=None, host=None):
			"""quick version for records that are already in cache; e.g. table views. requires subset."""

			v = {}
			records = self.getrecord(subset, ctxid=ctxid, host=host, filt=1)
			for i in records:
				if not valrange:
					v[i.recid] = i[param]
				else:
					if i[param] > valrange[0] and i[param] < valrange[1]:
						v[i.recid] = i[param]
			return v




		# ian: todo: better way to decide which grouping mechanism to use
		@publicmethod
		def groupbyrecorddef(self, all, optimize=1, ctxid=None, host=None):
			"""This will take a set/list of record ids and return a dictionary of ids keyed
			by their recorddef"""

			if not hasattr(all,"__iter__"):
				all=[all]

			if len(all) == 0:
				return {}

			if (optimize and len(all) < 1000) or (isinstance(list(all)[0],Record)):
				return self.__groupbyrecorddeffast(all, ctxid=ctxid, host=host)

			all = self.filterbypermissions(all,ctxid=ctxid,host=host)

			ret = {}
			while len(all) > 0:
				rid = all.pop()														 # get a random record id
				try:
					r = self.getrecord(rid, ctxid=ctxid, host=host)		# get the record
				except:
					continue												# if we can't, just skip it, pop already removed it
				ind = self.getindexbyrecorddef(r.rectype, ctxid=ctxid, host=host)				 # get the set of all records with this recorddef
				ret[r.rectype] = all & ind										# intersect our list with this recdef
				all -= ret[r.rectype]												 # remove the results from our list since we have now classified them
				ret[r.rectype].add(rid)										 # add back the initial record to the set

			return ret



		# this one gets records directly
		def __groupbyrecorddeffast(self, records, ctxid=None, host=None):

			if not isinstance(list(records)[0],Record):
				recs=self.getrecord(records, ctxid=ctxid, host=host, filt=1)
				#if len(records)==1: recs=[recs]

			ret={}
			for i in recs:
				if not ret.has_key(i.rectype): ret[i.rectype]=set([i.recid])
				else: ret[i.rectype].add(i.recid)

			return ret



		# this one gets rectype by index
		def __groupbyrecorddeffast2(self, records, ctxid=None, host=None):

			if len(records) == 0: return {}
			r = {}
			records = self.filterbypermissions(records,ctxid=ctxid,host=host)
			#records=set(records) & self.getindexbycontext(ctxid=ctxid, host=host)
			for i in records:
				j = self.__recorddefbyrec[i]		# security checked above
				if r.has_key(j):
					r[j].add(i)
				else:
					r[j] = set([i])
			return r






		@publicmethod
		def groupby(self, records, param, ctxid=None, host=None):
			"""This will group a list of record numbers based on the value of 'param' in each record.
			Records with no defined value will be grouped under the special key None. It would be a bad idea
			to, for example, groupby 500,000 records by a float parameter with a different value for each
			record. It will do it, but you may regret asking.

			We really need 2 implementations here (as above), one using indices for large numbers of records and
			another using record retrieval for small numbers of records"""
			r = {}
			for i in records:
				try:
					j = self.getrecord(i, ctxid=ctxid, host=host)
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




		@publicmethod
		def groupbyparentoftype(self, records, parenttype, recurse=3, ctxid=None, host=None):
			"""This will group a list of record numbers based on the recordid of any parents of
			type 'parenttype'. within the specified recursion depth. If records have multiple parents
			of a particular type, they may be multiply classified. Note that due to large numbers of
			recursive calls, this function may be quite slow in some cases. There may also be a
			None category if the record has no appropriate parents. The default recursion level is 3."""

			r = {}
			for i in records:
				try:
					p = self.getparents(i, recurse=recurse, ctxid=ctxid, host=host)
				except:
					continue
				try:
					k = [ii for ii in p if self.getrecord(ii, ctxid=ctxid, host=host).rectype == parenttype]
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



		# ian: todo: remove?
		@publicmethod
		def countchildren(self, key, recurse=0, ctxid=None, host=None):
			"""Unlike getchildren, this works only for 'records'. Returns a count of children
			of the specified record classified by recorddef as a dictionary. The special 'all'
			key contains the sum of all different recorddefs"""

			c = self.getchildren(key, "record", recurse=recurse, ctxid=ctxid, host=host)
			r = self.groupbyrecorddef(c, ctxid=ctxid, host=host)
			for k in r.keys(): r[k] = len(r[k])
			r["all"] = len(c)
			return r




		@publicmethod
		def getchildren(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctxid=None, host=None):
			"""Get children;
			keytype: record, paramdef, recorddef
			recurse: recursion depth
			rectype: for records, return only children of type rectype
			filt: filt by permissions
			tree: return results in graph format; default is set format
			"""
			return self.__getrel_wrapper(key=key,keytype=keytype,recurse=recurse,ctxid=ctxid,host=host,rectype=rectype,rel="children",filt=filt,tree=tree)



		@publicmethod
		def getparents(self, key, keytype="record", recurse=0, rectype=None, filt=0, tree=0, ctxid=None, host=None):
			"""see: getchildren"""
			return self.__getrel_wrapper(key=key,keytype=keytype,recurse=recurse,ctxid=ctxid,host=host,rectype=rectype,rel="parents",filt=filt,tree=tree)



		# wraps getrel / works as both getchildren/getparents
		@publicmethod
		def __getrel_wrapper(self, key, keytype="record", recurse=0, rectype=None, rel="children", filt=0, tree=0, ctxid=None, host=None):
			#print "getchildren: %s, recurse=%s, rectype=%s, filter=%s, tree=%s"%(key,recurse,rectype,filter,tree)
			"""Add some extra features to __getrel"""

			ol=0
			if not hasattr(key,"__iter__"):
				ol=1
				key=[key]

			if tree and rectype:
				raise Exception,"tree and rectype are mutually exclusive"

			ret={}
			all=set()

			for i in key:
				r = self.__getrel(key=i, keytype=keytype, recurse=recurse, rel=rel, ctxid=ctxid, host=host)
				ret[i] = r[tree]
				all |= r[0]


			# ian: think about doing this a better way
			if filt:
				all=self.filterbypermissions(all,ctxid=ctxid,host=host)

				if not tree:
					for k,v in ret.items():
						ret[k] = ret[k] & all

				else:
					for k,v in ret.items():
						for k2,v2 in v.items():
							ret[k][k2] = set(v2) & set(all)


			if rectype:
				r=self.groupbyrecorddef(self.__flatten(ret.values()),ctxid=ctxid,host=host).get(rectype,set())
				for k,v in ret.items():
					ret[k]=ret[k]&r
					if not ret[k]: del ret[k]

			if ol and tree==0: return ret.get(key[0],set())
			if ol and tree==1: return ret.get(key[0],{})
			return ret






		def __getrel(self, key, keytype="record", recurse=0, indc=None, rel="children", ctxid=None, host=None):
			"""get parent/child relationships; see: getchildren"""

			if (recurse < 0):
				return set(),{}

			if keytype == "record":
				trg = self.__records
				key=int(key)
				# read permission required
				try:
					self.getrecord(key, ctxid=ctxid, host=host)
				except:
					return set(),{}

			elif keytype == "recorddef":
				key = str(key).lower()
				trg = self.__recorddefs
				try: a = self.getrecorddef(key, ctxid=ctxid, host=host)
				except: return set(),{}

			elif keytype == "paramdef":
				key = str(key).lower()
				trg = self.__paramdefs

			else:
				raise Exception, "getchildren keytype must be 'record', 'recorddef' or 'paramdef'"

			if rel=="children":
				rel=trg.children
			elif rel=="parents":
				rel=trg.parents
			else:
				raise Exception, "Unknown relationship mode"

			# base result
			ret=rel(key) or []

			stack=[ret]
			result={key: ret}
			for x in xrange(recurse):
				if len(stack[x])==0:
					break
				if x >= self.maxrecurse-1:
					raise Exception, "Recurse limit reached; check for circular relationships?"
				stack.append([])

				for k in set(stack[x])-set(result.keys()):
					new=rel(k) or []
					stack[x+1].extend(new)
					result[k] = set(new)


			# hmm, too slow. manually flatten.
			#all=set(self.__flatten(result.values()))
			all=[]
			for i in stack:
				all.extend(i)
			all=set(all)


			if indc:
				all &= indc
				for k,v in result.items():
					result[k] = result[k] & all


			return all,result






		@publicmethod
		def getcousins(self, key, keytype="record", ctxid=None, host=None):
			"""This will get the keys of the cousins of the referenced object
			keytype is 'record', 'recorddef', or 'paramdef'"""

			if keytype == "record" :
				#if not self.trygetrecord(key, ctxid=ctxid, host=host) : return set()
				try:
					self.getrecord(key,ctxid=ctxid,host=host)
				except:
					return set
				return set(self.__records.cousins(key))

			if keytype == "recorddef":
				return set(self.__recorddefs.cousins(str(key).lower()))

			if keytype == "paramdef":
				return set(self.__paramdefs.cousins(str(key).lower()))

			raise Exception, "getcousins keytype must be 'record', 'recorddef' or 'paramdef'"




		#@txn
		@publicmethod
		def pclink(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
			"""Establish a parent-child relationship between two keys.
			A context is required for record links, and the user must
			have write permission on at least one of the two."""
			ctx = self.__getcontext(ctxid, host)
			return self.__link("pclink", pkey, ckey, keytype=keytype, ctx=ctx)


		#@txn
		@publicmethod
		def pcunlink(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
			"""Remove a parent-child relationship between two keys. Returns none if link doesn't exist."""
			ctx = self.__getcontext(ctxid, host)
			return self.__link("pcunlink", pkey, ckey, keytype=keytype, ctx=ctx)


		#@txn
		@publicmethod
		def link(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
			ctx = self.__getcontext(ctxid, host)
			return self.__link("link", pkey, ckey, keytype=keytype, ctx=ctx)

		#@txn
		@publicmethod
		def unlink(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
			ctx = self.__getcontext(ctxid, host)
			return self.__link("unlink", pkey, ckey, keytype=keytype, ctx=ctx)


		def __link(self, mode, pkey, ckey, keytype="record", ctx=None, txn=None):

			if keytype not in ["record", "recorddef", "paramdef"]:
				raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

			if mode not in ["pclink","pcunlink","link","unlink"]:
				raise Exception, "Invalid relationship mode %s"%mode

			if not ctx.checkcreate():
				raise SecurityError, "linking mode %s requires record creation priveleges"%mode

			if pkey==ckey:
				self.log("LOG_ERROR","Cannot link to self: keytype %s, key %s <-> %s"%(keytype, pkey, ckey))
				return

			# ian: circular reference detection.
			if mode=="pclink" and not self.__importmode:
				p = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="parents", ctxid=ctx.ctxid, host=ctx.host)[0]
				c = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="children", ctxid=ctx.ctxid, host=ctx.host)[0]
				if pkey in c or ckey in p or pkey == ckey:
					raise Exception, "Circular references are not allowed: parent %s, child %s"%(pkey,ckey)

			if keytype == "record":
				a = self.getrecord(pkey, ctxid=ctx.ctxid, host=ctx.host)
				b = self.getrecord(ckey, ctxid=ctx.ctxid, host=ctx.host)
				if (not a.writable()) and (not b.writable()):
					raise SecurityError, "pclink requires partial write permission"

			else:
				pkey = str(pkey).lower()
				ckey = str(pkey).lower()

			r = self.__commit_link(keytype, mode, pkey, ckey)
			return r



		#@write #self.__recorddefs, self.__records, self.__paramdefs
		def __commit_link(self, keytype, mode, pkey, ckey, ctx=None, txn=None):
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
			if not txn:
				txn = self.newtxn()

			linker(pkey, ckey, txn=txn)
			g.debug("LOG_COMMIT","Commit: link: keytype %s, mode %s, pkey %s, ckey %s"%(keytype, mode, pkey, ckey))

			if txn: txn.commit()
			elif not self.__importmode : DB_syncall()
			#@end

			if ctx is None:
				self.LOG(0, "pclink %s: %s <-> %s by unknown user" % (keytype, pkey, ckey))
			else:
				self.LOG(0, "pclink %s: %s <-> %s by user %s" % (keytype, pkey, ckey, ctx.user))


		#@txn
		@publicmethod
		def disableuser(self, username, ctxid=None, host=None):
			"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
			a complete historical record is maintained. Only an administrator can do this."""
			return self.__setuserstate(username, 1, ctxid=ctxid, host=host)


		#@txn
		@publicmethod
		def enableuser(self, username, ctxid=None, host=None):
			return self.__setuserstate(username, 0, ctxid=ctxid, host=host)



		def __setuserstate(self, username, state, ctxid=None, host=None):
			"""Set user enabled/disabled. 0 is enabled. 1 is disabled."""

			state=int(state)

			if state not in [0,1]:
				raise Exception, "Invalid state. Must be 0 or 1."

			ctx = self.__getcontext(ctxid, host)
			if not ctx.checkadmin():
					raise SecurityError, "Only administrators can disable users"

			ol=0
			if not hasattr(username, "__iter__"):
				ol=1
				username=[username]

			commitusers = []
			for i in username:
				if i == ctx.user:
					continue
					# raise SecurityError, "Even administrators cannot disable themselves"
				i = str(i)
				user = self.__users[i]
				if user.disabled == state:
					continue

				user.disabled = int(state)
				commitusers.append(i)


			ret = self.__commit_users(commitusers)
			self.LOG(0, "Users %s disabled by %s"%([user.username for user in ret], ctx.user))

			if ol: return ret[0].username
			return [user.username for user in ret]


		#@txn
		@publicmethod
		def approveuser(self, usernames, secret=None, ctxid=None, host=None):
			"""Only an administrator can do this, and the user must be in the queue for approval"""

			try:
				ctx = self.__getcontext(ctxid, host)
				admin = ctx.checkadmin()
				if secret == None or not admin:
					raise SecurityError, "Only administrators or users with self-authorization codes can approve new users"

			except SecurityError:
				raise

			except:
				admin = False
				if secret != None: pass
				else: raise


			ol=0
			if not hasattr(username,"__iter__"):
				ol=1
				usernames = [usernames]

			delusers = {}
			addusers = {}
			records = {}

			for username in usernames:
				if not username in self.__newuserqueue.keys():
					raise KeyError, "User %s is not pending approval" % username

				if username in self.__users:
					delusers[username] = None
					self.LOG("LOG_ERROR","User %s already exists, deleted pending record" % username)

				# ian: create record for user.
				user = self.__newuserqueue[username]
				user.validate()

				usersecret = user.signupinfo.get("secret")
				try: del user.signupinfo["secret"]
				except:	pass


				if secret and usersecret != secret:
					self.LOG("LOG_ERROR","Incorrect secret for user %s; skipping"%username)
					time.sleep(2)
					continue


				if user.record == None:
					rec = self.newrecord("person", init=1, ctxid=ctxid, host=host)
					rec["username"] = username
					rec["name_first"] = user.name[0]
					rec["name_middle"] = user.name[1]
					rec["name_last"] = user.name[2]
					rec["email"] = user.email
					rec.adduser(3,username)

					for k,v in user.signupinfo.items():
						rec[k]=v

					records[username] = rec

				user.signupinfo = None
				addusers[username] = user

			#recs, orecs, updrels = self.__putrecord_checknew(records.values(), ctx=ctx)

			#@begin

			txn = self.txncheck()

			crecs = self.__putrecord(recs, ctx=ctx, txn=txn)
			for rec in crecs:
				addusers[rec.get("username")].record = rec.recid

			self.__commit_users(addusers.values(), ctx=ctx, txn=txn)
			self.__commit_newusers(delusers, ctx=ctx, txn=txn)

			self.txncommit(txn)

			#@end

			ret = addusers.keys()
			if ol and len(ret)==1: return ret[0]
			return ret


		#@txn
		@publicmethod
		def rejectuser(self, usernames, ctxid=None, host=None):
			"""Remove a user from the pending new user queue - only an administrator can do this"""

			ctx = self.__getcontext(ctxid, host)

			# ian todo: move to general permission level check rather than hardcode -1 at each instance. several places.
			if not ctx.checkadmin():
				raise SecurityError, "Only administrators can approve new users"

			ol = 0
			if not hasattr(username,"__iter__"):
				ol = 1
				usernames = [usernames]

			delusers = {}

			for username in usernames:
				username = str(username)

				if not username in self.__newuserqueue:
					raise KeyError, "User %s is not pending approval" % username

				delusers[username] = None


			self.__commit_newusers(delusers) # queue[username] = None

			if ol and len(delusers) == 1: return delusers.keys()[0]
			return delusers



		@publicmethod
		def getuserqueue(self, ctxid=None, host=None):
			"""Returns a list of names of unapproved users"""
			ctx = self.__getcontext(ctxid, host)

			if not ctx.checkadmin():
				raise SecurityError, "Only administrators can approve new users"

			return self.__newuserqueue.keys()



		@publicmethod
		def getqueueduser(self, username, ctxid=None, host=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			if hasattr(username,"__iter__"):
				ret={}
				for i in username:
					ret[i] = self.getqueueduser(i,ctxid=ctxid,host=host)
				return ret


			username = str(username)

			ctx = self.__getcontext(ctxid, host)
			if not ctx.checkreadadmin():
				raise SecurityError, "Only administrators can access pending users"

			return self.__newuserqueue[username]


		#@txn
		@publicmethod
		def setuserprivacy(self, usernames, state, ctxid=None, host=None):
			ctx = self.__getcontext(ctxid, host)

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
				username = str(username)
				user = self.getuser(username, ctxid=ctxid, host=host)
				user.privacy = state
				commitusers.append(user)


			return self.__commit_users(commitusers, ctx=ctx)


		#@txn
		@publicmethod
		def setpassword(self, username, oldpassword, newpassword, ctxid=None, host=None):

			username = str(username)

			ctx = self.__getcontext(ctxid, host)
			user = self.getuser(username, ctxid=ctxid, host=host)

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

			self.__commit_users([user], ctx=ctx)

			return 1


		#@txn
		@publicmethod
		def adduser(self, user, ctxid=None, host=None):
			"""adds a new user record. However, note that this only adds the record to the
			new user queue, which must be processed by an administrator before the record
			becomes active. This system prevents problems with securely assigning passwords
			and errors with data entry. Anyone can create one of these"""

			if not isinstance(user, User):
				try:
					user = User(user)
				except:
					raise ValueError, "User instance or dict required"

			if user.username == None or len(str(user.username)) < 3:
				if self.__importmode:
					pass
				else:
					raise KeyError, "Attempt to add user with invalid name"

			if user.username in self.__users:
				if not self.__importmode:
					raise KeyError, "User with username %s already exists" % user.username
				else:
					pass

			if user.username in self.__newuserqueue:
				raise KeyError, "User with username %s already pending approval" % user.username

			# 40 = lenght of hex digest
			# we disallow bad passwords here, right now we just make sure that it
			# is at least 6 characters long
			if len(user.password) < 6 :
					raise SecurityError, "Passwords must be at least 6 characters long"

			s = hashlib.sha1(user.password)
			user.password = s.hexdigest()

			if not self.__importmode:
				user.creationtime = self.gettime()
				user.modifytime = self.gettime()

			user.validate()

 			self.__commit_newusers({user.username:user}, ctx=None)

			return user



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
					ouser = self.__users[user.username]
				except:
					raise KeyError, "Putuser may only be used to update existing users"

				if user.creator != ouser.creator or user.creationtime != ouser.creationtime:
					raise SecurityError, "Creation information may not be changed"

				user.validate()

				commitusers.append(user)

			#@begin

			if not txn:
				txn = self.newtxn()

			for user in commitusers:
				self.__users.set(user.username, user, txn)
				g.debug("LOG_COMMIT","Commit: self.__users.set: %s"%user.username)

			if txn:	txn.commit()
			elif not self.__importmode:	DB_syncall()

			#@end

			return commitusers


		#@write #self.__newuserqueue
		def __commit_newusers(self, users, ctx=None, txn=None):
			"""write to newuserqueue; users is dict; set value to None to del"""

			#@begin

			txn = self.txncheck(txn)

			for username, user in users.items():
				self.__newuserqueue.set(username, user, txn=txn)
				g.debug("LOG_COMMIT","Commit: self.__newuserqueue.set: %s"%username)

			self.txncommit(txn)

			#@end



		@publicmethod
		def getuser(self, usernames, filt=1, ctxid=None, host=None):
			"""retrieves a user's information. Information may be limited to name and id if the user
			requested privacy. Administrators will get the full record"""

			ol=0
			if not hasattr(usernames,"__iter__"):
				ol=1
				usernames=[usernames]

			ctx = self.__getcontext(ctxid, host)

			ret={}
			for i in usernames:

				try:
					user=self.__users[str(i)]
				except:

					try:
						int(i)
						continue

					except:
						pass

					if filt:
						continue
					else:
						raise KeyError, "No such user: %s"%i

				if ctx.checkreadadmin() or ctx.user == i:
					ret[i]=user
					continue

				# if the user has requested privacy, we return only basic info
				if (user.privacy == 1 and ctx.user == None) or user.privacy >= 2:
					user2 = User()
					user2.username = user.username
					user2.privacy = user.privacy
					user2.record = None
					user2.email = None
					user = user2

				# Anonymous users cannot use this to extract email addresses
				if ctx.user == None:
					user.groups = None
					user.email = None
					#ret.altemail=None

				ret[i]=user


			if len(ret.keys())==0: return {}

			if ol:
				return ret.get(ret.keys()[0])

			return ret



		@publicmethod
		def getusernames(self, ctxid=None, host=None):
			"""Not clear if this is a security risk, but anyone can get a list of usernames
					This is likely needed for inter-database communications"""

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
				return
			return self.__users.keys()




		@publicmethod
		def findusername(self, name, ctxid=None, host=None):
			"""This will look for a username matching the provided name in a loose way"""

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None: return

			name = str(name)
			if self.__users.has_key(name) : return name

			possible = filter(lambda x: name in x, self.__users.keys())
			if len(possible) == 1:
				return possible[0]
			if len(possible) > 1:
				return possible

			possible = []
			for i in self.getusernames(ctxid=ctxid, host=host):
				try:
					u = self.getuser(name, ctxid=ctxid, host=host)
				except:
					continue

				for j in u.__dict__:
					if isinstance(j, str) and name in j :
						possible.append(i)
						break

			if len(possible) == 1:
				return possible[0]
			if len(possible) > 1:
				return possible

			return None




		@publicmethod
		def getworkflow(self, ctxid=None, host=None):
			"""This will return an (ordered) list of workflow objects for the given context (user).
			it is an exceptionally bad idea to change a WorkFlow object's wfid."""

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
				raise SecurityError, "Anonymous users have no workflow"

			try:
				return self.__workflow[ctx.user]
			except:
				return []



		@publicmethod
		def getworkflowitem(self, wfid, ctxid=None, host=None):
			"""Return a workflow from wfid."""

			ret = None
			wflist = self.getworkflow(ctxid=ctxid,host=host)
			if len(wflist) == 0:
				return None
			else:
				for thewf in wflist:
					if thewf.wfid == wfid:
						ret = thewf.items_dict()
			return ret



		@publicmethod
		def newworkflow(self, vals, ctxid=None, host=None):
			"""Return an initialized workflow instance."""
			return WorkFlow(vals)



		#@txn
		#@write #self.__workflow
		@publicmethod
		def addworkflowitem(self, work, ctxid=None, host=None):
			"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""
			ctx = self.__getcontext(ctxid, host)

			if ctx.user == None:
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

			txn = self.newtxn()
			self.__workflow.set_txn(txn)
			work.wfid = self.__workflow[-1]
			self.__workflow[-1] = work.wfid + 1

			if self.__workflow.has_key(ctx.user):
				wf = self.__workflow[ctx.user]
			else:
				wf = []

			wf.append(work)
			self.__workflow[ctx.user] = wf
			self.__workflow.set_txn(None)

			if txn:	txn.commit()
			elif not self.__importmode:	DB_syncall()

			return work.wfid



		#@txn
		#@write #self.__workflow
		@publicmethod
		def delworkflowitem(self, wfid, ctxid=None, host=None):
			"""This will remove a single workflow object based on wfid"""
			#self = db

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
				raise SecurityError, "Anonymous users have no workflow"

			wf = self.__workflow[ctx.user]
			for i, w in enumerate(wf):
				if w.wfid == wfid :
					del wf[i]
					break
			else:
				raise KeyError, "Unknown workflow id"

			txn = self.newtxn()
			self.__workflow.set(ctx.user, wf, txn)

			if txn:	txn.commit()
			elif not self.__importmode:	DB_syncall()



		#@txn
		#@write #self.__workflow
		@publicmethod
		def setworkflow(self, wflist, ctxid=None, host=None):
			"""This allows an authorized user to directly modify or clear his/her workflow. Note that
			the external application should NEVER modify the wfid of the individual WorkFlow records.
			Any wfid's that are None will be assigned new values in this call."""
			#self = db

			ctx = self.__getcontext(ctxid, host)
			if ctx.user == None:
				raise SecurityError, "Anonymous users have no workflow"

			if wflist == None:
				wflist = []
			wflist = list(wflist)								 # this will (properly) raise an exception if wflist cannot be converted to a list

			txn = self.newtxn()

			for w in wflist:
				if not self.__importmode:
					#w=WorkFlow(w.__dict__.copy())
					w.validate()

				if not isinstance(w, WorkFlow):
					txn.abort()
					raise TypeError, "Only WorkFlow objects may be in the user's workflow"
				if w.wfid == None:
					w.wfid = self.__workflow[-1]
					self.__workflow.set(-1, w.wfid + 1, txn)

			self.__workflow.set(ctx.user, wflist, txn)

			if txn: txn.commit()
			elif not self.__importmode : DB_syncall()



		# ian: todo
		#@write #self.__workflow
		def __commit_workflow(self, wfs, ctx=None, txn=None):
			pass



		@publicmethod
		def getvartypenames(self, ctxid=None, host=None):
			"""This returns a list of all valid variable types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getvartypes()



		@publicmethod
		def getvartype(self, name, ctxid=None, host=None):
			"""This returns a list of all valid variable types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getvartype(name)
			#return valid_vartypes[thekey][1]


		@publicmethod
		def getpropertynames(self, ctxid=None, host=None):
			"""This returns a list of all valid property types in the database. This is currently a
			fixed list"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			return vtm.getproperties()




		@publicmethod
		def getpropertyunits(self, propname, ctxid=None, host=None):
			"""Returns a list of known units for a particular property"""
			vtm = emen2.Database.subsystems.datatypes.VartypeManager()
			# set(vtm.getproperty(propname).units) | set(vtm.getproperty(propname).equiv)
			return set(vtm.getproperty(propname).units)



		#@txn
		@publicmethod
		def addparamdef(self, paramdef, parents=[], ctxid=None, host=None):
			"""adds a new ParamDef object, group 0 permission is required
			a p->c relationship will be added if parent is specified"""

			if not isinstance(paramdef, ParamDef):
				try:
					paramdef = ParamDef(paramdef)
				except:
					raise ValueError, "ParamDef instance or dict required"
				#paramdef=ParamDef(paramdef.__dict__.copy())
				# paramdef.validate()

			ctx = self.__getcontext(ctxid, host)

			if not ctx.checkcreate():
				raise SecurityError, "No permission to create new paramdefs (need record creation permission)"

			paramdef.name = str(paramdef.name).lower()

			if self.__paramdefs.has_key(paramdef.name) :
				# Root is permitted to force changes in parameters, though they are supposed to be static
				# This permits correcting typos, etc., but should not be used routinely
				# skip relinking if we're editing
				parents=[]
				if not ctx.checkadmin():
					raise KeyError, "paramdef %s already exists" % paramdef.name

			else:
				# force these values
				paramdef.creator = ctx.user
				paramdef.creationtime = self.gettime()


			if not self.__importmode:
				paramdef.validate()

			# this actually stores in the database
			txn = self.txncheck(txn)

			self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)
			for parent in parents:
				self.pclink(parent, paramdef.name, "paramdef", txn=txn, ctxid=ctxid, host=host)

			self.txncommit(txn)



		#@txn
		@publicmethod
		def addparamchoice(self, paramdefname, choice, ctxid=None, host=None):
			"""This will add a new choice to records of vartype=string. This is
			the only modification permitted to a ParamDef record after creation"""

			paramdefname = str(paramdefname).lower()

			# ian: change to only allow logged in users to add param choices. silent return on failure.
			ctx = self.__getcontext(ctxid, host)
			if not ctx.checkcreate():
				return

			d = self.__paramdefs[paramdefname]
			if d.vartype != "string":
				raise SecurityError, "choices may only be modified for 'string' parameters"

			d.choices = d.choices + (str(choice).title(),)

			#self.__paramdefs.set(paramdefname, d, txn)
			self.__commit_paramdefs([d], ctx=ctx)



		#ian: todo
		#@write #self.__paramdefs
		def __commit_paramdefs(self, paramdefs, ctx=None, txn=None):

			#@begin

			txn = self.checktxn(txn)

			for paramdef in paramdefs:
				self.__paramdefs.set(paramdef.name, paramdef, txn=txn)
				g.debug("LOG_COMMIT","Commit: self.__paramdefs.set: %s"%paramdef.name)

			self.txncommit(txn)

			#@end



		# ian: remove this method
		def findparamdefname(self, name, ctxid=None, host=None):
			"""Find a paramdef similar to the passed 'name'. Returns the actual ParamDef, or None if no match is found."""
			name = str(name).lower()
			if self.__paramdefs.has_key(name):
				return name
			if name[-1] == "s":
				if self.__paramdefs.has_key(name[:-1]):
					return name[:-1]
				if name[ - 2] == "e" and self.__paramdefs.has_key(name[:-2]):
					return name[: - 2]
			if name[-3:] == "ing" and self.__paramdefs.has_key(name[:-3]):
				return name[: - 3]
			return None



		@publicmethod
		def getparamdefs(self, recs, filt=1, ctxid=None, host=None):
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
				recs = self.getrecord(recs, ctxid=ctxid, host=host)

			if isinstance(recs[0], Record):
				q = set((i.rectype for i in recs))
				for i in q:
					params |= set(self.getrecorddef(i, ctxid=ctxid, host=host).paramsK)
				for i in recs:
					params |= set(i.getparamkeys())

			if isinstance(recs[0], basestring):
				params = set(recs)

			paramdefs = {}
			for i in params:
				try:
					paramdefs[i] = self.__paramdefs[str(i)]
				except:
					if filt:
						print "WARNING: Invalid param: %s"%i
						pass
					else:
						raise Exception, "Invalid param: %s"%i

			return paramdefs




		# ian todo: combine this and getparamdefs; alot of older places use this version
		@publicmethod
		def getparamdef(self, key, ctxid=None, host=None):
			"""gets an existing ParamDef object, anyone can get any field definition"""
			key = str(key).lower()
			try:
				return self.__paramdefs[key]
			except:
				raise KeyError, "Unknown ParamDef: %s" % key



		@publicmethod
		def getparamdefnames(self, ctxid=None, host=None):
				"""Returns a list of all ParamDef names"""
				return self.__paramdefs.keys()


		#@txn
		@publicmethod
		def addrecorddef(self, recdef, parent=None, ctxid=None, host=None):
			"""adds a new RecordDef object. The user must be an administrator or a member of group 0"""

			if not isinstance(recdef, RecordDef):
				try:
					recdef = RecordDef(recdef)
				except:
					raise ValueError, "RecordDef instance or dict required"

			ctx = self.__getcontext(ctxid, host)

			recdef.validate()

			if not ctx.checkcreate():
				raise SecurityError, "No permission to create new RecordDefs"

			if self.__recorddefs.has_key(str(recdef.name).lower()):
				raise KeyError, "RecordDef %s already exists" % str(recdef.name).lower()

			recdef.findparams()
			pdn = self.getparamdefnames(ctxid=ctxid,host=host)
			for i in recdef.params:
				if i not in pdn:
					raise KeyError, "No such parameter %s" % i


			# force these values
			if (recdef.owner == None) : recdef.owner = ctx.user
			recdef.name = str(recdef.name).lower()
			recdef.creator = ctx.user
			recdef.creationtime = self.gettime()


			if not self.__importmode:
				recdef=RecordDef(recdef.__dict__.copy())
				recdef.validate()

			# commit
			txn = self.txncheck(txn)
			self.__commit_recorddefs([recdef], ctx=ctx, txn=txn)

			if parent:
				self.pclink(parent, recdef.name, "recorddef", txn=txn, ctxid=ctxid, host=host)

			self.txncommit(txn)

			return recdef.name


		#@txn
		@publicmethod
		def putrecorddef(self, recdef, ctxid=None, host=None):
			"""This modifies an existing RecordDef. The mainview should
			never be changed once used, since this will change the meaning of
			data already in the database, but sometimes changes of appearance
			are necessary, so this method is available."""
			#self = db

			if not isinstance(recdef, RecordDef):
				try:
					recdef = RecordDef(recdef)
				except:
					raise ValueError, "RecordDef instance or dict required"

			ctx = self.__getcontext(ctxid, host)

			recdef.validate()

			try:
				rd = self.__recorddefs[recdef.name]
			except:
				raise Exception, "No such recorddef %s"%recdef.name

			if ctx.user != rd.owner and not ctx.checkadmin():
				raise SecurityError, "Only the owner or administrator can modify RecordDefs"

			if recdef.mainview != rd.mainview and not ctx.checkadmin():
				raise SecurityError, "Only the administrator can modify the mainview of a RecordDef"


			recdef.findparams()
			pdn = self.getparamdefnames(ctxid=ctxid,host=host)
			for i in recdef.params:
				if i not in pdn:
					raise KeyError, "No such parameter %s" % i

			# reset
			recdef.creator = rd.creator
			recdef.creationtime = rd.creationtime
			#recdef.mainview=rd.mainview		#temp. change to allow mainview changes

			if not self.__importmode:
				recdef = RecordDef(recdef.__dict__.copy())
				recdef.validate()

			# commit
			self.__commit_recorddefs([recdef], ctx=ctx)



		#@write #self.__recorddefs
		def __commit_recorddefs(self, recorddefs, ctx=None, txn=None):

			#@begin

			txn = self.txncheck(txn)

			for recorddef in recorddefs:
				self.__recorddefs.set(recdef.name, recdef, txn=txn)
				g.debug("LOG_COMMIT","Commit: self.__recorddefs.set: %s"%recdef.name)

			self.txncommit(txn)

			#@end



		# ian todo: move host to end
		@publicmethod
		def getrecorddef(self, rectypename, recid=None, ctxid=None, host=None):
			"""Retrieves a RecordDef object. This will fail if the RecordDef is
			private, unless the user is an owner or	 in the context of a recid the
			user has permission to access"""

			if hasattr(rectypename,"__iter__"):
				ret={}
				for i in rectypename:
					ret[i]=self.getrecorddef(i,recid=recid,ctxid=ctxid,host=host)
				return ret


			rectypename = str(rectypename).lower()

			try:
				ret=self.__recorddefs[rectypename]
			except:
				raise KeyError, "No such RecordDef %s" % rectypename

			if not ret.private:
				return ret

			# if the RecordDef isn't private or if the owner is asking, just return it now
			ctx = self.__getcontext(ctxid, host)
			if (ret.private and (ret.owner == ctx.user or ret.owner in ctx.groups or ctx.checkreadadmin())):
				return ret

			# ian todo: make sure all calls to getrecorddef pass recid they are requesting

			# ok, now we need to do a little more work.
			if recid == None:
				raise SecurityError, "User doesn't have permission to access private RecordDef '%s'" % rectypename

			rec = self.getrecord(recid, ctxid=ctxid, host=host)
			# try to get the record, may (and should sometimes) raise an exception

			if rec.rectype != rectypename:
				raise SecurityError, "Record %d doesn't belong to RecordDef %s" % (recid, rectypename)

			# success, the user has permission
			return ret



		@publicmethod
		def getrecorddefnames(self, ctxid=None, host=None):
			"""This will retrieve a list of all existing RecordDef names,
			even those the user cannot access the contents of"""
			return self.__recorddefs.keys()



		@publicmethod
		def findrecorddefname(self, name, ctxid=None, host=None):
			"""Find a recorddef similar to the passed 'name'. Returns the actual RecordDef,
			or None if no match is found."""

			name = str(name).lower()

			if self.__recorddefs.has_key(name):
				return name
			if name[-1] == "s":
					if self.__recorddefs.has_key(name[:-1]):
						return name[:-1]
					if name[-2] == "e" and self.__recorddefs.has_key(name[:-2]):
						return name[:-2]
			if name[-3:] == "ing" and self.__recorddefs.has_key(name[:-3]):
				return name[:-3]
			return None



		#@write #self.__secrindex, self.__recorddefindex, self.__fieldindex*
		def __commit_indices(self):
			"""This is used in 'importmode' after many records have been imported using
			memory indices to dump the indices to the persistent files"""

			if not self.__importmode:
				g.debug.msg('LOG_ERROR',"commitindices may only be used in importmode")
				return

			for k, v in self.__fieldindex.items():
				if k == 'parent':
					continue
				print "commit index %s (%d)\tbtrees: %d\tfieldbtrees: %d" % (k, len(v), len(BTree.alltrees), len(FieldBTree.alltrees))
				i = FieldBTree(v.bdbname, v.bdbfile, v.keytype, v.bdbenv)
				txn = self.newtxn()
				i.set_txn(txn)
				for k2, v2 in v.items():
					#print "... addref: %s, len: %s"%(k2, len(v2))#,v2)
					i.addrefs(k2, v2)
				i.set_txn(None)
				if txn:
					txn.commit()
				i = None
				print "... done commit index"

			print "commit security"
			si = FieldBTree("secrindex", self.path + "/security/roindex.bdb", "s", dbenv=self.__dbenv)
			txn = self.newtxn()
			si.set_txn(txn)
			for k, v in self.__secrindex.items():
				si.addrefs(k, v)
			si.set_txn(None)
			if txn: txn.commit()

			print "commit recorddefs"
			rdi = FieldBTree("RecordDefindex", self.path + "/RecordDefindex.bdb", "s", dbenv=self.__dbenv)
			txn = self.newtxn()
			rdi.set_txn(txn)
			for k, v in self.__recorddefindex.items():
				rdi.addrefs(k, v)
			rdi.set_txn(None)
			if txn:
				txn.commit()
				self.LOG(4, "Index merge complete. Checkpointing")
				self.__dbenv.txn_checkpoint()
				self.LOG(4, "Checkpointing complete")
			else:
				print "Index merge complete Syncing"
				DB_syncall()

			DB_cleanup()
			self.__dbenv.close()
			if DEBUG > 2: print >> sys.stderr, '__dbenv.close() successful'
			sys.exit(0)



		def __getparamindex(self, paramname, create=1, ctxid=None, host=None):
			"""Internal function to open the parameter indices at need.
			Later this may implement some sort of caching mechanism.
			If create is not set and index doesn't exist, raises
			KeyError. Returns "link" or "child" for this type of indexing"""

			paramname = str(paramname).lower()

			try:
				return self.__fieldindex[paramname]				# Try to get the index for this key
			except Exception, inst:
				pass

			# index not open yet, open/create it
			#try:
			f = self.__paramdefs[paramname]				 # Look up the definition of this field
			#except:
			#		# Undefined field, we can't create it, since we don't know the type
			#		raise FieldError, "No such field %s defined" % paramname


			if f.vartype not in self.indexablevartypes:
				#print "\tunindexable vartype ",f.vartype
				return None

			tp = self.vtm.getvartype(f.vartype).getindextype()

			#print "Open paramindex for %s: vartype=%s, keytype=%s"%(f.name,f.vartype,tp)

			if not create and not os.access("%s/index/%s.bdb" % (self.path, paramname), os.F_OK):
				raise KeyError, "No index for %s" % paramname

			# create/open index
			if self.__importmode:
				#print "->MemBTree: %s"%paramname
				self.__fieldindex[paramname] = MemBTree(paramname, "%s/index/%s.bdb" % (self.path, paramname), tp, self.__dbenv)
			else:
				self.__fieldindex[paramname] = FieldBTree(paramname, "%s/index/%s.bdb" % (self.path, paramname), tp, self.__dbenv)

			return self.__fieldindex[paramname]






		# ian todo: redo these three methods
		#@txn
		@publicmethod
		def putrecordvalue(self, recid, param, value, ctxid=None, host=None, txn=None):
			"""Make a single change to a single record"""
			rec = self.getrecord(recid, ctxid=ctxid, host=host)
			rec[param] = value
			self.putrecord(rec, ctxid=ctxid, host=host)
			return self.getrecord(recid, ctxid=ctxid, host=host)[param]



		#@txn
		@publicmethod
		def putrecordvalues(self, recid, values, ctxid=None, host=None, txn=None):
			"""Make multiple changes to a single record"""

			try:
				rec = self.getrecord(recid, ctxid=ctxid, host=host)
			except:
				return

			for k, v in values.items():
				if v == None:
					del rec[k]
				else:
					rec[k] = v

			self.putrecord(rec, ctxid=ctxid, host=host)
			return self.getrecord(recid, ctxid=ctxid, host=host)



		#@txn
		@publicmethod
		def putrecordsvalues(self, d, ctxid=None, host=None):
			"""Make multiple changes to multiple records"""

			ret = {}
			for k, v in d.items():
				ret[k] = self.putrecordvalues(k, v, ctxid=ctxid, host=host)
			return ret


		#@txn
		@publicmethod
		def deleterecord(self,recid,ctxid=None,host=None):
			"""Unlink and hide a record; it is still accessible to owner and root. Records are never truly deleted, just hidden."""

			rec=self.getrecord(recid,ctxid=ctxid,host=host)
			if not rec.isowner():
				raise Exception,"No permission to delete record"

			parents=self.getparents(recid,ctxid=ctxid,host=host)
			children=self.getchildren(recid,ctxid=ctxid,host=host)

			if len(parents) > 0 and rec["deleted"] !=1 :
				rec["comments"]="Record marked for deletion and unlinked from parents: %s"%", ".join([str(x) for x in parents])
			elif rec["deleted"] != 1:
				rec["comments"]="Record marked for deletion"

			rec["deleted"]=1
			self.putrecord(rec,ctxid=ctxid,host=host)

			for i in parents:
				self.pcunlink(i,recid,ctxid=ctxid,host=host)

			for i in children:
				c2=self.getchildren(i,ctxid=ctxid,host=host)
				#c2.remove(recid)
				c2 -= set([recid])
				# if child had more than one parent, make a note one parent was removed
				if len(c2) > 0:
					rec2=self.getrecord(i,ctxid=ctxid,host=host)
					rec["comments"]="Parent record %s was deleted"%recid
					self.putrecord(rec2,ctxid=ctxid,host=host)
					self.pcunlink(recid,i,ctxid=ctxid,host=host)


		#@txn
		@publicmethod
		def addcomment(self, recid, comment, ctxid=None, host=None):
			rec = self.getrecord(recid, ctxid=ctxid, host=host)
			rec.addcomment(comment)
			self.putrecord(rec, ctxid=ctxid, host=host)
			return self.getrecord(recid, ctxid=ctxid, host=host)["comments"]




		# merge with getuser?
		@publicmethod
		def getgroupdisplayname(self, groupname, ctxid=None, host=None):
			groupnames = {"-3":"All Authenticated Users", "-4":"Anonymous Access", "-1":"Database Administrator"}
			return groupnames[str(username)]



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



		# ian: this might be helpful
		# e.g.: __filtervartype(136, ["user","userlist"])
		@publicmethod
		def filtervartype(self, recs, vts, params=None, paramdefs=None, filt=1, flat=0, returndict=0, ignore=None, ctxid=None, host=None):

			if not recs:
				return [None]

			if not paramdefs: paramdefs={}
			recs2=[]

			# process recs arg into recs2 records, process params by vartype, then return either a dict or list of values; ignore those specified
			ol=0
			if isinstance(recs,(int,Record)):
				ol=1
				recs=[recs]

			if not hasattr(vts,"__iter__"):
				vts=[vts]

			if not hasattr(ignore,"__iter__"):
				ignore=[ignore]
			ignore=set(ignore)

			recs2.extend(filter(lambda x:isinstance(x,Record),recs))
			recs2.extend(self.getrecord(filter(lambda x:isinstance(x,int),recs),ctxid=ctxid,host=host,filt=filt))

			if params:
				paramdefs=self.getparamdefs(params)

			if not paramdefs:
				pds=set(reduce(lambda x,y:x+y,map(lambda x:x.keys(),recs2)))
				paramdefs.update(self.getparamdefs(pds))

			l = set([pd.name for pd in paramdefs.values() if pd.vartype in vts]) - ignore
			#l = set(map(lambda x:x.name, filter(lambda x:x.vartype in vts, paramdefs.values()))) - ignore
			##l = set(filter(lambda x:x.vartype in vts, paramdefs.values())) - ignore

			if returndict or ol:
				ret={}
				for rec in recs2:
					re=[rec.get(pd) or None for pd in l]
					if flat:
						re=set(self.__flatten(re))-set([None])
					ret[rec.recid]=re

				if ol: return ret.values()[0]
				return ret

			# if not returndict
			re=[[rec.get(pd) for pd in l if rec.get(pd)] for rec in recs2]
			#re=filter(lambda x:x,map(lambda x:[x.get(pd) or None for pd in l],a))
			if flat:
				return set(self.__flatten(re))-set([None])
			return re




		@publicmethod
		def getuserdisplayname(self, username, lnf=1, perms=0, filt=1, ctxid=None, host=None):
			"""Return the full name of a user from the user record; include permissions param if perms=1"""

			namestoget = []
			ret = {}

			ol=0
			if isinstance(username, basestring):
				ol=1
			if isinstance(username, (basestring, int, Record)):
				username=[username]

			namestoget=[]
			namestoget.extend(filter(lambda x:isinstance(x,basestring),username))

			vts=["user","userlist"]
			if perms:
				vts.append("acl")

			recs=[]
			recs.extend(filter(lambda x:isinstance(x,Record), username))
			recs.extend(self.getrecord(filter(lambda x:isinstance(x,int), username),filt=filt,ctxid=ctxid,host=host))

			if recs:
				namestoget.extend(self.filtervartype(recs, vts, flat=1, ctxid=ctxid, host=host))
				# ... need to parse comments since it's special
				namestoget.extend(reduce(lambda x,y: x+y, [[i[0] for i in rec["comments"]] for rec in recs]))

			namestoget=set(namestoget)

			users = self.getuser(namestoget,filt=filt,ctxid=ctxid,host=host).items()
			users = filter(lambda x:x[1].record!=None, users)
			users = dict(users)

			recs = self.getrecord([user.record for user in users.values()],filt=filt,ctxid=ctxid,host=host)
			recs = dict([(i.recid,i) for i in recs])

			for k,v in users.items():
				ret[k] = self.__formatusername(k,recs[v.record],lnf=lnf)

			if len(ret.keys())==0:
				return {}
			if ol:
				return ret.values()[0]

			return ret




		def __formatusername(self, username, u, lnf=1):
			if u["name_first"] and u["name_middle"] and u["name_last"]:
				if lnf:
					uname = "%s, %s %s" % (u["name_last"], u["name_first"], u["name_middle"])
				else:
					uname = "%s %s %s" % (u["name_first"], u["name_middle"], u["name_last"])

			elif u["name_first"] and u["name_last"]:
				if lnf:
					uname = "%s, %s" % (u["name_last"], u["name_first"])
				else:
					uname = "%s %s" % (u["name_first"], u["name_last"])

			elif u["name_last"]:
				uname = u["name_last"]

			elif u["name_first"]:
				uname = u["name_first"]

			else:
				return username

			return uname



		@publicmethod
		def gettime(self, ctxid=None, host=None):
			return time.strftime(TIMESTR)



		#@txn
		@publicmethod
		@g.debug.debug_func
		def putrecord(self, recs, filt=1, warning=0, ctxid=None, host=None, txn=None):
			"""commits a record"""
			# input validation for __putrecord

			ctx = self.__getcontext(ctxid,host)

			if warning and not ctx.checkadmin():
				raise Exception,"Only administrators may bypass record validation"

			# filter input for dicts/records
			ol = 0
			if isinstance(recs,(Record,dict)):
				ol = 1
				recs = [recs]

			dictrecs = filter(lambda x:isinstance(x,dict), recs)
			recs.extend(map(lambda x:Record(x, ctx=ctx), dictrecs))
			recs = filter(lambda x:isinstance(x,Record), recs)

			# new records and updated records
			updrecs = filter(lambda x:x.recid != None, recs)
			newrecs = filter(lambda x:x.recid == None, recs)

			# check original records for write permission
			orecs = self.getrecord([rec.recid for rec in updrecs], ctxid=ctx.ctxid, host=ctx.host, filt=0)
			orecs = set(map(lambda x:x.recid, filter(lambda x:x.commentable(), orecs)))

			permerror = set([rec.recid for rec in updrecs]) - orecs
			if permerror:
				raise SecurityError,"No permission to write to records: %s"%permerror

			if newrecs and not ctx.checkcreate():
				raise SecurityError,"No permission to create records"

			ret = self.__putrecord(recs, warning=warning, ctx=ctx, txn=txn)

			if ol: return ret[0]
			return ret



		# def __putrecord(self, recs, warning=0, validate=1, log=1, forceupdate=0, ctx=None, txn=None):
		#
		# 	# i might change orecs in the future; for now it's a bit of a kludge to deal with new recs
		# 	nrecs, nrels = self.__putrecord_checknew(newrecs, ctx=ctx, txn=txn)
		# 	urecs, urels = self.__putrecord_check(updrecs, warning=warning, validate=validate, forceupdate=forceupdate, ctx=ctx, txn=txn)
		#
		# 	# commit
		# 	crecs = self.__commit_records(nrecs + urecs, updrels=nrels + urels, ctx=ctx, txn=txn)
		#
		# 	return crecs2



		# def __putrecord_checknew(self, newrecs, setcreator=1, ctx=None, txn=None):
		# 	# preprocess for __putrecordcheck, which itself is a filter to check before committing
		#
		# 	updrecs = []
		# 	orecs = {}
		#
		# 	# preprocess before putrecord
		# 	for offset,rec in enumerate(newrecs):
		#
		# 		recid = -1 * (offset + 1)
		#
		# 		if self.__importmode or not setcreator:
		# 			t = rec.get("creaiontime")
		# 			creator = rec.get("creator")
		# 		else:
		# 			t = self.gettime()
		# 			creator = ctx.user
		#
		# 		# set uneditable fields
		# 		rec._Record__creator = creator
		# 		rec._Record__creationtime = t
		# 		rec.recid = recid
		# 		rec.adduser(3, creator)
		#
		# 		updrecs.append(rec)
		#
		# 	return self.__putrecord_check(updrecs, warning=0, validate=1, log=0, forceupdate=1, ctx=ctx, txn=txn)


		def __putrecord_getupdrels(self, updrecs):
			# get parents/children to update relationships
			r = []
			for updrec in updrecs:
				_p = updrec.get("parents") or []
				_c = updrec.get("children") or []
				if _p:
					r.extend([(i,updrec.recid) for i in _p])
					del updrecs["parents"]
				if _c:
					r.extend([(updrec.recid,i) for i in _c])
					del updrecs["children"]
			return r



		# def __putrecord_getorecs(self, updrecs, ctx=None):
		# 	orecs = {}
		#
		# 	for updrec in updrecs:
		# 		try:
		# 			orec = self.__records[updrec.recid]
		# 			orec.setContext(ctx)
		# 			#orec = self.getrecord(updrec.recid, ctxid=ctx.ctxid, host=ctx.host)
		#
		# 		except TypeError, inst:
		# 			# new record... assign temp recid
		# 			orec = Record()
		# 			orec.setContext(ctx)
		# 			orec.rectype = updrec.rectype
		# 			orec.recid = updrec.recid
		# 			if self.__importmode:
		# 				orec._Record__creator = updrec["creator"]
		# 				orec._Record__creationtime = updrec["creationtime"]
		#
		# 		orecs[updrec.recid] = orec
		#
		# 	return orecs



		def __putrecord(self, updrecs, warning=0, validate=1, newrecord=0, log=1, ctx=None, txn=None):
			# process before committing
			# extended validation...

			if len(updrecs) == 0:
				return [], []

			crecs = []
			updrels = []
			param_immutable = set(["recid","rectype","creator","creationtime"])
			param_special = param_immutable | set(["comments","permissions"])

			# assign temp recids to new records
			for offset,rec in enumerate(filter(lambda x:x.recid == None, updrecs)):
				rec.recid = -1 * (offset + 100)

			#print "ok, assigned temp recids"
			#print [rec.recid for rec in updrecs]

			updrels = self.__putrecord_getupdrels(updrecs)

			# preprocess: copy updated record into original record (updrec -> orec)
			for updrec in updrecs:

				t = self.gettime()
				recid = updrec.recid

				try:
					orec = self.__records[updrec.recid]
					orec.setContext(ctx)
				except TypeError, inst:
					orec = self.newrecord(updrec.rectype, ctxid=ctx.ctxid, host=ctx.host)
					orec.recid = updrec.recid

					if self.__importmode:
						orec._Record__creator = updrec["creator"]
						orec._Record__creationtime = updrec["creationtime"]

					if recid > 0:
						raise Exception, "Cannot update non-existent record %s"%recid


				# compare to original record
				cp = orec.changedparams(updrec) - param_immutable

				if not cp and not orec.recid < 0:
					g.debug("LOG_INFO","putrecord: No changes for record %s, skipping"%recid)
					continue


				# add new comments; already checked for comment level security...
				for i in updrec["comments"]:
					if i not in orec._Record__comments:
						orec._Record__comments.append(i)
				# ian todo: need to check for param updates from comments here...


				# copy updates to orec, log changes
				if cp - param_special and not orec.writable():
					raise SecurityError, "Cannot change params in %s"%recid

				for param in cp - param_special:
					if log:
						orec._Record__comments.append((ctx.user, t, u"LOG: %s updated. was: %s" % (recid, orec[param])))
						#% (param, orec[param]), param, orec[param]))
					orec[param] = updrec[param]


				if "permissions" in cp:
					if not orec.isowner():
						raise SecurityError, "Cannot change permissions for %s"%recid
					orec["permissions"] = updrec["permissions"]


				if not self.__importmode:
					orec["modifytime"] = t
					orec["modifyuser"] = ctx.user


				if validate:
					orec.validate(warning=warning, params=cp)

				crecs.append(orec)

			# return records to commit, copies of the originals for indexing, and any relationships to update
			#return crecs, updrels

			return self.__commit_records(crecs, updrels, ctx=ctx)


		# commit
		#@write	#self.__records, self.__recorddefbyrec, self.__recorddefindex, self.__timeindex
		# also, self.fieldindex* through __commit_paramindex(), self.__secrindex through __commit_secrindex
		def __commit_records(self, crecs, updrels=[], ctx=None, txn=None):

			print "commiting %s recs"%(len(crecs))

			recmap = {}
			rectypes = {}
			timeupdate = {}
			newrecs = filter(lambda x:x.recid < 0, crecs)

			# first, get index updates
			indexupdates = self.__reindex_params(crecs, ctx=ctx)
			secr_addrefs, secr_removerefs = self.__reindex_security(crecs, ctx=ctx)
			timeupdate = self.__reindex_time(crecs, ctx=ctx)

			#@begin
			txn = self.txncheck(txn)

			# this needs a lock.
			if newrecs:
				baserecid = self.__records.get(-1, txn=txn)
				self.__records.set(-1, baserecid + len(newrecs))

			# add recids to new records, create map from temp recid, setup index
			for offset, newrec in enumerate(newrecs):
				oldid = newrec.recid
				newrec.recid = offset + baserecid
				recmap[oldid] = newrec.recid
				if not rectypes.has_key(newrec.rectype):
					rectypes[newrec.rectype]=[]
				rectypes[newrec.rectype].append(newrec.recid)


			if filter(lambda x:x.recid < 0, crecs):
				raise Exception, "Some new records were not given real recids; giving up"



			# This actually stores the record in the database
			for crec in crecs:
				self.__records.set(crec.recid, crec, txn=txn)
				#g.debug("LOG_COMMIT","Commit: self.__records.set: %s"%crec.recid)



			# New record RecordDef indexes
			for rec in newrecs:
				try:
					self.__recorddefbyrec.set(rec.recid, rec.rectype, txn=txn)
					#g.debug("LOG_COMMIT","Commit: self.__recorddefbyrec.set: %s, %s"%(rec.recid, rec.rectype))

				except Exception, inst:
					g.debug("LOG_ERR", "Could not update recorddefbyrec: record %s, rectype %s (%s)"%(rec.recid, rec.rectype, inst))


			for rectype,recs in rectypes.items():
				try:
					self.__recorddefindex.addrefs(rectype, recs, txn=txn)
					#g.debug("LOG_COMMIT","Commit: self.__recorddefindex.addrefs: %s, %s"%(rectype,recs))

				except Exception, inst:
					g.debug("LOG_ERR", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype,recs,inst))


			# Param index
			for param, updates in indexupdates.items():
				self.__commit_paramindex(param, updates[0], updates[1], recmap=recmap, ctx=ctx, txn=txn)


			# Security index
			self.__commit_secrindex(secr_addrefs, secr_removerefs, recmap=recmap, ctx=ctx, txn=txn)


			# Time index
			for recid,time in timeupdate.items():
				try:
					self.__timeindex.set(recmap.get(recid,recid), time, txn=txn)
					#g.debug("LOG_COMMIT","Commit: self.__timeindex.set: %s, %s"%(recmap.get(recid,recid), time))

				except Exception, inst:
					g.debug("LOG_ERR", "Could not update time index: key %s, value %s (%s)"%(recid,time,inst))


			# Create pc links
			for link in updrels:
				try:
					self.pclink(recmap.get(link[0],link[0]),recmap.get(link[1],link[1]))
				except:
					g.debug("LOG_ERR", "Could not link %s to %s"%(recmap.get(link[0],link[0]),recmap.get(link[1],link[1])))

			self.txncommit(txn)
			#@end

			return crecs


		#@write #self.__secrindex
		def __commit_secrindex(self, addrefs, removerefs, recmap={}, ctx=None, txn=None):

			txn = self.txncheck(txn)

			# Security index
			for user, recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.__secrindex.addrefs(user, recs, txn=txn)
						g.debug("LOG_COMMIT","Commit: self.__secrindex.addrefs: %s, %s"%(user, recs))
				except Exception, inst:
					g.debug("LOG_ERR", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))

			for user, recs in removerefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						self.__secrindex.removerefs(user, recs, txn=txn)
						g.debug("LOG_COMMIT","Commit: secrindex.removerefs: user %s, recs %s"%(user, recs))
				except Exception, inst:
					g.debug("LOG_ERR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))

			self.txncommit(txn)



		#@write #self.__fieldindex*
		def __commit_paramindex(self, param, addrefs, delrefs, recmap={}, ctx=None, txn=None):
			"""commit param updates"""

			# addrefs = upds[0], delrefs = upds[1]
			if not addrefs and not delrefs:
				return
				#continue

			try:
				ind = self.__getparamindex(param)
				if ind == None:
					raise Exception, "Index was None"
			except Exception, inst:
				g.debug("LOG_ERR","Could not open param index: %s (%s)"%param, inst)
				return

			for newval,recs in addrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs: ind.addrefs(newval, recs, txn=txn)
					#g.debug("LOG_COMMIT","Commit: param index %s.addrefs: '%s', %s"%(param, newval, recs))
				except Exception, inst:
					g.debug("LOG_ERR", "Could not update param index %s: addrefs %s, records %s (%s)"%(param,newval,recs,inst))


			for oldval,recs in delrefs.items():
				recs = map(lambda x:recmap.get(x,x), recs)
				try:
					if recs:
						ind.removerefs(oldval, recs, txn=txn)
						#g.debug("LOG_COMMIT","Commit: param index %s.removerefs: '%s', %s"%(param, oldval, recs))
				except Exception, inst:
					g.debug("LOG_ERR", "Could not update param index %s: removerefs %s, records %s (%s)"%(param,oldval,recs,inst))




		# index update methods
		def __reindex_params(self, updrecs, ctx=None, txn=None):
			"""update param indices"""

			ind = dict([(i,[]) for i in self.__paramdefs.keys()])
			indexupdates = {}
			unindexed = set(["recid","rectype","comments","permissions"])

			for updrec in updrecs:
				recid = updrec.recid

				# this is a fix for proper indexing of new records...
				try: orec = self.__records[recid]
				except:	orec = {}

				cp = updrec.changedparams(orec)

				if not cp:
					continue

				for param in set(cp) - unindexed:
					ind[param].append((recid,updrec.get(param),orec.get(param)))

			# Now update indices; filter because most param indexes have no changes
			for key,v in filter(lambda x:x[1],ind.items()):
				indexupdates[key] = self.__reindex_param(key,v)

			return indexupdates



		def __reindex_param(self, key, items, txn=None):
			# items format:
			# [recid, newval, oldval]

			pd = self.__paramdefs[key]
			addrefs = {}
			delrefs = {}

			if pd.name in ["recid","comments","permissions"]:
				return addrefs, delrefs

			if pd.vartype not in self.indexablevartypes:
				return addrefs, delrefs

			# remove oldval=newval; strip out wrong keys
			items = filter(lambda x:x[1] != x[2], items)

			if pd.vartype == "text":
				return self.__reindex_paramtext(key,items)

			addrefs = dict([[i,set()] for i in set([i[1] for i in items])])
			delrefs = dict([[i,set()] for i in set([i[2] for i in items])])
			for i in items:
				addrefs[i[1]].add(i[0])
				delrefs[i[2]].add(i[0])

			if addrefs.has_key(None): del addrefs[None]
			if delrefs.has_key(None): del delrefs[None]

			return addrefs, delrefs



		def __reindex_paramtext(self, key, items, txn=None):
			addrefs={}
			delrefs={}

			for item in items:
				for i in self.__reindex_getindexwords(item[1]):
					if not addrefs.has_key(i):
						addrefs[i]=[]
					addrefs[i].append(item[0])

				for i in self.__reindex_getindexwords(item[2]):
					if not delrefs.has_key(i):
						delrefs[i]=[]
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


		def __reindex_getindexwords(self, value):
			if value==None: return []
			m = re.compile('[\s]([a-zA-Z]+)[\s]|([0-9][.0-9]+)')
			return set(map(lambda x:x[0] or x[1], m.findall(unicode(value).lower())))




		def __reindex_time(self, updrecs, ctx=None, txn=None):
			timeupdate = {}

			for updrec in updrecs:
				timeupdate[updrec.recid] = updrec.get("modifytime") or updrec.get("creationtime")

			return timeupdate



		#def __reindex_security(self, updrecs, orecs={}, ctx=None, txn=None):
		def __reindex_security(self, updrecs, ctx=None, txn=None):

			secrupdate = []
			addrefs = {}
			delrefs = {}

			for updrec in updrecs:
				recid = updrec.recid

				# this is a fix for proper indexing of new records...
				try: orec = self.__records[recid]
				except:	orec = {}

				if updrec.get("permissions") == orec.get("permissions"):
					continue

				nperms = set(reduce(operator.concat, updrec["permissions"]))
				operms = set(reduce(operator.concat, orec.get("permissions",[[]])))

				for user in nperms - operms:
					if not addrefs.has_key(user): addrefs[user] = []
					addrefs[user].append(recid)
				for user in operms - nperms:
					if not delrefs.has_key(user): delrefs[user] = []
					delrefs[user].append(recid)

			return addrefs, delrefs






		# ian: todo: improve newrecord/putrecord
		# ian: todo: allow to copy existing record
		@publicmethod
		def newrecord(self, rectype, init=0, inheritperms=None, ctxid=None, host=None):
			"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
			already exist)."""

			ctx = self.__getcontext(ctxid, host)


			rec = Record(ctx=ctx)
			#rec.setContext(ctx)

			# try to get the RecordDef entry, this still may fail even if it exists, if the
			# RecordDef is private and the context doesn't permit access
			t = self.getrecorddef(rectype, ctxid=ctxid, host=host)

			rec.recid = None
			rec.rectype = rectype # if we found it, go ahead and set up

			if init:
				rec.update(t.params)

			# ian
			if inheritperms != None:
				#if self.trygetrecord(inheritperms, ctxid=ctxid, host=host):
				try:
					prec = self.getrecord(inheritperms, ctxid=ctxid, host=host, filt=0)
					for level, users in enumerate(prec["permissions"]):
						rec.adduser(level, users)
					#n = []
					#for i in range(0, len(prec["permissions"])):
					#	n.append(prec["permissions"][i] + rec["permissions"][i])
					#rec["permissions"] = tuple(n)
				except Exception, inst:
					self.log("LOG_ERROR","newrecord: Error setting inherited permissions from record %s (%s)"%(inheritperms, inst))

			rec.adduser(3,ctx.user)

			return rec




		@publicmethod
		def getrecordschangetime(self, recids, ctxid=None, host=None):
			"""Returns a list of times for a list of recids. Times represent the last modification
			of the specified records"""
			#secure = set(self.getindexbycontext(ctxid=ctxid, host=host))
			#rid = set(recids)
			#rid -= secure
			recids = self.filterbypermissions(recids,ctxid=ctxid,host=host)
			if len(rid) > 0:
				raise Exception, "Cannot access records %s" % str(rid)

			try:
				ret = [self.__timeindex[i] for i in recids]
			except:
				raise Exception, "unindexed time on one or more recids"

			return ret



		@publicmethod
		def getindexbycontext(self, ctxid=None, host=None):
			"""This will return the ids of all records a context has permission to access as a set. Does include groups."""

			ctx = self.__getcontext(ctxid, host)

			if ctx.checkreadadmin():
				return set(range(self.__records[-1])) #+1)) ###Ed: Fixed an off by one error

			ret=set(self.__secrindex[ctx.user])
			for group in sorted(ctx.groups,reverse=True):
				ret |= set(self.__secrindex[group])
			#ret = set(self.__secrindex[ctx.user or -4])
			#if ctx.user != None:
			#		ret |= set(self.__secrindex[-3] or [])

			return ret



		@publicmethod
		def filterbypermissions(self, recids, ctxid=None, host=None):

			ctx = self.__getcontext(ctxid, host)

			if ctx.checkreadadmin():
				return set(recids)

			recids=set(recids)

			# this is usually the fastest
			# method 2
			#ret=set()
			ret=[]
			ret.extend(recids & set(self.__secrindex[ctx.user]))
			#ret |= recids & set(self.__secrindex[ctx.user])
			#recids -= ret
			for group in sorted(ctx.groups, reverse=True):
				#if recids:
				#print "searching group %s"%group
				#ret |= recids & set(self.__secrindex[group])
				#recids -= ret
				ret.extend(recids & set(self.__secrindex[group]))
			return set(ret)


			# method 3
			ret=[]
			for i in recids:
				try:
					self.getrecord(i,ctxid=ctxid,host=host)
					ret.append(i)
				except:
					pass
			return ret


			# method 4 (same as getindexbycontext)
			ret=set(self.__secrindex[ctx.user])
			for group in sorted(ctx.groups,reverse=True):
				ret |= set(self.__secrindex[group])
			return ret & recids


			# method 1
			ret=[]
			for recid in recids:
				if self.__secrindex.testref(ctx.user, recid):
					ret.append(recid)
					continue
				if self.__secrindex.testref(-3, recid):
					ret.append(recid)
					continue
				if self.__secrindex.testref(-4, recid):
					ret.append(recid)
					continue
				for group in ctx.groups:
					if self.__secrindex.testref(group, recid):
						ret.append(recid)
						continue
			return set(ret)





		# @publicmethod
		def trygetrecord(self, recid, dbid=0, ctxid=None, host=None):
			"""Checks to see if a record could be retrieved without actually retrieving it."""
			#self = db
			ctx = self.__getcontext(ctxid, host)
			if ctx.checkreadadmin():
					return 1
			# ian: fix anonymous access
			if self.__secrindex.testref(ctx.user, recid) : return 1		# user access
			if self.__secrindex.testref(-4, recid) : return 1 # anonymous access
			if self.__secrindex.testref(-3, recid) : return 1				# global read access
			for i in ctx.groups:
					try:
							if self.__secrindex.testref(i, recid) : return 1
					except:
							continue
			return 0



		# ian: improved!
		# ed: more improvments!
		@publicmethod
		def getrecord(self, recid, filt=1, dbid=0, ctxid=None, host=None):
			"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
			if dbid is 0, the current database is used."""
			#print "GETRECORD %s ctxid=%s %s"%(recid,ctxid,type(ctxid))

			ctx = self.__getcontext(ctxid, host)

			if (dbid != 0):
				raise NotImplementedError("External database support not yet available")
				#Ed Changed to NotimplementedError

			ol=0
			if not hasattr(recid,"__iter__"):
				ol=1
				recid=[int(recid)]

			#recl = map(lambda x:self.__records[int(x)], recid)
			recid = map(lambda x:int(x), recid)

			ret=[]
			for i in recid:
				try:
					rec = self.__records[i]
					rec.setContext(ctx)
					ret.append(rec)
				except SecurityError, e:
					# if filtering, skip record; else bubble (SecurityError) exception
					if filt: pass
					else: raise e
				except TypeError, e:
					if filt: pass
					else: raise KeyError, "No such record %s"%i

			if len(ret)==1 and ol: return ret[0]
			return ret




		@publicmethod
		def getparamvalue(self, paramname, recid, dbid=0, ctxid=None, host=None):
			paramname = str(paramname).lower()
			paramindex = self.__getparamindex(paramname, ctxid=ctxid, host=host)

			if hasattr(recid, '__iter__'):
				results = []
				for key in paramindex.keys():
					if set(paramindex[key]) & set(recid):
						results.insert(0, key)
				return results

			else:
				for key in paramindex.keys():
					if paramindex[key].pop() == recid:
						return key



		@publicmethod
		def secrecordadduser2(self, recids, level, users, reassign=0, ctxid=None, host=None, txn=None):
				ctx = self.__getcontext(ctxid, host)

				if not hasattr(recids,"__iter__"):
					recids = [recids]
				recids = set(recids)

				if not hasattr(users,"__iter__"):
					users = [users]
				users = set(users)

				# change child perms
				if recurse:
					for c in self.getchildren(recids, recurse=recurse, ctxid=ctxid, host=host).values():
						recids |= c

				# check users
				try:
					db.getuser(users, filt=0, ctxid=ctxid, host=host)
				except KeyError, inst:
					raise

				recs = self.getrecord(recids, filt=1, ctxid=ctxid, host=host)

				for rec in recs:
					rec.adduser(level, users, reassign=reassign)





		# ian todo: check this thoroughly; probably rewrite
		#@txn
		#@write #self.__records, self.__secrindex
		@publicmethod
		def secrecordadduser(self, usertuple, recid, recurse=0, reassign=0, mode="union", ctxid=None, host=None, txn=None):
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
								usertuple[i][j] = str(usertuple[i][j])
							except:
								raise ValueError, "Invalid permissions format; must be 4-tuple/list of tuple/list/string/int"


				# all users
				userset = set(self.getusernames(ctxid=ctxid, host=host)) | set((-5, -4, -3, -2, -1))


				# get a list of records we need to update
				if recurse > 0:
						trgt = self.getchildren(recid, ctxid=ctxid, host=host, recurse=recurse-1)
						trgt.add(recid)
				else:
					trgt = set((recid,))


				ctx = self.__getcontext(ctxid, host)
				if ctx.checkadmin():
						isroot = 1
				else:
						isroot = 0


				rec=self.getrecord(recid,ctxid=ctxid,host=host)
				if ctx.user not in rec["permissions"][3] and not isroot:
					raise SecurityError,"Insufficient permissions for record %s"%recid

				# this will be a dictionary keyed by user of all records the user has
				# just gained access to. Used for fast index updating
				secrupd = {}

				#print trgt
				#recs = self.getrecord(trgt, ctxid=ctxid, host=host)
				if not txn:
					txn = self.newtxn()


				for i in trgt:
						#try:
						rec = self.getrecord(i, ctxid=ctxid, host=host)						 # get the record to modify
						#except:
						#		 print "skipping %s"%i
						#		 continue

						# if the context does not have administrative permission on the record
						# then we just skip this record and leave the permissions alone
						# TODO: probably we should also check for groups in [3]

						if ctx.user not in rec["permissions"][3] and not ctx.checkadmin(): continue

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
								self.__records.set(rec.recid, rec, txn)

				for i in secrupd.keys() :
						self.__secrindex.addrefs(i, secrupd[i], txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()

				return rec["permissions"]


		# ian todo: see above
		#@txn
		#@write	#self.__records, self.__secrindex
		@publicmethod
		def secrecorddeluser(self, users, recid, recurse=0, ctxid=None, host=None):
				"""This removes permissions from a record. users is a username or tuple/list of
				of usernames to have no access to the record at all (will not affect group
				access). If recurse>0, the operation will be performed recursively
				on the specified record's children to a limited recursion depth. Note that
				this REMOVES all access permissions for the specified users on the specified
				record."""
				#self = db


				if isinstance(users, unicode) or isinstance(users, str) or isinstance(users, int):
						users = set([users])
				else:
						users = set(users)

				# get a list of records we need to update
				if recurse > 0:
						#if DEBUG: print "Del user recursive..."
						trgt = self.getchildren(recid, ctxid=ctxid, host=host, recurse=recurse - 1)
						trgt.add(recid)
				else : trgt = set((recid,))

				ctx = self.__getcontext(ctxid, host)
				users.discard(ctx.user)								 # user cannot remove his own permissions
				#if ctx.user=="root" or -1 in ctx.groups : isroot=1
				if ctx.checkadmin(): isroot = 1
				else: isroot = 0

				# this will be a dictionary keyed by user of all records the user has
				# just gained access to. Used for fast index updating
				secrupd = {}

				txn = self.newtxn()
				# update each record as necessary
				for i in trgt:
						try:
								rec = self.getrecord(i, ctxid=ctxid, host=host)						 # get the record to modify
						except: continue

						# if the user does not have administrative permission on the record
						# then we just skip this record and leave the permissions alone
						# TODO: probably we should also check for groups in [3]
						if (not isroot) and (ctx.user not in rec["permissions"][3]) : continue

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
								self.__records.set(rec.recid, rec, txn)

				for i in secrupd.keys() :
						self.__secrindex.removerefs(i, secrupd[i], txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()


		##########
		# internal view rendering functions
		##########


		import operator


		# ian: remove this?
		@publicmethod
		def getrecordrecname(self, rec, returnsorted=0, showrectype=0, ctxid=None, host=None):
			"""Render the recname view for a record."""

			recs=self.getrecord(rec,ctxid=ctxid,host=host,filt=1)
			ret=self.renderview(recs,viewtype="recname",ctxid=ctxid,host=host)
			recs=dict([(i.recid,i) for i in recs])

			if showrectype:
				for k in ret.keys():
					ret[k]="%s: %s"%(recs[k].rectype,ret[k])

			if returnsorted:
				sl=[(k,recs[k].rectype+" "+v.lower()) for k,v in ret.items()]
				return [(k,ret[k]) for k,v in sorted(sl, key=operator.itemgetter(1))]

			return ret




		@publicmethod
		def getrecordrenderedviews(self, recid, ctxid=None, host=None):
				"""Render all views for a record."""

				rec = self.getrecord(recid, ctxid=ctxid, host=host)
				recdef = self.getrecorddef(rec["rectype"], ctxid=ctxid, host=host)
				views = recdef.views
				views["mainview"] = recdef.mainview
				for i in views:
						views[i] = self.renderview(rec, viewdef=views[i], ctxid=ctxid, host=host)
				return views





		def __dicttable_view(self, params, paramdefs={}, mode="unicode"):
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
		def renderview(self, recs, viewdef=None, viewtype="dicttable", paramdefs={}, showmacro=True, mode="unicode", outband=0, ctxid=None, host=None):
			"""Render views"""

			# viewtype "dicttable" is builtin now.
			if recs != 0 and not recs:
				g.debug('NOT RECS!!!')
				return

			ol=0
			if not hasattr(recs,"__iter__") or isinstance(recs,Record):
				ol=1
				recs=[recs]

			if not isinstance(list(recs)[0],Record):
				recs=self.getrecord(recs,ctxid=ctxid,host=host,filt=1)


			builtinparams=["recid","rectype","comments","creator","creationtime","permissions"]
			builtinparamsshow=["recid","rectype","comments","creator","creationtime"]

			groupviews={}
			groups=set([rec.rectype for rec in recs])
			recdefs=self.getrecorddef(groups, ctxid=ctxid, host=host)

			if not viewdef:
				for i in groups:
					rd=recdefs.get(i)

					if viewtype=="mainview":
						groupviews[i]=rd.mainview

					elif viewtype=="dicttable":
						# move built in params to end of table
						par=[p for p in rd.paramsK if p not in builtinparams]
						par+=builtinparamsshow
						groupviews[i]=self.__dicttable_view(par,mode=mode)

					else:
						groupviews[i]=rd.views.get(viewtype, rd.name)

			else:
				groupviews[None]=viewdef


			if outband:
				for rec in recs:
					obparams=[i for i in rec.keys() if i not in recdefs[rec.rectype].paramsK and i not in builtinparams and rec.get(i) != None]
					if obparams:
						groupviews[rec.recid]=groupviews[rec.rectype] + self.__dicttable_view(obparams,mode=mode)
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
						elif match.group("macro"):
								m.append((match.group("macro"),match.group("macrosep"),match.group("macro1")))

				paramdefs.update(self.getparamdefs(pd,ctxid=ctxid,host=host))
				#print "PD:%s"%paramdefs.keys()

				# invariant to recid
				if n:
					for i in n:
						vrend=vtm.name_render(paramdefs.get(i[2]), mode=mode, db=self, ctxid=ctxid, host=host)
						vd=vd.replace(u"$#" + i[0] + i[1], vrend + i[1])
					groupviews[g1]=vd

				names[g1]=n
				values[g1]=v
				macros[g1]=m


			ret={}


			for rec in recs:
				if groupviews.get(rec.recid):
					key = rec.recid
				else:
					key = rec.rectype
				if viewdef: key = None
				a = groupviews.get(key)

				for i in values[key]:
					v=vtm.param_render(paramdefs[i[2]], rec.get(i[2]), mode=mode, db=self, ctxid=ctxid, host=host)
					a=a.replace(u"$$" + i[0] + i[1], v + i[1])

				if showmacro:
					for i in macros[key]:
						v=vtm.macro_render(i[2], "params", rec, mode=mode, db=self, ctxid=ctxid, host=host) #macro, params, rec, mode="unicode", db=None, ctxid=None, host=None
						a=a.replace(u"$@" + i[0], v + i[1])

				ret[rec.recid]=a

			g.debug('ol ->', ol)
			if ol:
				return ret.values()[0]
			return ret





		###########
		# The following routines for xmlizing aspects of the database are very simple,
		# and also quite verbose. That is a lot of this could
		# be done with a function for, say, xmlizing a dictionary. However, this explicit approach
		# should be significantly faster, a key point if dumping an entire database
		###########


		def getparamdefxml(self, names=None, host=None):
				"""Returns XML describing all, or a subset of the existing paramdefs"""

				ret = []
				if names == None : names = self.getparamdefnames(ctxid=ctxid, host=host)

				# these lines are long for better speed despite their ugliness
				for i in names:
						pd = self.getparamdef(i, ctxid=ctxid, host=host)
						# This should probably be modified to make sure all included strings are XML-safe
						ret.append('<paramdef name="%s">\n	<vartype value="%s"/>\n	 <desc_short value="%s"/>\n	 <desc_long value="%s"/>\n' % (pd.name, pd.vartype, escape2(pd.desc_short), escape2(pd.desc_long)))
						ret.append('	<property value="%s"/>\n	<defaultunits value="%s"/>\n	<creator value="%s"/>\n	 <creationtime value="%s"/>\n	 <creationdb value="%s"/>\n' % (pd.property, escape2(pd.defaultunits), pd.creator, pd.creationtime, pd.creationdb))

						if pd.choices and len(pd.choices) > 0 :
								ret.append('	<choices>\n')
								for j in pd.choices:
										ret.append('	<choice>%s</choice>\n' % escape2(j))
								ret.append('	</choices>\n')

						ch = self.getchildren(i, keytype="paramdef", ctxid=ctxid, host=host)
						if ch and len(ch) > 0 :
								ret.append('	<children>\n')
								for j in ch:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</children>\n')

						csn = self.getcousins(i, keytype="paramdef", ctxid=ctxid, host=host)
						if csn and len(csn) > 0 :
								ret.append('	<cousins>\n')
								for j in csn:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</cousins>\n')
						ret.append('</paramdef>\n')

				return "".join(ret)


		# ian: moved host to end
		def getrecorddefxml(self, names=None, ctxid=None, host=None):
				"""Returns XML describing all, or a subset of existing recorddefs"""
				ret = []
				if names == None : names = self.getrecorddefnames(ctxid=ctxid, host=host)

				for i in names:
						try: rd = self.getrecorddef(i, ctxid=ctxid, host=host)
						except: continue

						ret.append('<recorddef name="%s">\n	 <private value="%d"/>\n	<owner value="%s"/>\n	 <creator value="%s"/>\n	<creationtime value="%s"/>\n	<creationdb value="%s"/>\n' % (i, rd.private, rd.owner, rd.creator, rd.creationtime, rd.creationdb))
						ret.append('	<mainview>%s</mainview>\n' % escape2(rd.mainview))

						if rd.params and len(rd.params) > 0 :
								ret.append('	<params>\n')
								for k, v in rd.params.items():
										if v == None : ret.append('		 <param name="%s"/>\n' % k)
										else: ret.append('		<param name="%s" default="%s"/>\n' % (k, v))
								ret.append('	</params>\n')

						if rd.views and len(rd.views) > 0 :
								ret.append('	<views>\n')
								for k, v in rd.views.items():
										ret.append('		<view name="%s">%s</view>\n' % (k, escape2(v)))
								ret.append('	</views>\n')

						ch = self.getchildren(i, keytype="recorddef", ctxid=ctxid, host=host)
						if len(ch) > 0 :
								ret.append('	<children>\n')
								for j in ch:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</children>\n')

						csn = self.getcousins(i, keytype="recorddef", ctxid=ctxid, host=host)
						if len(ch) > 0 :
								ret.append('	<cousins>\n')
								for j in csn:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</cousins>\n')

						ret.append('</recorddef>\n')

				return "".join(ret)


		# ian: moved host to end
		def getuserxml(self, names=None, ctxid=None, host=None):
				"""Returns XML describing all, or a subset of existing users"""
				qc = {'"':'&quot'}
				ret = []
				if names == None : names = self.getusernames(ctxid=ctxid, host=host)

				for i in names:
						try: u = self.getuser(i, ctxid=ctxid, host=host)
						except: continue
						ret.append('<user name="%s">\n' % i)
						ret.append('	<password value="%s"/>\n	<disabled value="%d"/>\n	<privacy value="%d"/>\n	 <creator value="%s"/>\n	<creationtime value="%s"/>\n' % (u.password, u.disabled, u.privacy, u.creator, u.creationtime))
						ret.append('	<firstname value="%s"/>\n	 <midname value="%s"/>\n	<lastname value="%s"/>\n	<institution value="%s"/>\n' % (escape2(u.name[0]), escape2(u.name[1]), escape2(u.name[2]), escape2(u.institution)))
						ret.append('	<department value="%s"/>\n	<address>%s</address>\n	 <city value="%s"/>\n	 <state value="%s"/>\n	<zipcode value="%s"/>\n' % (escape2(u.department), escape2(u.address), escape2(u.city), u.state, u.zipcode))
						ret.append('	<country value="%s"/>\n	 <webpage value="%s"/>\n	<email value="%s"/>\n	 <altemail value="%s"/>\n' % (u.country, escape2(u.webpage), escape2(u.email), escape2(u.altemail)))
						ret.append('	<phone value="%s"/>\n	 <fax value="%s"/>\n	<cellphone value="%s"/>\n' % (escape2(u.phone), escape2(u.fax), escape2(u.cellphone)))
						if len(u.groups) > 0:
								ret.append('	<groups>\n')
								for j in u.groups:
										ret.append('		<group value="%s"/>\n' % j)
								ret.append('	</groups>\n')
						ret.append('/user\n')

				return "".join(ret)



		# ian: moved host to end
		def getworkflowxml(self, wfid=None, ctxid=None, host=None):
				"""Returns XML describing all, or a subset of workflows"""
				print "WARNING getworkflowxml unimplemented"
				return ""



		# ian: moved host to end
		def getrecordxml(self, recids=None, ctxid=None, host=None):
				"""Returns XML describing all, or a subset of records"""
				qc = {'"':'&quot'}
				ret = []
				if recids == None : recids = self.getindexbycontext(ctxid=ctxid, host=host)

				for i in recids:
						try: rec = self.getrecord(i, ctxid=ctxid, host=host)
						except: continue

						ret.append('<record name="%s" dbid="%s" rectype="%s">\n' % (i, str(rec.dbid), rec.rectype))
						ret.append('	<creator value="%s"/>\n	 <creationtime value="%s"/>\n' % (rec["creator"], rec["creationtime"]))

						ret.append('	<permissions value="read">\n')
						for j in rec["permissions"][0]:
								if isinstance(j, int) : ret.append('		 <group value="%d"/>\n' % j)
								else : ret.append('		 <user value="%s"/>\n' % str(j))
						ret.append('	</permissions>\n')

						ret.append('	<permissions value="comment">\n')
						for j in rec["permissions"][1]:
								if isinstance(j, int) : ret.append('		 <group value="%d"/>\n' % j)
								else : ret.append('		 <user value="%s"/>\n' % str(j))
						ret.append('	</permissions>\n')

						ret.append('	<permissions value="write">\n')
						for j in rec["permissions"][2]:
								if isinstance(j, int) : ret.append('		 <group value="%d"/>\n' % j)
								else : ret.append('		 <user value="%s"/>\n' % str(j))
						ret.append('	</permissions>\n')

						pk = rec.getparamkeys()
						for j in pk:
								ret.append('	<param name="%s" value="%s"/>\n' % (j, str(rec[j])))

						for j in rec["comments"]:
								ret.append('	<comment user="%s" date="%s">%s</comment>\n' % (j[0], j[1], escape2(j[2])))

						ch = self.getchildren(i, keytype="record", ctxid=ctxid, host=host)
						if len(ch) > 0 :
								ret.append('	<children>\n')
								for j in ch:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</children>\n')

						csn = self.getcousins(i, keytype="record", ctxid=ctxid, host=host)
						if len(csn) > 0 :
								ret.append('	<cousins>\n')
								for j in csn:
										ret.append('		<link name="%s"/>\n' % j)
								ret.append('	</cousins>\n')

						ret.append('</record>')

				return "".join(ret)



		def getasxml(self, body, host=None):
				return '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generated by EMEN2 -->\n<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n%s\n</xs:schema>' % body


		def _backup(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctxid=None, host=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""

				#if user!="root" :
				ctx = self.__getcontext(ctxid, host)
				if not ctx.checkadmin():
						raise SecurityError, "Only root may backup the database"


				print 'backup has begun'
				#user,groups=self.checkcontext(ctxid,host)
				user = ctx.user
				groups = ctx.groups

				if users == None: users = self.__users.keys()
				if paramdefs == None: paramdefs = set(self.__paramdefs.keys())
				if recorddefs == None: recorddefs = set(self.__recorddefs.keys())
				if records == None: records = set(range(0, self.__records[ - 1]))
				if workflows == None: workflows = set(self.__workflow.keys())
				if bdos == None: bdos = set(self.__bdocounter.keys())
				if isinstance(records, list) or isinstance(records, tuple): records = set(records)

				if outfile == None:
						out = open(self.path + "/backup.pkl", "w")
				else:
						out = open(outfile, "w")

				print 'backup file opened'
				# dump users
				for i in users: dump(self.__users[i], out)
				print 'users dumped'
				# dump workflow
				for i in workflows: dump(self.__workflow[i], out)
				print 'workflows dumped'

				# dump binary data objects
				dump("bdos", out)
				bd = {}
				for i in bdos: bd[i] = self.__bdocounter[i]
				dump(bd, out)
				bd = None
				print 'bdos dumped'

				# dump paramdefs and tree
				for i in paramdefs: dump(self.__paramdefs[i], out)
				ch = []
				for i in paramdefs:
						c = set(self.__paramdefs.children(i))
#						 c=set([i[0] for i in c])
						c &= paramdefs
						c = tuple(c)
						ch += ((i, c),)
				dump("pdchildren", out)
				dump(ch, out)
				print 'paramdefs dumped'

				ch = []
				for i in paramdefs:
						c = set(self.__paramdefs.cousins(i))
						c &= paramdefs
						c = tuple(c)
						ch += ((i, c),)
				dump("pdcousins", out)
				dump(ch, out)
				print 'pdcousins dumped'

				# dump recorddefs and tree
				for i in recorddefs: dump(self.__recorddefs[i], out)
				ch = []
				for i in recorddefs:
						c = set(self.__recorddefs.children(i))
#						 c=set([i[0] for i in c])
						c &= recorddefs
						c = tuple(c)
						ch += ((i, c),)
				dump("rdchildren", out)
				dump(ch, out)
				print 'rdchildren dumped'

				ch = []
				for i in recorddefs:
						c = set(self.__recorddefs.cousins(i))
						c &= recorddefs
						c = tuple(c)
						ch += ((i, c),)
				dump("rdcousins", out)
				dump(ch, out)
				print 'rdcousins dumped'

				# dump actual database records
				print "Backing up %d/%d records" % (len(records), self.__records[ - 1])
				for i in records:
						dump(self.__records[i], out)
				print 'records dumped'

				ch = []
				for i in records:
						c = [x for x in self.__records.children(i) if x in records]
						c = tuple(c)
						ch += ((i, c),)
				dump("recchildren", out)
				dump(ch, out)
				print 'rec children dumped'

				ch = []
				for i in records:
						c = set(self.__records.cousins(i))
						c &= records
						c = tuple(c)
						ch += ((i, c),)
				dump("reccousins", out)
				dump(ch, out)
				print 'rec cousins dumped'

				out.close()

		def _backup2(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctxid=None, host=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""
				import demjson

				#if user!="root" :
				ctx = self.__getcontext(ctxid, host)
				if not self.checkadmin(ctx):
						raise SecurityError, "Only root may backup the database"


				print 'backup has begun'
				#user,groups=self.checkcontext(ctxid,host)
				user = ctx.user
				groups = ctx.groups

				return demjson.encode(self.__users.values())

		#@txn
		#@write #everything...
		def restore(self, restorefile=None, ctxid=None, host=None):
				"""This will restore the database from a backup file. It is nondestructive, in that new items are
				added to the existing database. Naming conflicts will be reported, and the new version
				will take precedence, except for Records, which are always appended to the end of the database
				regardless of their original id numbers. If maintaining record id numbers is important, then a full
				backup of the database must be performed, and the restore must be performed on an empty database."""

				if not self.__importmode:
					self.LOG(3, "WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
					return

				self.LOG(4, "Begin restore operation")

				ctx = self.__getcontext(ctxid, host)
				user = ctx.user
				groups = ctx.groups

				if not ctx.checkadmin():
						raise SecurityError, "Database restore requires admin access"

				if os.access(str(restorefile), os.R_OK):
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
				txn = None
				nel = 0

				recblock=[]
				#print "begin restore"
				recblocklength=10000

				while (1):

					try:
						r = load(fin)
					except Exception, inst:
						print inst
						break

					# new transaction every 100 elements
					# if nel%100==0 :
						# if txn : txn.commit()
						# txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)

					nel += 1
					if txn:
						txn.commit()
					elif nel % 500 == 0:
						# print "SYNC:",self.__dbenv.lock_stat()["nlocks"]," ... ",
						DB_syncall()
						# print self.__dbenv.lock_stat()["nlocks"]
						# time.sleep(10.0)
						# print self.__dbenv.lock_stat()["nlocks"]

					txn = self.newtxn()

					commitrecs=0

					# insert and renumber record
					if isinstance(r, Record):
						#print "record: %s"%r.recid
						recblock.append(r)
						if len(recblock) >= recblocklength:
							commitrecs=1
					else:
						commitrecs=1


					if commitrecs:
						# remove recids to put as new records...
						oldids = [rec.recid for rec in recblock]
						for i in recblock:
							i.recid = None

						newrecs = self.__putrecord(recblock, warning=1, newrecord=1, ctx=ctx)
						for oldid,newrec in zip(oldids,newrecs):
							recmap[oldid] = newrec.recid
							#print "Recmap %s -> %s"%(oldid, newrec.recid)
							if oldid != newrec.recid:
								print "Warning: recid %s changed to %s"%(oldid,newrec.recid)
						recblock=[]
						#sys.exit(0)


					# insert User
					if isinstance(r, User):
						print "user: %s"%r.username
						#self.__commit_users([r], ctx=ctx, txn=txn)
						if self.__users.has_key(r.username, txn):
							print "Duplicate user ", r.username
							self.__users.set(r.username, r, txn)
						else:
							self.__users.set(r.username, r, txn)


					# insert Workflow
					elif isinstance(r, WorkFlow):
						print "workflow: %s"%r.wfid
						self.__workflow.set(r.wfid, r, txn)


					# insert paramdef
					elif isinstance(r, ParamDef):
						print "paramdef: %s"%r.name
						#self.__commit_paramdefs([r], ctx=ctx, txn=txn)
						r.name = r.name.lower()
						if self.__paramdefs.has_key(r.name, txn):
							print "Duplicate paramdef ", r.name
							self.__paramdefs.set(r.name, r, txn)
						else :
							self.__paramdefs.set(r.name, r, txn)

					# insert recorddef
					elif isinstance(r, RecordDef):
						print "recorddef: %s"%r.name
						#self.__commit_recorddefs([r], ctx=ctx, txn=txn)
						r.name = r.name.lower()
						if self.__recorddefs.has_key(r.name, txn):
							print "Duplicate recorddef ", r.name
							self.__recorddefs.set(r.name, r, txn)
						else:
							self.__recorddefs.set(r.name, r, txn)


					elif isinstance(r, str):
						print "btree type: %s"%r
						if r == "bdos" :
							print "bdo"
							# read the dictionary of bdos
							rr = load(fin)
							for i, d in rr.items():
								self.__bdocounter.set(i, d, txn)

						elif r == "pdchildren" :
							print "pdchildren"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for p, cl in rr:
								for c in cl:
									self.__paramdefs.pclink(p, c, txn)

						elif r == "pdcousins" :
							print "pdcousins"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for a, bl in rr:
								for b in bl:
									self.__paramdefs.link(a, b, txn)

						elif r == "rdchildren" :
							print "rdchildren"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for p, cl in rr:
								for c in cl:
									self.__recorddefs.pclink(p, c, txn)

						elif r == "rdcousins" :
							print "rdcousins"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for a, bl in rr:
								for b in bl:
									self.__recorddefs.link(a, b, txn)

						elif r == "recchildren" :
							print "recchildren"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for p, cl in rr:
								for c in cl:
									if isinstance(c, tuple):
										print "Invalid (deprecated) named PC link, database restore will be incomplete"
									else:
										self.__records.pclink(recmap[p], recmap[c], txn)

						elif r == "reccousins" :
							print "reccousins"
							# read the dictionary of ParamDef PC links
							rr = load(fin)
							for a, bl in rr:
								for b in bl:
									self.__records.link(recmap[a], recmap[b], txn)

						else:
							print "Unknown category ", r


				print "Done!"

				if txn:
					txn.commit()
					self.LOG(4, "Import Complete, checkpointing")
					self.__dbenv.txn_checkpoint()

				elif not self.__importmode:
					DB_syncall()

				if self.__importmode:
					self.LOG(4, "Checkpointing complete, dumping indices")
					self.__commit_indices()



		def restoretest(self, ctxid=None, host=None):
				# NOT UPDATED...?
				"""This method will check a database backup and produce some statistics without modifying the current database."""

				if not self.__importmode: print("WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")

				#user,groups=self.checkcontext(ctxid,host)
				ctx = self.__getcontext(ctxid, host)
				user = ctx.user
				groups = ctx.groups
				#if user!="root" :
				if not ctx.checkadmin():
						raise SecurityError, "Only root may restore the database"

				if os.access(self.path + "/backup.pkl", R_OK) : fin = open(self.path + "/backup.pkl", "r")
				elif os.access(self.path + "/backup.pkl.bz2", R_OK) : fin = os.popen("bzcat " + self.path + "/backup.pkl.bz2", "r")
				elif os.access(self.path + "/../backup.pkl.bz2", R_OK) : fin = os.popen("bzcat " + self.path + "/../backup.pkl.bz2", "r")
				else: raise IOError, "backup.pkl not present"

				recmap = {}
				nrec = 0
				t0 = time.time()
				tmpindex = {}

				nu, npd, nrd, nr, np = 0, 0, 0, 0, 0

				while (1):
						try:
								r = load(fin)
						except:
								break

						# insert User
						if isinstance(r, User) :
								nu += 1

						# insert paramdef
						elif isinstance(r, ParamDef) :
								npd += 1

						# insert recorddef
						elif isinstance(r, RecordDef) :
								nrd += 1

						# insert and renumber record
						elif isinstance(r, Record) :
								r.setContext(ctx)
								try:
										o = r._Record__owner
										a = r._Record__permissions
										r._Record__permissions = (a[0], a[1], a[2], (o,))
										del r._Record__owner
								except:
										pass
								if (nr < 20) : print r["identifier"]
								nr += 1

						elif isinstance(r, str) :
								if r == "pdchildren" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								elif r == "pdcousins" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								elif r == "rdchildren" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								elif r == "rdcousins" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								elif r == "recchildren" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								elif r == "reccousins" :
										rr = load(fin)						# read the dictionary of ParamDef PC links
										np += len(rr)
								else : print "Unknown category ", r

				print "Users=", nu, "	 ParamDef=", npd, "	 RecDef=", nrd, "	 Records=", nr, "	 Links=", np


		def __del__(self):
				self.close()


		def close(self):
			if self.__allowclose == True:
				for btree in self.__dict__.values():
					if getattr(btree, '__class__', object).__name__.endswith('BTree'):
						try: btree.close()
						except db.InvalidArgError, e: print e
					for btree in self.__fieldindex.values(): btree.close()
					self.__dbenv.close()
#				 pass
#				 print self.__btreelist
#				 self.__btreelist.extend(self.__fieldindex.values())
#				 print self.__btreelist
#				 for bt in self.__btreelist:
#						 print '--', bt ; sys.stdout.flush()
#						 bt.close()




def DB_cleanup():
	"""This does at_exit cleanup. It would be nice if this were always called, but if python is killed
	with a signal, it isn't. This tries to nicely close everything in the database so no recovery is
	necessary at the next restart"""
	sys.stdout.flush()
	print >> sys.stderr, "Closing %d BDB databases" % (len(BTree.alltrees) + len(IntBTree.alltrees) + len(FieldBTree.alltrees))
	if DEBUG > 2: print >> sys.stderr, len(BTree.alltrees), 'BTrees'
	for i in BTree.alltrees.keys():
		if DEBUG > 2: sys.stderr.write('closing %s\n' % str(i))
		i.close()
		if DEBUG > 2: sys.stderr.write('%s closed\n' % str(i))
		if DEBUG > 2: print >> sys.stderr, '\n', len(IntBTree.alltrees), 'IntBTrees'
		for i in IntBTree.alltrees.keys(): i.close()
		if DEBUG > 2: sys.stderr.write('.')
		if DEBUG > 2: print >> sys.stderr, '\n', len(FieldBTree.alltrees), 'FieldBTrees'
		for i in FieldBTree.alltrees.keys(): i.close()
		if DEBUG > 2: sys.stderr.write('.')
		if DEBUG > 2: sys.stderr.write('\n')

# This rmakes sure the database gets closed properly at exit
atexit.register(DB_cleanup)
