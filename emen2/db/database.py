# $Author$ $Revision$
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
import bsddb3
import re
import shutil
import weakref
import getpass
import functools
import imp
import tempfile

import emen2.ext.mail_exts

import emen2.db.config
g = emen2.db.config.g()

try:
	import matplotlib.backends.backend_agg
	import matplotlib.figure
except ImportError:
	matplotlib = None
	g.log("No matplotlib; plotting will fail")


try:
	import markdown
except ImportError:
	markdown = None


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

import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group
import emen2.db.workflow
from emen2.util import listops
import emen2.util.decorators

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




# Colors to use in plot..
COLORS = ['#0000ff', '#00ff00', '#ff0000', '#800000', '#000080', '#808000',
	'#800080', '#c0c0c0', '#008080', '#7cfc00', '#cd5c5c', '#ff69b4', '#deb887',
	'#a52a2a', '#5f9ea0', '#6495ed', '#b8890b', '#8b008b', '#f08080', '#f0e68c',
	'#add8e6', '#ffe4c4', '#deb887', '#d08b8b', '#bdb76b', '#556b2f', '#ff8c00',
	'#8b0000', '#8fbc8f', '#ff1493', '#696969', '#b22222', '#daa520', '#9932cc',
	'#e9967a', '#00bfff', '#1e90ff', '#ffd700', '#adff2f', '#00ffff', '#ff00ff',
	'#808080']



# import extensions

# ian: todo: low: do this in a better way
# this is used by db.checkversion
# import this directly from emen2client, emdash
import emen2.clients.emen2client
VERSIONS = {
	"API": g.VERSION,
	"emen2client": emen2.clients.emen2client.VERSION
}


VIEW_REGEX = '\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?'


# pointer to database environment
DBENV = None


#basestring goes away in a later python version
basestring = (str, unicode)


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
def DB_Close():
	"""Close all open DBs"""
	l = DB.opendbs.keys()
	for i in l:
		# g.log.msg('LOG_DEBUG', i.dbenv)
		i.close()



def DB_stat():
	"""Print some statistics about the global DBEnv"""
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




# ian: todo: make these express GMT, then have display interfaces localize to time zone...
def getctime():
	return time.time()



def gettime():
	"""Return database local time in format %s"""%g.TIMESTR
	return time.strftime(g.TIMESTR)




# Wrapper methods for public API and admin API methods
def publicmethod(func):
	"""Decorator for public API database method"""
	emen2.db.proxy.DBProxy._register_publicmethod(func.func_name, func)
	return func



def adminmethod(func):
	"""Decorator for public admin API database method"""

	if not func.func_name.startswith('_'):
		emen2.db.proxy.DBProxy._register_adminmethod(func.func_name, func)

	@functools.wraps(func)
	def _inner(*args, **kwargs):
		ctx = kwargs.get('ctx')
		if ctx is None:
			ctx = [x for x in args is isinstance(x, emen2.db.user.User)] or None
			if ctx is not None: ctx = ctx.pop()
		if ctx.checkadmin():
			return func(*args, **kwargs)
		else:
			raise emen2.db.exceptions.SecurityError, 'No Admin Priviliges'

	return _inner






class DB(object):
	"""Main database class"""
	opendbs = weakref.WeakKeyDictionary()

	# ian: todo: have DBEnv and all BDBs in here -- DB should just be methods for dealing with this dbenv "core"
	@emen2.util.decorators.instonget
	class bdbs(object):
		"""Private class that actually stores the bdbs"""

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
			self.records = emen2.db.btrees.RelateBTree(filename="main/records", keytype="d_old", cfunc=False, sequence=True, dbenv=dbenv, txn=txn)


			# Indices
			self.secrindex = emen2.db.btrees.FieldBTree(filename="index/security/secrindex", datatype="d", dbenv=dbenv, txn=txn)
			self.secrindex_groups = emen2.db.btrees.FieldBTree(filename="index/security/secrindex_groups", datatype="d", dbenv=dbenv, txn=txn)
			self.groupsbyuser = emen2.db.btrees.FieldBTree(filename="index/security/groupsbyuser", datatype="s", dbenv=dbenv, txn=txn)
			self.usersbyemail = emen2.db.btrees.FieldBTree(filename="index/security/usersbyemail", datatype="s", dbenv=dbenv, txn=txn)
			self.recorddefindex = emen2.db.btrees.FieldBTree(filename="index/records/recorddefindex", datatype="d", dbenv=dbenv, txn=txn)
			self.bdosbyfilename = emen2.db.btrees.FieldBTree(filename="index/bdosbyfilename", keytype="s", datatype="s", dbenv=dbenv, txn=txn)
			self.indexkeys = emen2.db.btrees.FieldBTree(filename="index/indexkeys", dbenv=dbenv, txn=txn)


			self.bdbs = set(self.__dict__) - old
			self.contexts_cache = {}
			self.fieldindex = {}
			self.__db = db


		def openparamindex(self, paramname, keytype="s", datatype="d", dbenv=None, txn=None):
			"""Parameter values are indexed with 1 db file per param, stored in index/params/*.bdb.
			Key is param value, values are list of recids, stored using duplicate method.
			The opened param will be available in self.fieldindex[paramname] after open.

			@param paramname Param index to open
			@keyparam keytype Open index with this keytype (from core_vartypes.<vartype>.__indextype__)
			@keyparam datatype Open with datatype; will always be 'd'
			@keyparam dbenv A DBEnv instance must be passed
			"""

			filename = "index/params/%s"%(paramname)

			deltxn=False
			if txn == None:
				txn = self.__db.newtxn()
				deltxn = True
			try:
				self.fieldindex[paramname] = emen2.db.btrees.FieldBTree(keytype=keytype, datatype=datatype, filename=filename, dbenv=dbenv, txn=txn)
			except BaseException, e:
				# g.debug('openparamindex failed: %s' % e)
				if deltxn: self.__db.txnabort(txn=txn)
				raise
			else:
				if deltxn: self.__db.txncommit(txn=txn)



		def closeparamindex(self, paramname):
			"""Close a paramdef
			@param paramname Param index to close
			"""
			self.fieldindex.pop(paramname).close()


		def closeparamindexes(self):
			"""Close all paramdef indexes"""
			[self.__closeparamindex(x) for x in self.fieldindex.keys()]


	#@staticmethod
	def __init_vtm(self):
		"""Load vartypes, properties, and macros"""
		vtm = emen2.db.datatypes.VartypeManager()

		self.indexablevartypes = set()
		for y in vtm.getvartypes():
			y = vtm.getvartype(y)
			if y.getindextype():
				self.indexablevartypes.add(y.getvartype())

		self.__cache_vartype_indextype = {}
		for vt in vtm.getvartypes():
			self.__cache_vartype_indextype[vt] = vtm.getvartype(vt).getindextype()

		return vtm

	def __init_dbenv(self):
		global DBENV

		if DBENV == None:
			g.log.msg("LOG_INFO","Opening Database Environment: %s"%self.path)
			DBENV = bsddb3.db.DBEnv()
			DBENV.open(self.path, g.ENVOPENFLAGS)
			DB.opendbs[self] = 1
		return DBENV


	def __checkdirs(self):
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
			infile = emen2.db.config.get_filename('emen2', 'doc/examples/DB_CONFIG.sample')
			g.log.msg("LOG_INIT","Installing default DB_CONFIG file: %s"%configpath)
			shutil.copy(infile, configpath)


	def __init__(self, path=None, bdbopen=True):
		"""Init DB
		@keyparam path Path to DB (default=cwd)
		@keyparam bdbopen Open databases in addition to DBEnv (default=True)
		"""

		self.path = path or g.EMEN2DBHOME
		if not self.path:
			raise ValueError, "No path specified; check $EMEN2DBHOME and config.json files"

		self.lastctxclean = time.time()
		self.opentime = gettime()
		self.txnid = 0
		self.txnlog = {}

		# Check that all the needed directories exist
		self.__checkdirs()

		# VartypeManager handles registration of vartypes and properties, and also validation
		self.vtm = self.__init_vtm()


		# Open DB environment; check if global DBEnv has been opened yet
		self.dbenv = self.__init_dbenv()

		# If we are just doing backups or maintenance, don't open any BDB handles
		if not bdbopen: return

		# Open Database
		txn = self.newtxn()
		try: self.bdbs.init(self, self.dbenv, txn=txn)
		except Exception, inst:
			self.txnabort(txn=txn)
			raise
		else: self.txncommit(txn=txn)

		# Check if this is a valid db..
		txn = self.newtxn()
		try:
			maxr = self.bdbs.records.get_max(txn=txn)
			g.log.msg("LOG_INFO","Opened database with %s records"%maxr)
		except Exception, e:
			g.log.msg('LOG_INFO',"Could not open database! %s"%e)
			self.txnabort(txn=txn)
			raise
		else: self.txncommit(txn=txn)



	def __del__(self):
		g.log_info('cleaning up DB instance')



	def create_db(self, rootpw=None, ctx=None, txn=None):
		"""Creates a skeleton database; imports users/params/protocols/etc. from emen2/skeleton/core_*
		This is usually called from the setup.py script to create initial db env"""

		# typically uses SpecialRootContext
		from emen2 import skeleton

		ctx = self.__makerootcontext(txn=txn, host="localhost")

		try:
			testroot = self.getuser("root", filt=False, ctx=ctx, txn=txn)
			raise ValueError, "Found root user. This environment has already been initialized."
		except KeyError:
			pass


		for i in skeleton.core_paramdefs.items:
			self.putparamdef(i, ctx=ctx, txn=txn)
		for k,v in skeleton.core_paramdefs.children.items():
			for v2 in v:
				self.pclink(k, v2, keytype="paramdef", ctx=ctx, txn=txn)


		for i in skeleton.core_recorddefs.items:
			self.putrecorddef(i, ctx=ctx, txn=txn)

		for k,v in skeleton.core_recorddefs.children.items():
			for v2 in v:
				self.pclink(k, v2, keytype="recorddef", ctx=ctx, txn=txn)

		rootrec = self.newrecord('folder', ctx=ctx, txn=txn)
		rootrec["name_folder"] = "Root Record"
		self.putrecord(rootrec, ctx=ctx, txn=txn)

		for i in skeleton.core_users.items:
			if i.get('username') == 'root':
				i['password'] = rootpw
			self.adduser(i, ctx=ctx, txn=txn)


		for i in skeleton.core_groups.items:
			self.putgroup(i, ctx=ctx, txn=txn)


		for i in skeleton.core_records.items:
			self.putrecord(i, ctx=ctx, txn=txn)

		self.addgroups(0, ['authenticated'], ctx=ctx, txn=txn)

	# #@rename db.test.sleep
	# @publicmethod
	# def sleep(self, t=1, ctx=None, txn=None):
	# 	time.sleep(t)


	# #@rename db.test.exception
	# @publicmethod
	# def raise_exception(self, ctx=None, txn=None):
	# 	raise Exception, "Test! ctxid %s host %s txn %s"%(ctx.ctxid, ctx.host, txn)


	# ian: todo: simple: print more statistics; needs a txn?
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


	# ian: todo: there is a better version in emen2.util.listops
	def __flatten(self, l):
		"""Flatten an iterable of iterables recursively into a single list"""

		out = []
		for item in l:
			if hasattr(item, '__iter__'): out.extend(self.__flatten(item))
			else:
				out.append(item)
		return out



	###############################
	# section: Transaction Management
	###############################

	txncounter = 0

	def newtxn(self, parent=None, ctx=None, flags=None, snapshot=True):
		"""Start a new transaction.
		@keyparam parent Parent txn
		@return New txn
		"""
		
		if flags == None:
			flags = g.TXNFLAGS

		# print "New txn flags are: %s"%flags

		txn = self.dbenv.txn_begin(parent=parent, flags=flags)
		#print "\n\nNEW TXN --> %s"%txn

		try:
			type(self).txncounter += 1
			self.txnlog[id(txn)] = txn
		except:
			self.txnabort(ctx=ctx, txn=txn)
			raise

		return txn



	def txncheck(self, txnid=0, flags=None, ctx=None, txn=None):
		"""Check a txn status; accepts txnid or txn instance
		@return txn if valid
		"""

		txn = self.txnlog.get(txnid, txn)
		if not txn:
			txn = self.newtxn(ctx=ctx, flags=flags)
		return txn



	def txnabort(self, txnid=0, ctx=None, txn=None):
		"""Abort txn; accepts txnid or txn instance"""

		txn = self.txnlog.get(txnid, txn)
		#g.log.msg('LOG_TXN', "TXN ABORT --> %s"%txn)
		#g.log.print_traceback(steps=5)

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
		#g.log.msg("LOG_TXN","TXN COMMIT --> %s"%txn)
		#g.log.print_traceback(steps=5)

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

	#@rename db.versions.get @ok @return int
	@publicmethod
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program

		@keyparam program Check version for this program (API, emen2client, etc.)

		"""
		return VERSIONS.get(program)



	#@rename db.time.get @ok @return str
	@publicmethod
	def gettime(self, ctx=None, txn=None):
		"""Get current DB time. The time string format is in the config file; default is YYYY/MM/DD HH:MM:SS.

		@return DB time date string

		"""
		return gettime()




	###############################
	# section: Login and Context Management
	###############################

	#@rename db.auth.login
	# This is intentionally not a publicmethod because DBProxy wraps it
	LOGINERRMSG = 'Invalid username or password: %s'
	def login(self, username="anonymous", password="", host=None, maxidle=None, ctx=None, txn=None):
		"""(DBProxy Only) Logs a given user in to the database and returns a ctxid, which can then be used for
		subsequent access. Returns ctxid, or fails with AuthenticationError or SessionError

		@keyparam username Account username
		@keyparam password Account password
		@keyparam host Bind to this host
		@keyparam maxidle Maximum idle time

		@return Context key (ctxid)

		@exception AuthenticationError, KeyError
		"""

		if maxidle == None or maxidle > g.MAXIDLE:
			maxidle = g.MAXIDLE

		newcontext = None
		username = unicode(username).strip()

		# print "attempted login: %s"%username
		# Anonymous access

		byemail = self.bdbs.usersbyemail.get(username.lower(), txn=txn)
		if len(byemail) == 1:
			username = byemail.pop()
		elif len(byemail) > 1:
			g.log.msg('LOG_SECURITY', "Multiple accounts associated with email %s"%username)			
			raise emen2.db.exceptions.AuthenticationError, "Invalid username or password"
			

		if username == "anonymous":
			newcontext = self.__makecontext(host=host, ctx=ctx, txn=txn)
		else:
			try:
				user = self.__login_getuser(username, ctx=ctx, txn=txn)
			except:
				g.log.msg('LOG_SECURITY', "Invalid username or password: %s"%username)
				raise emen2.db.exceptions.AuthenticationError, "Invalid username or password"

			if user.checkpassword(password):
				newcontext = self.__makecontext(username=username, host=host, ctx=ctx, txn=txn)
			else:
				g.log.msg('LOG_SECURITY', "Invalid username or password: %s"%username)
				raise emen2.db.exceptions.AuthenticationError, "Invalid username or password"

		try:
			self.__commit_context(newcontext.ctxid, newcontext, ctx=ctx, txn=txn)
			g.log.msg('LOG_SECURITY', "Login succeeded: %s %s" % (username, newcontext.ctxid))
		except:
			g.log.msg('LOG_ERROR', "Error writing login context")
			raise

		return newcontext.ctxid


	# backwards compat
	_login = login


	# Logout is the same as delete context

	#@rename db.auth.logout @ok @return bool
	@publicmethod
	def logout(self, ctx=None, txn=None):
		"""Logout"""
		self.__commit_context(ctx.ctxid, None, ctx=ctx, txn=txn)
		return True


	#@rename db.auth.whoami @ok @return tuple
	@publicmethod
	def checkcontext(self, ctx=None, txn=None):
		"""This allows a client to test the validity of a context, and get basic information on the authorized user and his/her permissions.

		@return Tuple: (username, groups)

		"""
		return ctx.username, ctx.groups



	#@rename db.auth.check.admin @ok @return bool
	@publicmethod
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.

		@return bool

		"""
		return ctx.checkadmin()



	#@rename db.auth.check.readadmin @ok @return bool
	@publicmethod
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.

		@return bool

		"""
		return ctx.checkreadadmin()



	#@rename db.auth.check.create @ok @return bool
	@publicmethod
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.

		@return bool

		"""
		return ctx.checkcreate()



	def __makecontext(self, username="anonymous", host=None, ctx=None, txn=None):
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



	def __makerootcontext(self, ctx=None, host=None, txn=None):
		"""(Internal) Create a root context. Can use this internally when some admin tasks that require ctx's are necessary."""

		ctx = emen2.db.context.SpecialRootContext()
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
			raise emen2.db.exceptions.AuthenticationError, 'No such user' #emen2.db.exceptions.AuthenticationError.__doc__
		return user



	def __commit_context(self, ctxid, context, ctx=None, txn=None):
		"""(Internal) Manipulate cached and stored contexts. Use this to update or delete contexts.
		It will update BDB if necessary. This is called frequently to set idle time.

		@param ctxid ctxid key
		@param context Context instance

		@exception KeyError, DBError
		"""

		#@begin

		# any time you set the context, delete the cached context
		# this will retrieve it from disk next time it's needed
		if self.bdbs.contexts_cache.get(ctxid):
			del self.bdbs.contexts_cache[ctxid]

		# set context
		if context != None:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts.set: %r"%context.ctxid)
				self.bdbs.contexts.set(ctxid, context, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Unable to add persistent context %s (%s)"%(ctxid, inst))
				raise


		# delete context
		else:
			try:
				g.log.msg("LOG_COMMIT","self.bdbs.contexts.__delitem__: %r"%ctxid)
				self.bdbs.contexts.set(ctxid, None, txn=txn) #del ... [ctxid]

			except Exception, inst:
				g.log.msg("LOG_CRITICAL","Unable to delete persistent context %s (%s)"%(ctxid, inst))
				raise

		#@end



	# ian: todo: hard: flesh this out into a proper cron system, with a subscription model; right now just runs cleanupcontext
	# right now this is called during _getcontext, and calls cleanupcontexts not more than once every 10 minutes
	def __periodic_operations(self, ctx=None, txn=None):
		"""(Internal) Maintenance task scheduler. Eventually this will be replaced with a maintenance registration system, similar to @publicmethod"""

		t = getctime()
		if t > (self.lastctxclean + 600):
			self.lastctxclean = time.time()
			self.__cleanupcontexts(ctx=ctx, txn=txn)



	# ian: todo: hard: finish
	def __cleanupcontexts(self, ctx=None, txn=None):
		"""(Internal) Clean up sessions that have been idle too long."""

		g.log.msg("LOG_DEBUG","Clean up expired contexts: time %s -> %s"%(self.lastctxclean, time.time()))

		for ctxid, context in self.bdbs.contexts.items(txn=txn):
			# use the cached time if available
			try:
				c = self.bdbs.contexts_cached.sget(ctxid, txn=txn) #[ctxid]
				context.time = c.time
			# ed: fix: should check for more specific exception
			except:
				pass

			if context.time + (context.maxidle or 0) < time.time():
				# g.log_info("Expire context (%s) %d" % (context.ctxid, time.time() - context.time))
				self.__commit_context(context.ctxid, None, ctx=ctx, txn=txn)



	# ian: todo: hard:
	#		how often should we refresh groups?
	#		right now, every publicmethod will reset user/groups
	#		timer based?
	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Internal and DBProxy) Takes a ctxid key and returns a context. Note that both key and host must match.
		@param ctxid ctxid
		@param host host

		@return Context

		@exception SessionError
		"""

		self.__periodic_operations(ctx=ctx, txn=txn)

		context = None
		if ctxid:
			# g.log.msg("LOG_DEBUG", "local context cache: %s, cache db: %s"%(self.bdbs.contexts.get(ctxid), self.bdbs.contexts.get(ctxid, txn=txn)))
			context = self.bdbs.contexts_cache.get(ctxid) or self.bdbs.contexts.get(ctxid, txn=txn)
		else:
			context = self.__makecontext(host=host, ctx=ctx, txn=txn)

		if not context:
			g.log.msg('LOG_ERROR', "Session expired: %s"%ctxid)
			raise emen2.db.exceptions.SessionError, "Session expired: %s"%(ctxid)

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
		context.refresh(user=user, grouplevels=grouplevels, host=host, db=self, txn=txn)

		self.bdbs.contexts_cache[ctxid] = context

		return context





	###############################
	# section: binaries
	###############################



	#@multiple @filt @ok @return Binary or [Binaries]
	@publicmethod
	def getbinary(self, bdokeys=None, q=None, filt=True, params=None, ctx=None, txn=None):
		"""Get Binary objects from ids or references. Binaries include file name, size, md5, associated record, etc. Each binary has an ID, aka a 'BDO'

		@param bdokeys A single binary ID, or an iterable containing: records, recids, binary IDs
		@keyparam filt Ignore failures
		@keyparam params For record search, limit to (single/iterable) params

		@return A single Binary instance or a list of Binaries

		@exception KeyError, SecurityError
		"""

		# ian: recently rewrote this for substantial speed improvements when getting 1000+ binaries

		# process bdokeys argument for bids (into list bids) and then process bids
		ol, bdokeys = listops.oltolist(bdokeys)
		filt = False

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
		recs.extend(self.getrecord((x for x in bdokeys if isinstance(x,int)), filt=True, ctx=ctx, txn=txn))
		recs.extend(x for x in bdokeys if isinstance(x,emen2.db.record.Record))

		if recs:
			# get the params we're looking for
			params = params or self.getparamdefnames(ctx=ctx, txn=txn)
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
		parsed = [emen2.db.binary.Binary.parse(bdokey) for bdokey in bids]

		for k in parsed:
			bydatekey[k["datekey"]].append(k)


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




	#@rename db.binary.put @ok @single @return Binary
	#filename, recid=None, bdokey=None, filedata=None, filehandle=None, param=None, record=None, uri=None, ctx=None, txn=None):
	@publicmethod
	def putbinary(self, bdokey=None, recid=None, param=None, filename=None, filedata=None, filehandle=None, uri=None, clone=False, ctx=None, txn=None):
		"""Add binary object to database and attach to record. May specify record param to use and file data to write to storage area. Admins may modify existing binaries. Optional filedata/filehandle to specify file contents."""

		if clone and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only admins can update BDOs using the cloning tool"

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "Record creation permissions required to add BDOs"


		# Sanitize filename.. This will allow unicode characters, and check for reserved filenames on linux/windows
		if filename != None:
			filename = "".join([i for i in filename if i.isalpha() or i.isdigit() or i in '.()-=_'])
			if filename.upper() in ['.', 'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']:
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
		if filehandle or filedata:
			newfile, filesize, md5sum = self.__putbinary_file(filename, filehandle=filehandle, filedata=filedata, dkey=dkey, ctx=ctx, txn=txn)

		# Update the BDO: Start RMW cycle
		bdo = self.bdbs.bdocounter.get(dkey["datekey"], txn=txn, flags=g.RMWFLAGS) or {}		

		if dkey["counter"] == 0:
			counter = max(bdo.keys() or [-1]) + 1
			dkey = emen2.db.binary.Binary.parse(bdokey, counter=counter)


		nb = bdo.get(dkey["counter"])
		if newfile:
			if nb:
				raise emen2.db.exceptions.SecurityError, "BDOs are immutable"
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

		self.bdbs.bdosbyfilename.addrefs(filename, [dkey["name"]], txn=txn)
		g.log.msg("LOG_COMMIT","self.bdbs.bdosbyfilename: %s %s"%(filename, dkey["name"]))

		# Now move the file to the right location
		if newfile:
			os.rename(newfile, dkey["filepath"])

		return self.getbinary(nb.get('name'), ctx=ctx, txn=txn)



	def __putbinary_file(self, filename=None, filedata=None, filehandle=None, dkey=None, ctx=None, txn=None):
		try:
			os.makedirs(dkey["basepath"])
		except:
			pass

		filename = filename or "UnkownFilename"

		# Write out file to temporary storage
		(fd, tmpfilepath) = tempfile.mkstemp(suffix=".upload", dir=dkey["basepath"])
		m = hashlib.md5()
		filesize = 0

		with os.fdopen(fd, "w+b") as f:
			if not filedata:
				for line in filehandle:
					f.write(line)
					m.update(line)
					filesize += len(line)
			else:
				f.write(filedata)
				m.update(filedata)
				filesize = len(filedata)

		if filesize == 0 and not ctx.checkadmin():
			raise ValueError, "Empty file!"

		md5sum = m.hexdigest()
		g.log.msg('LOG_INFO', "Wrote: %s, filesize: %s, md5sum: %s"%(tmpfilepath, filesize, md5sum))

		return tmpfilepath, filesize, md5sum



	# ed: todo?: key by recid
	#@rename db.binary.list @ok @return set
	@publicmethod
	def getbinarynames(self, ctx=None, txn=None):
		"""Get a list of all binaries."""
		if ctx.username == None:
			raise emen2.db.exceptions.SecurityError, "getbinarynames not available to anonymous users"

		ret = (set(y.name for y in x.values()) for x in self.bdbs.bdocounter.values())
		ret = reduce(set.union, ret, set())
		return set().union(*ret)






	###############################
	# section: query
	###############################



	#@rename db.query.query @notok
	@publicmethod
	def query(self, c=None, q=None, boolmode=None, ignorecase=None, subset=None, ctx=None, txn=None, **kwargs):
		"""Query. New docstring coming soon."""

		# Setup defaults
		if not c:
			c = []

		if q:
			c.append(["root_parameter*", "contains_w_empty", q])

		if ignorecase == None:
			ignorecase = 1
		ignorecase = int(ignorecase)

		if boolmode == None:
			boolmode = "AND"
		if boolmode == "AND":
			boolop = "intersection_update"
		elif boolmode == "OR":
			boolop = "update"
		else:
			raise Exception, "Invalid boolean mode: %s. Must be AND, OR"%boolmode

		vtm = emen2.db.datatypes.VartypeManager()
		recids = None

		# Query Step 1: Run constraints
		groupby = {}
		for searchparam, comp, value in c:
			t = time.time()
			constraintmatches = self.__query_constraint(searchparam, comp, value, groupby=groupby, ctx=ctx, txn=txn)
			# print "== ", time.time()-t, searchparam, comp, value

			if recids == None:
				recids = constraintmatches
			if "^" not in searchparam and constraintmatches != None: # parent-value params are only for grouping..
				getattr(recids, boolop)(constraintmatches)


		# Step 2: Filter permissions
		if c:
			recids = self.filterbypermissions(recids or set(), ctx=ctx, txn=txn)
		else:
			# ... these are already filtered, so insert the result of an empty query here.
			recids = self.getindexbycontext(ctx=ctx, txn=txn)
	
		if subset:
			recids &= subset
			
					
		# Step 3: Group
		groups = collections.defaultdict(dict)
		for groupparam, keys in groupby.items():
			self.__query_groupby(groupparam, keys, groups=groups, recids=recids, ctx=ctx, txn=txn)
			

		ret = {
			"q":q,
			"c": c,
			"boolmode": boolmode,
			"ignorecase": ignorecase,
			"recids": recids,
			"groups": groups,
			"subset": subset
		}		
		return ret




	def __query_groupby(self, groupparam, keys, groups=None, recids=None, ctx=None, txn=None):
		param = self.__query_paramstrip(groupparam)

		if param == "rectype":
			groups["rectype"] = self.groupbyrecorddef(recids, ctx=ctx, txn=txn)

		elif param == "parent":
			# keys is parent rectypes...
			parentrectype = self.getindexbyrecorddef(keys, ctx=ctx, txn=txn)
			# recurse=-1 for all parents
			parenttree = self.getparents(recids, recurse=-1, ctx=ctx, txn=txn) 
			parentgroups = collections.defaultdict(set)
			for k,v in parenttree.items():
				v2 = v & parentrectype
				for i in v2:
					parentgroups[i].add(k)
			if parentgroups:
				groups["parent"] = dict(parentgroups)

		else:
			if not keys:
				return
				
			ind = self.__getparamindex(self.__query_paramstrip(groupparam), ctx=ctx, txn=txn)
			for key in keys:
				v = ind.get(key, txn=txn)
				if "^" in groupparam:
					children = self.getchildren(v, recurse=-1, ctx=ctx, txn=txn)
					for i in v:
						v2 = children.get(i, set()) & recids
						if v2: groups[param][key] = v2
				else:
					v2 = v & recids
					if v2: groups[param][key] = v2




	def __query_constraint(self, searchparam, comp, value, groupby=None, ctx=None, txn=None):
		param = self.__query_paramstrip(searchparam)
		value = unicode(value)

		recurse = 0
		if '*' in value:
			value = value.replace('*', '')
			recurse = -1

		if value == "":
			value = None
			
		subset = None

		# print "\n== running constraint: %s/%s %s %s"%(searchparam, param, comp, value)

		if param == "rectype":
			if comp == "==" and value != None:
				if recurse == -1:
					ovalue = value
					value = self.getchildren(value, recurse=recurse, keytype="recorddef", ctx=ctx, txn=txn)
					value.add(ovalue)
				subset = self.getindexbyrecorddef(value, ctx=ctx, txn=txn)
			groupby["rectype"] = None

		elif param == "recid":
			subset = set([int(value)])

		elif param == "parent":
			if comp == "recid" and value != None:
				subset = self.getchildren(value, recurse=recurse, ctx=ctx, txn=txn)

			if comp == "rectype":
				groupby["parent"] = value

		elif param == "child":
			if comp == "recid" and value != None:
				subset = self.getparents(value, recurse=recurse, ctx=ctx, txn=txn)
			

		elif param:
			subset = self.__query_index(searchparam, comp, value, groupby=groupby, ctx=ctx, txn=txn)

		else:
			pass
			# print "no param, skipping"

		# print "return was:"
		# print subset

		return subset



	def __query_index(self, searchparam, comp, value, groupby=None, ctx=None, txn=None):
		"""(Internal) index-based search. See DB.query()"""

		cfunc = self.__query_cmps().get(comp)

		if groupby == None:
			groupby = {}

		if value == None and comp not in ["!None", "contains_w_empty"]:
			return None

		if not cfunc:
			return None

		vtm = emen2.db.datatypes.VartypeManager()
		results = collections.defaultdict(set)

		# Get the list of param indexes to search
		if searchparam == "*":
			indparams = self.bdb.indexkeys.keys(txn=txn)
		elif '*' in searchparam:
			indparams = self.getchildren(self.__query_paramstrip(searchparam), recurse=-1, keytype="paramdef", ctx=ctx, txn=txn)
		else:
			indparams = [self.__query_paramstrip(searchparam)]

		# First, search the index index
		for indparam in indparams:
			pd = self.bdbs.paramdefs.get(indparam, txn=txn)
			try:
				cargs = vtm.validate(pd, value, db=ctx.db)
			except:
				continue

			r = set(filter(functools.partial(cfunc, cargs), self.bdbs.indexkeys.get(indparam, txn=txn)))
			if r:
				results[indparam] = r

		# Now search individual param indexes
		constraint_matches = set()
		for pp, matchkeys in results.items():

			# Mark these for children searches later
			if '^' in searchparam:
				groupby[pp+"^"] = matchkeys
			else:
				groupby[pp] = matchkeys

			ind = self.__getparamindex(pp, ctx=ctx, txn=txn)
			for matchkey in matchkeys:
				constraint_matches |= ind.get(matchkey, txn=txn)

		return constraint_matches



	def __query_cmps(self, ignorecase=1):
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

		return cmps



	def __query_paramstrip(self, param):
		return param.replace("*","").replace("^","")



	def __query_invert(self, d):
		invert = {}
		for k,v in d.items():
			for v2 in v: invert[v2] = k
		return invert



	def __getplotfile(self, prefix=None, suffix=None, ctx=None, txn=None):
		tempfile = "%s-%s-%s.%s"%(ctx.ctxid, prefix, time.strftime("%Y.%m.%d-%H.%M.%S"), suffix)
		return os.path.join(g.paths.TMPPATH, tempfile)
		
	

	
	@publicmethod
	def plot_xy(self, x, y, xmin=None, xmax=None, ymin=None, ymax=None, width=600, xlabel=None, ylabel=None, formats=None, buffer=False, style='b', ctx=None, txn=None, **kwargs):

		if not formats:
			formats = ["png"]

		width = int(width)
		fig = matplotlib.figure.Figure(figsize=(width/100.0, width/100.0), dpi=100)
		canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)

		ax_size = [0, 0, 1, 1]
		if xlabel or ylabel or buffer:
			ax_size = [0.15, 0.15, 0.8, 0.8]
			
		ax = fig.add_axes(ax_size)
		ax.grid(True)
		
		handle = ax.plot(x, y, style)
		
		if xmin == None: xmin = min(x)
		else: xmax = float(xmax)

		if xmax == None: xmax = max(x)
		else: xmax = float(xmax)

		if ymin == None: ymin = min(y)
		else: ymin = float(ymin)

		if ymax == None: ymax = max(y)
		else: ymax = float(ymax)
			
		ax.set_xlim(xmin, xmax)
		ax.set_ylim(ymin, ymax)		

		if xlabel: ax.set_xlabel(xlabel)
		if ylabel: ax.set_ylabel(ylabel)

		plots = {}
		if "png" in formats:
			pngfile = self.__getplotfile(prefix="plot_xy", suffix="png", ctx=ctx, txn=txn)
			fig.savefig(pngfile)
			plots["png"] = pngfile


		q = {}
		q.update({
			"plots": plots,
			"xlabel": xlabel,
			"ylabel": ylabel,
			"formats": formats,
			"width": width,
			"xmin": xmin,
			"xmax": xmax,
			"ymin": ymin,
			"ymax": ymax
		})

		return q					



	@publicmethod
	def querytable(self, pos=0, count=100, sortkey="creationtime", reverse=None, viewdef=None, ctx=None, txn=None, **q):
		
		xparam = q.get('xparam', None)
		yparam = q.get('yparam', None)
		count = int(count) or None
		pos = int(pos)
		
		if reverse == None:
			reverse = 1
		reverse = int(reverse)		

		# Run query
		if xparam or yparam:
			q.update(self.plot(ctx=ctx, txn=txn, **q))
		else:
			q.update(self.query(ctx=ctx, txn=txn, **q))
						
			
		length = len(q['recids'])		
		rectypes = q.get('groups', {}).get('rectype', {})
		rds = self.getrecorddef(rectypes.keys(), ctx=ctx, txn=txn)

		# Process into table
		if len(rds) == 1 and not viewdef:
			rds = rds.pop()
			viewdef = rds.views['tabularview']
		elif len(rds) > 1 or len(rds) == 0:
			viewdef = "$@recname() $@thumbnail() $$rectype $$recid $$creator $$creationtime"
		
		# Sort
		q['recids'] = self.sort(q['recids'], param=sortkey, reverse=reverse, pos=pos, count=count, rendered=True, ctx=ctx, txn=txn)
		
		# Render
		rendered = self.renderview(q['recids'], viewdef=viewdef, mode="htmledit_table", table=True, ctx=ctx, txn=txn)

		q.update(dict(
			pos = pos,
			count = count,
			sortkey = sortkey,
			reverse = reverse,
			viewdef = viewdef,
			length = length,
			rendered = rendered,
			groups = {}
		))

		return q



	@publicmethod
	def plot(self, xparam, yparam, groupby="rectype", c=None, groupshow=None, groupcolors=None, formats=None, xmin=None, xmax=None, ymin=None, ymax=None, width=600, cutoff=1, ctx=None, txn=None, **kwargs):

		# Run all the arguments through query..
		c = c or []
		cparams = [i[0] for i in c]
		if xparam not in cparams:
			c.append([xparam, "!None", ""])
		if yparam not in cparams:
			c.append([yparam, "!None", ""])
					

		# t = time.time()

		q = self.query(c=c, ctx=ctx, txn=txn, **kwargs)
		if not q["groups"].get(groupby):
			groupby = "rectype"
			q["groups"][groupby] = self.groupbyrecorddef(q["recids"], ctx=ctx, txn=txn)

		# print "Time: %s"%(time.time()-t)


		if not formats:
			formats = ["png"]

		width = int(width)
		groupcolors = groupcolors or {}

		# Get parameters
		xpd = self.getparamdef(xparam, ctx=ctx, txn=txn)
		ypd = self.getparamdef(yparam, ctx=ctx, txn=txn)

		groups = q["groups"]
		xinvert = self.__query_invert(groups[xparam])
		yinvert = self.__query_invert(groups[yparam])
		recids = set(xinvert.keys()) & set(yinvert.keys())

		### plot_plot
		colorcount = len(COLORS)

		# Generate labels
		# title = '%s vs %s, grouped by %s %s'%(xpd.desc_short, ypd.desc_short, grouptype, groupby or '')
		title = kwargs.get('title') or 'Test Graph'
		xlabel = kwargs.get('xlabel') or '%s'%(xpd.desc_short)
		ylabel = kwargs.get('ylabel') or '%s'%(ypd.desc_short)
		if xpd.defaultunits and not kwargs.get('xlabel'):
			xlabel = '%s (%s)'%(xlabel, xpd.defaultunits)
		if ypd.defaultunits and not kwargs.get('ylabel'):
			ylabel = '%s (%s)'%(ylabel, ypd.defaultunits)


		# Ok, actual plotting is pretty simple...
		fig = matplotlib.figure.Figure(figsize=(width/100.0, width/100.0), dpi=100)
		canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)

		ax_size = [0.1, 0.1, 0.8, 0.8]
		ax = fig.add_axes(ax_size)
		ax.grid(True)

		handles = []
		labels = []
		groupnames = {}
		nextcolor = 0

		nr = [None, None, None, None]

		def less(x,y):
			if x < y or y == None: return x
			return y
		def greater(x,y):
			if x > y or y == None: return x
			return y


		# plot each group
		for k,v in sorted(groups[groupby].items()):
			# v = v & recids
			if len(v) <= cutoff:
				continue
				
			groupnames[k] = "%s (%s records)"%(k, len(v))
			groupcolors[k] = groupcolors.get(k, COLORS[nextcolor%colorcount])
			nextcolor += 1

			if  (groupshow and k not in groupshow):
				continue
				
			x = map(xinvert.get, v)
			y = map(yinvert.get, v)

			nr = [less(min(x), nr[0]), less(min(y), nr[1]), greater(max(x), nr[2]), greater(max(y), nr[3])]
			handle = ax.scatter(x, y, c=groupcolors[k])
			handles.append(handle)
			labels.append(k)


		if xmin != None: nr[0] = float(xmin)
		if ymin != None: nr[1] = float(ymin)
		if xmax != None: nr[2] = float(xmax)
		if ymax != None: nr[3] = float(ymax)

		# print "ranges: %s"%nr
		ax.set_xlim(nr[0], nr[2])
		ax.set_ylim(nr[1], nr[3])


		plots = {}
		if "png" in formats:
			pngfile = self.__getplotfile(prefix="plot", suffix="png", ctx=ctx, txn=txn)
			fig.savefig(pngfile)
			plots["png"] = os.path.basename(pngfile)


		# We draw titles, labels, etc. in PDF graphs
		if "pdf" in formats:
			ax.set_title(title)
			ax.set_xlabel(xlabel)
			ax.set_ylabel(ylabel)
			fig.legend(handles, labels) #borderaxespad=0.0,  #bbox_to_anchor=(0.8, 0.8)
			pdffile = self.__getplotfile(prefix="plot", suffix="pdf", ctx=ctx, txn=txn)
			fig.savefig(pdffile)
			plots["pdf"] = os.path.basename(pdffile)


		q.update({
			"plots": plots,
			"xlabel": xlabel,
			"ylabel": ylabel,
			"title": title,
			"groupcolors": groupcolors,
			"groupshow": groupshow,
			"groupnames": groupnames,
			"formats": formats,
			"groupby": groupby,
			"xparam": xparam,
			"yparam": yparam,
			"width": width,
			"xmin": nr[0],
			"xmax": nr[2],
			"ymin": nr[1],
			"ymax": nr[3],
			"cutoff": cutoff
		})

		return q




	def __findqueryinstr(self, query, s, window=20):
		"""(Internal) Give a window of context around a substring match"""

		if not query:
			return False

		if query in (s or ''):
			pos = s.index(query)
			if pos < window: pos = window
			return s[pos-window:pos+len(query)+window]

		return False




	@publicmethod
	def sort(self, recids, param="creationtime", reverse=False, rendered=False, pos=0, count=None, ctx=None, txn=None):
		"""Sort recids based on a param or macro."""

		reverse = bool(reverse)
		pd = self.getparamdef(param, ctx=ctx, txn=txn)

		# Macro rendering not implemented..
		if not param or param == "creationtime" or param == "recid" or not pd:
			if pos != None and count != None:
				return sorted(recids, reverse=reverse)[pos:pos+count]
			return sorted(recids, reverse=reverse)


		_t=time.time()

		recs = listops.typefilter(recids, emen2.db.record.Record)		
		recids = listops.typefilter(recids, int)
		index = self.__getparamindex(param, ctx=ctx, txn=txn)
		values = collections.defaultdict(set)


		
		# sort/render using records directly..
		if recs or not index or len(recids)<1000:
			recs.extend(self.getrecord(recids, ctx=ctx, txn=txn))
			recids = set([rec.recid for rec in recs])		
			for rec in recs:
				try:
					values[rec.get(param)].add(rec.recid)		
				except TypeError:
					values[tuple(rec.get(param))].add(rec.recid)
					
					
		# Use the index
		else:
			recids = set(recids)
			# Not the best way to search the index..
			for k,v in index.items(txn=txn):
				v = v & recids
				if v:
					values[k] |= v



		# calling out to vtm, we will need a DBProxy
		# I'm only turning on render sort for these vartypes for now..
		if rendered and pd.vartype in ["user", "userlist", "binary", "binaryimage"]:
			if len(recids) > 1000:
				raise ValueError, "Too many items to sort by this key"
			dbp = ctx.db
			dbp._settxn(txn)
			vtm = emen2.db.datatypes.VartypeManager()
			newvalues = collections.defaultdict(set)
			for k in values:
				newvalues[vtm.param_render_sort(pd, k, db=dbp)] = values[k]
				# rec=recs_dict.get(recid) # may fail without record..
			values = newvalues


		
		ret = []
		for k in sorted(values.keys(), reverse=reverse):
			ret.extend(sorted(values[k]))
		
		seen = set(ret)
		ret.extend(sorted(recids-seen))	
		# ret.extend(nonevalues)

			
		if pos != None and count != None:	
			return ret[pos:pos+count]
		return ret



				



	#@notok
	@publicmethod
	def findrecorddef(self, query=None, name=None, desc_short=None, desc_long=None, mainview=None, childof=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		"""Find a recorddef, by general search string, or by name/desc_short/desc_long/mainview/childof

		@keyparam query Contained in any item below
		@keyparam name ... contains in name
		@keyparam desc_short ... contains in short description
		@keyparam desc_long ... contains in long description
		@keyparam mainview ... contains in mainview
		@keyparam childof ... is child of

		@return list of matching recorddefs
		"""
		return self.__find_pd_or_rd(query=query, keytype='recorddef', context=context, limit=limit, ctx=ctx, txn=txn, name=name, desc_short=desc_short, desc_long=desc_long, mainview=mainview, boolmode=boolmode, childof=childof)



	#@notok
	@publicmethod
	def findparamdef(self, query=None, name=None, desc_short=None, desc_long=None, vartype=None, childof=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		return self.__find_pd_or_rd(query=query, keytype='paramdef', context=context, limit=limit, ctx=ctx, txn=txn, name=name, desc_short=desc_short, desc_long=desc_long, vartype=vartype, boolmode=boolmode, childof=childof)



	def __filter_dict_zero(self, d):
		return dict(filter(lambda x:len(x[1])>0, d.items()))



	def __filter_dict_none(self, d):
		return dict(filter(lambda x:x[1]!=None, d.items()))



	def __find_pd_or_rd(self, childof=None, boolmode="OR", keytype="paramdef", context=False, limit=None, ctx=None, txn=None, **qp):
		# query=None, name=None, desc_short=None, desc_long=None, vartype=None, views=None,
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
		#p1 = []
		#if qp['name']:
		#	p1 = filter(lambda x:qp['name'] in x, rdnames)

		# ian: will there be a faster way to do this?
		rds2 = getitems(rdnames, filt=True, ctx=ctx, txn=txn) or []
		p2 = []

		qp = self.__filter_dict_none(qp)

		for i in rds2:
			qt = []
			for k,v in qp.items():
				qt.append(self.__findqueryinstr(v, i.get(k)))

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

		if context:
			return p2, c

		return p2



	#@ok
	@publicmethod
	def findbinary(self, query=None, broad=False, limit=None, ctx=None, txn=None):
		"""Find a binary by filename

		@keyparam query Match this filename
		@keyparam broad Try variations of filename (extension, partial matches, etc..)

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



	#@ok
	#@rename db.query.user
	@publicmethod
	def finduser(self, query=None, email=None, name_first=None, name_middle=None, name_last=None, username=None, boolmode="OR", context=False, limit=None, ctx=None, txn=None):
		"""Find a user, by general search string, or by name_first/name_middle/name_last/email/username

		@keyparam query Contained in any item below
		@keyparam email ... contains in email
		@keyparam name_first ... contains in first name
		@keyparam name_middle ... contains in middle name
		@keyparam name_last ... contains in last name
		@keyparam username ... contains in username
		@keyparam boolmode 'AND' / 'OR'
		@keyparam limit Limit number of items

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
			["name_first","contains", name_first],
			["name_middle","contains", name_middle],
			["name_last","contains", name_last],
			["email", "contains", email],
			["username","contains_w_empty", username]
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




	#@rename db.query.group @ok
	@publicmethod
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



	#@rename db.query.value @ok
	@publicmethod
	def findvalue(self, param, query, count=True, showchoices=True, limit=100, ctx=None, txn=None):
		"""Find values for a parameter.

		@param param Parameter to search
		@param query Match this

		@keyparam limit Limit number of results
		@keyparam showchoices Include any defined param 'choices'
		@keyparam count Return count of matches, otherwise return recids

		@return if count: [[matching value, count], ...]
				if not count: [[matching value, [recid, ...]], ...]
		"""

		pd = self.getparamdef(param, ctx=ctx, txn=txn)
		ret = self.query(c=[[param, "contains_w_empty", query]], ignorecase=1, ctx=ctx, txn=txn)

		s2 = ret.get('groups', {}).get(param, {})
		keys = sorted(s2.items(), key=lambda x:len(x[1]), reverse=True)
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
		

		# This method was simplified, and now uses __query_index directly
		# cmps = self.__query_cmps(ignorecase=True)
		# s1, s2 = self.__query_index(c=[[param, "contains_w_empty", query]], cmps=cmps, ctx=ctx, txn=txn)
		# #{('name_last', u'Rees'): set([271390])}
		# 
		# # This works nicely, I should rewrite some of my other list sorteds
		# keys = sorted(s2.items(), key=lambda x:len(x[1]), reverse=True)
		# if limit: keys = keys[:int(limit)]
		# 
		# # Turn back into a dictionary
		# ret = dict([(i[0][1], i[1]) for i in keys])
		# if count:
		# 	for k in ret:
		# 		ret[k]=len(ret[k])
		# 
		# return ret




	#########################
	# section: Query / Index Management
	#########################


	#@rename db.query.recorddef
	#@multiple @ok @return set of recids
	@publicmethod
	def getindexbyrecorddef(self, recdefs, ctx=None, txn=None):
		"""Records by Record Def. This is currently non-secured information.

		@param recdef A single or iterable Record Def name

		@keyparam filt Filter by permissions

		@return List of recids
		"""

		ol, recdefs = listops.oltolist(recdefs)

		ret = set()
		for i in recdefs:
			self.getrecorddef(i, ctx=ctx, txn=txn) # check for permissions
			ret |= self.bdbs.recorddefindex.get(i, txn=txn)

		# return self.filterbypermissions(ret, ctx=ctx, txn=txn)

		return ret




	# ian todo: medium: add unit support.
	#@rename db.query.param @ok @return set of recids
	@publicmethod
	def getindexbyvalue(self, param, value, ctx=None, txn=None):
		# """Query an indexed parameter. Return all records that contain a value, with optional value range
		#
		# @param param parameter name
		#
		# @keyparam valrange tuple of (min, max) values to search
		#
		# @return List of matching recids
		# """
		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
		if paramindex == None: return set()

		ret = paramindex.get(value, txn=txn)
		return self.filterbypermissions(ret, ctx=ctx, txn=txn) #ret & secure # intersection of the two search results


	@publicmethod
	def getindexinrange(self, param, low=None, high=None, ctx=None, txn=None):
		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
		if paramindex == None: return set()

		ret = None
		if low != None or high != None:
			keys = paramindex.keys(txn=txn)
			if low != None:
				keys = (x for x in keys if low <= x)
			if high != None:
				keys = (x for x in keys if high > x)
			keys = set(keys)
			ret = reduce(set.union, (paramindex.get(k, txn=txn) for k in keys), set())
		else:
			ret = paramindex.values(txn=txn)

		return self.filterbypermissions(ret, ctx=ctx, txn=txn) #ret & secure # intersection of the two search results



	# ian: todo: this could use updating
	#@rename db.query.paramdict @ok @return dict, k=param value, v=recids
	@publicmethod
	def getindexdictbyvalue(self, param, valrange=None, subset=None, ctx=None, txn=None):
		"""Query a param index, returned in a dict keyed by value.

		@param param parameter name

		@keyparam valrange tuple of (min, max) values to search
		@keyparam subset restrict to record subset

		@return Return dict with recids as key, param value as values
		"""

		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
		if paramindex == None:
			return {}

		r = dict(paramindex.items(txn=txn))

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
	def getindexbypermissions(self, recids=None, users=None, groups=None, ctx=None, txn=None):
		ret = set()
		
		if users:
			for user in users:
				ret |= self.bdbs.secrindex.get(user, set(), txn=txn)
		elif not groups:
			for k,v in self.bdbs.secrindex.items(txn=txn):
				ret |= v

		if groups:
			for group in groups:
				ret |= self.bdbs.secrindex_groups.get(group, set(), txn=txn)
		elif not users:
			for k,v in self.bdbs.secrindex_groups.items(txn=txn):
				ret |= v
		
		
		if ctx.checkreadadmin() and not recids:
			return ret

		if recids:
			ret &= recids
			
		return self.filterbypermissions(ret, ctx=ctx, txn=txn)
			
		


	# #@rename db.query.context
	@publicmethod
	def getindexbycontext(self, ctx=None, txn=None):
		"""Return all readable recids
		@return All readable recids"""
	
		if ctx.checkreadadmin():
			return set(range(self.bdbs.records.get_max(txn=txn))) #+1)) # Ed: Fixed an off by one error
	
		ret = set(self.bdbs.secrindex.get(ctx.username, set(), txn=txn)) #[ctx.username]
	
		for group in sorted(ctx.groups,reverse=True):
			ret |= set(self.bdbs.secrindex_groups.get(group, set(), txn=txn))#[group]
	
		return ret



	# ian: todo: finish this method
	# #@rename db.query.statistics @notok
	# @publicmethod
	# def getparamstatistics(self, param, ctx=None, txn=None):
	# 	"""Return statistics about an (indexable) param
	#
	# 	@param param parameter
	#
	# 	@return (Count of keys, count of values)
	# 	"""
	#
	# 	if ctx.username == None:
	# 		raise emen2.db.exceptions.SecurityError, "Not authorized to retrieve parameter statistics"
	#
	# 	try:
	# 		paramindex = self.__getparamindex(param, ctx=ctx, txn=txn)
	# 		return (len(paramindex.keys(txn=txn)), len(paramindex.values(txn=txn)))
	# 	except:
	# 		return (0,0)



	# ian: todo: simple: expose as offline admin method
	#@adminmethod
	def __rebuild_indexkeys(self, ctx=None, txn=None):
		"""(Internal) Rebuild index-of-indexes"""

		# g.log.msg("LOG_INFO", "self.bdbs.indexkeys: Starting rebuild")
		inds = dict(filter(lambda x:x[1]!=None, [(i,self.__getparamindex(i, ctx=ctx, txn=txn)) for i in self.getparamdefnames(ctx=ctx, txn=txn)]))

		g.log.msg("LOG_INFO","self.bdbs.indexkeys.truncate")
		self.bdbs.indexkeys.truncate(txn=txn)

		for k,v in inds.items():
			g.log.msg("LOG_INFO", "self.bdbs.indexkeys: rebuilding params %s"%k)
			pd = self.bdbs.paramdefs.get(k, txn=txn)
			self.bdbs.indexkeys.addrefs(k, v.keys(), txn=txn)
			#datatype=self.__cache_vartype_indextype.get(pd.vartype),



	#########################
	# section: Record Grouping Mechanisms
	#########################

	# ian: todo: medium: benchmark for new index system (01/10/2010)
	#@rename db.records.group @ok @multiple @return dict, k=group, v=set(recids)
	@publicmethod
	def groupbyrecorddef(self, recids, ctx=None, txn=None):
		"""This will take a set/list of record ids and return a dictionary of ids keyed by their recorddef

		@param recids

		@return dict, key is recorddef, value is set of recids
		"""

		ol, recids = listops.oltolist(recids)

		if len(recids) == 0:
			return {}

		if (len(recids) < 1000) or (isinstance(list(recids)[0],emen2.db.record.Record)):
			return self.__groupbyrecorddeffast(recids, ctx=ctx, txn=txn)

		# we need to work with a copy becuase we'll be changing it;
		# use copy.copy instead of list[:] because recids will usually be set()
		recids = copy.copy(recids)

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
		"""(Internal) Sometimes it's quicker to just get the records and filter, than to check all the indexes"""

		if not isinstance(list(records)[0],emen2.db.record.Record):
			records = self.getrecord(records, filt=1, ctx=ctx, txn=txn)

		ret={}
		for i in records:
			if not ret.has_key(i.rectype): ret[i.rectype]=set([i.recid])
			else: ret[i.rectype].add(i.recid)

		return ret




	###############################
	# section: relationships
	###############################


	#@rename db.<RelateBTree>.children
	#@single @notok @return set
	@publicmethod
	def getchildren(self, key, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get children.

		@param keys A Record ID, RecordDef name, or ParamDef name

		@keyparam keytype Children of type: record, paramdef, or recorddef
		@keyparam recurse Recursion level (default is 1, e.g. just immediate children)
		@keyparam rectype For Records, limit to a specific rectype

		@return Set of children
		"""
		# ok, some compatibility settings..
		# def getchildren(self, key, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		# def getchildren(self, key, keytype="record", recurse=1, rectype=None, filt=False, flat=False, tree=False):
		# recs = self.db.getchildren(self.recid, "record", self.options.get("recurse"), None, True, True)

		return self.__getrel_wrapper(keys=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", tree=False, ctx=ctx, txn=txn)


	# This is a new method -- might need some testing.
	@publicmethod
	def getsiblings(self, key, rectype=None, keytype="record", ctx=None, txn=None):
		parents = self.getparents(key, keytype=keytype, ctx=ctx, txn=txn)
		siblings = listops.combine(self.getchildren(parents, keytype=keytype, rectype=rectype, ctx=ctx, txn=txn).values(), dtype=list)
		if siblings:
			return siblings[0]
		return []


	#@rename db.<RelateBTree>.parents
	#@notok @single
	@publicmethod
	def getparents(self, key, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""See getchildren"""
		return self.__getrel_wrapper(keys=key, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", tree=False, ctx=ctx, txn=txn)


	#@multiple @notok @return dict
	@publicmethod
	def getchildtree(self, keys, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""Get multiple children for multiple items.

		@param keys Single or iterable key: Record IDs, RecordDef names, ParamDef names

		@keyparam keytype Children of type: record, paramdef, or recorddef
		@keyparam recurse Recursion level (default is 1, e.g. just immediate children)
		@keyparam rectype For Records, limit to a specific rectype

		@return Dict, keys are Record IDs or ParamDef/RecordDef names, values are sets of children for that key
		"""
		return self.__getrel_wrapper(keys=keys, keytype=keytype, recurse=recurse, rectype=rectype, rel="children", tree=True, ctx=ctx, txn=txn)


	#@multiple @notok
	@publicmethod
	def getparenttree(self, keys, recurse=1, rectype=None, keytype="record", ctx=None, txn=None):
		"""See getchildtree"""
		return self.__getrel_wrapper(keys=keys, keytype=keytype, recurse=recurse, rectype=rectype, rel="parents", tree=True, ctx=ctx, txn=txn)



	def __getrel_wrapper(self, keys, keytype="record", recurse=1, rectype=None, rel="children", tree=False, ctx=None, txn=None):
		"""(Internal) See getchildren/getparents, which are the wrappers/entry points for this method."""

		if recurse == -1:
			recurse = g.MAXRECURSE
		if recurse == False:
			recurse = True

		ol, keys = listops.oltolist(keys)

		__keytypemap = dict(
			record=self.bdbs.records,
			paramdef=self.bdbs.paramdefs,
			recorddef=self.bdbs.recorddefs
			)

		if keytype in __keytypemap:
			reldb = __keytypemap[keytype]
		else:
			raise ValueError, "Invalid keytype"


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
		if keytype=="record":
			allr &= self.filterbypermissions(allr, ctx=ctx, txn=txn)

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



	#@rename db.<RelateBTree>.pclinks
	#@multiple @ok
	@publicmethod
	def pclinks(self, links, keytype="record", ctx=None, txn=None):
		"""Create parent/child relationships. See pclink/pcunlink.

		@param links [[parent 1,child 1],[parent 2,child 2], ...]

		@keyparam keytype Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		return self.__link("pclink", links, keytype=keytype, ctx=ctx, txn=txn)



	#@rename db.<RelateBTree>.pcunlinks
	#@multiple @ok
	@publicmethod
	def pcunlinks(self, links, keytype="record", ctx=None, txn=None):
		"""Remove parent/child relationships. See pclink/pcunlink.

		@param links [[parent 1,child 1],[parent 2,child 2], ...]

		@keyparam keytype Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		return self.__link("pcunlink", links, keytype=keytype, ctx=ctx, txn=txn)



	#@rename db.<RelateBTree>.pclink
	#@single @ok
	@publicmethod
	def pclink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Establish a parent-child relationship between two keys.
		A context is required for record links, and the user must have write permission on at least one of the two.

		@param pkey Parent
		@param ckey Child

		@keyparam Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		return self.__link("pclink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	#@rename db.<RelateBTree>.pcunlink
	#@single @ok
	@publicmethod
	def pcunlink(self, pkey, ckey, keytype="record", ctx=None, txn=None):
		"""Remove a parent-child relationship between two keys.

		@param pkey Parent
		@param ckey Child

		@keyparam Link this type: ["record","paramdef","recorddef"] (default is "record")
		"""
		return self.__link("pcunlink", [(pkey, ckey)], keytype=keytype, ctx=ctx, txn=txn)



	def __link(self, mode, links, keytype="record", ctx=None, txn=None):
		"""(Internal) the *link functions wrap this."""
		#admin overrides security checks
		admin = False
		if ctx.checkadmin(): admin = True

		if keytype not in ["record", "recorddef", "paramdef"]:
			raise Exception, "pclink keytype must be 'record', 'recorddef' or 'paramdef'"

		if mode not in ["pclinks", "pclink","pcunlink","link","unlink"]:
			raise Exception, "Invalid relationship mode %s"%mode

		if not ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "linking mode %s requires record creation priveleges"%mode

		if filter(lambda x:x[0] == x[1], links):
			g.log.msg("LOG_ERROR","Cannot link to self: keytype %s, key %s <-> %s"%(keytype, pkey, ckey))
			return

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
		#	p = self.__getrel(key=pkey, keytype=keytype, recurse=g.MAXRECURSE, rel="parents")[0]
		#	c = self.__getrel(key=pkey, keytype=keytype, recurse=g.MAXRECURSE, rel="children")[0]
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

		self.__commit_link(keytype, mode, links, ctx=ctx, txn=txn)




	def __commit_link(self, keytype, mode, links, ctx=None, txn=None):
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

		#@begin

		if mode == "pclinks":
			linker(links, txn=txn)
		else:
			for pkey,ckey in links:
				g.log.msg("LOG_COMMIT","link: keytype %s, mode %s, pkey %s, ckey %s"%(keytype, mode, pkey, ckey))
				linker(pkey, ckey, txn=txn)

		#@end




	###############################
	# section: Admin User Management
	###############################


	#@rename db.users.disable
	#@multiple @ok
	@publicmethod
	@adminmethod
	def disableuser(self, usernames, filt=True, ctx=None, txn=None):
		return self.__setuserstate(usernames=usernames, disabled=True, filt=filt, ctx=ctx, txn=txn)



	#@rename db.users.enable
	#@multiple @ok
	@publicmethod
	@adminmethod
	def enableuser(self, usernames, filt=True, ctx=None, txn=None):
		"""Enable a disabled user.

		@param username

		@keyparam filt Ignore failures
		"""
		return self.__setuserstate(usernames=usernames, disabled=False, filt=filt, ctx=ctx, txn=txn)



	def __setuserstate(self, usernames, disabled, filt=True, ctx=None, txn=None):
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


		self.__commit_users(commitusers, ctx=ctx, txn=txn)

		t = "enabled"
		if disabled:
			t="disabled"

		ret = [user.username for user in commitusers]

		# g.log.msg('LOG_INFO', "Users %s %s by %s"%(ret, t, ctx.username))

		if ol: return return_first_or_none(ret)
		return ret



	#@rename db.users.approve
	#@multiple @ok
	@publicmethod
	@adminmethod
	def approveuser(self, usernames, filt=True, ctx=None, txn=None):
		"""Approve account in user queue

		@param usernames List of accounts to approve from new user queue

		@keyparam filt Ignore failures
		"""

		ol, usernames = listops.oltolist(usernames)

		# ian: I have turned secrets off for now until I can think about it some more..
		secret = None
		admin = ctx.checkadmin()

		if not admin:
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		delusers, records, childstore = {}, {}, {}
		addusers = []

		# Need to commit users before records will validate
		for username in usernames:

			try:
				user = self.bdbs.newuserqueue.sget(username, txn=txn)
				if not user:
					raise KeyError, "User %s is not pending approval"%username

				user.setContext(ctx)
				user.validate()
			except Exception, inst:
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise


			if self.bdbs.users.get(user.username, txn=txn):
				delusers[username] = None
				msg = "User %s already exists, deleted pending record"%user.username
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise KeyError, msg
				

			if self.bdbs.usersbyemail.get(user.email.lower(), txn=txn):
				delusers[username] = None
				msg = "The email address %s is already in use"%(user.email)
				if filt:
					g.log.msg("LOG_ERROR", msg)
					continue
				else:
					raise KeyError, msg
				
			# if secret is not None and not user.validate_secret(secret):
			# 	g.log.msg("LOG_ERROR","Incorrect secret for user %s; skipping"%username)
			# 	time.sleep(2)

			# clear out the secret
			user._User__secret = None
			addusers.append(user)
			delusers[username] = None


		# Update user queue / users
		self.__commit_users(addusers, ctx=ctx, txn=txn)
		self.__commit_newusers(delusers, ctx=ctx, txn=txn)

		# ian: todo: Do we need this root ctx? Probably...
		tmpctx = self.__makerootcontext(txn=txn)

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

		self.__commit_users(addusers, ctx=ctx, txn=txn)

		if user.username != 'root':
			for group in g.GROUP_DEFAULTS:
				gr = self.getgroup(group, ctx=tmpctx, txn=txn)
				if gr:
					gr.adduser(user.username)
					self.putgroup(gr, ctx=tmpctx, txn=txn)
				else:
					g.warn('Default Group %r is non-existent'%group)


		ret = [user.username for user in addusers]
		if ol: return return_first_or_none(ret)
		return ret



	#@rename db.users.reject
	#@multiple @filt @ok
	@publicmethod
	@adminmethod
	def rejectuser(self, usernames, filt=True, ctx=None, txn=None):
		"""Remove a user from the pending new user queue

		@param usernames List of usernames to reject from new user queue

		@keyparam filt Ignore failures
		"""

		ol, usernames = listops.oltolist(usernames)

		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		usernames = usernames
		delusers = {}

		for username in usernames:
			try:
				self.bdbs.newuserqueue.sget(username, txn=txn)
			except:
				if filt: continue
				else: raise KeyError, "User %s is not pending approval" % username

			delusers[username] = None

		self.__commit_newusers(delusers, ctx=ctx, txn=txn)

		ret = delusers.keys()
		if ol: return return_first_or_none(ret)
		return ret



	#@rename db.users.queue @ok
	@publicmethod
	@adminmethod
	def getuserqueue(self, ctx=None, txn=None):
		"""Returns a list of names of unapproved users

		@return list of names of approve users
		"""

		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators can approve new users"

		return set(self.bdbs.newuserqueue.keys(txn=txn))



	#@rename db.users.queue_get
	#@ok @single @return User
	@publicmethod
	@adminmethod
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




	#@ok @return User
	@publicmethod
	def newuser(self, username, password, email, ctx=None, txn=None):
		user = emen2.db.user.User(username=username, password=password, email=email)
		user.setContext(ctx)
		return user




	###############################
	# section: User Management
	###############################


	#@rename db.users.setprivacy @ok @return None
	@publicmethod
	def setprivacy(self, state, username=None, ctx=None, txn=None):
		"""Set privacy level for user information.

		@state 0, 1, or 2, in increasing level of privacy.

		@keyparam username Username to modify (admin only)
		"""

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise emen2.db.exceptions.SecurityError, "Cannot attempt to set other user's passwords"
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

		self.__commit_users(commitusers, ctx=ctx, txn=txn)


	



	#@rename db.users.setpassword @ok @return None
	@publicmethod
	def setpassword(self, oldpassword, newpassword, username=None, ctx=None, txn=None):
		"""Change password.

		@param oldpassword
		@param newpassword

		@keyparam username Username to modify (admin only)
		"""

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise emen2.db.exceptions.SecurityError, "Cannot attempt to set other user's passwords"
		else:
			username = ctx.username

		# ian: need to read directly because getuser hides password
		# user = self.getuser(username, ctx=ctx, txn=txn)
		user = self.bdbs.users.sget(username, txn=txn)
		user.setContext(ctx)

		if not user:
			raise emen2.db.exceptions.SecurityError, "Cannot change password for user '%s'"%username

		try:
			user.setpassword(oldpassword, newpassword)
		except:
			time.sleep(2)
			raise

		g.log.msg("LOG_SECURITY","Changing password for %s"%user.username)

		self.__commit_users([user], ctx=ctx, txn=txn)



	#@rename db.users.setemail @ok @return None
	@publicmethod
	def setemail(self, email, username=None, ctx=None, txn=None):
		"""Change email

		@param email

		@keyparam username Username to modify (Admin only)
		"""

		if username:
			if username != ctx.username and not ctx.checkadmin():
				raise emen2.db.exceptions.SecurityError, "You may only change your own email address"
		else:
			username = ctx.username

		user = self.getuser(username, ctx=ctx, txn=txn)
		user.email = email
		user.validate()

		if self.bdbs.usersbyemail.get(user.email.lower(), txn=txn):
			time.sleep(2)
			raise emen2.db.exceptions.SecurityError, "The email address %s is already in use"%(user.email)

		g.log.msg("LOG_INFO","Changing email for %s"%user.username)

		self.__commit_users([user], ctx=ctx, txn=txn)



	#@rename db.users.add @ok @return User
	@publicmethod
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

		assert hasattr(user, '_User__secret')

		if user.username != 'root':
			user.validate()

		self.__commit_newusers({user.username:user}, ctx=None, txn=txn)

		if ctx.checkadmin():
			self.approveuser(user.username, ctx=ctx, txn=txn)

		return user



	#@write #self.bdbs.users
	def __commit_users(self, users, ctx=None, txn=None):
		"""(Internal) Updates user. Takes validated User. Deprecated for non-administrators."""

		#@begin
		for user in users:
			
			ouser = self.bdbs.users.get(user.username, txn=txn)
			
			self.bdbs.users.set(user.username, user, txn=txn)
			g.log.msg("LOG_COMMIT","self.bdbs.users.set: %r"%user.username)

			try:
				oldemail = ouser.email
			except:
				oldemail = ''
				
			if oldemail != user.email:
				# g.log.msg("LOG_COMMIT_INDEX","self.bdbs.usersbyemail: %r"%user.username)
				self.bdbs.usersbyemail.addrefs(user.email.lower(), [user.username], txn=txn)
				self.bdbs.usersbyemail.removerefs(oldemail.lower(), [user.username], txn=txn)

		#@end



	#@write #self.bdbs.newuserqueue
	def __commit_newusers(self, users, ctx=None, txn=None):
		"""(Internal) Write to newuserqueue; users is dict; set value to None to del"""

		#@begin
		for username, user in users.items():
			if user:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.set: %r"%username)
			else:
				g.log.msg("LOG_COMMIT","self.bdbs.newuserqueue.set: %r, deleting"%username)

			self.bdbs.newuserqueue.set(username, user, txn=txn)
		#@end




	#@rename db.users.get
	#@multiple filt @ok @return User or [User...]
	@publicmethod
	def getuser(self, usernames, filt=True, lnf=False, getgroups=False, getrecord=True, ctx=None, txn=None):
		"""Get user information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record

		@param usernames A username, list of usernames, record, or list of records

		@keyparam filt Ignore failures
		@keyparam lnf Get user 'display name' as Last Name First (default=False)
		@keyparam getgroups Include user groups (default=False)
		@keyparam getrecord Include user information (default=True)

		@return Dict of users, keyed by username
		"""

		ol, usernames = listops.oltolist(usernames)

		# Are we looking for users referenced in records?
		recs = [x for x in usernames if isinstance(x, emen2.db.record.Record)]
		rec_ints = [x for x in usernames if isinstance(x, int)]

		if rec_ints:
			recs.extend(self.getrecord(rec_ints, filt=True, ctx=ctx, txn=txn))

		if recs:
			un2 = self.filtervartype(recs, vts=["user","userlist","acl"], flat=True, ctx=ctx, txn=txn)
			usernames.extend(un2)

		# Check list of users
		usernames = set(x for x in usernames if isinstance(x, basestring))

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

			user.getuserrec(lnf=lnf)
			user.password = None
			ret.append(user)

		if ol: return return_first_or_none(ret)
		return ret





	#@rename db.users.list @ok @return set
	@publicmethod
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


	#@rename db.groups.list @ok @return set
	@publicmethod
	def getgroupnames(self, ctx=None, txn=None):
		"""Return a set of all group names

		@return set of all group names
		"""
		return set(self.bdbs.groups.keys(txn=txn))



	#@rename db.groups.get
	#@multiple @filt @ok @return Group or [Group..]
	@publicmethod
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
	def __commit_groupsbyuser(self, addrefs=None, delrefs=None, ctx=None, txn=None):
		"""(Internal) Update groupbyuser index"""

		#@begin

		for user,groups in addrefs.items():
			try:
				if groups:
					# g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser key: %r, addrefs: %r"%(user, groups))
					self.bdbs.groupsbyuser.addrefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update self.bdbs.groupsbyuser key: %s, addrefs %s"%(user, groups))
				raise

		for user,groups in delrefs.items():
			try:
				if groups:
					# g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser key: %r, removerefs: %r"%(user, groups))
					self.bdbs.groupsbyuser.removerefs(user, groups, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update self.bdbs.groupsbyuser key: %s, removerefs %s"%(user, groups))
				raise


		#@end



	#@write self.bdbs.groupsbyuser
	def __rebuild_groupsbyuser(self, ctx=None, txn=None):
		"""(Internal) Rebuild groupbyuser index"""

		groups = self.getgroup(self.getgroupnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		users = collections.defaultdict(set)

		for group in groups:
			for user in group.members():
				users[user].add(group.name)

		#@begin
		# g.log.msg("LOG_INDEX","self.bdbs.groupsbyuser: rebuilding index")

		self.bdbs.groupsbyuser.truncate(txn=txn)

		for k,v in users.items():
			self.bdbs.groupsbyuser.addrefs(k, v, txn=txn)

		#@end



	def __rebuild_usersbyemail(self, ctx=None, txn=None):
		usernames = self.getusernames(ctx=ctx, txn=txn)
		users = self.getuser(usernames, ctx=ctx, txn=txn)

		self.bdbs.usersbyemail.truncate(txn=txn)
		for user in users:
			self.bdbs.usersbyemail.addrefs(user.email.lower(), [user.username], txn=txn)
			


	def __reindex_groupsbyuser(self, groups, ctx=None, txn=None):
		"""(Internal) Reindex a group's members for the groupsbyuser index"""

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


	@publicmethod
	def newgroup(self, ctx=None, txn=None):
		group = emen2.db.group.Group()
		group.adduser(ctx.username, level=3)
		group.setContext(ctx)
		return group



	#@rename db.groups.put @ok
	#@multiple @return Group or [Group..]
	@publicmethod
	def putgroup(self, groups, ctx=None, txn=None):
		"""Commit changes to a group or groups.

		@param groups A single or iterable Group

		@return Modified Group or Groups
		"""

		ol, groups = listops.oltolist(groups)
		admin = ctx.checkcreate()

		groups2 = []

		groups2.extend(x for x in groups if isinstance(x, emen2.db.group.Group))
		groups2.extend(emen2.db.group.Group(x, ctx=ctx) for x in groups if isinstance(x, dict))

		for group in groups2:
			group.setContext(ctx)
			group.validate(txn=txn)
			try: og = self.getgroup(group.name, ctx=ctx, txn=txn, filt=False)
			except KeyError:
				if not admin:
					raise emen2.db.exceptions.SecurityError, "Insufficient permissions to create a group"


		self.__commit_groups(groups2, ctx=ctx, txn=txn)

		if ol: return return_first_or_none(groups2)
		return groups2



	def __commit_groups(self, groups, ctx=None, txn=None):
		"""(Internal) see putgroup """

		addrefs, delrefs = self.__reindex_groupsbyuser(groups, ctx=ctx, txn=txn)

		#@begin
		for group in groups:
			# g.log.msg("LOG_COMMIT","self.bdbs.groups.set: %r"%(group))
			self.bdbs.groups.set(group.name, group, txn=txn)

		self.__commit_groupsbyuser(addrefs=addrefs, delrefs=delrefs, ctx=ctx, txn=txn)
		#@end



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
	# #@write #self.bdbs.workflow
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
	# #@write #self.bdbs.workflow
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
	# #@write #self.bdbs.workflow
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
	# def __commit_workflow(self, wfs, ctx=None, txn=None):
	# 	pass




	#########################
	# section: paramdefs
	#########################


	#@rename db.paramdefs.vartypes.list @ok @return set
	@publicmethod
	def getvartypenames(self, ctx=None, txn=None):
		"""Returns a list of all valid variable types.

		@return Set of vartypes
		"""
		return set(self.vtm.getvartypes())




	#@rename db.paramdefs.properties.get @ok
	@publicmethod
	def getpropertynames(self, ctx=None, txn=None):
		"""Return a list of all valid properties.

		@return list of properties
		"""
		return set(self.vtm.getproperties())



	#@rename db.paramdefs.properties.units @ok
	@publicmethod
	def getpropertyunits(self, propname, ctx=None, txn=None):
		"""Returns a list of known units for a particular property

		@param propname Property name

		@return a set of known units for property
		"""
		# set(vtm.getproperty(propname).units) | set(vtm.getproperty(propname).equiv)
		return set(self.vtm.getproperty(propname).units)



	#@notok @return ParamDef
	@publicmethod
	def newparamdef(self, ctx=None, txn=None):
		pd = emen2.db.paramdef.ParamDef()
		pd.setContext(ctx)
		return pd



	#@rename db.paramdefs.put @return ParamDef
	#@single @ok
	@publicmethod
	def putparamdef(self, paramdef, parents=None, children=None, ctx=None, txn=None):
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
			g.log.msg("LOG_CRITICAL","WARNING! Changing paramdef %s vartype from %s to %s. This MAY REQUIRE database revalidation and reindexing!!"%(paramdef.name, paramdef.vartype, paramdef.vartype))

		# These are not allowed to be changed
		paramdef.creator = orec.creator
		paramdef.creationtime = orec.creationtime
		paramdef.uri = orec.uri

		paramdef.validate()

		######### ^^^ ############

		self.__commit_paramdefs([paramdef], ctx=ctx, txn=txn)

		# create the index for later use
		# paramindex = self.__getparamindex(paramdef.name, create=True, ctx=ctx, txn=txn)

		# If parents or children are specified, add these relationships
		links = []
		if parents:
			links.extend( map(lambda x:(x, paramdef.name), parents) )
		if children:
			links.extend( map(lambda x:(paramdef.name, x), children) )
		if links:
			self.pclinks(links, keytype="paramdef", ctx=ctx, txn=txn)

		return paramdef



	def __commit_paramdefs(self, paramdefs, ctx=None, txn=None):
		"""(Internal) Commit paramdefs"""

		#@begin
		for paramdef in paramdefs:
			g.log.msg("LOG_COMMIT","self.bdbs.paramdefs.set: %r"%paramdef.name)
			self.bdbs.paramdefs.set(paramdef.name, paramdef, txn=txn)
		#@end




	#@rename db.paramdefs.gets @notok @multiple @return ParamDef or [ParamDef..]
	@publicmethod
	def getparamdef(self, keys, filt=True, ctx=None, txn=None):
		"""Get ParamDefs

		@param recs ParamDef name, list of names, a Record, or list of Records

		@keyparam filt Ignore failures

		@return A ParamDef or list of ParamDefs
		"""

		ol, keys = listops.oltolist(keys)

		params = set(filter(lambda x:isinstance(x, basestring), keys))

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



	#@rename db.paramdefs.list @ok
	@publicmethod
	def getparamdefnames(self, ctx=None, txn=None):
		"""Return a list of all ParamDef names

		@return set of all ParamDef names
		"""
		return set(self.bdbs.paramdefs.keys(txn=txn))



	def __getparamindex(self, paramname, ctx=None, txn=None):
		"""(Internal) Return handle to param index"""

		create = True

		try:
			return self.bdbs.fieldindex[paramname] # [paramname]				# Try to get the index for this key
		except Exception, inst:
			pass

		f = self.bdbs.paramdefs.sget(paramname, txn=txn) #[paramname]				 # Look up the definition of this field
		paramname = f.name

		if f.vartype not in self.indexablevartypes or not f.indexed:
			return None

		tp = self.vtm.getvartype(f.vartype).getindextype()

		if not create and not os.access("index/params/%s.bdb"%(paramname), os.F_OK):
			raise KeyError, "No index for %s" % paramname

		# opens with autocommit, don't need to pass txn
		self.bdbs.openparamindex(paramname, keytype=tp, dbenv=self.dbenv)

		return self.bdbs.fieldindex[paramname]




	#########################
	# section: recorddefs
	#########################


	#@notok @return RecordDef
	@publicmethod
	def newrecorddef(self, ctx=None, txn=None):
		rd = emen2.db.recorddef.RecordDef(ctx=ctx)
		rd.setContext(ctx)
		return rd



	#@single
	#@rename db.recorddefs.put @ok @return RecordDef
	@publicmethod
	def putrecorddef(self, recdef, parents=None, children=None, ctx=None, txn=None):
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
		self.__commit_recorddefs([recdef], ctx=ctx, txn=txn)

		links = []
		if parents:
			links.extend( map(lambda x:(x, recdef.name), parents) )
		if children:
			links.extend( map(lambda x:(recdef.name, x), children) )
		if links:
			self.pclinks(links, keytype="recorddef", ctx=ctx, txn=txn)

		return recdef



	# @rename db.recorddefs.puts
	# @publicmethod
	# def putrecorddefs(self, recdef, parents=None, children=None, ctx=None, txn=None):



	def __commit_recorddefs(self, recorddefs, ctx=None, txn=None):
		"""(Internal) Commit RecordDefs"""

		#@begin
		for recorddef in recorddefs:
			g.log.msg("LOG_COMMIT","self.bdbs.recorddefs.set: %r"%recorddef.name)
			self.bdbs.recorddefs.set(recorddef.name, recorddef, txn=txn)
		#@end



	#@rename db.recorddefs.get
	#@multiple @filt @notok @return RecordDef or [RecordDef..]
	@publicmethod
	def getrecorddef(self, keys, filt=True, recid=None, ctx=None, txn=None):
		"""Retrieves a RecordDef object. This will fail if the RecordDef is
		private, unless the user is an owner or	 in the context of a recid the
		user has permission to access.

		@param rdids A RecordDef name, an iterable of RecordDef names, a Record ID, or list of Record IDs

		@keyparam filt Ignore failures
		@keyparam recid For private RecordDefs, provide a readable Record ID of this type to gain access

		@return A RecordDef or list of RecordDefs
		"""

		ol, keys = listops.oltolist(keys)

		recdefs = set(filter(lambda x:isinstance(x, basestring), keys))

		# Find recorddefs record ID
		recs = filter(lambda x:isinstance(x, (dict, emen2.db.record.Record)), keys)
		recids = [i.get('recid') for i in recs]
		recids.extend(filter(lambda x:isinstance(x, int), keys))
		if recid:
			recids.append(recid)

		recs = self.getrecord(recids, ctx=ctx, txn=txn)
		groups = listops.groupbykey(recs, 'rectype')
		recdefs |= set(groups.keys())
		recs = listops.dictbykey(recs, 'recid')

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



	#@rename db.recorddefs.list @ok @return set
	@publicmethod
	def getrecorddefnames(self, ctx=None, txn=None):
		"""This will retrieve a list of all existing RecordDef names, even those the user cannot access

		@return set of RecordDef names

		"""
		return set(self.bdbs.recorddefs.keys(txn=txn))




	#########################
	# section: records
	#########################


	#@rename db.records.get @return Record or [Record..]
	#@multiple @filt @ok
	@publicmethod
	def getrecord(self, recids, filt=True, writable=None, owner=None, ctx=None, txn=None):
		"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.

		@param recids Record ID or iterable of Record IDs

		@keyparam filt Ignore failures

		@return Record or list of Records
		"""

		ol, recids = listops.oltolist(recids)
		ret = []
		# if filt: lfilt = self.bdbs.records.get....

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

		if owner:
			ret = filter(lambda x:x.isowner(), ret)				

		if ol:
			return return_first_or_none(ret)
		return ret



	# ian: todo: medium: allow to copy existing record
	#@rename db.records.new @ok @return Record
	@publicmethod
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
		if init:
			rec.update(t)

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
	def __getparamdefnamesbyvartype(self, vts, paramdefs=None, ctx=None, txn=None):
		"""(Internal) As implied, get paramdef names by vartype"""

		if not hasattr(vts,"__iter__"): vts = [vts]

		if not paramdefs:
			paramdefs = self.getparamdef(self.getparamdefnames(ctx=ctx, txn=txn), ctx=ctx, txn=txn)

		return [x.name for x in paramdefs if x.vartype in vts]




	# ian: this might be helpful
	# e.g.: filtervartype(136, ["user","userlist"])
	# ian: todo: make this much faster, or drop it.. @ok
	#@rename db.records.filter.vartype @return set
	@publicmethod
	def filtervartype(self, recs, vts, filt=True, flat=0, ctx=None, txn=None):
		"""This is deprecated. Consider it semi-internal."""

		result = [None]
		if recs:
			recs2 = []

			# process recs arg into recs2 records, process params by vartype, then return either a dict or list of values; ignore those specified
			ol = 0
			if isinstance(recs,(int,emen2.db.record.Record)):
				ol = 1
				recs = [recs]

			# get the records...
			recs2.extend(filter(lambda x:isinstance(x,emen2.db.record.Record),recs))
			recs2.extend(self.getrecord(filter(lambda x:isinstance(x,int),recs), filt=filt, ctx=ctx, txn=txn))

			params = self.__getparamdefnamesbyvartype(vts, ctx=ctx, txn=txn)

			result = [[rec.get(pd) for pd in params if rec.get(pd)] for rec in recs2]

		params = self.__getparamdefnamesbyvartype(vts, ctx=ctx, txn=txn)
		re = [[rec.get(pd) for pd in params if rec.get(pd)] for rec in recs2]

		if flat:
			# ian: todo: medium: replace this with something faster
			# the reason flatten is used because some vartypes are nested lists, e.g. permissions.
			re = self.__flatten(re)
			return set(re)-set([None])

		return re



	#@rename db.records.check.orphans @ok @return set
	@publicmethod
	def checkorphans(self, recid, ctx=None, txn=None):
		"""Find orphaned records that would occur if recid was deleted.

		@param recid Return orphans that would result from deletion of this Record

		@return Set of orphaned Record IDs
		"""
		srecid = set([recid])
		saved = set()

		# this is hard to calculate
		children = self.getchildtree(recid, recurse=-1, ctx=ctx, txn=txn)
		orphaned = reduce(set.union, children.values(), set())
		orphaned.add(recid)
		parents = self.getparenttree(orphaned, ctx=ctx, txn=txn)

		# orphaned is records that will be orphaned if they are not rescued
		# find subtrees that will be rescued by links to other places
		for child in orphaned - srecid:
			if parents.get(child, set()) - orphaned:
				saved.add(child)

		children_saved = self.getchildtree(saved, recurse=-1, ctx=ctx, txn=txn)
		children_saved_set = set()
		for i in children_saved.values() + [set(children_saved.keys())]:
			children_saved_set |= i
		# .union( *(children_saved.values()+[set(children_saved.keys())], set()) )

		orphaned -= children_saved_set

		return orphaned




	#@rename db.records.delete
	#@single @ok @return Record
	@publicmethod
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
			rec.addcomment("Record marked for deletion and unlinked from parents: %s"%", ".join([unicode(x) for x in parents]))

		elif rec.get("deleted") != 1:
			rec.addcomment("Record marked for deletion")

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


	#@rename db.records.comments.add @ok @return Record
	@publicmethod
	def addcomment(self, recid, comment, ctx=None, txn=None):
		"""Add comment to a record. Requires comment permissions on that Record.

		@param recid
		@param comment

		@return Updated Record
		"""

		# g.log.msg("LOG_DEBUG","addcomment %s %s"%(recid, comment))
		rec = self.getrecord(recid, filt=False, ctx=ctx, txn=txn)
		rec.addcomment(comment)
		self.putrecord(rec, ctx=ctx, txn=txn)

		return self.getrecord(recid, ctx=ctx, txn=txn) #["comments"]



	#@rename db.records.comments.get
	#@multiple @filt @ok @return list
	@publicmethod
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

	#@notok
	@publicmethod
	def publish(self, recids, ctx=None, txn=None):
		pass



	#@rename db.records.putvalue
	#@single @ok
	@publicmethod
	def putrecordvalue(self, recid, param, value, ctx=None, txn=None):
		"""Convenience method to update a single value in a record

		@param recid Record ID
		@param param Parameter
		@param value New value

		@return Updated Record
		"""

		rec = self.getrecord(recid, filt=False, ctx=ctx, txn=txn)
		rec[param] = value
		self.putrecord(rec, ctx=ctx, txn=txn)
		return self.getrecord(recid, ctx=ctx, txn=txn) #.get(param)





	# ian: todo: merge this with putrecordvalues
	#@rename db.records.putsvalues
	#@multiple @ok @return Record or [Record..]
	@publicmethod
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



	#@rename db.records.validate @ok
	@publicmethod
	def validaterecord(self, rec, ctx=None, txn=None):
		"""Check that a record will validate before committing.

		@param recs Record or iterable of Records

		@return Validated Records
		"""

		return self.putrecord(rec, commit=False, ctx=ctx, txn=txn)




	#@rename db.records.put
	#@multiple @ok
	@publicmethod
	def putrecord(self, recs, warning=0, commit=True, ctx=None, txn=None):
		"""Commit records

		@param recs Record or iterable Records
		@keyparam warning Bypass validation (Admin only)
		@keyparam commit If False, do not actually commit (e.g. for valdiation)

		@return Committed records

		@exception SecurityError, DBError, KeyError, ValueError, TypeError..
		"""
		
		ol, recs = listops.oltolist(recs)
		
		if warning and not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only administrators may bypass validation"

		# Preprocess
		recs.extend(emen2.db.record.Record(x, ctx=ctx) for x in listops.typefilter(recs, dict))
		recs = listops.typefilter(recs, emen2.db.record.Record)
		
		
		ret = self.__putrecord(recs, warning=warning, commit=commit, ctx=ctx, txn=txn)

		if ol: return return_first_or_none(ret)
		return ret



	# And now, a long parade of internal putrecord methods
	def __putrecord(self, updrecs, warning=0, commit=True, ctx=None, txn=None):
		"""(Internal) Proess records for committing. If anything is wrong, raise an Exception, which will cancel the
			operation and usually the txn. If OK, then proceed to write records and all indexes. At that point, only
			really serious DB errors should ever occur."""

		crecs = []
		updrels = []

		# These are built-ins that we treat specially
		param_immutable = set(["recid","rectype","creator","creationtime","modifytime","modifyuser"])
		param_special = param_immutable | set(["comments","permissions","groups","history"])

		# Assign temp recids to new records
		# ian: changed to x.recid == None to preserve trees in uncommitted records
		for offset,updrec in enumerate(x for x in updrecs if x.recid == None):
			updrec.recid = -1 * (offset + 100)

		# Check 'parent' and 'children' special params
		updrels = self.__putrecord_getupdrels(updrecs, ctx=ctx, txn=txn)

		# Assign all changes the same time
		t = self.gettime(ctx=ctx, txn=txn)

		
		validation_cache = emen2.db.record.make_cache()
		
		# preprocess: copy updated record into original record (updrec -> orec)
		for updrec in updrecs:
			recid = updrec.recid

			if recid < 0:
				orec = self.newrecord(updrec.rectype, recid=updrec.recid, ctx=ctx, txn=txn)

			else:
				# we need to acquire RMW lock here to prevent changes during commit
				#elif self.bdbs.records.exists(updrec.recid, txn=txn, flags=g.RMWFLAGS):
				try:
					orec = self.bdbs.records.sget(updrec.recid, txn=txn, flags=g.RMWFLAGS)
					orec.setContext(ctx)
				except:
					raise KeyError, "Cannot update non-existent record %s"%recid


			# Set Context and validate; warning=True ignores validation errors (Admin only)
			updrec.setContext(ctx)
			updrec.validate(orec=orec, warning=warning, cache=validation_cache)

			# Compare to original record
			cp = orec.changedparams(updrec) - param_immutable

			# orec.recid < 0 because new records will always be committed, even if skeletal
			if not cp and orec.recid >= 0:
				g.log.msg("LOG_DEBUG","putrecord: No changes for record %s, skipping"%recid)
				continue

			# ian: todo: have records be able to update themselves from another record

			# This adds text of comment as new to prevent tampering
			if "comments" in cp:
				for i in updrec["comments"]:
					if i not in orec._Record__comments:
						orec.addcomment(i[2])

			# Update params
			for param in cp - param_special:
				# Logging handled inside Record now
				orec[param] = updrec.get(param)

			# Update permissions / groups
			if "permissions" in cp:
				orec.setpermissions(updrec.get("permissions"))
			if "groups" in cp:
				orec.setgroups(updrec.get("groups"))

			# ian: we have to set these manually for now...
			orec._Record__params["modifytime"] = t
			orec._Record__params["modifyuser"] = ctx.username

			# having validation at the top lets us only eval what changes, usually
			# if validate:
			# 	orec.validate(orec=orcp, warning=warning, params=cp)

			crecs.append(orec)

		return self.__commit_records(crecs, updrels, commit=commit, ctx=ctx, txn=txn)



	def __putrecord_getupdrels(self, updrecs, ctx=None, txn=None):
		"""(Internal) Get relationships from parents/children params of Records"""

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
	def __commit_records(self, crecs, updrels=[], onlypermissions=False, reindex=False, commit=True, ctx=None, txn=None):
		"""(Internal) Actually commit Records... This is the last step of several in the process.
		onlypermissions and reindex are used for some internal record updates, e.g. permissions, and save some work. USE CAREFULLY.
		commit=False aborts before writing begins but after all updates are calculated
		"""

		rectypes = collections.defaultdict(list)
		newrecs = [x for x in crecs if x.recid < 0]
		recmap = {}

		# Fetch the old records for calculating index updates. Set RMW flags.
		# To force reindexing (e.g. to rebuild indexes) treat as new record
		cache = {}
		for i in crecs:
			#print "checking %s"%i.recid
			if reindex or i.recid < 0:
				continue
			try:
				orec = self.bdbs.records.sget(i.recid, txn=txn, flags=g.RMWFLAGS) # [recid]
			except:
				orec = {}
			cache[i.recid] = orec

		#print "calculating index updates"

		# Calculate index updates. Shortcut if we're only modifying permissions. Use with caution.
		indexupdates = {}
		if not onlypermissions:
			indexupdates = self.__reindex_params(crecs, cache=cache, ctx=ctx, txn=txn)
		secr_addrefs, secr_removerefs = self.__reindex_security(crecs, cache=cache, ctx=ctx, txn=txn)
		secrg_addrefs, secrg_removerefs = self.__reindex_security_groups(crecs, cache=cache, ctx=ctx, txn=txn)


		# If we're just validating, exit here..
		if not commit:
			return crecs


		# OK, all go to write records/indexes!

		#@begin
		
		# Reassign new record IDs and update record counter
		# BTree may use DBSequences at some point in the future, if it's ever stable
		if newrecs:
			baserecid = self.bdbs.records.get_sequence(delta=len(newrecs), txn=txn)
			g.log.msg("LOG_DEBUG","Setting recid counter: %s -> %s"%(baserecid, baserecid + len(newrecs)))


		# add recids to new records, create map from temp recid to real recid, setup index
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
		"""(Internal) Update self.bdbs.recorddefindex"""

		if not recmap: recmap = {}

		for rectype,recs in rectypes.items():
			try:
				# g.log.msg("LOG_INDEX","self.bdbs.recorddefindex.addrefs: %r, %r"%(rectype, recs))
				self.bdbs.recorddefindex.addrefs(rectype, recs, txn=txn)

			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update recorddef index: rectype %s, records: %s (%s)"%(rectype, recs, inst))
				raise



	#@write #self.bdbs.secrindex
	def __commit_secrindex(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):
		"""(Internal) Update self.bdbs.secrindex"""

		if not recmap: recmap = {}

		for user, recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				# g.log.msg("LOG_INDEX","self.bdbs.secrindex.addrefs: %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex.addrefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not add security index for user %s, records %s (%s)"%(user, recs, inst))
				raise

		for user, recs in removerefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				# g.log.msg("LOG_INDEX","secrindex.removerefs: user %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex.removerefs(user, recs, txn=txn)
			except bsddb3.db.DBError, inst:
				g.log.msg("LOG_CRITICAL", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
				raise
			except Exception, inst:
				g.log.msg("LOG_ERROR", "Could not remove security index for user %s, records %s (%s)"%(user, recs, inst))
				raise



	#@write #self.bdbs.secrindex
	def __commit_secrindex_groups(self, addrefs, removerefs, recmap=None, ctx=None, txn=None):
		"""(Internal) Update self.bdbs.secrindex_groups"""

		if not recmap: recmap = {}

		for user, recs in addrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				# g.log.msg("LOG_INDEX","self.bdbs.secrindex_groups.addrefs: %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex_groups.addrefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not add security index for group %s, records %s (%s)"%(user, recs, inst))
				raise

		for user, recs in removerefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				g.log.msg("LOG_INDEX","secrindex_groups.removerefs: user %r, len %r"%(user, len(recs)))
				self.bdbs.secrindex_groups.removerefs(user, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not remove security index for group %s, records %s (%s)"%(user, recs, inst))
				raise



	#@write #self.bdbs.fieldindex*
	def __commit_paramindex(self, param, addrefs, delrefs, recmap=None, ctx=None, txn=None):
		"""(Internal) commit param updates"""

		if not recmap: recmap = {}

		addindexkeys = []
		delindexkeys = []

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
					# g.log.msg("LOG_INDEX","param index %r.addrefs: %r '%r', %r"%(param, type(newval), newval, len(recs)))
					addindexkeys = paramindex.addrefs(newval, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update param index %s: addrefs %s '%s', records %s (%s)"%(param,type(newval), newval, len(recs), inst))
				raise

		for oldval,recs in delrefs.items():
			recs = map(lambda x:recmap.get(x,x), recs)
			try:
				if recs:
					# g.log.msg("LOG_INDEX","param index %r.removerefs: %r '%r', %r"%(param, type(oldval), oldval, len(recs)))
					delindexkeys = paramindex.removerefs(oldval, recs, txn=txn)
			except Exception, inst:
				g.log.msg("LOG_CRITICAL", "Could not update param index %s: removerefs %s '%s', records %s (%s)"%(param,type(oldval), oldval, len(recs), inst))
				raise


		# Update index-index, a necessary evil..
		self.bdbs.indexkeys.addrefs(param, addindexkeys, txn=txn)
		self.bdbs.indexkeys.removerefs(param, delindexkeys, txn=txn)



	# These methods calculate what index updates to make

	# ian: todo: merge all the __reindex_params together...
	def __reindex_params(self, updrecs, cache=None, ctx=None, txn=None):
		"""(Internal) update param indices"""

		# g.log.msg('LOG_DEBUG', "Calculating param index updates...")

		if not cache: cache = {}
		ind = collections.defaultdict(list)
		indexupdates = {}

		# ian: todo: this is handled gracefully by openparamindex now
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
		"""(Internal) calculate param index updates"""

		# items format:
		# [recid, newval, oldval]
		pd = self.bdbs.paramdefs.sget(key, txn=txn) # [key]
		addrefs = {}
		delrefs = {}

		if pd.vartype not in self.indexablevartypes or not pd.indexed:
			return addrefs, delrefs

		# remove oldval=newval; strip out wrong keys
		items = filter(lambda x:x[1] != x[2], items)

		result = None
		if pd.vartype == "text":
			addrefs, delrefs = self.__reindex_paramtext(key, items, ctx=ctx, txn=txn)
		else:

			addrefs = collections.defaultdict(set)
			delrefs = collections.defaultdict(set)

			for recid, new, old in items:
				if not hasattr(new, '__iter__'): new = [new]
				for n in new:
					addrefs[n].add(recid)
				if not hasattr(old, '__iter__'): old = [old]
				for o in old:
					delrefs[o].add(recid)

			if None in addrefs: del addrefs[None]
			if None in delrefs: del delrefs[None]

		return addrefs, delrefs



	def __reindex_paramtext(self, key, items, ctx=None, txn=None):
		"""(Internal) calculate param index updates for vartype == text"""

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
		"""(Internal) Split up a text param into components"""
		if value == None: return []
		value = unicode(value).lower()
		return set((x[0] or x[1]) for x in self.__reindex_getindexwords_m.findall(value))



	def __reindex_security(self, updrecs, cache=None, ctx=None, txn=None):
		"""(Internal) Calculate secrindex updates"""

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
		"""(Internal) Calculate secrindex_groups updates"""

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
		"""(Internal) Rebuild all indexes. This should only be used if you blow something up, change a paramdef vartype, etc.
		It might test the limits of your Berkeley DB configuration and fail if the resources are too low."""

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
				# g.log.msg('LOG_DEBUG', paramindex)
				try:
					paramindex.truncate(txn=txn)
				except Exception, e:
					g.log.msg("LOG_INFO","Couldn't truncate %s: %s"%(param, e))
				paramindexes[param] = paramindex


		g.log.msg("LOG_INFO","Done truncating all indexes")

		self.__rebuild_groupsbyuser(ctx=ctx, txn=txn)

		self.__rebuild_usersbyemail(ctx=ctx, txn=txn)

		maxrecords = self.bdbs.records.get_max(txn=txn) #get(-1, txn=txn)["max"]
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
		"""(Internal) Rebuild self.bdbs.secrindex and self.bdbs.secrindex_groups"""

		g.log.msg("LOG_INFO","Rebuilding secrindex/secrindex_groups")

		g.log.msg("LOG_INFO","self.bdbs.secrindex.truncate")
		self.bdbs.secrindex.truncate(txn=txn)

		g.log.msg("LOG_INFO","self.bdbs.secrindex_groups.truncate")
		self.bdbs.secrindex_groups.truncate(txn=txn)

		pos = 0
		crecs = True
		recmap = {}
		maxrecords = self.bdbs.records.get_max(txn=txn)


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
	#@rename db.records.permissions.filter
	#@multiple @ok @return set
	@publicmethod
	def filterbypermissions(self, recids, ctx=None, txn=None):
		"""Filter a list of Record IDs by read permissions.

		@param recids Iterable of Record IDs
		@return Set of accessible Record IDs
		"""

		if ctx.checkreadadmin():
			return set(recids)

		ol, recids = listops.oltolist(recids, dtype=set)

		# ian: indexes are now faster, generally...
		if len(recids) < 100:
			return set([x.recid for x in self.getrecord(recids, filt=True, ctx=ctx, txn=txn)])

		find = copy.copy(recids)
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



	#@rename db.records.permissions.compat_add @ok
	@publicmethod
	def secrecordadduser_compat(self, umask, recid, recurse=0, reassign=False, delusers=None, addgroups=None, delgroups=None, ctx=None, txn=None):
		"""Legacy permissions method.
		@param umask Add this user mask to the specified recid, and child records to recurse level
		@param recid Record ID to modify
		@keyparam recurse
		@keyparam reassign
		@keyparam delusers
		@keyparam addgroups
		@keyparam delgroups
		"""
		return self.__putrecord_setsecurity(recids=[recid], umask=umask, addgroups=addgroups, recurse=recurse, reassign=reassign, delusers=delusers, delgroups=delgroups, ctx=ctx, txn=txn)


	#@multiple @filt
	#@rename db.records.permissions.add @notok
	@publicmethod
	def addpermissions(self, recids, users, level=0, recurse=0, reassign=False, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids=recids, addusers=users, addlevel=level, recurse=recurse, reassign=reassign, ctx=ctx, txn=txn)


	#@multiple @filt
	#@rename db.records.permissions.remove @notok
	@publicmethod
	def removepermissions(self, recids, users, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids=recids, delusers=users, recurse=recurse, ctx=ctx, txn=txn)


	#@multiple @filt
	#@rename db.records.permissions.addgroup @notok
	@publicmethod
	def addgroups(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids=recids, addgroups=groups, recurse=recurse, ctx=ctx, txn=txn)


	#@multiple @filt
	#@rename db.records.permissions.removegroup @notok
	@publicmethod
	def removegroups(self, recids, groups, recurse=0, ctx=None, txn=None):
		return self.__putrecord_setsecurity(recids=recids, delgroups=groups, recurse=recurse, ctx=ctx, txn=txn)


	def __putrecord_setsecurity(self, recids=None, addusers=None, addlevel=0, addgroups=None, delusers=None, delgroups=None, umask=None, recurse=0, reassign=False, filt=True, ctx=None, txn=None):

		if recurse == -1:
			recurse = g.MAXRECURSE

		recids = listops.tolist(recids or set(), dtype=set)
		addusers = listops.tolist(addusers or set(), dtype=set)
		addgroups = listops.tolist(addgroups or set(), dtype=set)
		delusers = listops.tolist(delusers or set(), dtype=set)
		delgroups = listops.tolist(delgroups or set(), dtype=set)

		if not umask:
			umask = [[],[],[],[]]
			if addusers:
				umask[addlevel] = addusers

		addusers = set(reduce(operator.concat, umask, []))

		checkitems = self.getusernames(ctx=ctx, txn=txn) | self.getgroupnames(ctx=ctx, txn=txn)

		# print addusers, addgroups, delusers, delgroups, checkitems
		if (addusers | addgroups | delusers | delgroups) - checkitems:
			raise emen2.db.exceptions.SecurityError, "Invalid users/groups: %s"%((addusers | addgroups | delusers | delgroups) - checkitems)

		# change child perms
		if recurse:
			recids |= listops.flatten(self.getchildtree(recids, recurse=recurse, ctx=ctx, txn=txn))


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

	def __endpoints(self, tree):
		return set(filter(lambda x:len(tree.get(x,()))==0, set().union(*tree.values())))


	#@rename db.records.render.childtree @notok @single @return tuple
	@publicmethod
	def renderchildtree(self, recid, recurse=1, rectypes=None, treedef=None, ctx=None, txn=None):
		"""Convenience method used by some clients to render a bunch of records and simple relationships"""

		#if recurse == -1:
		#	recurse = g.MAXRECURSE
		recurse = 3

		c_all = self.getchildtree(recid, recurse=recurse, ctx=ctx, txn=txn)
		c_rectype = self.getchildren(recid, recurse=recurse, rectype=rectypes, ctx=ctx, txn=txn)

		endpoints = self.__endpoints(c_all) - c_rectype
		while endpoints:
			for k,v in c_all.items():
				c_all[k] -= endpoints
			endpoints = self.__endpoints(c_all) - c_rectype

		rendered = self.renderview(listops.flatten(c_all), viewtype="recname", ctx=ctx, txn=txn)

		c_all = self.__filter_dict_zero(c_all)

		return rendered, c_all




	# ian: todo: simple: deprecate: still used in a few places in the js. Convenience methods go outside core?
	#@rename db.records.render.recname @notok @deprecated @return dict
	@publicmethod
	def getrecordrecname(self, rec, returnsorted=0, showrectype=0, ctx=None, txn=None):
		"""Render the recname view for a record."""

		if not hasattr(rec, '__iter__'): rec = [rec]
		recs = self.getrecord(rec, filt=1, ctx=ctx, txn=txn)
		ret = self.renderview(recs,viewtype="recname", ctx=ctx, txn=txn)
		recs = dict([(i.recid,i) for i in recs])

		if showrectype:
			for k in ret.keys():
				ret[k]="%s: %s"%(recs[k].rectype,ret[k])

		if returnsorted:
			sl=[(k,recs[k].rectype+" "+v.lower()) for k,v in ret.items()]
			return [(k,ret[k]) for k,v in sorted(sl, key=operator.itemgetter(1))]

		return ret



	def __dicttable_view(self, params, paramdefs={}, mode="unicode", ctx=None, txn=None):
		"""generate html table of params"""

		if mode in ["html","htmledit"]:
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



	#@notok
	#@multiple
	@publicmethod
	def renderview(self, recs, viewdef=None, viewtype="dicttable", showmacro=True, mode="unicode", filt=True, table=False, ctx=None, txn=None):
		"""Render views"""
						
		# This is the new, more general regex for parsing views..
		# type = name, param, macro, or..
		# name = param or macro name
		# def = default value
		# args = macro args
		# sep = separating character
		regex = re.compile(VIEW_REGEX)
		
		ol, recs = listops.oltolist(recs)

		if viewtype == "tabularview":
			table = True

		# Calling out to vtm, we will need a DBProxy
		dbp = ctx.db
		dbp._settxn(txn)
		vtm = emen2.db.datatypes.VartypeManager()

		# We'll be working with a list of recs
		recs = self.getrecord(listops.typefilter(recs, int), filt=filt, ctx=ctx, txn=txn) + listops.typefilter(recs, emen2.db.record.Record)

		# Default params
		builtinparams = set(["recid","rectype","comments","creator","creationtime","permissions", "history", "groups"])
		builtinparamsshow = builtinparams - set(["permissions", "comments", "history", "groups"])

		# Get and pre-process views
		groupviews = {}
		recdefs = listops.dictbykey(self.getrecorddef(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

		if not viewdef:
			for rd in recdefs.values():
				i = rd.name
				v = None
				rd["views"]["mainview"] = rd.mainview

				if viewtype=="dicttable":
					# move built in params to end of table
					par = [p for p in set(rd.paramsK) if p not in builtinparams]
					par += builtinparamsshow
					v = self.__dicttable_view(par, mode=mode, ctx=ctx, txn=txn)

				elif viewtype in ["tabularview","recname"]:
					v = rd.views.get(viewtype, rd.name)

				else:
					v = rd.views.get(viewtype, rd.mainview)
					v = markdown.markdown(v)

				groupviews[i] = v

		else:
			groupviews[None] = viewdef


		# Pre-process once to get paramdefs
		pds = set()
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				if match.group('type') in ["#", "$", '*']:
					pds.add(match.group('name'))
				else:
					vtm.macro_preprocess(match.group('name'), match.group('args'), recs, db=dbp)
					

		pds = listops.dictbykey(self.getparamdef(pds, ctx=ctx, txn=txn), 'name')

		# Parse views and build header row..
		matches = collections.defaultdict(list)
		headers = collections.defaultdict(list)
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				matches[group].append(match)
				h = pds.get(match.group('name'),{}).get('desc_short') or '%s(%s)'%(match.group('name'), match.group('args') or '')
				headers[group].append([h, match.group('type'), match.group('name'), match.group('args')])


		# Process records
		ret = {}
		for rec in recs:
			if groupviews.get(rec.rectype):
				key = rec.rectype
			elif viewdef:
				key = None
			else:
				key = None
				
			a = groupviews.get(key)
			vs = []

			for match in matches.get(key, []):
				t = match.group('type')
				n = match.group('name')
				s = match.group('sep') or ''
				m = mode
				if t == '#':
					v = vtm.name_render(pds[n], mode=mode, db=dbp)
				elif t == '$' or t == '*':
					# _t = time.time()
					v = vtm.param_render(pds[n], rec.get(n), mode=mode, rec=rec, db=dbp) or ''
					# print "-> %s, %s"%(n, time.time()-_t)
				elif t == '@' and showmacro:
					v = vtm.macro_render(n, match.group('args'), rec, mode=mode, db=dbp)
				else:
					continue

				vs.append(v)
				a = a.replace(match.group(), v+s)

			if table:
				ret[rec.recid] = vs
			else:
				ret[rec.recid] = a

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
	# @adminmethod
	def log_archive(self, remove=True, checkpoint=False, outpath=None, ctx=None, txn=None):

		outpath = outpath or g.paths.LOG_ARCHIVE

		if checkpoint:
			g.log.msg('LOG_INFO', "Log Archive: Checkpoint")
			self.dbenv.txn_checkpoint()

		archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

		g.log.msg('LOG_INFO', "Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

		if not os.access(outpath, os.F_OK):
			os.makedirs(outpath)

		self.__log_archive(archivefiles, outpath, remove=remove)



	def __log_archive(self, archivefiles, outpath, remove=False):

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
	
	
	
	
	
	
	
	
	
	
