# $Id$

import atexit
import collections
import copy
import functools
import getpass
import inspect
import operator
import os
import re
import smtplib
import sys
import time
import traceback
import weakref
import email
import email.mime.text

# Berkeley DB; the 'bsddb' module is not sufficient.
import bsddb3

# Markdown (HTML) Processing
# At some point, I may provide "extremely simple" markdown processor if markdown isn't available
try:
	import markdown
except ImportError:
	markdown = None


# EMEN2 Config
import emen2.db.config
g = emen2.db.config.g()

# If no configuration has been loaded, load the default configuration.
try:
	g.CONFIG_LOADED
except:
	emen2.db.config.defaults()


# EMEN2 Imports
import emen2.db.datatypes
import emen2.db.vartypes
import emen2.db.properties
import emen2.db.macros

import emen2.db.proxy
import emen2.db.validators
import emen2.db.dataobject

# DBObjects
import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group
import emen2.db.workflow

# Utilities
import emen2.util.listops as listops
import emen2.util.jsonutil

# Exceptions
from emen2.db.exceptions import *


# Conveniences
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



def fakemodules():
	"""Fixes some problems with backwards compatibility by manipulating module names"""
	import imp
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


# Version control
from emen2.clients import __version__
VERSIONS = {
	"API": g.VERSION,
	"emen2client": emen2.clients.__version__
}

# Regular expression to parse Protocol views. Perhaps this should go in recorddefs.py?
VIEW_REGEX = '(\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?)|((?P<text>[^\$]+))'


# Global pointer to database environment
DBENV = None


# basestring goes away in a later python version
basestring = (str, unicode)


DB_CONFIG = """\
# These can be tuned somewhat, depending on circumstances
set_cachesize 0 134217728 1
set_tx_max 65536
set_lk_max_locks 300000
set_lk_max_lockers 300000
set_lk_max_objects 300000
# Don't touch these
set_lg_dir log
set_data_dir data
set_lk_detect DB_LOCK_YOUNGEST
set_lg_regionmax 1048576
set_lg_max 8388608
set_lg_bsize 2097152
"""


def clock(times, key=0, t=0, limit=60):
	"""A timing method for controlling timeouts to prevent hanging.
	 On operations that might take a long time, call this at each step
	@param times Keep track of multiple times, e.g. debugging
	@keyparam key Use this key in the times dictionary
	@keyparam t Time at start of operation
	@keyparam limit Maximum amount of time allowed in this timing dict
	@return Time elapsed since start of operation (float)
	"""
	
	t2 = time.time()
	if not times.get(key):
		times[key] = 0
	times[key] += t2-t
	if sum(times.values()) >= limit:
		raise TimeError, "Operation timed out (max %s seconds)"%(limit)
	return t2


def check_output(args, **kwds):
	"""Run a command using Popen and return the stdout.
	@return stdout from the program after exit (str)
	"""
	
	kwds.setdefault("stdout", subprocess.PIPE)
	kwds.setdefault("stderr", subprocess.STDOUT)
	p = subprocess.Popen(args, **kwds)
	return p.communicate()[0]





# Close all database handles.
# Make this a static method of EMEN2DBEnv?
@atexit.register
def DB_Close(*args, **kwargs):
	"""Close all open DBs"""
	for i in EMEN2DBEnv.opendbs.keys():
		i.close()
		


# ian: todo: make these express GMT, then have display interfaces localize to time zone...
def getctime():
	"""@return Current database time, as float in seconds since the epoch"""
	return time.time()



def gettime():
	"""@return Current database time, as string in format %s"""%g.TIMESTR
	return time.strftime(g.TIMESTR)




# Use introspection to handle accepting single or iterable items
# It will look through the calling args/kwargs and convert ol=keyword
# to an iterable before passing to the public method.
# It will also transform the return value in the same way
# This will be easier in Python 2.7 using inspect.getcallargs.
def ol(name, output=True):
	def wrap(f):
		olpos = inspect.getargspec(f).args.index(name)

		@functools.wraps(f)
		def wrapped_f(*args, **kwargs):
			if kwargs.has_key(name):
				olreturn, olvalue = listops.oltolist(kwargs[name])
				kwargs[name] = olvalue
			else:
				olreturn, olvalue = listops.oltolist(args[olpos])
				args = list(args)
				args[olpos] = olvalue				

			result = f(*args, **kwargs)
			
			if output and olreturn:
				return listops.first_or_none(result)
			return result

		return wrapped_f

	return wrap



def error(e=None, msg=''):
	"""Error handler.
	@keyparam msg Error message; default is Excpetion's docstring
	@keyparam e Exception class; default is ValidationError
	"""
	if e == None:
		e = SecurityError
	if not msg:
		msg = e.__doc__
	# if warning:
	# 	g.warn(msg)
	raise e(msg)



# ian: todo: have DBEnv and all BDBs in here -- DB should just be methods for dealing with this dbenv "core"
class EMEN2DBEnv(object):

	opendbs = weakref.WeakKeyDictionary()

	def __init__(self, path=None, snapshot=False):
		"""EMEN2 Database Environment.
		The DB files are accessible as attributes, and indexes are loaded in self.index.
		@keyparam path Directory containing EMEN2 Database Environment.
		@keyparam snapshot Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
		"""
		
		self.keytypes = {}
		self.path = path or g.EMEN2DBHOME
		if not self.path:
			raise ValueError, "No path specified; check $EMEN2DBHOME and config.json files"

		#########################
		# Check that all the needed directories exist
		self.checkdirs()

		#########################
		# txn info
		self.txnid = 0
		self.txnlog = {}

		#########################
		# VartypeManager handles registration of vartypes and properties, and also validation
		vtm = emen2.db.datatypes.VartypeManager()
		self.indexablevartypes = set()
		for y in vtm.getvartypes():
			y = vtm.getvartype(y)
			if y.keytype:
				self.indexablevartypes.add(y.getvartype())								
			
		#########################
		# Open DB environment; check if global DBEnv has been opened yet
		# self.dbenv = self._init_dbenv()
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
			if snapshot:
				DBENV.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
			DBENV.open(self.path, ENVOPENFLAGS)
			self.opendbs[self] = 1

		self.dbenv = DBENV

		#########################
		# If we are just doing backups or maintenance, don't open any BDB handles
		# if maintenance:
		# 	return

		#########################
		# Open Database
		self.init()

		# txn = self.newtxn(write=True)
		# try:
		# 	self.init(txn=txn)
		# except Exception, inst:
		# 	self.txnabort(txn=txn)
		# 	raise
		# else:
		# 	self.txncommit(txn=txn)


	def init(self):
		"""Open the databases"""
		
		# Authentication
		self.context = emen2.db.context.ContextBTree(filename="security/contexts", dbenv=self.dbenv, bdbs=self)
		
		# Security items
		self.newuser = emen2.db.user.NewUserBTree(filename="security/newuserqueue", dbenv=self.dbenv, bdbs=self)
		self.user = emen2.db.user.UserBTree(filename="security/users", dbenv=self.dbenv, bdbs=self)
		self.group = emen2.db.group.GroupBTree(filename="security/groups", dbenv=self.dbenv, bdbs=self)

		# Main database items
		self.workflow = emen2.db.workflow.WorkFlowBTree(filename="main/workflow", dbenv=self.dbenv, bdbs=self)
		self.binary = emen2.db.binary.BinaryBTree(filename="main/bdocounter", dbenv=self.dbenv, bdbs=self)

		#  ... relationship items
		self.record = emen2.db.record.RecordBTree(filename="main/records", dbenv=self.dbenv, bdbs=self)
		self.paramdef = emen2.db.paramdef.ParamDefBTree(filename="main/paramdefs", dbenv=self.dbenv, bdbs=self)
		self.recorddef = emen2.db.recorddef.RecordDefBTree(filename="main/recorddefs", dbenv=self.dbenv, bdbs=self)

		# access by keytype..
		self.keytypes = {
			'record': self.record,
			'paramdef': self.paramdef,
			'recorddef': self.recorddef,
			'user': self.user,
			'group': self.group,
			'newuser': self.newuser,
			'workflow': self.workflow,
		}



	# ian: todo: make this nicer.
	def close(self):
		"""Close the Database Environment"""		
		for k,v in self.keytypes.items():
			v.close()
		self.dbenv.close()



	####################################
	# Utility methods
	####################################

	def checkdirs(self):
		"""Check that all necessary directories referenced from config file exist."""
		
		if not os.access(self.path, os.F_OK):
			os.makedirs(self.path)

		# ian: todo: create the necessary subdirectories when creating a database
		paths = [
			"data", 
			"data/main",
			"data/security",
			"data/index",
			"data/index/security",
			"data/index/params",
			"data/index/records",
			"log",
			"overlay",
			"overlay/views",
			"overlay/templates"
			]
			
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


	def stat():
		"""List some statistics about the Database Environment."""
		
		sys.stdout.flush()

		tx_max = self.dbenv.get_tx_max()
		g.log.msg('LOG_DEBUG', "Open transactions: %s"%tx_max)

		txn_stat = self.dbenv.txn_stat()
		g.log.msg('LOG_DEBUG', "Transaction stats: ")
		for k,v in txn_stat.items():
			g.log.msg('LOG_DEBUG', "\t%s: %s"%(k,v))

		log_archive = self.dbenv.log_archive()
		g.log.msg('LOG_DEBUG', "Archive: %s"%log_archive)

		lock_stat = self.dbenv.lock_stat()
		g.log.msg('LOG_DEBUG', "Lock stats: ")
		for k,v in lock_stat.items():
			g.log.msg('LOG_DEBUG', "\t%s: %s"%(k,v))


	####################################
	# Transaction management
	####################################
	
	txncounter = 0
	
	def newtxn(self, parent=None, write=False):
		"""Start a new transaction.
		@keyparam parent Open new txn as a child of this parent txn
		@keyparam write Transaction will be likely to write data; turns off Berkeley DB Snapshot
		@return New transaction
		"""

		flags = bsddb3.db.DB_TXN_SNAPSHOT
		if write:
			flags = 0

		txn = self.dbenv.txn_begin(parent=parent, flags=flags) #
		# g.log.msg('LOG_INFO', "NEW TXN, flags: %s --> %s"%(flags, txn))

		try:
			type(self).txncounter += 1
			self.txnlog[id(txn)] = txn
		except:
			self.txnabort(txn=txn)
			raise

		return txn



	def txncheck(self, txnid=0, write=False, txn=None):
		"""Check a transaction status, or create a new transaction.
		@keyparam txnid Transaction ID
		@keyparam write See newtxn
		@keyparam txn An existing open transaction
		@return Open transaction
		"""
		
		txn = self.txnlog.get(txnid, txn)
		if not txn:
			txn = self.newtxn(write=write)
		return txn



	def txnabort(self, txnid=0, txn=None):
		"""Abort transaction.
		@keyparam txnid Transaction ID
		@keyparam txn An existing open transaction
		@exception KeyError if transaction was not found
		"""
		
		txn = self.txnlog.get(txnid, txn)
		# g.log.msg('LOG_INFO', "TXN ABORT --> %s"%txn)

		if txn:
			txn.abort()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise KeyError, 'Transaction not found'



	def txncommit(self, txnid=0, txn=None):
		"""Commit a transaction.
		@keyparam txnid Transaction ID
		@keyparam txn An existing open transaction
		@exception KeyError if transaction was not found
		"""
		
		txn = self.txnlog.get(txnid, txn)
		# g.log.msg("LOG_INFO","TXN COMMIT --> %s"%txn)

		if txn != None:
			txn.commit()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise KeyError, 'Transaction not found'


	def checkpoint(self, txn=None):
		"""Checkpoint the Database Environment"""
		return self.dbenv.txn_checkpoint()



	###########################
	# Backup / restore
	###########################

	def log_archive(self, remove=True, checkpoint=False, txn=None):
		"""Archive completed log files.
		@keyparam remove Remove the log files after moving them to the backup location
		@keyparam checkpoint Run a checkpoint first; this will allow more files to be archived
		"""
		
		outpath = g.paths.LOG_ARCHIVE

		if checkpoint:
			g.log.msg('LOG_INFO', "Log Archive: Checkpoint")
			self.dbenv.txn_checkpoint()

		archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

		g.log.msg('LOG_INFO', "Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

		if not os.access(outpath, os.F_OK):
			os.makedirs(outpath)

		self._log_archive(archivefiles, outpath, remove=remove)


	def _log_archive(self, archivefiles, outpath, remove=False):
		"""(Internal) Backup database log files"""
		
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






class DB(object):
	"""Main database class"""

	# Regular stuff...
	def __init__(self, path=None):
		"""Initialize DB.
		Default path is g.EMEN2DBHOME, which checks $EMEN2DBHOME and program arguments.
		@keyparam path Directory containing EMEN2 Database Environment.
		"""
		
		# Open the database
		self.bdbs = EMEN2DBEnv(path=path)
		
		# Periodic operations..
		self.lastctxclean = time.time()
		self.opentime = gettime()

		# Cache contexts
		self.contexts_cache = {}

		# if maintenance:
		# 	return
		# Check if this is a valid db.. 
		# Probably move this into EMEN2DBEnv, but keep the setup in DB
		# txn = self.bdbs.newtxn(write=True)
		# try:
		# 	maxr = self.bdbs.bdbs.record.get_max(txn=txn)
		# 	g.log.msg("LOG_INFO","Opened database with %s records"%maxr)
		# 	if not self.bdbs.user.get('root', txn=txn):
		# 		self.setup(txn=txn)
		# 
		# except Exception, e:
		# 	g.log.msg('LOG_INFO',"Could not open database! %s"%e)
		# 	self.bdbs.txnabort(txn=txn)
		# 	raise
		# 
		# else:
		# 	self.bdbs.txncommit(txn=txn)


	def __del__(self):
		g.log_info('Cleaning up DB instance')


	def __str__(self):
		return "<DB: %s>"%(hex(id(self)))


	def __del__(self):
		"""Close DB when deleted"""
		self.bdbs.close()



	###############################
	# Utility methods
	###############################

	def setup(self, rootpw=None, rootemail=None, ctx=None, txn=None):
		"""Initialize a new DB.
		@keyparam rootpw Root Account Password
		@keyparam rootemail Root Account email
		"""
		
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

		# Create a fake root context for importing
		ctx = self._makerootcontext(txn=txn)
		dbp = ctx.db
		dbp._settxn(txn)

		g.log.msg("LOG_INFO","Initializing new database; root email: %s"%rootemail)

		import emen2.db.load
		path = emen2.db.config.get_filename('emen2', 'skeleton')
		loader = emen2.db.load.Loader(path=path, db=dbp)
		loader.load(rootemail=rootemail, rootpw=rootpw)


	# ian: todo: move this to UserBTree
	def _userbyemail(self, name, ctx=None, txn=None):
		"""(Internal) Attempt to lookup a username by email.
		@param name User name or Email
		@return User name
		"""
		ind = self.bdbs.user.getindex('email')
 		name = (ind.get(name, txn=txn) or [name])
		# If we got a hit, return the first one.
		return name.pop()


	# Find referenced recorddefs
	def _findrecorddefnames(self, names, ctx=None, txn=None):
		# Preprocess
		rds, recnames = listops.filter_partition(lambda x:isinstance(x, basestring), names)
		rds = set(rds)
		if recnames:
			grouped = self.groupbyrecorddef(names, ctx=ctx, txn=txn)
			rds |= set(grouped.keys())
		return rds


	# Find referenced paramdefs
	def _findparamdefnames(self, names, ctx=None, txn=None):
		# Preprocess
		params, recnames = listops.filter_partition(lambda x:isinstance(x, basestring), names)
		params = set(params)
		if recnames:
			recs = self.bdbs.record.cgets(recnames, ctx=ctx, txn=txn)
			rds = set([i.rectype for i in recs])
			for rd in self.bdbs.recorddef.cgets(rds, ctx=ctx, txn=txn):
				params |= set(rd.paramsK)
			for i in recs:
				params |= set(i.keys())
		print "found paramdef names:", params
		return params
		
		
	# Find referenced users/binaries
	def _findbyvartype(self, names, vartypes, ctx=None, txn=None):

		recnames, recs, values = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject)
		
		# print "getting recs"
		if recnames:
			recs.extend(self.bdbs.record.cgets(recnames, ctx=ctx, txn=txn))

		if not recs:
			return values
		
		# print "getting params"	
		# get the params we're looking for
		vtm = emen2.db.datatypes.VartypeManager()			
		vt = set()
		vt_iterable = set()
		pds = set()
		for rec in recs:
			pds |= set(rec.keys())
		for pd in self.bdbs.paramdef.cgets(pds, ctx=ctx, txn=txn):
			if pd.vartype not in vartypes:
				continue
			vartype = vtm.getvartype(pd.vartype)
			if vartype.iterable:
				vt_iterable.add(pd.name)
			else:
				vt.add(pd.name)

		# print "filtering"
		for param in vt_iterable:
			for rec in recs:
				values.extend(rec.get(param) or [])
		for param in vt:
			for rec in recs:
				if rec.get(param):
					values.append(rec.get(param))

		return values


	def _map_commit(self, keytype, names, method, ctx=None, txn=None, *args, **kwargs):
		"""(Internal) Get keytype items, run a method with *args **kwargs, and commit.
		@param keytype DBO keytype
		@param names DBO names
		@param method DBO method
		@*args method args
		@*kwargs method kwargs
		@return Results of commit/puts
		"""

		items = self.bdbs.keytypes[keytype].cgets(names, ctx=ctx, txn=txn)
		for item in items:
			getattr(item, method)(*args, **kwargs)
		return self.bdbs.keytypes[keytype].cputs(items, ctx=ctx, txn=txn)


	def _map_commit_ol(self, keytype, names, method, default, ctx=None, txn=None, *args, **kwargs):
		if names is None:
			names = default
		ol, names = listops.oltolist(names)
		ret = self._map_commit(keytype, names, method, ctx, txn, *args, **kwargs)
		if ol: return listops.first_or_none(ret)
		return ret
		

	# ian: todo: hard: flesh this out into a proper cron system, 
	# with a subscription model; right now just runs cleanupcontext
	# right now this is called during _getcontext, and calls
	# cleanupcontexts not more than once every 10 minutes
	def periodic_operations(self, ctx=None, txn=None):
		"""(Internal) Maintenance task scheduler.
		Eventually this will be replaced with a maintenance registration system."""

		t = getctime()
		if t > (self.lastctxclean + 600):
			self._cleanupcontexts(ctx=ctx, txn=txn)
			self.lastctxclean = t



	###############################
	# Email
	###############################
	
	def testmail(self, recipient, ctx=None, txn=None):
		self.sendmail(recipient, msg="Test!", subject="Test!", ctx=ctx, txn=txn)
		
		
	def sendmail(self, recipient, msg='', subject='', template=None, ctxt=None, ctx=None, txn=None):
		"""Send an email based on a template. Both the template system and mail system must be configured.
		@param recipient Email recipient
		@keyparam msg Message text, or..
		@keyparam template Template name
		@keyparam ctxt Dictionary to pass to template
		@return Email recipient, or None if no message was sent
		"""
		
		# get MAILADMIN from the root record...
		try:
			mailadmin = self.bdbs.user.get('root', txn=txn).email
			if not mailadmin:
				raise ValueError, "No email set for root"
			if not g.MAILHOST:
				raise ValueError, "No SMTP server"
		except Exception, inst:
			g.log('LOG_INFO',"Couldn't get mail config: %s"%inst)
			return

		ctxt = ctxt or {}
		ctxt["recipient"] = recipient
		ctxt["MAILADMIN"] = mailadmin
		ctxt["EMEN2DBNAME"] = g.EMEN2DBNAME
		ctxt["EMEN2EXTURI"] = g.EMEN2EXTURI

		if not recipient:
			return

		if msg:
			msg = email.mime.text.MIMEText(msg)
			msg['Subject'] = subject
			msg['From'] = mailadmin
			msg['To'] = recipient
			msg = msg.as_string()

		elif template:
			try:
				msg = g.templates.render_template(template, ctxt)
			except Exception, e:
				g.log('LOG_INFO','Could not render template %s: %s'%(template, e))
				return
		else:
			raise ValueError, "No message to send!"


		try:
			s = smtplib.SMTP(g.MAILHOST)
			s.set_debuglevel(1)
			s.sendmail(mailadmin, [mailadmin, recipient], msg)
			g.log('LOG_INFO', 'Mail sent: %s -> %s'%(mailadmin, recipient))
		except Exception, e:
			g.log('LOG_ERROR', 'Could not send email: %s'%e)
			raise e

		return recipient



	###############################
	# Time and Version Management
	###############################

	@publicmethod("version")
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program.
		@keyparam program Check version for this program (API, emen2client, etc.)
		@return Version string
		"""
		return VERSIONS.get(program)


	@publicmethod("time")
	def gettime(self, ctx=None, txn=None):
		"""Get current time.
		@return Current time string, YYYY/MM/DD HH:MM:SS
		"""
		return gettime()



	###############################
	# Login and Context Management
	###############################

	@publicmethod("auth.login", write=True)
	def login(self, name="anonymous", password="", host=None, ctx=None, txn=None):
		"""Logs a given user in to the database. 
		Returns ctxid (auth token), or fails with AuthenticationError or SessionError.
		@keyparam name Account name
		@keyparam password Account password
		@keyparam host Bind to this host (usually set by the proxy)
		@return Auth token string (ctxid)
		@exception AuthenticationError, SessionError, KeyError
		"""
	
		# Check the account name, or lookup account name by email
		name = unicode(name).strip()

		if name == "anonymous":
			# Make an anonymous Context
			newcontext = self._makecontext(host=host, ctx=ctx, txn=txn)
		else:
			# Try to find the user by account name, or by email
			name = self._userbyemail(name, txn=txn)

			# Check the password; user.checkpassword will raise Exception if wrong
			try:
				user = self.bdbs.user.get(name, txn=txn)
				user.checkpassword(password)
			except:
				raise AuthenticationError
			
			# Create the Context for this user/host
			newcontext = self._makecontext(username=name, host=host, ctx=ctx, txn=txn)
		
		self.bdbs.context.put(newcontext.ctxid, newcontext, txn=txn)
		g.log.msg('LOG_SECURITY', "Login succeeded: %s -> %s" % (name, newcontext.name))

		return newcontext.name


	# Logout is the same as delete context
	@publicmethod("auth.logout", write=True)
	def logout(self, ctx=None, txn=None):
		"""Logout."""
		self.bdbs.context.delete(ctx.name, txn=txn)


	@publicmethod("auth.check.context")
	def checkcontext(self, ctx=None, txn=None):
		"""Return basic information about the current Context.
		@return (Context User name, set of Context groups)
		"""
		return ctx.username, ctx.groups


	@publicmethod("auth.check.admin")
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.
		@return True if user is an admin
		"""
		return ctx.checkadmin()


	@publicmethod("auth.check.readadmin")
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.
		@return True if user is a read admin
		"""
		return ctx.checkreadadmin()


	@publicmethod("auth.check.create")
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.
		@return True if the user can create records
		"""
		return ctx.checkcreate()


	def _makecontext(self, username="anonymous", host=None, ctx=None, txn=None):
		"""(Internal) Initializes a context.
		@keyparam username Account name (default "anonymous")
		@keyparam host Host
		@return Context
		"""
		# Anonymous users can "login" to create a written Context;
		# Anonymous access without login uses an AnonymousContext which isn't written
		# I may use this distinction to create a "anonymous with email address" Context
		if username == "anonymous":
			ctx = emen2.db.context.AnonymousContext(host=host)
		else:
			ctx = emen2.db.context.Context(username=username, host=host)
		return ctx


	def _makerootcontext(self, ctx=None, host=None, txn=None):
		"""(Internal) Create a special root context.
		Can use this internally when some admin tasks that require ctx's are necessary.
		@return SpecialRootContext
		"""
		
		ctx = emen2.db.context.SpecialRootContext()
		ctx.refresh(db=self)
		ctx._setDBProxy(txn=txn)
		return ctx


	# ian: todo: hard: finish
	def _cleanupcontexts(self, ctx=None, txn=None):
		"""(Internal) Clean up sessions that have been idle too long."""
		
		newtime = getctime()
		old_strftime = time.strftime(g.TIMESTR, time.gmtime(self.lastctxclean))
		new_strftime = time.strftime(g.TIMESTR, time.gmtime(newtime))

		g.log.msg("LOG_DEBUG","Removing expired contexts: %s -> %s"%(old_strftime, new_strftime))

		for ctxid, context in self.bdbs.context.items(txn=txn):
			# If the item is in the cache, use the current last-access time..
			c = self.contexts_cache.get(ctxid)
			if c:
				context.time = c.time
			
			# Delete any expired contexts
			if context.time + (context.maxidle or 0) < newtime:
				g.log_info("Expire context (%s) %d" % (context.name, time.time() - context.time))
				self.bdbs.context.delete(context.name, txn=txn)


	# how often should we refresh groups? right now, every publicmethod will reset user/groups.
	# timer based?
	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Internal and DBProxy) Takes a ctxid key and returns a context.
		Note: The host provided must match the host in the Context
		@param ctxid ctxid
		@param host host
		@return Context
		@exception SessionError
		"""

		if txn == None:
			raise ValueError, "No txn"

		self.periodic_operations(ctx=ctx, txn=txn)

		# Find the context; check the cache first, then the bdb.
		# If no ctxid was provided, make an anonymous context.
		context = None
		if ctxid:
			context = self.contexts_cache.get(ctxid) or self.bdbs.context.get(ctxid, txn=txn)
		else:
			context = self._makecontext(host=host, ctx=ctx, txn=txn)

		# If no ctxid was found, it's an expired context and has already been cleaned out.
		if not context:
			g.log.msg('LOG_ERROR', "Session expired for %s"%ctxid)
			raise SessionError, "Session expired"


		# ian: todo: check referenced groups, referenced records... (complicated.): #groups
		user = None
		grouplevels = {}

		# Fetch the user record and group memberships
		if context.username not in ["anonymous"]:
			# This should probably be sget.
			user = self.bdbs.user.get(context.username, filt=False, txn=txn) 
			# ian: critical todo: check this index!!!
			groups = self.bdbs.group.getindex('permissions').get(context.username, set(), txn=txn)

			grouplevels = {}
			for group in self.bdbs.group.cgets(groups, ctx=ctx, txn=txn):
				grouplevels[group.name] = group.getlevel(context.username)

		# g.debug("kw host is %s, context host is %s"%(host, context.host))
		# Sets the database reference, user record, display name, groups, and updates
		#	context access time.
		context.refresh(user=user, grouplevels=grouplevels, host=host, db=self)

		# Keep contexts cached.
		self.contexts_cache[ctxid] = context

		return context



	###############################
	# Query
	###############################

	@publicmethod("record.query")
	def query(self, 
			c=None, 
			boolmode="AND", 
			ignorecase=True, 
			subset=None, 
			pos=0, 
			count=0, 
			sortkey="creationtime", 
			reverse=False,
			names=False,
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
		returnrecs = True # bool(names)
		boolops = {"AND":"intersection_update", "OR":"update"}
		names = None

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
			
		_cm, _cc = listops.filter_partition(lambda x:x[0].startswith('$@') or x[1]=='none' or x[1]=='noop', _c)		
		
		recs = collections.defaultdict(dict)
				
		############################				
		# Step 1: Run constraints
		t = clock(times, 0, t0)

		for searchparam, comp, value in _cc:
			# Matching names for each step
			constraintmatches = self._query(searchparam, comp, value, recs=recs, ctx=ctx, txn=txn)
			if names == None: # For the first constraint..
				names = constraintmatches
			elif constraintmatches != None: # Apply AND/OR
				getattr(names, boolops[boolmode])(constraintmatches)

		
		############################				
		# Step 2: Filter permissions. If no constraint, use all records..
		t = clock(times, 1, t)

		if names == None:
			names = self.bdbs.record.names(ctx=ctx, txn=txn)

		if subset:
			names &= subset

		if c:
			# Filter
			names = self.bdbs.record.names(names or set(), ctx=ctx, txn=txn)
			
			
		############################				
		# Step 3: Run constraints that include macros or "value is empty"
		t = clock(times, 2, t)

		for searchparam, comp, value in _cm:
			constraintmatches = self._query(searchparam, comp, value, names=names, recs=recs, ctx=ctx, txn=txn)
			if constraintmatches != None:
				getattr(names, boolops[boolmode])(constraintmatches)


		############################				
		# Step 4: Generate stats on rectypes (do this before other sorting..)
		t = clock(times, 3, t)

		rectypes = collections.defaultdict(int)
		rds = set([rec.get('rectype') for rec in recs.values()]) - set([None])
		if len(rds) == 0:
			if stats: # don't do this unless we want these.
				r = self._groupbyrecorddef_index(names, ctx=ctx, txn=txn)
				for k,v in r.items():
					rectypes[k] = len(v)
		elif len(rds) == 1:
			rectypes[rds.pop()] = len(names)
		elif len(rds) > 1:
			for name, rec in recs.iteritems():
				rectypes[rec.get('rectype')] += 1


		############################					
		# Step 5: Sort and slice to the right range
		# This processes the values for sorting:
		#	running any macros, rendering any user names, checking indexes, etc.
		t = clock(times, 4, t)

		keytype, sortvalues = self._query_sort(sortkey, names, recs=recs, c=c, ctx=ctx, txn=txn)

		key = sortvalues.get
		if sortkey in ['creationtime', 'recid', 'name']:
			key = None
			reverse = not reverse
		elif keytype == 's':
			key = lambda name:(sortvalues.get(name) or '').lower()
		
		# We want to put empty values at the end..
		nonenames = set(filter(lambda x:not (sortvalues.get(x) or sortvalues.get(x)==0), names))
		names -= nonenames

		# not using reverse=reverse so we can add nonenames at the end
		names = sorted(names, key=key) 
		names.extend(sorted(nonenames))
		if reverse:
			names.reverse()
		
		# Truncate results.
		length = len(names)
		if count > 0:
			names = names[pos:pos+count]

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
			defaultviewdef = "$@recname() $@thumbnail() $$rectype $$name"
			addparamdefs = ["creator","creationtime"]
			
			# Get the viewdef
			if len(rectypes) == 1:
				rd = self.bdbs.recorddef.cget(rectypes.keys()[0], ctx=ctx, txn=txn)
				viewdef = rd.views.get('tabularview', defaultviewdef)
			else:
				try:
					rd = self.bdbs.recorddef.cget("root_protocol", ctx=ctx, txn=txn)
					viewdef = rd.views.get('tabularview', defaultviewdef)
				except:
					viewdef = defaultviewdef


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
			table = self.renderview(names, viewdef=viewdef, table=True, ctx=ctx, txn=txn)

		
		t = clock(times, 6, t)

		stats = {}
		stats['time'] = time.time()-t0
		stats['rectypes'] = rectypes

		# stats['times'] = times
		# for k,v in times.items():
		# 	print k, '%5.3f'%(v)
				
		
		############################							
		# Step 7: Fix for output
		for name in names:
			recs[name]['name'] = name
		recs = [recs[i] for i in names]

		ret = {
			"c": c,
			"boolmode": boolmode,
			"ignorecase": ignorecase,
			"names": names,
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


	def _query(self, searchparam, comp, value, names=None, recs=None, ctx=None, txn=None):
		"""(Internal) index-based search. See DB.query()
		@param searchparam Param
		@param comp Comparison method
		@param value Comparison value
		@keyparam names Record names (used in some query operations)
		@keyparam recs Record cache dict, by name
		@return Record names returned by query operation, or None
		"""

		if recs == None:
			recs = {}

		cfunc = self._query_cmps()[comp]
			
		if value == None and comp not in ["any", "none", "contains_w_empty"]:
			return None
			
						
		# Sadly, will need to run macro on everything.. :(
		# Run these as the last constraints.
		if searchparam.startswith('$@'):
			keytype, ret = self._run_macro(searchparam, names or set(), ctx=ctx, txn=txn)
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
		searchnames = set()		
		
		if searchparam == 'rectype' and value:
			# Get child protocols, skip the index-index search
			matchkeys['rectype'] = self.bdbs.recorddef.expand([value], ctx=ctx, txn=txn)
			
		elif searchparam == 'children':
			# Get children, skip the other steps
			# ian: todo: integrate this with the other * processing methods
			recurse = 0
			if unicode(value).endswith('*'):
				value = int(unicode(value).replace('*', ''))
				recurse = -1
			recs[value]['children'] = self.bdbs.record.rel([value], recurse=recurse, ctx=ctx, txn=txn).get(value, set())
			searchnames = recs[value]['children']

		elif searchparam == 'name':
			# This is useful in a few places
			searchnames.add(int(value))

		else:
			# Get the list of indexes to search
			if searchparam.endswith('*'):
				sp = self._query_paramstrip(searchparam)
				indparams |= self.bdbs.paramdef.rel([sp], recurse=recurse, ctx=ctx, txn=txn)[sp]
			indparams.add(self._query_paramstrip(searchparam))
				
				
		# First, search the index index
		indk = self.bdbs.record.getindex('indexkeys')

		for indparam in indparams:
			pd = self.bdbs.paramdef.cget(indparam, ctx=ctx, txn=txn)
			ik = indk.get(indparam, txn=txn)

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
				cargs = listops.combine(*cargs)

			r = set()
			for v in listops.check_iterable(cargs):
				r |= set(filter(functools.partial(cfunc, v), ik))

			if r:
				matchkeys[indparam] = r


		# Now search individual param indexes
		for pp, keys in matchkeys.items():
			ind = self.bdbs.record.getindex(pp)
			for key in keys:
				v = ind.get(key, txn=txn)
				searchnames |= v 
				for v2 in v:
					recs[v2][pp] = key

		# If the comparison is "value is empty", then we 
		# 	return the items we couldn't find in the index
		# 'No constraint' doesn't affect search results -- just store the values.
		if comp == 'noop':
			return None
		elif comp == 'none':
			return (names or set()) - searchnames
			
		return searchnames


	def _query_sort(self, sortkey, names, recs=None, rendered=False, c=None, ctx=None, txn=None):
		"""(Internal) Sort Records by sortkey
		@param sortkey
		@param names
		@keyparam recs Record cache, keyed by name
		@keyparam rendered Compare using 'rendered' value
		@c Query constraints; used for checking items in cache
		@return Sortkey keytype ('s'/'d'/'f'/None), and {name:value} of values that can be sorted
		"""

		# No work necessary if sortkey is creationtime
		if sortkey in ['creationtime', 'name', 'recid']:
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
			pd = self.bdbs.paramdef.cget(sortkey, ctx=ctx, txn=txn)
			vartype = pd.vartype
			vt = vtm.getvartype(vartype)
			keytype = vt.keytype
			iterable = vt.iterable
			ind = self.bdbs.record.getindex(pd.name)
		except:
			pass


		# These will always sort using the rendered value
		if vartype in ["user", "userlist", "binary", "binaryimage"]:
			rendered = True				


		# Ian: todo: if the vartype is iterable,
		#	then we can't trust the index to get the search order right!

		# ian: this can't be trustedif boolmode is 'OR'
		#if sortkey in [i[0] for i in c] and not iterable:
		#	# Do we already have these values?
		#	for name in names:
		#		sortvalues[name] = recs[name].get(sortkey)

		if sortkey.startswith('$@'):
			# Sort using a macro, and get the right sort function
			keytype, sortvalues = self._run_macro(sortkey, names, ctx=ctx, txn=txn)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v
				# Unghhgh... ian: todo: make a macro_render_sort
				if hasattr(v, '__iter__'):
					v = ", ".join(map(unicode, v))
					sortvalues[k] = v


		elif not ind or len(names) < 1000 or iterable:
			# We don't have the value, no index.. 
			# Can be very slow! Chunk to limit damage.
			for chunk in listops.chunk(names):
				for rec in self.bdbs.record.cgets(chunk, ctx=ctx, txn=txn):
					sortvalues[rec.name] = rec.get(sortkey)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v

		elif ind:
			# We don't have the value, but there is an index..
			# modifytime is kindof a pathological index.. need to find a better way
			for k,v in ind.iterfind(names, txn=txn):
				inverted[k] = v
			sortvalues = listops.invert(inverted)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v

		else:
			# raise ValueError, "Don't know how to sort by %s"%sortkey
			pass


		# Use a "rendered" representation of the value,
		#	e.g. user names to sort by user's current last name
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

	def _query_cmps(self, ignorecase=1):
		"""(Internal) Return the list of query constraint operators.
		@keyparam ignorecase Use case-insensitive comparison methods
		@return Dict of query methods
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
			'name': lambda y,x: x,
			#'rectype': lambda y,x: x,
			# "!contains": lambda y,x:unicode(y) not in unicode(x),
			# "range": lambda x,y,z: y < x < z
		}

		if ignorecase:
			cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			cmps['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

		return cmps


	def _query_paramstrip(self, param):
		"""(Internal) Remove decorations ($$, *, etc.) from a param name.
		@return Un-decorated ParamDef name
		"""
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
		

	def _run_macro(self, macro, names, ctx=None, txn=None):
		"""(Internal) Run a macro over a set of Records.
		@param macro Macro in view format: $@macro(args)
		@param names Record names
		@return Macro keytype ('d'/'s'/'f'/None), and dict of processed Records
		"""
		
		recs = {}
		mrecs = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)

		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		
		regex = re.compile(VIEW_REGEX)
		k = regex.match(macro)
		
		keytype = vtm.getmacro(k.group('name')).getkeytype()
		vtm.macro_preprocess(k.group('name'), k.group('args'), mrecs)

		for rec in mrecs:
			recs[rec.name] = vtm.macro_process(k.group('name'), k.group('args'), rec)

		return keytype, recs
			
			
			
	###############################
	# Other query methods
	###############################			

	def _boolmode_collapse(self, rets, boolmode):
		if not rets:
			rets = [set()]
		if boolmode == 'AND':
			allret = reduce(set.intersection, rets)
		elif boolmode == 'OR':
			allret = reduce(set.union, rets)
		return allret
		

	@publicmethod("recorddef.find")
	def findrecorddef(self, *args, **kwargs):
		"""Find a RecordDef, by general search string, or by name/desc_short/desc_long/mainview.
		@param query Contained in any item below
		@keyparam name ... contains in name
		@keyparam desc_short ... contains in short description
		@keyparam desc_long ... contains in long description
		@keyparam mainview ... contains in mainview
		@keyparam record Referenced in Record name(s)
		@keyparam limit Limit number of results
		@keyparam boolmode AND / OR for each search constraint
		@return RecordDefs
		"""
		return self._find_pdrd(keytype='recorddef', *args, **kwargs)


	@publicmethod("paramdef.find")
	def findparamdef(self, *args, **kwargs):
		"""Find a RecordDef, by general search string, or by name/desc_short/desc_long/mainview.
		@param query Contained in any item below
		@keyparam name ... contains in name
		@keyparam desc_short ... contains in short description
		@keyparam desc_long ... contains in long description
		@keyparam vartype ... is of vartype(s)
		@keyparam record Referenced in Record name(s)
		@keyparam limit Limit number of results
		@keyparam boolmode AND / OR for each search constraint
		@return RecordDefs
		"""
		return self._find_pdrd(keytype='paramdef', *args, **kwargs)


	def _find_pdrd(self, query=None, childof=None, boolmode="AND", keytype="paramdef", limit=None, record=None, vartype=None, ctx=None, txn=None, **qp):
		"""(Internal) Find ParamDefs or RecordDefs based on **qp constraints."""

		rets = []		
		# This can still be done much better
		names = self.bdbs.keytypes[keytype].names(ctx=ctx, txn=txn)
		items = self.bdbs.keytypes[keytype].cgets(names, ctx=ctx, txn=txn)
		ditems = listops.dictbykey(items, 'name')

		query = unicode(query or '').split()
		for q in query:
			ret = set()
			# Search some text-y fields
			for param in ['name', 'desc_short', 'desc_long', 'mainview']:
				for item in items:
					if q in unicode(item.get(param) or ''):
						ret.add(item.name)
			rets.append(ret)

		if vartype:
			ret = set()
			vartype = listops.check_iterable(vartype)
			for item in items:
				if item.vartype in vartype:
					ret.add(item.name)
			rets.append(ret)			

		if record:
			if keytype == 'recorddef':
				rets.append(self._findrecorddefnames(listops.check_iterable(record), ctx=ctx, txn=txn))
			elif keytype == 'paramdef':
				rets.append(self._findparamdefnames(listops.check_iterable(record), ctx=ctx, txn=txn))
					
			
		allret = self._boolmode_collapse(rets, boolmode)
		ret = map(ditems.get, allret)

		if limit:
			return ret[:int(limit)]
		return ret


	@publicmethod("user.find")
	def finduser(self, query=None, record=None, boolmode="AND", limit=None, ctx=None, txn=None, **kwargs):
		"""Find a user, by general search string, or by name_first/name_middle/name_last/email/name.
		@keyparam query Contained in any item below
		@keyparam email ... contains in email
		@keyparam name_first ... contains in first name
		@keyparam name_middle ... contains in middle name
		@keyparam name_last ... contains in last name
		@keyparam name ... contains in user name
		@keyparam record Referenced in Record name(s)
		@keyparam limit Limit number of results
		@keyparam boolmode AND / OR for each search constraint
		@return Users
		"""
		rets = []
		query = unicode(query or '').split()
		for q in query:
			q = q.strip()
			c = [
				["name_first", "contains", q],
				["name_last", "contains", q],
				["name_middle", "contains", q],
				["email", "contains", q],
				["username", "contains", q]
				]
			qr = self.query(boolmode='OR', c=c, sortkey='username', ctx=ctx, txn=txn)
			un = filter(None, [i.get('username') for i in qr['recs']])
			rets.append(set(un))
				
		# email=None, name_first=None, name_middle=None, name_last=None, name=None, 
		for param in ['email', 'name_first', 'name_middle', 'name_last']:
			if kwargs.get(param):
				q = self.query(c=[[param,'contains', kwargs.get(param)]], sortkey='username', ctx=ctx, txn=txn)
				un = filter(None, [i.get('username') for i in q['recs']])
				rets.append(set(un))

		name = kwargs.get('name') or kwargs.get('username')
		if name:
			ret = set()
			for i in self.bdbs.user.names(ctx=ctx, txn=txn):
				if name in i:
					ret.add(i)
			rets.append(ret)
		
		if record:
			ret = self._findbyvartype(listops.check_iterable(record), ['user', 'userlist'], ctx=ctx, txn=txn)
			rets.append(ret)
		
		allret = self._boolmode_collapse(rets, boolmode)
		return self.getuser(allret, ctx=ctx, txn=txn)


	@publicmethod("group.find")
	def findgroup(self, query=None, record=None, limit=None, boolmode='AND', ctx=None, txn=None):
		"""Find a group.
		@keyparam query Find in Group's name or displayname
		@keyparam record Referenced in Record name(s)
		@keyparam limit Limit number of results
		@keyparam boolmode AND / OR for each search constraint
		@return Groups
		"""
		rets = []

		# No real indexes yet (small). Just get everything and sort directly.
		items = self.bdbs.group.cgets(self.bdbs.group.names(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		ditems = listops.dictbykey(items, 'name')

		query = unicode(query or '').split()
		# empty set.. do this only for groups, for now.
		if not query:
			query = ['']
			
		for q in query:
			ret = set()
			for item in items:
				# Search these params
				for param in ['name', 'displayname']:
					if q in item.get(param, ''):
						ret.add(item.name)
			rets.append(ret)
			
		if record:
			ret = self._findbyvartype(listops.check_iterable(record), ['groups'], ctx=ctx, txn=txn)
			rets.append(set(ret))

		allret = self._boolmode_collapse(rets, boolmode)
		ret = map(ditems.get, allret)

		if limit:
			return ret[:int(limit)]
		return ret


	# Warning: This can be SLOW! It needs an index-index.
	@publicmethod("binary.find")
	def findbinary(self, query=None, record=None, limit=None, boolmode='AND', ctx=None, txn=None, **kwargs):
		"""Find a binary by filename.
		@keyparam query Contained in any item below
		@keyparam name ... Binary name
		@keyparam filename ... filename
		@keyparam record Referenced in Record name(s)
		@keyparam limit Limit number of results
		@keyparam boolmode AND / OR for each search constraint (default: AND)
		@return Binaries
		"""
		
		# @keyparam min_filesize
		# @keyparam max_filesize

		def searchfilenames(filename, txn):
			ind = self.bdbs.binary.getindex('filename')
			ret = set()
			keys = (f for f in ind.keys(txn=txn) if filename in f)
			for key in keys:
				ret |= ind.get(key, txn=txn)
			return ret			

		rets = []		
		# This would probably work better if we used the sequencedb keys as a first step
		if query or kwargs.get('name'):
			names = self.bdbs.binary.names(ctx=ctx, txn=txn)

		query = unicode(query or '').split()
		for q in query:
			ret = set()
			ret |= set(name for name in names if q in name)
			ret |= searchfilenames(q, txn=txn)
		
		if kwargs.get('filename'):
			rets.append(searchfilenames(kwargs.get('filename'), txn=txn))
		
		if kwargs.get('name'):
			rets.append(set(name for name in names if q in name))

		if record:
			ret = self._findbyvartype(listops.check_iterable(record), ['binary', 'binaryimage'], ctx=ctx, txn=txn)
			rets.append(ret)

		allret = self._boolmode_collapse(rets, boolmode)
		ret = self.bdbs.binary.cgets(allret, ctx=ctx, txn=txn)

		if limit:
			return ret[:int(limit)]
		return ret
			
			
	# query should replace this... also, make two methods instead of changing return format
	@publicmethod("record.find.byvalue")
	def findvalue(self, param, query='', count=True, showchoices=True, limit=100, ctx=None, txn=None):
		"""Find values for a parameter. This is mostly used for interactive UI elements: e.g. combobox.
		More detailed results can be performed using db.query.
		@param param Parameter to search
		@param query Value to match
		@keyparam limit Limit number of results
		@keyparam showchoices Include any defined param 'choices'
		@keyparam count Return count of matches, otherwise return names
		@return if count: [[matching value, count], ...]
				if not count: [[matching value, [name, ...]], ...]
		"""

		pd = self.bdbs.paramdef.cget(param, ctx=ctx, txn=txn)
		q = self.query(c=[[param, "contains_w_empty", query]], ignorecase=1, recs=True, ctx=ctx, txn=txn)
		inverted = collections.defaultdict(set)
		for rec in q['recs']:
			inverted[rec.get(param)].add(rec.get('name'))		

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
	# Note: both of these methods might go away..

	@publicmethod("record.find.byrecorddef")
	@ol('names', output=False)
	def getindexbyrecorddef(self, names, ctx=None, txn=None):
		"""Get Record names by RecordDef.
		@param names RecordDef name(s)
		@return Set of Record names
		"""
		rds = self.bdbs.recorddef.cgets(names, ctx=ctx, txn=txn)
		ind = self.bdbs.record.getindex("rectype")
		ret = set()
		for i in rds:
			ret |= ind.get(i.name, txn=txn)			
		return ret



	#########################
	# Grouping
	#########################

	# ian: I intend to add more records.group.* methods.
	@publicmethod("record.group.byrecorddef")
	@ol('names')
	def groupbyrecorddef(self, names, ctx=None, txn=None):
		"""Group Records by RecordDef.
		@param names Record name(s)
		@return Dictionary of Record names by RecordDef
		"""
		if len(names) == 0:
			return {}

		if (len(names) < 1000) or (isinstance(list(names)[0],emen2.db.record.Record)):
			return self._groupbyrecorddef_fast(names, ctx=ctx, txn=txn)

		names = self.bdbs.record.filter(names, ctx=ctx, txn=txn)
		return self._groupbyrecorddef_index(names, ctx=ctx, txn=txn)


	def _groupbyrecorddef_index(self, names, ctx=None, txn=None):
		"""(Internal) Group Records by RecordDef using the indexes.
		@param names Record names
		@return Dictionary of Record names by RecordDef
		"""
		
		ret = {}
		# Work with a copy becuase we'll be changing it
		names = copy.copy(names)
		ind = self.bdbs.record.getindex("rectype")

		while names:
			# get a random record id
			rid = names.pop() 
			# get the set of all records with this recorddef
			rec = self.bdbs.record.get(rid, txn=txn) 
			# intersect our list with this recdef
			ret[rec.rectype] = ind.get(rec.rectype, txn=txn) & names 
			# remove the results from our list since we have now classified them
			names -= ret[rec.rectype] 
			# add back the initial record to the set
			ret[rec.rectype].add(rid) 

		return ret


	def _groupbyrecorddef_fast(self, names, ctx=None, txn=None):
		"""(Internal) Sometimes it's quicker to just get the records and filter directly.
		@param names Records or Record names
		@return Dictionary of Record names by RecordDef
		"""

		# ian: todo: better input checking and error handling
		if not isinstance(list(names)[0],emen2.db.record.Record):
			names = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)

		ret={}
		for i in names:
			if not ret.has_key(i.rectype): ret[i.rectype]=set([i.name])
			else: ret[i.rectype].add(i.name)

		return ret



	#############################
	# Record Rendering
	#############################

	#@remove?
	@publicmethod("record.renderchildtree")
	def renderchildtree(self, name, recurse=3, rectype=None, ctx=None, txn=None):
		"""Convenience method used by some clients to render a bunch of 
		records and simple relationships.
		@name Record name
		@keyparam recurse Recurse level
		@keyparam rectype Restrict to these rectypes ('*' notation allowed)
		@return (Dictionary of rendered views {Record.name:view}, Child tree dictionary)
		"""

		c_all = self.bdbs.record.rel([name], recurse=recurse, tree=True, ctx=ctx, txn=txn)
		c_rectype = self.bdbs.record.rel([name], recurse=recurse, rectype=rectype, ctx=ctx, txn=txn).get(name, set())

		endpoints = self._endpoints(c_all) - c_rectype
		while endpoints:
			for k,v in c_all.items():
				c_all[k] -= endpoints
			endpoints = self._endpoints(c_all) - c_rectype

		rendered = self.renderview(listops.flatten(c_all), ctx=ctx, txn=txn)

		c_all = listops.filter_dict_zero(c_all)

		return rendered, c_all


	def _endpoints(self, tree):
		return set(filter(lambda x:len(tree.get(x,()))==0, set().union(*tree.values())))


	@publicmethod("record.render")
	@ol('names')
	def renderview(self, names, viewdef=None, viewtype='recname', edit=False, markup=True, table=False, mode=None, vtm=None, ctx=None, txn=None):
		"""Render views.
		Note: if 'names' is not iterable, will return a string instead of dictionary
		@param names Record name(s)
		@keyparam viewdef View definition
		@keyparam viewtype Use this view from the Record's RecordDdef (default='recname')
		@keyparam edit Render with editing HTML markup; use 'auto' for autodetect. (default=False)
		@keyparam markup Render with HTML markup (default=True)
		@keyparam table Return table format (this may go into a separate method) (default=False)
		@keyparam mode Deprecated, no effect.
		@return Dictionary of {Record.name: rendered view}
		"""
		
		regex = re.compile(VIEW_REGEX)

		if viewtype == "tabularview":
			table = True

		if viewtype == 'recname' and not viewdef:
			markup = False

		if table:
			edit = "auto"
		
		if table or edit:
			markup = True

		# Calling out to vtm, we will need a DBProxy
		vtm = vtm or emen2.db.datatypes.VartypeManager(db=ctx.db)

		# We'll be working with a list of names
		names, recs = listops.partition_dbobjects(names)
		recs.extend(self.bdbs.record.cgets(names, ctx=ctx, txn=txn))
		
		# Default params
		builtinparams = set() | emen2.db.record.Record.param_all
		builtinparamsshow = builtinparams - set(["permissions", "comments", "history", "groups"])

		# Get and pre-process views
		groupviews = {}
		recdefs = listops.dictbykey(self.bdbs.recorddef.cgets(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

		if viewdef:
			groupviews[None] = viewdef


		elif viewtype == "dicttable":
			for rec in recs:
				# move built in params to end of table
				par = [p for p in set(recdefs.get(rec.rectype).paramsK) if p not in builtinparams]
				par += builtinparamsshow
				par += [p for p in rec.getparamkeys() if p not in par]
				groupviews[rec.name] = self._dicttable_view(par, markup=markup, ctx=ctx, txn=txn)


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


		pds = listops.dictbykey(self.bdbs.paramdef.cgets(pds, ctx=ctx, txn=txn), 'name')

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
				key = rec.name

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
					v = vtm.param_render(pds[n], rec.get(n), name=rec.name, edit=_edit, markup=markup, table=table)
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
				ret[rec.name] = vs
			else:
				ret[rec.name] = a


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

		return ret


	def _dicttable_view(self, params, paramdefs={}, markup=False, ctx=None, txn=None):
		"""(Internal) Create an HTML table for rendering.
		@param params Use these ParamDef names
		@keyparam paramdefs ParamDef cache
		@keyparam markup Use HTML Markup (default=False)
		@return HTML table of params
		"""

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





	#########################################################################
	#************************************************************************
	#*	Start: BDB Methods
	#*	Most of these methods are just wrappers for the various 
	#* 	DBOBTree methods.
	#************************************************************************
	#########################################################################
	
	
	###############################
	# Relationships
	###############################

	# This is a new method -- might need some testing.
	@publicmethod("rel.siblings")
	def getsiblings(self, name, rectype=None, keytype="record", ctx=None, txn=None, **kwargs):
		return self.bdbs.keytypes[keytype].siblings(name, rectype=rectype, ctx=ctx, txn=txn, **kwargs)
		

	@publicmethod("rel.parenttree")
	@ol('names', output=False)
	def getparenttree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', tree=True, ctx=ctx, txn=txn, **kwargs)
	

	@publicmethod("rel.childtree")
	@ol('names', output=False)
	def getchildtree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', tree=True, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.parents")
	@ol('names')
	def getparents(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', ctx=ctx, txn=txn, **kwargs)

	@publicmethod("rel.children")
	@ol('names')
	def getchildren(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.rel")
	@ol('names')
	def rel(self, names, keytype="record", recurse=1, rel="children", tree=False, ctx=None, txn=None, **kwargs):
		"""Get relationships. See the RelateBTree.rel()"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel=rel, tree=tree, ctx=ctx, txn=txn, **kwargs)


	# Change relationships
	@publicmethod('rel.pclink', write=True)
	def pclink(self, parent, child, keytype='record', ctx=None, txn=None):
		return self.bdbs.keytypes[keytype].pclink(parent, child, ctx=ctx, txn=txn)
		
		
	@publicmethod('rel.pcunlink', write=True)
	def pcunlink(self, parent, child, keytype='record', ctx=None, txn=None):
		return self.bdbs.keytypes[keytype].pcunlink(parent, child, ctx=ctx, txn=txn)


	@publicmethod('rel.relink', write=True)
	def relink(self, parent, child, keytype='record', ctx=None, txn=None):
		return self.bdbs.keytypes[keytype].relink(parent, child, ctx=ctx, txn=txn)



	###############################
	# User Management
	###############################

	@publicmethod("user.get")
	@ol('names')
	def getuser(self, names, filt=True, ctx=None, txn=None):
		"""Get user information. Information may be limited to name and id if the user
		requested privacy.
		@param names User name(s), Record(s), or Record name(s)
		@keyparam filt Ignore failures
		@return User(s)
		"""		
		return self.bdbs.user.cgets(names, filt=filt, ctx=ctx, txn=txn)
		

	@publicmethod("user.names")
	def getusernames(self, names=None, ctx=None, txn=None):
		"""@return Set of all User names."""
		return self.bdbs.user.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("user.put", write=True)
	@ol('items')
	def putuser(self, items, ctx=None, txn=None):
		"""Allow a User to change some of their account settings.
		@param items User(s)
		@return Updated User(s)
		"""
		return self.bdbs.user.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("user.disable", write=True, admin=True)
	def disableuser(self, names, ctx=None, txn=None):
		"""(Admin Only) Disable a User.	
		@param names User name(s)
		@keyparam filt Ignore failures
		@return List of names disabled
		"""
		return self._map_commit('user', names, 'disable', ctx=ctx, txn=txn)
	
	
	@publicmethod("user.enable", write=True, admin=True)
	def enableuser(self, names, ctx=None, txn=None):
		"""(Admin Only) Re-enable a User.
		@param names User name(s)
		@keyparam filt Ignore failures
		"""
		return self._map_commit('user', names, 'enable', ctx=ctx, txn=txn)

	
	@publicmethod("user.setprivacy", write=True)
	def setprivacy(self, state, names=None, ctx=None, txn=None):
		"""Set privacy level.
		@state 0, 1, or 2, in increasing level of privacy.
		@keyparam names User names to modify (admin only)
		"""
		# This is a modification of _map_commit to allow if names=None
		# ctx.username will be used as the default.
		return self._map_commit_ol('user', names, 'setprivacy', ctx.username, ctx, txn, state)
		
		
		
	##########
	# User Email / Password
	# These methods sometimes use put instead of cput because they need to modify
	# the user's secret auth token.
	#########
	
	@publicmethod("user.setemail", write=True)
	def setemail(self, email, secret=None, password=None, name=None, ctx=None, txn=None):
		"""Change a User's email address. This will require you to verify that you
		own the account by responding with an auth token sent to that address.
		Note: This method only takes a single User name.
		Note: An Admin will always succeed in changing email, with or without password/token.
		@param email New email address
		@keyparam secret Auth token, or...
		@keyparam password Current User password
		@keyparam name User name (default is current Context user)
		@exception SecurityError if the password and/or auth token are wrong
		"""

		#@action		
		# Get the record, and keep the existing email address to see if it changes.
		name = name or ctx.username
		ctxt = {}

		# Verify the email address is owned by the person requesting the change.
		# 1 -> User authenticates they *really* own the account by providing the acct password
		# 2 -> An email will be sent to the new account specified, containing an auth token
		# 3 -> The user comes back and calls the method with this token
		# 4 -> Email address is updated, and reindexed

		user = self.bdbs.user.cget(name, filt=False, ctx=ctx, txn=txn)
		oldemail = user.email
		email = user.setemail(email, password=password, secret=secret)

		#@postprocess
		# Check that no other user is currently using this email.
		ind = self.bdbs.user.getindex('email')
		if ind.get(email, txn=txn) - set([user.name]):
			time.sleep(2)
			raise SecurityError, "The email address %s is already in use"%(email)

		if user.email == oldemail:
			# The email didn't change, but the secret did
			# Note: cputs will always ignore the secret; write directly
			self.bdbs.user.put(user.name, user, txn=txn)

			# Send the verify email containing the auth token
			ctxt['secret'] = user._secret[2]
			self.sendmail(email, template='/email/email.verify', ctxt=ctxt, ctx=ctx, txn=txn)

		else:
			# Email changed.
			g.log.msg("LOG_INFO","Changing email for %s"%user.name)	
			self.bdbs.user.cputs([user], txn=txn)			

			# Send the user an email to acknowledge the change
			self.sendmail(user.email, template='/email/email.verified', ctxt=ctxt, ctx=ctx, txn=txn)

	
	@publicmethod("auth.setpassword", write=True)
	def setpassword(self, oldpassword, newpassword, secret=None, name=None, ctx=None, txn=None):
		"""Change password.
		Note: This method only takes a single User name.
		@param oldpassword
		@param newpassword
		@keyparam name User name (default is current Context user)
		"""
		
		#@preprocess
		name = self._userbyemail(name, ctx=ctx, txn=txn)

		#@action
		# Try to authenticate using either the password OR the secret!
		# ian: need to read directly because setContext hides password
		user = self.bdbs.user.cget(name, filt=False, ctx=ctx, txn=txn)
		user.setpassword(oldpassword, newpassword, secret=secret)

		# ian: todo: evaluate to use put/cput..
		g.log.msg("LOG_SECURITY","Changing password for %s"%user.name)
		self.bdbs.user.put(user.name, user, txn=txn)
		# self.bdbs.user.cputs([user], ctx=ctx, txn=txn)

		#@postprocess
		self.sendmail(user.email, template='/email/password.changed', ctx=ctx, txn=txn)


	@publicmethod("auth.resetpassword", write=True)
	def resetpassword(self, name, ctx=None, txn=None):
		"""Send a password reset token to the User's currently registered email address.
		Note: This method only takes a single User name.
		@keyparam name User name, or User Email
		@keyparam secret
		"""

		#@preprocess
		name = self._userbyemail(name, txn=txn)

		#@action
		# Set the password reset secret..
		user = self.bdbs.user.get(name, filt=False, txn=txn)
		user.resetpassword()			
		# Use direct put to preserve the secret
		self.bdbs.user.put(user.name, user, txn=txn)

		#@postprocess
		# Absolutely never reveal the secret via any mechanism but email to registered address
		ctxt = {'secret': user._secret[2]}
		self.sendmail(user.email, template='/email/password.reset', ctxt=ctxt, ctx=ctx, txn=txn)

		g.log.msg("LOG_SECURITY","Setting resetpassword secret for %s"%user.name)
		


	###############################
	# New Users
	###############################

	@publicmethod("user.queue.names", admin=True)
	def getuserqueue(self, names=None, ctx=None, txn=None):
		"""@return Set of names of Users in the new user queue."""
		return self.bdbs.newuser.names(names=names, ctx=ctx, txn=txn)


	# Only allow admins!
	@publicmethod("user.queue.get", admin=True)
	@ol('names')
	def getqueueduser(self, names, ctx=None, txn=None):
		"""(Admin Only) Get users from the new user approval queue.
		@param names New user queue name(s)
		@return User(s) from new user queue
		"""	
		return self.bdbs.newuser.cgets(names, ctx=ctx, txn=txn)


	@publicmethod("user.queue.new")
	def newuser(self, name, password, email, ctx=None, txn=None):
		"""Create a new User.	
		@param name Desired account name
		@param password Password
		@param email Email Address
		@return New User
		@exception KeyError if there is already a user or pending user with this name
		"""
		# This will check existing new users, users, and emails
		return self.bdbs.newuser.new(name=name, password=password, email=email, ctx=ctx, txn=txn)


	@publicmethod("user.queue.put", write=True)
	@ol('users')
	def adduser(self, users, ctx=None, txn=None):
		"""Add a new User.
		Note: This only adds the user to the new user queue. The
		account must be processed by an administrator before it
		becomes active.
		@param users New User(s)
		@return New User(s)
		"""
		#@action
		# NewUserBTree.new will check against existing username/emails
		users = self.bdbs.newuser.cputs(users, ctx=ctx, txn=txn)
		
		#@postprocess
		# Send account request email
		for user in users:
			self.sendmail(user.email, template='/email/adduser.signup', ctx=ctx, txn=txn)

		return users


	@publicmethod("user.queue.approve", write=True, admin=True)
	@ol('names')
	def approveuser(self, names, secret=None, ctx=None, txn=None):
		"""(Admin Only) Approve account in user queue.
		@param names New user approval queue name(s)
		@return Approved User name(s)
		"""

		# Get users from the new user approval queue
		newusers = self.bdbs.newuser.cgets(names, ctx=ctx, txn=txn)
		cusers = []

		# This will also check if the current username or email is in use
		for newuser in newusers:
			name = newuser.name

			# Delete the pending user
			self.bdbs.newuser.delete(name, txn=txn)

			user = self.bdbs.user.new(name=name, email=newuser.email, password=newuser.password, ctx=ctx, txn=txn)
			print user
			# Put the new user
			user = self.bdbs.user.cput(user, ctx=ctx, txn=txn)
			
			# Update default Groups
			if user.name != 'root':
				for group in g.GROUP_DEFAULTS:
					gr = self.bdbs.group.cget(group, ctx=ctx, txn=txn)
					gr.adduser(user.name)
					self.bdbs.group.cput(gr, ctx=ctx, txn=txn)
			
			# Create the "Record" for this user
			rec = self.bdbs.record.new(rectype='person', ctx=ctx, txn=txn)

			# This gets updated with the user's signup info
			rec.update(newuser.signupinfo)
			rec.adduser(name, level=2)
			rec.addgroup("authenticated")
			
			rec = self.bdbs.record.cput(rec, ctx=ctx, txn=txn)
			
			# Update the User with the Record name and put again
			user.record = rec.name
			user = self.bdbs.user.cput(user, ctx=ctx, txn=txn)
			cusers.append(user)
		
		# Send the 'account approved' emails
		for user in cusers:
			ctxt = {'name':user.name}
			self.sendmail(user.email, template='/email/adduser.approved', ctxt=ctxt, ctx=ctx, txn=txn)

		return cusers
			
	
	@publicmethod("user.queue.reject", write=True, admin=True)
	@ol('names')
	def rejectuser(self, names, filt=False, ctx=None, txn=None):
		"""(Admin Only) Remove a user from the new user queue.
		@param names New user name(s) to reject
		@keyparam filt Ignore failures
		@return Rejected user name(s)
		"""
				
		#@action
		# ian: move this to UserBTree.new()? Probably make it explicit..
		# This is an admin only method
		emails = {}
		users = self.bdbs.newuser.cgets(names, filt=False, ctx=ctx, txn=txn)
		for user in users:
			emails[user.name] = user.email
			
		for	user in users:
			self.bdbs.newuser.delete(user.name, txn=txn)
	
		#@postprocess
		# Send the emails
		for name, email in emails.items():
			ctxt = {'name':name}
			self.sendmail(email, template='/email/adduser.rejected', ctxt=ctxt, ctx=ctx, txn=txn)

		return set(emails.keys())



	##########################
	# Groups
	##########################

	@publicmethod("group.names")
	def getgroupnames(self, names=None, ctx=None, txn=None):
		"""@return Set of all Group names."""
		return self.bdbs.group.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("group.get")
	@ol('names')
	def getgroup(self, names, filt=True, ctx=None, txn=None):
		"""Get a Group.
		@param names Group name(s)
		@keyparam filt Ignore failures
		@return Group(s)
		"""
		return self.bdbs.group.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("group.new")
	def newgroup(self, name, ctx=None, txn=None):
		"""Construct a new Group.
		@param name Group name
		@return New Group
		"""
		return self.bdbs.group.new(name=name, ctx=ctx, txn=txn)


	@publicmethod("group.put", write=True, admin=True)
	@ol('items')
	def putgroup(self, items, ctx=None, txn=None):
		"""Add or update Group(s).
		@param items Group(s)
		@return Updated Group(s)
		"""		
		return self.bdbs.groups.cputs(items, ctx=ctx, txn=txn)
	


	#########################
	# section: paramdefs
	#########################

	@publicmethod("paramdef.vartypes")
	def getvartypenames(self, ctx=None, txn=None):
		"""@return Set of all available vartypes."""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getvartypes())


	@publicmethod("paramdef.properties")
	def getpropertynames(self, ctx=None, txn=None):
		"""@return Set of all available properties."""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getproperties())


	@publicmethod("paramdef.units")
	def getpropertyunits(self, name, ctx=None, txn=None):
		"""Returns a list of recommended units for a particular property.
		Other units may be used if they can be converted to the property's default units.
		@param name Property name
		@return Set of recommended units for property.
		"""
		if not name:
			return set()
		vtm = emen2.db.datatypes.VartypeManager()
		prop = vtm.getproperty(name)
		return set(prop.units)


	@publicmethod("paramdef.new")
	def newparamdef(self, name, vartype, ctx=None, txn=None):
		"""Construct a new ParamDef.
		@param name ParamDef name
		@param vartype ParamDef vartype
		@keyparam inherit
		@return New ParamDef
		"""
		return self.bdbs.paramdef.new(name=name, vartype=vartype, ctx=ctx, txn=txn)


	@publicmethod("paramdef.put", write=True)
	@ol('items')
	def putparamdef(self, items, ctx=None, txn=None):
		"""Add or update ParamDef(s).
		@param items ParamDef(s)
		@return Updated ParamDef(s)
		"""		
		return self.bdbs.paramdef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("paramdef.get")
	@ol('names')
	def getparamdef(self, names, filt=True, ctx=None, txn=None):
		"""Get ParamDefs.
		@param names ParamDef name(s) and/or Record name(s)
		@keyparam filt Ignore failures
		@return ParamDef(s)
		"""
		return self.bdbs.paramdef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("paramdef.names")
	def getparamdefnames(self, names=None, ctx=None, txn=None):
		"""@return Set of all ParamDef names."""
		return self.bdbs.paramdef.names(names=names, ctx=ctx, txn=txn)



	#########################
	# section: recorddefs
	#########################

	@publicmethod("recorddef.new")
	def newrecorddef(self, name, mainview, ctx=None, txn=None):
		"""Construct a new RecordDef.
		@param name RecordDef name
		@param mainview RecordDef mainview
		@return New RecordDef
		"""
		return self.bdbs.recorddef.new(name=name, mainview=mainview, ctx=ctx, txn=txn)


	@publicmethod("recorddef.put", write=True)
	@ol('items')
	def putrecorddef(self, items, ctx=None, txn=None):
		"""Add or update RecordDef(s).
		Note: RecordDef mainviews should
		never be changed once used, since this will change the meaning of
		data already in the database, but sometimes changes of appearance
		are necessary, so this method is available.
		@param items RecordDef(s)
		@return Updated RecordDef(s)
		"""
		return self.bdbs.recorddef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("recorddef.get")
	@ol('names')
	def getrecorddef(self, names, filt=True, ctx=None, txn=None):
		"""Get RecordDef(s).
		@param names RecordDef name(s), and/or Record ID(s)
		@keyparam filt Ignore failures
		@return RecordDef(s)
		"""
		return self.bdbs.recorddef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("recorddef.names")
	def getrecorddefnames(self, names=None, ctx=None, txn=None):
		"""@return All RecordDef names."""
		return self.bdbs.recorddef.names(names=names, ctx=ctx, txn=txn)



	#########################
	# section: records
	#########################

	@publicmethod("record.get")
	@ol('names')
	def getrecord(self, names, filt=True, ctx=None, txn=None):
		"""Get Record(s).
		@param names Record name(s)
		@keyparam filt Ignore failures
		@return Record(s)
		"""
		return self.bdbs.record.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("record.new")
	def newrecord(self, rectype, inherit=None, ctx=None, txn=None):
		"""Construct a new Record.
		@param rectype RecordDef
		@keyparam inherit Inherit permissions from an existing Record
		"""
		
		rec = self.bdbs.record.new(rectype=rectype, ctx=ctx, txn=txn)
		
		#@postprocess
		# Apply any inherited permissions
		if inherit != None:
			inherit = set(listops.tolist(inherit))
			try:
				precs = self.bdbs.record.cgets(inherit, filt=False, ctx=ctx, txn=txn)
				for prec in precs:
					rec.addumask(prec["permissions"])
					rec.addgroup(prec["groups"])
			except Exception, inst:
				g.log.msg("LOG_ERROR","Error setting inherited permissions from record %s: %s"%(inherit, inst))
	
			rec["parents"] |= inherit	
		return rec


	@publicmethod("record.delete", write=True)
	@ol('names')
	def deleterecord(self, names, ctx=None, txn=None):
		"""Unlink and hide a record; it is still accessible to owner. Records are never truly deleted, just hidden.	
		@param name Record name(s) to delete
		@return Deleted Record(s)
		"""	
		self.bdbs.record.delete(names, ctx=ctx, txn=txn)


	@publicmethod("record.addcomment", write=True)
	@ol('names')
	def addcomment(self, names, comment, ctx=None, txn=None):
		"""Add comment to a record. Requires comment permissions on that Record.
		@param name Record name(s)
		@param comment Comment text
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'addcomment', ctx, txn, comment)


	@publicmethod("record.find.comments")
	@ol('names', output=False)
	def getcomments(self, names, filt=True, ctx=None, txn=None):
		"""Get comments from Records.
		@param names Record name(s)
		@return A list of comments, with the Record ID as the first item in each comment:
			[[recid, username, time, comment], ...]
		"""
		recs = self.bdbs.record.cgets(names, filt=filt, ctx=ctx, txn=txn)

		#@postprocess
		ret = []		
		# This filters out a couple "history" types of comments
		for rec in recs:
			cp = rec.get("comments")
			if not cp:
				continue
			cp = filter(lambda x:"LOG: " not in x[2], cp)
			cp = filter(lambda x:"Validation error: " not in x[2], cp)
			for c in cp:
				ret.append([rec.name]+list(c))

		return sorted(ret, key=operator.itemgetter(2))



	###############################
	# Record Updates
	###############################

	@publicmethod("record.update", write=True)
	@ol('names')
	def putrecordvalues(self, names, update, ctx=None, txn=None):
		"""Convenience method to update Records.
		@param names Record name(s)
		@param update Update Records with this dictionary
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'update', ctx, txn, update)


	@publicmethod("record.validate")
	@ol('items')
	def validaterecord(self, items, ctx=None, txn=None):
		"""Check that a record will validate before committing.
		@param items Record(s)
		@return Validated Record(s)
		"""
		return self.bdbs.record.validate(items, ctx=ctx, txn=txn)


	@publicmethod("record.put", write=True)
	@ol('items')
	def putrecord(self, items, ctx=None, txn=None):
		"""Add or update Record.
		@param items Record(s)
		@return Updated Record(s)
		"""		
		return self.bdbs.record.cputs(items, ctx=ctx, txn=txn)



	###############################
	# Record Permissions
	###############################

	# These map to the normal Record methods
	@publicmethod("record.adduser", write=True)
	@ol('names')
	def addpermission(self, names, users, level=0, reassign=False, ctx=None, txn=None):
		"""Add users to a Record's permissions.
		@param names Record name(s)
		@param users User name(s) to add
		@keyparam level Permissions level; 0=read, 1=comment, 2=write, 3=owner
		@keyparam reassign Allow a decrease in permissions level (default=False)
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'adduser', ctx, txn, users)
	
	
	@publicmethod("record.removeuser", write=True)
	@ol('names')
	def removepermission(self, names, users, ctx=None, txn=None):
		"""Remove users from a Record's permissions.
		@param names Record name(s)
		@param users User name(s) to remove
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'removeuser', ctx, txn, users)
	
		
	@publicmethod("record.addgroup", write=True)
	@ol('names')	
	def addgroup(self, names, groups, ctx=None, txn=None):
		"""Add groups to a Record's permissions.
		@param names Record name(s)
		@param groups Group name(s) to add
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'addgroup', ctx, txn, groups)


	@publicmethod("record.removegroup", write=True)
	@ol('names')
	def removegroup(self, names, groups, ctx=None, txn=None):
		"""Remove groups from a Record's permissions.
		@param names Record name(s)
		@param groups Group name(s)
		@return Updated Record(s)
		"""
		return self._map_commit('record', names, 'removegroup', ctx, txn, groups)


	# This method is for compatibility with the web interface widget..
	@publicmethod("record.setpermissions_compat", write=True)
	@ol('names')
	def setpermissions(self, names, permissions, groups, recurse=None, overwrite_users=False, overwrite_groups=False, ctx=None, txn=None):

		"""Legacy permissions method.
		@param names Record(s)
		@param umask Add permissions mask
		@keyparam recurse
		@keyparam reassign
		@keyparam delusers
		@keyparam addgroups
		@keyparam delgroups
		"""

		allusers = set()
		for i in permissions:
			allusers |= set(i)

		groups = set(groups or [])
		recs = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)
		for rec in recs:
			current = rec.members()
			addusers = allusers - current
			delusers = current - allusers
			addgroups = groups - rec.groups
			delgroups = rec.groups - groups
			
			print "record %s:"%rec.name
			print "current:", current
			print "allusers:", allusers
			print "addusers:", addusers
			print "delusers:", delusers
			print "addgroups:", addgroups
			print "delgroups:", delgroups
		
		
		


	###############################
	# Binaries
	###############################

	@publicmethod("binary.get")
	@ol('names')
	def getbinary(self, names=None, filt=True, ctx=None, txn=None):
		"""Get Binaries.
		@param names Record name(s), Binary name(s)
		@keyparam filt Ignore failures
		@return Binary(s)
		@exception KeyError if Binary not found, SecurityError if insufficient permissions
		"""
		return self.bdbs.binary.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("binary.new")
	def newbinary(self, ctx=None, txn=None):
		"""Construct a new Binary. This doesn't do anything until committed with a file data source.
		@return New Binary
		"""
		return self.bdbs.binary.new(name=None, ctx=ctx, txn=txn)


	# def putbinary(self, name=None, record=None, filename=None, infile=None, clone=False, ctx=None, txn=None):
	@publicmethod("binary.put", write=True)
	def putbinary(self, item, filename=None, infile=None, clone=False, record=None, param='file_binary', ctx=None, txn=None):
		"""Note: This currently only takes a single item."""

		# Preprocess
		if not item:
			item = self.bdbs.binary.new(ctx=ctx, txn=txn)

		# Convenience
		if filename:
			item.filename = filename

		# Check the record
		if isinstance(record, int):
			item.record = record
		elif record != None:
			# record is a dict or new Record to commit.
			rec = self.bdbs.record.cput(record, ctx=ctx, txn=txn)
			item.record = rec.recid		

		# ian: todo: sort out item.compressed..

		# Test that we can write to the record
		rec = self.bdbs.record.cget(item.record, filt=False, ctx=ctx, txn=txn)
		if not rec.writable():
			raise SecurityError, "No write permissions for Record %s"%rec.name			
	
		newfile = None
		if infile:
			newfile, filesize, md5sum = emen2.db.binary.write_binary(infile=infile, ctx=ctx, txn=txn)			
			item.filesize = filesize
			item.md5 = md5sum

		# Commit the BDO to get a name.
		bdo = self.bdbs.binary.cput(item, ctx=ctx, txn=txn)

		#@postprocess
		# Update the record.
		if bdo.name != item.name:
			pd = self.bdbs.paramdef.cget(param, ctx=ctx, txn=txn)
			rec = self.bdbs.record.cget(bdo.record, filt=False, ctx=ctx, txn=txn)
			if pd.vartype == 'binary':
				v = rec.get(pd.name, [])
				if bdo.name not in v:
					v.append(bdo.name)
					rec[pd.name] = v
			elif pd.vartype == 'binaryimage':
				if bdo.name != rec.get(pd.name):
					rec[pd.name] = bdo.name
			else:
				raise KeyError, "ParamDef %s does not accept attachments"%pd.name
				
			self.bdbs.record.cputs([rec], ctx=ctx, txn=txn)

		# Now move the file to the right location
		if newfile:
			if os.path.exists(bdo.filepath):
				raise SecurityError, "Cannot overwrite existing file!"
			print "Renaming file %s -> %s"%(newfile, bdo.filepath)
			os.rename(newfile, bdo.filepath)
	
		# Create the tiles/previews, in a background process
		try:
			emen2.web.thumbs.run_from_bdo(bdo)
		except Exception, inst:
			pass

		return bdo
			


	#########################
	# section: workflow
	#########################

	# Workflows are currently turned off, need to be fixed.

	# @publicmethod
	# def getworkflownames(self, name=None, ctx=None, txn=None):
	# 	"""This will return an (ordered) list of workflow objects for the given context (user).
	# 	it is an exceptionally bad idea to change a WorkFlow object's wfid."""
	#	name = name or ctx.username
	#	return self.bdbs.workflow.get(name).names(ctx=ctx, txn=txn)
	#
	#
	# @publicmethod
	# @ol('names')
	# def getworkflow(self, names, ctx=None, txn=None):
	# 	"""Return a workflow by names."""
	#	return self.bdbs.workflow.get(name).cgets(names, ctx=ctx, txn=txn))
	#
	#
	# @publicmethod
	# def newworkflow(self, ctx=None, txn=None):
	# 	"""Return an initialized workflow instance."""
	# 	return self.bdbs.workflow.new(ctx=ctx, txn=txn)
	#
	#
	# @publicmethod
	# @ol('items')
	# def putworkflow(self, items, ctx=None, txn=None):
	# 	"""This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""
	#	return self.bdbs.workflow.get(name).cputs(items, ctx=ctx, txn=txn)
	# 
	#
	# @publicmethod
	# @ol('names')
	# def delworkflowitem(self, names, ctx=None, txn=None):
	# 	"""This will remove a single workflow object based on wfid"""
	#	return self.bdbs.workflow.get(name).delete(names, ctx=ctx, txn=txn)



	#############################
	# Rebuild Indexes
	#############################

	# def _rebuild_all(self, ctx=None, txn=None):
	# 	"""(Internal) Rebuild all indexes. This should only be used if you blow something up, change a paramdef vartype, etc.
	# 	It might test the limits of your Berkeley DB configuration and fail if the resources are too low."""
	# 
	# 	g.log.msg("LOG_INFO","Rebuilding ALL indexes!")
	# 
	# 	allparams = self.bdbs.paramdef.keys()
	# 	paramindexes = {}
	# 	for param in allparams:
	# 		paramindex = self.bdbs.getindex(param)
	# 		if paramindex != None:
	# 			# g.log.msg('LOG_DEBUG', paramindex)
	# 			try:
	# 				g.log.msg("LOG_INDEX","self.bdbs.fieldindex[%s].truncate"%param)
	# 				paramindex.truncate(txn=txn)
	# 			except Exception, e:
	# 				g.log.msg("LOG_INFO","Critical! self.bdbs.fieldindex[%s].truncate failed: %s"%(param, e))
	# 			paramindexes[param] = paramindex
	# 
	# 
	# 	g.log.msg("LOG_INFO","Done truncating all indexes")
	# 
	# 	self._rebuild_groupsbyuser(ctx=ctx, txn=txn)
	# 	self._rebuild_usersbyemail(ctx=ctx, txn=txn)
	# 
	# 	maxrecords = self.bdbs.record.get_max(txn=txn) #get(-1, txn=txn)["max"]
	# 	g.log.msg('LOG_INFO',"Rebuilding indexes for %s records..."%(maxrecords-1))
	# 
	# 	blocks = range(0, maxrecords, g.BLOCKLENGTH) + [maxrecords]
	# 	blocks = zip(blocks, blocks[1:])
	# 
	# 
	# 	for pos, pos2 in blocks:
	# 		g.log.msg("LOG_INFO","Reindexing records %s -> %s"%(pos, pos2))
	# 		crecs = []
	# 		for i in range(pos, pos2):
	# 			g.log.msg("LOG_INFO","... %s"%i)
	# 			crecs.append(self.bdbs.record.get(i, filt=False, txn=txn))
	# 
	# 		self._commit_records(crecs, reindex=True, ctx=ctx, txn=txn)
	# 
	# 	g.log.msg("LOG_INFO","Done rebuilding all indexes!")
	# def _rebuild_groupsbyuser(self, ctx=None, txn=None):
	# 	"""(Internal) Rebuild groupbyuser index"""
	# 
	# 	g.log.msg("LOG_INDEX","self.bdbs.groupbyuser: Rebuilding index")
	# 
	# 	groups = self.bdbs.group.get(self.bdbs.group.names(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
	# 	users = collections.defaultdict(set)
	# 
	# 	for group in groups:
	# 		for user in group.members():
	# 			users[user].add(group.name)
	# 
	# 	g.log.msg("LOG_INDEX","self.bdbs.groupbyuser.truncate")
	# 	self.bdbs.groupbyuser.truncate(txn=txn)
	# 
	# 	for k,v in users.items():
	# 		g.log.msg("LOG_INDEX","self.bdbs.groupbyuser.addrefs: %s -> %s"%(k,v))
	# 		self.bdbs.groupbyuser.addrefs(k, v, txn=txn)
	# 
	# 
	# def _rebuild_usersbyemail(self, ctx=None, txn=None):
	# 	names = self.getusernames(ctx=ctx, txn=txn)
	# 	users = self.bdbs.user.cgets(names, ctx=ctx, txn=txn)
	# 
	# 	g.log.msg("LOG_INDEX","self.bdbs.userbyemail.truncate")
	# 	self.bdbs.userbyemail.truncate(txn=txn)
	# 
	# 	for user in users:
	# 		#g.log.msg("LOG_INDEX","self.bdbs.userbyemail.addrefs: %s -> %s"%(user.email.lower(), user.name))
	# 		self.bdbs.userbyemail.addrefs(user.email.lower(), [user.name], txn=txn)
	# 
	# 
	# def _reindex_groupsbyuser(self, groups, ctx=None, txn=None):
	# 	"""(Internal) Reindex a group's members for the groupsbyuser index"""
	# 
	# 	addrefs = collections.defaultdict(set)
	# 	delrefs = collections.defaultdict(set)
	# 
	# 	for group in groups:
	# 
	# 		ngm = group.members()
	# 		try:
	# 			ogm = self.bdbs.group.get(group.name, txn=txn).members()
	# 		except:
	# 			ogm = set()
	# 
	# 		addusers = ngm - ogm
	# 		delusers = ogm - ngm
	# 
	# 		for user in addusers:
	# 			addrefs[user].add(group.name)
	# 		for user in delusers:
	# 			delrefs[user].add(group.name)
	# 
	# 	return addrefs, delrefs



__version__ = "$Revision$".split(":")[1][:-1].strip()
