# $Id$
"""Main database module

Functions:
	clock: Time a method's execution time
	getctime: Local ctime
	gettime: Formatted time
	ol: Decorator to make sure a method argument is iterable
	limit_result_length: Limit the number of items returned
	error: Error handler
	sendmail: Send an email

Classes:
	EMEN2DBEnv: Manage an EMEN2 Database Environment
	DB: Main database class

"""

import datetime
import threading
import atexit
import collections
import copy
import functools
import getpass
import imp
import inspect
import os
import re
import sys
import time
import traceback
import weakref
import shutil
import glob
import random
import smtplib
import email
import email.mime.text

# Berkeley DB
# Note: the 'bsddb' module is not sufficient.
import bsddb3

# Markdown (HTML) Processing
# At some point, I may provide "extremely simple" markdown processor fallback
try:
	import markdown
except ImportError:
	markdown = None

# JSON-RPC support
import jsonrpc.jsonutil

# EMEN2 Config
import emen2.db.config
import emen2.db.log

# EMEN2 Core
import emen2.db.datatypes
import emen2.db.vartypes
import emen2.db.properties
import emen2.db.macros
import emen2.db.proxy
import emen2.db.load
import emen2.db.handlers

# EMEN2 DBObjects
import emen2.db.dataobject
import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group
import emen2.db.workflow

# EMEN2 Utilities
import emen2.util.listops as listops

# EMEN2 Exceptions into local namespace
from emen2.db.exceptions import *

# EMEN2 Extensions
emen2.db.config.load_exts()

##### Conveniences #####
publicmethod = emen2.db.proxy.publicmethod

# Version names
# from emen2.clients import __version__
VERSIONS = {
	"API": emen2.VERSION
}

# Regular expression to parse Protocol views.
VIEW_REGEX = '(\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?)|((?P<text>[^\$]+))'
VIEW_REGEX = re.compile(VIEW_REGEX)

# basestring goes away in Python 3
basestring = (str, unicode)

# ian: todo: move this to EMEN2DBEnv
DB_CONFIG = """\
# Don't touch these
set_lg_dir log
set_data_dir data
set_lg_regionmax 1048576
set_lg_max 8388608
set_lg_bsize 2097152
"""


##### Utility methods #####

def clock(times, key=0, t=0, limit=180):
	"""A timing method for controlling timeouts to prevent hanging.
	On operations that might take a long time, call this at each step.

	:param times: Keep track of multiple times, e.g. debugging
	:keyword key: Use this key in the times dictionary
	:keyword t: Time at start of operation
	:keyword limit: Maximum amount of time allowed in this timing dict
	:return: Time elapsed since start of operation (float)
	"""
	t2 = time.time()
	if not times.get(key):
		times[key] = 0
	times[key] += t2-t
	if sum(times.values()) >= limit:
		raise TimeError, "Operation timed out (max %s seconds)"%(limit)
	return t2


import uuid
def getrandomid():
	"""Generate a random ID"""
	return uuid.uuid4().hex
	# return '%032x'%random.getrandbits(128)


# ian: todo: make these express GMT, then localize using a user preference
def getctime():
	""":return: Current database time, as float in seconds since the epoch."""
	return time.time()


def gettime():
	"""Returns the current database UTC time in ISO 8601 format"""
	return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'+00:00'


def ol(name, output=True):
	"""Use method argument introspection to convert an argument value to a list.
	If the value was originally a list, return a list. If it was not, return
	a single value.

	:param name: Argument name to transform to list.
	:keyword output: Transform output.
	"""
	# This will be easier in Python 2.7 using inspect.getcallargs.

	def wrap(f):
		olpos = inspect.getargspec(f).args.index(name)

		@functools.wraps(f)
		def wrapped_f(*args, **kwargs):
			if kwargs.has_key(name):
				olreturn, olvalue = listops.oltolist(kwargs[name])
				kwargs[name] = olvalue
			elif (olpos-1) <= len(args):
				olreturn, olvalue = listops.oltolist(args[olpos])
				args = list(args)
				args[olpos] = olvalue
			else:
				raise TypeError, 'function %r did not get argument %s' % (f, name)

			result = f(*args, **kwargs)

			if output and olreturn:
				return listops.first_or_none(result)
			return result

		return wrapped_f

	return wrap


def limit_result_length(default=None):
	"""Limit the number of items returned by a query result."""
	ns = dict(func = None)
	def _inner(*a, **kw):
		func = ns.get('func')
		result = func(*a, **kw)
		limit = kw.pop('limit', default)
		if limit  and hasattr(result, '__len__') and len(result) > limit:
			result = result[:limit]
		return result

	def wrapped_f(f):
		ns['func'] = f
		return functools.wraps(f)(_inner)

	result = wrapped_f
	if callable(default):
		ns['func'] = default
		result = functools.wraps(default)(_inner)

	return result


# Error handler
def error(e=None, msg='', warning=False):
	"""Error handler.

	:keyword msg: Error message; default is Excpetion's docstring
	:keyword e: Exception class; default is ValidationError
	"""
	if e == None:
		e = SecurityError
	if not msg:
		msg = e.__doc__
	if warning:
		emen2.db.log.warn(msg)
	else:
		raise e(msg)



##### Email #####

# ian: TODO: put this in a separate module
def sendmail(recipient, msg='', subject='', template=None, ctxt=None, ctx=None, txn=None):
	"""(Semi-internal) Send an email. You can provide either a template or a message subject and body.

	:param recipient: Email recipient
	:keyword msg: Message text, or
	:keyword template: ... Template name
	:keyword ctxt: ... Dictionary to pass to template
	:return: Email recipient, or None if no message was sent
	"""
	# ctx and txn arguments don't do anything. I accept them because it's a force of habit to include them.

	mailadmin = emen2.db.config.get('mailsettings.MAILADMIN')
	mailhost = emen2.db.config.get('mailsettings.MAILHOST')

	if not mailadmin:
		emen2.db.log.warn("Couldn't get mail config: No admin email set")
		return
	if not mailhost:
		emen2.db.log.warn("Couldn't get mail config: No SMTP Server")
		return

	ctxt = ctxt or {}
	ctxt["recipient"] = recipient
	ctxt["MAILADMIN"] = mailadmin
	ctxt["EMEN2DBNAME"] = emen2.db.config.get('customization.EMEN2DBNAME', 'EMEN2')
	ctxt["EMEN2EXTURI"] = emen2.db.config.get('network.EMEN2EXTURI', '')

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
			msg = emen2.db.config.templates.render_template(template, ctxt)
		except Exception, e:
			emen2.db.log.warn('Could not render template %s: %s'%(template, e))
			return
	else:
		raise ValueError, "No message to send!"

	# Actually send the message
	s = smtplib.SMTP(mailhost)
	s.set_debuglevel(1)
	s.sendmail(mailadmin, [mailadmin, recipient], msg)
	emen2.db.log.info('Mail sent: %s -> %s'%(mailadmin, recipient))
	# emen2.db.log.error('Could not send email: %s'%e, e=e)
	# raise e

	return recipient


##### EMEN2 Database Environment #####

class EMEN2DBEnv(object):
	"""EMEN2 Database Environment.

	Each DBO table will be available in self.keytypes[keytype].
	"""

	# Manage open btrees
	opendbs = weakref.WeakKeyDictionary()

	# Transaction counter
	txncounter = 0

	# From global configuration
	cachesize = emen2.db.config.get('BDB.CACHESIZE', 1024)
	path = emen2.db.config.get('EMEN2DBHOME')
	create = emen2.db.config.get('params.CREATE')
	snapshot = emen2.db.config.get('params.SNAPSHOT')

	# paths from global configuration
	LOGPATH = emen2.db.config.get('paths.LOGPATH')
	LOG_ARCHIVE = emen2.db.config.get('paths.LOG_ARCHIVE')
	TILEPATH = emen2.db.config.get('paths.TILEPATH')
	TMPPATH = emen2.db.config.get('paths.TMPPATH')
	SSLPATH = emen2.db.config.get('paths.SSLPATH')


	def __init__(self, path=None, create=None, snapshot=False):
		"""
		:keyword path: Directory containing environment.
		:keyword snapshot: Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
		:keyword create: Create the environment if it does not already exist.
		"""

		self.keytypes =  {}

		if path is not None:
			self.path = path

		if not self.path:
			raise ValueError, "No EMEN2 Database Environment specified."

		if create is not None:
			self.create = create

		# Check that all the needed directories exist
		self.checkdirs()

		# Txn info
		self.txnid = 0
		self.txnlog = {}

		# Cache the vartypes that are indexable
		vtm = emen2.db.datatypes.VartypeManager()
		self.indexablevartypes = set()
		for y in vtm.getvartypes():
			y = vtm.getvartype(y)
			if y.keytype:
				self.indexablevartypes.add(y.getvartype())

		# Open DB environment; check if global DBEnv has been opened yet
		ENVOPENFLAGS = \
			bsddb3.db.DB_CREATE | \
			bsddb3.db.DB_INIT_MPOOL | \
			bsddb3.db.DB_INIT_TXN | \
			bsddb3.db.DB_INIT_LOCK | \
			bsddb3.db.DB_INIT_LOG | \
			bsddb3.db.DB_THREAD
			# bsddb3.db.DB_RECOVER
			# bsddb3.db.DB_REGISTER


		# Open the Database Environment
		dbenv = None
		if dbenv == None:
			emen2.db.log.info("Opening Database Environment: %s"%self.path)
			dbenv = bsddb3.db.DBEnv()

			if snapshot or self.snapshot:
				dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)

			cachesize = self.cachesize * 1024 * 1024l
			txncount = (cachesize / 4096) * 2
			if txncount > 1024*128:
				txncount = 1024*128

			dbenv.set_cachesize(0, cachesize)
			dbenv.set_tx_max(txncount)
			dbenv.set_lk_max_locks(300000)
			dbenv.set_lk_max_lockers(300000)
			dbenv.set_lk_max_objects(300000)

			dbenv.open(self.path, ENVOPENFLAGS)
			self.opendbs[self] = 1

		self.dbenv = dbenv

		# Open Databases
		self.init()


	def init(self):
		"""Open the databases."""

		# Authentication
		self.context = emen2.db.context.ContextDB(path="context", dbenv=self)

		# Security items
		self.newuser = emen2.db.user.NewUserDB(path="newuser", dbenv=self)
		self.user = emen2.db.user.UserDB(path="user", dbenv=self)
		self.group = emen2.db.group.GroupDB(path="group", dbenv=self)

		# Main database items
		self.workflow = emen2.db.workflow.WorkFlowDB(path="workflow", dbenv=self)
		self.binary = emen2.db.binary.BinaryDB(path="binary", dbenv=self)
		self.record = emen2.db.record.RecordDB(path="record", dbenv=self)
		self.paramdef = emen2.db.paramdef.ParamDefDB(path="paramdef", dbenv=self)
		self.recorddef = emen2.db.recorddef.RecordDefDB(path="recorddef", dbenv=self)

		# Uploaded files.
		self.upload = emen2.db.binary.BinaryTmpDB(path="upload", dbenv=self)

		# access by keytype..
		self.keytypes = {
			'record': self.record,
			'paramdef': self.paramdef,
			'recorddef': self.recorddef,
			'user': self.user,
			'group': self.group,
			'binary': self.binary,
			'upload': self.upload
		}


	# ian: todo: make this nicer.
	def close(self):
		"""Close the Database Environment"""

		for k,v in self.keytypes.items():
			# print "Closing", v
			v.close()
		self.dbenv.close()


	def __getitem__(self, key, default=None):
		"""Pass dictionary gets to self.keytypes."""
		return self.keytypes.get(key, default)



	##### Utility methods #####

	def checkdirs(self):
		"""Check that all necessary directories exist."""

		checkpath = os.access(self.path, os.F_OK)
		checkconfig = os.access(os.path.join(self.path, 'DB_CONFIG'), os.F_OK)

		# Check if we are creating a new database environment.
		if self.create:
			if checkconfig:
				self.create = False
				# raise ValueError, "Database environment already exists in EMEN2DBHOME directory: %s"%self.path
			if not checkpath:
				os.makedirs(self.path)
		else:
			if not checkpath:
				raise ValueError, "EMEN2DBHOME directory does not exist: %s"%self.path
			if not checkconfig:
				raise ValueError, "No database environment in EMEN2DBHOME directory: %s"%self.path

		paths = [
			"data",
			"log",
			"exts"
			]

		for i in ['record', 'paramdef', 'recorddef', 'user', 'newuser', 'group', 'workflow', 'context', 'binary', 'upload']:
			for j in ['', '/index']:
				paths.append('data/%s%s'%(i,j))

		paths = (os.path.join(self.path, path) for path in paths)
		for path in paths:
			if not os.path.exists(path):
				os.makedirs(path)

		paths = []
		for path in [self.LOGPATH, self.LOG_ARCHIVE, self.TILEPATH, self.TMPPATH, self.SSLPATH]:
			try:
				paths.append(path)
			except AttributeError:
				pass
		paths = [os.makedirs(path) for path in paths if not os.path.exists(path)]

		configpath = os.path.join(self.path,"DB_CONFIG")
		if not os.path.exists(configpath):
			emen2.db.log.info("Copying default DB_CONFIG file: %s"%configpath)
			f = open(configpath, "w")
			f.write(DB_CONFIG)
			f.close()


	def stat():
		"""Print some statistics about the environment."""

		sys.stdout.flush()

		tx_max = self.dbenv.get_tx_max()
		emen2.db.log.info("Open transactions: %s"%tx_max)

		txn_stat = self.dbenv.txn_stat()
		emen2.db.log.info("Transaction stats: ")
		for k,v in txn_stat.items():
			emen2.db.log.info("\t%s: %s"%(k,v))

		log_archive = self.dbenv.log_archive()
		emen2.db.log.info("Archive: %s"%log_archive)

		lock_stat = self.dbenv.lock_stat()
		emen2.db.log.info("Lock stats: ")
		for k,v in lock_stat.items():
			emen2.db.log.info("\t%s: %s"%(k,v))


	##### Transaction management #####

	def newtxn(self, parent=None, write=False):
		"""Start a new transaction.

		:keyword parent: Open new txn as a child of this parent txn
		:keyword write: Transaction will be likely to write data; turns off Berkeley DB Snapshot
		:return: New transaction
		"""

		parent = None
		flags = bsddb3.db.DB_TXN_SNAPSHOT
		if write:
			flags = 0

		txn = self.dbenv.txn_begin(parent=parent, flags=flags) #
		# emen2.db.log.msg('TXN', "NEW TXN, flags: %s --> %s"%(flags, txn))

		type(self).txncounter += 1
		self.txnlog[id(txn)] = txn

		return txn


	def txncheck(self, txnid=0, write=False, txn=None):
		"""Check a transaction status, or create a new transaction.

		:keyword txnid: Transaction ID
		:keyword write: See newtxn
		:keyword txn: An existing open transaction
		:return: Open transaction
		"""

		txn = self.txnlog.get(txnid, txn)
		if not txn:
			txn = self.newtxn(write=write)
		return txn


	def txnabort(self, txnid=0, txn=None):
		"""Abort transaction.

		:keyword txnid: Transaction ID
		:keyword txn: An existing open transaction
		:exception: KeyError if transaction was not found
		"""

		txn = self.txnlog.get(txnid, txn)
		# emen2.db.log.msg('TXN', "TXN ABORT --> %s"%txn)

		if txn:
			txn.abort()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise KeyError, 'Transaction not found'


	def txncommit(self, txnid=0, txn=None):
		"""Commit a transaction.

		:keyword txnid: Transaction ID
		:keyword txn: An existing open transaction
		:exception: KeyError if transaction was not found
		"""

		txn = self.txnlog.get(txnid, txn)
		# emen2.db.log.msg('TXN', "TXN COMMIT --> %s"%txn)

		if txn != None:
			txn.commit()
			if id(txn) in self.txnlog:
				del self.txnlog[id(txn)]
			type(self).txncounter -= 1
		else:
			raise KeyError, 'Transaction not found'

		if DB.sync_contexts.is_set():
			self.context.bdb.sync()
			DB.sync_contexts.clear()


	def checkpoint(self, txn=None):
		"""Checkpoint the database environment."""
		return self.dbenv.txn_checkpoint()



	##### Backup / restore #####

	def log_archive(self, remove=True, checkpoint=False, txn=None):
		"""Archive completed log files.

		:keyword remove: Remove the log files after moving them to the backup location
		:keyword checkpoint: Run a checkpoint first; this will allow more files to be archived
		"""

		outpath = self.LOG_ARCHIVE

		if checkpoint:
			emen2.db.log.info("Log Archive: Checkpoint")
			self.dbenv.txn_checkpoint()

		archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

		emen2.db.log.info("Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

		if not os.access(outpath, os.F_OK):
			os.makedirs(outpath)

		self._log_archive(archivefiles, outpath, remove=remove)


	def _log_archive(self, archivefiles, outpath, remove=False):
		"""(Internal) Backup database log files"""

		outpaths = []
		for archivefile in archivefiles:
			dest = os.path.join(outpath, os.path.basename(archivefile))
			emen2.db.log.info('Log Archive: %s -> %s'%(archivefile, dest))
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
			emen2.db.log.info('Log Archive: Removing %s'%(removefile))
			os.unlink(removefile)

		return removefiles


##### Main Database Class #####

class DB(object):
	"""EMEN2 Database

	This class provides access to the public API methods.
	"""

	extensions = emen2.db.config.get('extensions.EXTS')
	sync_contexts = threading.Event()

	def __init__(self, path=None, create=None):
		"""EMEN2 Database.

		:keyword path: Directory containing an EMEN2 Database Environment.
		:keyword create: Create the environment if it does not already exist.
		"""

		# Open the database
		self.bdbs = EMEN2DBEnv(path=path, create=create)

		#if not hasattr(self.periodic_operations, 'next'):
		#	self.__class__.periodic_operations = self.periodic_operations()

		# Load ParamDefs/RecordDefs from extensions.
		self.load_json(os.path.join(emen2.db.config.get_filename('emen2', 'db'), 'base.json'))
		emen2.db.config.load_jsons(cb=self.load_json)

		# Periodic operations..
		self.lastctxclean = time.time()

		# Cache contexts
		self.contexts_cache = {}

		# Create root account, groups, and root record if necessary
		if self.bdbs.create:
			self.setup()


	def load_json(self, infile):
		"""Load and cache a JSON file containing DBOs."""

		# Create a special root context to load the items
		ctx = emen2.db.context.SpecialRootContext(db=self)
		loader = emen2.db.load.BaseLoader(infile=infile)

		for item in loader.loadfile(keytype='paramdef'):
			pd = self.bdbs.paramdef.dataclass(ctx=ctx, **item)
			self.bdbs.paramdef.addcache(pd)

		for item in loader.loadfile(keytype='recorddef'):
			rd = self.bdbs.recorddef.dataclass(ctx=ctx, **item)
			self.bdbs.recorddef.addcache(rd)


	def __str__(self):
		return "<DB: %s>"%(hex(id(self)))


	##### Open or create new database #####

	@classmethod
	def opendb(cls, name=None, password=None, admin=False, db=None):
		"""Class method to open a database proxy.

		Returns a DBProxy, with either a
		user context (name and password specified), an administrative context
		(admin is True), or no context.

		:keyparam name: Username
		:keyparam password: Password
		:keyparam admin: Open DBProxy with administrative context
		:keyparam db: Use an existing DB instance.
		"""

		# Import here to avoid issues with publicmethod.
		import emen2.db.proxy
		# Use self or create new instance..
		db = db or cls()
		proxy = emen2.db.proxy.DBProxy(db=db)
		if name:
			proxy._login(name, password)
		elif admin:
			ctx = emen2.db.context.SpecialRootContext()
			ctx.refresh(db=proxy)
			proxy._ctx = ctx
		return proxy


	def setup(self, rootpw=None, rootemail=None):
		"""Initialize a new DB.

		@keyparam rootpw Root Account Password
		@keyparam rootemail Root Account email
		"""

		import platform
		def getpw(rootpw=None, rootemail=None):
			host = platform.node() or 'localhost'
			# defaultemail = "%s@%s"%(pwd.getpwuid(os.getuid()).pw_name, host)
			defaultemail = 'root@localhost'
			print "\n=== Setup Admin (root) account ==="
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
			return rootpw, rootemail

		db = self.opendb(db=self, admin=True)
		with db:
			root = db.getuser('root')
			rootpw, rootemail = getpw(rootpw=rootpw, rootemail=rootemail)
			root = {'name':'root','email':rootemail, 'password':rootpw}
			db.put([root], keytype='user')

			loader = emen2.db.load.Loader(db=db, infile=emen2.db.config.get_filename('emen2', 'db/skeleton.json'))
			loader.load()



	##### Utility methods #####

	def _sudo(self, username=None, ctx=None, txn=None):
		"""(Internal) Create an admin context for performing actions that require admin privileges."""
		# print "Temporarily granting user %s administrative privileges"
		ctx = emen2.db.context.SpecialRootContext()
		ctx.refresh(db=self, username=username)
		return ctx


	def _findrecorddefnames(self, names, ctx=None, txn=None):
		"""(Internal) Find referenced recorddefs."""

		recnames, recs, rds = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject)
		rds = set(rds)
		rds |= set([i.rectype for i in recs])
		if recnames:
			grouped = self.groupbyrectype(names, ctx=ctx, txn=txn)
			rds |= set(grouped.keys())
		return rds


	def _findparamdefnames(self, names, ctx=None, txn=None):
		"""(Internal) Find referenced paramdefs."""

		recnames, recs, params = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject)
		params = set(params)
		if recnames:
			recs.extend(self.bdbs.record.cgets(recnames, ctx=ctx, txn=txn))
		for i in recs:
			params |= set(i.keys())
			#rds = set([i.rectype for i in recs])
			#for rd in self.bdbs.recorddef.cgets(rds, ctx=ctx, txn=txn):
			#	params |= set(rd.paramsK)
		return params


	def _findbyvartype(self, names, vartypes, ctx=None, txn=None):
		"""(Internal) Find referenced users/binaries."""
		recnames, recs, values = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject)
		values = set(values)
		# print "getting recs"
		if recnames:
			recs.extend(self.bdbs.record.cgets(recnames, filt=False, ctx=ctx, txn=txn))
		if not recs:
			return values

		# print "getting params"
		# get the params we're looking for
		vtm = emen2.db.datatypes.VartypeManager()
		vt = set()
		vt_iterable = set()
		vt_firstitem = set()
		vt_reduce = set()
		pds = set()
		for rec in recs:
			pds |= set(rec.keys())
		for pd in self.bdbs.paramdef.cgets(pds, ctx=ctx, txn=txn):
			if pd.vartype not in vartypes:
				continue
			vartype = vtm.getvartype(pd.vartype)
			if pd.vartype in ['comments', 'history']:
				vt_firstitem.add(pd.name)
			elif pd.vartype in ['acl']:
				vt_reduce.add(pd.name)
			elif pd.iter:
				vt_iterable.add(pd.name)
			else:
				vt.add(pd.name)

		for rec in recs:
			# print "filtering"
			for param in vt_reduce:
				for j in rec.get(param, []):
					values |= set(j)

			for param in vt_firstitem:
				values |= set([i[0] for i in rec.get(param,[])])

			for param in vt_iterable:
				values |= set(rec.get(param, []))

			for param in vt:
				if rec.get(param):
					values.add(rec.get(param))

		return values


	def _mapput(self, keytype, names, method, ctx=None, txn=None, *args, **kwargs):
		"""(Internal) Get keytype items, run a method with *args **kwargs, and put.

		This method is used to get a bunch of DBOs, run each instance's
		specified method and commit.

		:param keytype: DBO keytype
		:param names: DBO names
		:param method: DBO method
		:param *args: method args
		:param *kwargs: method kwargs
		:return: Results of commit/puts
		"""

		items = self.bdbs.keytypes[keytype].cgets(names, ctx=ctx, txn=txn)
		for item in items:
			getattr(item, method)(*args, **kwargs)
		return self.bdbs.keytypes[keytype].cputs(items, ctx=ctx, txn=txn)


	def _mapput_ol(self, keytype, names, method, default, ctx=None, txn=None, *args, **kwargs):
		"""(Internal) See _mapput."""

		if names is None:
			names = default
		ol, names = listops.oltolist(names)
		ret = self._mapput(keytype, names, method, ctx, txn, *args, **kwargs)
		if ol: return listops.first_or_none(ret)
		return ret


	def _run_macro(self, macro, names, ctx=None, txn=None):
		"""(Internal) Run a macro over a set of Records.

		:param macro: Macro in view format: $@macro(args)
		:param names: Record names
		:return: Macro keytype ('d'/'s'/'f'/None), and dict of processed Records
		"""
		recs = {}
		mrecs = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)

		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)

		regex = VIEW_REGEX
		k = regex.match(macro)

		keytype = vtm.getmacro(k.group('name')).getkeytype()
		vtm.macro_preprocess(k.group('name'), k.group('args'), mrecs)

		for rec in mrecs:
			recs[rec.name] = vtm.macro_process(k.group('name'), k.group('args'), rec)

		return keytype, recs



	##### Events #####

	tasks = []
	# ed: here's an implementation that seems to work, the first time
	#     this class is instantiated, this is called and it is replaced
	#     by the generator that results.  Then, everytime a function is
	#     called, self.periodic_operations.next() is called as well.
	#     this function catches all errors and prints a traceback to
	#     the log so that it doesn't mess up the user's transaction.
	#     also, this function runs all tasks as root and in their own
	#     txn. We could eventually rip this out into a class that defines
	#     next() appropriately, but I don't think its complicated enough
	#     to justify that :)

	def periodic_operations(self):
		"""(Internal) Maintenance task scheduler.
		Eventually this will be replaced with a more complete system."""
		ctx = emen2.db.context.SpecialRootContext(db=self)
		first_run = True
		while 1:
			t = getctime()
			if first_run or t > (self.lastctxclean + 600):
				for task in self.tasks:
					txn = self.bdbs.newtxn()
					try:
							task(self, ctx=ctx, txn=txn)
					except Exception, e:
						txn.abort()
						emen2.db.log.error('Exception in periodic_operations:', e)
					else:
						txn.commit()
					finally:
						self.lastctxclean = t
			if first_run: first_run = False
			yield


	# ian: todo: finish
	# def cleanupcontexts(self, ctx=None, txn=None):
	# 	"""(Internal) Clean up sessions that have been idle too long."""
	# 	newtime = getctime()
	# 	for ctxid, context in self.bdbs.context.items(txn=txn):
	# 		# If the item is in the cache, use the current last-access time..
	# 		c = self.contexts_cache.get(ctxid)
	# 		if c:
	# 			context.time = c.time
	#
	# 		# Delete any expired contexts
	# 		if context.time + (context.maxidle or 0) < newtime:
	# 			emen2.db.log.info("Expire context (%s) %d" % (ctxid, time.time() - context.time))
	# 			self.bdbs.context.delete(ctxid, txn=txn)



	###############################
	# Time and Version Management
	###############################

	@publicmethod("version")
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program.

		Examples:

		>>> db.version()
		2.0rc7

		>>> db.version(program='API')
		2.0rc7

		:keyword program: Check version for this program (API, emen2client, etc.)
		:return: Version string
		"""
		return VERSIONS.get(program)


	@publicmethod("time")
	def gettime(self, ctx=None, txn=None):
		"""Get current time.

		Examples:

		>>> db.time()
		2011-10-10T14:23:11+00:00

		:return: Current time string, YYYY-MM-DDTHH:MM:SS+00:00
		"""
		return gettime()


	@publicmethod('time.difference')
	def timedifference(self, t1, t2=None, ctx=None, txn=None):
		t1 = emen2.db.vartypes.parse_iso8601(t1)[0]
		if t2:
			t2 = emen2.db.vartypes.parse_iso8601(t2)[0]
		else:
			t2 = datetime.datetime.now()
		return t2 - t1


	##### Login and Context Management #####

	@publicmethod("auth.login", write=True)
	def login(self, name="anonymous", password="", host=None, ctx=None, txn=None):
		"""Login.

		Returns auth token (ctxid), or fails with AuthenticationError.

		Examples:

		>>> db.login(name='my.account@example.com', password='foobar')
		654067667525479cba8eb2940a3cf745de3ce608

		>>> db.login(name='ian@example.com', password='fobar')
		AuthenticationError, "Invalid user name, email, or password"

		:keyword name: Account name or email address
		:keyword password: Account password
		:keyword host: Bind auth token to this host. Set by proxy.
		:return: Auth token (ctxid)
		:exception AuthenticationError: Invalid user name, email, or password
		"""

		# Make an anonymous Context
		if name == "anonymous":
			newcontext = emen2.db.context.AnonymousContext(host=host)

		# Try to find the user by account name, or by email
		else:
			# Check the password; user.checkpassword will raise Exception if wrong
			try:
				user = self.bdbs.user.getbyemail(name, filt=False, txn=txn)
				user.checkpassword(password)
			except SecurityError, e:
				raise AuthenticationError, str(e)
			except KeyError, e:
				raise AuthenticationError, AuthenticationError.__doc__

			# Create the Context for this user/host
			newcontext = emen2.db.context.Context(username=user.name, host=host)

		self.bdbs.context.put(newcontext.name, newcontext, txn=txn)
		emen2.db.log.msg('SECURITY', "Login succeeded: %s -> %s" % (name, newcontext.name))

		return newcontext.name


	# Logout is the same as delete context
	### this doesn't work until DB restart (the context isn't immediately cleared)
	@publicmethod("auth.logout", write=True)
	def logout(self, ctx=None, txn=None):
		"""Delete context and logout.

		Examples:

		>>> db.logout()
		None
		"""
		self.contexts_cache.pop(ctx.name, None)
		self.bdbs.context.delete(ctx.name, txn=txn)
		self.sync_contexts.set()


	@publicmethod("auth.check.context")
	def checkcontext(self, ctx=None, txn=None):
		"""Return basic information about the current Context.

		Examples:

		>>> db.checkcontext()
		(ian, set(['admin', 'authenticated']))

		:return: (Context User name, set of Context groups)
		"""
		return ctx.username, ctx.groups


	@publicmethod("auth.check.admin")
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.

		Examples:

		>>> db.checkadmin()
		True

		:return: True if user is an admin
		"""
		return ctx.checkadmin()


	@publicmethod("auth.check.readadmin")
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.

		Examples:

		>>> db.checkreadadmin()
		True

		:return: True if user is a read admin
		"""
		return ctx.checkreadadmin()


	@publicmethod("auth.check.create")
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.

		Examples:

		>>> db.checkcreate()
		True

		:return: True if the user can create records
		"""
		return ctx.checkcreate()


	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Internal) Takes a ctxid key and returns a Context.

		Note: The host provided must match the host in the Context

		:param ctxid: ctxid
		:param host: host
		:return: Context
		:exception: SessionError
		"""

		# Check for any scheduled actions
		# self.periodic_operations(ctx=ctx, txn=txn)

		# Find the context; check the cache first, then the bdb.
		# If no ctxid was provided, make an Anonymous Context.
		if ctxid:
			context = self.contexts_cache.get(ctxid) or self.bdbs.context.get(ctxid, txn=txn)
		else:
			context = emen2.db.context.AnonymousContext(host=host)

		# If no ctxid was found, it's an expired context and has already been cleaned out.
		if not context:
			emen2.db.log.security("Session expired for %s"%ctxid)
			raise SessionError, "Session expired"

		# ian: todo: check referenced groups, referenced records... (complicated.): #groups
		user = None
		grouplevels = {}

		# Fetch the user record and group memberships
		if context.username != 'anonymous':
			indg = self.bdbs.group.getindex('permissions', txn=txn)
			groups = indg.get(context.username, set(), txn=txn)
			grouplevels = {}
			for group in groups:
				group = self.bdbs.group.get(group, txn=txn)
				grouplevels[group.name] = group.getlevel(context.username)

		# Sets the database reference, user record, display name, groups, and updates
		#	context access time.
		context.refresh(grouplevels=grouplevels, host=host, db=self)

		# Keep contexts cached.
		self.contexts_cache[ctxid] = context

		return context



	##### Query #####

	@publicmethod("record.query")
	def query(self, c=None, mode='AND', sortkey='name', pos=0, count=0, reverse=None, keytype="record", ctx=None, txn=None, **kwargs):
		"""General query.

		Constraints are provided in the following format:
			[param, operator, value]

		Operation and value are optional. An arbitrary number of constraints may be given.

		Operators:
			is			or		==
			not			or		!=
			gt			or		>
			lt			or		<
			gte			or		>=
			lte			or		<=
			any
			none
			contains
			contains_w_empty
			noop
			name

		Examples constraints:
			[name, '==', 136]
			['creator', '==', 'ian']
			['rectype', 'is', 'image_capture*']
			['$@recname()', 'noop']
			[['modifytime', '>=', '2011'], ['name_pi', 'contains', 'steve']]

		For record names, parameter names, and protocol names, a '*' can be used to also match children, e.g:
			[['children', 'name', '136*'], ['rectype', '==', 'image_capture*']]
		Will match all children of record 136, recursively, for any child protocol of image_capture.

		The result will be a dictionary containing all the original query arguments, plus:
			names:	Names of records found
			stats:	Query statistics
				length		Number of records found
				time		Execution time

		Examples:

		>>> db.query()
		{'names':[1,2, ...], 'stats': {'time': 0.001, 'length':1234}, 'c': [], ...}

		>>> db.query([['creator', 'is', 'ian']])
		{'names':[1,2,3], 'stats': {'time': 0.002, 'length':3}, 'c': [['creator', 'is', 'ian]], ...}

		>>> db.query([['creator', 'is', 'ian']], sortkey='creationtime', reverse=True)
		{'names':[3,2,1], 'stats': {'time': 0.002, 'length':3}, 'c': [['creator', 'is', 'ian]], 'sortkey': 'creationtime' ...}

		:keyparam c: Constraints
		:keyparam pos: Return results starting from (sorted record name) position
		:keyparam count: Return a limited number of results
		:keyparam sortkey: Sort returned records by this param. Default is creationtime.
		:keyparam reverse: Reverse results
		:keyparam ignorecase: Ignore case when comparing strings
		:return: A dictionary containing the original query arguments, and the result in the 'names' key
		:exception KeyError: Broken constraint
		:exception ValidationError: Broken constraint
		:exception SecurityError: Unable to access specified RecordDefs or other constraint parameters.
		"""
		c = c or []
		ret = dict(
			c=c[:], #copy
			mode=mode,
			sortkey=sortkey,
			pos=pos,
			count=count,
			reverse=reverse,
			ignorecase=True,
			stats={},
			keytype=keytype
		)

		# Run the query
		q = self.bdbs.keytypes[keytype].query(c=c, mode=mode, ctx=ctx, txn=txn)
		q.run()
		ret['names'] = q.sort(sortkey=sortkey, pos=pos, count=count, reverse=reverse)
		ret['stats']['length'] = len(q.result)
		ret['stats']['time'] = q.time
		return ret


	@publicmethod("record.table")
	def table(self, c=None, mode='AND', sortkey='name', pos=0, count=100, reverse=None, viewdef=None, keytype="record", ctx=None, txn=None, **kwargs):
		"""Query results suitable for making a table.

		This method extends query() to include rendered views in the results.
		These are available in the 'rendered' key in the return value. Key is
		the item name, value is a list of the values for each column. The
		headers for each column are in the 'headers' key.

		The maximum number of items returned in the table is 1000.
		"""

		# Limit tables to 1000 items per page.
		if count < 1 or count > 1000:
			count = 1000

		# Records are shown newest-first by default...
		if keytype == "record" and sortkey in ['name', 'recid', 'creationtime'] and reverse is None:
			reverse = True

		c = c or []
		ret = dict(
			c=c[:], # copy
			mode=mode,
			sortkey=sortkey,
			pos=pos,
			count=count,
			reverse=reverse,
			ignorecase=True,
			stats={},
			keytype=keytype
		)

		# Run the query
		q = self.bdbs.keytypes[keytype].query(c=c, mode=mode, ctx=ctx, txn=txn)
		q.run()
		names = q.sort(sortkey=sortkey, pos=pos, count=count, reverse=reverse, rendered=True)

		# Additional time
		t = time.time()

		# Build the viewdef
		defaultviewdef = "$@recname() $@thumbnail() $$rectype $$name"
		rectypes = set(q.cache[i].get('rectype') for i in q.result)
		rectypes -= set([None])

		if not rectypes:
			viewdef = defaultviewdef

		elif not viewdef:
			# todo: move this to q.check('rectype') or similar..
			# Check which views we need to fetch
			toget = []
			for i in q.result:
				if not q.cache[i].get('rectype'):
					toget.append(i)

			if toget:
				rt = self.groupbyrectype(toget, ctx=ctx, txn=txn)
				for k,v in rt.items():
					for name in v:
						q.cache[name]['rectype'] = k

			# Update..
			rectypes = set(q.cache[i].get('rectype') for i in q.result)
			rectypes -= set([None])

			# Get the viewdef
			if len(rectypes) == 1:
				rd = self.bdbs.recorddef.cget(rectypes.pop(), ctx=ctx, txn=txn)
				viewdef = rd.views.get('tabularview', defaultviewdef)
			else:
				try:
					rd = self.bdbs.recorddef.cget("root", filt=False, ctx=ctx, txn=txn)
				except (KeyError, SecurityError):
					viewdef = defaultviewdef
				else:
					viewdef = rd.views.get('tabularview', defaultviewdef)

		# addparamdefs = ["creator","creationtime"]
		addparamdefs = emen2.db.config.get('customization.TABLE_ADD_COLUMNS', ['creator', 'creationtime'])
		for i in addparamdefs:
			viewdef = '%s $$%s'%(viewdef.replace('$$%s'%i, ''), i)

		# Render the table
		table = self.renderview(names, viewdef=viewdef, table=True, edit='auto', ctx=ctx, txn=txn)

		ret['table'] = table
		ret['names'] = names
		ret['stats']['length'] = len(q.result)
		ret['stats']['time'] = q.time + (time.time()-t)
		return ret


	@publicmethod("record.plot")
	def plot(self, c=None, mode='AND', x=None, y=None, z=None, keytype="record", ctx=None, txn=None, **kwargs):
		"""Query results suitable for plotting.

		This method extends query() to help generate a plot. The results are
		not sorted; the sortkey, pos, count, and reverse keyword arguments
		are ignored.

		Provide dictionaries for the x, y, and z keywords. These may have the
		following keys:
			key:	Parameter name for this axis.
			bin:	Number of bins, or date width for time parameters.
			min:	Minimum
			max:	Maximum

		Currently only the 'key' from each x, y, z attribute is used to make
		sure it is part of the query that runs.

		The matching values for each constraint are available in the "items"
		key in the return value. This is a list of stub items.

		"""
		x = x or {}
		y = y or {}
		z = z or {}
		c = c or []
		ret = dict(
			c=c[:],
			x=x,
			y=y,
			z=z,
			mode=mode,
			stats={},
			ignorecase=True,
			keytype=keytype,
		)

		qparams = [i[0] for i in c]
		qparams.append('name')
		for axis in [x.get('key'), y.get('key'), z.get('key')]:
			if axis and axis not in qparams:
				c.append([axis, 'any', None])
		# Run the query
		q = self.bdbs.keytypes[keytype].query(c=c, mode=mode, ctx=ctx, txn=txn)
		q.run()
		ret['names'] = q.result
		ret['recs'] = q.cache.values()
		ret['stats']['length'] = len(q.result)
		ret['stats']['time'] = q.time
		return ret

	##### Other query methods #####

	def _boolmode_collapse(self, rets, boolmode):
		"""(Internal) Perform bool operation on results."""
		if not rets:
			rets = [set()]
		if boolmode == 'AND':
			allret = reduce(set.intersection, rets)
		elif boolmode == 'OR':
			allret = reduce(set.union, rets)
		return allret


	@publicmethod("recorddef.find")
	def findrecorddef(self, *args, **kwargs):
		"""Find a RecordDef, by general search string, or by searching attributes.

		Keywords can be combined.

		Examples:

		>>> db.findrecorddef(query='CCD')
		[<RecordDef ccd>, <RecordDef image_capture>]

		>>> db.findrecorddef(name='image_capture*')
		[<RecordDef ccd>, <RecordDef scan>, <RecordDef micrograph>, ...]

		>>> db.findrecorddef(mainview='freezing apparatus')
		[<RecordDef freezing], <RecordDef vitrobot>, <RecordDef gatan_cp3>, ...]

		>>> db.findrecorddef(record=[1,2,3])
		[<RecordDef folder>, <RecordDef project>]

		>>> db.findrecorddef(name='project*', record='136*')
		[<RecordDef folder>, <RecordDef project>, <RecordDef subproject>, ...]

		:keyword query: Matches any of the following:
		:keyword name: ... contained in name (* for recursive)
		:keyword desc_short: ... contained in short description
		:keyword desc_long: ... contained in long description
		:keyword mainview: ... contained in mainview
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
		:keyword boolmode: AND / OR for each search constraint
		:return: RecordDefs
		"""
		return self._find_pdrd(self._findrecorddefnames, keytype='recorddef', *args, **kwargs)


	@publicmethod("paramdef.find")
	def findparamdef(self, *args, **kwargs):
		"""Find a ParamDef, by general search string, or by searching attributes.

		Keywords can be combined.

		Examples:

		>>> db.findparamdef(query='temperature')
		[<ParamDef temperature>, <ParamDef temperature_ambient>, <ParamDef temperature_cryoholder>, ...]

		>>> db.findparamdef(vartype=binary, record='136*')
		[<ParamDef file_binary>, <ParamDef file_binary_image>, <ParamDef person_photo>, ...]

		:param query: Contained in any item below
		:keyword name: ... contains in name (* for recursive)
		:keyword desc_short: ... contains in short description
		:keyword desc_long: ... contains in long description
		:keyword vartype: ... is of vartype(s)
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
		:keyword boolmode: AND / OR for each search constraint
		:return: RecordDefs
		"""
		return self._find_pdrd(self._findparamdefnames, keytype='paramdef', *args, **kwargs)


	def _find_pdrd_vartype(self, vartype, items):
		"""(Internal) Find RecordDef based on vartype."""
		ret = set()
		vartype = listops.check_iterable(vartype)
		for item in items:
			if item.vartype in vartype:
				ret.add(item.name)
		return ret


	# todo: This should just use the query system.
	def _find_pdrd(self, cb, query=None, childof=None, keytype="paramdef", record=None, vartype=None, ctx=None, txn=None, **qp):
		"""(Internal) Find ParamDefs or RecordDefs based on **qp constraints."""

		rets = []
		# This can still be done much better
		names, items = zip(*self.bdbs.keytypes[keytype].items(ctx=ctx, txn=txn))
		ditems = listops.dictbykey(items, 'name')

		query = unicode(query or '').split()
		for q in query:
			ret = set()
			# Search some text-y fields
			for param in ['name', 'desc_short', 'desc_long', 'mainview']:
				for item in items:
					if q in (item.get(param) or ''):
						ret.add(item.name)
			rets.append(ret)

		if vartype is not None:
			rets.append(self._find_pdrd_vartype(vartype, items))

		if record is not None:
			rets.append(cb(listops.check_iterable(record), ctx=ctx, txn=txn))

		allret = self._boolmode_collapse(rets, boolmode='AND')
		ret = map(ditems.get, allret)

		return ret


	@publicmethod("user.find")
	def finduser(self, query=None, record=None, count=100, ctx=None, txn=None, **kwargs):
		"""Find a user, by general search string, or by name_first/name_middle/name_last/email/name.

		Keywords can be combined.

		Examples:

		>>> db.finduser(name_last='rees')
		[<User ian>, <User kay>, ...]

		>>> db.finduser(record=136)
		[<User ian>, <User steve>, ...]

		>>> db.finduser(email='bcm.edu', record='137*')
		[<User ian>, <User wah>, <User mike>, ...]

		:keyword query: Contained in name_first or name_last
		:keyword email: ... contains in email
		:keyword name_first: ... contains in first name
		:keyword name_middle: ... contains in middle name
		:keyword name_last: ... contains in last name
		:keyword name: ... contains in the user name
		:keyword record: Referenced in Record name(s)
		:keyword count: Limit number of results
		:return: Users
		"""

		foundusers = None
		foundrecs = None
		query = filter(None, [i.strip() for i in unicode(query or '').split()])

		# If no options specified, find all users
		if not any([query, record, kwargs]):
			foundusers = self.bdbs.user.names(ctx=ctx, txn=txn)

		cs = []
		for term in query:
			cs.append([['name_first', 'contains', term], ['name_last', 'contains', term]])
		for param in ['name_first', 'name_middle', 'name_last']:
			if kwargs.get(param):
				cs.append([[param, 'contains', kwargs.get(param)]])
		for c in cs:
			# btree.query supports nested constraints,
			# but I don't have the interface finalized.
			q = self.bdbs.record.query(c=c, mode='OR', ctx=ctx, txn=txn)
			q.run()
			if q.result is None:
				pass
			elif foundrecs is None:
				foundrecs = q.result
			else:
				foundrecs &= q.result

		# Get 'username' from the found records.
		if foundrecs:
			recs = self.bdbs.record.cgets(foundrecs, ctx=ctx, txn=txn)
			f = set([rec.get('username') for rec in recs])
			if foundusers is None:
				foundusers = f
			else:
				foundusers &= f

		# Also search for email and name in users
		cs = []
		if kwargs.get('email'):
			cs.append([['email', 'contains', kwargs.get('email')]])
		if kwargs.get('name'):
			cs.append([['name', 'contains', kwargs.get('name')]])
		for c in cs:
			print c
			q = self.bdbs.user.query(c=c, ctx=ctx, txn=txn)
			q.run()
			if q.result is None:
				pass
			elif foundusers is None:
				foundusers = q.result
			else:
				foundusers &= q.result

		# Find users referenced in a record
		if record:
			f = self._findbyvartype(listops.check_iterable(record), ['user', 'acl', 'comments', 'history'], ctx=ctx, txn=txn)
			if foundusers is None:
				foundusers = f
			else:
				foundusers &= f

		foundusers = sorted(foundusers or [])
		if count:
			foundusers = foundusers[:count]

		return self.bdbs.user.cgets(foundusers or [], ctx=ctx, txn=txn)


	@publicmethod("group.find")
	def findgroup(self, query=None, record=None, count=100, ctx=None, txn=None):
		"""Find a group.

		Keywords can be combined.

		Examples:

		>>> db.findgroup('admin')
		[<Group admin>, <Group readonlyadmin>]

		>>> db.findgroup(record=136)
		[<Group authenticated>, <Group ncmiusers>]

		:keyword query: Find in Group's name or displayname
		:keyword record: Referenced in Record name(s)
		:keyword count: Limit number of results
		:keyword boolmode: AND / OR for each search constraint
		:return: Groups
		"""

		# No real indexes yet (small). Just get everything and sort directly.
		items = self.bdbs.group.cgets(self.bdbs.group.names(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
		ditems = listops.dictbykey(items, 'name')

		rets = []
		query = unicode(query or '').split()

		# If query is empty, match everything. Do this only for findgroups, for now.
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

		allret = self._boolmode_collapse(rets, boolmode='AND')
		ret = map(ditems.get, allret)

		if count:
			return ret[:count]
		return ret



	@publicmethod("record.find.byvalue")
	def findvalue(self, param, query='', choices=True, count=100, ctx=None, txn=None):
		"""Find values for a parameter.

		This is mostly used for interactive UI elements: e.g. combobox.
		More detailed results can be returned by using db.query directly.

		Examples:

		>>> db.findvalue('name_pi')
		[['wah', 124], ['steve', 89], ['ian', 43]], ...]

		>>> db.findvalue('ccd_id', limit=2)
		[['Gatan 4k', 182845], ['Gatan 10k', 48181]]

		>>> db.findvalue('tem_magnification', choices=True, limit=10)
		[[10, ...], [20, ...], [60, ...], [100, ...], ...]

		:param param: Parameter to search
		:keyword query: Value to match
		:keyword choices: Include any parameter-defined choices. These will preceede other results.
		:keyword count: Limit number of results
		:return: [[matching value, count], ...]
		:exception KeyError: No such ParamDef
		"""

		# Use db.plot because it returns the matched values.
		c = [[param, 'contains', query]]
		q = self.plot(c=c, ctx=ctx, txn=txn)

		# Group the values by items.
		inverted = collections.defaultdict(set)
		for rec in q['recs']:
			inverted[rec.get(param)].add(rec.get('name'))

		# Include the ParamDef choices if choices=True.
		pd = self.bdbs.paramdef.cget(param, ctx=ctx, txn=txn)
		if pd and choices:
			choices = pd.get('choices') or []
		else:
			choices = []

		# Sort by the number of items.
		keys = sorted(inverted, key=lambda x:len(inverted[x]), reverse=True)
		keys = filter(lambda x:x not in choices, keys)

		ret = []
		for key in choices + keys:
			ret.append([key, len(inverted[key])])

		if count:
			ret = ret[:count]

		return ret


	# Warning: This can be SLOW!
	@publicmethod("binary.find")
	def findbinary(self, query=None, record=None, count=100, ctx=None, txn=None, **kwargs):
		"""Find a binary by filename.

		Keywords can be combined.

		Examples:

		>>> db.findbinary(filename='dm3')
		[<Binary 2011... test.dm3.gz>, <Binary 2011... test2.dm3.gz>]

		>>> db.findbinary(record=136)
		[<Binary 2011... presentation.ppt>, <Binary 2011... retreat_photo.jpg>, ...]

		:keyword query: Contained in any item below
		:keyword name: ... Binary name
		:keyword filename: ... filename
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
		:keyword boolmode: AND / OR for each search constraint (default: AND)
		:return: Binaries
		"""
		# @keyword min_filesize
		# @keyword max_filesize
		def searchfilenames(filename, txn):
			ind = self.bdbs.binary.getindex('filename', txn=txn)
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
		if record is not None:
			ret = self._findbyvartype(listops.check_iterable(record), ['binary'], ctx=ctx, txn=txn)
			rets.append(ret)
		allret = self._boolmode_collapse(rets, boolmode='AND')
		ret = self.bdbs.binary.cgets(allret, ctx=ctx, txn=txn)
		if count:
			return ret[:count]
		return ret



	##### Grouping #####

	@publicmethod("record.find.byrectype")
	@ol('names', output=False)
	def getindexbyrectype(self, names, ctx=None, txn=None):
		"""Get Record names by RecordDef.

		Note: Not currently filtered for permissions. This is not
		considered sensitive information.

		Examples:

		>>> db.getindexbyrectype('ccd')
		set([4180, 4513, 4514, ...])

		>>> db.getindexbyrectype('image_capture*')
		set([141, 142, 4180, ...])

		>>> db.getindexbyrectype(['scan','micrograph'])
		set([141, 142, 262153, ...])

		:param names: RecordDef name(s)
		:keyword filt: Ignore failures
		:return: Set of Record names
		:exception KeyError: No such RecordDef
		:exception SecurityError: Unable to access RecordDef
		"""
		rds = self.bdbs.recorddef.cgets(names, ctx=ctx, txn=txn)
		ind = self.bdbs.record.getindex("rectype", txn=txn)
		ret = set()
		for i in rds:
			ret |= ind.get(i.name, txn=txn)
		return ret


	@publicmethod("record.group.byrectype")
	@ol('names')
	def groupbyrectype(self, names, filt=True, ctx=None, txn=None):
		"""Group Record(s) by RecordDef.

		Examples:

		>>> db.groupbyrectype([136,137,138])
		{u'project': set([137]), u'subproject': set([138]), u'group': set([136])}

		>>> db.groupbyrectype([<Record instance 1>, <Record instance 2>])
		{u'all_microscopes': set([1]), u'folder': set([2])}

		:param names: Record name(s) or Record(s)
		:keyword filt: Ignore failures
		:return: Dictionary of Record names by RecordDef
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.record.groupbyrectype(names, ctx=ctx, txn=txn)



	##### Record Rendering #####

	#@remove?
	@publicmethod("record.render.children")
	def renderchildtree(self, name, recurse=3, rectype=None, ctx=None, txn=None):
		"""(Deprecated) Convenience method used by some clients to render a bunch of
		records and simple relationships.

		Examples:

		>>> db.renderchildtree(0, recurse=1, rectype=["group"])
		(
			{0: u'EMEN2', 136: u'NCMI', 358307: u'Visitors'},
			{0: set([136, 358307])}
		)

		:param name: Record name
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword filt: Ignore failures
		:return: (Dictionary of rendered views {Record.name:view}, Child tree dictionary)
		:exception SecurityError:
		:exception KeyError:
		"""
		def find_endpoints(tree):
			return set(filter(lambda x:len(tree.get(x,()))==0, set().union(*tree.values())))

		c_all = self.bdbs.record.rel([name], recurse=recurse, tree=True, ctx=ctx, txn=txn)
		c_rectype = self.bdbs.record.rel([name], recurse=recurse, rectype=rectype, ctx=ctx, txn=txn).get(name, set())

		endpoints = find_endpoints(c_all) - c_rectype
		while endpoints:
			for k,v in c_all.items():
				c_all[k] -= endpoints
			endpoints = find_endpoints(c_all) - c_rectype

		rendered = self.renderview(listops.flatten(c_all), ctx=ctx, txn=txn)

		c_all = listops.filter_dict_zero(c_all)

		return rendered, c_all


	def _make_tables(self, recdefs, rec, markup, ctx, txn):
		"""(Internal) Find "out-of-band" parameters."""
		# move built in params to end of table
		#par = [p for p in set(recdefs.get(rec.rectype).paramsK) if p not in builtinparams]
		# Default params
		public = set() | emen2.db.record.Record.attr_public
		show = set(rec.keys()) | recdefs.get(rec.rectype).paramsK | public
		descs = dict((i.name,i.desc_short) for i in self.getparamdef(show, ctx=ctx, txn=txn))
		show -= public
		par = []
		par.extend(sorted(show, key=lambda x:descs.get(x, x)))
		par.extend(sorted(public, key=lambda x:descs.get(x, x)))
		# par = [p for p in recdefs.get(rec.rectype).paramsK if p not in builtinparams]
		# par += [p for p in rec.keys() if p not in par]
		return self._view_dicttable(par, markup=markup, ctx=ctx, txn=txn)


	def _view_dicttable(self, params, paramdefs={}, markup=False, ctx=None, txn=None):
		"""(Internal) Create an HTML table for rendering.

		:param params: Use these ParamDef names
		:keyword paramdefs: ParamDef cache
		:keyword markup: Use HTML Markup (default=False)
		:return: HTML table of params
		"""

		if markup:
			dt = ["""<table class="e2l-kv e2l-shaded" cellspacing="0" cellpadding="0">
					<thead><th>Parameter</th><th>Value</th></thead>
					<tbody>"""]
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


	@publicmethod("record.render")
	@ol('names')
	def renderview(self, names, viewname='recname', viewdef=None, edit=False, markup=True, table=False, mode=None, vtm=None, ctx=None, txn=None):
		"""Render record(s).

		For each record, render the view given either by the viewdef keyword,
		or the viewname keyword in the record's protocol. The default action
		is to render the "recname" view.

		The keywords markup, edit, and table affect rendering. markup=True
		will cause HTML to be returned and, with edit=True, editable parameters
		wrapped in elements with the "e2-edit" class. If table=True, the results
		will differ slightly. Each result will be a list of elements, representing
		each parameter defined in the view, and an additional 'header' item in the
		returned dictionary. Both edit and table will imply markup=True.

		The special view 'dicttable' will returned a markup=True result with each
		record parameter/value pair rendered as a two-column HTML table.

		Examples:

		>>> db.renderview([0, 136, 137])
		{0: u'EMEN2', 136: u'NCMI', 137: u'A Project'}

		>>> db.renderview([0, 136], viewname="mainview")
		{0: u'<p>Folder: EMEN2</p>...', 136: u'<h1><span class="e2-paramdef">Group</span>: NCMI</h1>...'}

		>>> db.renderview([0, 136], viewdef="$$creator $$creationtime")
		{0: u'<p><a href="/user/root">Admin</a> 2007/07/23 10:30:22</p>', 136: u'<p><a href="/user/ian">Rees, Ian</a> 2008/07/05</p>'}

		>>> db.renderview(0, viewname="defaultview", edit=True, markup=True)
		u'<p>Folder: <span class="e2-edit" data-name="0" data-param="name_folder">EMEN2</span>...'

		>>> db.renderview([0], viewname="tabularview", table=True, markup=True)
		{0: [u'<a href="/record/0">EMEN2</a>'], 'headers': {u'folder': [[u'Folder name', u'$', u'name_folder', None]]})}

		:param names: Record name(s)
		:keyword viewdef: View definition
		:keyword viewname: Use this view from the Record's RecordDdef (default='recname')
		:keyword edit: Render with editing HTML markup; use 'auto' for autodetect. (default=False)
		:keyword markup: Render with HTML markup (default=True)
		:keyword table: Return table format (this may go into a separate method) (default=False)
		:keyword mode: Deprecated, no effect.
		:keyword filt: Ignore failures
		:return: Dictionary of {Record.name: rendered view}
		:exception KeyError:
		:exception SecurityError:
		"""

		if viewname == "tabularview":
			table = True

		if viewname == 'recname' and not viewdef:
			markup = False

		if edit:
			markup = True

		# if table:
		# 	edit = "auto"

		# Regular expression for parsing views
		regex = VIEW_REGEX

		# VartypeManager manages the rendering methods
		vtm = vtm or emen2.db.datatypes.VartypeManager(db=ctx.db)

		# We'll be working with a list of names
		# ed: added the *() for better visual grouping :)
		names, recs, newrecs, other = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject, dict)
		other = map(int, other)
		names.extend(other)
		recs.extend(self.bdbs.record.cgets(names, ctx=ctx, txn=txn))

		for newrec in newrecs:
			rec = self.bdbs.record.new(name=None, rectype=newrec.get('rectype'), ctx=ctx, txn=txn)
			#.update(newrec)
			rec.update(newrec)
			recs.append(rec)

		# Get and pre-process views
		groupviews = {}
		recdefs = listops.dictbykey(self.bdbs.recorddef.cgets(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

		if viewdef:
			if markup and markdown:
				viewdef = markdown.markdown(viewdef, ['tables'])
			groupviews[None] = viewdef
		elif viewname == "dicttable":
			for rec in recs:
				groupviews[rec.name] = self._make_tables(recdefs, rec, markup, ctx=ctx, txn=txn)
		else:
			for rd in recdefs.values():
				rd["views"]["mainview"] = rd.mainview

				if viewname in ["tabularview","recname"]:
					v = rd.views.get(viewname, rd.name)

				else:
					v = rd.views.get(viewname, rd.mainview)
					if markdown:
						v = markdown.markdown(v, ['tables'])

				groupviews[rd.name] = v

		# Pre-process once to get paramdefs
		pds = set()
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				if match.group('type') in ["#", "$", '!']:
					pds.add(match.group('name'))

				elif match.group('type') == '@':
					# t = time.time()
					vtm.macro_preprocess(match.group('name'), match.group('args'), recs)

		pds = listops.dictbykey(self.bdbs.paramdef.cgets(pds, ctx=ctx, txn=txn), 'name')

		# Parse views and build header row..
		matches = collections.defaultdict(list)
		headers = collections.defaultdict(list)
		for group, vd in groupviews.items():
			for match in regex.finditer(vd):
				matches[group].append(match)
				# ian: temp fix. I added support for text blocks.
				if not match.group('name'):
					continue
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
			elif viewname == "dicttable":
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
				elif t == '$' or t == '!':
					# t = time.time()
					v = vtm.param_render(pds[n], rec.get(n), name=rec.name, edit=_edit, markup=markup, table=table, embedtype=t)
					# pt[n].append(time.time()-t)
				elif t == '@':
					# t = time.time()
					v = vtm.macro_render(n, match.group('args'), rec, markup=markup, table=table)
					# mt[n].append(time.time()-t)
				else:
					continue

				if table:
					vs.append(v)
				else:
					a = a.replace(match.group(), v+s, 1)

			if table:
				ret[rec.name] = vs
			else:
				ret[rec.name] = a.strip() or '(%s)'%rec.name

		# def pp(t, times):
		# 	for k,v in times.items():
		# 		p = (sum(v), sum(v)/float(len(v)), min(v), max(v))
		# 		p = [t[:5].ljust(5), k[:20].ljust(20)] + [("%2.2f"%i).rjust(5) for i in p] + [str(len(v)).rjust(5)]
		# 		print "   ".join(p)
		# header = ["Type ", "Name".ljust(20), "Total", "  Avg", "  Min", "  Max", "Count"]
		# print "   ".join(header)
		# pp("param", pt)
		# pp("macro", mt)

		if table:
			ret["headers"] = headers

		return ret




	#************************************************************************
	#*	Start: BDB Methods
	#*	Most of these methods are just wrappers for the various
	#* 	BDB/BTree methods.
	#************************************************************************

	# This was incorrectly tagged as an admin method
	@publicmethod("get")
	@ol('names')
	def get(self, names, keytype='record', filt=True, ctx=None, txn=None):
		"""Get item(s).

		This method is effectively the same as:
			db.<keytype>.get(items)

		>>> db.get(0)
		<Record 0, folder>

		>>> db.get([0, 136])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.get('creator', keytype='paramdef')
		<ParamDef creator>

		>>> db.get(['ian', 'steve'], keytype='user')
		[<User ian>, <User steve>]

		:param names: Item name(s)
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return: Item(s)
		:exception KeyError:
		:exception SecurityError:
		"""

		return self.bdbs.keytypes[keytype].cgets(names, filt=filt, ctx=ctx, txn=txn)

	@publicmethod("put", write=True)
	@ol('items')
	def put(self, items, keytype='record', ctx=None, txn=None):
		"""Put item(s).

		This method is effectively the same as:
			db.<keytype>.put(items)

		Examples:

		>>> db.put({'rectype':'folder', 'name_folder':'Test', 'parents':[0]})
		<Record 499203, folder>

		>>> db.put([<Record 0, folder>, <Record 136, group])
		[<Record 0, folder>]

		>>> db.put({'name': 'silly_name', 'vartype':'string', 'desc_short':'Silly name'}, keytype='paramdef')
		<ParamDef silly_name>

		:param items: Item(s) to commit
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return: Updated item(s)
		:exception SecurityError:
		:exception ValidationError:
		"""

		return self.bdbs.keytypes[keytype].cputs(items, ctx=ctx, txn=txn)

	@publicmethod("new")
	def new(self, *args, **kwargs):
		"""Create a new item.

		This method is effectively the same as:
			db.<keytype>.new(*args, **kwargs)

		The keytype keyword is required. See the db.<keytype>.new methods for
		other arguments and keywords.

		Examples:

		>>> db.new(name='sillier_name', vartype='string', keytype='paramdef')
		<ParamDef sillier_name>

		>>> db.new(name='sillier_name', vartype='string', keytype='paramdef')
		SecurityError, "No permission to create ParamDefs"

		>>> db.new(name='sillier_name', vartype='unknown_vartype', keytype='paramdef')
		ValidationError: "Unknown vartype unknown_vartype"

		>>> db.new(rectype='folder', keytype='record')
		ExistingKeyError, "RecordDef folder already exists."

		:keyword keytype:
		:return: New, uncommitted item
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""

		keytype = kwargs.pop('keytype', 'record')
		return dict(
			user = self.newuser,
			group = self.newgroup,
			paramdef = self.newparamdef,
			record = self.newrecord,
			recorddef = self.newrecorddef,
			binary = self.newbinary,
		)[keytype](*args, **kwargs)



	##### Relationships #####

	# This is a new method -- might need some testing.
	@publicmethod("rel.siblings")
	def getsiblings(self, name, rectype=None, keytype="record", ctx=None, txn=None, **kwargs):
		"""Get the siblings of the object as a tree.

		Siblings are any items that share a common parent.

		Examples:

		>>> db.getsiblings(136, rectype='group')
		set([136, 358307])

		>>> db.getsiblings('creationtime', keytype='paramdef')
		set([u'website', u'date_start', u'name_first', u'observed_by', ...])

		>>> db.getsiblings('ccd', keytype='recorddef')
		set([u'ccd', u'micrograph', u'ddd', u'stack', u'scan'])

		:param names: Item name(s)
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return: All items that share a common parent
		:exception KeyError:
		:exception SecurityError:
		"""

		return self.bdbs.keytypes[keytype].siblings(name, rectype=rectype, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.parents.tree")
	@ol('names', output=False)
	def getparenttree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		"""Get the parents of the object as a tree

		This method is the same as as db.rel(rel='parents', tree=True, *args, **kwargs)

		Examples:

		>>> db.getparenttree(46604, recurse=-1)
		{136: set([0]), 46604: set([136])}

		>>> db.getparenttree([46604, 74547], recurse=-1)
		{136: set([0]), 74547: set([136]), 46604: set([136])}

		>>> db.getparenttree([46604, 74547], recurse=-1, rectype='group')
		{74547: set([136]), 46604: set([136])}

		>>> db.getparenttree('ccd', recurse=2, keytype='recorddef')
		{'ccd': set([u'image_capture']), u'image_capture': set([u'tem'])}

		:param names: Item name(s)
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		#:exception MaxRecurseError:
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', tree=True, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.children.tree")
	@ol('names', output=False)
	def getchildtree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		"""Get the children of the object as a tree

		This method is the same as as db.rel(rel='children', tree=True, *args, **kwargs)

		Examples:

		>>> db.getchildtree(0, rectype='group')
		{0: set([136, 358307])}

		>>> db.getchildtree([46604, 74547], rectype='subproject')
		{74547: set([75585, 270211, ...]), 46604: set([380432, 57474, ...])}

		>>> db.getchildtree(136, recurse=2, rectype=['project*'])
		{432645: set([449391]), 268295: set([268296]), 299528: set([460329, 299529]), ...}

		:param names: Item name(s)
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', tree=True, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.parents")
	@ol('names')
	def getparents(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		"""Get the parents of an object

		This method is the same as as db.rel(rel='parents', tree=False, *args, **kwargs)

		Examples:

		>>> db.getparents(0)
		set([])

		>>> db.getparents(46604, recurse=-1)
		set([136, 0])

		>>> db.getparents('ccd', recurse=-1, keytype='recorddef')
		set([u'image_capture', u'experiments', u'root', u'tem'])

		:param names: Item name(s)
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword param keytype: Item keytype
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.children")
	@ol('names')
	def getchildren(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		"""Get the children of an object.

		This method is the same as db.rel(rel='children', tree=False, *args, **kwargs)

		>>> db.rel.children(0)
		set([136, 358307, 270940])

		>>> db.rel.children(0, recurse=2)
		set([2, 4, 268295, 260104, ...])

		>>> db.rel.children(0, recurse=2, rectype=["project*"])
		set([344513, 432645, 237313, 260104, ...])

		>>> db.rel.children('root', keytype='paramdef')
		set([u'core', u'descriptive_information', ...])

		:param names: Item name(s)
		:keyword recurse: Recursion depth
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.rel")
	@ol('names')
	def rel(self, names, keytype="record", recurse=1, rel="children", tree=False, ctx=None, txn=None, **kwargs):
		"""Get relationships.

		Examples:

		See also rel.children(), rel.parents(), rel.children.tree(), rel.parents.tree().

		:param names: Item name(s)
		:keyword keytype: Item keytype
		:keyword recurse: Recursion depth
		:keyword rel: Relationship type: children, parents
		:keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
		:keyword tree: Return tree
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel=rel, tree=tree, ctx=ctx, txn=txn, **kwargs)


	@publicmethod('rel.pclink', write=True)
	def pclink(self, parent, child, keytype='record', ctx=None, txn=None):
		"""Link a parent object with a child

		Examples:

		>>> db.pclink(0, 46604)
		None

		>>> db.pclink('physical_property', 'temperature', keytype='paramdef')
		None

		:param parent: Parent name
		:param child: Child name
		:param keytype: Item type
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].pclink(parent, child, ctx=ctx, txn=txn)


	@publicmethod('rel.pcunlink', write=True)
	def pcunlink(self, parent, child, keytype='record', ctx=None, txn=None):
		"""Remove a parent-child link

		Examples:

		>>> db.pcunlink(0, 46604)
		None

		>>> db.pcunlink('physical_property', 'temperature', keytype='paramdef')
		None

		:param parent: Parent name
		:param child: Child name
		:keyword keytype: Item type
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.keytypes[keytype].pcunlink(parent, child, ctx=ctx, txn=txn)


	@publicmethod('rel.relink', write=True)
	def relink(self, removerels=None, addrels=None, keytype='record', ctx=None, txn=None):
		"""Add and remove a number of parent-child relationships at once.

		Examples:

		>>> db.relink([0,136], [100, 136])
		None

		:keyword removerels: Relationships to remove. Can be a single or list of tuples.
		:keyword addrels: Relationships to add. Can be a single or list of tuples.
		:keyword keytype: Item keytype
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		"""

		# Uses the new .parents/.children attributes to do this simply
		removerels = removerels or []
		addrels = addrels or []
		remove = collections.defaultdict(set)
		add = collections.defaultdict(set)

		# grumble.. Temporary hack. If keytype == record, convert everything to ints.
		if keytype == 'record':
			removerels = [(int(x), int(y)) for x,y in removerels]
			addrels = [(int(x), int(y)) for x,y in addrels]

		for parent, child in removerels:
			remove[parent].add(child)
		for parent, child in addrels:
			add[parent].add(child)

		# print "Adding:", add
		# print "Removing:", remove
		items = set(remove.keys()) | set(add.keys())
		items = self.get(items, keytype=keytype, filt=False, ctx=ctx, txn=txn)
		for item in items:
			item.children -= remove[item.name]
			item.children |= add[item.name]

		return self.bdbs.keytypes[keytype].cputs(items, ctx=ctx, txn=txn)



	###############################
	# User Management
	###############################

	@publicmethod("user.get")
	@ol('names')
	def getuser(self, names, filt=True, ctx=None, txn=None):
		"""Get user information.
		Information may be limited to name and id if the user
		requested additional privacy.

		Examples:

		>>> db.getuser('ian')
		<User ian>

		>>> db.getuser(['ian', 'steve'])
		[<User ian>, <User steve>]

		:param names: User name(s)
		:keyword filt: Ignore failures
		:return: User(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.user.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("user.names")
	def getusernames(self, names=None, ctx=None, txn=None):
		"""Get all accessible user names.

		Examples:

		>>> db.getusernames()
		set([u'ian', u'steve', ...])

		:keyword names: Restrict to this subset of names
		:return: User names
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.user.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("user.put", write=True)
	@ol('items')
	def putuser(self, items, filt=True, ctx=None, txn=None):
		"""Allow a User to change some of their account settings.

		Examples:

		>>> db.putuser({'name':'ian', 'privacy': 1})
		<User ian>

		:param items: User(s)
		:keyword filt: Ignore failures
		:return: Updated user(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.user.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("user.disable", write=True, admin=True)
	def disableuser(self, names, filt=True, ctx=None, txn=None):
		"""(Admin Only) Disable a User.

		Examples:

		>>> db.disableuser('steve')
		<User steve>

		>>> db.disableuser(['wah', 'steve'])
		[<User wah>, <User steve>]

		:param names: User name(s)
		:keyword filt: Ignore failures
		:return: Updated user(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self._mapput('user', names, 'disable', ctx=ctx, txn=txn)


	@publicmethod("user.enable", write=True, admin=True)
	def enableuser(self, names, filt=True, ctx=None, txn=None):
		"""(Admin Only) Re-enable a User.

		Examples:

		>>> db.enableuser('steve')
		<User steve>

		>>> db.enableuser(['wah', 'steve'])
		[<User wah>, <User steve>]

		:param names: User name(s)
		:keyword filt: Ignore failures
		:return: Updated user(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self._mapput('user', names, 'enable', ctx=ctx, txn=txn)


	@publicmethod("user.setprivacy", write=True)
	def setprivacy(self, state, names=None, ctx=None, txn=None):
		"""Set privacy level.

		Examples:

		>>> db.setprivacy(2)
		<User ian>

		>>> db.setprivacy(2, names=['ian', 'wah'])
		[<User ian>, <User wah>]

		:param state: 0, 1, or 2, in increasing level of privacy.
		:keyword names: User name(s). Default is the current context user.
		:return: Updated user(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		# This is a modification of _mapput to allow if names=None
		# ctx.username will be used as the default.
		return self._mapput_ol('user', names, 'setprivacy', ctx.username, ctx, txn, state)



	#####
	# User Email / Password
	# These methods sometimes use put instead of cput because they need to modify
	# the user's secret auth token.
	#####

	@publicmethod("user.setemail", write=True)
	def setemail(self, email, secret=None, password=None, name=None, ctx=None, txn=None):
		"""Change a User's email address.

		This will require you to verify that you own the account by
		responding with an auth token sent to the new email address.
		Use the received auth token to sign the call using the
		'secret' keyword.

		Note: This method only takes a single User name.

		Note: An Admin can change a user's email without the user's password or auth token.

		Examples:

		>>> db.setemail('ian@example.com', password='foobar')
		<User ian>

		>>> db.setemail('ian@example.com', secret='654067667525479cba8eb2940a3cf745de3ce608')
		<User ian>

		:param str email: New email address
		:param str secret: Auth token to verify email address is owned by user.
		:param str password: Current User password
		:param str name: User name. Default is current context user.
		:return: Updated user
		:exception KeyError:
		:exception: :py:class:`SecurityError <SecurityError>` if the password and/or auth token are wrong
		:exception ValidationError:
		"""
		# :exception InvalidEmail:

		#@action
		# Get the record.
		# Keep the existing email address to see if it changes.
		name = name or ctx.username
		ctxt = {}

		# Verify the email address is owned by the user requesting change.
		# 1. User authenticates they *really* own the account
		# 	by providing the acct password
		# 2. An email will be sent to the new account specified,
		# 	containing an auth token
		# 3. The user comes back and calls the method with this token
		# 4. Email address is updated and reindexed

		# Do not use cget; it will strip out the secret.
		user = self.bdbs.user.get(name, filt=False, txn=txn)

		# If we're an admin, the secret and password aren't required,
		# but user._ctx is.
		if ctx.checkadmin():
			user.setContext(ctx)

		# Actually change user email.
		oldemail = user.email
		email = user.setemail(email, password=password, secret=secret)

		#@postprocess
		# Check that no other user is currently using this email.
		ind = self.bdbs.user.getindex('email', txn=txn)
		if ind.get(email, txn=txn) - set([user.name]):
			time.sleep(2)
			raise SecurityError, "The email address %s is already in use"%(email)

		if user.email == oldemail:
			emen2.db.log.msg("SECURITY","Sending email verification for user %s to %s"%(user.name, user.email))
			# The email didn't change, but the secret did
			# Note: cputs will always ignore the secret; write directly
			self.bdbs.user.put(user.name, user, txn=txn)

			# Send the verify email containing the auth token
			ctxt['secret'] = user.secret[2]
			sendmail(email, template='/email/email.verify', ctxt=ctxt, ctx=ctx, txn=txn)

		else:
			# Email changed.
			emen2.db.log.msg("SECURITY","Changing email for user %s to %s"%(user.name, user.email))
			# Note: Since we're putting directly,
			# 	have to force the index to update
			self.bdbs.user.reindex([user], ctx=ctx, txn=txn)
			self.bdbs.user.put(user.name, user, txn=txn)

			# Send the user an email to acknowledge the change
			sendmail(user.email, template='/email/email.verified', ctxt=ctxt)

		return self.bdbs.user.cget(user.name, ctx=ctx, txn=txn)


	@publicmethod("user.setpassword", write=True)
	def setpassword(self, oldpassword, newpassword, secret=None, name=None, ctx=None, txn=None):
		"""Change password.

		Note: This method only takes a single User name.

		The 'secret' keyword can be used for 'password reset' auth tokens. See db.resetpassword().

		Examples:

		>>> db.setpassword('foobar', 'barfoo')
		<User ian>

		>>> db.setpassword(None, 'barfoo', secret=654067667525479cba8eb2940a3cf745de3ce608)
		<User ian>

		:param oldpassword: Old password.
		:param newpassword: New password.
		:keyword secret: Auth token for resetting password.
		:keyword name: User name. Default is the current context user.
		:return: Updated user
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		# :exception InvalidPassword:

		#@action
		# Try to authenticate using either the password OR the secret!
		# Note: The password will be hidden if ctx.username != user.name
		# user = self.bdbs.user.cget(name or ctx.username, filt=False, ctx=ctx, txn=txn)
		#ed: odded 'or ctx.username' to match docs
		user = self.bdbs.user.getbyemail(name or ctx.username, filt=False, txn=txn)
		if not secret:
			user.setContext(ctx)
		user.setpassword(oldpassword, newpassword, secret=secret)

		# ian: todo: evaluate to use put/cput..
		emen2.db.log.msg("SECURITY", "Changing password for %s"%user.name)
		self.bdbs.user.put(user.name, user, txn=txn)

		#@postprocess
		sendmail(user.email, template='/email/password.changed')
		return self.bdbs.user.cget(user.name, ctx=ctx, txn=txn)


	@publicmethod("user.resetpassword", write=True)
	def resetpassword(self, name=None, ctx=None, txn=None):
		"""Reset User password.

		This is accomplished by sending a password reset auth token to the
		User's currently registered email address. Use this auth token
		to sign a call to db.setpassword() using the 'secret' keyword.

		Note: This method only takes a single User name.

		Examples:

		>>> db.resetpassword()
		<User ian>

		:keyword name: User name. Default is the current context user.
		:return: Updated user
		:exception KeyError:
		:exception SecurityError:
		"""

		name = name or ctx.username

		#@action
		user = self.bdbs.user.getbyemail(name, filt=False, txn=txn)
		user.resetpassword()

		# Use direct put to preserve the secret
		self.bdbs.user.put(user.name, user, txn=txn)

		#@postprocess
		# Absolutely never reveal the secret via any mechanism
		# but email to registered address
		ctxt = {'secret': user.secret[2]}
		sendmail(user.email, template='/email/password.reset', ctxt=ctxt)

		emen2.db.log.msg('SECURITY', "Setting resetpassword secret for %s"%user.name)

		return self.bdbs.user.cget(user.name, ctx=ctx, txn=txn)



	##### New Users #####

	@publicmethod("user.queue.names", admin=True)
	def getuserqueue(self, names=None, ctx=None, txn=None):
		"""(Admin only) Get the queue of users awaiting approval.

		Examples:

		>>> db.getuserqueue()
		set(['spambot', 'kay'])

		:keyword names: Restrict to these names
		:keyword filt: Ignore failures
		:return: Set of names of users in the new user queue.
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.newuser.names(names=names, ctx=ctx, txn=txn)


	# Only allow admins!
	@publicmethod("user.queue.get", admin=True)
	@ol('names')
	def getqueueduser(self, names, ctx=None, txn=None):
		"""(Admin Only) Get users from the new user approval queue.

		Examples:

		>>> db.getqueueduser('kay')
		<NewUser kay>

		>>> db.getqeueuduser(['spambot', 'kay'])
		[<NewUser spambot>, <NewUser kay>]

		:param names: New user queue name(s)
		:keyword filt: Ignore failures
		:return: New user(s) from new user queue
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.newuser.cgets(names, ctx=ctx, txn=txn)


	@publicmethod("user.queue.new")
	def newuser(self, name, password, email, ctx=None, txn=None):
		"""Create a new User.

		Examples:

		>>> db.newuser(name='kay', password='foobar', email='kay@example.com')
		<NewUser kay>

		:param name: Desired account name. This will be a random hash if omitted.
		:param password: Password
		:param email: Email Address
		:return: New user
		:exception ExistingKeyError: ExistingKeyError if there is already a user or pending user with this name or email
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.newuser.new(name=name, password=password, email=email, ctx=ctx, txn=txn)


	@publicmethod("user.queue.put", write=True)
	@ol('users')
	def adduser(self, users, ctx=None, txn=None):
		"""Add a new user.

		Note: This only adds the user to the new user queue. The
		account must be processed by an administrator before it
		becomes active.

		Examples:

		>>> db.adduser(<NewUser kay>)
		<NewUser kay>

		>>> db.adduser({'name':'kay', 'password':'foobar', 'email':'kay@example.com'})
		<NewUser kay>

		:param users: New user(s).
		:return: New user(s)
		:exception KeyError:
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""

		users = self.bdbs.newuser.cputs(users, ctx=ctx, txn=txn)
		user_autoapprove = emen2.db.config.get('users.USER_AUTOAPPROVE', False)

		if user_autoapprove:
			# print "Autoapproving........"
			rootctx = self._sudo()
			rootctx.db._txn = txn
			self.approveuser([user.name for user in users], ctx=rootctx, txn=txn)

		elif ctx.checkadmin():
			self.approveuser([user.name for user in users], ctx=ctx, txn=txn)

		else:
			# Send account request email
			for user in users:
				sendmail(user.email, template='/email/adduser.signup')

		return users



	@publicmethod("user.queue.approve", write=True, admin=True)
	@ol('names')
	def approveuser(self, names, secret=None, reject=None, filt=True, ctx=None, txn=None):
		"""(Admin Only) Approve account in user queue.

		Examples:

		>>> db.approveuser('kay')
		<User kay>

		>>> db.approveuser(['kay', 'matt'])
		[<User kay>, <User matt>]

		>>> db.approveuser('kay', secret='654067667525479cba8eb2940a3cf745de3ce608')
		<User kay>

		:param names: New user queue name(s)
		:keyword secret: User secret for self-approval
		:keyword reject: Also reject new users: see db.rejectuser(). For convenience.
		:keyword filt: Ignore failures
		:return: Approved User(s)
		:exception ExistingKeyError:
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""

		# group_defaults = emen2.db.config.get('users.GROUP_DEFAULTS', ['create'])
		user_autoapprove = emen2.db.config.get('users.USER_AUTOAPPROVE', False)

		# Get users from the new user approval queue
		newusers = self.bdbs.newuser.cgets(names, filt=filt, ctx=ctx, txn=txn)
		cusers = []

		# This will also check if the current username or email is in use
		for newuser in newusers:
			name = newuser.name

			# Delete the pending user
			self.bdbs.newuser.delete(name, txn=txn)

			user = self.bdbs.user.new(name=name, email=newuser.email, password=newuser.password, ctx=ctx, txn=txn)
			# Put the new user
			user = self.bdbs.user.cput(user, ctx=ctx, txn=txn)

			# Update default Groups
			# for group in group_defaults:
			#	gr = self.bdbs.group.cget(group, ctx=ctx, txn=txn)
			#	gr.adduser(user.name)
			#	self.bdbs.group.cput(gr, ctx=ctx, txn=txn)

			# Create the "Record" for this user
			rec = self.bdbs.record.new(rectype='person', ctx=ctx, txn=txn)

			# Are there any child records specified...
			childrec = newuser.signupinfo.pop('child', None)

			# This gets updated with the user's signup info
			rec['username'] = name
			rec.update(newuser.signupinfo)
			rec.adduser(name, level=2)
			rec.addgroup("authenticated")
			rec = self.bdbs.record.cput(rec, ctx=ctx, txn=txn)

			# Update the User with the Record name and put again
			user.record = rec.name
			user = self.bdbs.user.cput(user, ctx=ctx, txn=txn)
			cusers.append(user)

			if childrec:
				crec = self.newrecord(rectype=childrec.get('rectype'), ctx=ctx, txn=txn)
				crec.adduser(name, level=3)
				crec.parents.add(rec.name)
				crec.update(childrec)
				crec = self.bdbs.record.cput(crec, ctx=ctx, txn=txn)


		# Send the 'account approved' emails
		for user in cusers:
			user.getdisplayname()
			ctxt = {'name':user.name, 'displayname':user.displayname}
			template = '/email/adduser.approved'
			if user_autoapprove:
				template = '/email/adduser.autoapproved'
			sendmail(user.email, template=template, ctxt=ctxt)

		return self.bdbs.user.cgets(set([user.name for user in cusers]), ctx=ctx, txn=txn)


	@publicmethod("user.queue.reject", write=True, admin=True)
	@ol('names')
	def rejectuser(self, names, filt=True, ctx=None, txn=None):
		"""(Admin Only) Remove a user from the new user queue.

		Examples:

		>>> db.rejectuser('spambot')
		set(['spambot'])

		>>> db.rejectuser(['kay', 'spambot'])
		set(['kay', 'spambot'])

		:param names: New queue name(s) to reject
		:keyword filt: Ignore failures
		:return: Rejected user name(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		#@action
		emails = {}
		users = self.bdbs.newuser.cgets(names, filt=filt, ctx=ctx, txn=txn)
		for user in users:
			emails[user.name] = user.email

		for	user in users:
			self.bdbs.newuser.delete(user.name, txn=txn)

		#@postprocess
		# Send the emails
		for name, email in emails.items():
			ctxt = {'name':name}
			sendmail(email, template='/email/adduser.rejected', ctxt=ctxt)

		return set(emails.keys())



	##### Groups #####

	@publicmethod("group.names")
	def getgroupnames(self, names=None, ctx=None, txn=None):
		"""Get all accessible group names.

		Examples:

		>>> db.getgroupnames()
		set([u'readadmin', u'authenticated', u'admin', u'create', u'publish', u'ncmi', u'anon'])

		>>> db.getgroupnames(names=['admin','create'])
		set(['admin', 'create'])

		:keyword names: Restrict to this subset.
		:keyword filt: Ignore failures
		:return: Set of all Group names.
		:exception KeyError:
		:exception SecurityError:
		"""
		# ian: todo: fix keyword names argument.
		return self.bdbs.group.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("group.get")
	@ol('names')
	def getgroup(self, names, filt=True, ctx=None, txn=None):
		"""Get a Group.

		Examples:

		>>> db.getgroup('admin')
		<Group admin>

		>>> db.getgroup(['create', 'admin'])
		[<Group admin>, <Group create>]

		:param names: Group name(s)
		:keyword filt: Ignore failures
		:return: Group(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.group.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("group.new")
	def newgroup(self, name, ctx=None, txn=None):
		"""Construct a new Group.

		Examples:

		>>> db.newgroup(name='demo')
		<Group demo>

		>>> db.newgroup(name='admin')
		ExistingKeyError, "There is already a group with the name 'admin'."

		:param name: Group name
		:return: New Group
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.group.new(name=name, ctx=ctx, txn=txn)


	@publicmethod("group.put", write=True, admin=True)
	@ol('items')
	def putgroup(self, items, ctx=None, txn=None):
		"""Add or update Group(s).

		Examples:

		>>> db.putgroup({'name':'demo', 'displayname': 'Demo', 'permissions':[['ian','wah'],[],[],[]]))
		<Group demo>

		>>> db.putgroup([<Group admin>, <Group readadmin>])
		[<Group admin>, <Group readadmin>]

		:param items: Group(s)
		:return: Updated Group(s)
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.group.cputs(items, ctx=ctx, txn=txn)



	##### ParamDefs #####

	@publicmethod("paramdef.vartypes")
	def getvartypenames(self, ctx=None, txn=None):
		"""Get all supported datatypes.

		A number of parameter data types (vartypes) are included by default.
		Extensions may add extend this by subclassing emen2.db.vartypes.Vartype()
		and using the registration decorator. See that module for details.

		Examples:

		>>> db.getvartypenames()
		set(['text', 'string', 'binary', 'user', ...])

		:return: Set of all available datatypes.
		"""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getvartypes())


	@publicmethod("paramdef.properties")
	def getpropertynames(self, ctx=None, txn=None):
		"""Get all supported physical properties.

		A number of physical properties are included by default.
		Extensions may extend this by subclassing emen2.db.properties.Property()
		and using the registration decorator. See that module for details.

		>>> db.getpropertynames()
		set(['transmittance', 'force', 'bytes', 'energy', 'resistance', ...])

		:return: Set of all available properties.
		"""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getproperties())


	@publicmethod("paramdef.units")
	def getpropertyunits(self, name, ctx=None, txn=None):
		"""Returns a list of recommended units for a particular property.
		Other units may be used if they can be converted to the property's
		default units.

		Examples:

		>>> db.getpropertyunits('volume')
		set(['nL', 'mL', 'L', 'uL', 'gallon', 'm^3'])

		>>> db.getpropertyunits('length')
		set([u'\xc5', 'nm', 'mm', 'm', 'km', 'um'])

		:param name: Property name
		:return: Set of recommended units for property.
		:exception KeyError:
		"""
		if not name:
			return set()
		vtm = emen2.db.datatypes.VartypeManager()
		prop = vtm.getproperty(name)
		return set(prop.units)


	@publicmethod("paramdef.new")
	def newparamdef(self, name, vartype, ctx=None, txn=None):
		"""Construct a new ParamDef.

		Examples:

		>>> db.newparamdef(name='silly_name', vartype='string')
		<ParamDef silly_name>

		:param name: ParamDef name
		:param vartype: ParamDef vartype
		:keyword inherit:
		:return: New ParamDef
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.paramdef.new(name=name, vartype=vartype, ctx=ctx, txn=txn)


	@publicmethod("paramdef.put", write=True)
	@ol('items')
	def putparamdef(self, items, ctx=None, txn=None):
		"""Add or update ParamDef(s).

		Examples:

		>>> db.putparamdef(<ParamDef silly_name>)
		<ParamDef silly_name>

		>>> db.putparamdef({'name':'silly_name', 'desc_short':'A silly name'})
		<ParamDef silly_name>

		:param items: ParamDef(s)
		:return: Updated ParamDef(s)
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.paramdef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("paramdef.get")
	@ol('names')
	def getparamdef(self, names, filt=True, ctx=None, txn=None):
		"""Get ParamDefs.

		Examples:

		>>> db.getparamdef('creator')
		<ParamDef creator>

		>>> db.getparamdef(['silly_name', 'creator', 'modifyuser'])
		[<ParamDef silly_name>, <ParamDef creator>, <ParamDef modifyuser>]

		:param names: ParamDef name(s)
		:keyword filt: Ignore failures
		:return: ParamDef(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.paramdef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("paramdef.names")
	def getparamdefnames(self, names=None, ctx=None, txn=None):
		"""Get all ParamDef names.

		Examples:

		>>> db.getparamdefnames()
		set(['creator', 'creationtime', 'permissions', ...])

		>>> db.getparamdefnames(names=['name_first', 'name_last', 'unknown_parameter'])
		set(['name_first', 'name_last'])

		:keyword names: Restrict to this subset.
		:keyword filt: Ignore failures
		:return: Set of all ParamDef names.
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.paramdef.names(names=names, ctx=ctx, txn=txn)



	##### RecordDefs #####

	@publicmethod("recorddef.new")
	def newrecorddef(self, name, mainview, ctx=None, txn=None):
		"""Construct a new RecordDef.

		A name for the RecordDef and the RecordDef main protocol description
		(mainview) are required.

		Examples:

		>>> db.newrecorddef(name='dna_miniprep', mainview='DNA purification. $#performed_by: $$performed_by')
		<RecordDef dna_miniprep>

		>>> db.newrecorddef(name='folder', mainview='Folder')
		ExistingKeyError: 'folder' already exists

		:param name: RecordDef name
		:param mainview: RecordDef main protocol description (mainview)
		:return: New RecordDef
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.recorddef.new(name=name, mainview=mainview, ctx=ctx, txn=txn)


	@publicmethod("recorddef.put", write=True)
	@ol('items')
	def putrecorddef(self, items, ctx=None, txn=None):
		"""Add or update RecordDef(s).

		Note: RecordDef main protocol descriptions (mainview) should never
		be changed once used, since this will change the meaning of data
		already in the database.

		Examples:

		>>> db.putrecorddef(<RecordDef folder>)
		<RecordDef folder>

		>>> db.putrecorddef([<RecordDef folder>, <RecordDef project>])
		[<RecordDef folder>, <RecordDef project>]

		>>> db.putrecorddef({'name':'folder', ...., {'views':{'recname':'Folder: $$creator'}}})
		<RecordDef folder>

		>>> db.putrecorddef({'name':'dna_miniprep', 'mainview': 'DNA purification....', 'desc_short':'DNA miniprep'})
		<RecordDef dna_miniprep>

		>>> db.putrecorddef({'name':'folder', mainview:'Changed mainview', ....})
		ValidationError: Cannot change mainview.

		:param items: RecordDef(s)
		:return: Updated RecordDef(s)
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.recorddef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("recorddef.get")
	@ol('names')
	def getrecorddef(self, names, filt=True, ctx=None, txn=None):
		"""Get RecordDef(s).

		Examples:

		>>> db.getrecorddef('folder')
		<RecordDef folder>

		>>> db.getrecorddef(['folder', 'project'])
		[<RecordDef folder>, <RecordDef project>]

		>>> db.getrecorddef(['folder', 'unknown_recorddef'], filt=True)
		[<RecordDef folder>]

		:param names: RecordDef name(s)
		:keyword filt: Ignore failures
		:return: RecordDef(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.recorddef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("recorddef.names")
	def getrecorddefnames(self, names=None, ctx=None, txn=None):
		"""Get all RecordDef names.

		Examples:

		>>> db.getrecorddefnames()
		set(['folder', 'project', 'person', ...])

		>>> db.getrecorddefnames(['folder', 'project', 'unknown_recorddef'])
		set(['folder', 'project'])

		>>> db.getrecorddefnames(['folder', 'project', 'unknown_recorddef'], filt=False)
		KeyError, "No such key unknown_recorddef"

		:keyword names: Restrict to this subset.
		:keyword filt: Ignore failures
		:return: All RecordDef names.
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.recorddef.names(names=names, ctx=ctx, txn=txn)



	##### Records #####

	@publicmethod("record.get")
	@ol('names')
	def getrecord(self, names, filt=True, ctx=None, txn=None):
		"""Get Record(s).

		Examples:

		>>> db.getrecord(0)
		<Record 0, folder>

		>>> db.getrecord([0, 136])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.getrecord([0, 136, -1, 181828], filt=True)
		[<Record 0, folder>, <Record 136, group>]

		>>> db.getrecord([0, 136, 181828], filt=False)
		KeyError

		:param names: Record name(s)
		:keyword filt: Ignore failures
		:return: Record(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		return self.bdbs.record.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("record.new")
	def newrecord(self, rectype, inherit=None, ctx=None, txn=None):
		"""Construct a new Record.

		Examples:

		>>> db.newrecord('folder')
		<Record None, folder>

		>>> db.newrecord('folder', inherit=0)
		<Record None, folder>

		>>> db.newrecord('folder')
		SecurityError

		>>> db.newrecord('unknown_recorddef')
		ValidationError

		:param rectype: RecordDef name
		:keyword inherit: Use these Record(s) as parents, and copy their permissions.
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
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
			except (KeyError, SecurityError), inst:
				emen2.db.log.warn("Couldn't get inherited permissions from record %s: %s"%(inherit, inst))

			rec["parents"] |= inherit

		# Let's try this and see how it works out...
		rec['date_occurred'] = gettime()
		rec['performed_by'] = ctx.username

		return rec


	@publicmethod("record.hide", write=True)
	@ol('names')
	def hiderecord(self, names, childaction=None, filt=True, ctx=None, txn=None):
		"""Unlink and hide a record; it is still accessible to owner.
		Records are never truly deleted, just hidden.

		Examples:

		>>> db.hiderecord(136)
		<Record 136 group>

		>>> db.hiderecord([136, 137])
		[<Record 136 group>]

		>>> db.hiderecord([136, 137], filt=False)
		SecurityError

		>>> db.hiderecord(12345, filt=False)
		KeyError

		:param name: Record name(s) to delete
		:keyword filt: Ignore failures
		:return: Deleted Record(s)
		:exception KeyError:
		:exception SecurityError:
		"""

		names = set(names)

		if childaction == 'orphaned':
			names |= self.findorphans(names, ctx=ctx, txn=txn)
		elif childaction == 'all':
			c = self.getchildren(names, ctx=ctx, txn=txn)
			for k,v in c.items():
				names |= v
				names.add(k)

		self.bdbs.record.delete(names, ctx=ctx, txn=txn)


	@publicmethod("record.findorphans")
	def findorphans(self, names, root=0, keytype='record', ctx=None, txn=None):
		"""Find orphaned items that would occur if names were hidden.
		@param name Return orphans that would result from deletion of these items
		@return Orphaned items
		"""

		names = set(names)

		children = self.getchildtree(names, recurse=-1, ctx=ctx, txn=txn)
		allchildren = set()
		allchildren |= names
		for k,v in children.items():
			allchildren.add(k)
			allchildren |= v

		parents = self.getparenttree(allchildren, ctx=ctx, txn=txn)

		# Find a path back to root for each child
		orphaned = set()
		for child in allchildren:
			visited = set()
			stack = set() | parents.get(child, set())
			while stack:
				cur = stack.pop()
				visited.add(cur)
				stack |= (parents.get(cur, set()) - names)
			if root not in visited:
				orphaned.add(child)

		return orphaned - names



	@publicmethod("record.addcomment", write=True)
	@ol('names')
	def addcomment(self, names, comment, filt=True, ctx=None, txn=None):
		"""Add comment to a record.

		Requires comment permissions on that Record.

		Examples:

		>>> db.addcomment(136, 'Test comment')
		<Record 136, group>

		>>> db.addcomment(137, 'No comment permissions!?')
		SecurityError

		>>> db.addcomment(12345, 'Record does not exist')
		KeyError

		:param name: Record name(s)
		:param comment: Comment text
		:keyparam filt: Ignore failures
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'addcomment', ctx, txn, comment)


	@publicmethod("record.find.comments")
	@ol('names', output=False)
	def getcomments(self, names, filt=True, ctx=None, txn=None):
		"""Get comments from Records.

		Note: This method always returns a list of items, even if only one record
			is specified, or only one comment is found.

		Examples:

		>>> db.getcomments(1)
		[[1, u'root', u'2010/07/19 14:43:03', u'Record marked for deletion and unlinked from parents: 270940']]

		>>> db.getcomments([1, 138])
		[[1, u'root', u'2010/07/19 14:43:03', u'Record marked...'], [138, u'ianrees', u'2011/10/01 02:28:51', u'New comment']]

		:param names: Record name(s)
		:keyword filt: Ignore failures
		:return: A list of comments, with the Record ID as the first item@[[recid, username, time, comment], ...]
		:exception KeyError:
		:exception SecurityError:
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

		return sorted(ret, key=lambda x:x[2])
		# return sorted(ret, key=operator.itemgetter(2))



	##### Record Updates #####

	@publicmethod("record.update", write=True)
	@ol('names')
	def putrecordvalues(self, names, update, ctx=None, txn=None):
		"""Convenience method to update Records.

		Examples:

		>>> db.putrecordvalues([0,136], {'performed_by':'ian'})
		[<Record 0, folder>, <Record 136, group>]

		>>> db.putrecordvalues([0,136, 137], {'performed_by':'ian'}, filt=False)
		SecurityError

		:param names: Record name(s)
		:param update: Update Records with this dictionary
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'update', ctx, txn, update)


	@publicmethod("record.validate")
	@ol('items')
	def validaterecord(self, items, ctx=None, txn=None):
		"""Check that a record will validate before committing.

		Examples:

		>>> db.validaterecord([{'rectype':'folder', 'name_folder':'Test folder'}, {'rectype':'folder', 'name_folder':'Another folder'}])
		[<Record None, folder>, <Record None, folder>]

		>>> db.validaterecord([<Record 499177, folder>, <Record 499178, folder>])
		[<Record 499177, folder>, <Record 499178, folder>]

		>>> db.validaterecord({'rectype':'folder', 'performed_by':'unknown_user'})
		ValidationError

		>>> db.validaterecord({'name':136, 'name_folder':'No permission to edit..'})
		SecurityError

		>>> db.validaterecord({'name':12345, 'name_folder':'Unknown record'})
		KeyError

		:param items: Record(s)
		:return: Validated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.record.validate(items, ctx=ctx, txn=txn)


	@publicmethod("record.put", write=True)
	@ol('items')
	def putrecord(self, items, filt=True, ctx=None, txn=None):
		"""Add or update Record.

		Examples:

		>>> db.putrecord({'rectype':'folder', 'name_folder':'Test folder'})
		<Record 499176, folder>

		>>> db.putrecord([{'rectype':'folder', 'name_folder':'Test folder'}, {'rectype':'folder', 'name_folder':'Another folder'}])
		[<Record 499177, folder>, <Record 499178, folder>]

		>>> db.putrecord([<Record 499177, folder>, <Record 499178, folder>])
		[<Record 499177, folder>, <Record 499178, folder>]

		>>> db.putrecord([<Record 499177, folder>, <Record 499178, folder>], filt=False)
		SecurityError

		>>> db.putrecord({'rectype':'folder', 'performed_by':'unknown_user'})
		ValidationError

		:param items: Record(s)
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.record.cputs(items, ctx=ctx, txn=txn)



	##### Record Permissions #####

	# These map to the normal Record methods
	@publicmethod("record.adduser", write=True)
	@ol('names')
	def addpermission(self, names, users, level=0, ctx=None, txn=None):
		"""Add users to a Record's permissions.

		>>> db.addpermission(0, 'ian')
		<Record 0, folder>

		>>> db.addpermission([0, 136], ['ian', 'steve'])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.addpermission([0, 136], ['ian', 'steve'], filt=False)
		SecurityError

		:param names: Record name(s)
		:param users: User name(s) to add
		:keyword filt: Ignore failures
		:keyword level: Permissions level; 0=read, 1=comment, 2=write, 3=owner
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'adduser', ctx, txn, users)


	@publicmethod("record.removeuser", write=True)
	@ol('names')
	def removepermission(self, names, users, ctx=None, txn=None):
		"""Remove users from a Record's permissions.

		Examples:

		>>> db.removepermission(0, 'ian')
		<Record 0, folder>

		>>> db.removepermission([0, 136], ['ian', 'steve'])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.removepermission([0, 136], ['ian', 'steve'], filt=False)
		SecurityError

		:param names: Record name(s)
		:param users: User name(s) to remove
		:keyword filt: Ignore failures
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'removeuser', ctx, txn, users)


	@publicmethod("record.addgroup", write=True)
	@ol('names')
	def addgroup(self, names, groups, ctx=None, txn=None):
		"""Add groups to a Record's permissions.

		Examples:

		>>> db.addgroup(0, 'authenticated')
		<Record 0, folder>

		>>> db.addgroup([0, 136], 'authenticated')
		[<Record 0, folder>, <Record 136, group>]

		>>> db.addgroup([0, 136], ['anon', 'authenticated'])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.addgroup([0, 136], 'authenticated', filt=False)
		SecurityError

		:param names: Record name(s)
		:param groups: Group name(s) to add
		:keyword filt: Ignore failures
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'addgroup', ctx, txn, groups)


	@publicmethod("record.removegroup", write=True)
	@ol('names')
	def removegroup(self, names, groups, ctx=None, txn=None):
		"""Remove groups from a Record's permissions.

		Examples:

		>>> db.removegroup(0, 'authenticated')
		<Record 0, folder>

		>>> db.removegroup([0, 136], 'authenticated')
		[<Record 0, folder>, <Record 136, group>]

		>>> db.removegroup([0, 136], ['anon', 'authenticated'])
		[<Record 0, folder>, <Record 136, group>]

		>>> db.removegroup([0, 136], 'authenticated', filt=False)
		SecurityError

		:param names: Record name(s)
		:param groups: Group name(s)
		:keyword filt: Ignore failures
		:return: Updated Record(s)
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self._mapput('record', names, 'removegroup', ctx, txn, groups)



	# This method is for compatibility with the web interface widget..
	@publicmethod("record.setpermissions_compat", write=True)
	@ol('names')
	def setpermissions(self, names, addumask=None, addgroups=None, removeusers=None, removegroups=None, recurse=None, overwrite_users=False, overwrite_groups=False, filt=True, ctx=None, txn=None):
		"""Update a Record's permissions.

		This method is mostly for convenience and backwards compatibility.

		Examples:

		>>> db.setpermissions(names=[137, 138], addumask=[['ian'], [], [], []])

		>>> db.setpermissions(names=[137], recurse=-1, addumask=[['ian', 'steve'], [], [], ['wah']])

		>>> db.setpermissions(names=[137], recurse=-1, removegroups=['anon'], addgroups=['authenticated])

		>>> db.setpermissions(names=[137], recurse=-1, addgroups=['authenticated'], overwrite_groups=True)

		>>> db.setpermissions(names=[137], recurse=-1, addgroups=['authenticated'], overwrite_groups=True, filt=False)
		SecurityError

		:param names: Record name(s)
		:keyword addumask: Add this permissions mask to the record's current permissions.
		:keyword addgroups: Add these groups to the records' current groups.
		:keyword removeusers: Remove these users from each record.
		:keyword removegroups: Remove these groups from each record.
		:keyword recurse: Recursion depth
		:keyword overwrite_users: Overwrite the permissions of each record to the value of addumask.
		:keyword overwrite_groups: Overwrite the groups of each record to the value of addgroups.
		:keyword filt: Ignore failures
		:return:
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""

		recs = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)
		crecs = []

		for rec in recs:
			# Get the record and children
			children = [rec]
			if recurse:
				c = self.bdbs.record.rel([rec.name], recurse=recurse, ctx=ctx, txn=txn).get(rec.name, set())
				c = self.bdbs.record.cgets(c, ctx=ctx, txn=txn)
				children.extend(c)

			# Apply the operations
			for crec in children:
				# Filter out items we can't edit..
				if not crec.isowner() and filt:
					continue

				if removeusers:
					crec.removeuser(removeusers)

				if removegroups:
					crec.removegroup(removegroups)

				if overwrite_users:
					crec['permissions'] = addumask
				elif addumask:
					crec.addumask(addumask)

				if overwrite_groups:
					crec['groups'] = addgroups
				elif addgroups:
					crec.addgroup(addgroups)

				crecs.append(crec)

		return self.bdbs.record.cputs(crecs, ctx=ctx, txn=txn)



	##### Binaries #####

	@publicmethod("binary.get")
	@ol('names')
	def getbinary(self, names=None, filt=True, ctx=None, txn=None):
		"""Get Binaries.

		Examples:

		>>> db.getbinary('bdo:2011101000000')
		<Binary bdo:2011101000000>

		>>> db.getbinary(['bdo:2011101000000', 'bdo:2011101000001', 'bdo:2011101000002'], filt=True)
		[<Binary bdo:2011101000000>, <Binary bdo:2011101000001>]

		>>> db.getbinary(['bdo:2011101000000', 'bdo:2011101000001', 'bdo:2011101000002'], filt=False)
		KeyError

		:param names: Binary name(s). Also, for backwards compat, accepts Record name(s)
		:keyword bool filt: Ignore failures
		:return: Binary(s)
		:exception KeyError:
		:exception SecurityError:
		"""
		# This call to findbinary is a deprecated feature
		# that remains for backwards compat
		bdos, recnames, other = listops.typepartition(names, str, int)
		if len(recnames) > 0:
			return self.findbinary(record=recnames, count=0, ctx=ctx, txn=txn)
		return self.bdbs.binary.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("binary.new")
	def newbinary(self, ctx=None, txn=None):
		"""Construct a new Binary.

		Note: This is not very useful. Instead, use the
			keyword arguments to db.putbinary():
			infile, filename, record, param.

		Examples:

		>>> db.newbinary()
		<Binary None at 10d9e1950>

		:return: New Binary
		:exception ExistingKeyError:
		:exception SecurityError:
		:exception ValidationError:
		"""
		return self.bdbs.binary.new(name=None, ctx=ctx, txn=txn)


	@publicmethod("binary.put", write=True)
	@ol('items')
	def putbinary(self, items, extract=False, ctx=None, txn=None):
		"""Add or update a Binary (file attachment).

		For new items, data must be supplied using with either
		bdo.get('filedata') or bdo.get('fileobj').

		The contents of a Binary cannot be changed after uploading. The file
		size and md5 checksum will be calculated as the file is written to
		binary storage. Any attempt to change the contents raise a
		SecurityError. Not even admin users may override this.

		Examples:

		>>> db.putbinary({filename='hello.txt', filedata='Hello, world', record=0})
		<Binary bdo:2011101000000>

		>>> db.putbinary({'name':'bdo:2011101000000', 'filename':'newfilename.txt'})
		<Binary bdo:2011101000000>

		>>> db.putbinary({'name':'bdo:2011101000000', 'filedata':'Goodbye'})
		SecurityError

		:param item: Binary
		:exception SecurityError:
		:exception ValidationError:
		"""

		bdos = []
		rename = []
		for bdo in items:
			# New BDO details
			newfile = False
			handler = None
			rec = None
			param = bdo.get('param', 'file_binary') # keep this

			# Test that we can write to the record, this will catch errors before we do alot of file IO.
			if bdo.get('record') is not None:
				rec = self.bdbs.record.cget(bdo.get('record'), ctx=ctx, txn=txn)
				if not rec.writable():
					raise SecurityError, "No write permissions for Record %s"%rec.name

			# If this is a new item, go through newbinary to create a new Binary from the Handler
			if not bdo.get('name'):
				# Create a new binary from the Handler details; keep the Handler around
				handler = bdo
				bdo = self.bdbs.binary.new(filename=handler.get('filename'), record=handler.get('record'), ctx=ctx, txn=txn)

				# Write the file to temporary storage. This will update the
				# filesize and MD5. This will generally be the same
				# filesystem as the final file location, so the final
				# operation in this method will be a rename operation. But in
				# situations where the file storage area changes between the
				# time the temp file is written and the sequence is updated,
				# it will require a copy and remove operation.
				newfile = bdo.writetmp(filedata=handler.get('filedata', None), fileobj=handler.get('fileobj', None))

			# Commit the BDO. This will set the Binary's name.
			bdo = self.bdbs.binary.cput(bdo, ctx=ctx, txn=txn)
			bdos.append(bdo)

			# If this is a new BDO.. Please excuse this complicated block.
			if newfile:
				# Check that we won't be overwriting an existing file.
				# Note: it's possible that an aborted txn left files...
				# if os.path.exists(bdo.filepath):
				#	raise SecurityError, "Cannot overwrite existing file!"
				# Add to the list of files to rename/copy.
				rename.append([newfile, bdo.filepath])

				# Update the referenced record.
				if rec:
					# Extract any file metadata..
					if handler:
						header = {}
						try:
							header = handler.extract()
						except Exception, e:
							emen2.db.log.info("Could not extract metadata: %s"%e)

						# Update the record from the file metadata
						rec.update(header)

					pd = self.bdbs.paramdef.cget(param, ctx=ctx, txn=txn)
					if pd.vartype != 'binary':
						raise KeyError, "ParamDef %s does not accept file attachments"%pd.name

					if pd.iter:
						v = rec.get(pd.name) or []
						v.append(bdo.name)
					else:
						v = bdo.name
					rec[pd.name] = v

					# Commit the record
					self.bdbs.record.cput(rec, ctx=ctx, txn=txn)


		# Rename/copy temporary files to final destination.
		# todo: Handle exceptions.
		for newfile, filepath in rename:
			os.rename(newfile, filepath)

		# Run the thumbnail generator
		# for bdo in bdos:
		#	emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)

		return bdos


	##### Temporary binaries #####

	@publicmethod("upload.get")
	@ol('names')
	def getupload(self, names=None, filt=True, ctx=None, txn=None):
		return self.bdbs.upload.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("upload.new")
	def newupload(self, ctx=None, txn=None):
		return self.bdbs.upload.new(name=None, ctx=ctx, txn=txn)
	
	
	@publicmethod("upload.put", write=True)
	@ol('items')
	def putupload(self, items, extract=False, ctx=None, txn=None):
		raise NotImplementedError
		tmpdir = '/Users/irees/'
		
		bdos = []
		rename = []
		for bdo in items:
			newfile = False
			if not bdo.get('name'):
				handler = bdo
				bdo = self.bdbs.upload.new(filename=handler.get('filename'), ctx=ctx, txn=txn)
				newfile = bdo.writetmp(filedata=handler.get('filedata', None), fileobj=handler.get('fileobj', None), basepath=tmpdir)

			bdo = self.bdbs.upload.cput(bdo, ctx=ctx, txn=txn)
			bdos.append(bdo)

			if newfile:
				dest = os.path.join(tmpdir, bdo.name)
				rename.append([newfile, dest])

		# Rename/copy temporary files to final destination.
		for newfile, filepath in rename:
			os.rename(newfile, filepath)

		return bdos
		

	##### Debugging #####

	@publicmethod("ping")
	def ping(self, *a, **kw):
		"""Utitlity method to ensure the server is up

		Examples:

		>>> db.ping()
		'pong'

		:return: Ping? 'pong'
		"""
		return 'pong'


	##### Workflow #####

	# Workflows are currently turned off, need to be fixed.

	# @publicmethod
	# def getworkflownames(self, name=None, ctx=None, txn=None):
	# 	"""This will return an (ordered) list of workflow objects
	# 	for the given context (user)."""
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
	# 	"""This appends a new workflow object to the user's list.
	# wfid will be assigned by this function and returned"""
	#	return self.bdbs.workflow.get(name).cputs(items, ctx=ctx, txn=txn)
	#
	#
	# @publicmethod
	# @ol('names')
	# def delworkflowitem(self, names, ctx=None, txn=None):
	# 	"""This will remove a single workflow object based on wfid"""
	#	return self.bdbs.workflow.get(name).delete(names, ctx=ctx, txn=txn)




__version__ = "$Revision$".split(":")[1][:-1].strip()
