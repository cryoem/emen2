from bsddb3 import db
from cPickle import load, dump

from emen2.Database.btrees import *
from emen2.Database.datastorage import *
from emen2.Database.exceptions import *
from emen2.Database.user import *
import emen2.Database.subsystems

from functools import partial

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
		g.debug.msg('LOG_INIT', "REGISTERING PUBLICMETHOD (%s)"% name)
		cls.__publicmethods[name]=func
#		cls._allmethods.add(name)
		

	@classmethod
	def _register_extmethod(cls, name, refcl):
		if name in cls._allmethods():
			raise ValueError('''method %s already registered''' % name)
		g.debug.msg('LOG_INIT', "REGISTERING EXTENSION (%s)"% name)
		cls.__extmethods[name]=refcl
#		cls._allmethods.add(name)

	
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
		if self.__publicmethods.has_key(name) or self.__extmethods.has_key(name):

			#print "\n\nDB: %s, kwargs: %s"%(name,kwargs)

			result = self.__publicmethods.get(name)# or self.__extmethods.get(name)()

			if result:
				result = partial(result, db, **kwargs)
			else:
				result = self.__extmethods.get(name)()

				kwargs['db'] = db
				if result: result = partial(result.execute, **kwargs)
# 			if method:
# 				result = method(*args[1:], **kwargs)
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
		if DEBUG > 2: print "sync %d BDB databases" % (len(BTree.alltrees) + len(IntBTree.alltrees) + len(FieldBTree.alltrees))
		t = time.time()
		for i in BTree.alltrees.keys(): i.sync()
		for i in IntBTree.alltrees.keys(): i.sync()
		for i in FieldBTree.alltrees.keys(): i.sync()
#		 print "%f sec to sync"%(time.time()-t)






#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()		
class Database(object):
		"""This class represents the database as a whole. There are 3 primary identifiers used in the database:
		dbid - Database id, a unique identifier for this database server
		recid - Record id, a unique (32 bit int) identifier for a particular record
		ctxid - A key for a database 'context' (also called a session), allows access for pre-authenticated user
		
		TODO : Probably should make more of the member variables private for slightly better security"""
		
		
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
					print "Note: transaction support disabled"
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
				if recover: xtraflags = db.DB_RECOVER
				
				# This sets up a DB environment, which allows multithreaded access, transactions, etc.
				if not os.access(path + "/home", os.F_OK) : os.makedirs(path + "/home")
				self.LOG(4, "Database initialization started")
				self.__allowclose = bool(allowclose)
				self.__dbenv = db.DBEnv()
				self.__dbenv.set_cachesize(0, cachesize, 4)				 # gbytes, bytes, ncache (splits into groups)
				self.__dbenv.set_data_dir(path)
				self.__dbenv.set_lk_detect(db.DB_LOCK_DEFAULT)		# internal deadlock detection
				# ian: lockers
				self.__dbenv.set_lk_max_locks(20000)
				self.__dbenv.set_lk_max_lockers(20000)
				
				#if self.__dbenv.DBfailchk(flags=0):
						#self.LOG(1,"Database recovery required")
						#sys.exit(1)
						
				self.__dbenv.open(path + "/home", envopenflags | xtraflags)
				global globalenv
				globalenv = self.__dbenv


				if not os.access(path + "/security", os.F_OK) : os.makedirs(path + "/security")
				if not os.access(path + "/index", os.F_OK) : os.makedirs(path + "/index")

				# Users
				self.__users = BTree("users", path + "/security/users.bdb", dbenv=self.__dbenv)												 # active database users
				self.__newuserqueue = BTree("newusers", path + "/security/newusers.bdb", dbenv=self.__dbenv)						# new users pending approval
				self.__contexts_p = BTree("contexts", path + "/security/contexts.bdb", dbenv=self.__dbenv)						# multisession persistent contexts
				self.__contexts = {}						# local cache dictionary of valid contexts
				
				txn = self.newtxn()
				
				# Create an initial administrative user for the database
				if (not self.__users.has_key("root")):
						self.LOG(0, "Warning, root user recreated")
						u = User()
						u.username = "root"
						if rootpw : p = hashlib.sha1(rootpw)
						else: p = hashlib.sha1(g.ROOTPW)
						u.password = p.hexdigest()
						u.groups = [-1]
						u.creationtime = time.strftime(TIMESTR)
						u.name = ('','','Admin')
						self.__users.set("root", u, txn)

				# Binary data names indexed by date
				self.__bdocounter = BTree("BinNames", path + "/BinNames.bdb", dbenv=self.__dbenv, relate=0)
				
				# Defined ParamDefs
				self.__paramdefs = BTree("ParamDefs", path + "/ParamDefs.bdb", dbenv=self.__dbenv, relate=1)												 # ParamDef objects indexed by name

				# Defined RecordDefs
				self.__recorddefs = BTree("RecordDefs", path + "/RecordDefs.bdb", dbenv=self.__dbenv, relate=1)										# RecordDef objects indexed by name
				# The actual database, keyed by recid, a positive integer unique in this DB instance
				# 2 special keys exist, the record counter is stored with key -1
				# and database information is stored with key=0
				self.__records = IntBTree("database", path + "/database.bdb", dbenv=self.__dbenv, relate=1)												# The actual database, containing id referenced Records
				try:
						maxr = self.__records.get(- 1, txn)
				except:
						self.__records.set(- 1, 0, txn)
						self.LOG(3, "New database created")
						
				# Indices
				if self.__importmode :
						self.__secrindex = MemBTree("secrindex", path + "/security/roindex.bdb", "s", dbenv=self.__dbenv)								# index of records each user can read
						self.__recorddefindex = MemBTree("RecordDefindex", path + "/RecordDefindex.bdb", "s", dbenv=self.__dbenv)				# index of records belonging to each RecordDef
				else:
						self.__secrindex = FieldBTree("secrindex", path + "/security/roindex.bdb", "s", dbenv=self.__dbenv)								# index of records each user can read
						self.__recorddefindex = FieldBTree("RecordDefindex", path + "/RecordDefindex.bdb", "s", dbenv=self.__dbenv)				# index of records belonging to each RecordDef
				self.__timeindex = BTree("TimeChangedindex", path + "/TimeChangedindex.bdb", dbenv=self.__dbenv)										# key=record id, value=last time record was changed
				self.__recorddefbyrec = IntBTree("RecordDefByRec", path + "/RecordDefByRec.bdb", dbenv=self.__dbenv, relate=0)
				self.__fieldindex = {}								# dictionary of FieldBTrees, 1 per ParamDef, not opened until needed
				
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
				if not self.__paramdefs.has_key("owner"):
						self.__paramdefs.set_txn(txn)

						pd = ParamDef("owner", "string", "Record Owner", "This is the user-id of the 'owner' of the record")
						self.__paramdefs["owner"] = pd

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
		
				if txn : txn.commit()
				elif not self.__importmode : DB_syncall()
				self.LOG(4, "Database initialized")



		# one of these 2 methods is mapped to self.newtxn()
		def newtxn1(self):
				return self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
		
		
		# ian: why?
		def newtxn2(self):
				return None
		
		
		
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
				if (level < 0 or level > 6) : level = 0
				try:
						o = file(self.logfile, "a")
						o.write("%s: (%s)	 %s\n" % (time.strftime(TIMESTR), LOGSTRINGS[level], message))
						o.close()
						if level < 4 : print "%s: (%s)	%s" % (time.strftime(TIMESTR), LOGSTRINGS[level], message)
				except:
						traceback.print_exc(file=sys.stdout)
						print("Critical error!!! Cannot write log message to '%s'\n" % self.logfile)



		# verbose
		#def __getattribute__(self,name):
		#	print "\tdb: %s"%name
		#	return object.__getattribute__(self,name)	


		def __str__(self):
				"""Try to print something useful"""
				return "Database %d records\n( %s )" % (int(self.__records[ - 1]), format_string_obj(self.__dict__, ["path", "logfile", "lastctxclean"]))
		
		
		
		# Not a public method
		def __checkpassword(self, username, password, ctxid=None, host=None):
				"""Check password against stored hash value; Returns bool"""
				
				s = hashlib.sha1(password)
				try:
					user = self.__users[username]
				except TypeError:
					raise AuthenticationError, AuthenticationError.__doc__

				if user.disabled:
					raise DisabledUserError, DisabledUserError.__doc__ % username

				return s.hexdigest() == user.password



		@publicmethod
		def login(self, username="anonymous", password="", maxidle=MAXIDLE, ctxid=None, host=None):
				"""Logs a given user in to the database and returns a ctxid, which can then be used for
				subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""

				ctx = None
				username = str(username)				

				#print "LOGIN ATTEMPT: user = %s, host = %s"%(username, host)
				
				
				# Anonymous access
				if (username == "anonymous"): # or username == ""
					ctx = Context(None, self, None, [-4], host, maxidle)


				# check password, hashed with sha-1 encryption
				else :
					try:
						user = self.__users[username]
					except TypeError:
						raise AuthenticationError, AuthenticationError.__doc__

					if user.disabled:
						raise DisabledUserError, DisabledUserError.__doc__ % username

					# Admins can "su"
					if (self.__checkpassword(username, password, ctxid=ctxid, host=host)) or self.checkadmin(ctxid,host):
						ctx = Context(None, self, username, user.groups, host, maxidle)

					else:
						self.LOG(0, "Invalid password: %s (%s)" % (username, host))
						raise AuthenticationError, AuthenticationError.__doc__

				
				# This shouldn't happen
				if ctx == None:
					self.LOG(1, "System ERROR, login(): %s (%s)" % (username, host))
					raise Exception, "System ERROR, login()"
				

				# we use sha to make a key for the context as well
				s = hashlib.sha1(username + str(host) + str(time.time()))
				ctx.ctxid = s.hexdigest()
				self.__contexts[ctx.ctxid] = ctx				# local context cache
				ctx.db = None
				txn = self.newtxn()
				self.__contexts_p.set(ctx.ctxid, ctx, txn)		# persistent context database
				ctx.db = self
				if txn : txn.commit()
				elif not self.__importmode : DB_syncall()
				self.LOG(4, "Login succeeded %s (%s)" % (username, ctx.ctxid))
				
				return ctx.ctxid
				
				
				
				
		@publicmethod
		def deletecontext(self, ctxid=None, host=None):
				"""Delete a context/Logout user. Returns None."""

				if hasattr(ctxid,"__iter__"):
					for i in ctxid:
						self.deletecontext(ctxid=i,host=host)
					return
					

				# check we have access to this context
				ctx = self.__getcontext(ctxid, host)
				
				txn = self.newtxn()
				self.__contexts_p.set_txn(txn)
				for k in self.__contexts_p.items():
						if k[0] == ctxid:
								try: del self.__contexts[k[0]]
								except: pass
								try: del self.__contexts_p[k[0]]
								except: pass
								self.__contexts_p.set_txn(None)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()				 


		# Logout is the same as delete context
		@publicmethod
		def logout(self, ctxid=None, host=None): 
			self.deletecontext(	ctxid, host)
		
		
		
		
		@publicmethod
		def newbinary(self, date, name, recid, key=None, filedata=None, paramname=None, ctxid=None, host=None):
				"""Get a storage path for a new binary object. Must have a
				recordid that references this binary, used for permissions. Returns a tuple
				with the identifier for later retrieval and the absolute path"""

				ctx = self.__getcontext(ctxid, host)
				
				if name == None or str(name) == "":
					raise ValueError, "BDO name may not be 'None'"				
				
				if key and not self.checkadmin(ctx):
					raise SecurityError, "Only admins may manipulate binary tree directly"

				if date == None:
					date = time.strftime(TIMESTR)
				
				
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
					
				print year
				print mon
				print day
				print newid
				key = "%04d%02d%02d" % (year, mon, day)
				print "newbinary key is %s; date=%s"%(key,date)


				# ian: check for permissions because actual operations are performed.
				rec = self.getrecord(recid, ctxid=ctxid, host=host)
				if not rec.writable():
						raise SecurityError, "Write permission needed on referenced record."
				

				for i in g.BINARYPATH:
						if key >= i[0] and key < i[1] :
								# actual storage path
								path = "%s/%04d/%02d/%02d" % (i[2], year, mon, day)
								break
				else:
						raise KeyError, "No storage specified for date %s" % key
		
		
				# try to make sure the directory exists
				try: os.makedirs(path)
				except: pass
		
		
				# Now we need a filespec within the directory
				# dictionary keyed by date, 1 directory per day
				#if usetxn:
				#	txn = self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
				#else:
				txn = self.newtxn()

				try:
					itm=self.__bdocounter.get(key,txn)
					newid = max(itm.keys()) + 1
				except:
					itm = {}
				
				itm[newid] = (name, recid)
				self.__bdocounter.set(key, itm, txn)
					

				if txn:
					txn.commit()
				elif not self.__importmode:
					DB_syncall()


				filename = path + "/%05X"%newid
				bdo = key + "%05X"%newid

				#todo: ian: raise exception if overwriting existing file (but this should never happen unless the file was pre-existing?)
				if os.access(path + "/%05X" % newid, os.F_OK) and not self.checkadmin(ctx):
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




		def __cleanupcontexts(self):
				"""This should be run periodically to clean up sessions that have been idle too long. Returns None."""

				self.lastctxclean = time.time()
				txn = self.newtxn()
				self.__contexts_p.set_txn(txn)
				for k in self.__contexts_p.items():
					
						if not isinstance(k[0], str):
								self.LOG(6, "Inverted context detected " + str(k[0].ctxid))
								pass
								#del(self._Database__contexts_p[k[0]])
						
						# use the cached time if available
						try:
								c = self.__contexts[k[0]]
								k[1].time = c.time

						except: pass
						#g.debug.msg('LOG_DEBUG', k[1].time, k[1].maxidle)
						if k[1].time + (k[1].maxidle or 0) < time.time(): 
								self.LOG(4, "Expire context (%s) %d" % (k[1].ctxid, time.time() - k[1].time))
								try: del self.__contexts[k[0]]
								except: pass
								try: del self.__contexts_p[k[0]]
								except: pass

				self.__contexts_p.set_txn(None)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				



		def __getcontext(self, key, host):
				"""Takes a ctxid key and returns a context (for internal use only)
				Note that both key and host must match. Returns context instance."""

				key = str(key)

				if (time.time() > self.lastctxclean + 30):
						# maybe not the perfect place to do this, but it will have to do
						self.__cleanupcontexts()
						pass

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

				if ctx.user!=None:
					ctx.groups.append(-3)
				ctx.groups.append(-4)
				ctx.groups=list(set(ctx.groups))
				
				return ctx						

		
		



		@publicmethod
		def getbinary(self, idents, ctxid=None, host=None, vts=None, params=None, filt=1):
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
				return(a.user, a.groups)





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

				if ctxid == None:
					return False
				
				if not isinstance(ctxid, Context):
						ctxid = self.__getcontext(ctxid, host)

				if (-1 in ctxid.groups):
						return True
				
				return False




		@publicmethod
		def checkreadadmin(self, ctxid=None, host=None):
				"""Checks if the user has global read access. Returns bool."""

				if ctxid == None:
					return False
				
				if not isinstance(ctxid, Context):
						ctxid = self.__getcontext(ctxid, host)

				if (-1 in ctxid.groups) or (-2 in ctxid.groups):
						return True

				return False	
		
		
		
		
		@publicmethod
		def checkcreate(self, ctxid=None, host=None):
				"""Check for permission to create records. Returns bool."""
				
				if ctxid == None:
					return False
			
				if not isinstance(ctxid, Context):
						ctxid = self.__getcontext(ctxid, host)
						
				if 0 in ctxid.groups or -1 in ctxid.groups:
						return True

				return False




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
				
				
				
				
				
		# ian todo: eventually let's move query stuff to end of file for neatness, or separate module...
		querykeywords = ["find", "plot", "histogram", "timeline", "by", "vs", "sort", "group", "and", "or", "child", "parent", "cousin", "><", ">", "<", ">=", "<=", "=", "!=", ","]
		querycommands = ["find", "plot", "histogram", "timeline"]
	
		# ian todo: fix
		@publicmethod
		def query(self, query, retindex=False, ctxid=None, host=None):
				"""This performs a general database query.
! - exclude protocol name
@ - protocol name
$ - parameter name
% - username
parentheses grouping not supported yet"""
				#self = db

				query = str(query)

				tm0 = time.time()
				query2 = self.querypreprocess(query, ctxid=ctxid, host=host)
				if isinstance(query2, tuple) : return query2				 # preprocessing returns a tuple on failure and a list on success
#				 print query2
				
				# Make sure there is only one command in the query
				command = [i for i in Database.querycommands if (i in query2)]
				
				if len(command) == 0 : command = "find"
				elif len(command) == 1 : command = command[0]
				else : return (- 2, "Too many commands in query", command)
				
				# start by querying for specified record type
				# each record can only have one type, so intersection combined with
				# multiple record types would always yield nothing, so we assume
				# the intent is union, not intersection
				byrecdef = set()
				excludeset = set()
				for n, i in enumerate(query2):
						if isinstance(i, str) and i[0] == "@" and (query[n - 1] not in ("by", "group")):
								byrecdef |= self.getindexbyrecorddef(i[1:], ctxid=ctxid, host=host)
						if isinstance(i, str) and i[0] == "!":
								excludeset |= self.getindexbyrecorddef(i[1:], ctxid=ctxid, host=host)

				# We go through the query word by word and perform each operation
				byparamval = set()
				groupby = None
				n = 0
				while (n < len(query2)):
						i = query2[n]
						if i == "plot" :
								if not query2[n + 2] in (",", "vs", "vs.") : return (- 1, "plot <y param> vs <x param>", "")
								comops = (query2[n + 1], query2[n + 3])
								n += 4
								
								# We make sure that any record containing either parameter is included
								# in the results by default, and cache the values for later use in plotting
								ibvx = self.getindexdictbyvalue(comops[1][1:], None, ctxid=ctxid, host=host)
								ibvy = self.getindexdictbyvalue(comops[0][1:], None, ctxid=ctxid, host=host)
								
								if len(byparamval) > 0 : byparamval.intersection_update(ibvx.keys())
								else: byparamval = set(ibvx.keys())
								byparamval.intersection_update(ibvy.keys())
								continue
						elif i == "histogram" :
								if not query2[n + 1][0] == "$" : return (- 1, "histogram <parametername>", "")
								comops = (query2[n + 1],)
								n += 2
								
								# We make sure that any record containing the parameter is included
								ibvh = self.getindexdictbyvalue(comops[0][1:], None, ctxid=ctxid, host=host)
								if len(byparamval) > 0 : byparamval.intersection_update(ibvh.keys())
								else: byparamval = set(ibvh.keys())
								continue
						elif i == "group" :
								if query2[n + 1] == "by" :
										groupby = query2[n + 2]
										n += 3
										continue
								groupby = query2[n + 1]
								n += 2
								continue
						elif i == "child" :
								#print "QUERY CHILD OF: %s"%query2[n+1]
								#print query2
								chl = self.getchildren(query2[n + 1], recurse=20, ctxid=ctxid, host=host)
								#print "getchildren result... %s"%len(chl)
#								 chl=set([i[0] for i in chl])	 # children no longer suppport names 
								if len(byparamval) > 0 : byparamval &= chl
								else: byparamval = chl
								#print byparamval
								n += 2
								continue
						elif i == "parent" :
								if len(byparamval) > 0 : byparamval &= self.getparents(query2[n + 1], "record", recurse=20, ctxid=ctxid, host=host)
								else: byparamval = self.getparents(query2[n + 1], "record", recurse=20, ctxid=ctxid, host=host)
								n += 2
								continue
						elif i == "cousin" :
								if len(byparamval) > 0 : byparamval &= self.getcousins(query2[n + 1], "record", recurse=20, ctxid=ctxid, host=host)
								else: byparamval = self.getcousins(query2[n + 1], "record", recurse=20, ctxid=ctxid, host=host)
								n += 2
								continue
						elif i[0] == "@" or i[0] == "!" or i in ("find", "timeline") :
								n += 1
								continue
						elif i[0] == "%" :
								if len(byparamval) > 0 : byparamval &= self.getindexbyuser(i[1:], ctxid=ctxid, host=host)
								else: byparamval = self.getindexbyuser(i[1:], ctxid=ctxid, host=host)
						elif i[0] == "$" :
								vrange = [None, None]
								op = query2[n + 1]
								if op == ">" or op == ">=" : 
										vrange[0] = query2[n + 2]		 # indexing mechanism doesn't support > or < yet
										n += 2
								elif op == "<" or op == "<=" : 
										vrange[1] = query2[n + 2]		 # so we treat them the same for now
										n += 2
								elif op == "=" : 
										vrange = query2[n + 2]
										n += 2
								elif op == "><" : 
										if not query2[n + 3] in (",", "and") : raise Exception, "between X and Y (%s)" % query2[n + 3]
										vrange = [query2[n + 2], query2[n + 4]]
										n += 4
								if len(byparamval) > 0 : byparamval &= self.getindexbyvalue(i[1:], vrange, ctxid=ctxid, host=host)
								else: byparamval = self.getindexbyvalue(i[1:], vrange, ctxid=ctxid, host=host)
						elif i == "and" : pass
						
						else :
								return (- 1, "Unknown word", i)

						n += 1
				
				if len(byrecdef) == 0: byrecdef = byparamval
				elif len(byparamval) != 0: byrecdef &= byparamval 
				
				if len(excludeset) > 0 : byrecdef -= excludeset
						
				
				# Complicated block of code to handle 'groupby' queries
				# this splits the set of located records (byrecdef) into
				# a dictionary keyed by whatever the 'groupby' request wants
				# For splits based on a parameter ($something), it will recurse
				# into the parent records up to 3 levels to try to find the
				# referenced parameter. If a protocol name is supplied, it will
				# look for a parent record of that class.
				if groupby:
						dct = {}
						if groupby[0] == '$':
								gbi = self.getindexdictbyvalue(groupby[1:], None, None, ctxid=ctxid, host=host)
								for i in byrecdef:
										if gbi.has_key(i) :
												try: dct[gbi[i]].append(i)
												except: dct[gbi[i]] = [i]
										else :
												p = self.getparents(i,'record',4,ctxid=ctxid,host=host)
												#p = self.__getparentssafe(i, 'record', 4, ctxid=ctxid, host=host)
												for j in p:
														if gbi.has_key(j) :
																try: dct[gbi[j]].append(i)
																except: dct[gbi[j]] = [i]
						elif groupby[0] == "@":
								alloftype = self.getindexbyrecorddef(groupby[1:], ctxid=ctxid, host=host)
								for i in byrecdef:
										#p = self.__getparentssafe(i, 'record', 10, ctxid=ctxid, host=host)
										p = self.getparents(i,'record',10,ctxid=ctxid,host=host)
										p &= alloftype
										for j in p:
												try: dct[j].append(i)
												except: dct[j] = [i]
#										 else: print p,alloftype,self.getparents(i,'record',10,ctxid)
						elif groupby in ("class", "protocol", "recorddef") :
#								 for i in byrecdef:
#										 r=self.getrecord(i,ctxid)
#										 try: dct[r.rectype].append(i)
#										 except: dct[r.rectype]=[i]
								for i in self.getrecorddefnames(ctxid=ctxid, host=host):
										s = self.getindexbyrecorddef(i, ctxid=ctxid, host=host)
										ss = s & byrecdef
										if len(ss) > 0 : dct[i] = tuple(ss)
						ret = dct
				else: ret = byrecdef

				if command == "find" :
						allrec = self.getindexbycontext(ctxid=ctxid,host=host)
						ret &= allrec
						# Simple find request, no further processing required
						if isinstance(ret, dict):
								return { 'type':'find', 'querytime':time.time() - tm0, 'data':ret}
						else:
								return { 'type':'find', 'querytime':time.time() - tm0, 'data':tuple(ret) }
				elif command == "plot" :
						# This deals with 'plot' requests, which are currently 2D scatter plots
						# It will return a sorted list of (x,y) pairs, or if a groupby request,
						# a dictionary of such lists. Note that currently output is also
						# written to plot*txt text files
						if isinstance(ret, dict) :
								multi = {}
								# this means we had a 'groupby' request		 
								x0, x1, y0, y1 = 1e38, - 1e38, 1e38, - 1e38
								for j in ret.keys():
										ret2x = []
										ret2y = []
										ret2i = []
										for i in ret[j]:
												ret2x.append(ibvx[i])
												ret2y.append(ibvy[i])
												ret2i.append(i)
												x0 = min(x0, ibvx[i])
												y0 = min(y0, ibvy[i])
												x1 = max(x1, ibvx[i])
												y1 = max(y1, ibvy[i])
										
										if retindex:
												multi[j] = { 'x':ret2x, 'y':ret2y, 'i':ret2i }
										else:
												multi[j] = { 'x':ret2x, 'y':ret2y }
								return {'type': 'multiplot', 'data': multi, 'xrange': (x0, x1), 'yrange': (y0, y1), 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'groupby': groupby, 'querytime':time.time() - tm0, 'query':query2}
		
						else:
								# no 'groupby', just a single query
								x0, x1, y0, y1 = 1e38, - 1e38, 1e38, - 1e38
								ret2x = []
								ret2y = []
								ret2i = []
								for i in byrecdef:
										ret2x.append(ibvx[i])
										ret2y.append(ibvy[i])
										ret2i.append(i)
										x0 = min(x0, ibvx[i])
										y0 = min(y0, ibvy[i])
										x1 = max(x1, ibvx[i])
										y1 = max(y1, ibvy[i])

								if retindex :
										return {'type': 'plot', 'data': {'x':ret2x, 'y':ret2y, 'i':ret2i}, 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'xrange': (x0, x1), 'yrange': (y0, y1), 'querytime':time.time() - tm0, 'query':query2}
								else:
										return {'type': 'plot', 'data': {'x':ret2x, 'y':ret2y}, 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'xrange': (x0, x1), 'yrange': (y0, y1), 'querytime':time.time() - tm0, 'query':query2}
				elif command == "histogram" :
						# This deals with 'histogram' requests
						# This is much more complicated than the plot query, since a wide variety
						# of datatypes must be handled sensibly
						if len(byrecdef) == 0 : return (- 1, "no records found", "")
						
						if not isinstance(ret, dict) :				 # we make non groupby requests look like a groupby with one null category
								ret = {"":ret}
								
						if 1:
								ret2 = {}
								tmp = []
								pd = self.getparamdef(comops[0][1:],ctxid=ctxid,host=host)
								
								if (pd.vartype in ("int", "longint", "float", "longfloat")) :
										# get all of the values for the histogrammed field
										# and associated numbers, (value, record #, split key)
										for k, j in ret.items(): 
												for i in j: tmp.append((ibvh[i], i, k))
										tmp.sort()
										
										# Find limits and make a decent range for the histogram
										m0, m1 = float(tmp[0][0]), float(tmp[ - 1][0])
										n = min(len(tmp) / 10, 50)
										step = setdigits((m1 - m0) / (n - 1), 2)				 # round the step to 2 digits
										m0 = step * (floor(m0 / step) - .5)								 # round the min val to match step size
										n = int(ceil((m1 - m0) / step)) + 1
#										 if m0+step*n<=m1 : n+=1
										digits = max(0, 1 - floor(log10(step)))
										fmt = "%%1.%df" % digits
										
										# now we build the actual histogram. Result is ret2 = { 'keys':keylist,'x':xvalues,1:first hist,2:2nd hist,... }
										ret2 = {}
										ret2['keys'] = []
										for i in tmp:
												if not i[2] in ret2['keys']: 
														ret2['keys'].append(i[2])
														kn = ret2['keys'].index(i[2])
														ret2[kn] = [0] * n
												else: kn = ret2['keys'].index(i[2])
												ret2[kn][int(floor((i[0] - m0) / step))] += 1
										
										# These are the x values
										ret2['x'] = [fmt % ((m0 + step * (i + 0.5))) for i in range(n)]
								elif (pd.vartype in ("date", "datetime")) :
										# get all of the values for the histogrammed field
										# and associated numbers
										# This could be rewritten MUCH more concisely
										for k, j in ret.items(): 
												for i in j: tmp.append((ibvh[i], i, k))
										tmp.sort()
										
										# Work out x-axis values. This is complicated for dates
										t0 = int(timetosec(tmp[0][0]))
										t1 = int(timetosec(tmp[ - 1][0]))
										totaltime = t1 - t0				 # total time span in seconds
										
										# now we build the actual histogram. Result is ret2 = { 'keys':keylist,'x':xvalues,1:first hist,2:2nd hist,... }
										ret2 = {}
										ret2['keys'] = []
										ret2['x'] = []
										
										if totaltime < 72 * 3600:		 # by hour, less than 3 days
												for i in range(t0, t1 + 3599, 3600):
														t = time.localtime(i)
														ret2['x'].append("%04d/%02d/%02d %02d" % (t[0], t[1], t[2], t[3]))
												n = len(ret2['x'])
												for i in tmp:
														if not i[2] in ret2['keys']: 
																ret2['keys'].append(i[2])
																kn = ret2['keys'].index(i[2])
																ret2[kn] = [0] * n
														else: kn = ret2['keys'].index(i[2])
														try: ret2[kn][ret2['x'].index(i[0][:13])] += 1
														except: g.debug.msg('LOG_ERROR', "Index error on ", i[0])
												
										elif totaltime < 31 * 24 * 3600:		# by day, less than ~1 month
												for i in range(t0, t1 + 3600 * 24 - 1, 3600 * 24):
														t = time.localtime(i)
														ret2['x'].append("%04d/%02d/%02d" % (t[0], t[1], t[2]))
												n = len(ret2['x'])
												for i in tmp:
														if not i[2] in ret2['keys']: 
																ret2['keys'].append(i[2])
																kn = ret2['keys'].index(i[2])
																ret2[kn] = [0] * n
														else: kn = ret2['keys'].index(i[2])
														try: ret2[kn][ret2['x'].index(i[0][:10])] += 1
														except: g.debug.msg('LOG_ERROR', "Index error on ", i[0])
												
										elif totaltime < 52 * 7 * 24 * 3600: # by week, less than ~1 year
												for i in range(int(t0), int(t1) + 3600 * 24 * 7 - 1, 3600 * 24 * 7):
														t = time.localtime(i)
														ret2['x'].append(timetoweekstr("%04d/%02d/%02d" % (t[0], t[1], t[2])))
												n = len(ret2['x'])
												for i in tmp:
														if not i[2] in ret2['keys']: 
																ret2['keys'].append(i[2])
																kn = ret2['keys'].index(i[2])
																ret2[kn] = [0] * n
														else: kn = ret2['keys'].index(i[2])
														try: ret2[kn][ret2['x'].index(timetoweekstr(i[0]))] += 1
														except: g.debug.msg('LOG_ERROR', "Index error on ", i[0])
														
										elif totaltime < 4 * 365 * 24 * 3600: # by month, less than ~4 years
												m0 = int(tmp[0][0][:4]) * 12 + int(tmp[0][0][5:7]) - 1
												m1 = int(tmp[ - 1][0][:4]) * 12 + int(tmp[ - 1][0][5:7]) - 1
												for i in range(m0, m1 + 1):
														ret2['x'].append("%04d/%02d" % (i / 12, (i % 12) + 1))
												n = len(ret2['x'])
												for i in tmp:
														if not i[2] in ret2['keys']: 
																ret2['keys'].append(i[2])
																kn = ret2['keys'].index(i[2])
																ret2[kn] = [0] * n
														else: kn = ret2['keys'].index(i[2])
														try: ret2[kn][ret2['x'].index(i[0][:7])] += 1
														except: g.debug.msg('LOG_ERROR', "Index error on ", i[0])
										else :		# by year
												for i in range(int(tmp[0][0][:4]), int(tmp[ - 1][0][:4]) + 1):
														ret2['x'].append("%04d" % i)
												n = len(ret2['x'])
												for i in tmp:
														if not i[2] in ret2['keys']: 
																ret2['keys'].append(i[2])
																kn = ret2['keys'].index(i[2])
																ret2[kn] = [0] * n
														else: kn = ret2['keys'].index(i[2])
														ret2[kn][ret2['x'].index(i[0][:4])] += 1
										
								elif (pd.vartype in ("choice", "string")):
										# get all of the values for the histogrammed field
										# and associated record ids. Note that for string/choice
										# this may be a list of values rather than a single value
										gkeys = set()				 # group key list
										vkeys = set()				 # item key list
										for k, j in ret.items(): 
												gkeys.add(k)
												for i in j: 
														v = ibvh[i]
														vkeys.add(v)
														if isinstance(v, str) : tmp.append((v, i, k))
														else:
																for l in v: tmp.append((l, i, k))
										
										gkeys = list(gkeys)
										gkeys.sort()
										vkeys = list(vkeys)
										vkeys.sort()

										# a string field
										tmp2 = [[0] * len(vkeys) for i in range(len(gkeys))]
										for i in tmp:
												tmp2[gkeys.index(i[2])][vkeys.index(i[0])] += 1
										
										ret2 = { 'keys':gkeys, 'x':vkeys}
										for i, j in enumerate(tmp2): ret2[i] = tmp2[i]
										
#								 ret2.sort()
								return {'type': 'histogram', 'data': ret2, 'xlabel': comops[0][1:], 'ylabel': "Counts", 'querytime':time.time() - tm0, 'query':query2}
						
				elif command == "timeline" :
						pass
						
										
		def querypreprocess(self, query, ctxid=None, host=None):
				"""This performs preprocessing on a database query string.
preprocessing involves remapping synonymous keywords/symbols and
identification of parameter and recorddef names, it is normally
called by query()

! - exclude protocol
@ - protocol name
$ - parameter name
% - username
parentheses not supported yet. Upon failure returns a tuple:
(code, message, bad element)"""
				
				# Words get replaced with their normalized equivalents
				replacetable = {
				"less":"<", "before":"<", "lower":"<", "under":"<", "older":"<", "shorter":"<",
				"greater":">", "after":">", "more":">", "over":">", "newer":">", "taller":">",
				"between":"><", "&":"and", "|":"or", "$$":"$", "==":"=", "equal":"=", "equals":"=",
				"locate":"find", "split":"group", "children":"child", "parents":"parent", "cousins":"cousin",
				"than":None, "is":None, "where":None, "of":None}
				
				
				# parses the strings into discrete units to process (words and operators)
				e = [i for i in re.split("\s|(<=|>=|><|!=|<|>|==|=|,)", query) if i != None and len(i) > 0]

				# this little mess rejoins quoted strings into a single element
				elements = []
				i = 0
				while i < len(e) :
						if e[i][0] == '"' or e[i][0] == "'" :
								q = e[i][0]
								e[i] = e[i][1:]
								s = ""
								while(i < len(e)):
										if e[i][ - 1] == q :
												s += e[i][: - 1]
												elements.append(s)
												i += 1
												break
										s += e[i] + " "
										i += 1
						else: 
								elements.append(e[i])
								i += 1
				
				# Now we clean up the list of terms and check for errors
				for n, e in enumerate(elements):
						# replace descriptive words with standard symbols
						if replacetable.has_key(e) : 
								elements[n] = replacetable[e]
								e = replacetable[e]
								
						if e == None or len(e) == 0 : continue
						
						# if it's a keyword, we don't need to do anything else to it
						if e in Database.querykeywords : continue
						
						# this checks to see if the element is simply a number, in which case we need to keep it!
						try: elements[n] = int(e)
						except: pass
						else: continue
						
						try: elements[n] = float(e)
						except: pass
						else: continue
						
						if e[0] == "@" :
								a = self.findrecorddefname(e[1:],ctxid=ctxid,host=host)
								if a == None : return (- 1, "Invalid protocol", e)
								elements[n] = "@" + a
								continue
						if e[0] == '!':
								a = self.findrecorddefname(e[1:],ctxid=ctxid,host=host)
								if a == None : return (- 1, "Invalid protocol", e)
								elements[n] = "!" + a
								continue
						elif e[0] == "$" :
								a = self.findparamdefname(e[1:],ctxid=ctxid,host=host)
								if a == None : return (- 1, "Invalid parameter", e)
								elements[n] = "$" + a
								continue
						elif e[0] == "%" :
								a = self.findusername(e[1:], ctxid,ctxid=ctxid,host=host)
								if a == None : return (- 1, "Username does not exist", e)
								if isinstance(a, str) :
										elements[n] = "%" + a
										continue
								if len(a) > 0 : return (- 1, "Ambiguous username", e, a)
						else:
								a = self.findrecorddefname(e,ctxid=ctxid,host=host)
								if a != None : 
										elements[n] = "@" + a
										continue
								a = self.findparamdefname(e,ctxid=ctxid,host=host)
								if a != None : 
										elements[n] = "$" + a
										continue
								
								# Ok, if we don't recognize the word, we just ignore it
								# if it's in a critical spot we can raise an error later
				
				return [i for i in elements if i != None]

#				 """This will use a context to return
#				 a list of records the user can access"""
#				 u,g=self.checkcontext(ctxid,host)
#				 
#				 ret=set(self.__secrindex[u])
#				 for i in g: ret|=set(self.__secrindex[i])
#				 return ret



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

				for k,v in ret.items(): g.debug(k,v)
				return ret





		# ian: finish..
		# decide how much security to allow...
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

				if ctx.user != username and not self.checkreadadmin(ctx):
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

			paramname = str(paramname).lower()
			
			ind = self.__getparamindex(paramname, create=0, ctxid=ctxid, host=host)				
			
			if valrange == None:
				ret = set(ind.values())

			elif isinstance(valrange, tuple) or isinstance(valrange, list):
				ret = set(ind.values(valrange[0], valrange[1]))

			else:
				ret = set(ind[valrange] or [])
			
			#u,g=self.checkcontext(ctxid,host)
			#ctx=self.__getcontext(ctxid,host)
			if self.checkreadadmin(ctxid,host):
					return ret
					
			#secure = set(self.getindexbycontext(ctxid=ctxid, host=host))				 # all records the user can access
			return self.filterbypermissions(ret,ctxid=ctxid,host=host) #ret & secure				 # intersection of the two search results
		
		
		
						
		
		
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
				if self.checkreadadmin(ctx):
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
						try: j = self.getrecord(i, ctxid=ctxid, host=host)
						except: continue
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
						try: p = self.getparents(i, recurse=recurse, ctxid=ctxid, host=host)
						except: continue
						try: k = [ii for ii in p if self.getrecord(ii, ctxid=ctxid, host=host).rectype == parenttype]
						except: k = [None]
						if len(k) == 0 : k = [None]
						
						for j in k:
								if r.has_key(j) : r[j].append(i)
								else : r[j] = [i]
				
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
						try: self.getrecord(key,ctxid=ctxid,host=host)
						except: return set
						return set(self.__records.cousins(key))

				if keytype == "recorddef":
						return set(self.__recorddefs.cousins(str(key).lower()))

				if keytype == "paramdef":
						return set(self.__paramdefs.cousins(str(key).lower()))
				
				raise Exception, "getcousins keytype must be 'record', 'recorddef' or 'paramdef'"






		@publicmethod
		def pclink(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
				"""Establish a parent-child relationship between two keys.
				A context is required for record links, and the user must
				have write permission on at least one of the two."""
				
				ctx = self.__getcontext(ctxid, host)

				if not self.checkcreate(ctx):
						raise SecurityError, "pclink requires record creation priveleges"

				if keytype not in ["record", "recorddef", "paramdef"]:
						raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

				if pkey==ckey:
					print "WARNING: Cannot link to self."
					return
								
				# ian: circular reference detection. 
				if not self.__importmode:
						p = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="parents", ctxid=ctxid, host=host)[0]
						c = self.__getrel(key=pkey, keytype=keytype, recurse=self.maxrecurse, rel="children", ctxid=ctxid, host=host)[0]
						if pkey in c or ckey in p or pkey == ckey:
								raise Exception, "Circular references are not allowed: parent=%s child=%s"%(pkey,ckey)
				
				
				if keytype == "record": 
						g.debug("pclink: %s -> %s"%(pkey,ckey))
						a = self.getrecord(pkey, ctxid=ctxid, host=host)
						b = self.getrecord(ckey, ctxid=ctxid, host=host)
						#print a.writable(),b.writable()
						if (not a.writable()) and (not b.writable()):
								raise SecurityError, "pclink requires partial write permission"
						r = self.__records.pclink(pkey, ckey, txn=txn)

				if keytype == "recorddef":
						r = self.__recorddefs.pclink(str(pkey).lower(), str(ckey).lower(), txn=txn)

				if keytype == "paramdef":
						r = self.__paramdefs.pclink(str(pkey).lower(), str(ckey).lower(), txn=txn)

				self.LOG(0, "pclink %s: %s <-> %s by user %s" % (keytype, pkey, ckey, ctx.user))
				return r
						
		
		

		@publicmethod
		def pcunlink(self, pkey, ckey, keytype="record", txn=None, ctxid=None, host=None):
				"""Remove a parent-child relationship between two keys. Returns none if link doesn't exist."""
				
				ctx = self.__getcontext(ctxid, host)
				
				if not self.checkcreate(ctx):
						raise SecurityError, "pcunlink requires record creation priveleges"

				if keytype not in ["record", "recorddef", "paramdef"]:
						raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"
										
				if keytype == "record" : 
						a = self.getrecord(pkey, ctxid=ctxid, host=host)
						b = self.getrecord(ckey, ctxid=ctxid, host=host)
						if (not a.writable()) and (not b.writable()):
								raise SecurityError, "pcunlink requires partial write permission"
						r = self.__records.pcunlink(str(pkey).lower(), str(ckey).lower(), txn)

				if keytype == "recorddef":
						r = self.__recorddefs.pcunlink(str(pkey).lower(), str(ckey).lower(), txn)

				if keytype == "paramdef":
						r = self.__paramdefs.pcunlink(str(pkey).lower(), str(ckey).lower(), txn)
				
				self.LOG(0, "pcunlink %s: %s <-> %s by user %s" % (keytype, pkey, ckey, ctx.user))
				return r
				
		
		

		@publicmethod
		def link(self, key1, key2, keytype="record", txn=None, ctxid=None, host=None):
				"""Establish a 'cousin' relationship between two keys. For Records
				the context is required and the user must have read permission
				for both records."""
				# ian todo: check for circular references.

				ctx = self.__getcontext(ctxid,host)

				if not self.checkcreate(ctx):
						raise SecurityError, "link requires record creation priveleges"

				if keytype not in ["record", "recorddef", "paramdef"]:
						raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

				if keytype == "record": 
						a = self.getrecord(key1, ctxid=ctxid, host=host)
						b = self.getrecord(key2, ctxid=ctxid, host=host)
						r = self.__records.link(key1, key2)

				if keytype == "recorddef":
						r = self.__recorddefs.link(str(key1).lower(), str(key2).lower(), txn)

				if keytype == "paramdef":
						r = self.__paramdefs.link(str(key1).lower(), str(key2).lower(), txn)

				self.LOG(0, "link %s: %s <-> %s by user %s" % (keytype, key1, key2, ctx.user))
				return r
		
		
		
		# ian: made ctxid req'd
		#@write,user
		@publicmethod
		def unlink(self, key1, key2, keytype="record", txn=None, ctxid=None, host=None):
				"""Remove a 'cousin' relationship between two keys."""
				#self = db
				ctx = self.__getcontext(ctxid,host)

				if not self.checkcreate(ctx):
						raise SecurityError, "unlink requires record creation priveleges"
				if keytype not in ["record", "recorddef", "paramdef"]:
						raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"
										
				if keytype == "record":
						a = self.getrecord(key1, ctxid=ctxid, host=host)
						b = self.getrecord(key2, ctxid=ctxid, host=host)
						r = self.__records.unlink(key1, key2)
				if keytype == "recorddef":
						r = self.__recorddefs.unlink(str(key1).lower(), str(key2).lower(), txn)
				if keytype == "paramdef":
						r = self.__paramdefs.unlink(str(key1).lower(), str(key2).lower(), txn)
				
				# ian todo: add loggging
				self.LOG(0, "unlink %s: %s <-> %s by user %s" % (keytype, key1, key2, ctx.user))
				return r
				
				
				
				
				
		@publicmethod
		def disableuser(self, username, ctxid=None, host=None):
			"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
			a complete historical record is maintained. Only an administrator can do this."""
			return self.__setuserstate(username, 1, ctxid=ctxid, host=host)
		
		
				
		@publicmethod
		def enableuser(self, username, ctxid=None, host=None):
			return self.__setuserstate(username, 0, ctxid=ctxid, host=host)



		def __setuserstate(self, username, state, ctxid=None, host=None):
			"""Set user enabled/disabled. 0 is enabled. 1 is disabled."""

			state=int(state)

			if state not in [0,1]:
				raise Exception, "Invalid state. Must be 0 or 1."

			ctx = self.__getcontext(ctxid, host)
			if not self.checkadmin(ctx):
					raise SecurityError, "Only administrators can disable users"

			ol=0
			if not hasattr(username, "__iter__"):
				ol=1
				username=[username]
				
			ret=[]
			for i in username:
				if i == ctx.user:
					continue
				#	raise SecurityError, "Even administrators cannot disable themselves"
				i=str(i)
				user = self.__users[i]
				if user.disabled == state:
					continue
				
				user.disabled = int(state)
				self.__users[i] = user
				ret.append(i)
				
				if state:
					self.LOG(0, "User %s disabled by %s" % (username, ctx.user))
				else:
					self.LOG(0, "User %s enabled by %s" % (username, ctx.user))
			
			if ol: return ret[0]
			return ret
					
					

		@publicmethod
		def approveuser(self, username, ctxid=None, host=None):
			"""Only an administrator can do this, and the user must be in the queue for approval"""

			ctx = self.__getcontext(ctxid, host)

			if not self.checkadmin(ctx):
				raise SecurityError, "Only administrators can approve new users"

			if hasattr(username,"__iter__"):
				ret=[]
				for i in username:
					ret.append(self.approveuser(username=str(i),ctxid=ctxid,host=host))
				return ret

			username = str(username)
							
			if not username in self.__newuserqueue :
				raise KeyError, "User %s is not pending approval" % username
					
			if username in self.__users :
				self.__newuserqueue[username] = None
				raise KeyError, "User %s already exists, deleted pending record" % username

			# ian: create record for user.
			user = self.__newuserqueue[username]

			user.validate()

			if user.record == None:
				userrec = self.newrecord("person", init=1, ctxid=ctxid, host=host)
				#print user
				userrec["username"] = username
				userrec["name_first"] = user.name[0]
				userrec["name_middle"] = user.name[1]
				userrec["name_last"] = user.name[2]
				userrec["email"] = user.email

				# can't add permissions before user is approved
				#p=(p[0]+(-3,),p[1]+(userrec['username'],),p[2]+(userrec['username'],),p[3])

				for k,v in user.signupinfo.items():
					userrec[k]=v


			user.validate()

			txn = self.newtxn()

			user.record = self.putrecord(userrec, ctxid=ctxid, host=host, txn=txn)
			user.signupinfo = None
			self.__users.set(username, user, txn=txn)
			self.__newuserqueue.set(username, None, txn=txn)
			self.secrecordadduser([[],[],[],[user.username]],user.record,ctxid=ctxid,host=host,txn=txn)

			if txn: txn.commit()
			elif not self.__importmode : DB_syncall()

			return username




		@publicmethod
		def rejectuser(self, username, ctxid=None, host=None):
			"""Remove a user from the pending new user queue - only an administrator can do this"""

			ctx = self.__getcontext(ctxid, host)

			# ian todo: move to general permission level check rather than hardcode -1 at each instance. several places.
			if not self.checkadmin(ctx):
				raise SecurityError, "Only administrators can approve new users"

			if hasattr(username,"__iter__"):
				ret={}
				for i in username:
					ret[i] = self.rejectuser(username=i,ctxid=ctxid,host=host)
				return ret
				
			username = str(username)

								
			if not username in self.__newuserqueue :
				raise KeyError, "User %s is not pending approval" % username

			self.__newuserqueue[username] = None

			return username



		@publicmethod
		def getuserqueue(self, ctxid=None, host=None):
			"""Returns a list of names of unapproved users"""
			ctx = self.__getcontext(ctxid, host)				

			if not self.checkadmin(ctx):
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
				
				if not self.checkreadadmin(ctx):
						raise SecurityError, "Only administrators can access pending users"
						
				return self.__newuserqueue[username]
						



		# ian todo: allow users to change privacy setting
		@publicmethod
		def putuser(self, user, ctxid=None, host=None):
				"""Updates user. Takes User object (w/ validation.) Deprecated for non-administrators."""

				if not isinstance(user, User):
						try: user = User(user)
						except: raise ValueError, "User instance or dict required"
				#user=User(user.__dict__.copy())
				#user.validate()

				try:
						ouser = self.__users[user.username]
				except:
						raise KeyError, "Putuser may only be used to update existing users"
				
				ctx = self.__getcontext(ctxid, host)
				
				if not self.checkadmin(ctx):
						raise SecurityError, "Only administrators may update a user with this method"
				
				if user.password != ouser.password:
						raise SecurityError, "Passwords may not be changed with this method"
				
				if user.creator != ouser.creator or user.creationtime != ouser.creationtime:
						raise SecurityError, "Creation information may not be changed"				 
				
				user.validate()				 
				
				txn = self.newtxn()
				self.__users.set(user.username, user, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				return user

		
#				 ian 03.30.08: old method no longer necessary
#		 
#			def putuserdict(self,username,userdict,ctxid,host=None):
#					#use to only update user information listed in allowKeys
#					denyKeys = ["username","password","creator","creationtime"]
#					allowKeys = ["firstname","lastname", "midname","email","phone","fax","cellphone","webpage","institution","department","address","city","state","zipcode","country","groups","privacy", "disabled"]
#					try:
#							ouser=self.__users[username]
#					except:
#							raise KeyError,"Putuser may only be used to update existing users"
#					
#					ctx=self.__getcontext(ctxid,host)
#					if ctx.user!=ouser.username and not(-1 in ctx.groups) :
#							raise SecurityError,"Only administrators and the actual user may update a user record"
# 
#					for thekey in denyKeys:
#							if userdict.has_key(thekey):
#									 del userdict[thekey]
#									 
#					userdict['name'] = []
#					for thekey in ['firstname', 'midname', 'lastname']:
#							if userdict.has_key(thekey):
#								userdict['name'].append(userdict[thekey])
#							else:
#										userdict['name'].append("")
#							
#					if not (-1 in ctx.groups) :
#							userdict['groups']=ouser.groups
#							if userdict.has_key('disabled'):
#											 del userdict['disabled']
# 
#					else:
#							if isinstance(userdict['groups'], list):
#									thegroups = [int(i) for i in userdict['groups']]
#							else:
#									thegroups = [int(userdict['groups'])]
#							userdict['groups'] = thegroups
#									
#					ouser.__dict__.update(userdict)
#					txn=self.newtxn()
#					self.__users.set(username,ouser,txn)
#					if txn: txn.commit()
#					elif not self.__importmode : DB_syncall()
#					return userdict
		
		
		
		@publicmethod
		def setpassword(self, username, oldpassword, newpassword, ctxid=None, host=None):

				username = str(username)

				ctx = self.__getcontext(ctxid, host)
				user = self.getuser(username, ctxid=ctxid, host=host)
				
				s = hashlib.sha1(oldpassword)

				if s.hexdigest() != user.password and not self.checkadmin(ctx):
						time.sleep(2)
						raise SecurityError, "Original password incorrect"
				
				# we disallow bad passwords here, right now we just make sure that it 
				# is at least 6 characters long

				if (len(newpassword) < 6):
					raise SecurityError, "Passwords must be at least 6 characters long" 

				t = hashlib.sha1(newpassword)
				user.password = t.hexdigest()
				
				txn = self.newtxn()
				self.__users.set(user.username, user, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				return 1
		
		
		

		@publicmethod
		def adduser(self, user, ctxid=None, host=None):
				"""adds a new user record. However, note that this only adds the record to the
				new user queue, which must be processed by an administrator before the record
				becomes active. This system prevents problems with securely assigning passwords
				and errors with data entry. Anyone can create one of these"""

				if not isinstance(user, User):
						try: user = User(user)
						except: raise ValueError, "User instance or dict required"
				#user=User(user.__dict__.copy())
				#user.validate()				

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
						user.creationtime = time.strftime(TIMESTR)
						user.modifytime = time.strftime(TIMESTR)
				
				user.validate()
				
				txn = self.newtxn()
				self.__newuserqueue.set(user.username, user, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				
				return user
				
				
				

								
								
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

				if self.checkreadadmin(ctx) or ctx.user == i:
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





		# ian todo: update. the find* functions need to be fast and good at fulltext searches for autocomplete functionality.
		# ian: redo? not sure...
		def findusername(self, name, ctxid=None, host=None):
				"""This will look for a username matching the provided name in a loose way"""

				ctx = self.__getcontext(ctxid, host)
				if ctx.user == None: return

				name = str(name)
				if self.__users.has_key(name) : return name
				
				possible = filter(lambda x: name in x, self.__users.keys())
				if len(possible) == 1 : return possible[0]
				if len(possible) > 1 : return possible
				
				possible = []
				for i in self.getusernames(ctxid=ctxid, host=host):
						try: u = self.getuser(name, ctxid=ctxid, host=host)
						except: continue
						
						for j in u.__dict__:
								if isinstance(j, str) and name in j :
										possible.append(i)
										break

				if len(possible) == 1 : return possible[0]
				if len(possible) > 1 : return possible
										
				return None
		
		
		
		
		@publicmethod
		def getworkflow(self, ctxid=None, host=None):
				"""This will return an (ordered) list of workflow objects for the given context (user).
				it is an exceptionally bad idea to change a WorkFlow object's wfid."""
				
				ctx = self.__getcontext(ctxid, host)
				if ctx.user == None: raise SecurityError, "Anonymous users have no workflow"
				
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
				
				
				
				

		@publicmethod
		def addworkflowitem(self, work, ctxid=None, host=None):
				"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""

				
				ctx = self.__getcontext(ctxid, host)

				if ctx.user == None:
						raise SecurityError, "Anonymous users have no workflow"

				if not isinstance(work, WorkFlow):
						try: work = WorkFlow(work)
						except: raise ValueError, "WorkFlow instance or dict required"
				#work=WorkFlow(work.__dict__.copy())
				work.validate()

				#if not isinstance(work,WorkFlow):
				#		 raise TypeError,"Only WorkFlow objects can be added to a user's workflow"
				
				txn = self.newtxn()
				self.__workflow.set_txn(txn)
				work.wfid = self.__workflow[ - 1]
				self.__workflow[ - 1] = work.wfid + 1

				if self.__workflow.has_key(ctx.user) :
								wf = self.__workflow[ctx.user]
				else:
						wf = []
						
				wf.append(work)
				self.__workflow[ctx.user] = wf
				self.__workflow.set_txn(None)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				return work.wfid
		
		
		
		
		#@write,user
		@publicmethod
		def delworkflowitem(self, wfid, ctxid=None, host=None):
				"""This will remove a single workflow object based on wfid"""
				#self = db
				
				ctx = self.__getcontext(ctxid, host)
				if ctx.user == None: raise SecurityError, "Anonymous users have no workflow"
				
				wf = self.__workflow[ctx.user]
				for i, w in enumerate(wf):
						if w.wfid == wfid :
								del wf[i]
								break
				else: raise KeyError, "Unknown workflow id"
				
				txn = self.newtxn()
				self.__workflow.set(ctx.user, wf, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				
				
				
				
		#@write,user
		@publicmethod
		def setworkflow(self, wflist, ctxid=None, host=None):
				"""This allows an authorized user to directly modify or clear his/her workflow. Note that
				the external application should NEVER modify the wfid of the individual WorkFlow records.
				Any wfid's that are None will be assigned new values in this call."""
				#self = db
				
				ctx = self.__getcontext(ctxid, host)
				if ctx.user == None: raise SecurityError, "Anonymous users have no workflow"
				
				if wflist == None : wflist = []
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
								w.wfid = self.__workflow[ - 1]
								self.__workflow.set(- 1, w.wfid + 1, txn)
				
				self.__workflow.set(ctx.user, wflist, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
		

		
		
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
						
						
						


		@publicmethod
		def addparamdef(self, paramdef, parents=[], ctxid=None, host=None):
			"""adds a new ParamDef object, group 0 permission is required
			a p->c relationship will be added if parent is specified"""


			if not isinstance(paramdef, ParamDef):
				try: paramdef = ParamDef(paramdef)
				except: raise ValueError, "ParamDef instance or dict required"
			#paramdef=ParamDef(paramdef.__dict__.copy())
			# paramdef.validate()
	
	
			ctx = self.__getcontext(ctxid, host)

			if not self.checkcreate(ctx):
				raise SecurityError, "No permission to create new paramdefs (need record creation permission)"

			paramdef.name = str(paramdef.name).lower()
			
			if self.__paramdefs.has_key(paramdef.name) : 
				# Root is permitted to force changes in parameters, though they are supposed to be static
				# This permits correcting typos, etc., but should not be used routinely
				# skip relinking if we're editing
				parents=[]
				if not self.checkadmin(ctx):
					raise KeyError, "paramdef %s already exists" % paramdef.name

			else:
				# force these values
				paramdef.creator = ctx.user
				paramdef.creationtime = time.strftime(TIMESTR)


			if not self.__importmode:
				paramdef.validate()


			# this actually stores in the database
			txn = self.newtxn()
			self.__paramdefs.set(paramdef.name, paramdef, txn)
			for parent in parents:
				self.pclink(parent, paramdef.name, "paramdef", txn=txn, ctxid=ctxid, host=host)
			if txn: txn.commit()
			elif not self.__importmode : DB_syncall()
				

				
		# ian: made ctxid required argument.
		#@write,user
		@publicmethod
		def addparamchoice(self, paramdefname, choice, ctxid=None, host=None):
				"""This will add a new choice to records of vartype=string. This is
				the only modification permitted to a ParamDef record after creation"""

				paramdefname = str(paramdefname).lower()
				
				# ian: change to only allow logged in users to add param choices. silent return on failure.
				ctx = self.__getcontext(ctxid, host)
				if not self.checkcreate(ctx):
						return

				d = self.__paramdefs[paramdefname]
				if d.vartype != "string":
						raise SecurityError, "choices may only be modified for 'string' parameters"
				
				d.choices = d.choices + (str(choice).title(),)
				txn = self.newtxn()
				self.__paramdefs.set(paramdefname, d, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()




		

		
		# ian: remove this method
		def findparamdefname(self, name, ctxid=None, host=None):
				"""Find a paramdef similar to the passed 'name'. Returns the actual ParamDef, 
or None if no match is found."""
				name = str(name).lower()
				if self.__paramdefs.has_key(name) : return name
				if name[ - 1] == "s" :
						if self.__paramdefs.has_key(name[: - 1]) : return name[: - 1]
						if name[ - 2] == "e" and self.__paramdefs.has_key(name[: - 2]): return name[: - 2]
				if name[ - 3:] == "ing" and self.__paramdefs.has_key(name[: - 3]): return name[: - 3]
				return None
		
		
		
		@publicmethod
		def getparamdefs(self, recs, filt=0, ctxid=None, host=None):
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
				

# 				key = str(key).lower()
# 				try:
# 						return self.__paramdefs[key]
# 				except:
# 						raise KeyError, "Unknown ParamDef: %s" % key

#					for i in recs:
#							if isinstance(i,str):
#									if not ret.has_key(i):
#											ret[i]=self.getparamdef(i)
#							elif isinstance(i,int):
#									j=self.getrecord(i,ctxid,host)
#									for k in j.getparamkeys():
#											if not ret.has_key(k):
#													ret[k]=self.getparamdef(k)								
#							elif isinstance(i,Record):
#									for k in i.getparamkeys():
#											if not ret.has_key(k):
#													ret[k]=self.getparamdef(k)
#							else:
#									continue
										
#					if isinstance(recs[0],str) :
#							for p in recs:
#									if ret.has_key(p) or p in ("comments","creationtime","permissions","creator","owner") : continue
#									try: 
#											ret[p]=self.__paramdefs[p]
#									except: 
#											raise KeyError,"Request for unknown ParamDef %s"%p #self.LOG(2,"Request for unknown ParamDef %s"%(p))
#					else:		 
#							for r in recs:
#									for p in r.keys():
#											if ret.has_key(p) or p in ("comments","creationtime","permissions","creator","owner") : continue
#											try:
#													ret[p]=self.__paramdefs[p]
#											except:
#													raise KeyError,"Request for unknown paramdef %s in %s"%(p,r.rectype) #self.LOG(2,"Request for unknown ParamDef %s in %s"%(p,r.rectype))				 




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
				

				
	
	
		@publicmethod
		def addrecorddef(self, recdef, parent=None, ctxid=None, host=None):
				"""adds a new RecordDef object. The user must be an administrator or a member of group 0"""


				if not isinstance(recdef, RecordDef):
						try: recdef = RecordDef(recdef)
						except: raise ValueError, "RecordDef instance or dict required"

				ctx = self.__getcontext(ctxid, host)

				recdef.validate()

				if not self.checkcreate(ctx):
						raise SecurityError, "No permission to create new RecordDefs"
						
				if self.__recorddefs.has_key(str(recdef.name).lower()):
						raise KeyError, "RecordDef %s already exists" % str(recdef.name).lower()

				recdef.findparams()
				pdn = self.getparamdefnames(ctxid=ctxid,host=host)
				for i in recdef.params:
						if i not in pdn: raise KeyError, "No such parameter %s" % i


				# force these values
				if (recdef.owner == None) : recdef.owner = ctx.user
				recdef.name = str(recdef.name).lower()
				recdef.creator = ctx.user
				recdef.creationtime = time.strftime(TIMESTR)


				if not self.__importmode:
						recdef=RecordDef(recdef.__dict__.copy())
						recdef.validate()
				
				# commit
				txn = self.newtxn()
				self.__recorddefs.set(recdef.name, recdef, txn)

				if parent:
					self.pclink(parent, recdef.name, "recorddef", txn=txn, ctxid=ctxid, host=host)

				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				return recdef.name




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

				if ctx.user != rd.owner and not self.checkadmin(ctx):
						raise SecurityError, "Only the owner or administrator can modify RecordDefs"

				if recdef.mainview != rd.mainview and not self.checkadmin(ctx):
						raise SecurityError, "Only the administrator can modify the mainview of a RecordDef"


				recdef.findparams()
				pdn = self.getparamdefnames(ctxid=ctxid,host=host)
				for i in recdef.params:
						if i not in pdn: raise KeyError, "No such parameter %s" % i

				# reset
				recdef.creator = rd.creator
				recdef.creationtime = rd.creationtime
				#recdef.mainview=rd.mainview		#temp. change to allow mainview changes

				if not self.__importmode:
						recdef = RecordDef(recdef.__dict__.copy())
						recdef.validate()

				# commit
				txn = self.newtxn()
				self.__recorddefs.set(recdef.name, recdef, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				

				
				
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
				
				if (ret.private and (ret.owner == ctx.user or ret.owner in ctx.groups or self.checkreadadmin(ctx))):
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
		
		
		# ian: reviewed to this point...
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
				
				if self.__recorddefs.has_key(name) : return name
				if name[ - 1] == "s" :
						if self.__recorddefs.has_key(name[: - 1]) : return name[: - 1]
						if name[ - 2] == "e" and self.__recorddefs.has_key(name[: - 2]): return name[: - 2]
				if name[ - 3:] == "ing" and self.__recorddefs.has_key(name[: - 3]): return name[: - 3]
				return None
		
		

				
		def __commitindices(self):
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
								print "... addref: %s, len: %s"%(k2, len(v2))#,v2)
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
						print "\tunindexable vartype ",f.vartype
						return None

				tp = self.vtm.getvartype(f.vartype).getindextype()

				#print "Open paramindex for %s: vartype=%s, keytype=%s"%(f.name,f.vartype,tp)


				if not create and not os.access("%s/index/%s.bdb" % (self.path, paramname), os.F_OK):
					raise KeyError, "No index for %s" % paramname
				
				# create/open index
				if self.__importmode:
						print "->MemBTree"
						self.__fieldindex[paramname] = MemBTree(paramname, "%s/index/%s.bdb" % (self.path, paramname), tp, self.__dbenv)
				else:
						self.__fieldindex[paramname] = FieldBTree(paramname, "%s/index/%s.bdb" % (self.path, paramname), tp, self.__dbenv)

				return self.__fieldindex[paramname]
				

		# testing...
		def __testreindex(self,q=None,ctxid=None,host=None):
				#recs=self.getindexbyrecorddef("subproject",ctxid=ctxid,host=host)
				#keys=self.getrecorddef("subproject",ctxid=ctxid,host=host).paramsK+("creator",)
				keys=sorted(self.getparamdefnames(),reverse=True)
				oq=q or "catalase"
				oq=str(oq).lower()
				#keys=self.getparamdefnames()
				#[:500])#-set(["visualization_bitrate"])
				#keys=["url"]

				for key in keys:
					f = self.__paramdefs[key]
					tp = self.vtm.getvartype(f.vartype).getindextype()
					print "Trying key: %s, vartype is %s, tp is %s"%(key, f.vartype, tp)

					if tp != None:

						if tp=="f":
							try: q=float(oq)
							except: q=None
						elif tp=="d":
							try: q=int(oq)
							except: q=None
						elif tp=="s":
							try: q=str(oq)
							except: q=None

						if q==None: continue

						bdb=db.DB(globalenv)
						bdb.index_open("%s/index/%s.bdb" % (self.path, key),tp,key,db.DB_BTREE,dbopenflags)
						print "\topened, keys: %s"%len(bdb)
						if bdb.has_key(q):
							print "\tdirect test: %s"%(bdb.index_get(q))
						bdb.close()

						#bt=FieldBTree(key, "%s/index/%s.bdb" % (self.path, key), tp, self.__dbenv)
						#try:
						#	print "\tindirect: %s"%bt.get(q)
						#except:
						#	print "\tindirect error"
						#bt.close()

				print "done"
				
				
		def __reindexmanyrecs(self, key, oparamdict, nparamdict, txn=None):
				"""This function reindexes a single key/value pair
				This includes creating any missing indices if necessary"""

				#print "REINDEX: key: %s, oldval: %s, newval: %s, recid: %s"%(key,oldval,newval,recid)
				if (key == "comments" or key == "permissions") : return				 # comments & permissions are not currently indexed 

				f=self.__paramdefs[key]
				if f.vartype not in self.indexablevartypes:
					print "Unindexable vartype %s"%f.vartype
					return
				
				# Painful, but if this is a 'text' field, we index the words not the value
				# ie - full text indexing				
				if f.vartype == "text":pass
#					for oldval, newval in  zip(oldvals, newvals):
#						return self.__reindextext(key, oldval, newval, recid)
				
				# whew, not full text, get the index for this key
				ind = self.__getparamindex(key)

				if ind == None:
					return
				
				# remove the old ref and add the new one
				print oparamdict
				for x in oparamdict:pass
				for oval in oparamdict:
					#g.debug('ind.removerefs(',oval,',', '%r' % oparamdict[oval])
					if oval is not None:
						ind.removerefs(oval, oparamdict[oval], txn=txn)
				for nval in nparamdict:
					g.debug('ind.addrefs(',nval,',', '%r' % nparamdict[nval])
					ind.addrefs(nval, nparamdict[nval], txn=txn)
				#print ind.items()


		def __reindex(self, key, oldval, newval, recid, txn=None):
				"""This function reindexes a single key/value pair
				This includes creating any missing indices if necessary"""

				#print "REINDEX: key: %s, oldval: %s, newval: %s, recid: %s"%(key,oldval,newval,recid)
				if (key == "comments" or key == "permissions") : return				 # comments & permissions are not currently indexed 

				if (oldval == newval) : return				# no change, no indexing required

				f=self.__paramdefs[key]
				if f.vartype not in self.indexablevartypes:
					print "Unindexable vartype %s"%f.vartype
					return
				
				# Painful, but if this is a 'text' field, we index the words not the value
				# ie - full text indexing				
				if f.vartype == "text":
					return self.__reindextext(key, oldval, newval, recid)
				
				# whew, not full text, get the index for this key
				ind = self.__getparamindex(key)

				if ind == None:
					return
				
				if ind == "child" or ind == "link":
						print "reindex, child or link"
						# make oldval and newval into sets
						try: oldval = set((int(oldval),))
						except: 
								if oldval == None : oldval = set()
								else: oldval = set(oldval)
						try: newval = set((int(newval),))
						except: 
								if newval == None : newval = set()
								else : newval = set(newval)
								
						i = oldval & newval				 # intersection
						oldval -= i
						newval -= i
						# now we know that oldval and newval are unique
						if (not self.__importmode) : 
							if ind == "child" :
								for i in oldval: self.__records.pcunlink(recid, i, txn=txn)
								for i in newval: self.__records.pclink(recid, i, txn=txn)
								return
						
							if ind == "link" :
								for i in oldval: self.__records.unlink(recid, i, txn=txn)
								for i in newval: self.__records.link(recid, i, txn=txn)
								return
						else:
								return

				# remove the old ref and add the new one
				if oldval != None:
					ind.removeref(oldval, recid, txn=txn)
				if newval != None:
					ind.addref(newval, recid, txn=txn)
				#print ind.items()



		#@write,private
		def __reindextext(self, key, oldval, newval, recid, txn=None):
				"""This function reindexes a single key/value pair
				where the values are text strings designed to be searched
				by 'word' """

				unindexed_words = set(["in", "of", "for", "this", "the", "at", "to", "from", "at", "for", "and", "it", "or"])				# need to expand this
				
				ind = self.__getparamindex(key)
				if ind == None:
						g.debug.msg('LOG_ERROR', 'No parameter index for ', key)
						return
				
				# remove the old ref and add the new one
				if oldval != None:
						for s in set([x.lower() for x in oldval.split()])-unindexed_words:
							ind.removeref(s,recid,txn=txn)		
		
				if newval != None:
						for s in set([x.lower() for x in newval.split()])-unindexed_words:
							ind.addref(s,recid,txn=txn)
				
				#print ind.items()



		def __reindexsec2(self, items, txn=None):
			# item format:
			# [recid, newusers, oldusers]
			deluser=set(reduce(lambda x,y:x+y, [i[2] for i in items]))
			deluser=dict([[i,[]] for i in deluser])
			adduser=set(reduce(lambda x,y:x+y, [i[1] for i in items]))
			adduser=dict([[i,[]] for i in adduser])

			for i in items:
				for j in i[2]:
					deluser[j].append(i[0])
				for j in i[1]:
					adduser[j].append(i[0])


			print deluser
			
			for user in deluser.keys()+adduser.keys():
				deluser[user]=set(deluser.get(user,[]))
				adduser[user]=set(adduser.get(user,[]))
				deluser[user] -= adduser[user]
				if deluser[user]:
					self.__secrindex.removerefs(user, deluser[user], txn=txn)
				if adduser[user]:
					self.__secrindex.addrefs(user, adduser[user], txn=txn)
				
				

		#@write,private
		def __reindexsec(self, oldlist, newlist, recid, txn=None):
				"""This updates the security (read-only) index
				takes two lists of userid/groups (may be None)"""
#				 print "reindexing security.."
#				 print oldlist
#				 print newlist
				o = set(oldlist)
				n = set(newlist)
				
				uo = o - n		# unique elements in the 'old' list
				un = n - o		# unique elements in the 'new' list
#				 print o,n,uo,un

				# anything in both old and new should be ok,
				# So, we remove the index entries for all of the elements in 'old', but not 'new'
				for i in uo:
#						 print i," ",len(self.__secrindex[i]),self.__secrindex.testref(i,recid)
						self.__secrindex.removeref(i, recid, txn=txn)
#				 print "now un"
				# then we add the index entries for all of the elements in 'new', but not 'old'
				for i in un:
						self.__secrindex.addref(i, recid, txn=txn)


		@publicmethod
		def publish(self, recids, policy="anonymous", allresources=0, resources=None, children=0, includerectypes=None, excluderectypes=None, ctxid=None, host=None, txn=None):
			"""Mark records available for cloning to selected resources
			policy = access policy on clone server
			resources = which resources can access published records
			allchildren = include children
			childrectypes = include children of this rectype
			"""

			if not hasattr(recids,"__iter__"):
				recids=[recids]
			recids=set(recids)

			policydef=self.getparamdef("publish")
			if policy not in policydef.choices:
				raise Exception,"Invalid policy %s; options=%s"%(policy,policydef.choices)
				
							
			resources=set(resources or [])
			includerectypes=set(includerectypes or [])
			excluderectypes=set(excluderectypes or [])


			if len(includerectypes) > 0 and len(excluderectypes) > 0:
				raise Exception,"includerectypes/excluderectypes are mutually exclusive"

			childids = set()
			if children:
				child = self.getchildren(recids, recurse=self.maxrecurse, ctxid=ctxid, host=host)
				childids = reduce(lambda x,y:x|y,child.values())
			
			#recs=self.getrecord(recids | childids,filter=1,ctxid=ctxid,host=host)
			#rectypes=dict([(rec.recid,rec.rectype) for rec in recs])
			rectypes = self.groupbyrecorddef(recids | childids, ctxid=ctxid, host=host)

			if len(includerectypes) == 0:
				recids |= childids

			for i in includerectypes:
				recids |= rectypes.get(i,set())

			for i in excluderectypes:
				recids -= rectypes.get(i,set())

			if len(recids)==0:
				raise Exception,"No records to publish"
			

			print recids

			# group -5 is resources
			if allresources:
				resources = [-5]
			else:
				resources = map(lambda x:x.username, filter(lambda x:-5 in x.groups, self.getuser(resources,ctxid=ctxid,host=host).values()))
				if len(resources)==0:
					raise Exception,"No valid resources"
			
							
			ret=[]
			for i in recids:
				try:
					print "adding %s to %s"%(resources,i)
					self.putrecordvalue(i,"publish",policy,ctxid=ctxid,host=host,txn=txn)
					self.secrecordadduser([resources,[],[],[]],i,ctxid=ctxid,host=host,txn=txn)
					ret.append(i)
				except Exception,inst:
					print "Error publishing recid %s:%s"%(i,inst)
				
			return ret
			

		@publicmethod
		def unpublish(self, recids, children=0, ctxid=None, host=None, txn=None):
			pass



		@publicmethod
		def putrecordvalue(self, recid, param, value, ctxid=None, host=None, txn=None):
				"""Make a single change to a single record"""
				rec = self.getrecord(recid, ctxid=ctxid, host=host)
				rec[param] = value
				self.putrecord(rec, ctxid=ctxid, host=host)
				return self.getrecord(recid, ctxid=ctxid, host=host)[param]



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


				
		@publicmethod
		def putrecordsvalues(self, d, ctxid=None, host=None):
				"""Make multiple changes to multiple records"""
				
				ret = {}
				for k, v in d.items():
						ret[k] = self.putrecordvalues(k, v, ctxid=ctxid, host=host)
				return ret
				
		
		
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


												

		def __formatusername(self,username,u,lnf=1):
				if u["name_first"] and u["name_middle"] and u["name_last"]:
						if lnf:		 uname = "%s, %s %s" % (u["name_last"], u["name_first"], u["name_middle"])
						else:		 uname = "%s %s %s" % (u["name_first"], u["name_middle"], u["name_last"])
		
				elif u["name_first"] and u["name_last"]:
						if lnf: uname = "%s, %s" % (u["name_last"], u["name_first"])
						else: uname = "%s %s" % (u["name_first"], u["name_last"])
				
				elif u["name_last"]:
						uname = u["name_last"]
				
				elif u["name_first"]:
						uname = u["name_first"]
						
				else:
						return username

				return uname

		

		def __putnewrecord(self, record, parents=[], children=[], ctxid=None, host=None):
			# Record must not exist, lets create it
			
			ctx = self.__getcontext(ctxid, host)
			
			if not isinstance(record, Record):
					try: record = Record(record, ctx)
					except: raise ValueError, "Record instance or dict required"
			
			
			# security check / validate input
			record.setContext(ctx)
			record.validate()


			if not self.checkcreate(ctx):
					txn and txn.abort()
					raise SecurityError, "No permission to create records"

			#	txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
			txn = self.newtxn()

			record.recid = self.__records.get(- 1, txn)

			record._Record__creator = ctx.user
			record._Record__creationtime = time.strftime(TIMESTR)
			
			if not self.__importmode:
				record["modifytime"] = record["creationtime"]
				record["modifyuser"] = ctx.user
				
				

			if not self.__importmode:
				df = file("/tmp/dbbug3", "a")
				print >> df, "%s\n%s\n" % (str(ctx.__dict__), str(record))
				df.close()


			self.__records.set(record.recid, record, txn)				 # This actually stores the record in the database
			self.__recorddefbyrec.set(record.recid, record.rectype, txn)
		
			# index params
			for k, v in record.items():
				if k != 'recid':
					self.__reindex(k, None, v, record.recid, txn)

			self.__reindexsec([], reduce(operator.concat, record["permissions"]), record.recid, txn=txn)				 # index security
			self.__recorddefindex.addref(record.rectype, record.recid, txn)						 # index recorddef
			self.__timeindex.set(record.recid, record["creationtime"], txn)
		
			self.__records.set(- 1, record.recid + 1, txn)						 # Update the recid counter, TODO: do the update more safely/exclusive access
														
			#print "putrec->\n",record.__dict__
			#print "txn: %s" % txn
			if txn: txn.commit()
		
			elif not self.__importmode : DB_syncall()
		
			# ian todo: restore this
			#try:
			#		 self.__validaterecordaddchoices(record,ctxid)
			#except:
			#		 print "Unable to add choices to paramdefs."
		
			# ian
			if type(parents) == int: parents = set([parents])
			for i in parents:
					#print "...linking %s -> %s"%(i,record.recid)
					self.pclink(i, record.recid, ctxid=ctxid, host=host)

			if type(children) == int: children = set([children])
			for i in children:
					self.pclink(record.recid, i, ctxid=ctxid, host=host)
								
			return record.recid			


		@publicmethod
		def clonerecord(self, recs, ctxid=None, host=None, txn=None):
			"""clone records; fix this up and integrate with putrecord"""

			ctx=self.__getcontext(ctxid,host)
			if not self.checkadmin(ctx):
				raise Exception,"Only administrators may clone"
			
			dictrecs=filter(lambda x:isinstance(x,dict), recs)
			dictrecs=map(lambda x:Record(x), dictrecs)
			recs.extend(dictrecs)		
			updrecs=filter(lambda x:isinstance(x,Record), recs)

			ind=dict([(i,[]) for i in self.getparamdefnames(ctxid=ctxid,host=host)])			
			ret=[]
			orecs=[]
			pc=[]
			cp=[]
			secrupdate=[]
			timeupdate={}			
			
			for offset, rec in enumerate(updrecs):
				pc.extend([(i,rec.recid) for i in rec.get("parents",[])])
				cp.extend([(rec.recid,i) for i in rec.get("children",[])])
				rec["children"]=None
				rec["parents"]=None
				rec["permissions"]=((-3,),(),(),())
				
				for param in filter(lambda x:rec.get(x), rec.keys()):
					ind[param].append((rec.recid,rec[param],None))		

				secr=[rec.recid, reduce(operator.concat, rec["permissions"]), []]
				secrupdate.append(secr)
				timeupdate[rec.recid]=rec.get("modifytime")
				orecs.append(rec)

			if not txn:
				txn=self.newtxn()			

			#maxrecid = self.__records.get(-1)
			#newmax = max([i.recid for i in orecs])
			#if newmax > maxrecid:
			#	self.__records.set(-1, maxrecid+1)
			
			for orec in orecs:
				self.__records.set(orec.recid, orec, txn=txn)
				self.__recorddefbyrec.set(orec.recid, orec.rectype, txn=txn)
				self.__recorddefindex.addref(orec.rectype, orec.recid, txn=txn)			
	
			# Now update indices
			for k,v in filter(lambda x:x[1],ind.items()):
				try: self.__reindex2(k,v)
				except Exception, inst: print "Could not index %s: %s"%(k,inst)

			if secrupdate:
				self.__reindexsec2(secrupdate, txn=txn)

			for k,v in timeupdate.items():
				self.__timeindex.set(k, v, txn=txn)

			# create links
			for link in pc+cp:
				try: self.pclink(link[0],link[1],ctxid=ctxid,host=host)
				except: print "couldn't link %s -> %s"%(link[0],link[1])


		@publicmethod
		def putrecord2(self, recs, warning=0, clone=0, ctxid=None, host=None, txn=None):
			"""test"""
			
			ctx=self.__getcontext(ctxid,host)

			if warning and not self.checkadmin(ctx):
				raise Exception,"Only administrators may bypass record validation"	

			ol=0
			if isinstance(recs,Record):
				ol=1
				recs=[recs]
				
				
			dictrecs=filter(lambda x:isinstance(x,dict), recs)
			dictrecs=map(lambda x:Record(x), dictrecs)
			recs.extend(dictrecs)		
			
			updrecs=filter(lambda x:isinstance(x,Record), recs)

			ret=[]
			
			ind=dict([(i,[]) for i in self.getparamdefnames(ctxid=ctxid,host=host)])
			orecs=[]
			nrecs=[]
			pc=[]
			cp=[]
			
			secrupdate=[]
			timeupdate={}
			baserecid=self.__records.get(-1, txn=txn)
			
						
			for offset,rec in enumerate(updrecs):
				t = time.strftime(TIMESTR)
				newrecord = 0
				
				#print "putrecord2 processing: %s"%rec.recid
				
				try:
					orec = self.getrecord(rec.recid, ctxid=ctxid, host=host)					

				except TypeError, inst:
					if not self.checkcreate(ctx):
						raise SecurityError, "No permission to create records"
					# new record here... assign negative recid
					newrecord = 1
					orec = Record()
					rec.setContext(ctx)
					orec.setContext(ctx)
					orec.recid = (baserecid+offset+1)*-1
					orec.rectype = rec.rectype
					orec._Record__creator = ctx.user
					orec._Record__creationtime = t
				
				# why isn't this working normally...
				test1=rec.get("parents") or []
				test2=rec.get("children") or []
				pc.extend([(i,orec.recid) for i in test1])
				cp.extend([(orec.recid,i) for i in test2])
				rec["children"]=None
				rec["parents"]=None
					
				cp=rec.changedparams(orec)
				
				if len(cp)==0 and not newrecord:
					print "No changes"
					continue				
				
				print "putrecord2 recid: %s cp: %s"%(orec.recid,cp)
				
				if not self.__importmode:
					ind["modifytime"].append((orec.recid,t,orec.get("modifytime")))
					ind["modifyuser"].append((orec.recid,ctx.user,orec.get("modifyuser")))
					orec["modifytime"] = t
					orec["modifyuser"] = ctx.user
				
				for i in rec["comments"]:
					if i not in orec._Record__comments:
						orec._Record__comments.append(i)
						
				for param in cp:
					if not newrecord:
						orec._Record__comments.append((ctx.user, t, u"LOG: %s updated. was: %s" % (orec.recid, orec[param])))
					ind[param].append((orec.recid,rec[param],orec[param]))		
					orec[param]=rec[param]
			
				
				if rec["permissions"] != orec["permissions"]:
					secr=[orec.recid, set(reduce(operator.concat, rec["permissions"])), set(reduce(operator.concat, orec["permissions"]))]
					secrupdate.append(secr)

				timeupdate[orec.recid]=t
				
				orec.validate(warning=warning)

				if newrecord:
					nrecs.append(orec)
				else:
					orecs.append(orec)
				
				

			if not txn:
				txn=self.newtxn()			

			print "putrecord2: recs to update: %s"%len(orecs)
			
			for orec in orecs:
				self.__records.set(orec.recid, orec, txn=txn)				 # This actually stores the record in the database

			if nrecs:
				print "putrecord2: recs to add: %s"%len(nrecs)
				recidmap={}
				count=len(nrecs)
				# update rec counter
				baserecid=self.__records.get(-1, txn=txn)
				self.__records.set(-1, baserecid + count, txn=txn)

				for offset,orec in enumerate(nrecs):
					newrecid=offset+baserecid
					print "new record: prov=%s final=%s"%(orec.recid,newrecid)
					recidmap[orec.recid]=newrecid
					orec.recid=newrecid
					self.__records.set(orec.recid, orec, txn=txn)
					self.__recorddefbyrec.set(orec.recid, orec.rectype, txn=txn)
					self.__recorddefindex.addref(orec.rectype, orec.recid, txn=txn)	

				# adjust indices
				for k,v in ind.items():
					v=map(lambda x:(recidmap.get(x[0],x[0]),x[1],x[2]), v)
					ind[k]=v

				secrupdate=map(lambda x:(recidmap.get(x[0],x[0]), x[1], x[2]), secrupdate)

				t2=map(lambda x:(recidmap.get(x[0],x[0]),x[1]), timeupdate.items())
				timeupdate=dict(t2)
				
				pc=map(lambda x:(recidmap.get(x[0],x[0]), recidmap.get(x[1],x[1])), pc)
				cp=map(lambda x:(recidmap.get(x[0],x[0]), recidmap.get(x[1],x[1])), cp)
			
			

			# Now update indices
			for k,v in filter(lambda x:x[1],ind.items()):
				try:
					self.__reindex2(k,v)
				except Exception, inst:
					print "Could not index %s: %s"%(k,inst)

			if secrupdate:
				self.__reindexsec2(secrupdate, txn=txn)

			for k,v in timeupdate.items():
				self.__timeindex.set(k, v, txn=txn)

			# create links
			for link in pc:
				try:
					self.pclink(link[0],link[1],ctxid=ctxid,host=host)
				except:
					print "couldn't link"

			for link in cp:
				try:
					self.pclink(link[0],link[1],ctxid=ctxid,host=host)
				except:
					print "couldn't link"
			
			# fix returns
			#if ol:
			#	return [orecs][0].recid
			#return orecs
			#return [i.recid for i in orecs]
			
			
			

		def __reindex2(self, key, items, txn=None):
			# items format:
			# [recid, newval, oldval]
			
			pd = self.__paramdefs[key]
			
			
			if pd.vartype not in self.indexablevartypes or pd.name in ["recid","comments"]:
				print "Unindexable vartype: %s"%pd.vartype
				return

			ind = self.__getparamindex(key)
			if ind == None:
				return			
							
			# remove oldval=newval; strip out wrong keys
			items = filter(lambda x:x[1]!=x[2], items)

			# these vartypes require special indexing
			#if pd.vartype=="comments":
			#	return
			if pd.vartype=="text":
				return self.reindextext2(key,items)
				
			oldvals = dict([[i,set()] for i in set([i[2] for i in items])])
			newvals = dict([[i,set()] for i in set([i[1] for i in items])])
			for i in items:
				oldvals[i[2]].add(i[0])
				newvals[i[1]].add(i[0])
			
			if oldvals.has_key(None): del oldvals[None]
			if newvals.has_key(None): del newvals[None]
				
			for oldval,recs in oldvals.items():
				print "reindex: param: %s, removerefs: %s, recs: %s"%(key,oldval,recs)
				ind.removerefs(oldval, recs, txn=txn)
			for newval,recs in newvals.items():
				print "reindex: param: %s, addrefs: %s, recs: %s"%(key,newval,recs)
				ind.addrefs(newval, recs, txn=txn)
						


		@publicmethod
		def reindextext2(self, key, items, txn=None):
			# ind is already ok and indexable, items is filtered for unchanged items
			ind = self.__getparamindex(key)

			allwords=[i[2].lower() for i in items if isinstance(i[2],basestring)] + [i[1].lower() for i in items if isinstance(i[1],basestring)]
			allwords=set(reduce(lambda x,y: x+y, [x.split() for x in allwords]))
			# lprint "allwords: %s"%allwords
			# key=word, val=recids
			addrefs=dict([i,[]] for i in allwords)
			delrefs=dict([i,[]] for i in allwords)
			
			for item in items:
				otxt=[]
				ntxt=[]
				if isinstance(item[2],basestring):
					otxt=[i.lower() for i in item[2].split()]
				if isinstance(item[1],basestring):
					ntxt=[i.lower() for i in item[1].split()]
				for i in otxt:
					delrefs[i].append(i[0])
				for i in ntxt:
					addrefs[i].append(i[0])	
			
			for i in allwords:
				# make set, remove unchanged items
				addrefs[i] = set(addrefs[i])
				delrefs[i] = set(delrefs[i])
				u = addrefs[i] & delrefs[i]
				addrefs[i] -= u
				delrefs[i] -= u

			for word in allwords - self.unindexed_words:
				if delrefs[word]:
					print "reindex text: param:%s delrefs: %s, recs: %s"%(key, word, delrefs[word])
					ind.removerefs(key, delrefs[word], txn=txn)
				if addrefs[word]:
					print "reindex text: param:%s delrefs: %s, recs: %s"%(key, word, delrefs[word])
					ind.addrefs(key, addrefs[word], txn=txn)
						


		#@write,user
		@publicmethod
		def putrecord(self, records, parents=[], children=[], ctxid=None, host=None, txn=None):
				"""The record has everything we need to commit the data. However, to 
				update the indices, we need the original record as well. This also provides
				an opportunity for double-checking security vs. the original. If the 
				record is new, recid should be set to None. recid is returned upon success. 
				parents and children arguments are conveniences to link new records at time of creation."""

				ctx = self.__getcontext(ctxid, host)
				orecords, results = [], set([])
				recdict = {}
				cp = dict()
				
				_recs = records
				if not isinstance(records, list):
					_recs = [records]

				for record in _recs:
					g.debug('record -> %r' % record)

					if not isinstance(record, Record):
							try: record = Record(record, ctx)
							except: raise ValueError, "Record instance or dict required"

					if record.recid is None:
						results.add(self.__putnewrecord(record, ctxid=ctxid, parents=parents, children=children, host=host))
						continue
					else:
						orecord = self.__records[record.recid]				 # get the unmodified record
						orecords.append(orecord)
						recdict[record.recid] = orecord

					# security check on the original record	
					# copy old record to check for changed values
					record.setContext(ctx)
					orecord.setContext(ctx)

					record.validate(orecord)
					ncp = record.changedparams(orecord)

					# permissions can be changed using putrecord again, pref using adduser/removeuser
					if len(ncp)==0:
						results.add("Record %d: No changes made" % record.recid)
						del recdict[record.recid]
					else:
						for x in ncp:
							if cp.has_key(x):
								cp[x].append((record, orecord))
							else:
								cp[x] = [(record, orecord)]
						g.debug('cp -> %r' % cp)
		
						if not txn:
							txn = self.newtxn()
		
		
						# Now update the indices
						log = []
		
		
						# Update: modifytime / modifyuser
						if (not self.__importmode): 
								orecord["modifytime"] = time.strftime(TIMESTR)
								orecord["modifyuser"] = ctx.user
								self.__timeindex.set(record.recid, 'modifytime', txn)
	
	
						# Update: comments
						#print "orecord._Record__comments: %s"%orecord._Record__comments
						for i in log:
							if not i in orecord._Record__comments:
								orecord._Record__comments.append(i)
	
						for i in record["comments"]:
							if not i in orecord._Record__comments:
								orecord._Record__comments.append(i)
### indexing
				for name, recs in cp.items(): #record.param_special
						newvals, oldvals, recids = [],[], []
						for new, old in recs:
							newvals.append(new[name])
							oldvals.append(old[name])
							recids.append(new.recid)
						oparamdict = {}
						nparamdict = {}
						for nv, ov, recid in zip(newvals, oldvals, recids):
							if type(nv) == list: nv = tuple(nv)
							if type(ov) == list: ov = tuple(nv)
							g.debug('nv = <%r>, ov = <%r>, recid = <%r>' % (nv, ov, recid))
							if nparamdict.has_key(nv): nparamdict[nv].append(recid)
							else: nparamdict[nv] = [recid]
							if oparamdict.has_key(ov): oparamdict[ov].append(recid)
							else: oparamdict[ov] = [recid]
						self.__reindexmanyrecs(name, oparamdict, nparamdict)
						for rec, orec in recs:
							log.append((ctx.user, time.strftime(TIMESTR), u"LOG: %s updated. was: %s" % (name, orec[name])))
							orec[name] = rec[name]
						
				# Update: permissions
				# index security
				for rec, orec in zip(recdict.values(), orecords):
					self.__reindexsec(reduce(operator.concat, orec["permissions"]),
							reduce(operator.concat, rec["permissions"]), rec.recid, txn)
				
				
#				# This actually stores the record in the database
				self.__records.update(recdict)
				results.update(recdict.keys())
				for orecord in orecords:
					# recdef index
					self.__recorddefbyrec.set(orecord.recid, orecord.rectype, txn)
				if txn: txn.commit()
				elif not self.__importmode : DB_syncall()
				if not hasattr(records, 'commit'):
					return results
				else:
					return results.pop()



		# ian: todo: improve newrecord/putrecord	
		@publicmethod
		def newrecord(self, rectype, init=0, inheritperms=None, ctxid=None, host=None):
				"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
				already exist)."""

				ctx = self.__getcontext(ctxid, host)

				rec = Record()
				rec.setContext(ctx)
				
				# try to get the RecordDef entry, this still may fail even if it exists, if the
				# RecordDef is private and the context doesn't permit access
				t = self.getrecorddef(rectype, ctxid=ctxid, host=host)

				rec.recid = None
				rec.rectype = rectype												 # if we found it, go ahead and set up
								
				if init:
					rec.update(t.params)
						#for k, v in t.params.items():
						#		if v:
						#				rec[k] = v												# hmm, in the new scheme, perhaps this should just be a deep copy

				# ian
				if inheritperms != None:
						#if self.trygetrecord(inheritperms, ctxid=ctxid, host=host):
						try:
								prec = self.getrecord(inheritperms, ctxid=ctxid, host=host)
								n = []
								for i in range(0, len(prec["permissions"])):
										n.append(prec["permissions"][i] + rec["permissions"][i])
								rec["permissions"] = tuple(n)				 
						except:
								pass

				rec.adduser(3,ctx.user)

				# make sure we have ownership
				#rec["permissions"][3] = rec["permissions"][3] + (ctx.user,)
				
				return rec


		
		
		@publicmethod		
		def getrecordschangetime(self, recids, ctxid=None, host=None):
				"""Returns a list of times for a list of recids. Times represent the last modification 
				of the specified records"""
				#self = db

				#secure = set(self.getindexbycontext(ctxid=ctxid, host=host))
				#rid = set(recids)
				#rid -= secure
				recids = self.filterbypermissions(recids,ctxid=ctxid,host=host)
				if len(rid) > 0 : raise Exception, "Cannot access records %s" % str(rid)
				
				try: ret = [self.__timeindex[i] for i in recids]
				except: raise Exception, "unindexed time on one or more recids"
				
				return ret 
				
				

		@publicmethod
		def getindexbycontext(self, ctxid=None, host=None):
				"""This will return the ids of all records a context has permission to access as a set. Does include groups.""" 

				ctx = self.__getcontext(ctxid, host)

				if self.checkreadadmin(ctx):
						return set(range(self.__records[-1]))#+1)) ###Ed: Fixed an off by one error

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

			if self.checkreadadmin(ctx):
				return set(recids)

			recids=set(recids)


			# this is usually the fastest
			# method 2
			#ret=set()
			ret=[]
			ret.extend(recids & set(self.__secrindex[ctx.user]))
			#ret |= recids & set(self.__secrindex[ctx.user])
			#recids -= ret
			for group in sorted(ctx.groups,reverse=True):
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
				if self.checkreadadmin(ctx):
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

		@publicmethod
		def getrecord(self, recid, filt=1, dbid=0, ctxid=None, host=None):
				"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
				if dbid is 0, the current database is used. host must match the host of the
				context"""

				#print "GETRECORD %s ctxid=%s %s"%(recid,ctxid,type(ctxid))
				
				ctx = self.__getcontext(ctxid, host)
				
				if (dbid != 0):
					raise NotImplementedError("External database support not yet available") #Ed Changed to NotimplementedError
				
				if not hasattr(recid,"__iter__"):
					chop=1
					recid=[int(recid)]
				else:
					chop=0
				
				#recl = map(lambda x:self.__records[int(x)], recid)				
				recid = map(lambda x:int(x), recid)
				
				ret=[]
				for i in recid:
					try:
						rec=self.__records[i]
						rec.setContext(ctx)
						ret.append(rec)
					except SecurityError, e:
						# if filtering, skip record; else bubble (SecurityError) exception
						if filt: pass
						else: raise e

				if len(ret)==1 and chop: return ret[0]
				return ret



				

				
								
				

		@publicmethod				
		def getparamvalue(self, paramname, recid, dbid=0, ctxid=None, host=None):
				#slow and insecure needs indexes for speed

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


		
		
		
		# ian todo: check this thoroughly
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
				if self.checkadmin(ctx):
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
						if ctx.user not in rec["permissions"][3] and not self.checkadmin(ctx): continue				 
						
						#print "rec: %s" % i
						
						cur = [set(v) for v in rec["permissions"]]				# make a list of sets out of the current permissions
						xcur = [set(v) for v in rec["permissions"]]				 # copy of cur that will be changed
#						 l=[len(v) for v in cur]		#length test not sufficient # length of each tuple so we can decide if we need to commit changes
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
		
		
		
		# ian: moved host to end. see notes above.
		#@write,user
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
				if self.checkadmin(ctx): isroot = 1
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
		@g.debug.debug_func
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

				
		# ian: moved host to end
		#@write,private
		def _backup(self, users=None, paramdefs=None, recorddefs=None, records=None, workflows=None, bdos=None, outfile=None, ctxid=None, host=None):
				"""This will make a backup of all, or the selected, records, etc into a set of files
				in the local filesystem"""

				#if user!="root" :
				ctx = self.__getcontext(ctxid, host)
				if not self.checkadmin(ctx):
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

				if not self.checkadmin(ctx):
						raise SecurityError, "Database restore requires admin access"

				if os.access(str(restorefile), os.R_OK):
					fin = open(restorefile, "r")

				if os.access(self.path + "/backup.pkl", os.R_OK):
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
				
				#print "begin restore"
				#print load(fin)
				
				while (1):
						try:
								r = load(fin)
						except Exception, inst:
								print inst
								break
						
						# new transaction every 100 elements
						#if nel%100==0 :
								#if txn : txn.commit()
								#txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
								
						nel += 1
						if txn: txn.commit()
						else : 
								if nel % 500 == 0 : 
#										 print "SYNC:",self.__dbenv.lock_stat()["nlocks"]," ... ",
										DB_syncall()
#										 print self.__dbenv.lock_stat()["nlocks"]
#										 time.sleep(10.0)
#										 print self.__dbenv.lock_stat()["nlocks"]

						txn = self.newtxn()
						
						
						#print type(r)
						
						# insert User
						if isinstance(r, User) :
								print "user: %s"%r.username
								if self.__users.has_key(r.username, txn) :
										print "Duplicate user ", r.username
										self.__users.set(r.username, r, txn)
								else :
										self.__users.set(r.username, r, txn)
						# insert Workflow
						elif isinstance(r, WorkFlow) :
								print "workflow: %s"%r.wfid
								self.__workflow.set(r.wfid, r, txn)
						# insert paramdef
						elif isinstance(r, ParamDef) :
								print "paramdef: %s"%r.name
								r.name = r.name.lower()
								if self.__paramdefs.has_key(r.name, txn):
										print "Duplicate paramdef ", r.name
										self.__paramdefs.set(r.name, r, txn)
								else :
										self.__paramdefs.set(r.name, r, txn)
						# insert recorddef
						elif isinstance(r, RecordDef) :
								print "recorddef: %s"%r.name
								r.name = r.name.lower()
								if self.__recorddefs.has_key(r.name, txn):
										print "Duplicate recorddef ", r.name
										self.__recorddefs.set(r.name, r, txn)
								else :
										self.__recorddefs.set(r.name, r, txn)

						# insert and renumber record
						elif isinstance(r, Record) :
										
								#try:
								#		o = r._Record__owner
								#		a = r._Record__permissions
								#		r._Record__permissions = (a[0], a[1], a[2], (o,))
								#		del r._Record__owner
								#except:
								#		pass
								
								# renumbering
								nrec += 1
								if nrec % 1000 == 0 :
										print "%8d records	 (%f/sec)\r" % (nrec, nrec / (time.time() - t0))
										sys.stdout.flush()


										
								oldid = r.recid
								# r.recid = self.__dbseq.get()																 # Get a new record-id
								r.recid = self.__records.get(- 1, txn)
								self.__records.set(- 1, r.recid + 1, txn)								# Update the recid counter, TODO: do the update more safely/exclusive access
								recmap[oldid] = r.recid
								self.__records.set(r.recid, r, txn)
								#self.__records.set(r.recid, {}, txn)
								self.__recorddefbyrec.set(r.recid, r.rectype, txn)
								#r.setContext(ctx)
								
								# work in progress. Faster indexing on restore.
								# Index record
								#for k, v in r.items():
								#		if self.__paramdefs[k].vartype in indexablevartypes:
								#				try:
								#						self.__reindex(k, None, v, r.recid, txn)
								#				except Exception, inst:
								#						pass
								#						#print "Error indexing %s (%s): %s"%(k,r.recid, inst)
								#						#print "\t%s"%inst
								#set(r.keys()) & indexableparams:
								for k,v in r.items(): 
									#if k != "number_exposure":
									#	continue
									try:
										self.__reindex(k, None, r[k], r.recid, txn)
									except Exception, inst:
										print "Error indexing %s (%s): %s"%(k,r.recid,inst)
								
								
								self.__reindexsec([], reduce(operator.concat, r["permissions"]), r.recid, txn)				# index security
								self.__recorddefindex.addref(r.rectype, r.recid, txn)						 # index recorddef
								self.__timeindex.set(r.recid, r["creationtime"], txn)

								
						elif isinstance(r, str):
								print "btree type: %s"%r
								if r == "bdos" :
										#print "bdo"
										rr = load(fin)						# read the dictionary of bdos
										for i, d in rr.items():
												self.__bdocounter.set(i, d, txn)
								elif r == "pdchildren" :
										#print "pdchildren"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for p, cl in rr:
												for c in cl:
														self.__paramdefs.pclink(p, c, txn)
								elif r == "pdcousins" :
										#print "pdcousins"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for a, bl in rr:
												for b in bl:
														self.__paramdefs.link(a, b, txn)
								elif r == "rdchildren" :
										#print "rdchildren"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for p, cl in rr:
												for c in cl:
														self.__recorddefs.pclink(p, c, txn)
								elif r == "rdcousins" :
										#print "rdcousins"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for a, bl in rr:
												for b in bl:
														self.__recorddefs.link(a, b, txn)
								elif r == "recchildren" :
										#print "recchildren"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for p, cl in rr:
												for c in cl:
#														 print p, c
#														 print recmap[p],recmap[c[0]],c[1]
														if isinstance(c, tuple) : print "Invalid (deprecated) named PC link, database restore will be incomplete"
														else : self.__records.pclink(recmap[p], recmap[c], txn)
								elif r == "reccousins" :
										#print "reccousins"
										rr = load(fin)						# read the dictionary of ParamDef PC links
										for a, bl in rr:
												for b in bl:
														self.__records.link(recmap[a], recmap[b], txn)
								else : print "Unknown category ", r
				
				print "Done!"
				
				if txn: 
						txn.commit()
						self.LOG(4, "Import Complete, checkpointing")
						self.__dbenv.txn_checkpoint()
				elif not self.__importmode : DB_syncall()
				if self.__importmode :
						self.LOG(4, "Checkpointing complete, dumping indices")
						self.__commitindices()
						
						
						
		def restoretest(self, ctxid=None, host=None):
				"""This method will check a database backup and produce some statistics without modifying the current database."""
				
				if not self.__importmode: print("WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
				
				#user,groups=self.checkcontext(ctxid,host)
				ctx = self.__getcontext(ctxid, host)
				user = ctx.user
				groups = ctx.groups
				#if user!="root" :
				if not self.checkadmin(ctx):
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


		#@write,private
		def __del__(self): 
				self.close()


		#@write,admin
		def close(self):
			"disabled at the moment"
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
