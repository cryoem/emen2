# $Id$

import copy
import atexit
import signal
import hashlib
import operator
import os
import sys
import time
import traceback
import collections
import itertools
import random
import re
import shutil
import weakref
import getpass
import functools
import imp
import tempfile
import cStringIO
import smtplib


import bsddb3


import emen2.db.config
g = emen2.db.config.g()
try:
	g.CONFIG_LOADED
except:
	emen2.db.config.defaults()


import emen2.db.proxy
import emen2.db.flags
import emen2.db.validators
import emen2.db.dataobject
import emen2.db.datatypes
import emen2.db.btrees
import emen2.db.datatypes
import emen2.db.exceptions
import emen2.db.plot

import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group
import emen2.db.workflow

import emen2.util.decorators
# import emen2.clients

from emen2.util import listops
import emen2.util.jsonutil

# convenience
Record = emen2.db.record.Record
Binary = emen2.db.binary.Binary
Context = emen2.db.context.Context
ParamDef = emen2.db.paramdef.ParamDef
RecordDef = emen2.db.recorddef.RecordDef
User = emen2.db.user.User
Group = emen2.db.group.Group
WorkFlow = emen2.db.workflow.WorkFlow
proxy = emen2.db.proxy
publicmethod = emen2.db.proxy.publicmethod


try:
	import markdown
except ImportError:
	markdown = None



def fakemodules():
	Database = imp.new_module("Database")
	Database.dataobjects = imp.new_module("dataobjects")
	sys.modules["emen2.Database"] = Database
	sys.modules["emen2.Database.dataobjects"] = Database.dataobjects
	sys.modules["emen2.Database.dataobjects.record"] = emen2.db.record
	sys.modules["emen2.Database.dataobjects.binary"] = emen2.db.binary
	sys.modules["emen2.Database.dataobjects.context"] = emen2.db.context
	sys.modules["emen2.Database.dataobjects.paramdef"] = emen2.db.paramdef
	sys.modules["emen2.Database.dataobjects.recorddef"] = emen2.db.recorddef
	sys.modules["emen2.Database.dataobjects.user"] = emen2.db.user
	sys.modules["emen2.Database.dataobjects.group"] = emen2.db.group
	sys.modules["emen2.Database.dataobjects.workflow"] = emen2.db.workflow

fakemodules()

from emen2.clients import __version__
VERSIONS = {
	"API": g.VERSION,
	"emen2client": emen2.clients.__version__
}


VIEW_REGEX = '\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?'


# Pointer to database environment
DBENV = None


#basestring goes away in a later python version
basestring = (str, unicode)


DB_CONFIG = """\
# Environment layout
set_lg_dir log
set_data_dir data
# These can be tuned somewhat, depending on circumstances
set_cachesize 0 134217728 1
set_tx_max 65536
set_lk_max_locks 100000
set_lk_max_lockers 100000
set_lk_max_objects 100000
# Don't touch these
set_lk_detect DB_LOCK_YOUNGEST
set_lg_regionmax 1048576
set_lg_max 8388608
set_lg_bsize 2097152
"""



def clock(times, key=0, t=0, limit=60):
	t2 = time.time()
	if not times.get(key):
		times[key] = 0
	times[key] += t2-t
	if sum(times.values()) >= limit:
		raise Exception, "Operation timed out (max %s seconds)"%(limit)
	return t2




def check_output(args, **kwds):
	kwds.setdefault("stdout", subprocess.PIPE)
	kwds.setdefault("stderr", subprocess.STDOUT)
	p = subprocess.Popen(args, **kwds)
	return p.communicate()[0]





def return_first_or_none(items):
	items = items or []
	result = None
	if len(items) > 0:
		if hasattr(items, 'keys'):
			result = items.get(return_first_or_none(items.keys()))
		else:
			result = iter(items).next()
	return result



@atexit.register
def DB_Close(*args, **kwargs):
	"""Close all open DBs"""
	l = DB.opendbs.keys()
	for i in l:
		# g.log.msg('LOG_DEBUG', i.dbenv)
		i.close()
		



def DB_stat():
	"""List some statistics about the global DBEnv"""
	global DBENV
	if not DBENV:
		return

	sys.stdout.flush()

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





# ian: todo: make these express GMT, then have display interfaces localize to time zone...
def getctime():
	return time.time()



def gettime():
	"""Return database local time in format %s"""%g.TIMESTR
	return time.strftime(g.TIMESTR)






class DB(object):
	"""Main database class"""
	opendbs = weakref.WeakKeyDictionary()

	# ian: todo: have DBEnv and all BDBs in here -- DB should just be methods for dealing with this dbenv "core"
	@emen2.util.decorators.instonget
	class bdbs(object):
		"""A private class -- the actual core of the DB. The DB files are accessible as attributes, and indexes are loaded in fieldindex."""

		def init(self, db, dbenv, txn):
			old = set(self.__dict__)

			# Security items
			self.newuserqueue = emen2.db.btrees.BTree(filename="security/newuserqueue", dbenv=dbenv, txn=txn)
			self.contexts = emen2.db.btrees.BTree(filename="security/contexts", dbenv=dbenv, txn=txn)
			self.users = emen2.db.btrees.BTree(filename="security/users", dbenv=dbenv, txn=txn)
			self.groups = emen2.db.btrees.BTree(filename="security/groups", dbenv=dbenv, txn=txn)

			# Main database items
			self.bdocounter = emen2.db.btrees.BTree(filename="main/bdocounter", dbenv=dbenv, txn=txn)
			self.workflow = emen2.db.btrees.BTree(filename="main/workflow", dbenv=dbenv, txn=txn)

			self.paramdefs = emen2.db.btrees.RelateBTree(filename="main/paramdefs", dbenv=dbenv, txn=txn)
			self.recorddefs = emen2.db.btrees.RelateBTree(filename="main/recorddefs", dbenv=dbenv, txn=txn)
			self.records = emen2.db.btrees.RelateBTree(filename="main/records", keytype="d", cfunc=False, sequence=True, dbenv=dbenv, txn=txn)

			# This is an index of indices
			self.indexkeys = emen2.db.btrees.FieldBTree(filename="index/indexkeys", dbenv=dbenv, txn=txn)

			# These index things outside of Records
			self.groupsbyuser = emen2.db.btrees.FieldBTree(filename="index/security/groupsbyuser", datatype="s", dbenv=dbenv, txn=txn)
			self.usersbyemail = emen2.db.btrees.FieldBTree(filename="index/security/usersbyemail", datatype="s", dbenv=dbenv, txn=txn)
			self.bdosbyfilename = emen2.db.btrees.FieldBTree(filename="index/bdosbyfilename", keytype="s", datatype="s", dbenv=dbenv, txn=txn)

			# Some attributes
			self.bdbs = set(self.__dict__) - old
			self.contexts_cache = {}
			self.fieldindex = {}
			self._db = db


		def openparamindex(self, paramname, keytype="s", datatype="d", dbenv=None, txn=None):
			"""Parameter values are indexed with 1 db file per param, stored in index/params/*.bdb.
			Key is param value, values are list of recids, stored using BDB duplicate keys method.
			The opened param will be available in self.fieldindex[paramname] after open.

			@param paramname Param index to open
			@keyparam keytype Open index with this keytype (from core_vartypes.<vartype>.keytype)
			@keyparam datatype Open with datatype; will always be 'd'
			@keyparam dbenv A DBEnv instance must be passed
			"""

			filename = "index/params/%s"%(paramname)

			deltxn=False
			if txn == None:
				txn = self._db.newtxn(write=True)
				deltxn = True
			try:
				self.fieldindex[paramname] = emen2.db.btrees.FieldBTree(keytype=keytype, datatype=datatype, filename=filename, dbenv=dbenv, txn=txn)
			except BaseException, e:
				if deltxn:
					self._db.txnabort(txn=txn)
				raise
			else:
				if deltxn: self._db.txncommit(txn=txn)



		def closeparamindex(self, paramname):
			"""Close a paramdef
			@param paramname Param index to close
			"""
			self.fieldindex.pop(paramname).close()


		def closeparamindexes(self):
			"""Close all paramdef indexes"""
			[self._closeparamindex(x) for x in self.fieldindex.keys()]




	#@staticmethod
	def _init_vtm(self):
		"""Load vartypes, properties, and macros"""

		vtm = emen2.db.datatypes.VartypeManager()

		self.indexablevartypes = set()
		for y in vtm.getvartypes():
			y = vtm.getvartype(y)
			if y.keytype:
				self.indexablevartypes.add(y.getvartype())

		return vtm



	def _init_dbenv(self):
		"""Setup DBEnv"""

		global DBENV
		
		ENVOPENFLAGS = \
			bsddb3.db.DB_CREATE | \
			bsddb3.db.DB_INIT_MPOOL | \
			bsddb3.db.DB_INIT_TXN | \
			bsddb3.db.DB_INIT_LOCK | \
			bsddb3.db.DB_INIT_LOG | \
			bsddb3.db.DB_THREAD  | \
			bsddb3.db.DB_REGISTER |	\
			bsddb3.db.DB_RECOVER


		if DBENV == None:
			g.log.msg("LOG_INFO","Opening Database Environment: %s"%self.path)
			DBENV = bsddb3.db.DBEnv()
			DBENV.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
			DBENV.open(self.path, ENVOPENFLAGS)
			DB.opendbs[self] = 1

		return DBENV




	def _checkdirs(self):
		"Check that all necessary directories referenced from config file exist"

		if not os.access(self.path, os.F_OK):
			os.makedirs(self.path)

		paths = ["data", "data/main", "data/security", "data/index", "data/index/security", "data/index/params", "data/index/records", "log", "overlay", "overlay/views", "overlay/templates"]
		paths = (os.path.join(self.path, path) for path in paths)
		paths = [os.makedirs(path) for path in paths if not os.path.exists(path)]

		paths = []
		for i in ['LOGPATH', 'HOTBACKUP', 'LOG_ARCHIVE', 'TILEPATH', 'TMPPATH', 'SSLPATH']:
			try: paths.append(getattr(g.paths, i))
			except: pass
		paths = [os.makedirs(path) for path in paths if not os.path.exists(path)]


		configpath = os.path.join(self.path,"DB_CONFIG")
		if not os.path.exists(configpath):
			g.log.msg("LOG_INIT","Installing default DB_CONFIG file: %s"%configpath)
			f = open(configpath, "w")
			f.write(DB_CONFIG)
			f.close()



	def __init__(self, path=None, maintenance=False):
		"""Initialize DB

		@keyparam path Path to DB (default is g.EMEN2DBHOME, which checks $EMEN2DBHOME and program arguments; see db.config)
		@keyparam maintenance Open in maintenance mode; only the environment will be created; no bdbs will be opened.
		"""

		self.path = path or g.EMEN2DBHOME
		if not self.path:
			raise ValueError, "No path specified; check $EMEN2DBHOME and config.json files"

		self.lastctxclean = time.time()
		self.opentime = gettime()
		self.txnid = 0
		self.txnlog = {}

		# Check that all the needed directories exist
		self._checkdirs()

		# VartypeManager handles registration of vartypes and properties, and also validation
		self.vtm = self._init_vtm()

		# Open DB environment; check if global DBEnv has been opened yet
		self.dbenv = self._init_dbenv()

		# If we are just doing backups or maintenance, don't open any BDB handles
		if maintenance:
			return


		# Open Database
		txn = self.newtxn(write=True)
		try:
			self.bdbs.init(self, self.dbenv, txn=txn)
		except Exception, inst:
			self.txnabort(txn=txn)
			raise
		else: self.txncommit(txn=txn)


		# Check if this is a valid db..
		txn = self.newtxn(write=True)
		try:
			maxr = self.bdbs.records.get_max(txn=txn)
			g.log.msg("LOG_INFO","Opened database with %s records"%maxr)
			if not self.bdbs.users.get('root', txn=txn):
				self.setup(txn=txn)

		except Exception, e:
			g.log.msg('LOG_INFO',"Could not open database! %s"%e)
			self.txnabort(txn=txn)
			raise

		else:
			self.txncommit(txn=txn)



	def __del__(self):
		g.log_info('Cleaning up DB instance')



	def setup(self, rootpw=None, rootemail=None, resetup=False, ctx=None, txn=None):
		"""Initialize a new DB"""
		
		if not rootpw or not rootemail:
			import pwd
			import platform

			host = platform.node() or 'localhost'
			try:
				defaultemail = "%s@%s"%(pwd.getpwuid(os.getuid()).pw_name, host)
			except:
				defaultemail = "root@localhost"

			print "\n=== New Database Setup ==="
			rootemail = rootemail or raw_input("Admin (root) email (default %s): "%defaultemail) or defaultemail
			rootpw = rootpw or getpass.getpass("Admin (root) password (default: none): ")

			while len(rootpw) < 6:
				if len(rootpw) == 0:
					print "Warning! No root password!"
					rootpw = ''
					break
				elif len(rootpw) < 6:
					print "Warning! If you set a password, it needs to be more than 6 characters."
					rootpw = getpass.getpass("Admin (root) password (default: none): ")



		# Private method to load config
		def load_skeleton(t):
			infile = emen2.db.config.get_filename('emen2', 'skeleton/%s.json'%t)
			f = open(infile)
			ret = emen2.util.jsonutil.decode(f.read())
			f.close()
			return ret


		# Create a fake root context
		ctx = self._makerootcontext(txn=txn)
		dbp = ctx.db
		dbp._settxn(txn)

		g.log.msg("LOG_INFO","Initializing new database; root email: %s"%rootemail)

		import emen2.db.load
		path = emen2.db.config.get_filename('emen2', 'skeleton')
		loader = emen2.db.load.Loader(path=path, db=dbp)
		loader.load(rootemail=rootemail, rootpw=rootpw)




	# ian: todo: simple: more statistics; needs a txn?
	def __str__(self):
		return "<DB: %s>"%(hex(id(self))) #, ~%s records>"%(hex(id(self)), self.bdbs.records.get_max())


	def __del__(self):
		"""Close DB when deleted"""

		self.close()


	def close(self):
		"""Close DB"""

		g.log.msg('LOG_DEBUG', "Closing %d BDB databases"%(len(emen2.db.btrees.BTree.alltrees)))
		try:
			for i in emen2.db.btrees.BTree.alltrees.keys():
				i.close()
		except Exception, inst:
			g.log.msg('LOG_ERROR', inst)

		self.dbenv.close()



	# @remove
	# ian: todo: there is a better version in emen2.util.listops
	def _flatten(self, l):
		"""Flatten an iterable of iterables recursively into a single list"""

		out = []
		for item in l:
			if hasattr(item, '__iter__'): out.extend(self._flatten(item))
			else:
				out.append(item)
		return out



	###############################
	# section: Email and utilities
	###############################

	def sendmail(self, recipient, template, ctxt=None, ctx=None, txn=None):
		"""(Internal) Send an email based on a template. If the template subsystem is not available, or email is not configured, this will fail without an exception."""

		# get MAILADMIN from the root record...
		try:
			mailadmin = self.bdbs.users.sget('root', txn=txn).email
			if not mailadmin:
				raise ValueError, "No email set for root"
			if not g.MAILHOST:
				raise ValueError, "No SMTP server"
		except Exception, inst:
			g.log('LOG_INFO','Could not send email: %s'%inst)
			return

		ctxt = ctxt or {}
		ctxt["recipient"] = recipient
		ctxt["MAILADMIN"] = mailadmin
		ctxt["EMEN2DBNAME"] = g.EMEN2DBNAME
		ctxt["EMEN2EXTURI"] = g.EMEN2EXTURI

		if not recipient:
			return

		try:
			msg = g.templates.render_template(template, ctxt)
		except Exception, e:
			g.log('LOG_INFO','Could not render template %s: %s'%(template, e))
			return

		try:
			s = smtplib.SMTP(g.MAILHOST)
			s.set_debuglevel(1)
			s.sendmail(mailadmin, [recipient], msg)
			g.log('LOG_INFO', 'Mail sent: %s -> %s'%(mailadmin, recipient))
		except Exception, e:
			g.log('LOG_ERROR', 'Could not send email: %s'%e)
			raise e

		return recipient



	###############################
	# section: Transaction Management
	###############################

	txncounter = 0

	def newtxn(self, parent=None, ctx=None, write=False):
		"""Start a new transaction.

		@keyparam parent Open new txn as a child of this parent txn
		@return New txn
		"""

		flags = bsddb3.db.DB_TXN_SNAPSHOT
		if write:
			flags = 0
			
		txn = self.dbenv.txn_begin(parent=parent, flags=flags)
		# g.log.msg('LOG_INFO', "NEW TXN, flags: %s --> %s"%(flags, txn))

		try:
			type(self).txncounter += 1
			self.txnlog[id(txn)] = txn
		except:
			self.txnabort(ctx=ctx, txn=txn)
			raise

		return txn



	def txncheck(self, txnid=0, write=False, ctx=None, txn=None):
		"""Check a txn status; accepts txnid or txn instance

		@return txn if valid
		"""
		txn = self.txnlog.get(txnid, txn)
		if not txn:
			txn = self.newtxn(ctx=ctx, write=write)
		return txn



	def txnabort(self, txnid=0, ctx=None, txn=None):
		"""Abort txn; accepts txnid or txn instance"""

		txn = self.txnlog.get(txnid, txn)
		# g.log.msg('LOG_INFO', "TXN ABORT --> %s"%txn)

		if txn:
			txn.abort()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise ValueError, 'Transaction not found'



	def txncommit(self, txnid=0, ctx=None, txn=None):
		"""Commit txn; accepts txnid or instance"""

		txn = self.txnlog.get(txnid, txn)
		# g.log.msg("LOG_INFO","TXN COMMIT --> %s"%txn)

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

	@publicmethod("versions.get")
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program

		@keyparam program Check version for this program (API, emen2client, etc.)
		@return Version string
		"""
		return VERSIONS.get(program)



	@publicmethod("time")
	def gettime(self, ctx=None, txn=None):
		"""Get current DB time. The time string format is in the config file; default is YYYY/MM/DD HH:MM:SS.

		@return Date string of current DB time
		"""
		return gettime()




	###############################
	# section: Login and Context Management
	###############################

	# This is intentionally not a publicmethod because DBProxy wraps it
	LOGINERRMSG = 'Invalid username or password: %s'

	@publicmethod("auth.login", write=True)
	def login(self, username="anonymous", password="", host=None, maxidle=None, ctx=None, txn=None):
		"""Logs a given user in to the database and returns a ctxid, which can then be used for
		subsequent access. Returns ctxid, or fails with AuthenticationError or SessionError

		@keyparam username Account username
		@keyparam password Account password
		@keyparam host Bind to this host (usually set by proxy access method)
		@return Context key (ctxid)
		@exception AuthenticationError, KeyError
		"""
		
		if maxidle == None or maxidle > g.MAXIDLE:
			maxidle = g.MAXIDLE

		newcontext = None
		username = unicode(username).strip()

		username = self._userbyemail(username, ctx=ctx, txn=txn) or username

		if username == "anonymous":
			newcontext = self._makecontext(host=host, ctx=ctx, txn=txn)
		else:
			try:
				user = self._login_getuser(username, ctx=ctx, txn=txn)
			except:
				g.log.msg('LOG_SECURITY', "Invalid username or password for %s"%username)
				raise emen2.db.exceptions.AuthenticationError, "Invalid username or password"

			if user.checkpassword(password):
				newcontext = self._makecontext(username=username, host=host, ctx=ctx, txn=txn)
			else:
				g.log.msg('LOG_SECURITY', "Invalid username or password for %s"%username)
				raise emen2.db.exceptions.AuthenticationError, "Invalid username or password"

		try:
			self._commit_context(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
			g.log.msg('LOG_SECURITY', "Login succeeded: %s -> %s" % (username, newcontext.ctxid))
		except Exception, e:
			g.log.msg('LOG_CRITICAL', "Critical! Error writing login context: %s"%e)
			raise

		return newcontext.ctxid


	# backwards compat
	# _login = login
	@publicmethod("auth.login2", write=True)
	def _login(self, *args, **kwargs):
		return self.login(*args, **kwargs)


	# Logout is the same as delete context
	@publicmethod("auth.logout", write=True)
	def logout(self, ctx=None, txn=None):
		"""Logout"""

		self._commit_context(ctx.ctxid, None, ctx=ctx, txn=txn)
		return True




	@publicmethod("auth.whoami")
	def checkcontext(self, ctx=None, txn=None):
		"""This allows a client to test the validity of a context, and get basic information on the authorized user and his/her permissions.

		@return (context username, context groups)
		"""

		return ctx.username, ctx.groups




	@publicmethod("auth.check.admin")
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.

		@return Bool; True if user is an admin
		"""
		return ctx.checkadmin()




	@publicmethod("auth.check.readadmin")
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.

		@return Bool; True if user is a read admin
		"""
		return ctx.checkreadadmin()




	@publicmethod("auth.check.create")
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.

		@return Bool; True if the user can create records
		"""
		return ctx.checkcreate()



	def _makecontext(self, username="anonymous", host=None, ctx=None, txn=None):
		"""(Internal) Initializes a context; Avoid instantiating Contexts directly.

		@keyparam username Username (default "anonymous")
		@keyparam host Host
		@return Context instance
		"""

		if username == "anonymous":
			ctx = emen2.db.context.AnonymousContext(host=host)
		else:
			ctx = emen2.db.context.Context(username=username, host=host)

		return ctx



	def _makerootcontext(self, ctx=None, host=None, txn=None):
		"""(Internal) Create a root context. Can use this internally when some admin tasks that require ctx's are necessary."""

		ctx = emen2.db.context.SpecialRootContext()
		ctx.refresh(db=self)
		ctx._setDBProxy(txn=txn)
		return ctx



	# ian: todo: simple: finish
	def _login_getuser(self, username, ctx=None, txn=None):
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
			raise emen2.db.exceptions.AuthenticationError, 'No such user' #emen2.db.exceptions.AuthenticationError.__doc__
		return user



	def _commit_context(self, ctxid, context, ctx=None, txn=None):
		"""(Internal) Manipulate cached and stored contexts. Use this to update or delete contexts.
		It will update BDB if necessary. This is called frequently to set idle time.

		@param ctxid ctxid key
		@param context Context instance
		@exception KeyError, DBError
		"""

		# any time you set the context, delete the cached context
		# this will retrieve it from disk next time it's needed
		if self.bdbs.contexts_cache.get(ctxid):
			del self.bdbs.contexts_cache[ctxid]


		# set context
		if context != None:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts.set: %s"%context.ctxid)
				self.bdbs.contexts.set(ctxid, context, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Critical! self.bdbs.contexts.set %s: %s"%(ctxid, inst))
				raise

		# delete context
		else:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts.__delitem__: %s"%ctxid)
				self.bdbs.contexts.set(ctxid, None, txn=txn) #del ... [ctxid]

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Critical! self.bdbs.context.set %s: %s"%(ctxid, inst))
				raise




	# ian: todo: hard: flesh this out into a proper cron system, with a subscription model; right now just runs cleanupcontext
	# right now this is called during _getcontext, and calls cleanupcontexts not more than once every 10 minutes
	def _periodic_operations(self, ctx=None, txn=None):
		"""(Internal) Maintenance task scheduler. Eventually this will be replaced with a maintenance registration system"""

		t = getctime()
		if t > (self.lastctxclean + 600):
			self.lastctxclean = time.time()
			self._cleanupcontexts(ctx=ctx, txn=txn)



	# ian: todo: hard: finish
	def _cleanupcontexts(self, ctx=None, txn=None):
		"""(Internal) Clean up sessions that have been idle too long."""

		old_strftime = time.strftime(g.TIMESTR, time.gmtime(self.lastctxclean))
		newtime = time.time()
		new_strftime = time.strftime(g.TIMESTR, time.gmtime(newtime))

		g.log.msg("LOG_DEBUG","Cleaning up expired contexts: %s -> %s"%(old_strftime, new_strftime))

		for ctxid, context in self.bdbs.contexts.items(txn=txn):
			# use the cached time if available
			try:
				c = self.bdbs.contexts_cached.sget(ctxid, txn=txn) #[ctxid]
				context.time = c.time
			# ed: fix: should check for more specific exception
			except:
				pass


			if context.time + (context.maxidle or 0) < newtime:
				# g.log_info("Expire context (%s) %d" % (context.ctxid, time.time() - context.time))
				self._commit_context(context.ctxid, None, ctx=ctx, txn=txn)



	# how often should we refresh groups? right now, every publicmethod will reset user/groups. timer based?
	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Internal and DBProxy) Takes a ctxid key and returns a context. Note that both key and host must match.

		@param ctxid ctxid
		@param host host
		@return Context
		@exception SessionError
		"""

		if txn == None:
			raise ValueError, "No txn"

		self._periodic_operations(ctx=ctx, txn=txn)

		context = None
		if ctxid:
			context = self.bdbs.contexts_cache.get(ctxid) or self.bdbs.contexts.get(ctxid, txn=txn)
		else:
			context = self._makecontext(host=host, ctx=ctx, txn=txn)

		if not context:
			g.log.msg('LOG_ERROR', "Session expired for %s"%ctxid)
			raise emen2.db.exceptions.SessionError, "Session expired"

		user = None
		grouplevels = {}

		# Update and cache
		if context.username not in ["anonymous"]:
			user = self.bdbs.users.get(context.username, None, txn=txn)
			groups = self.bdbs.groupsbyuser.get(context.username, set(), txn=txn)
			grouplevels = {}
			for group in [self.bdbs.groups.get(i, txn=txn) for i in groups]:
				grouplevels[group.name] = group.getlevel(context.username)

		# g.debug("kw host is %s, context host is %s"%(host, context.host))
		context.refresh(user=user, grouplevels=grouplevels, host=host, db=self)

		self.bdbs.contexts_cache[ctxid] = context

		return context





	###############################
	# section: binaries
	###############################


	@publicmethod("binaries.get")
	def getbinary(self, bdokeys=None, q=None, filt=True, ctx=None, txn=None):
		"""Get Binary objects from ids or references. Binaries include file name, size, md5, associated record, etc. Each binary has an ID, aka a 'BDO'

		@param bdokeys A single binary ID, or an iterable containing: records, recids, binary IDs
		@keyparam q Return binaries found in the result of this Query
		@keyparam filt Ignore failures
		@return A single Binary instance or a list of Binaries
		@exception KeyError, SecurityError
		"""

		# process bdokeys argument for bids (into list bids) and then process bids
		ol, bdokeys = listops.oltolist(bdokeys)
		ret = []
		bids = []
		recs = []

		# Use a query for BDO search
		if q:
			# grumble -- json keys are unicode, need to convert to str
			qr = self.query(c=q.get('c'), boolmode=q.get('boolmode'), ignorecase=q.get('ignorecase'), ctx=ctx, txn=txn)
			recs.extend(self.getrecord(qr.get('recids', []), ctx=ctx, txn=txn))
			ol = False

		# ian: todo: fix this in a sane way..
		if hasattr(bdokeys, "__iter__"):
			bids.extend(x for x in bdokeys if isinstance(x, basestring))

		# If we're doing any record lookups...
		recs.extend(self.getrecord((x for x in bdokeys if isinstance(x, int)), filt=True, ctx=ctx, txn=txn))
		recs.extend(x for x in bdokeys if isinstance(x, emen2.db.record.Record))

		if recs:
			# ian: todo: this needs more speed. Maybe I should index params by vartype?
			# get the params we're looking for
			params = self.getparamdefnames(ctx=ctx, txn=txn)
			params = self.getparamdef(params, ctx=ctx, txn=txn)
			params_binary = filter(lambda x:x.vartype=="binary", params) or []
			params_binaryimage = filter(lambda x:x.vartype=="binaryimage", params) or []

			# get the values in the records. vartype BINARY is a LIST, BINARYIMAGE is a STRING
			for i in [j.name for j in params_binary]:
				for rec in recs:
					bids.extend(rec.get(i,[]))
			for i in [j.name for j in params_binaryimage]:
				for rec in recs:
					if rec.get(i):
						bids.append(rec.get(i))


		# Ok, we now have a list of all the BDO items we need to lookup

		# keyed by recid and keyed by date
		byrec = collections.defaultdict(list)
		bydatekey = collections.defaultdict(list)

		# ian: todo: filter bids by "bdo:"...
		bids = filter(lambda x:x[:4]=="bdo:", bids)

		# This resolves path references and parses out dates, id #, etc.
		for bdokey in bids:
			try:
				parsed = emen2.db.binary.Binary.parse(bdokey)
			except ValueError:
				if filt:
					continue
				else:
					raise KeyError, "Bad BDO format: %s"%(bdokey)
				
			bydatekey[parsed["datekey"]].append(parsed)


		for datekey,bydate in bydatekey.items():
			try:
				bdocounter = self.bdbs.bdocounter.sget(datekey, txn=txn)
				for i in bydate:
					bdo = bdocounter.get(i["counter"])
					bdo["filepath"] = i["filepath"]
					byrec[bdo["recid"]].append(bdo)

			except Exception, inst:
				if filt:
					continue
				else:
					raise KeyError, "Unknown BDO identifier: %s"%(datekey)


		recstoget = set(byrec.keys()) - set([rec.recid for rec in recs])
		recs.extend(self.getrecord(recstoget, ctx=ctx, txn=txn))

		for rec in recs:
			for i in byrec.get(rec.recid,[]):
				ret.append(i)

		# We allow BDO owners to access even if not associated with a recid
		username = ctx.username
		admin = ctx.checkadmin()
		for i in byrec.get(None, []):
			if i.creator == username or admin:
				ret.append(i)


		if ol: return return_first_or_none(ret)
		return ret




	@publicmethod("binaries.put", write=True)
	def putbinary(self, bdokey=None, recid=None, filename=None, infile=None, uri=None, ctx=None, txn=None):
		"""Add binary object to database and attach to record. May specify record param to use and file data to write to storage area. Admins may modify existing binaries.

		@keyparam bdokey Update an existing BDO. Only the filename and record ID can be updated.
		@keypram recid Link Binary to this Record
		@keyparam filename Filename
		@keyparam infile A file-like object (hasattr read) or a string
		@keyparam uri Binary source
		@return Binary instance
		"""

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "Record creation permissions required to add BDOs"


		# Sanitize filename.. This will allow unicode characters, and check for reserved filenames on linux/windows
		if filename != None:
			filename = "".join([i for i in filename if i.isalpha() or i.isdigit() or i in '.()-=_'])
			if filename.upper() in ['..', '.', 'CON', 'PRN', 'AUX', 'NUL',
											'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
											'COM6', 'COM7', 'COM8', 'COM9', 'LPT1',
											'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
											'LPT7', 'LPT8', 'LPT9']:
				filename = "renamed."+filename
			filename = unicode(filename)


		# bdo items are stored one bdo per day
		# key is sequential item #, value is (filename, recid)
		dkey = emen2.db.binary.Binary.parse(bdokey)
		t = self.gettime()


		# First write out the file
		newfile = None
		filesize = 0
		md5sum = ''
		if infile:
			newfile, filesize, md5sum = self._putbinary_file(filename, infile=infile, dkey=dkey, ctx=ctx, txn=txn)


		# Update the BDO: Start RMW cycle
		bdo = self.bdbs.bdocounter.get(dkey["datekey"], txn=txn, flags=bsddb3.db.DB_RMW) or {}

		if dkey["counter"] == 0:
			counter = max(bdo.keys() or [-1]) + 1
			dkey = emen2.db.binary.Binary.parse(bdokey, counter=counter)


		nb = bdo.get(dkey["counter"])
		if newfile:
			if nb:
				raise emen2.db.exceptions.SecurityError, "BDOs are immutable"

			if not filesize:
				raise ValueError, "Cannot create a BDO without a file"

			nb = emen2.db.binary.Binary()
			nb.update(
				uri = uri,
				creator = ctx.username,
				creationtime = t,
				name = dkey["name"],
				filesize = filesize,
				md5 = md5sum
			)

		if not nb:
			raise KeyError, "No such BDO: %s"%bdokey

		if nb['creator'] != ctx.username and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "You cannot modify a BDO you did not create"

		if recid != None:
			nb["recid"] = recid

		if filename != None:
			nb["filename"] = filename

		nb["modifyuser"] = ctx.username
		nb["modifytime"] = t

		bdo[dkey["counter"]] = nb

		g.log.msg("LOG_COMMIT","self.bdbs.bdocounter.set: %s"%dkey["datekey"])
		self.bdbs.bdocounter.set(dkey["datekey"], bdo, txn=txn)

		g.log.msg("LOG_COMMIT","self.bdbs.bdosbyfilename.addrefs: %s -> %s"%(filename, dkey["name"]))
		self.bdbs.bdosbyfilename.addrefs(filename, [dkey["name"]], txn=txn)

		# Now move the file to the right location
		if newfile:
			os.rename(newfile, dkey["filepath"])

		return self.getbinary(nb.get('name'), ctx=ctx, txn=txn)



	def _putbinary_file(self, filename=None, infile=None, dkey=None, ctx=None, txn=None):
		"""(Internal) Behind the scenes -- read infile out to a temporary file. The temporary file will be renamed to the final destination when everything else is cleared.

		@keyparam filename
		@keyparam infile
		@keyparam dkey Binary Key -- see staticmethod Binary.parse

		@return Temporary file path, the file size, and an md5 digest.
		"""

		closefd = True
		if hasattr(infile, "read"):
			# infile is a file-like object; do not close
			closefd = False
		else:
			# string data..
			infile = cStringIO.StringIO(infile)

		try:
			os.makedirs(dkey["basepath"])
		except:
			pass


		filename = os.path.basename(filename or "UnkownFilename")

		# Write out file to temporary storage
		(fd, tmpfilepath) = tempfile.mkstemp(suffix=".upload", dir=dkey["basepath"])
		m = hashlib.md5()
		filesize = 0

		with os.fdopen(fd, "w+b") as f:
			for line in infile:
				f.write(line)
				m.update(line)
				filesize += len(line)

		if filesize == 0 and not ctx.checkadmin():
			raise ValueError, "Empty file!"

		if closefd:
			infile.close()

		md5sum = m.hexdigest()
		g.log.msg('LOG_INFO', "Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfilepath, filesize, md5sum))

		return tmpfilepath, filesize, md5sum





	###############################
	# section: query
	###############################


	@publicmethod("records.find.query")
	def query(self, 
			c=None, 
			boolmode="AND", 
			ignorecase=True, 
			subset=None, 
			pos=0, 
			count=0, 
			sortkey="creationtime", 
			reverse=False,
			recs=False,
			table=False,
			stats=False,
			ctx=None,
			txn=None,
			**kwargs):
		"""Query"""


		############################
		# Setup
		times = {}
		t0 = time.time()
		t = time.time()
		returnrecs = bool(recs)
		boolops = {"AND":"intersection_update", "OR":"update"}
		recids = None

		# Process the query constraints..
		c = c or []
		_c = []
		default = [None, 'any', None]
		for i in c:
			# A simple constraint is [param, "any", None]
			if not hasattr(i, "__iter__"):
				i = [i]
			i = i[:len(i)]+default[len(i):3]
			_c.append(i)
		_cm, _cc = emen2.util.listops.filter_partition(lambda x:x[0].startswith('$@') or x[1]=='none' or x[1]=='noop', _c)		
		
		recs = collections.defaultdict(dict)
				
		############################				
		# Step 1: Run constraints
		t = clock(times, 0, t0)

		for searchparam, comp, value in _cc:
			# Matching recids for each step
			constraintmatches = self._query(searchparam, comp, value, recs=recs, ctx=ctx, txn=txn)
			if recids == None: # For the first constraint..
				recids = constraintmatches
			elif constraintmatches != None: # Apply AND/OR
				getattr(recids, boolops[boolmode])(constraintmatches)

		
		############################				
		# Step 2: Filter permissions. If no constraint, use all records..
		t = clock(times, 1, t)

		if recids == None:
			recids = self.getindexbycontext(ctx=ctx, txn=txn)
		if subset:
			recids &= subset
		if c:
			recids = self._filterbypermissions(recids or set(), ctx=ctx, txn=txn)
			
			
		############################				
		# Step 3: Run constraints that include macros or "value is empty"
		t = clock(times, 2, t)

		for searchparam, comp, value in _cm:
			constraintmatches = self._query(searchparam, comp, value, recids=recids, recs=recs, ctx=ctx, txn=txn)
			if constraintmatches != None:
				getattr(recids, boolops[boolmode])(constraintmatches)



		############################				
		# Step 4: Generate stats on rectypes (do this before other sorting..)
		t = clock(times, 3, t)

		rectypes = collections.defaultdict(int)
		rds = set([rec.get('rectype') for rec in recs.values()]) - set([None])
		if len(rds) == 0:
			if stats: # don't do this unless we want these.
				r = self._groupbyrecorddef_index(recids, ctx=ctx, txn=txn)
				for k,v in r.items():
					rectypes[k] = len(v)
		elif len(rds) == 1:
			rectypes[rds.pop()] = len(recids)
		elif len(rds) > 1:
			for recid, rec in recs.iteritems():
				rectypes[rec.get('rectype')] += 1


		############################					
		# Step 5: Sort and slice to the right range
		# This processes the values for sorting: running any macros, rendering any usernames, checking indexes, etc.
		t = clock(times, 4, t)

		keytype, sortvalues = self._query_sort(sortkey, recids, recs=recs, c=c, ctx=ctx, txn=txn)

		key = sortvalues.get
		if sortkey == 'creationtime' or sortkey == 'recid':
			key = None
		elif keytype == 's':
			key = lambda recid:(sortvalues.get(recid) or '').lower()
		
		# We want to put empty values at the end..
		nonerecids = set(filter(lambda x:not (sortvalues.get(x) or sortvalues.get(x)==0), recids))
		recids -= nonerecids

		# not using reverse=reverse so we can add nonerecids at the end
		recids = sorted(recids, key=key) 
		recids.extend(sorted(nonerecids))
		if reverse:
			recids.reverse()
		
		# Truncate results.
		length = len(recids)
		if count > 0:
			recids = recids[pos:pos+count]



		############################					
		# Step 6: Rendered....
		# This is purely a convenience to save a callback
		t = clock(times, 5, t)

		def add_to_viewdef(viewdef, param):
			if not param.startswith('$'):
				param = '$$%s'%i
			if param in ['$$children','$$rectype', '$$parents']:
				pass
			elif param not in viewdef:
				viewdef.append(i)

		if table:			
			defaultviewdef = "$@recname() $@thumbnail() $$rectype $$recid"
			addparamdefs = ["creator","creationtime"]
			
			# Get the viewdef
			if len(rectypes) == 1:
				rd = self.getrecorddef(rectypes.keys()[0], ctx=ctx, txn=txn)
				viewdef = rd.views.get('tabularview', defaultviewdef)
			else:
				viewdef = self.getrecorddef(["root", "root_protocol"], ctx=ctx, txn=txn).pop().views.get('tabularview', defaultviewdef)

			viewdef = [i.strip() for i in viewdef.split()]

			for i in addparamdefs:
				if not i.startswith('$'):
					i = '$$%s'%i
				if i in viewdef:
					viewdef.remove(i)

			for i in [i[0] for i in c] + addparamdefs:
				if not i.startswith('$'):
					i = '$$%s'%i
				add_to_viewdef(viewdef, i)

			viewdef = " ".join(viewdef)
			table = self.renderview(recids, viewdef=viewdef, table=True, ctx=ctx, txn=txn)

		
		t = clock(times, 6, t)

		stats = {}
		stats['time'] = time.time()-t0
		stats['rectypes'] = rectypes

		# stats['times'] = times
		# for k,v in times.items():
		# 	print k, '%5.3f'%(v)
				
		
		############################							
		# Step 7: Fix for output
		for recid in recids:
			recs[recid]['recid'] = recid
		recs = [recs[i] for i in recids]

		ret = {
			"c": c,
			"boolmode": boolmode,
			"ignorecase": ignorecase,
			"recids": recids,
			"subset": subset,
			"pos": pos,
			"count": count,
			"length": length,
			"sortkey": sortkey,
			"reverse": reverse
		}
		if stats:
			ret['stats'] = stats
		if returnrecs:
			ret['recs'] = recs
		if table:
			ret['table'] = table
		

		return ret




	def _query_sort(self, sortkey, recids, recs=None, rendered=False, c=None, ctx=None, txn=None):

		# No work necessary if sortkey is creationtime
		if sortkey == 'creationtime' or sortkey == 'recid':
			return 's', {}

		# Setup
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)

		inverted = collections.defaultdict(set)
		c = c or []
		sortvalues = {}
		vartype = None
		keytype = None
		iterable = False
		ind = False
		
		# Check the paramdef
		try:
			pd = self.bdbs.paramdefs.get(sortkey, txn=txn)
			vartype = pd.vartype
			vt = vtm.getvartype(vartype)
			keytype = vt.keytype
			iterable = vt.iterable
			ind = self._getindex(pd.name)
		except:
			pass


		# These will always sort using the rendered value
		if vartype in ["user", "userlist", "binary", "binaryimage"]:
			rendered = True				


		# Ian: todo: if the vartype is iterable, then we can't trust the index to get the search order right!
		if sortkey in [i[0] for i in c] and not iterable:
			# Do we already have these values?
			for recid in recids:
				sortvalues[recid] = recs[recid].get(sortkey)

		elif sortkey.startswith('$@'):
			# Sort using a macro, and get the right sort function
			keytype, sortvalues = self._run_macro(sortkey, recids, ctx=ctx, txn=txn)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v
				# Unghhgh... ian: todo: make a macro_render_sort
				if hasattr(v, '__iter__'):
					v = ", ".join(map(unicode, v))
					sortvalues[k] = v
				

		elif not ind or len(recids) < 1000 or iterable:
			# We don't have the value, no index.. 
			# Can be very slow! Chunk to limit damage.
			for chunk in emen2.util.listops.chunk(recids):
				for rec in self.getrecord(chunk, ctx=ctx, txn=txn):
					sortvalues[rec.recid] = rec.get(sortkey)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v

		elif ind:
			# We don't have the value, but there is an index..
			# modifytime is kindof a pathological index.. need to find a better way
			for k,v in ind.iterfind(recids, txn=txn):
				inverted[k] = v
			sortvalues = emen2.util.listops.invert(inverted)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v

		else:
			# raise ValueError, "Don't know how to sort by %s"%sortkey
			pass
		

		# Use a "rendered" representation of the value, e.g. usernames to sort by user's current last name
		if rendered:
			# Invert again.. then render. This will save time on users.
			if not inverted:
				for k,v in sortvalues.items():
					try:
						inverted[v].add(k)
					except TypeError: 
						# Handle iterable vartypes, e.g. userlist
						inverted[tuple(v)].add(k)

			sortvalues = {}
			for k,v in inverted.items():
				r = vtm.param_render_sort(pd, k)
				for v2 in v:
					sortvalues[v2] = r
			

		return keytype, sortvalues
		
						
				

	def _query(self, searchparam, comp, value, recids=None, recs=None, ctx=None, txn=None):
		"""(Internal) index-based search. See DB.query()"""

		if recs == None:
			recs = {}

		cfunc = self._query_cmps()[comp]
			
		if value == None and comp not in ["any", "none", "contains_w_empty"]:
			return None
			
						
		# Sadly, will need to run macro on everything.. :( Run these as the last constraints.
		if searchparam.startswith('$@'):
			keytype, ret = self._run_macro(searchparam, recids or set(), ctx=ctx, txn=txn)
			# *minimal* validation of input..
			if keytype == 'd':
				value = int(value)
			elif keytype == 'f':
				value = float(value)
			else:
				value = unicode(value)
			# Filter by comp/value
			r = set()
			for k, v in ret.items():
				if cfunc(value, v): # cfunc(value, v):
					recs[k][searchparam] = v # Update the record cache
					r.add(k)
			return r
			
			
		# Additional setup..
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		matchkeys = collections.defaultdict(set)
		indparams = set()
		searchrecids = set()		
		
		if searchparam == 'rectype' and value:
			# Get child protocols, skip the index-index search
			matchkeys['rectype'] = set()
			if unicode(value).endswith('*'):
				value = unicode(value).replace('*', '')
				matchkeys['rectype'] |= self.getchildren(value, recurse=-1, keytype="recorddef", ctx=ctx, txn=txn)
			matchkeys['rectype'].add(value)
			
		elif searchparam == 'children':
			# Get children, skip the other steps
			recurse = 0
			if unicode(value).endswith('*'):
				value = int(unicode(value).replace('*', ''))
				recurse = -1
			recs[value]['children'] = self.getchildren(value, recurse=recurse, ctx=ctx, txn=txn)
			searchrecids = recs[value]['children']

		elif searchparam == 'recid':
			# This is useful in a few places
			searchrecids.add(int(value))

		else:
			# Get the list of indexes to search
			if searchparam.endswith('*'):
				indparams |= self.getchildren(self._query_paramstrip(searchparam), recurse=-1, keytype="paramdef", ctx=ctx, txn=txn)
			indparams.add(self._query_paramstrip(searchparam))
				

		# First, search the index index
		for indparam in indparams:
			pd = self.bdbs.paramdefs.get(indparam, txn=txn)
			ik = self.bdbs.indexkeys.get(indparam, txn=txn)

			if not pd:
				continue

			# Don't need to validate these
			if comp in ['any', 'none', 'noop']:
				matchkeys[indparam] = ik
				continue
				
			# Validate for comparisons (vartype, units..)	
			try:
				cargs = vtm.validate(pd, value)
			except Exception, inst:
				continue

			# Special case for nested iterables (e.g. permissions) --
			# 		they validate as list of lists
			if pd.name == 'permissions':
				cargs = emen2.util.listops.combine(*cargs)

			r = set()
			for v in emen2.util.listops.check_iterable(cargs):
				r |= set(filter(functools.partial(cfunc, v), ik))

			if r:
				matchkeys[indparam] = r


		# Now search individual param indexes
		for pp, keys in matchkeys.items():
			ind = self._getindex(pp, ctx=ctx, txn=txn)
			for key in keys:
				v = ind.get(key, txn=txn)
				searchrecids |= v 
				for v2 in v:
					recs[v2][pp] = key

		# If the comparison is "value is empty", then we return only values we didn't find anything for
		# 'No constraint' doesn't affect search results -- just store the values.
		if comp == 'noop':
			return None
		elif comp == 'none':
			return (recids or set()) - searchrecids
			
		return searchrecids



	def _query_cmps(self, ignorecase=1):
		"""(Internal) Return the list of query constraint operators.

		@keyparam ignorecase Use case-insensitive query operators
		@return dict of query operators
		"""

		# y is argument, x is record value
		cmps = {
			"==": lambda y,x:x == y,
			"!=": lambda y,x:x != y,
			">": lambda y,x: x > y,
			"<": lambda y,x: x < y,
			">=": lambda y,x: x >= y,
			"<=": lambda y,x: x <= y,
			'any': lambda y,x: x != None,
			'none': lambda y,x: x != None,
			"contains": lambda y,x:unicode(y) in unicode(x),
			'contains_w_empty': lambda y,x:unicode(y or '') in unicode(x),
			'noop': lambda y,x: True,
			'recid': lambda y,x: x,
			#'rectype': lambda y,x: x,
			# "!contains": lambda y,x:unicode(y) not in unicode(x),
			# "range": lambda x,y,z: y < x < z
		}

		if ignorecase:
			cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			cmps['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

		return cmps



	def _query_paramstrip(self, param):
		"""(Internal) Return basename of param"""
		return param.replace('*','').replace('$$','')




	def _findqueryinstr(self, query, s, window=20):
		"""(Internal) Give a window of context around a substring match"""
		
		if query == '':
			return True
		
		query = query.lower()
		s = (s or '').lower()
		if query in s:
			pos = s.index(query)
			if pos < window: pos = window
			return s[pos-window:pos+len(query)+window]

		return False
		


	def _run_macro(self, macro, recids, ctx=None, txn=None):
		recs = {}
		mrecs = self.getrecord(recids, ctx=ctx, txn=txn)

		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		
		regex = re.compile(VIEW_REGEX)
		k = regex.match(macro)
		
		keytype = vtm.getmacro(k.group('name')).getkeytype()
		vtm.macro_preprocess(k.group('name'), k.group('args'), mrecs)

		for rec in mrecs:
			recs[rec.recid] = vtm.macro_process(k.group('name'), k.group('args'), rec)

		return keytype, recs
			


	@publicmethod("recorddefs.find")
	def findrecorddef(self, query=None, name=None, desc_short=None, desc_long=None, mainview=None, childof=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		"""Find a RecordDef, by general search string, or by name/desc_short/desc_long/mainview/childof

		@keyparam query Contained in any item below
		@keyparam name ... contains in name
		@keyparam desc_short ... contains in short description
		@keyparam desc_long ... contains in long description
		@keyparam mainview ... contains in mainview
		@keyparam childof ... is child of
		@keyparam limit Limit number of results
		@return list of matching RecordDefs
		"""
		return self._find_pd_or_rd(query=query, keytype='recorddef', context=context, limit=limit, ctx=ctx, txn=txn, name=name, desc_short=desc_short, desc_long=desc_long, mainview=mainview, boolmode=boolmode, childof=childof)





	@publicmethod("paramdefs.find")
	def findparamdef(self, query=None, name=None, desc_short=None, desc_long=None, vartype=None, childof=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		"""@see findrecorddef"""
		return self._find_pd_or_rd(query=query, keytype='paramdef', context=context, limit=limit, ctx=ctx, txn=txn, name=name, desc_short=desc_short, desc_long=desc_long, vartype=vartype, boolmode=boolmode, childof=childof)




	def _filter_dict_zero(self, d):
		return dict(filter(lambda x:len(x[1])>0, d.items()))



	def _filter_dict_none(self, d):
		return dict(filter(lambda x:x[1]!=None, d.items()))



	def _find_pd_or_rd(self, childof=None, boolmode="OR", keytype="paramdef", context=False, limit=None, vartype=None, ctx=None, txn=None, **qp):
		"""(Internal) Find ParamDefs or RecordDefs based on **qp constraints."""

		# context of where query was found
		c = {}

		if keytype == "paramdef":
			getnames = self.getparamdefnames
			getitems = self.getparamdef

		else:
			getnames = self.getrecorddefnames
			getitems = self.getrecorddef

		if qp.get("query"):
			for k in qp.keys():
				qp[k]=qp["query"]
			del qp["query"]


		rdnames = getnames(ctx=ctx, txn=txn)

		# ian: will there be a faster way to do this?
		rds2 = getitems(rdnames, filt=True, ctx=ctx, txn=txn) or []
		p2 = []

		qp = self._filter_dict_none(qp)
		
		for i in rds2:
			qt = []
			for k,v in qp.items():
				qt.append(self._findqueryinstr(v, i.get(k)))

			if boolmode == "OR":
				if any(qt):
					p2.append(i)
					c[i.name] = filter(None, qt).pop()
			else:
				if all(qt):
					p2.append(i)
					c[i.name] = filter(None, qt).pop()

		if childof:
			children = self.getchildren(childof, recurse=-1, keytype=keytype, ctx=ctx, txn=txn)
			names = set(c.keys()) & children
			p2 = filter(lambda x:x.name in names, p2)
			c = dict(filter(lambda x:x[0] in names, c.items()))
			

		if vartype:
			vartype = emen2.util.listops.check_iterable(vartype)
			p2 = filter(lambda x:x.vartype in vartype, p2)	


		if context:
			return p2, c

		return p2





	@publicmethod("binaries.find")
	def findbinary(self, query=None, broad=False, limit=None, ctx=None, txn=None):
		"""Find a binary by filename

		@keyparam query Match this filename
		@keyparam broad Try variations of filename (extension, partial matches, etc..)
		@keyparam limit Limit number of results
		@return list of matching binaries
		"""
		if limit: limit=int(limit)

		qbins = self.bdbs.bdosbyfilename.get(query, txn=txn) or []

		qfunc = lambda x:query in x
		if broad:
			qfunc = lambda x:query in x or x in query

		if not qbins:
			matches = filter(qfunc, self.bdbs.bdosbyfilename.keys(txn))
			if matches:
				for i in matches:
					qbins.extend(self.bdbs.bdosbyfilename.get(i))

		bins = self.getbinary(qbins, ctx=ctx, txn=txn)
		bins = [j[1] for j in sorted([(len(i["filename"]), i) for i in bins])]

		if limit: bins = bins[:int(limit)]
		return bins




	@publicmethod("users.find")
	def finduser(self, query=None, email=None, name_first=None, name_middle=None, name_last=None, username=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		"""Find a user, by general search string, or by name_first/name_middle/name_last/email/username

		@keyparam query Contained in any item below
		@keyparam email ... contains in email
		@keyparam name_first ... contains in first name
		@keyparam name_middle ... contains in middle name
		@keyparam name_last ... contains in last name
		@keyparam username ... contains in username
		@keyparam boolmode 'AND' / 'OR'
		@keyparam limit Limit number of results
		@return list of matching user instances
		"""


		if query:
			email = query
			name_first = query
			name_middle = query
			name_last = query
			username = query

		if not query and not username:
			username = ""

		c = [
			["name_first", "contains", name_first],
			["name_last", "contains", name_last],
			["name_middle", "contains", name_middle],
			["email", "contains", email],
			["username", "contains_w_empty", username]
			]

		c = filter(lambda x:x[2] != None, c)

		q = self.query(
			boolmode=boolmode,
			ignorecase=1,
			c=c,
			ctx=ctx,
			txn=txn
		)

		recs = self.getrecord(q["recids"], ctx=ctx, txn=txn)
		usernames = listops.dictbykey(recs, 'username').keys()
		users = self.getuser(usernames, ctx=ctx, txn=txn)

		if limit: users = users[:int(limit)]
		return users




	@publicmethod("groups.find")
	def findgroup(self, query, limit=None, ctx=None, txn=None):
		"""Find a group.

		@param query
		@keyparam limit Limit number of items
		@return list of matching groups
		"""
		built_in = set(["anon","authenticated","create","readadmin","admin"])

		groups = self.getgroup(self.getgroupnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		search_keys = ["name", "displayname"]
		ret = []

		for v in groups:
			if any([query in v.get(search_key, "") for search_key in search_keys]):
				ret.append([v, v.get('displayname', v.name)])

		ret = sorted(ret, key=operator.itemgetter(1))
		ret = [i[0] for i in ret]

		if limit: ret = ret[:int(limit)]
		return ret



	# query should replace this...
	@publicmethod("records.find.byvalue")
	def findvalue(self, param, query='', count=True, showchoices=True, limit=100, ctx=None, txn=None):
		"""Find values for a parameter. This is mostly used for interactive UI elements: e.g. combobox.
		More detailed results can be performed using db.query.

		@param param Parameter to search
		@param query Value to match
		@keyparam limit Limit number of results
		@keyparam showchoices Include any defined param 'choices'
		@keyparam count Return count of matches, otherwise return recids
		@return if count: [[matching value, count], ...]
				if not count: [[matching value, [recid, ...]], ...]
		"""

		pd = self.getparamdef(param, ctx=ctx, txn=txn)
		q = self.query(c=[[param, "contains_w_empty", query]], ignorecase=1, recs=True, ctx=ctx, txn=txn)
		inverted = collections.defaultdict(set)
		for rec in q['recs']:
			inverted[rec.get(param)].add(rec.get('recid'))		

		keys = sorted(inverted.items(), key=lambda x:len(x[1]), reverse=True)
		if limit:
			keys = keys[:int(limit)]
		
		ret = dict([(i[0], i[1]) for i in keys])
		if count:
			for k,v in ret.items():
				ret[k] = len(v)
		
		ri = []
		choices = pd.choices or []
		if showchoices:
			for i in choices:
				ri.append((i, ret.get(i, 0)))
		
		for i,j in sorted(ret.items(), key=operator.itemgetter(1), reverse=True):
			if i not in choices:
				ri.append((i, ret.get(i, [])))
		
		return ri





	#########################
	# section: Query / Index Management
	#########################

	@publicmethod("records.find.byrecorddef")
	def getindexbyrecorddef(self, recdefs, ctx=None, txn=None):
		"""Records by Record Def. This is currently non-secured information.

		@param recdef Single or iterable RecordDef names
		@return Set of recids
		"""

		ol, recdefs = listops.oltolist(recdefs)

		# expand *'s
		recdefs = self.getrecorddef(recdefs, ctx=ctx, txn=txn)

		ret = set()
		ind = self._getindex("rectype")
		for i in recdefs:
			ret |= ind.get(i.name, txn=txn)

		# return self._filterbypermissions(ret, ctx=ctx, txn=txn)

		return ret



	# ian: todo: This is going to need work to handle the improvements to indexes
	# query really replaces this -- but it's useful.
	@publicmethod("records.find.dictbyvalue")
	def getindexdictbyvalue(self, param, subset=None, ctx=None, txn=None):
		"""Query a param index, returned in a dict keyed by value.

		@param param parameter name
		@keyparam valrange tuple of (min, max) values to search
		@keyparam subset Restrict to this subset of Record IDs
		@return Dict, key=recids, param value as values
		"""

		ind = self._getindex(param, ctx=ctx, txn=txn)
		if ind == None:
			return {}

		r = dict(ind.items(txn=txn))

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

		secure = self._filterbypermissions(ret.keys(), ctx=ctx, txn=txn)

		# remove any recids the user cannot access
		for i in set(ret.keys()) - secure:
			del ret[i]

		return ret




	@publicmethod("records.find.bypermissions")
	def getindexbypermissions(self, users=None, groups=None, subset=None, ctx=None, txn=None):
		"""Search permission indexes. Useful for seeing where permissions have been set.

		@keyparam users Single or iterable list of users
		@keyparam groups Single or iterable list of groups
		@keyparam subset Restrict to this subset of Record IDs
		@return Filtered set of records matching users/groups specified
		"""
		ret = set()

		ind = self._getindex("permissions", ctx=ctx, txn=txn)
		indg = self._getindex("groups", ctx=ctx, txn=txn)

		if users:
			for user in users:
				ret |= ind.get(user, set(), txn=txn)
		elif not groups:
			for k,v in ind.items(txn=txn):
				ret |= v

		if groups:
			for group in groups:
				ret |= indg.get(group, set(), txn=txn)
		elif not users:
			for k,v in indg.items(txn=txn):
				ret |= v


		if ctx.checkreadadmin() and not subset:
			return ret

		if subset:
			ret &= subset

		return self._filterbypermissions(ret, ctx=ctx, txn=txn)




	@publicmethod("records.list")
	def getindexbycontext(self, ctx=None, txn=None):
		"""Return all readable recids

		@return Set of all readable recids
		"""

		if ctx.checkreadadmin():
			return set(range(self.bdbs.records.get_max(txn=txn))) #+1)) # Ed: Fixed an off by one error

		ind = self._getindex("permissions", ctx=ctx, txn=txn)
		indg = self._getindex("groups", ctx=ctx, txn=txn)
		ret = ind.get(ctx.username, set(), txn=txn)

		for group in sorted(ctx.groups, reverse=True):
			ret |= indg.get(group, set(), txn=txn)

		return ret




	# ian: todo: finish this method
	# def getparamstatistics(self, param, ctx=None, txn=None):
	#	pass


	def _rebuild_indexkeys(self, ctx=None, txn=None):
		"""(Internal) Rebuild index-of-indexes"""

		g.log.msg("LOG_INFO", "self.bdbs.indexkeys: Starting rebuild")
		inds = dict(filter(lambda x:x[1]!=None, [(i,self._getindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

		g.log.msg("LOG_INDEX","self.bdbs.indexkeys.truncate")
		self.bdbs.indexkeys.truncate(txn=txn)

		for k,v in inds.items():
			pd = self.bdbs.paramdefs.get(k, txn=txn)
			g.log.msg("LOG_INDEX", "self.bdbs.indexkeys.addrefs: %s -> ...%s items"%(k, len(v)))
			self.bdbs.indexkeys.addrefs(k, v.keys(), txn=txn)




	#########################
	# section: Record Grouping Mechanisms
	#########################

	# ian: I intend to add more records.group.* methods.
	@publicmethod("records.group.byrecorddef")
	def groupbyrecorddef(self, recids, ctx=None, txn=None):
		"""This will take a set/list of record ids and return a dictionary of ids keyed by their recorddef

		@param recids
		@return Dict, keys are RecordDef names, values are set of recids
		"""

		ol, recids = listops.oltolist(recids)

		if len(recids) == 0:
			return {}

		if (len(recids) < 1000) or (isinstance(list(recids)[0],emen2.db.record.Record)):
			return self._groupbyrecorddef_fast(recids, ctx=ctx, txn=txn)

		# also converts to set..
		recids = self._filterbypermissions(recids, ctx=ctx, txn=txn)

		return self._groupbyrecorddef_index(recids, ctx=ctx, txn=txn)



	# this one gets records directly
	def _groupbyrecorddef_fast(self, records, ctx=None, txn=None):
		"""(Internal) Sometimes it's quicker to just get the records and filter, than to check all the indexes"""

		if not isinstance(list(records)[0],emen2.db.record.Record):
			records = self.getrecord(records, filt=1, ctx=ctx, txn=txn)

		ret={}
		for i in records:
			if not ret.has_key(i.rectype): ret[i.rectype]=set([i.recid])
			else: ret[i.rectype].add(i.recid)

		return ret

	
	
	def _groupbyrecorddef_index(self, recids, ctx=None, txn=None):
		ret = {}
		# we need to work with a copy becuase we'll be changing it
		recids = copy.copy(recids)
		ind = self._getindex("rectype", ctx=ctx, txn=txn)

		while recids:
			rid = recids.pop()	# get a random record id
			rec = self.bdbs.records.get(rid, txn=txn) # get the set of all records with this recorddef
			ret[rec.rectype] = ind.get(rec.rectype, txn=txn) & recids # intersect our list with this recdef
			recids -= ret[rec.rectype] # remove the results from our list since we have now classified them
			ret[rec.rectype].add(rid) # add back the initial record to the set

		return ret



	###############################
	# section: relationships
	###############################


	#@rename db.<RelateBTree>.children
	@publicmethod("rels.children")
	def getchildren(self, key, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get children.

		@param keys A (single or iterable) Record ID, RecordDef name, or ParamDef name
		@keyparam keytype Children of type: record, paramdef, or recorddef
		@keyparam recurse Recursion level (default is 1, e.g. just immediate children)
		@keyparam rectype For Records, limit to a specific rectype
		@return Set of children. If request was an iterable, return a dict, with input keys for keys, and children for values
		"""
		return self._getrel_wrapper(keys=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", tree=False, ctx=ctx, txn=txn)



	# This is a new method -- might need some testing.
	@publicmethod("rels.siblings")
	def getsiblings(self, key, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get siblings of an item. @see getchildren."""

		parents = self.getparents(key, keytype=keytype, ctx=ctx, txn=txn)
		siblings = listops.combine(self.getchildren(parents, keytype=keytype, rectype=rectype, ctx=ctx, txn=txn).values(), dtype=list)
		if siblings:
			return siblings[0]
		return []



	#@rename db.<RelateBTree>.parents
	@publicmethod("rels.parents")
	def getparents(self, key, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get parents of an item. @see getchildren."""
		return self._getrel_wrapper(keys=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", tree=False, ctx=ctx, txn=txn)



	@publicmethod("rels.childtree")
	def getchildtree(self, keys, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get multiple children for multiple items.

		@param keys A (single or iterable) Record ID, RecordDef name, or ParamDef name
		@keyparam keytype Children of type: record, paramdef, or recorddef
		@keyparam recurse Recursion level (default is 1, e.g. just immediate children)
		@keyparam rectype For Records, limit to a specific rectype
		@return Dict, keys are Record IDs or ParamDef/RecordDef names, values are sets of children for that key
		"""
		return self._getrel_wrapper(keys=keys, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", tree=True, ctx=ctx, txn=txn)



	@publicmethod("rels.parenttree")
	def getparenttree(self, keys, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""See getchildtree"""
		return self._getrel_wrapper(keys=keys, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", tree=True, ctx=ctx, txn=txn)



	def _getrel_wrapper(self, keys, keytype="record", recurse=1, rectype=None, rel="children", tree=False, ctx=None, txn=None):
		"""(Internal) See getchildren/getparents, which are the wrappers/entry points for this method. This abstracts out rel=children/parents."""

		if recurse == -1:
			recurse = g.MAXRECURSE
		if recurse == False:
			recurse = True

		ol, keys = listops.oltolist(keys)

		_keytypemap = dict(
			record=self.bdbs.records,
			paramdef=self.bdbs.paramdefs,
			recorddef=self.bdbs.recorddefs
			)

		if keytype in _keytypemap:
			reldb = _keytypemap[keytype]
		else:
			raise ValueError, "Invalid keytype"

		# For convenience, allow dbobjects to be passed directly
		keys, dbokeys = emen2.util.listops.partition_dbobjects(keys)
		keys.extend([i.name for i in dbokeys])

		# This calls the relationship getting method in the appropriate RelateBTree
		# result is a two-level dictionary
		# k1 = input recids
		# k2 = related recid and v2 = relations of k2
		t=time.time()
		result, ret_visited = {}, {}
		for i in keys:
			result[i], ret_visited[i] = getattr(reldb, rel)(i, recurse=recurse, txn=txn)

		# Flatten the dictionary to get all touched keys
		allr = set().union(*ret_visited.values())

		# Restrict to a particular rectype
		if rectype:
			allr &= self.getindexbyrecorddef(rectype, ctx=ctx, txn=txn)

		# Filter by permissions
		if keytype == "record":
			allr &= self._filterbypermissions(allr, ctx=ctx, txn=txn)

		# perform filtering on both levels, and removing any items that become empty
		# If Tree=True, we're returning the tree...
		if tree:
			outret = {}
			for k, v in result.iteritems():
				for k2 in v:
					outret[k2] = result[k][k2] & allr

			return outret

		# Else we're just ruturning the total list of all children, keyed by requested recid
		for k in ret_visited:
			ret_visited[k] &= allr


		if ol: return return_first_or_none(ret_visited)
		return ret_visited




	#@remove; although, it's used in a few places where it's useful..
	@publicmethod("rels.pcs.unlinks", write=True)
	def pcunlinks(self, links, keytype="record", ctx=None, txn=None):
		"""Remove parent/child relationships. See pclink/pcunlink.

		@param links [[parent 1,child 1],[parent 2,child 2], ...]
		@keyparam keytype Link this type: ["record","paramdef","recorddef"] (default is "record")
		@return
		"""
		self._link("pcunlink", links, keytype=keytype, ctx=ctx, txn=txn)




	@publicmethod("rels.pc.links", write=True)
	def pclink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Establish a parent-child relationship between two keys.
		A context is required for record links, and the user must have write permission on at least one of the two.

		@param pkey Parent
		@param ckey Child
		@keyparam Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		self._link("pclink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	@publicmethod("rels.pc.unlink", write=True)
	def pcunlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Remove a parent-child relationship between two keys.

		@param pkey Parent
		@param ckey Child
		@keyparam Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		self._link("pcunlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	@publicmethod("rels.pc.relink", write=True)
	def pcrelink(self, remove, add, keytype="record", ctx=None, txn=None):
		def conv(link):
			pkey, ckey = link
			if keytype=="record":
				return int(pkey), int(ckey)
			return unicode(pkey), unicode(ckey)

		remove = set(map(conv, remove))
		add = set(map(conv, add))		
		common = remove & add
		remove -= common
		add -= common
		
		self._link("pcunlink", remove, keytype=keytype, ctx=ctx, txn=txn)
		self._link("pclink", add, keytype=keytype, ctx=ctx, txn=txn)



	def _link(self, mode, links, keytype="record", ctx=None, txn=None):
		"""(Internal) the *link functions wrap this."""
		#admin overrides security checks
		admin = False
		if ctx.checkadmin(): admin = True

		if keytype not in ["record", "recorddef", "paramdef"]:
			raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

		if mode not in ["pclink","pcunlink","link","unlink"]:
			raise Exception, "Invalid relationship mode %s"%mode

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "linking mode %s requires record creation priveleges"%mode

		# ian: these are just silently filtered out now..
		#if filter(lambda x:x[0] == x[1], links):
		#	g.log.msg("LOG_ERROR","Cannot link to self: keytype %s"%(keytype))
		#	return

		if not links:
			return

		# Get a list of all items in all links
		items = set()
		for i in links:
			for j in i:
				items.add(j)

		# ian: todo: high: for recorddef/paramdefs, check that all items exist..
		# self.getparamdef(items, filt=False, ctx=ctx, txn=txn)

		# ian: circular reference detection.
		# ian: todo: high: turn this back on..

		#if mode=="pclink":
		#	p = self._getrel(key=pkey, keytype=keytype, recurse=g.MAXRECURSE, rel="parents")[0]
		#	c = self._getrel(key=pkey, keytype=keytype, recurse=g.MAXRECURSE, rel="children")[0]
		#	if pkey in c or ckey in p or pkey == ckey:
		#		raise Exception, "Circular references are not allowed: parent %s, child %s"%(pkey,ckey)

		# Check that items exist
		if keytype == "record":
			recs = dict([(x.recid,x) for x in self.getrecord(items, filt=False, ctx=ctx, txn=txn)])
			for a,b in links:
				if not (admin or (recs[a].writable() or recs[b].writable())):
					raise emen2.db.exceptions.SecurityError, "pclink requires partial write permission: %s <-> %s"%(a,b)

		elif keytype == "paramdef":
			self.getparamdef(items, filt=False, ctx=ctx, txn=txn)

		elif keytype == "recorddef":
			self.getrecorddef(items, filt=False, ctx=ctx, txn=txn)

		self._commit_link(keytype, mode, links, ctx=ctx, txn=txn)




	def _commit_link(self, keytype, mode, links, ctx=None, txn=None):
		"""(Internal) Write links"""

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


		for pkey,ckey in links:
			g.log.msg("LOG_COMMIT", "self.bdbs.%s.%s: %s -> %s"%(keytype, mode, pkey, ckey))
			linker(pkey, ckey, txn=txn)





	###############################
	# section: Admin User Management
	###############################


	@publicmethod("users.disable", write=True, admin=True)
	def disableuser(self, usernames, filt=False, ctx=None, txn=None):
		"""Disable a user. Admins-only.

		@param usernames Single or iterable list of usernames to disable
		@keyparam filt Ignore failures
		@return List of usernames disabled
		"""
		return self._setuserstate(usernames=usernames, disabled=True, filt=filt, ctx=ctx, txn=txn)



	@publicmethod("users.enable", write=True, admin=True)
	def enableuser(self, usernames, filt=False, ctx=None, txn=None):
		"""Enable a disabled user.

		@param username

		@keyparam filt Ignore failures
		"""
		return self._setuserstate(usernames=usernames, disabled=False, filt=filt, ctx=ctx, txn=txn)



	def _setuserstate(self, usernames, disabled, filt=False, ctx=None, txn=None):
		"""(Internal) Set username as enabled/disabled. 0 is enabled. 1 is disabled."""

		ol, usernames = listops.oltolist(usernames)

		state = bool(disabled)

		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can disable users"

		if not hasattr(usernames, "__iter__"):
			usernames = [usernames]

		commitusers = []
		for username in usernames:
			if username == ctx.username:
				g.warn('Warning: user %s tried to disable themself' % ctx.username)
				continue

			if filt:
				user = self.bdbs.users.get(username, txn=txn)
				if not user:
					continue
			else:
				user = self.bdbs.users.sget(username, txn=txn)

			if user.disabled == state:
				continue

			user.disabled = bool(state)
			commitusers.append(user)


		self._commit_users(commitusers, ctx=ctx, txn=txn)

		t = "enabled"
		if disabled:
			t="disabled"

		ret = [user.username for user in commitusers]

		# g.log.msg('LOG_INFO', "Users %s %s by %s"%(ret, t, ctx.username))

		if ol: return return_first_or_none(ret)
		return ret



	@publicmethod("users.put", write=True, admin=True)
	def putuser(self, users, warning=False, ctx=None, txn=None):
		"""Admin-only method to directly modify a User. Generally used during import/clone."""
		ol, users = listops.oltolist(users)
		users = [emen2.db.user.User(user, ctx=ctx) for user in users]
		for user in users:
			user.setContext(ctx)
			user.validate(warning=warning)

		self._commit_users(users, ctx=ctx, txn=txn)

		if ol: return return_first_or_none(users)
		return users
		



	@publicmethod("users.queue.approve", write=True, admin=True)
	def approveuser(self, usernames, secret=None, filt=False, ctx=None, txn=None):
		"""Approve account in user queue

		@param usernames Single or iterabe list of accounts to approve from new user queue
		@keyparam filt Ignore failures
		@return List of usernames approved
		"""

		ol, usernames = listops.oltolist(usernames)
		admin = ctx.checkadmin()

		if not admin:
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		delusers, records, childstore = {}, {}, {}
		addusers = []

		# Need to commit users before records will validate
		for username in usernames:

			# Get the user from the queue
			try:
				user = self.bdbs.newuserqueue.sget(username, txn=txn)
				if not user:
					raise KeyError, "User %s is not pending approval"%username

				user.setContext(ctx)
				user.validate()
			except Exception, msg:
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise

			# Check that this user does not already exist
			if self.bdbs.users.get(user.username, txn=txn):
				delusers[username] = None
				msg = "User %s already exists, removing from queue"%user.username
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise KeyError, msg


			# Check that there is no other user with the same email address
			if self.bdbs.usersbyemail.get(user.email.lower(), txn=txn):
				delusers[username] = None
				msg = "The email address %s is already in use, removing from queue"%(user.email)
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise KeyError, msg


			# clear out the secret
			addusers.append(user)
			delusers[username] = None


		# Update user queue / users
		self._commit_users(addusers, ctx=ctx, txn=txn)
		self._commit_newusers(delusers, ctx=ctx, txn=txn)

		# ian: todo: Do we need this root ctx? Probably...
		tmpctx = self._makerootcontext(txn=txn)

		# Pass 2 to add records
		for user in addusers:
			rec = self.newrecord("person", ctx=tmpctx, txn=txn)

			rec["username"] = user.username
			rec["email"] = user.signupinfo.get('email')

			name = user.signupinfo.get('name', ['', '', ''])
			rec["name_first"], rec["name_middle"], rec["name_last"] = name[0], ' '.join(name[1:-1]) or None, name[1]

			rec.adduser(user.username, level=3)
			rec.addgroup("authenticated")

			for k,v in user.signupinfo.items():
				rec[k] = v

			rec = self.putrecord(rec, ctx=tmpctx, txn=txn)
			user.record = rec.recid
			user.signupinfo = None

		self._commit_users(addusers, ctx=ctx, txn=txn)


		if user.username != 'root':
			for group in g.GROUP_DEFAULTS:
				gr = self.getgroup(group, ctx=tmpctx, txn=txn)
				if gr:
					gr.adduser(user.username)
					self.putgroup(gr, ctx=tmpctx, txn=txn)
				else:
					g.warn('Default Group %r is non-existent'%group)


		# Send the emails
		for user in addusers:
			ctxt = {'username':user.username}
			self.sendmail(user.email, '/email/adduser.approved', ctxt=ctxt, ctx=ctx, txn=txn)


		ret = [user.username for user in addusers]
		if ol: return return_first_or_none(ret)
		return ret



	@publicmethod("users.queue.reject", write=True, admin=True)
	def rejectuser(self, usernames, filt=False, ctx=None, txn=None):
		"""Remove a user from the pending new user queue

		@param usernames Single or iterable list of usernames to reject from new user queue
		@keyparam filt Ignore failures
		@return List of rejected users
		"""

		ol, usernames = listops.oltolist(usernames)

		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		delusers = {}
		emails = {}

		for username in usernames:
			try:
				user = self.bdbs.newuserqueue.sget(username, txn=txn)
			except:
				if filt: continue
				else: raise KeyError, "User %s is not pending approval" % username

			emails[user.username] = user.email
			delusers[user.username] = None

		self._commit_newusers(delusers, ctx=ctx, txn=txn)

		# Send the emails
		for username in delusers.keys():
			email = emails.get(username)
			ctxt = {'username':username}
			self.sendmail(email, '/email/adduser.rejected', ctxt=ctxt, ctx=ctx, txn=txn)


		ret = delusers.keys()
		if ol: return return_first_or_none(ret)
		return ret




	@publicmethod("users.queue.list", admin=True)
	def getuserqueue(self, ctx=None, txn=None):
		"""Returns a list of names of unapproved users

		@return Set of users in approval queue
		"""

		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		return set(self.bdbs.newuserqueue.keys(txn=txn))



	@publicmethod("users.queue.get", admin=True)
	def getqueueduser(self, username, ctx=None, txn=None):
		"""Get user from new user queue.

		@param username Username ot get from new user queue
		@return User from user queue
		"""

		if not ctx.checkreadadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can access pending users"

		ret = self.bdbs.newuserqueue.sget(username, txn=txn)
		ret.setContext(ctx)
		return ret




	@publicmethod("users.new")
	def newuser(self, username, password, email, ctx=None, txn=None):
		"""Construct a new User instance.

		@param username Required user field
		@param password Required user field. See restrictionsin user.py.
		@param email Required user field
		@return New User
		"""
		user = emen2.db.user.User(username=username, password=password, email=email)
		user.setContext(ctx)
		return user




	###############################
	# section: User Management
	###############################


	@publicmethod("users.setprivacy", write=True)
	def setprivacy(self, state, username=None, ctx=None, txn=None):
		"""Set privacy level for user information.

		@state 0, 1, or 2, in increasing level of privacy.
		@keyparam username Username to modify (admin only)
		"""

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise emen2.db.exceptions.SecurityError, "Cannot attempt to set other user's privacy levels"
		else:
			username = ctx.username

		try:
			state=int(state)
			if state not in [0,1,2]:
				raise ValueError
		except ValueError, inst:
			raise Exception, "Invalid state. Must be 0, 1, or 2."

		commitusers = []

		if username != ctx.username and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Cannot set another user's privacy"

		user = self.getuser(username, ctx=ctx, txn=txn)
		user.privacy = state
		commitusers.append(user)

		self._commit_users(commitusers, ctx=ctx, txn=txn)



	def _userbyemail(self, email, ctx=None, txn=None):
		byemail = self.bdbs.usersbyemail.get(email.lower(), txn=txn)
		username = None
		if len(byemail) == 1:
			username = byemail.pop()
		return username



	@publicmethod("auth.resetpassword", write=True)
	def resetpassword(self, username, newpassword=None, secret=None, ctx=None, txn=None):

		errmsg = "Could not reset password"
		username = self._userbyemail(username, ctx=ctx, txn=txn) or username

		try:
			user = self.bdbs.users.sget(username, txn=txn)
			user.setContext(ctx)
		except Exception, e:
			g.log.msg('LOG_SECURITY', "Password reset failed for %s: %s"%(username, e))
			time.sleep(2)
			raise emen2.db.exceptions.AuthenticationError, "No account associated with %s"%username


		try:
			# Absolutely never reveal the secret via any mechanism but email to registered address
			user.resetpassword()
			ctxt = {'secret': user._secret[2]}
			self.sendmail(user.email, '/email/password.reset', ctxt, ctx=ctx, txn=txn)

		except Exception, e:
			g.log.msg('LOG_SECURITY', "Password reset failed for %s: %s"%(username, e))
			raise emen2.db.exceptions.AuthenticationError, errmsg


		g.log.msg("LOG_SECURITY","Setting resetpassword secret for %s"%user.username)
		self._commit_users([user], ctx=ctx, txn=txn)



	@publicmethod("auth.setpassword", write=True)
	def setpassword(self, oldpassword, newpassword, secret=None, username=None, ctx=None, txn=None):
		"""Change password.

		@param oldpassword
		@param newpassword
		@keyparam username Username to modify (Admin only)
		"""

		username = self._userbyemail(username, ctx=ctx, txn=txn) or username
		msg = "Could not change password"

		# ian: need to read directly because getuser hides password
		user = self.bdbs.users.sget(username, txn=txn)
		user.setContext(ctx)

		# Existing password / auth token is checked before password is reset.. Or user is admin.
		#try:
		user.setpassword(oldpassword, newpassword, secret=secret)
		# except:
		# 	raise emen2.db.exceptions.SecurityError, msg

		g.log.msg("LOG_SECURITY","Changing password for %s"%user.username)

		self._commit_users([user], ctx=ctx, txn=txn)
		
		self.sendmail(user.email, '/email/password.changed', ctx=ctx, txn=txn)

		return username



	@publicmethod("users.setemail", write=True)
	def setemail(self, email, secret=None, username=None, password=None, ctx=None, txn=None):
		"""Change email
		@param email
		@keyparam username Username to modify
		@keyparam secret Auth token
		@keyparam password Current account password is required
		"""

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise emen2.db.exceptions.SecurityError, "You may only change your own email address"
		else:
			username = ctx.username

		if not username or username == "anonymous":
			raise emen2.db.exceptions.SecurityError, "You must login before completing this action"

		if self.bdbs.usersbyemail.get(email.lower(), txn=txn):
			time.sleep(2)
			raise emen2.db.exceptions.SecurityError, "The email address %s is already in use"%(email)

		# user.setemail will check the password and secret, and raise an exception if something is wrong.
		# if password and no secret, set auth token
		# if secret, check the secret and set email and return the new email
		user = self.bdbs.users.sget(username, txn=txn)
		user.setContext(ctx)
		ret = user.setemail(email, secret=secret, password=password)
		user.validate()

		ctxt = {}
		if ret:
			self.sendmail(email, '/email/email.verified', ctxt, ctx=ctx, txn=txn)
		else:
			ctxt['secret'] = user._secret[2]
			self.sendmail(email, '/email/email.verify', ctxt, ctx=ctx, txn=txn)

		g.log.msg("LOG_INFO","Changing email for %s"%user.username)

		self._commit_users([user], ctx=ctx, txn=txn)
		return ret




	@publicmethod("users.queue.put", write=True)
	def adduser(self, user, ctx=None, txn=None):
		"""Adds a new user. However, note that this only adds the record to the
		new user queue, which must be processed by an administrator before the record
		becomes active. This system prevents problems with securely assigning passwords
		and errors with data entry. Anyone can create one of these.

		@param user New user instance/dict
		@return New user instance
		"""

		try:
			user = emen2.db.user.User(user, ctx=ctx)
		except Exception, inst:
			raise ValueError, "User instance or dict required (%s)"%inst

		if self.bdbs.users.get(user.username, txn=txn) or self.bdbs.usersbyemail.get(user.email.lower(), txn=txn):
			raise KeyError, "An account already exists with this username or email address"

		#if user.username in self.bdbs.newuserqueue:
		if self.bdbs.newuserqueue.get(user.username, txn=txn):
			raise KeyError, "User with username '%s' already pending approval" % user.username

		if user.username != 'root':
			user.validate()

		self._commit_newusers({user.username:user}, ctx=None, txn=txn)

		# Send account request email
		self.sendmail(user.email, '/email/adduser.signup')

		if ctx.checkadmin():
			self.approveuser(user.username, ctx=ctx, txn=txn)

		return user





	#@write #self.bdbs.users
	def _commit_users(self, users, ctx=None, txn=None):
		"""(Internal) Updates user. Takes validated User."""

		for user in users:
			ouser = self.bdbs.users.get(user.username, txn=txn)

			g.log.msg("LOG_COMMIT","self.bdbs.users.set: %s"%user.username)
			self.bdbs.users.set(user.username, user, txn=txn)

			try:
				oldemail = ouser.email
			except:
				oldemail = ''

			# root's email is not indexed because
			#	 the email for root will often also be used for a user acct
			if oldemail != user.email and user.username != "root":
				#g.log.msg("LOG_INDEX","self.bdbs.usersbyemail.addrefs: %s -> %s"%(user.email.lower(), user.username))
				self.bdbs.usersbyemail.addrefs(user.email.lower(), [user.username], txn=txn)
				#g.log.msg("LOG_INDEX","self.bdbs.usersbyemail.removerefs: %s -> %s"%(oldemail.lower(), user.username))
				self.bdbs.usersbyemail.removerefs(oldemail.lower(), [user.username], txn=txn)




	#@write #self.bdbs.newuserqueue
	def _commit_newusers(self, users, ctx=None, txn=None):
		"""(Internal) Write to newuserqueue; users is dict; set value to None to del"""

		for username, user in users.items():
			if user:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.set: %s"%username)
			else:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.__delitem__: %s"%username)

			self.bdbs.newuserqueue.set(username, user, txn=txn)





	@publicmethod("users.get")
	def getuser(self, usernames, filt=True, lnf=False, getgroups=False, getrecord=True, ctx=None, txn=None):
		"""Get user information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record

		@param usernames Single or iterable list of usernames or Record IDs
		@keyparam filt Ignore failures
		@keyparam lnf Get user 'display name' as Last Name First (default=False)
		@keyparam getgroups Include user groups (default=False)
		@keyparam getrecord Include user information (default=True)
		@return List of users
		"""

		ol, usernames = listops.oltolist(usernames)

		# Are we looking for users referenced in records?
		recs = [x for x in usernames if isinstance(x, emen2.db.record.Record)]
		rec_ints = [x for x in usernames if isinstance(x, int)]

		if rec_ints:
			recs.extend(self.getrecord(rec_ints, filt=True, ctx=ctx, txn=txn))

		# ian: todo: urgent! replace this.
		#if recs:
		#	un2 = self.filtervartype(recs, vts=["user","userlist","acl"], flat=True, ctx=ctx, txn=txn)
		#	usernames.extend(un2)

		# Check list of users
		usernames = set(x.strip().lower() for x in usernames if isinstance(x, basestring))

		ret = []

		for i in usernames:
			user = self.bdbs.users.get(i, None, txn=txn)

			if user == None:
				if filt:
					continue
				else:
					raise KeyError, "No such user: %s"%i

			user.setContext(ctx)

			# if the user has requested privacy, we return only basic info
			if user.privacy and not (ctx.checkreadadmin() or ctx.username == user.username):
				# password is just dummy value because of how the constructor works; it's immediately set to None
				user = emen2.db.user.User(username=user.username, email=user.email, password='123456')
				user.email = None
				user.password = None

			# Anonymous users cannot use this to extract email addresses
			if ctx.username == "anonymous":
				user.email = None

			if getgroups:
				user.groups = self.bdbs.groupsbyuser.get(user.username, set(), txn=txn)

			if getrecord:
				user.getuserrec(lnf=lnf)
			# ian: todo: complicated -- users need to get their own hash pw's to change their emails..
			# user.password = None
			ret.append(user)

		if ol: return return_first_or_none(ret)
		return ret





	@publicmethod("users.list")
	def getusernames(self, ctx=None, txn=None):
		"""Return a set of all usernames. Not available to anonymous users.

		@return set of all usernames
		"""
		if ctx.username == "anonymous":
			return set()

		return set(self.bdbs.users.keys(txn=txn))




	##########################
	# section: Group Management
	##########################


	@publicmethod("groups.list")
	def getgroupnames(self, ctx=None, txn=None):
		"""Return a set of all Group names

		@return Set of all Group names
		"""
		return set(self.bdbs.groups.keys(txn=txn))



	@publicmethod("groups.get")
	def getgroup(self, groups, filt=True, ctx=None, txn=None):
		"""Get a group, which includes the owners, members, etc.

		@param groups A single or iterable of Group names
		@keyparam filt Ignore failures
		@return Group or list of groups
		"""
		ol, groups = listops.oltolist(groups)

		if filt:
			lfilt = self.bdbs.groups.get
		else:
			lfilt = self.bdbs.groups.sget

		ret = filter(None, [lfilt(i, txn=txn) for i in groups])
		for i in ret:
			i.setContext(ctx)
			if not i.get('displayname'):
				i.displayname = i.name

		if ol: return return_first_or_none(ret)
		return ret



	#@write self.bdbs.groupsbyuser
	def _commit_groupsbyuser(self, addrefs=None, delrefs=None, ctx=None, txn=None):
		"""(Internal) Update groupbyuser index"""

		for user,groups in addrefs.items():
			try:
				if groups:
					#g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser.addrefs: %s -> %s"%(user, groups))
					self.bdbs.groupsbyuser.addrefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Critical! self.bdbs.groupsbyuser.addrefs %s failed: %s"%(user, inst))
				raise

		for user,groups in delrefs.items():
			try:
				if groups:
					#g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser.removerefs: %s -> %s"%(user, groups))
					self.bdbs.groupsbyuser.removerefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Critical! self.bdbs.groupsbyuser.removerefs %s failed: %s"%(user, inst))
				raise





	def _rebuild_groupsbyuser(self, ctx=None, txn=None):
		"""(Internal) Rebuild groupbyuser index"""

		g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser: Rebuilding index")

		groups = self.getgroup(self.getgroupnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		users = collections.defaultdict(set)

		for group in groups:
			for user in group.members():
				users[user].add(group.name)

		g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser.truncate")
		self.bdbs.groupsbyuser.truncate(txn=txn)

		for k,v in users.items():
			g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser.addrefs: %s -> %s"%(k,v))
			self.bdbs.groupsbyuser.addrefs(k, v, txn=txn)





	def _rebuild_usersbyemail(self, ctx=None, txn=None):
		usernames = self.getusernames(ctx=ctx, txn=txn)
		users = self.getuser(usernames, ctx=ctx, txn=txn)

		g.log.msg("LOG_INDEX","self.bdbs.usersbyemail.truncate")
		self.bdbs.usersbyemail.truncate(txn=txn)

		for user in users:
			#g.log.msg("LOG_INDEX","self.bdbs.usersbyemail.addrefs: %s -> %s"%(user.email.lower(), user.username))
			self.bdbs.usersbyemail.addrefs(user.email.lower(), [user.username], txn=txn)



	def _reindex_groupsbyuser(self, groups, ctx=None, txn=None):
		"""(Internal) Reindex a group's members for the groupsbyuser index"""

		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)

		for group in groups:

			ngm = group.members()
			try:
				ogm = self.bdbs.groups.get(group.name, txn=txn).members()
			except:
				ogm = set()

			addusers = ngm - ogm
			delusers = ogm - ngm

			for user in addusers:
				addrefs[user].add(group.name)
			for user in delusers:
				delrefs[user].add(group.name)

		return addrefs, delrefs



	@publicmethod("groups.new")
	def newgroup(self, ctx=None, txn=None):
		group = emen2.db.group.Group()
		group.adduser(ctx.username, level=3)
		group.setContext(ctx)
		return group




	# ian: fix non-admin group editing
	@publicmethod("groups.put", write=True, admin=True)
	def putgroup(self, groups, warning=False, ctx=None, txn=None):
		"""Commit changes to a group or groups.

		@param groups A single or iterable Group

		@return Modified Group or Groups
		"""

		ol, groups = listops.oltolist(groups)
		admin = ctx.checkcreate()
		if not admin:
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to create or edit a group"
			
		groups2 = []

		groups2.extend(x for x in groups if isinstance(x, emen2.db.group.Group))
		groups2.extend(emen2.db.group.Group(x, ctx=ctx) for x in groups if isinstance(x, dict))

		commitgroups = []

		for group in groups2:
			try:
				og = self.getgroup(group.name, ctx=ctx, txn=txn, filt=False)
			except KeyError:
				if not admin:
					raise emen2.db.exceptions.SecurityError, "Insufficient permissions to create or edit a group"
				else:
					og = group

			og.setContext(ctx)
			og.validate(txn=txn)			
			og.setpermissions(group.permissions)
			og.displayname = group.displayname		
					
			commitgroups.append(og)



		self._commit_groups(commitgroups, ctx=ctx, txn=txn)

		if ol: return return_first_or_none(commitgroups)
		return groups2



	def _commit_groups(self, groups, ctx=None, txn=None):
		"""(Internal) see putgroup """

		addrefs, delrefs = self._reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

		for group in groups:
			g.log.msg("LOG_COMMIT","self.bdbs.groups.set: %s"%(group.name))
			self.bdbs.groups.set(group.name, group, txn=txn)

		self._commit_groupsbyuser(addrefs=addrefs, delrefs=delrefs, ctx=ctx, txn=txn)




	#########################
	# section: workflow
	#########################

	# ian: todo: medium priority, medium difficulty:
	#	Workflows are currently turned off, need to be fixed.
	#	Do this soon.

	# @publicmethod
	# def getworkflow(self, ctx=None, txn=None):
	# 	"""This will return an (ordered) list of workflow objects for the given context (user).
	# 	it is an exceptionally bad idea to change a WorkFlow object's wfid."""
	#
	# 	if ctx.username == None:
	# 		raise emen2.db.exceptions.SecurityError, "Anonymous users have no workflow"
	#
	# 	try:
	# 		return self.bdbs.workflow.sget(ctx.username, txn=txn) #[ctx.username]
	# 	except:
	# 		return []
	#
	#
	#
	# @publicmethod
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
	# @publicmethod
	# def newworkflow(self, vals, ctx=None, txn=None):
	# 	"""Return an initialized workflow instance."""
	# 	return WorkFlow(vals)
	#
	#
	#
	#
	# @publicmethod
	# def addworkflowitem(self, work, ctx=None, txn=None):
	# 	"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""
	#
	# 	if ctx.username == None:
	# 		raise emen2.db.exceptions.SecurityError, "Anonymous users have no workflow"
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
	# @publicmethod
	# def delworkflowitem(self, wfid, ctx=None, txn=None):
	# 	"""This will remove a single workflow object based on wfid"""
	# 	#self = db
	#
	# 	if ctx.username == None:
	# 		raise emen2.db.exceptions.SecurityError, "Anonymous users have no workflow"
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
	# @publicmethod
	# def setworkflow(self, wflist, ctx=None, txn=None):
	# 	"""This allows an authorized user to directly modify or clear his/her workflow. Note that
	# 	the external application should NEVER modify the wfid of the individual WorkFlow records.
	# 	Any wfid's that are None will be assigned new values in this call."""
	# 	#self = db
	#
	# 	if ctx.username == None:
	# 		raise emen2.db.exceptions.SecurityError, "Anonymous users have no workflow"
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
	# def _commit_workflow(self, wfs, ctx=None, txn=None):
	# 	pass




	#########################
	# section: paramdefs
	#########################

	@publicmethod("paramdefs.vartypes")
	def getvartypenames(self, ctx=None, txn=None):
		"""Returns a list of all valid variable types.

		@return Set of vartypes
		"""
		return set(self.vtm.getvartypes())





	@publicmethod("paramdefs.properties")
	def getpropertynames(self, ctx=None, txn=None):
		"""Return a list of all valid properties.

		@return list of properties
		"""
		return set(self.vtm.getproperties())





	@publicmethod("paramdefs.units")
	def getpropertyunits(self, propname, ctx=None, txn=None):
		"""Returns a list of known units for a particular property
		@param propname Property name
		@return a set of known units for property
		"""

		return set(self.vtm.getproperty(propname).units)






	@publicmethod("paramdefs.new")
	def newparamdef(self, ctx=None, txn=None):
		pd = emen2.db.paramdef.ParamDef()
		pd.setContext(ctx)
		return pd





	@publicmethod("paramdefs.put", write=True)
	def putparamdef(self, paramdef, parents=None, children=None, warning=False, ctx=None, txn=None):
		"""Add or update a ParamDef. Updates are limited to descriptions. Only administrators may change existing paramdefs in any way that changes their meaning, and even this is strongly discouraged.

		@param paramdef A paramdef instance

		@keyparam parents Link to parents
		@keyparam children Link to children

		@return Updated ParamDef
		"""

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "No permission to create new ParamDefs (need record creation permission)"

		paramdef = emen2.db.paramdef.ParamDef(paramdef, ctx=ctx)
		orec = self.bdbs.paramdefs.get(paramdef.name, txn=txn) or paramdef
		orec.setContext(ctx)

		#####################
		# Root is permitted to force some changes in parameters, though they are supposed to be static
		# This permits correcting typos, etc., but should not be used routinely
		if orec != paramdef and not ctx.checkadmin():
			raise KeyError, "Only administrators can modify paramdefs: %s"%paramdef.name

		if orec.vartype != paramdef.vartype:
			g.log.msg("LOG_CRITICAL","Warning! Changing paramdef %s vartype from %s to %s. This MAY REQUIRE database revalidation and reindexing!!"%(paramdef.name, paramdef.vartype, paramdef.vartype))

		# These are not allowed to be changed
		paramdef.creator = orec.creator
		paramdef.creationtime = orec.creationtime
		paramdef.uri = orec.uri

		paramdef.validate()

		######### ^^^ ############

		self._commit_paramdefs([paramdef], ctx=ctx, txn=txn)

		# create the index for later use
		# paramindex = self._getindex(paramdef.name, create=True, ctx=ctx, txn=txn)

		# If parents or children are specified, add these relationships
		links = []
		if parents:
			links.extend( map(lambda x:(x, paramdef.name), parents) )
		if children:
			links.extend( map(lambda x:(paramdef.name, x), children) )
		for link in links:
			self.pclink(link[0], link[1], keytype="paramdef", ctx=ctx, txn=txn)

		return paramdef



	def _commit_paramdefs(self, paramdefs, ctx=None, txn=None):
		"""(Internal) Commit paramdefs"""

		for paramdef in paramdefs:
			g.log.msg("LOG_COMMIT","self.bdbs.paramdefs.set: %s"%paramdef.name)
			self.bdbs.paramdefs.set(paramdef.name, paramdef, txn=txn)






	@publicmethod("paramdefs.get")
	def getparamdef(self, keys, filt=True, ctx=None, txn=None):
		"""Get ParamDefs

		@param recs ParamDef name, list of names, a Record, or list of Records

		@keyparam filt Ignore failures

		@return A ParamDef or list of ParamDefs
		"""

		ol, keys = listops.oltolist(keys)

		params = filter(lambda x:isinstance(x, basestring), keys)
		params = set([i.strip().lower() for i in params])

		# Process records if given
		recs = (x for x in keys if isinstance(x, (int, emen2.db.record.Record)))
		recs = self.getrecord(recs, ctx=ctx, txn=txn)
		if recs:
			q = set([i.rectype for i in recs])
			for i in q:
				params |= set(self.getrecorddef(i, ctx=ctx, txn=txn).paramsK)
			for i in recs:
				params |= set(i.getparamkeys())


		# Get paramdefs
		if filt:
			lfilt = self.bdbs.paramdefs.get
		else:
			lfilt = self.bdbs.paramdefs.sget


		paramdefs = filter(None, [lfilt(i, txn=txn) for i in params])
		for pd in paramdefs:
			if pd.vartype not in self.indexablevartypes:
				pd.indexed = False
			# pd.setContext(ctx)

		if ol: return return_first_or_none(paramdefs)
		return paramdefs





	@publicmethod("paramdefs.list")
	def getparamdefnames(self, ctx=None, txn=None):
		"""Return a list of all ParamDef names

		@return set of all ParamDef names
		"""
		return set(self.bdbs.paramdefs.keys(txn=txn))




	def _getindex(self, paramname, ctx=None, txn=None):
		"""(Internal) Return handle to param index"""

		create = True
		ind = self.bdbs.fieldindex.get(paramname)
		if ind:
			return ind

		pd = self.bdbs.paramdefs.sget(paramname, txn=txn) # Look up the definition of this field
		paramname = pd.name
		if pd.vartype not in self.indexablevartypes or not pd.indexed:
			return None

		tp = self.vtm.getvartype(pd.vartype).keytype

		if not create and not os.access("%s/index/params/%s.bdb"%(self.path, paramname), os.F_OK):
			raise KeyError, "No index for %s" % paramname

		# opens with autocommit, don't need to pass txn
		self.bdbs.openparamindex(paramname, keytype=tp, dbenv=self.dbenv, txn=txn)

		return self.bdbs.fieldindex[paramname]




	#########################
	# section: recorddefs
	#########################


	@publicmethod("recorddefs.new")
	def newrecorddef(self, ctx=None, txn=None):
		rd = emen2.db.recorddef.RecordDef(ctx=ctx)
		rd.setContext(ctx)
		return rd




	@publicmethod("recorddefs.put", write=True)
	def putrecorddef(self, recdef, parents=None, children=None, warning=False, ctx=None, txn=None):
		"""Add or update RecordDef. The mainview should
		never be changed once used, since this will change the meaning of
		data already in the database, but sometimes changes of appearance
		are necessary, so this method is available.

		@param recdef RecordDef instance

		@keyparam parents Link to parents
		@keyparam children Link to children

		@return Updated RecordDef
		"""

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "No permission to create new RecordDefs"

		recdef = emen2.db.recorddef.RecordDef(recdef, ctx=ctx)
		orec = self.bdbs.recorddefs.get(recdef.name, txn=txn) or recdef
		orec.setContext(ctx)

		##################
		# ian: todo: move to validate..

		if ctx.username != orec.owner and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only the owner or administrator can modify RecordDefs"

		# web forms might add extra spacing, causing equality to fail
		recdef.mainview = recdef.mainview.strip()
		orec.mainview = orec.mainview.strip()

		if recdef.mainview != orec.mainview and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only the administrator can modify the mainview of a RecordDef"

		# Check all params are valid
		recdef.findparams()
		self.getparamdef(recdef.params, filt=False, ctx=ctx, txn=txn)

		# reset
		recdef.creator = orec.creator
		recdef.creationtime = orec.creationtime
		recdef.uri = orec.uri

		recdef.validate()

		########## ^^^ ########

		# commit
		self._commit_recorddefs([recdef], ctx=ctx, txn=txn)

		links = []
		if parents:
			links.extend( map(lambda x:(x, recdef.name), parents) )
		if children:
			links.extend( map(lambda x:(recdef.name, x), children) )
		for link in links:
			self.pclink(link[0], link[1], keytype="recorddef", ctx=ctx, txn=txn)

		return recdef




	def _commit_recorddefs(self, recorddefs, ctx=None, txn=None):
		"""(Internal) Commit RecordDefs"""

		for recorddef in recorddefs:
			g.log.msg("LOG_COMMIT","self.bdbs.recorddefs.set: %s"%recorddef.name)
			self.bdbs.recorddefs.set(recorddef.name, recorddef, txn=txn)





	@publicmethod("recorddefs.get")
	def getrecorddef(self, keys=None, filt=True, recid=None, ctx=None, txn=None):
		"""Retrieves a RecordDef object. This will fail if the RecordDef is
		private, unless the user is an owner or	 in the context of a recid the
		user has permission to access.

		@param keys A RecordDef name, an iterable of RecordDef names, a Record ID, or list of Record IDs

		@keyparam filt Ignore failures
		@keyparam recid For private RecordDefs, provide a readable Record ID of this type to gain access

		@return A RecordDef or list of RecordDefs
		"""

		ol, keys = listops.oltolist(keys)

		recdefs = filter(lambda x:isinstance(x, basestring), keys)
		recdefs = set([i.strip().lower() for i in recdefs])

		# Find recorddefs record ID
		recs = filter(lambda x:isinstance(x, (dict, emen2.db.record.Record)), keys)
		recids = [i.get('recid') for i in recs]
		recids.extend(filter(lambda x:isinstance(x, int), keys))
		if recid != None:
			recids.append(recid)

		recs = self.getrecord(recids, ctx=ctx, txn=txn)
		groups = listops.groupbykey(recs, 'rectype')
		recdefs |= set(groups.keys()) # ian todo: process weird names.. [i.lower() for i in groups.keys()].. __process_keys(groups.keys())
		# recs = listops.dictbykey(recs, 'recid')

		# Expand * searches: (todo: implement ^ for parents as well)
		replaced = {}
		for rd in recdefs:
			if '*' in rd:
				rd = rd.replace('*', '')
				# Probably not the fastest way to do this
				replaced[rd] = self.getchildren(rd, recurse=-1, keytype="recorddef", ctx=ctx, txn=txn)

		for k,v in replaced.items():
			# Update the list of items to get with found children
			recdefs.discard(k+'*')
			recdefs.add(k)
			recdefs |= v


		# Prepare filter
		if filt:
			lfilt = self.bdbs.recorddefs.get
		else:
			lfilt = self.bdbs.recorddefs.sget

		# Ok, get the recorddefs and check if accessible
		ret = []
		recdefs = filter(None, [lfilt(i, txn=txn) for i in recdefs])
		for rd in recdefs:
			rd.setContext(ctx)
			if not rd.accessible() and rd.name not in groups:
				if filt: continue
				raise emen2.db.exceptions.SecurityError, "RecordDef %s not accessible"%(rd.name)
			ret.append(rd)


		if ol: return return_first_or_none(ret)
		return ret





	@publicmethod("recorddefs.list")
	def getrecorddefnames(self, ctx=None, txn=None):
		"""This will retrieve a list of all existing RecordDef names, even those the user cannot access

		@return set of RecordDef names

		"""
		return set(self.bdbs.recorddefs.keys(txn=txn))





	#########################
	# section: records
	#########################


	@publicmethod("records.get")
	def getrecord(self, recids, filt=True, writable=None, q=None, getrels=False, ctx=None, txn=None):
		"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.

		@param recids Record ID or iterable of Record IDs
		@keyparam filt Ignore failures
		@keyparam writable
		@keyparam owner
		@keyparam q

		@return Record or list of Records
		"""

		ol, recids = listops.oltolist(recids)
		if q:
			qr = self.query(c=q.get('c'), boolmode=q.get('boolmode'), ignorecase=q.get('ignorecase'), ctx=ctx, txn=txn)
			recids = qr['recids']
			ol = False

		ret = []
		for i in recids:
			try:
				rec = self.bdbs.records.sget(i, txn=txn)
				rec.setContext(ctx)
				ret.append(rec)
			except (emen2.db.exceptions.SecurityError, KeyError, TypeError), e:
				if filt: pass
				else: raise

		if writable:
			ret = filter(lambda x:x.writable(), ret)

		# if owner:
		# 	ret = filter(lambda x:x.isowner(), ret)


		if getrels:
			recs = [rec.recid for rec in ret]
			# this will normally filter for permissions
			parents = self.getparents(recs, ctx=ctx, txn=txn)
			children = self.getchildren(recs, ctx=ctx, txn=txn)
			for rec in ret:
				rec.parents = parents.get(rec.recid, set())
				rec.children = children.get(rec.recid, set())

		# if getrels:
		# 	cursor = self.bdbs.records.pcdb2.bdb.cursor(txn=txn)
		# 	for rec in ret:
		# 		p = self.bdbs.records.pcdb2.get(rec.recid, cursor=cursor)
		# 	cursor.close()
		# 
		# 	cursor = self.bdbs.records.cpdb2.bdb.cursor(txn=txn)
		# 	for rec in ret:
		# 		c = self.bdbs.records.cpdb2.get(rec.recid, cursor=cursor)
		# 	cursor.close()


		if ol:
			return return_first_or_none(list(ret))	
			
		return list(ret)





	@publicmethod("records.new")
	def newrecord(self, rectype, inheritperms=None, init=True, recid=None, ctx=None, txn=None):
		"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
		already exist).

		@param rectype RecordDef type

		@keyparam recid Deprecated
		@keyparam init Initialize Record with defaults from RecordDef
		@keyparam inheritperms

		@return A new Record
		"""

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "No permission to create new records"

		# Check if we can access RecordDef
		t = [ (x,y) for x,y in self.getrecorddef(rectype, filt=False, ctx=ctx, txn=txn).params.items() if y != None]

		# Create new record
		rec = emen2.db.record.Record(rectype=rectype, recid=recid, ctx=ctx)

		# Apply any default values
		#if init:
		#	rec.update(t)

		# Apply any inherited permissions
		if inheritperms != None:
			inheritperms = listops.tolist(inheritperms)
			try:
				precs = self.getrecord(inheritperms, filt=False, ctx=ctx, txn=txn)
				for prec in precs:
					rec.addumask(prec["permissions"])
					rec.addgroup(prec["groups"])

			except Exception, inst:
				g.log.msg("LOG_ERROR","Error setting inherited permissions from record %s: %s"%(inheritperms, inst))

			rec["parents"] = inheritperms

		return rec





	#@rename good question!
	def _getparamdefnamesbyvartype(self, vts, paramdefs=None, ctx=None, txn=None):
		"""(Internal) As implied, get paramdef names by vartype"""

		if not hasattr(vts,"__iter__"): vts = [vts]

		if not paramdefs:
			paramdefs = self.getparamdef(self.getparamdefnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)

		return [x.name for x in paramdefs if x.vartype in vts]






	@publicmethod("records.delete", write=True)
	def deleterecord(self, recid, ctx=None, txn=None):
		"""Unlink and hide a record; it is still accessible to owner and root. Records are never truly deleted, just hidden.

		@param recid Record ID to delete

		@return Deleted Record
		"""

		rec = self.getrecord(recid, ctx=ctx, txn=txn)
		if not (ctx.checkadmin() or rec.isowner()):
			raise emen2.db.exceptions.SecurityError, "No permission to delete record"

		parents = self.getparents(recid, ctx=ctx, txn=txn)
		children = self.getchildren(recid, ctx=ctx, txn=txn)

		if len(parents) > 0 and rec.get("deleted") != 1:
			rec["comments"] = "Record marked for deletion and unlinked from parents: %s"%", ".join([unicode(x) for x in parents])

		elif rec.get("deleted") != 1:
			rec["comments"] = "Record marked for deletion"

		rec["deleted"] = True

		self.putrecord(rec, ctx=ctx, txn=txn)

		for i in parents:
			self.pcunlink(i,recid, ctx=ctx, txn=txn)


		for i in children:
			self.pcunlink(recid, i, ctx=ctx, txn=txn)

			# ian: todo: not sure if I want to do this or not.
			# c2 = self.getchildren(i, ctx=ctx, txn=txn)
			# c2 -= set([recid])
			# if child had more than one parent, make a note one parent was removed
			# if len(c2) > 0:
			#	rec2=self.getrecord(i, ctx=ctx, txn=txn)
			#	rec["comments"]="Parent record %s was deleted"%recid
			#	self.putrecord(rec2, ctx=ctx, txn=txn)

		return rec





	@publicmethod("records.addcomment", write=True)
	def addcomment(self, recid, comment, ctx=None, txn=None):
		"""Add comment to a record. Requires comment permissions on that Record.

		@param recid
		@param comment

		@return Updated Record
		"""

		# g.log.msg("LOG_DEBUG","addcomment %s %s"%(recid, comment))
		rec = self.getrecord(recid, filt=False, ctx=ctx, txn=txn)
		rec["comments"] = comment
		self.putrecord(rec, ctx=ctx, txn=txn)

		return self.getrecord(recid, ctx=ctx, txn=txn) #["comments"]





	@publicmethod("records.find.comments")
	def getcomments(self, recids, filt=True, ctx=None, txn=None):
		"""Get comments from Records.

		@param recids A Record ID or iterable Record IDs

		@return A list of comments; the Record ID is set to the first item in each comment
		"""

		ol, recs = listops.oltolist(recids, dtype=set)
		recs = self.getrecord(recids, filt=filt, ctx=ctx, txn=txn)

		ret = []
		for rec in recs:
			cp = rec.get("comments")
			if not cp:
				continue
			cp = filter(lambda x:"LOG: " not in x[2], cp)
			cp = filter(lambda x:"Validation error: " not in x[2], cp)
			for c in cp:
				ret.append([rec.recid]+list(c))

		return sorted(ret, key=operator.itemgetter(2))





	#########################
	# section: Records / Put
	#########################


	@publicmethod("records.update", write=True)
	def putrecordvalues(self, recids, d, q=None, ctx=None, txn=None):
		"""Convenience method to update a record

		@param recids Single or iterable Record IDs
		@param d Update with this dictionary
		@keyparam q A query to use instead of recids
		@return Updated Record
		"""

		ol, recids = listops.oltolist(recids)

		recs = self.getrecord(recids, filt=False, q=q, ctx=ctx, txn=txn)
		for rec in recs:
			rec.update(d)
		self.putrecord(recs, ctx=ctx, txn=txn)

		ret = self.getrecord(recids, ctx=ctx, txn=txn) #.get(param)

		if ol: return return_first_or_none(ret)
		return ret




	@publicmethod("records.updates", write=True)
	def putrecordsvalues(self, d, ctx=None, txn=None):
		"""dict.update()-like operation on a number of records
		@param d A dict (key=recid) of dicts (key=param, value=new value)
		@return Updated Records
		"""

		recs = self.getrecord(d.keys(), filt=False, ctx=ctx, txn=txn)
		recs = listops.dictbykey(recs, 'recid')
		for k, v in d.items():
			recs[int(k)].update(v)

		return self.putrecord(recs.values(), ctx=ctx, txn=txn)





	@publicmethod("records.validate")
	def validaterecord(self, rec, ctx=None, txn=None):
		"""Check that a record will validate before committing.
		@param recs Record or iterable of Records
		@return Validated Records
		"""

		return self.putrecord(rec, commit=False, ctx=ctx, txn=txn)




	@publicmethod("records.put", write=True)
	def putrecord(self, updrecs, warning=0, commit=True, clone=False, ctx=None, txn=None):
		"""Commit records
		@param recs Record or iterable Records
		@keyparam warning Bypass validation (Admin only)
		@keyparam commit If False, do not actually commit (e.g. for valdiation)
		@return Committed records
		@exception SecurityError, DBError, KeyError, ValueError, TypeError..
		"""

		ol, updrecs = listops.oltolist(updrecs)

		if (warning or clone) and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators may bypass validation or clone/import records"

		# Assign all changes the same time
		t = self.gettime(ctx=ctx, txn=txn)
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)

		# Process inputs (records, dicts..) into Records
		updrecs.extend(emen2.db.record.Record(x, ctx=ctx) for x in listops.typefilter(updrecs, dict))
		updrecs = listops.typefilter(updrecs, emen2.db.record.Record)

		# Process records for committing. If anything is wrong, raise an Exception, which will cancel the
		#	operation and usually the txn. If OK, then proceed to write records and all indexes. At that point, only
		#	really serious DB errors should ever occur.
		crecs = []
		cps = {}
		updrels = []

		# Assign temp recids to new records (note: you can assign your own negative pre-commit IDs)
		for offset,updrec in enumerate(x for x in updrecs if x.recid == None):
			updrec.recid = -1 * (offset + 100)


		# Preprocess: copy updated record into original record (updrec -> orec) and validate
		for updrec in updrecs:
			recid = updrec.recid			
			if updrec.parents:
				updrels.extend([(i, updrec.recid) for i in updrec.get("parents", [])])
			if updrec.children:
				updrels.extend([(updrec.recid, i) for i in updrec.get("children", [])])

			if recid < 0:
				orec = self.newrecord(updrec.rectype, recid=updrec.recid, ctx=ctx, txn=txn)
			else:
				# we need to acquire RMW lock here to prevent changes during commit
				try:
					orec = self.bdbs.records.sget(updrec.recid, txn=txn, flags=bsddb3.db.DB_RMW)
					orec.setContext(ctx)
				except:
					raise KeyError, "Cannot update non-existent record %s"%recid

			# Update and validate.
			cp = orec.validate(updrec, warning=warning, clone=clone, vtm=vtm, t=t)
			if cp:
				cps[orec.recid] = cp
				crecs.append(orec)				


		ret = self._commit_records(crecs, cps=cps, updrels=updrels, commit=commit, ctx=ctx, txn=txn)
		if ol:
			return return_first_or_none(ret)
			
		return ret




	# commit
	def _commit_records(self, crecs, cps=None, updrels=[], reindex=False, commit=True, ctx=None, txn=None):
		"""(Internal) Actually commit Records... This is the last step of several in the process.
		commit=False aborts before writing begins but after all updates are calculated"""

		cps = cps or {}
		recmap = {}
		newrecs = [x for x in crecs if x.recid < 0]

		# Fetch the old records for calculating index updates. Set RMW flags.
		# If reindex==True, force reindexing (e.g. to rebuild indexes) by treating as new record
		cache = {}
		for i in crecs:
			if reindex or i.recid < 0:
				orec = {}
			else:
				# Cannot update non-existent record
				orec = self.bdbs.records.sget(i.recid, txn=txn, flags=bsddb3.db.DB_RMW)
			cache[i.recid] = orec


		# Calculate index updates.
		indexupdates = self._reindex_params(crecs, cps=cps, cache=cache, ctx=ctx, txn=txn)

		# If we're just validating, exit here, before any changes are written..
		if not commit:
			return crecs

		# OK, all go to write records/indexes!

		# Reassign new record IDs and update record counter
		if newrecs:
			baserecid = self.bdbs.records.get_sequence(delta=len(newrecs), txn=txn)
			g.log.msg("LOG_DEBUG","Setting recid counter: %s -> %s"%(baserecid, baserecid + len(newrecs)))


		# Add recids to new records, create map from temp recid to real recid
		for offset, newrec in enumerate(newrecs):
			oldid = newrec.recid
			newrec.recid = offset + baserecid
			recmap[oldid] = newrec.recid


		# This actually stores the record in the database
		# If we're just reindexing, no need to waste time/log space writing records.
		if not reindex:
			for crec in crecs:
				g.log.msg("LOG_COMMIT","self.bdbs.records.set: %s"%crec.recid)
				self.bdbs.records.set(crec.recid, crec, txn=txn)


		# Write param index updates
		for param, (addrefs, delrefs) in indexupdates.items():
			self._commit_paramindex(param, addrefs, delrefs, recmap=recmap, ctx=ctx, txn=txn)


		# Create parent/child links
		for parent,child in updrels:
			try:
				self.pclink(recmap.get(parent,parent), recmap.get(child,child), ctx=ctx, txn=txn)
			except Exception, inst:
				# msg = "Could not link %s to %s: %s"%( recmap.get(parent,parent), recmap.get(child,child), inst)
				msg = "Critical! self.bdbs.records.pclink %s -> %s failed: %s"%(recmap.get(parent,parent), recmap.get(child,child), inst)
				g.log.msg("LOG_CRITICAL", msg)
				raise ValueError, msg

		g.log.msg("LOG_INFO", "Committed %s records"%(len(crecs)))

		return crecs



	# These methods calculate what index updates to make

	# ian: todo: merge all the __reindex_params together...
	def _reindex_params(self, updrecs, cps=None, cache=None, ctx=None, txn=None):
		"""(Internal) update param indices"""

		# g.log.msg('LOG_DEBUG', "Calculating param index updates...")
		cps = cps or {} # cached list of recid:changed parameters
		cache = cache or {} # cached records
		ind = collections.defaultdict(list)
		indexupdates = {}

		# Rearrange to param:(values)
		for updrec in updrecs:
			orec = cache.get(updrec.recid, {})
			for param in cps.get(updrec.recid, updrec.changedparams(orec)):
				ind[param].append((updrec.recid, updrec.get(param), orec.get(param)))

		# Now update indices; filter because most param indexes have no changes
		for key, v in ind.items():
			if not v:
				continue
			pd = self.bdbs.paramdefs.sget(key, txn=txn)
			vt = self.vtm.getvartype(pd.vartype)
			if not vt.keytype or not pd.indexed:
				continue

			indexupdates[key] = vt.reindex(v)

		return indexupdates



	# The following methods write to the various indexes
	def _commit_paramindex(self, param, addrefs, delrefs, recmap=None, ctx=None, txn=None):
		"""(Internal) commit param updates"""

		recmap = recmap or {}
		addindexkeys = []
		delindexkeys = []

		if not addrefs and not delrefs:
			return

		try:
			ind = self._getindex(param, ctx=ctx, txn=txn)
			if ind == None:
				raise Exception, "Index was None; unindexable?"
		except Exception, inst:
			g.log.msg("LOG_CRITICAL","Critical! Could not open self.bdbs.fieldindex[%s]: %s"% (param, inst))
			raise


		# delrefs comes first, so I don't have to check for common items
		for oldval,recs in delrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				if recs:
					g.log.msg("LOG_INDEX","self.bdbs.fieldindex[%s].removerefs: %r -> ... %s items"%(param, oldval, len(recs)))
					delindexkeys.extend(ind.removerefs(oldval, recs, txn=txn))
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Critical! self.bdbs.fieldindex[%s].removerefs %s failed: %s"%(param, oldval, inst))
				raise


		for newval,recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				if recs:
					g.log.msg("LOG_INDEX","self.bdbs.fieldindex[%s].addrefs: %r -> ... %s items"%(param, newval, len(recs)))
					addindexkeys.extend(ind.addrefs(newval, recs, txn=txn))
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Critical! self.bdbs.fieldindex[%s].addrefs %s failed: %s"%(param, newval, inst))
				raise


		# Update index-index, a necessary evil..
		if delindexkeys:
			#g.log.msg("LOG_INDEX","self.bdbs.indexkeys.removerefs: %s -> %s"%(param, delindexkeys))
			self.bdbs.indexkeys.removerefs(param, delindexkeys, txn=txn)
		if addindexkeys:
			#g.log.msg("LOG_INDEX","self.bdbs.indexkeys.addrefs: %s -> %s"%(param, addindexkeys))
			self.bdbs.indexkeys.addrefs(param, addindexkeys, txn=txn)





	# If the indexes blow up...

	# Stage 1
	def _rebuild_all(self, ctx=None, txn=None):
		"""(Internal) Rebuild all indexes. This should only be used if you blow something up, change a paramdef vartype, etc.
		It might test the limits of your Berkeley DB configuration and fail if the resources are too low."""

		g.log.msg("LOG_INFO","Rebuilding ALL indexes!")

		allparams = self.bdbs.paramdefs.keys()
		paramindexes = {}
		for param in allparams:
			paramindex = self._getindex(param, ctx=ctx, txn=txn)
			if paramindex != None:
				# g.log.msg('LOG_DEBUG', paramindex)
				try:
					g.log.msg("LOG_INDEX","self.bdbs.fieldindex[%s].truncate"%param)
					paramindex.truncate(txn=txn)
				except Exception, e:
					g.log.msg("LOG_INFO","Critical! self.bdbs.fieldindex[%s].truncate failed: %s"%(param, e))
				paramindexes[param] = paramindex


		g.log.msg("LOG_INFO","Done truncating all indexes")

		self._rebuild_groupsbyuser(ctx=ctx, txn=txn)
		self._rebuild_usersbyemail(ctx=ctx, txn=txn)

		maxrecords = self.bdbs.records.get_max(txn=txn) #get(-1, txn=txn)["max"]
		g.log.msg('LOG_INFO',"Rebuilding indexes for %s records..."%(maxrecords-1))

		blocks = range(0, maxrecords, g.BLOCKLENGTH) + [maxrecords]
		blocks = zip(blocks, blocks[1:])


		for pos, pos2 in blocks:
			g.log.msg("LOG_INFO","Reindexing records %s -> %s"%(pos, pos2))
			#txn2 = self.newtxn(txn)
			crecs = []
			for i in range(pos, pos2):
				g.log.msg("LOG_INFO","... %s"%i)
				crecs.append(self.bdbs.records.sget(i, txn=txn))

			self._commit_records(crecs, reindex=True, ctx=ctx, txn=txn)

			#txn2.commit()

		g.log.msg("LOG_INFO","Done rebuilding all indexes!")





	###############################
	# section: Record Permissions View / Modify
	###############################

	# this has gone internal, since it is almost always enforced
	def _filterbypermissions(self, recids, ctx=None, txn=None):
		"""Filter a list of Record IDs by read permissions.
		@param recids Iterable of Record IDs
		@return Set of accessible Record IDs
		"""

		if ctx.checkreadadmin():
			return set(recids)

		ol, recids = listops.oltolist(recids, dtype=set)

		# ian: indexes are now faster, generally...
		if len(recids) < 100:
			return set([x.recid for x in self.getrecord(recids, filt=True, getrels=False, ctx=ctx, txn=txn)])

		ind = self._getindex("permissions", ctx=ctx, txn=txn)
		indg = self._getindex("groups", ctx=ctx, txn=txn)

		find = copy.copy(recids)
		find -= ind.get(ctx.username, set(), txn=txn)

		for group in sorted(ctx.groups):
			if find:
				find -= indg.get(group, set(), txn=txn)

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



	@publicmethod("records.permissions.compat", write=True)
	def secrecordadduser_compat(self, umask, recid, recurse=0, reassign=False, delusers=None, addgroups=None, delgroups=None, overwrite_users=None, overwrite_groups=None, ctx=None, txn=None):
		"""Legacy permissions method.
		@param umask Add this user mask to the specified recid, and child records to recurse level
		@param recid Record ID to modify
		@keyparam recurse
		@keyparam reassign
		@keyparam delusers
		@keyparam addgroups
		@keyparam delgroups
		"""
		return self._putrecord_setsecurity(recids=[recid], umask=umask, addgroups=addgroups, recurse=recurse, reassign=reassign, delusers=delusers, delgroups=delgroups, overwrite_users=overwrite_users, overwrite_groups=overwrite_groups, ctx=ctx, txn=txn)




	@publicmethod("records.permissions.addusers", write=True)
	def addpermissions(self, recids, users, level=0, recurse=0, reassign=False, ctx=None, txn=None):
		return self._putrecord_setsecurity(recids=recids, addusers=users, addlevel=level, recurse=recurse, reassign=reassign, ctx=ctx, txn=txn)




	@publicmethod("records.permissions.removeusers", write=True)
	def removepermissions(self, recids, users, recurse=0, ctx=None, txn=None):
		return self._putrecord_setsecurity(recids=recids, delusers=users, recurse=recurse, ctx=ctx, txn=txn)




	@publicmethod("records.permissions.addgroups", write=True)
	def addgroups(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self._putrecord_setsecurity(recids=recids, addgroups=groups, recurse=recurse, ctx=ctx, txn=txn)




	@publicmethod("records.permissions.removegroups", write=True)
	def removegroups(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self._putrecord_setsecurity(recids=recids, delgroups=groups, recurse=recurse, ctx=ctx, txn=txn)




	def _putrecord_setsecurity(self, recids=None, addusers=None, addlevel=0, addgroups=None, delusers=None, delgroups=None, umask=None, overwrite_users=None, overwrite_groups=None, recurse=0, reassign=False, filt=True, ctx=None, txn=None):

		if recurse == -1:
			recurse = g.MAXRECURSE

		# make iterables
		if recids == None:
			recids = set()
		recids = listops.tolist(recids, dtype=set)
		addusers = listops.tolist(addusers or set(), dtype=set)
		addgroups = listops.tolist(addgroups or set(), dtype=set)
		delusers = listops.tolist(delusers or set(), dtype=set)
		delgroups = listops.tolist(delgroups or set(), dtype=set)

		if not umask:
			umask = [[],[],[],[]]
			if addusers:
				umask[addlevel] = addusers

		# Check that all specified users/groups exist
		addusers = set()
		for i in umask:
			addusers |= set(i)

		checkitems = set()
		checkitems |= addusers
		checkitems |= addgroups

		found = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)
		if checkitems - found:
			raise emen2.db.exceptions.SecurityError, "Invalid users/groups: %s"%(checkitems - found)


		# Change child perms
		if recurse:
			recids |= listops.flatten(self.getchildtree(recids, recurse=recurse, ctx=ctx, txn=txn))

		recs = self.getrecord(recids, filt=filt, ctx=ctx, txn=txn)
		if filt:
			recs = filter(lambda x:x.isowner(), recs)


		# This is becoming slightly more complicated to avoid unnecessary writes and allow overwriting.
		cps = {}
		crecs = []
		for crec in recs:
			cps[crec.recid] = set()
			op = copy.copy(crec['permissions'])
			og = copy.copy(crec['groups'])

			# If we are overwriting users or groups, replace
			if overwrite_users or overwrite_groups:
				if overwrite_users: crec['permissions'] = umask
				if overwrite_groups: crec['groups'] = addgroups

			# ... or update.
			else:
				if addusers:
					crec.addumask(umask, reassign=reassign)
				if delusers:
					crec.removeuser(delusers)
				if addgroups:
					crec.addgroup(addgroups)
				if delgroups:
					crec.removegroup(delgroups)

			if crec['permissions'] != op:
				cps[crec.recid].add('permissions')
			if crec['groups'] != og:
				cps[crec.recid].add('groups')

			if cps[crec.recid]:
				crecs.append(crec)

		# Go ahead and directly commit here, since we know only permissions have changed...
		ret = self._commit_records(crecs, cps=cps, ctx=ctx, txn=txn)




	#############################
	# section: Rendering Record Views
	#############################


	def _endpoints(self, tree):
		return set(filter(lambda x:len(tree.get(x,()))==0, set().union(*tree.values())))


	#@remove?
	@publicmethod("records.renderchildtree")
	def renderchildtree(self, recid, recurse=3, rectypes=None, treedef=None, ctx=None, txn=None):
		"""Convenience method used by some clients to render a bunch of records and simple relationships"""

		# There is a definite issue here with performance and recurse > 3...

		c_all = self.getchildtree(recid, recurse=recurse, ctx=ctx, txn=txn)
		c_rectype = self.getchildren(recid, recurse=recurse, rectype=rectypes, ctx=ctx, txn=txn)

		endpoints = self._endpoints(c_all) - c_rectype
		while endpoints:
			for k,v in c_all.items():
				c_all[k] -= endpoints
			endpoints = self._endpoints(c_all) - c_rectype

		rendered = self.renderview(listops.flatten(c_all), ctx=ctx, txn=txn)

		c_all = self._filter_dict_zero(c_all)

		return rendered, c_all




	def _dicttable_view(self, params, paramdefs={}, markup=False, ctx=None, txn=None):
		"""generate html table of params"""

		if markup:
			dt = ['<table cellspacing="0" cellpadding="0">\n\t<thead><th>Parameter</th><th>Value</th></thead>\n\t<tbody>']
			for count, i in enumerate(params):
				if count%2:
					dt.append("\t\t<tr class=\"s\"><td>$#%s</td><td>$$%s</td></tr>"%(i,i))
				else:
					dt.append("\t\t<tr><td>$#%s</td><td>$$%s</td></tr>"%(i,i))

			dt.append("\t<thead>\n</table>")

		else:
			dt = []
			for i in params:
				dt.append("$#%s:\t$$%s\n"%(i,i))

		return "\n".join(dt)





	@publicmethod("records.render")
	def renderview(self, recs, viewdef=None, viewtype='recname', edit=False, markup=False, table=False, mode=None, ctx=None, txn=None):
		"""Render views"""
		
		regex = re.compile(VIEW_REGEX)
		ol, recs = listops.oltolist(recs)

		if viewtype == "tabularview":
			table = True

		if table:
			edit = "auto"
		
		if table or edit:
			markup = True


		# Calling out to vtm, we will need a DBProxy
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)

		# We'll be working with a list of recs
		recs = self.getrecord(listops.typefilter(recs, int), ctx=ctx, txn=txn) + listops.typefilter(recs, emen2.db.record.Record)

		# Default params
		builtinparams = set(["recid","rectype","comments","creator","creationtime","permissions", "history", "groups"])
		builtinparamsshow = builtinparams - set(["permissions", "comments", "history", "groups"])

		# Get and pre-process views
		groupviews = {}
		recdefs = listops.dictbykey(self.getrecorddef(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

		if viewdef:
			groupviews[None] = viewdef


		elif viewtype == "dicttable":
			for rec in recs:
				# move built in params to end of table
				par = [p for p in set(recdefs.get(rec.rectype).paramsK) if p not in builtinparams]
				par += builtinparamsshow
				par += [p for p in rec.getparamkeys() if p not in par]
				groupviews[rec.recid] = self._dicttable_view(par, markup=markup, ctx=ctx, txn=txn)


		else:
			for rd in recdefs.values():
				rd["views"]["mainview"] = rd.mainview

				if viewtype in ["tabularview","recname"]:
					v = rd.views.get(viewtype, rd.name)

				else:
					v = rd.views.get(viewtype, rd.mainview)
					if markdown:
						v = markdown.markdown(v)

				groupviews[rd.name] = v


		# Pre-process once to get paramdefs
		pds = set()
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				if match.group('type') in ["#", "$", '*']:
					pds.add(match.group('name'))

				elif match.group('type') == '@':
					t = time.time()
					vtm.macro_preprocess(match.group('name'), match.group('args'), recs)


		pds = listops.dictbykey(self.getparamdef(pds, ctx=ctx, txn=txn), 'name')

		# Parse views and build header row..
		matches = collections.defaultdict(list)
		headers = collections.defaultdict(list)
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				matches[group].append(match)

				# ian: temp fix.
				n = match.group('name')
				h = pds.get(match.group('name'),dict()).get('desc_short')
				if match.group('type') == '@':
					if n == "childcount":
						n = "#"
					h = '%s %s'%(n, match.group('args') or '')

				headers[group].append([h, match.group('type'), match.group('name'), match.group('args')])


		# Process records
		ret = {}
		pt = collections.defaultdict(list)
		mt = collections.defaultdict(list)
		
		for rec in recs:
			key = rec.rectype
			if viewdef:
				key = None
			elif viewtype == "dicttable":
				key = rec.recid

			_edit = edit
			if edit == "auto":
				_edit = rec.writable()
			
			a = groupviews.get(key)
			vs = []

			for match in matches.get(key, []):
				t = match.group('type')
				n = match.group('name')
				s = match.group('sep') or ''
				if t == '#':
					v = vtm.name_render(pds[n])
				elif t == '$' or t == '*':
					t = time.time()
					v = vtm.param_render(pds[n], rec.get(n), recid=rec.recid, edit=_edit, markup=markup, table=table)
					pt[n].append(time.time()-t)
				elif t == '@':
					t = time.time()
					v = vtm.macro_render(n, match.group('args'), rec, markup=markup, table=table)
					mt[n].append(time.time()-t)
				else:
					continue

				if table:
					vs.append(v)
				else:
					a = a.replace(match.group(), v+s)

			if table:
				ret[rec.recid] = vs
			else:
				ret[rec.recid] = a


		def pp(t, times):
			for k,v in times.items():
				p = (sum(v), sum(v)/float(len(v)), min(v), max(v))
				p = [t[:5].ljust(5), k[:20].ljust(20)] + [("%2.2f"%i).rjust(5) for i in p] + [str(len(v)).rjust(5)]
				print "   ".join(p)
		# header = ["Type ", "Name".ljust(20), "Total", "  Avg", "  Min", "  Max", "Count"]
		# print "   ".join(header)
		# pp("param", pt)
		# pp("macro", mt)
		
		
		if table:
			ret["headers"] = headers

		if ol: return return_first_or_none(ret)
		return ret






	###########################
	# section: backup / restore
	###########################



	def get_dbpath(self, tail):
		return os.path.join(self.path, tail)


	def checkpoint(self, ctx=None, txn=None):
		return self.dbenv.txn_checkpoint()



	#@rename db.admin.log_archive
	def log_archive(self, remove=True, checkpoint=False, outpath=None, ctx=None, txn=None):

		outpath = outpath or g.paths.LOG_ARCHIVE

		if checkpoint:
			g.log.msg('LOG_INFO', "Log Archive: Checkpoint")
			self.dbenv.txn_checkpoint()

		archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

		g.log.msg('LOG_INFO', "Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

		if not os.access(outpath, os.F_OK):
			os.makedirs(outpath)

		self._log_archive(archivefiles, outpath, remove=remove)



	def _log_archive(self, archivefiles, outpath, remove=False):

		outpaths = []
		for archivefile in archivefiles:
			dest = os.path.join(outpath, os.path.basename(archivefile))
			g.log.msg('LOG_INFO','Log Archive: %s -> %s'%(archivefile, dest))
			shutil.copy(archivefile, dest)
			outpaths.append(dest)

		if not remove:
			return outpaths

		removefiles = []

		# ian: check if all files are in the archive before we remove any
		for archivefile in archivefiles:
			if not os.path.exists(outpath):
				raise ValueError, "Log Archive: %s not found in backup archive!"%(archivefile)
			removefiles.append(archivefile)


		for removefile in removefiles:
			g.log.msg('LOG_INFO','Log Archive: Removing %s'%(removefile))
			os.unlink(removefile)

		return removefiles


	# ian: todo: finish
	# def coldbackup(self, force=False, ctx=None, txn=None):
	# 	g.log.msg('LOG_INFO', "Cold Backup: Checkpoint")
	#
	# 	self.checkpoint(ctx=ctx, txn=txn)
	#
	# 	if os.path.exists(g.paths.BACKUPPATH):
	# 		if force:
	# 			pass
	# 		else:
	# 			raise ValueError, "Directory %s exists -- remove before starting a new cold backup"%g.paths.BACKUPPATH
	#
	# 	# ian: just use shutil.copytree
	# 	g.log.msg('LOG_INFO',"Cold Backup: Copying data: %s -> %s"%(os.path.join(g.EMEN2DBHOME, "data"), os.path.join(g.paths.BACKUPPATH, "data")))
	# 	shutil.copytree(os.path.join(g.EMEN2DBHOME, "data"), os.path.join(g.paths.BACKUPPATH, "data"))
	#
	# 	for i in ["config.yml","DB_CONFIG"]:
	# 		g.log.msg('LOG_INFO',"Cold Backup: Copying config: %s -> %s"%(os.path.join(g.EMEN2DBHOME, i), os.path.join(g.paths.BACKUPPATH, i)))
	# 		shutil.copy(os.path.join(g.EMEN2DBHOME, i), os.path.join(g.paths.BACKUPPATH, i))
	#
	# 	os.makedirs(os.path.join(g.paths.BACKUPPATH, "log"))
	#
	# 	# Get the last log file
	# 	archivelogs = self.dbenv.log_archive(bsddb3.db.DB_ARCH_LOG)[-1:]
	#
	# 	for i in archivelogs:
	# 		g.log.msg('LOG_INFO',"Cold Backup: Copying log: %s -> %s"%(os.path.join(g.EMEN2DBHOME, "log", i), os.path.join(g.paths.BACKUPPATH, "log", i)))
	# 		shutil.copy(os.path.join(g.EMEN2DBHOME, "log", i), os.path.join(g.paths.BACKUPPATH, "log", i))
	#
	#
	#
	# def hotbackup(self, ctx=None, txn=None):
	# 	g.log.msg('LOG_INFO', "Hot Backup: Checkpoint")
	# 	self.checkpoint(ctx=ctx, txn=txn)
	#
	# 	g.log.msg('LOG_INFO', "Hot Backup: Log Archive")
	# 	self.archivelogs(remove=True, outpath=g.paths.ARCHIVEPATH, ctx=ctx, txn=txn)
	#
	# 	g.log.msg('LOG_INFO', "Hot Backup: You will want to run 'db_recover -c' on the hot backup directory")


__version__ = "$Revision$".split(":")[1][:-1].strip()
