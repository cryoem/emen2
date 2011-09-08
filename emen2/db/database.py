# $Id$

import threading
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
import shutil
import glob
import email
import email.mime.text

# Berkeley DB; the 'bsddb' module is not sufficient.
import bsddb3

# Markdown (HTML) Processing
# At some point, I may provide "extremely simple" markdown processor fallback
try:
	import markdown
except ImportError:
	markdown = None

# EMEN2 Config
import emen2.db.config
g = emen2.db.config.g()

# EMEN2 Core
import emen2.db.datatypes
import emen2.db.vartypes
import emen2.db.properties
import emen2.db.macros
import emen2.db.proxy
import emen2.db.load

# DBObjects
import emen2.db.dataobject
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
import jsonrpc.jsonutil

# Exceptions
from emen2.db.exceptions import *

# Conveniences
publicmethod = emen2.db.proxy.publicmethod

# Version names
# from emen2.clients import __version__
VERSIONS = {
	"API": emen2.VERSION
}

# Regular expression to parse Protocol views.
VIEW_REGEX = '(\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?)|((?P<text>[^\$]+))'
VIEW_REGEX = re.compile(VIEW_REGEX)

# Global pointer to database environment
DBENV = None

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

# inst for instantiate
inst = lambda x:x()
is_str = lambda x: hasattr(x, 'upper')
@inst
class CVars(object):
	MAILADMIN = g.claim('MAILADMIN', default="", validator=is_str)
	MAILHOST = g.claim('MAILHOST', default="", validator=is_str)
	TIMESTR = g.claim('TIMESTR', default="%Y/%m/%d %H:%M:%S", validator=is_str)
	EMEN2DBNAME = g.claim('EMEN2DBNAME', default="EMEN2", validator=is_str)
	EMEN2EXTURI = g.claim('EMEN2EXTURI', "", validator=is_str)


def fakemodules():
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



# Utility methods

def clock(times, key=0, t=0, limit=60):
	"""A timing method for controlling timeouts to prevent hanging.
	On operations that might take a long time, call this at each step

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



def check_output(args, **kwds):
	"""Run a command using Popen and return the stdout.

	:return: stdout from the program after exit (str)
	"""
	kwds.setdefault("stdout", subprocess.PIPE)
	kwds.setdefault("stderr", subprocess.STDOUT)
	p = subprocess.Popen(args, **kwds)
	return p.communicate()[0]


# @atexit.register
def DB_Close(*args, **kwargs):
	"""Close all open DBs"""
	for i in EMEN2DBEnv.opendbs.keys():
		i.close()



# ian: todo: make these express GMT, then localize using a user preference
def getctime():
	""":return: Current database time, as float in seconds since the epoch"""
	return time.time()



def gettime():
	""":return: Current database time, as string in format %s"""%CVars.TIMESTR
	return time.strftime(CVars.TIMESTR)



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
		g.warn(msg)
	else:
		raise e(msg)



###############################
# Email
###############################

def sendmail(recipient, msg='', subject='', template=None, ctxt=None, ctx=None, txn=None):
	"""(Semi-internal) Send an email. You can provide either a template or a message subject and body.

	:param recipient: Email recipient
	:keyword msg: Message text, or
	:keyword template: ... Template name
	:keyword ctxt: ... Dictionary to pass to template
	:return: Email recipient, or None if no message was sent
	"""
	# ctx and txn arguments don't do anything. I accept them because it's a force of habit to include them.

	if not CVars.MAILADMIN:
		g.warn("Couldn't get mail config: No admin email available, config.MAILADMIN or root.email.")
		return
	if not CVars.MAILHOST:
		g.warn("Couldn't get mail config: No SMTP Server")
		return

	ctxt = ctxt or {}
	ctxt["recipient"] = recipient
	ctxt["MAILADMIN"] = CVars.MAILADMIN
	ctxt["EMEN2DBNAME"] = CVars.EMEN2DBNAME
	ctxt["EMEN2EXTURI"] = CVars.EMEN2EXTURI

	if not recipient:
		return

	if msg:
		msg = email.mime.text.MIMEText(msg)
		msg['Subject'] = subject
		msg['From'] = CVars.MAILADMIN
		msg['To'] = recipient
		msg = msg.as_string()

	elif template:
		try:
			msg = g.templates.render_template(template, ctxt)
		except Exception, e:
			g.warn('Could not render template %s: %s'%(template, e))
			return
	else:
		raise ValueError, "No message to send!"

	# Actually send the message
	s = smtplib.SMTP(CVars.MAILHOST)
	s.set_debuglevel(1)
	s.sendmail(CVars.MAILADMIN, [CVars.MAILADMIN, recipient], msg)
	g.info('Mail sent: %s -> %s'%(CVars.MAILADMIN, recipient))
	# g.error('Could not send email: %s'%e, e=e)
	# raise e

	return recipient





# ian: todo: have DBEnv and all BDBs in here --
#	DB should just be methods for dealing with this dbenv "core"
class EMEN2DBEnv(object):
	opendbs = weakref.WeakKeyDictionary()
	cachesize = g.claim('CACHESIZE')

	path = g.claim('EMEN2DBHOME')
	snapshot = g.claim('SNAPSHOT', True)
	def __init__(self, path=None, maintenance=False, snapshot=False):
		"""EMEN2 Database Environment.
		The DB files are accessible as attributes, and indexes are loaded in self.index.

		:keyword path: Directory containing EMEN2 Database Environment.
		:keyword snapshot: Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
		"""
		self.keytypes =  {}

		if path is not None:
			self.path = path

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
		# Cache the vartypes that are indexable
		vtm = emen2.db.datatypes.VartypeManager()
		self.indexablevartypes = set()
		for y in vtm.getvartypes():
			y = vtm.getvartype(y)
			if y.keytype:
				self.indexablevartypes.add(y.getvartype())

		#########################
		# Open DB environment; check if global DBEnv has been opened yet
		ENVOPENFLAGS = \
			bsddb3.db.DB_CREATE | \
			bsddb3.db.DB_INIT_MPOOL | \
			bsddb3.db.DB_INIT_TXN | \
			bsddb3.db.DB_INIT_LOCK | \
			bsddb3.db.DB_INIT_LOG | \
			bsddb3.db.DB_THREAD  | \
			bsddb3.db.DB_REGISTER |	\
			bsddb3.db.DB_RECOVER

		global DBENV

		if DBENV == None:
			g.info("Opening Database Environment: %s"%self.path)
			DBENV = bsddb3.db.DBEnv()

			if snapshot or self.snapshot:
				DBENV.set_flags(bsddb3.db.DB_MULTIVERSION, 1)

			cachesize = self.cachesize * 1024 * 1024l
			txncount = (cachesize / 4096) * 2
			if txncount > 1024*128:
				txncount = 1024*128

			DBENV.set_cachesize(0, cachesize)
			DBENV.set_tx_max(txncount)
			DBENV.set_lk_max_locks(300000)
			DBENV.set_lk_max_lockers(300000)
			DBENV.set_lk_max_objects(300000)

			DBENV.open(self.path, ENVOPENFLAGS)
			self.opendbs[self] = 1

		self.dbenv = DBENV

		#########################
		# Open Databases
		if not maintenance:
			self.init()


	def getdbenv(self):
		return self.dbenv


	def __getitem__(self, key, default):
		return self.keytypes.get(key, default)


	def init(self):
		"""Open the databases"""

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

		# access by keytype..
		self.keytypes = {
			'record': self.record,
			'paramdef': self.paramdef,
			'recorddef': self.recorddef,
			'user': self.user,
			'group': self.group,
		}


	# ian: todo: make this nicer.
	def close(self):
		"""Close the Database Environment"""
		for k,v in self.keytypes.items():
			print "Closing", v
			v.close()
		print "Closing dbenv"
		self.dbenv.close()
		print "Done closing dbenv"


	####################################
	# Load Extensions
	####################################



	####################################
	# Utility methods
	####################################

	LOGPATH = g.watch('paths.LOGPATH')
	LOG_ARCHIVE = g.claim('paths.LOG_ARCHIVE')
	TILEPATH = g.claim('paths.TILEPATH')
	TMPPATH = g.claim('paths.TMPPATH')
	SSLPATH = g.watch('paths.SSLPATH')

	def checkdirs(self):
		"""Check that all necessary directories referenced from config file exist."""

		if not os.access(self.path, os.F_OK):
			os.makedirs(self.path)

		# ian: todo: create the necessary subdirectories when creating a database
		paths = [
			"data",
			"log",
			"overlay",
			"overlay/views",
			"overlay/templates"
			]

		for i in ['record', 'paramdef', 'recorddef', 'user', 'newuser', 'group', 'workflow', 'context', 'binary']:
			for j in ['', '/index']:
				paths.append('data/%s%s'%(i,j))

		paths = (os.path.join(self.path, path) for path in paths)
		for path in paths:
			if not os.path.exists(path):
				os.makedirs(path)
		#paths = [os.makedirs(path) for path in paths if not os.path.exists(path)]

		paths = []
		for path in [self.LOGPATH, self.LOG_ARCHIVE, self.TILEPATH, self.TMPPATH, self.SSLPATH]:
			try:
				paths.append(path)
			except AttributeError:
				pass
		paths = [os.makedirs(path) for path in paths if not os.path.exists(path)]

		configpath = os.path.join(self.path,"DB_CONFIG")
		if not os.path.exists(configpath):
			g.info("Installing default DB_CONFIG file: %s"%configpath)
			f = open(configpath, "w")
			f.write(DB_CONFIG)
			f.close()


	def stat():
		"""List some statistics about the Database Environment."""

		sys.stdout.flush()

		tx_max = self.dbenv.get_tx_max()
		g.info("Open transactions: %s"%tx_max)

		txn_stat = self.dbenv.txn_stat()
		g.info("Transaction stats: ")
		for k,v in txn_stat.items():
			g.info("\t%s: %s"%(k,v))

		log_archive = self.dbenv.log_archive()
		g.info("Archive: %s"%log_archive)

		lock_stat = self.dbenv.lock_stat()
		g.info("Lock stats: ")
		for k,v in lock_stat.items():
			g.info("\t%s: %s"%(k,v))


	####################################
	# Transaction management
	####################################

	txncounter = 0

	def newtxn(self, parent=None, write=False):
		"""Start a new transaction.

		:keyword parent: Open new txn as a child of this parent txn
		:keyword write: Transaction will be likely to write data; turns off Berkeley DB Snapshot
		:return: New transaction
		"""

		flags = bsddb3.db.DB_TXN_SNAPSHOT
		if write:
			flags = 0

		txn = self.dbenv.txn_begin(parent=parent, flags=flags) #
		# g.log.msg('TXN', "NEW TXN, flags: %s --> %s"%(flags, txn))

		#try:
		type(self).txncounter += 1
		self.txnlog[id(txn)] = txn
		#except KeyError:
		#	self.txnabort(txn=txn)
		#	raise

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
		# g.log.msg('TXN', "TXN ABORT --> %s"%txn)

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
		# g.log.msg('TXN', "TXN COMMIT --> %s"%txn)

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
		"""Checkpoint the Database Environment"""
		return self.dbenv.txn_checkpoint()



	###########################
	# Backup / restore
	###########################

	def log_archive(self, remove=True, checkpoint=False, txn=None):
		"""Archive completed log files.

		:keyword remove: Remove the log files after moving them to the backup location
		:keyword checkpoint: Run a checkpoint first; this will allow more files to be archived
		"""

		outpath = self.LOG_ARCHIVE

		if checkpoint:
			g.info("Log Archive: Checkpoint")
			self.dbenv.txn_checkpoint()

		archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

		g.info("Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

		if not os.access(outpath, os.F_OK):
			os.makedirs(outpath)

		self._log_archive(archivefiles, outpath, remove=remove)


	def _log_archive(self, archivefiles, outpath, remove=False):
		"""(Internal) Backup database log files"""

		outpaths = []
		for archivefile in archivefiles:
			dest = os.path.join(outpath, os.path.basename(archivefile))
			g.info('Log Archive: %s -> %s'%(archivefile, dest))
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
			g.info('Log Archive: Removing %s'%(removefile))
			os.unlink(removefile)

		return removefiles



class DB(object):
	sync_contexts = threading.Event()

	def __init__(self, path=None):
		"""Initialize DB.
		Default path is g.EMEN2DBHOME, which checks $EMEN2DBHOME and program arguments.

		:keyword path: Directory containing EMEN2 Database Environment.
		"""
		# Open the database
		self.bdbs = EMEN2DBEnv(path=path)

		
		# Load built-in paramdefs/recorddefs
		self.load_json(os.path.join(emen2.db.config.get_filename('emen2', 'db'), 'base.json'))		
		for ext, path in g.EXTS.items():
			self.load_extension(ext, path)

		#if not hasattr(self.periodic_operations, 'next'):
		#	self.__class__.periodic_operations = self.periodic_operations()

		# Periodic operations..
		self.lastctxclean = time.time()
		# Cache contexts
		self.contexts_cache = {}


	def load_json(self, infile):
		ctx = emen2.db.context.SpecialRootContext(db=self)

		# print "Loading... %s"%infile
		loader = emen2.db.load.BaseLoader(infile=infile)

		for item in loader.loadfile(keytype='paramdef'):
			pd = self.bdbs.paramdef.dataclass(ctx=ctx, **item)
			self.bdbs.paramdef.addcache(pd)

		for item in loader.loadfile(keytype='recorddef'):
			rd = self.bdbs.recorddef.dataclass(ctx=ctx, **item)
			self.bdbs.recorddef.addcache(rd)


	def load_extension(self, ext, path):
		for j in glob.glob(os.path.join(path, 'json', '*.json')):
			self.load_json(infile=j)


	def __str__(self):
		return "<DB: %s>"%(hex(id(self)))


	# def __del__(self):
	# 	"""Close DB when deleted"""
	# 	self.bdbs.close()

	###############################
	# Utility methods
	###############################

	def _sudo(self, username=None, ctx=None, txn=None):
		print "Temporarily granting user %s administrative privileges"
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
			elif vartype.iterable:
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


	def _mapcommit(self, keytype, names, method, ctx=None, txn=None, *args, **kwargs):
		"""(Internal) Get keytype items, run a method with *args **kwargs, and commit.

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


	def _mapcommit_ol(self, keytype, names, method, default, ctx=None, txn=None, *args, **kwargs):
		if names is None:
			names = default
		ol, names = listops.oltolist(names)
		ret = self._mapcommit(keytype, names, method, ctx, txn, *args, **kwargs)
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



	###############################
	# Events
	###############################

	# ian: todo: hard: flesh this out into a proper cron system,
	# with a registration model; right now just runs cleanupcontext
	# Currently, this is called during _getcontext, and calls
	# cleanupcontexts not more than once every 10 minutes

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
						g.error('Exception in periodic_operations:', e)
						traceback.print_exc(file=g.log)
					else:
						txn.commit()
					finally:
						self.lastctxclean = t
			if first_run: first_run = False
			yield


	# ian: todo: hard: finish
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
	# 			g.info("Expire context (%s) %d" % (ctxid, time.time() - context.time))
	# 			self.bdbs.context.delete(ctxid, txn=txn)



	###############################
	# Time and Version Management
	###############################

	@publicmethod("version")
	def checkversion(self, program="API", ctx=None, txn=None):
		"""Returns current version of API or specified program.

		:keyword program: Check version for this program (API, emen2client, etc.)
		:return: Version string
		"""
		return VERSIONS.get(program)


	@publicmethod("time")
	def gettime(self, ctx=None, txn=None):
		"""Get current time.

		:return: Current time string, YYYY/MM/DD HH:MM:SS
		"""

		return gettime()



	###############################
	# Login and Context Management
	###############################

	@publicmethod("auth.login", write=True)
	def login(self, name="anonymous", password="", host=None, ctx=None, txn=None):
		"""Login. Returns auth token (ctxid), or fails with AuthenticationError, SessionError, or KeyError.

		:keyword name: Account name
		:keyword password: Account password
		:keyword host: Bind auth token to this host (usually set by the proxy)
		:return: Auth token (ctxid)
		:exception: AuthenticationError, SessionError, KeyError
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
			except (KeyError, emen2.db.exceptions.SecurityError):
				raise AuthenticationError, AuthenticationError.__doc__

			# Create the Context for this user/host
			newcontext = emen2.db.context.Context(username=user.name, host=host)

		self.bdbs.context.put(newcontext.name, newcontext, txn=txn)
		g.log.msg('SECURITY', "Login succeeded: %s -> %s" % (name, newcontext.name))

		return newcontext.name


	@publicmethod("auth.login_compat", write=True)
	def _login(self, *args, **kwargs):
		return self.login(*args, **kwargs)


	# Logout is the same as delete context
	### this doesn't work until DB restart (the context isn't immediately cleared)
	@publicmethod("auth.logout", write=True)
	def logout(self, ctx=None, txn=None):
		"""Logout."""
		self.contexts_cache.pop(ctx.name, None)
		self.bdbs.context.delete(ctx.name, txn=txn)
		self.sync_contexts.set()


	@publicmethod("auth.check.context")
	def checkcontext(self, ctx=None, txn=None):
		"""Return basic information about the current Context.

		:return: (Context User name, set of Context groups)
		"""
		return ctx.username, ctx.groups


	@publicmethod("auth.check.admin")
	def checkadmin(self, ctx=None, txn=None):
		"""Checks if the user has global write access.

		:return: True if user is an admin
		"""
		return ctx.checkadmin()


	@publicmethod("auth.check.readadmin")
	def checkreadadmin(self, ctx=None, txn=None):
		"""Checks if the user has global read access.

		:return: True if user is a read admin
		"""
		return ctx.checkreadadmin()


	@publicmethod("auth.check.create")
	def checkcreate(self, ctx=None, txn=None):
		"""Check for permission to create records.

		:return: True if the user can create records
		"""
		return ctx.checkcreate()


	def _getcontext(self, ctxid, host, ctx=None, txn=None):
		"""(Internal and DBProxy) Takes a ctxid key and returns a Context.
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
			g.error("Session expired for %s"%ctxid)
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
			reverse=None,
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

		# Pre-process the query constraints..
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
			if stats: # don't do this unless we need the records grouped.
				r = self.bdbs.record.groupbyrectype(names, ctx=ctx, txn=txn)
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
			if reverse == None:
				reverse = True

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
					rd = self.bdbs.recorddef.cget("root", filt=False, ctx=ctx, txn=txn)
				except (KeyError, emen2.db.exceptions.SecurityError):
					viewdef = defaultviewdef
				else:
					viewdef = rd.views.get('tabularview', defaultviewdef)


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
			table = self.renderview(names, viewdef=viewdef, table=True, edit='auto', ctx=ctx, txn=txn)


		############################
		# Step 7: Fix for output
		t = clock(times, 6, t)

		stats = {}
		stats['time'] = time.time()-t0
		stats['rectypes'] = rectypes
		# stats['times'] = times
		# for k,v in times.items():
		# 	print k, '%5.3f'%(v)

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

		:param searchparam: Param
		:param comp: Comparison method
		:param value: Comparison value
		:keyword names: Record names (used in some query operations)
		:keyword recs: Record cache dict, by name
		:return: Record names returned by query operation, or None
		"""

		if recs == None:
			recs = {}

		cfunc = self._query_cmps(comp)

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
			param_stripped = searchparam.replace('*','').replace('$$','')
			if searchparam.endswith('*'):
				indparams |= self.bdbs.paramdef.rel([param_stripped], recurse=-1, ctx=ctx, txn=txn)[param_stripped]
			indparams.add(param_stripped)

		# First, search the index index
		indk = self.bdbs.record.getindex('indexkeys', txn=txn)

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
			# ian: todo: When validating for a user, needs
			# to return value if not validated?
			try:
				cargs = vtm.validate(pd, value)
			except ValueError:
				if pd.vartype == 'user':
					cargs = value
				else:
					continue
			except:
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
			ind = self.bdbs.record.getindex(pp, txn=txn)
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

		:param sortkey:
		:param names:
		:keyword recs: Record cache, keyed by name
		:keyword rendered: Compare using 'rendered' value
		:param c: Query constraints; used for checking items in cache
		:return: Sortkey keytype ('s'/'d'/'f'/None), and {name:value} of values that can be sorted
		"""
		# No work necessary if sortkey is creationtime
		if sortkey in ['creationtime', 'name', 'recid']:
			return 's', {}

		# Setup
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		inverted = collections.defaultdict(set)
		c = c or []

		# Check the paramdef
		pd = self.bdbs.paramdef.cget(sortkey, ctx=ctx, txn=txn)
		sortvalues = {}
		vartype = None
		keytype = None
		iterable = False
		ind = False
		if pd:
			vartype = pd.vartype
			vt = vtm.getvartype(vartype)
			keytype = vt.keytype
			iterable = vt.iterable
			ind = self.bdbs.record.getindex(pd.name, txn=txn)

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
			# Iterable params are indexed, but the order is not preserved,
			# 	so we must check directly.
			# No index can be very slow! Chunk the record gets to help.
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
			raise ValueError, "Don't know how to sort by %s"%sortkey


		# Use a "rendered" representation of the value,
		#	e.g. user names to sort by user's current last name
		# These will always sort using the rendered value
		if vartype in ["user", "binary"]:
			rendered = True

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


	def _query_cmps(self, comp, ignorecase=1):
		"""(Internal) Return the list of query constraint operators.

		:keyword ignorecase: Use case-insensitive comparison methods
		:return: Dict of query methods
		"""
		# y is search argument, x is the record's value
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

		# Synonyms
		synonyms = {
			"is": "==",
			"not": "!=",
			"gte": ">=",
			"lte": "<=",
			"gt": ">",
			"lt": "<"
		}

		if ignorecase:
			cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			cmps['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

		comp = synonyms.get(comp, comp)
		return cmps[comp]



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

		:param query: Contained in any item below
		:keyword name: ... contains in name
		:keyword desc_short: ... contains in short description
		:keyword desc_long: ... contains in long description
		:keyword mainview: ... contains in mainview
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
		:keyword boolmode: AND / OR for each search constraint
		:return: RecordDefs
		"""
		return self._find_pdrd(self._findrecorddefnames, keytype='recorddef', *args, **kwargs)


	@publicmethod("paramdef.find")
	def findparamdef(self, *args, **kwargs):
		"""Find a ?RecordDef?, by general search string, or by name/desc_short/desc_long/mainview.

		:param query: Contained in any item below
		:keyword name: ... contains in name
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
			ret = set()
			vartype = listops.check_iterable(vartype)
			for item in items:
				if item.vartype in vartype:
					ret.add(item.name)
			return ret


	@limit_result_length
	def _find_pdrd(self, cb, query=None, childof=None, boolmode="AND", keytype="paramdef", record=None, vartype=None, ctx=None, txn=None, **qp):
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


		allret = self._boolmode_collapse(rets, boolmode)
		ret = map(ditems.get, allret)

		return ret


	@publicmethod("user.find")
	@limit_result_length
	def finduser(self, query=None, record=None, boolmode="AND", limit=None, ctx=None, txn=None, **kwargs):
		"""Find a user, by general search string, or by name_first/name_middle/name_last/email/name.

		:keyword query: Contained in any item below
		:keyword email: ... contains in email
		:keyword name_first: ... contains in first name
		:keyword name_middle: ... contains in middle name
		:keyword name_last: ... contains in last name
		:keyword name: ... contains in user name
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
		:keyword boolmode: AND / OR for each search constraint
		:return: Users
		"""
		rets = []
		if query == '':
			allnames = self.bdbs.user.names(ctx=ctx, txn=txn)
			rets.append(allnames)

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
			recs = self.bdbs.record.cgets(qr['names'], ctx=ctx, txn=txn)
			un = filter(None, [i.get('username') for i in recs])
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
			ret = self._findbyvartype(listops.check_iterable(record), ['user', 'acl', 'comments', 'history'], ctx=ctx, txn=txn)
			rets.append(ret)

		allret = self._boolmode_collapse(rets, boolmode)
		return self.getuser(allret, ctx=ctx, txn=txn, filt=False)


	@publicmethod("group.find")
	def findgroup(self, query=None, record=None, limit=None, boolmode='AND', ctx=None, txn=None):
		"""Find a group.

		:keyword query: Find in Group's name or displayname
		:keyword record: Referenced in Record name(s)
		:keyword limit: Limit number of results
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

		allret = self._boolmode_collapse(rets, boolmode)
		ret = map(ditems.get, allret)

		if limit:
			return ret[:int(limit)]
		return ret


	# Warning: This can be SLOW!
	@publicmethod("binary.find")
	def findbinary(self, query=None, record=None, limit=None, boolmode='AND', ctx=None, txn=None, **kwargs):
		"""Find a binary by filename.

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

		:param str param: Parameter to search
		:param str query: Value to match
		:keyword bool count: Return count of matches, otherwise return names
		:keyword bool showchoices: Include any defined param 'choices'
		:keyword int limit: Limit number of results
		:return: [[matching value, count], ...] if count is True, otherwise
				[[matching value, [name, ...]], ...]
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
	# Grouping
	#########################

	@publicmethod("record.find.byrectype")
	@ol('names', output=False)
	def getindexbyrectype(self, names, ctx=None, txn=None):
		"""Get Record names by RecordDef.
		:param names: RecordDef name(s)
		:return: Set of Record names
		"""
		rds = self.bdbs.recorddef.cgets(names, ctx=ctx, txn=txn)
		ind = self.bdbs.record.getindex("rectype", txn=txn)
		ret = set()
		for i in rds:
			ret |= ind.get(i.name, txn=txn)
		return ret


	@publicmethod("record.group.byrectype")
	@ol('names')
	def groupbyrectype(self, names, ctx=None, txn=None):
		"""Group Records by RecordDef.
		:param names: Record name(s) or Record(s)
		:return: Dictionary of Record names by RecordDef
		"""
		return self.bdbs.record.groupbyrectype(names, ctx=ctx, txn=txn)



	#############################
	# Record Rendering
	#############################

	#@remove?
	@publicmethod("record.render.child.tree")
	def renderchildtree(self, name, recurse=3, rectype=None, ctx=None, txn=None):
		"""Convenience method used by some clients to render a bunch of
		records and simple relationships.

		:param name: Record name
		:keyword recurse: Recurse level
		:keyword rectype: Restrict to these rectypes ('*' notation allowed)
		:return: (Dictionary of rendered views {Record.name:view}, Child tree dictionary)
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


	def _make_tables(self, recdefs, rec, builtinparams, builtinparamsshow, markup, ctx, txn):
		# move built in params to end of table
		#par = [p for p in set(recdefs.get(rec.rectype).paramsK) if p not in builtinparams]
		par = [p for p in recdefs.get(rec.rectype).paramsK if p not in builtinparams]
		par += builtinparamsshow
		par += [p for p in rec.getparamkeys() if p not in par]
		return self._dicttable_view(par, markup=markup, ctx=ctx, txn=txn)


	@publicmethod("record.render")
	@ol('names')
	def renderview(self, names, viewdef=None, viewtype='recname', edit=False, markup=True, table=False, mode=None, vtm=None, ctx=None, txn=None):
		"""Render views.
		Note: if 'names' is not iterable, will return a string instead of dictionary

		:param names: Record name(s)
		:keyword viewdef: View definition
		:keyword viewtype: Use this view from the Record's RecordDdef (default='recname')
		:keyword edit: Render with editing HTML markup; use 'auto' for autodetect. (default=False)
		:keyword markup: Render with HTML markup (default=True)
		:keyword table: Return table format (this may go into a separate method) (default=False)
		:keyword mode: Deprecated, no effect.
		:return: Dictionary of {Record.name: rendered view}
		"""
		if viewtype == "tabularview":
			table = True

		if viewtype == 'recname' and not viewdef:
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
		# 
		names, recs, newrecs, other = listops.typepartition(names, int, emen2.db.dataobject.BaseDBObject, dict)
		recs.extend(self.bdbs.record.cgets(names, ctx=ctx, txn=txn))
		
		for newrec in newrecs:
			rec = self.bdbs.record.new(name=None, rectype=newrec.get('rectype'), ctx=ctx, txn=txn)#.update(newrec)
			rec.update(newrec)
			recs.append(rec)

		# Default params
		builtinparams = set() | emen2.db.record.Record.param_all
		builtinparamsshow = builtinparams - set(['permissions', 'comments', 'history', 'groups', 'parents', 'children'])

		# Get and pre-process views
		groupviews = {}
		recdefs = listops.dictbykey(self.bdbs.recorddef.cgets(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

		if viewdef:
			if markup and markdown:
				viewdef = markdown.markdown(viewdef)
			groupviews[None] = viewdef
		elif viewtype == "dicttable":
			for rec in recs:
				groupviews[rec.name] = self._make_tables(recdefs, rec, builtinparams, builtinparamsshow, markup, ctx=ctx, txn=txn)
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

		:param params: Use these ParamDef names
		:keyword paramdefs: ParamDef cache
		:keyword markup: Use HTML Markup (default=False)
		:return: HTML table of params
		"""
		if markup:
			dt = ['''<table cellspacing="0" cellpadding="0">
					<thead><th>Parameter</th><th>Value</th></thead>
					<tbody>''']
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
	#* 	BDB/BTree methods.
	#************************************************************************
	#########################################################################


	@publicmethod("get", write=True, admin=True)
	def get(self, names, keytype='record', ctx=None, txn=None):
		'''Get an object

			:param names: the IDs for which the children are to be retrieved
			:param keytype: What kind of objects the IDs refer to
		'''

		return self.bdbs.keytypes[keytype].cgets(names, ctx=ctx, txn=txn)


	@publicmethod("put", write=True, admin=True)
	def put(self, items, keytype='record', clone=False, ctx=None, txn=None):
		'''Get the children of the object as a tree

			:param names: the IDs for which the children are to be retrieved
			:param keytype: What kind of objects the IDs refer to
			:param clone: ???
		'''

		return self.bdbs.keytypes[keytype].cputs(items, clone=clone, ctx=ctx, txn=txn)

	@publicmethod("new", write=True, admin=True)
	def new(self, *args, **kwargs):
		keytype = kwargs.pop('keytype', 'record')
		return dict(
			user = self.newuser,
			group = self.newgroup,
			paramdef = self.newparamdef,
			record = self.newrecord,
			recorddef = self.newrecorddef,
			binary = self.newbinary,
		)[keytype](*args, **kwargs)



	###############################
	# Relationships
	###############################

	# This is a new method -- might need some testing.
	@publicmethod("rel.sibling")
	def getsiblings(self, name, rectype=None, keytype="record", ctx=None, txn=None, **kwargs):
		'''Get the siblings of the object as a tree

			:param names: the IDs for which the children are to be retrieved
			:param recurse: how many levels of children to retrieve
			:param rectype: filter by rectype (Not Implemented?)
			:param keytype: What kind of objects the IDs refer to
		'''

		return self.bdbs.keytypes[keytype].siblings(name, rectype=rectype, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.parent.tree")
	@ol('names', output=False)
	def getparenttree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		'''Get the parents of the object as a tree

			:param names: the IDs for which the children are to be retrieved
			:param recurse: how many levels of children to retrieve
			:param rectype: filter by rectype (Not Implemented?)
			:param keytype: What kind of objects the IDs refer to
		'''
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', tree=True, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.child.tree")
	@ol('names', output=False)
	def getchildtree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		'''Get the children of the object as a tree

			:param names: the IDs for which the children are to be retrieved
			:param recurse: how many levels of children to retrieve
			:param rectype: filter by rectype (Not Implemented?)
			:param keytype: What kind of objects the IDs refer to
		'''
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', tree=True, ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.parent")
	@ol('names')
	def getparents(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		'''Get the parents of an object

			:param names: the IDs for which the children are to be retrieved
			:param recurse: how many levels of children to retrieve
			:param rectype: filter by rectype (Not Implemented?)
			:param keytype: What kind of objects the IDs refer to

			'''
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.child")
	@ol('names')
	def getchildren(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None, **kwargs):
		'''Get the children of an object

		:param names: the IDs for which the children are to be retrieved
		:param recurse: how many levels of children to retrieve
		:param rectype: filter by rectype (Not Implemented?)
		:param keytype: What kind of objects the IDs refer to

		'''
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', ctx=ctx, txn=txn, **kwargs)


	@publicmethod("rel.rel")
	@ol('names')
	def rel(self, names, keytype="record", recurse=1, rel="children", tree=False, ctx=None, txn=None, **kwargs):
		"""Get relationships. See the RelateDB.rel()"""
		return self.bdbs.keytypes[keytype].rel(names, recurse=recurse, rectype=rectype, rel=rel, tree=tree, ctx=ctx, txn=txn, **kwargs)


	@publicmethod('rel.pclink', write=True)
	def pclink(self, parent, child, keytype='record', ctx=None, txn=None):
		'''Link a parent object with a child

		:param parent: the ID of the parent object
		:param child: the ID of the child object
		:param keytype: the kind of object being linked

		Keytype can be one of:

			- record
			- recorddef
			- paramdef
		'''

		return self.bdbs.keytypes[keytype].pclink(parent, child, ctx=ctx, txn=txn)


	@publicmethod('rel.pcunlink', write=True)
	def pcunlink(self, parent, child, keytype='record', ctx=None, txn=None):
		'''Remove a parent-child link

		:param parent: the ID of the parent record
		:param child: the ID of the child record
		:param keytype: the kind of object being linked

		Keytype can be one of:

			- record
			- recorddef
			- paramdef
		'''
		return self.bdbs.keytypes[keytype].pcunlink(parent, child, ctx=ctx, txn=txn)


	#@publicmethod('rel.relink', write=True)
	# not implemented
	def relink(self, parent, child, keytype='record', ctx=None, txn=None):
		return self.bdbs.keytypes[keytype].relink(parent, child, ctx=ctx, txn=txn)



	###############################
	# User Management
	###############################

	@publicmethod("user.get")
	@ol('names')
	def getuser(self, names, filt=True, ctx=None, txn=None):
		"""Get user information.
		Information may be limited to name and id if the user
		requested additional privacy.

		:param names: User name(s), Record(s), or Record name(s)
		:keyword filt: Ignore failures
		:return: User(s)
		"""
		return self.bdbs.user.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("user.names")
	def getusernames(self, names=None, ctx=None, txn=None):
		""":return: Set of all User names."""
		return self.bdbs.user.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("user.put", write=True)
	@ol('items')
	def putuser(self, items, ctx=None, txn=None):
		"""Allow a User to change some of their account settings.

		:param items: User(s)
		:return: Updated User(s)
		"""
		return self.bdbs.user.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("user.disable", write=True, admin=True)
	def disableuser(self, names, ctx=None, txn=None):
		"""(Admin Only) Disable a User.

		:param names: User name(s)
		:keyword filt: Ignore failures
		:return: List of names disabled
		"""
		return self._mapcommit('user', names, 'disable', ctx=ctx, txn=txn)


	@publicmethod("user.enable", write=True, admin=True)
	def enableuser(self, names, ctx=None, txn=None):
		"""(Admin Only) Re-enable a User.

		:param names: User name(s)
		:keyword filt: Ignore failures
		"""
		return self._mapcommit('user', names, 'enable', ctx=ctx, txn=txn)


	@publicmethod("user.setprivacy", write=True)
	def setprivacy(self, state, names=None, ctx=None, txn=None):
		"""Set privacy level.

		:param state: 0, 1, or 2, in increasing level of privacy.
		:keyword names: User names to modify (admin only)
		"""
		# This is a modification of _mapcommit to allow if names=None
		# ctx.username will be used as the default.
		return self._mapcommit_ol('user', names, 'setprivacy', ctx.username, ctx, txn, state)



	##########
	# User Email / Password
	# These methods sometimes use put instead of cput because they need to modify
	# the user's secret auth token.
	#########

	@publicmethod("user.setemail", write=True)
	def setemail(self, email, secret=None, password=None, name=None, ctx=None, txn=None):
		"""Change a User's email address.
		This will require you to verify that you own the account by
		responding with an auth token sent to that address.

		Note: This method only takes a single User name.

		Note: An Admin will always succeed in changing email, with or without password/token.

		:param str email: New email address
		:param str secret: Auth token, or...
		:param str password: Current User password
		:param str name: User name (default is current Context user)

		:exception: :py:class:`SecurityError <emen2.db.exceptions.SecurityError>` if the password and/or auth token are wrong
		"""
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
		# 4. Email address is updated, and reindexed

		user = self.bdbs.user.cget(name, filt=False, ctx=ctx, txn=txn)
		oldemail = user.email
		email = user.setemail(email, password=password, secret=secret)

		#@postprocess
		# Check that no other user is currently using this email.
		ind = self.bdbs.user.getindex('email', txn=txn)
		if ind.get(email, txn=txn) - set([user.name]):
			time.sleep(2)
			raise SecurityError, "The email address %s is already in use"%(email)

		if user.email == oldemail:
			# The email didn't change, but the secret did
			# Note: cputs will always ignore the secret; write directly
			self.bdbs.user.put(user.name, user, txn=txn)

			# Send the verify email containing the auth token
			ctxt['secret'] = user._secret[2]
			sendmail(email, template='/email/email.verify', ctxt=ctxt, ctx=ctx, txn=txn)

		else:
			# Email changed.
			g.log.msg("SECURITY","Changing email for %s"%user.name)
			self.bdbs.user.cputs([user], txn=txn)

			# Send the user an email to acknowledge the change
			sendmail(user.email, template='/email/email.verified', ctxt=ctxt)


	@publicmethod("auth.setpassword", write=True)
	def setpassword(self, oldpassword, newpassword, secret=None, name=None, ctx=None, txn=None):
		"""Change password.
		Note: This method only takes a single User name.

		:param oldpassword:
		:param newpassword:
		:keyword name: User name (default is current Context user)
		"""
		#@action
		# Try to authenticate using either the password OR the secret!
		# Note: The password will be hidden if ctx.username != user.name
		# user = self.bdbs.user.cget(name or ctx.username, filt=False, ctx=ctx, txn=txn)
		#ed: odded 'or ctx.username' to match docs
		user = self.bdbs.user.getbyemail(name or ctx.username, filt=False, txn=txn)
		user.setpassword(oldpassword, newpassword, secret=secret)

		# ian: todo: evaluate to use put/cput..
		g.log.msg("SECURITY", "Changing password for %s"%user.name)
		self.bdbs.user.put(user.name, user, txn=txn)

		#@postprocess
		sendmail(user.email, template='/email/password.changed')


	@publicmethod("auth.resetpassword", write=True)
	def resetpassword(self, name, ctx=None, txn=None):
		"""Reset User password.
		This is accomplished by sending a password reset token to the
		User's currently registered email address.
		Note: This method only takes a single User name.

		:keyword name: User name, or User Email
		:keyword secret:
		"""
		#@action
		user = self.bdbs.user.getbyemail(name, filt=False, txn=txn)
		user.resetpassword()

		# Use direct put to preserve the secret
		self.bdbs.user.put(user.name, user, txn=txn)

		#@postprocess
		# Absolutely never reveal the secret via any mechanism
		# but email to registered address
		ctxt = {'secret': user._secret[2]}
		sendmail(user.email, template='/email/password.reset', ctxt=ctxt)

		g.log.msg('SECURITY', "Setting resetpassword secret for %s"%user.name)



	###############################
	# New Users
	###############################

	@publicmethod("user.queue.names", admin=True)
	def getuserqueue(self, names=None, ctx=None, txn=None):
		""":return: Set of names of Users in the new user queue."""
		return self.bdbs.newuser.names(names=names, ctx=ctx, txn=txn)


	# Only allow admins!
	@publicmethod("user.queue.get", admin=True)
	@ol('names')
	def getqueueduser(self, names, ctx=None, txn=None):
		"""(Admin Only) Get users from the new user approval queue.

		:param names: New user queue name(s)
		:return: User(s) from new user queue
		"""
		return self.bdbs.newuser.cgets(names, ctx=ctx, txn=txn)


	@publicmethod("user.queue.new")
	def newuser(self, name, password, email, ctx=None, txn=None):
		"""Create a new User.

		:param name: Desired account name
		:param password: Password
		:param email: Email Address
		:return: New User
		:exception: KeyError if there is already a user
			or pending user with this name
		"""
		return self.bdbs.newuser.new(name=name, password=password, email=email, ctx=ctx, txn=txn)


	@publicmethod("user.queue.put", write=True)
	@ol('users')
	def adduser(self, users, ctx=None, txn=None):
		"""Add a new User.
		Note: This only adds the user to the new user queue. The
		account must be processed by an administrator before it
		becomes active.

		:param users: New User(s)
		:return: New User(s)
		"""
		users = self.bdbs.newuser.cputs(users, ctx=ctx, txn=txn)

		if g.USER_AUTOAPPROVE:
			# print "Autoapproving........"
			rootctx = self._sudo()
			rootctx.db._txn = txn
			self.approveuser([user.name for user in users], ctx=rootctx, txn=txn)

		else:
			# Send account request email
			for user in users:
				sendmail(user.email, template='/email/adduser.signup')

		return users


	group_defaults = g.claim('GROUP_DEFAULTS')

	@publicmethod("user.queue.approve", write=True, admin=True)
	@ol('names')
	def approveuser(self, names, secret=None, ctx=None, txn=None):
		"""(Admin Only) Approve account in user queue.

		:param names: New user approval queue name(s)
		:return: Approved User name(s)
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
			# Put the new user
			user = self.bdbs.user.cput(user, ctx=ctx, txn=txn)

			# Update default Groups
			if user.name != 'root':
				for group in self.group_defaults:
					gr = self.bdbs.group.cget(group, ctx=ctx, txn=txn)
					gr.adduser(user.name)
					self.bdbs.group.cput(gr, ctx=ctx, txn=txn)

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
			if g.USER_AUTOAPPROVE:
				template = '/email/adduser.autoapproved'
			sendmail(user.email, template=template, ctxt=ctxt)

		return set([user.name for user in cusers])


	@publicmethod("user.queue.reject", write=True, admin=True)
	@ol('names')
	def rejectuser(self, names, filt=False, ctx=None, txn=None):
		"""(Admin Only) Remove a user from the new user queue.

		:param names: New user name(s) to reject
		:keyword filt: Ignore failures
		:return: Rejected user name(s)
		"""
		#@action
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
			sendmail(email, template='/email/adduser.rejected', ctxt=ctxt)

		return set(emails.keys())



	##########################
	# Groups
	##########################

	@publicmethod("group.names")
	def getgroupnames(self, names=None, ctx=None, txn=None):
		""":return: Set of all Group names."""
		return self.bdbs.group.names(names=names, ctx=ctx, txn=txn)


	@publicmethod("group.get")
	@ol('names')
	def getgroup(self, names, filt=True, ctx=None, txn=None):
		"""Get a Group.

		:param names: Group name(s)
		:keyword filt: Ignore failures
		:return: Group(s)
		"""
		return self.bdbs.group.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("group.new")
	def newgroup(self, name, ctx=None, txn=None):
		"""Construct a new Group.

		:param name: Group name
		:return: New Group
		"""
		return self.bdbs.group.new(name=name, ctx=ctx, txn=txn)


	@publicmethod("group.put", write=True, admin=True)
	@ol('items')
	def putgroup(self, items, ctx=None, txn=None):
		"""Add or update Group(s).

		:param items: Group(s)
		:return: Updated Group(s)
		"""
		return self.bdbs.group.cputs(items, ctx=ctx, txn=txn)



	#########################
	# section: paramdefs
	#########################

	@publicmethod("paramdef.vartypes")
	def getvartypenames(self, ctx=None, txn=None):
		""":return: Set of all available vartypes."""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getvartypes())


	@publicmethod("paramdef.properties")
	def getpropertynames(self, ctx=None, txn=None):
		""":return: Set of all available properties."""
		vtm = emen2.db.datatypes.VartypeManager()
		return set(vtm.getproperties())


	@publicmethod("paramdef.units")
	def getpropertyunits(self, name, ctx=None, txn=None):
		"""Returns a list of recommended units for a particular property.
		Other units may be used if they can be converted to the property's
		default units.

		:param name: Property name
		:return: Set of recommended units for property.
		"""
		if not name:
			return set()
		vtm = emen2.db.datatypes.VartypeManager()
		prop = vtm.getproperty(name)
		return set(prop.units)


	@publicmethod("paramdef.new")
	def newparamdef(self, name, vartype, ctx=None, txn=None):
		"""Construct a new ParamDef.

		:param name: ParamDef name
		:param vartype: ParamDef vartype
		:keyword inherit:
		:return: New ParamDef
		"""
		return self.bdbs.paramdef.new(name=name, vartype=vartype, ctx=ctx, txn=txn)


	@publicmethod("paramdef.put", write=True)
	@ol('items')
	def putparamdef(self, items, ctx=None, txn=None):
		"""Add or update ParamDef(s).

		:param items: ParamDef(s)
		:return: Updated ParamDef(s)
		"""
		return self.bdbs.paramdef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("paramdef.get")
	@ol('names')
	def getparamdef(self, names, filt=True, ctx=None, txn=None):
		"""Get ParamDefs.

		:param names: ParamDef name(s) and/or Record name(s)
		:keyword filt: Ignore failures
		:return: ParamDef(s)
		"""
		return self.bdbs.paramdef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("paramdef.names")
	def getparamdefnames(self, names=None, ctx=None, txn=None):
		""":return: Set of all ParamDef names."""
		return self.bdbs.paramdef.names(names=names, ctx=ctx, txn=txn)



	#########################
	# section: recorddefs
	#########################

	@publicmethod("recorddef.new")
	def newrecorddef(self, name, mainview, ctx=None, txn=None):
		"""Construct a new RecordDef.

		:param name: RecordDef name
		:param mainview: RecordDef mainview
		:return: New RecordDef
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

		:param items: RecordDef(s)
		:return: Updated RecordDef(s)
		"""
		return self.bdbs.recorddef.cputs(items, ctx=ctx, txn=txn)


	@publicmethod("recorddef.get")
	@ol('names')
	def getrecorddef(self, names, filt=True, ctx=None, txn=None):
		"""Get RecordDef(s).

		:param names: RecordDef name(s), and/or Record ID(s)
		:keyword filt: Ignore failures
		:return: RecordDef(s)
		"""
		return self.bdbs.recorddef.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("recorddef.names")
	def getrecorddefnames(self, names=None, ctx=None, txn=None):
		""":return: All RecordDef names."""
		return self.bdbs.recorddef.names(names=names, ctx=ctx, txn=txn)



	#########################
	# section: records
	#########################

	@publicmethod("record.get")
	@ol('names')
	def getrecord(self, names, filt=True, ctx=None, txn=None):
		"""Get Record(s).

		:param names: Record name(s)
		:keyword filt: Ignore failures
		:return: Record(s)
		"""
		return self.bdbs.record.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("record.new")
	def newrecord(self, rectype, inherit=None, ctx=None, txn=None):
		"""Construct a new Record.

		:param rectype: RecordDef
		:keyword inherit: Inherit permissions from an existing Record
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
			except (KeyError, emen2.db.exceptions.SecurityError), inst:
				g.warn("Couldn't get inherited permissions from record %s: %s"%(inherit, inst))

			rec["parents"] |= inherit

		# Let's try this and see how it works out...
		rec['date_occurred'] = gettime()
		rec['performed_by'] = ctx.username

		return rec


	@publicmethod("record.delete", write=True)
	@ol('names')
	def deleterecord(self, names, ctx=None, txn=None):
		"""Unlink and hide a record; it is still accessible to owner.
		Records are never truly deleted, just hidden.

		:param name: Record name(s) to delete
		:return: Deleted Record(s)
		"""
		self.bdbs.record.delete(names, ctx=ctx, txn=txn)


	@publicmethod("record.addcomment", write=True)
	@ol('names')
	def addcomment(self, names, comment, ctx=None, txn=None):
		"""Add comment to a record.
		Requires comment permissions on that Record.

		:param name: Record name(s)
		:param comment: Comment text
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'addcomment', ctx, txn, comment)


	@publicmethod("record.find.comments")
	@ol('names', output=False)
	def getcomments(self, names, filt=True, ctx=None, txn=None):
		"""Get comments from Records.

		:param names: Record name(s)
		:return: A list of comments, with the Record ID as the first item@[[recid, username, time, comment], ...]
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

		:param names: Record name(s)
		:param update: Update Records with this dictionary
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'update', ctx, txn, update)


	@publicmethod("record.validate")
	@ol('items')
	def validaterecord(self, items, ctx=None, txn=None):
		"""Check that a record will validate before committing.

		:param items: Record(s)
		:return: Validated Record(s)
		"""
		return self.bdbs.record.validate(items, ctx=ctx, txn=txn)


	@publicmethod("record.put", write=True)
	@ol('items')
	def putrecord(self, items, ctx=None, txn=None):
		"""Add or update Record.

		:param items: Record(s)
		:return: Updated Record(s)
		"""
		return self.bdbs.record.cputs(items, ctx=ctx, txn=txn)



	###############################
	# Record Permissions
	###############################

	# These map to the normal Record methods
	@publicmethod("record.adduser", write=True)
	@ol('names')
	def addpermission(self, names, users, level=0, ctx=None, txn=None):
		"""Add users to a Record's permissions.

		:param names: Record name(s)
		:param users: User name(s) to add
		:keyword level: Permissions level; 0=read, 1=comment, 2=write, 3=owner
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'adduser', ctx, txn, users)


	@publicmethod("record.removeuser", write=True)
	@ol('names')
	def removepermission(self, names, users, ctx=None, txn=None):
		"""Remove users from a Record's permissions.

		:param names: Record name(s)
		:param users: User name(s) to remove
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'removeuser', ctx, txn, users)


	@publicmethod("record.addgroup", write=True)
	@ol('names')
	def addgroup(self, names, groups, ctx=None, txn=None):
		"""Add groups to a Record's permissions.

		:param names: Record name(s)
		:param groups: Group name(s) to add
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'addgroup', ctx, txn, groups)


	@publicmethod("record.removegroup", write=True)
	@ol('names')
	def removegroup(self, names, groups, ctx=None, txn=None):
		"""Remove groups from a Record's permissions.

		:param names: Record name(s)
		:param groups: Group name(s)
		:return: Updated Record(s)
		"""
		return self._mapcommit('record', names, 'removegroup', ctx, txn, groups)


	# This method is for compatibility with the web interface widget..
	@publicmethod("record.setpermissions_compat", write=True)
	@ol('names')
	def setpermissions(self, names, permissions, groups, recurse=None, overwrite_users=False, overwrite_groups=False, ctx=None, txn=None):
		"""Update a Record's permissions.

		:param names: Record name(s)
		:param permissions:
		:param groups:
		:keyword recurse:
		:keyword overwrite_users:
		:keyword overwrite_groups:
		"""
		allusers = set()
		for i in permissions:
			allusers |= set(i)

		groups = set(groups or [])
		recs = self.bdbs.record.cgets(names, ctx=ctx, txn=txn)
		crecs = []
		for rec in recs:
			current = rec.members()

			# Calculate changes
			addusers = allusers - current
			delusers = current - allusers
			addgroups = groups - rec.groups
			delgroups = rec.groups - groups
			added = []
			for old,new in zip(rec.permissions, permissions):
				added.append(set(new)-set(old))

			# Apply the changes
			rec.setpermissions(permissions)
			rec.setgroups(groups)
			crecs.append(rec)

			# Apply the changes to the children
			if recurse:
				children = self.bdbs.record.rel([rec.name], recurse=recurse, ctx=ctx, txn=txn).get(rec.name, set())
				childrecs = self.bdbs.record.cgets(children, ctx=ctx, txn=txn)
				for child in childrecs:
					if overwrite_users:
						child.setpermissions(permissions)
					else:
						child.removeuser(delusers)
						child.addumask(added)

					if overwrite_groups:
						child.setgroups(groups)
					else:
						child.removegroup(delgroups)
						child.addgroup(addgroups)

					crecs.append(child)

		return self.bdbs.record.cputs(crecs, ctx=ctx, txn=txn)




	###############################
	# Binaries
	###############################

	@publicmethod("binary.get")
	@ol('names')
	def getbinary(self, names=None, filt=True, ctx=None, txn=None):
		"""Get Binaries.

		:param names: Either a list of recids and/or binary names or either of the two
		:type names: string or list of strings
		:keyword bool filt: If True, ignore failures
		:exception: KeyError if Binary not found
		:exception: SecurityError if insufficient permissions
		:return: A binary if given is a single binary, otherwise a list of binaries
		"""
		# This call to findbinary is a deprecated feature
		# that remains for backwards compat
		bdos, recnames, other = listops.typepartition(names, str, int)
		if len(recnames) > 0:
			return self.findbinary(record=recnames, ctx=ctx, txn=txn)
		return self.bdbs.binary.cgets(names, filt=filt, ctx=ctx, txn=txn)


	@publicmethod("binary.new")
	def newbinary(self, ctx=None, txn=None):
		"""Construct a new Binary.
		This doesn't do anything until committed with a file data source.

		:return: New Binary
		"""
		return self.bdbs.binary.new(name=None, ctx=ctx, txn=txn)


	@publicmethod("binary.put", write=True)
	def putbinary(self, item, infile=None, filename=None, record=None, param='file_binary', ctx=None, txn=None):
		"""Add or update a Binary (file attachment).
		Note: This currently only takes a single item.

		:param item: Binary or dictionary
		:keyword infile: File-like object
			or string containing the data for a new Binary
		:keyword filename: ... the filename to use
		:keyword record: ... the Record name, or new Record, to use
		:keyword param: ... Record param to use
			for the reference to the Binary name
		"""
		
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
				if pd.iter:
					v = rec.get(pd.name, [])
					if bdo.name not in v:
						v.append(bdo.name)
						rec[pd.name] = v
				else:
					if bdo.name != rec.get(pd.name):
						rec[pd.name] = bdo.name
			else:
				raise KeyError, "ParamDef %s does not accept files"%pd.name

			self.bdbs.record.cputs([rec], ctx=ctx, txn=txn)

		# Now move the file to the right location
		if newfile:
			if os.path.exists(bdo.filepath):
				raise SecurityError, "Cannot overwrite existing file!"
			# print "Renaming file %s -> %s"%(newfile, bdo.filepath)
			os.rename(newfile, bdo.filepath)


		return bdo


	@publicmethod("ping")
	def ping(self, *a, **kw):
		'Utitlity method to ensure the server is up'
		return 'pong'

	#########################
	# section: workflow
	#########################

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
