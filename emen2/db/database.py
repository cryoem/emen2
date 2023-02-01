# $Id: database.py,v 1.801 2012/10/31 13:00:49 irees Exp $
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
import uuid
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

# Versions
# from emen2.clients import __version__
VERSIONS = {
    "API": emen2.__version__,
    None: emen2.__version__
}

# Regular expression to parse Protocol views.
VIEW_REGEX = '(\$(?P<type>.)(?P<name>[\w\-]+)(?:="(?P<def>.+)")?(?:\((?P<args>[^$]+)?\))?(?P<sep>[^$])?)|((?P<text>[^\$]+))'
VIEW_REGEX = re.compile(VIEW_REGEX)

# basestring goes away in Python 3
basestring = (str, unicode)

# ian: todo: move this to EMEN2DBEnv
DB_CONFIG = """\
# Don't touch these
set_data_dir data
set_lg_dir journal
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


def getrandomid():
    """Generate a random ID."""
    return uuid.uuid4().hex


def getctime():
    """Current database time, as float in seconds since the epoch."""
    return time.time()


def gettime():
    """Returns the current database UTC time in ISO 8601 format."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'+00:00'


def getpw(pw=None):
    # import platform
    # import pwd
    # host = platform.node() or 'localhost'
    # defaultemail = "%s@%s"%(pwd.getpwuid(os.getuid()).pw_name, host)
    pw = pw or getpass.getpass("Password: ")
    while len(pw) < 6:
        if len(pw) == 0:
            print "Warning! No password!"
            pw = ''
            break
        elif len(pw) < 6:
            print "Warning! If you set a password, it needs to be more than 6 characters."
            pw = getpass.getpass("Password: ")
    return pw


def ol(name, output=True):
    """Convert a function argument to a list.
    
    Use method argument introspection to convert an argument value to a list.
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

    :keyword msg: Error message; default is Exception's docstring
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
def sendmail(to_addr, subject='', msg='', template=None, ctxt=None, **kwargs):
    """(Semi-internal) Send an email. You can provide either a template or a message subject and body.

    :param to_addr: Email recipient
    :keyword msg: Message text, or
    :keyword template: ... Template name  
    :keyword ctxt: ... Dictionary to pass to template  
    :return: Email recipient, or None if no message was sent  

    """    
    from_addr = emen2.db.config.get('mail.from')
    smtphost = emen2.db.config.get('mail.smtphost')

    ctxt = ctxt or {}
    ctxt["to_addr"] = to_addr
    ctxt["from_addr"] = from_addr
    ctxt["TITLE"] = emen2.db.config.get('customization.title')
    ctxt["uri"] = emen2.db.config.get('web.uri')

    if msg:
        msg = email.mime.text.MIMEText(msg)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg = msg.as_string()

    elif template:
        try:
            msg = emen2.db.config.templates.render_template(template, ctxt)
        except Exception, e:
            emen2.db.log.warn('Could not render template %s: %s'%(template, e))
            return
    else:
        raise ValueError, "No message to send!"

    print "Sending mail:"
    print msg

    if not from_addr:
        emen2.db.log.warn("Couldn't get mail config: No admin email set")
        return
    if not smtphost:
        emen2.db.log.warn("Couldn't get mail config: No SMTP Server")
        return

    # Actually send the message
    s = smtplib.SMTP(smtphost)
    s.set_debuglevel(1)
    s.sendmail(from_addr, [from_addr, to_addr], msg)
    emen2.db.log.info('Mail sent: %s -> %s'%(from_addr, to_addr))
    return to_addr
    
    
    

##### Open or create new database #####

def opendb(name=None, password=None, admin=False, db=None):
    """Open a database proxy.

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
    db = db or DB()
    
    # Create the proxy and login, as a user or admin.
    proxy = emen2.db.proxy.DBProxy(db=db)
    if name:
        proxy._login(name, password)
    elif admin:
        ctx = emen2.db.context.SpecialRootContext()
        ctx.refresh(db=proxy)
        proxy._ctx = ctx

    return proxy


def setup(db=None, rootpw=None, rootemail=None):
    """Initialize a new DB.

    @keyparam rootpw Root Account Password
    @keyparam rootemail Root Account email

    """
    defaultemail = 'root@localhost'
    print "\n=== Setup Admin (root) account ==="
    rootemail = rootemail or raw_input("Admin (root) email (default %s): "%defaultemail) or defaultemail
    rootpw = getpw(pw=rootpw)

    db = opendb(db=db, admin=True)
    with db:
        root = {'name':'root','email':rootemail, 'password':rootpw}
        db.put([root], keytype='user')
        loader = emen2.db.load.Loader(db=db, infile=emen2.db.config.get_filename('emen2', 'db/skeleton.json'))
        loader.load()
        rec = db.record.new(rectype='folder')
        rec.addgroup('authenticated')
        rec['name_folder'] = 'Root'
        db.record.put(rec)




##### EMEN2 Database Environment #####

class EMEN2DBEnv(object):
    """EMEN2 Database Environment."""
    
    # Transaction counter
    txncounter = 0

    # DB Environment flags
    ENVOPENFLAGS = 0
    ENVOPENFLAGS |= bsddb3.db.DB_CREATE
    ENVOPENFLAGS |= bsddb3.db.DB_INIT_MPOOL
    ENVOPENFLAGS |= bsddb3.db.DB_INIT_TXN
    ENVOPENFLAGS |= bsddb3.db.DB_INIT_LOCK
    ENVOPENFLAGS |= bsddb3.db.DB_INIT_LOG
    ENVOPENFLAGS |= bsddb3.db.DB_THREAD


    def __init__(self, path=None, create=None, snapshot=False, dbenv=None):
        """
        :keyword path: Directory containing environment.
        :keyword snapshot: Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
        :keyword create: Create the environment if it does not already exist.
        """
        
        # Database environment directory
        self.path = path or emen2.db.config.get('EMEN2DBHOME')
        if not self.path:
            raise ValueError, "No EMEN2 Database Environment specified."

        self.create = create or emen2.db.config.get('params.create')
        self.snapshot = snapshot or emen2.db.config.get('bdb.snapshot')
        self.cachesize = emen2.db.config.get('bdb.cachesize') * 1024 * 1024l

        # Paths
        self.LOGPATH = emen2.db.config.get('paths.log')
        self.JOURNAL_ARCHIVE = emen2.db.config.get('paths.journal_archive')
        self.TMPPATH = emen2.db.config.get('paths.tmp')
        self.SSLPATH = emen2.db.config.get('paths.ssl')

        # DBO BTrees
        self.keytypes =  {}

        # Txn info
        self.txnlog = {}

        # Pre- and post-commit actions.
        # These are used for things like renaming files during the commit phase.
        # TODO: The details of this are highly likely to change,
        #     or be moved to a different place.
        self._txncbs = collections.defaultdict(list)

        # Cache the vartypes that are indexable
        vtm = emen2.db.datatypes.VartypeManager()
        self.indexablevartypes = set()
        allvartypes = set()
        for y in vtm.getvartypes():
            y = vtm.getvartype(y)
            allvartypes.add(y.vartype)
            if y.keyformat:
                self.indexablevartypes.add(y.vartype)

        # Check that all the needed directories exist
        self.checkdirs()

        # Open the Database Environment
        emen2.db.log.info("Opening Database Environment: %s"%self.path)

        if dbenv:
            self.dbenv = dbenv
        else:
            dbenv = bsddb3.db.DBEnv()

            if snapshot or self.snapshot:
                dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
            
            txncount = (self.cachesize / 4096) * 2
            if txncount > 1024*128:
                txncount = 1024*128

            dbenv.set_cachesize(0, self.cachesize)
            dbenv.set_tx_max(txncount)
            dbenv.set_lk_max_locks(300000)
            dbenv.set_lk_max_lockers(300000)
            dbenv.set_lk_max_objects(300000)

            self.dbenv = dbenv

            # Open the DBEnv
            self.open()



    def start_replication(self, repmgr_host, repmgr_port):
        return
        # self.dbsite = None
        # if not (repmgr_host and repmgr_port):
        #     return
        #     
        # priority = repmgr_port - 10000
        #     
        # self.dbsite = self.dbenv.repmgr_site(repmgr_host, repmgr_port)
        # self.dbsite.set_config(bsddb3.db.DB_LOCAL_SITE, 1)
        # if priority == 0:
        #     self.dbsite.set_config(bsddb3.db.DB_GROUP_CREATOR, 1)
        #     
        # self.dbenv.rep_set_priority(100 - priority)
        # self.dbenv.repmgr_set_ack_policy(bsddb3.db.DB_REPMGR_ACKS_ONE)
        # self.dbenv.rep_set_timeout(bsddb3.db.DB_REP_ACK_TIMEOUT, 500)
        # self.dbenv.repmgr_start(3, bsddb3.db.DB_REP_ELECTION)


    def add_db(self, cls, **kwargs):
        """Add a BTree."""
        db = cls(dbenv=self, **kwargs)
        self.keytypes[db.keytype] = db


    def open(self):
        """Open the Database Environment."""
        try: self.dbenv.open(self.path, self.ENVOPENFLAGS)
	except:
		traceback.print_exc()
		print "Error opening environment: ",self.path


    # ian: todo: make this nicer.
    def close(self):
        """Close the Database Environment"""
        for k,v in self.keytypes.items():
            v.close()
        self.dbenv.close()
        self.dbenvs[self] = False
        
        
    #@classmethod()
    #def closeall(cls):
    #    pass    


    def __getitem__(self, key, default=None):
        """Pass dictionary gets to self.keytypes."""
        return self.keytypes.get(key, default)



    ##### Methods to create a database environment #####

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
            return

        paths = []
        for path in ['data', 'journal']:
            paths.append(os.path.join(self.path, path))
        
        for path in [self.LOGPATH, self.JOURNAL_ARCHIVE,  self.TMPPATH, self.SSLPATH]:
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


    ##### Log archive #####

    def log_archive(self, remove=True, checkpoint=True, txn=None):
        """Archive completed log files.

        :keyword remove: Remove the log files after moving them to the backup location
        :keyword checkpoint: Run a checkpoint first; this will allow more files to be archived
        """
        outpath = self.JOURNAL_ARCHIVE

        if checkpoint:
            emen2.db.log.info("Log Archive: Checkpoint")
            self.dbenv.txn_checkpoint()

        archivefiles = self.dbenv.log_archive(bsddb3.db.DB_ARCH_ABS)

        emen2.db.log.info("Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

        if not os.access(outpath, os.F_OK):
            os.makedirs(outpath)

        outpaths = []
        for archivefile in archivefiles:
            dest = os.path.join(outpath, os.path.basename(archivefile))
            emen2.db.log.info('Log Archive: %s -> %s'%(archivefile, dest))
            shutil.move(archivefile, dest)
            outpaths.append(dest)

        return outpaths
        
        
        
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

        txn = self.dbenv.txn_begin(parent=parent, flags=flags)
        # emen2.db.log.msg('TXN', "NEW TXN, flags: %s --> %s"%(flags, txn))

        type(self).txncounter += 1
        self.txnlog[txn.id()] = txn
        return txn


    def txncheck(self, txn=None, write=False):
        """Check a transaction status, or create a new transaction.

        :keyword txn: An existing open transaction
        :keyword write: See newtxn
        :return: Open transaction
        """
        if not txn:
            txn = self.newtxn(write=write)
        return txn


    def txnabort(self, txn):
        """Abort transaction.

        :keyword txn: An existing open transaction
        :exception: KeyError if transaction was not found
        """
        # emen2.db.log.msg('TXN', "TXN ABORT --> %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'before', 'abort')

        txn.abort()
        if txnid in self.txnlog:
            del self.txnlog[txnid]
        type(self).txncounter -= 1

        self._txncb(txnid, 'after', 'abort')
        self._txncbs.pop(txnid, None)


    def txncommit(self, txn):
        """Commit a transaction.

        :param txn: An existing open transaction
        :exception: KeyError if transaction was not found
        """
        # emen2.db.log.msg('TXN', "TXN COMMIT --> %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'before', 'commit')

        txn.commit()
        if txnid in self.txnlog:
            del self.txnlog[txnid]
        type(self).txncounter -= 1

        self._txncb(txnid, 'after', 'commit')
        self._txncbs.pop(txnid, None)

        if DB.sync_contexts.is_set():
            self._context.bdb.sync()
            DB.sync_contexts.clear()


    def checkpoint(self, txn=None):
        """Checkpoint the database environment."""
        return self.dbenv.txn_checkpoint()


    def txncb(self, txn, action, args=None, kwargs=None, when='before', condition='commit'):
        if when not in ['before', 'after']:
            raise ValueError, "Transaction callback 'when' must be before or after"
        if condition not in ['commit', 'abort']:
            raise ValueError, "Transaction callback 'condition' must be commit or abort"
        item = [when, condition, action, args or [], kwargs or {}]
        self._txncbs[txn.id()].append(item)


    # This is still being developed. Do not touch.
    def _txncb(self, txnid, when, condition):
        # Note: this takes txnid, not a txn. This
        # is because txn.id() is null after commit.
        actions = self._txncbs.get(txnid, [])
        for w, c, action, args, kwargs in actions:
            if w == when and c == condition:
                if action == 'rename':
                    self._txncb_rename(*args, **kwargs)
                elif action == 'email':
                    self._txncb_email(*args, **kwargs)
                elif action == 'thumbnail':
                    self._txncb_thumbnail(*args, **kwargs)
    
    
    def _txncb_rename(self, source, dest):
        emen2.db.log.info("Renaming file: %s -> %s"%(source, dest))
        try:
            shutil.move(source, dest)
        except Exception, e:
            emen2.db.log.error("Couldn't rename file %s -> %s"%(source, dest))

        
    def _txncb_email(self, *args, **kwargs):
        try:
            sendmail(*args, **kwargs)
        except Exception, e:
            emen2.db.log.error("Couldn't send email: %s"%e)
            
            
    def _txncb_thumbnail(self, bdo):
        try:
            emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
        except Exception, e:
            emen2.db.log.error("Couldn't start thumbnail builder")
            print e
    


##### Main Database Class #####

class DB(object):
    """EMEN2 Database

    This class provides access to the public API methods.
    """

    sync_contexts = threading.Event()

    def __init__(self, path=None, create=None):
        """EMEN2 Database.

        :keyword path: Directory containing an EMEN2 Database Environment.
        :keyword create: Create the environment if it does not already exist.

        """

        # Open the database
        self.dbenv = EMEN2DBEnv(path=path, create=create)

        # Cache for contexts
        self.contexts_cache = {}

        # Open Databases
        self._init()

        # Load DBOs from extensions.
        self._load_json(os.path.join(emen2.db.config.get_filename('emen2', 'db'), 'base.json'))
        emen2.db.config.load_jsons(cb=self._load_json)

        # Create root account, groups, and root record if necessary
        if self.dbenv.create:
            setup(db=self)


    def _init(self):
        """Open the databases."""
    
        # Authentication. These are not public.
        self.dbenv._context = emen2.db.context.ContextDB(keytype='context', dbenv=self.dbenv)
    
        # Main database items. These are available in the public API.
        self.dbenv.add_db(emen2.db.paramdef.ParamDefDB, keytype='paramdef')
        self.dbenv.add_db(emen2.db.user.UserDB, keytype='user')
        self.dbenv.add_db(emen2.db.group.GroupDB, keytype='group')
        self.dbenv.add_db(emen2.db.user.NewUserDB, keytype='newuser')
        self.dbenv.add_db(emen2.db.binary.BinaryDB, keytype="binary")
        self.dbenv.add_db(emen2.db.recorddef.RecordDefDB, keytype="recorddef")
        self.dbenv.add_db(emen2.db.binary.BinaryTmpDB, keytype="upload")
        
        # Records have moved to keyformat "s"
        self.dbenv.add_db(emen2.db.record.RecordDB, keytype="record") 


    def __str__(self):
        return "<DB: %s>"%(hex(id(self)))



    ##### Utility methods #####

    def _load_json(self, infile):
        """Load and cache a JSON file containing DBOs."""
        # Create a special root context to load the items
        ctx = emen2.db.context.SpecialRootContext(db=self)
        loader = emen2.db.load.BaseLoader(infile=infile)
        for keytype in ['paramdef', 'user', 'group', 'recorddef', 'binary', 'record']:
            for item in loader.loadfile(keytype=keytype):
                i = self.dbenv[keytype].dataclass(ctx=ctx)
                i._load(item)
                self.dbenv[keytype].addcache(i)


    def _getcontext(self, ctxid, host, ctx=None, txn=None):
        """(Internal) Takes a ctxid key and returns a Context.

        Note: The host provided must match the host in the Context

        :param ctxid: ctxid
        :param host: host
        :return: Context
        :exception: SessionError
        """
        
        # Find the context; check the cache first, then the bdb.
        # If no ctxid was provided, make an Anonymous Context.
        if ctxid:
            context = self.contexts_cache.get(ctxid) or self.dbenv._context.get(ctxid, txn=txn)
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
            indg = self.dbenv["group"].getindex('permissions', txn=txn)
            groups = indg.get(context.username, set(), txn=txn)
            grouplevels = {}
            for group in groups:
                group = self.dbenv["group"].get(group, txn=txn)
                grouplevels[group.name] = group.getlevel(context.username)

        # Sets the database reference, user record, display name, groups, and updates
        #    context access time.
        context.refresh(grouplevels=grouplevels, host=host, db=self)

        # Keep contexts cached.
        self.contexts_cache[ctxid] = context

        return context


    def _sudo(self, username=None, ctx=None, txn=None):
        """(Internal) Create an admin context for performing actions that require admin privileges."""
        emen2.db.log.security("Temporarily granting user %s administrative privileges"%username)
        ctx = emen2.db.context.SpecialRootContext()
        ctx.refresh(db=self, username=username)
        return ctx


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
        items = self.dbenv[keytype].cgets(names, ctx=ctx, txn=txn)
        for item in items:
            getattr(item, method)(*args, **kwargs)
        return self.dbenv[keytype].cputs(items, ctx=ctx, txn=txn)


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
        mrecs = self.dbenv["record"].cgets(names, ctx=ctx, txn=txn)
        vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
        regex = VIEW_REGEX
        
        k = regex.match(macro)
        keyformat = vtm.getmacro(k.group('name')).keyformat
        vtm.macro_preprocess(k.group('name'), k.group('args'), mrecs)

        for rec in mrecs:
            recs[rec.name] = vtm.macro_process(k.group('name'), k.group('args'), rec)

        return keyformat, recs


    def _boolmode_collapse(self, rets, boolmode):
        """(Internal) Perform bool operation on results."""
        if not rets:
            rets = [set()]
        if boolmode == 'AND':
            allret = reduce(set.intersection, rets)
        elif boolmode == 'OR':
            allret = reduce(set.union, rets)
        return allret


    def _findrecorddefnames(self, names, ctx=None, txn=None):
        """(Internal) Find referenced recorddefs."""
        recnames, recs, rds = listops.typepartition(names, basestring, emen2.db.dataobject.BaseDBObject)
        rds = set(rds)
        rds |= set([i.rectype for i in recs])
        if recnames:
            grouped = self.record_groupbyrectype(names, ctx=ctx, txn=txn)
            rds |= set(grouped.keys())
        return rds


    def _findparamdefnames(self, names, ctx=None, txn=None):
        """(Internal) Find referenced paramdefs."""
        recnames, recs, params = listops.typepartition(names, basestring, emen2.db.dataobject.BaseDBObject)
        params = set(params)
        if recnames:
            recs.extend(self.dbenv["record"].cgets(recnames, ctx=ctx, txn=txn))
        for i in recs:
            params |= set(i.keys())
            #rds = set([i.rectype for i in recs])
            #for rd in self.dbenv["recorddef"].cgets(rds, ctx=ctx, txn=txn):
            #    params |= set(rd.paramsK)
        return params


    def _findbyvartype(self, names, vartypes, ctx=None, txn=None):
        """(Internal) Find referenced users/binaries."""
        recnames, recs, values = listops.typepartition(names, basestring, emen2.db.dataobject.BaseDBObject)
        values = set(values)
        if recnames:
            recs.extend(self.dbenv["record"].cgets(recnames, filt=False, ctx=ctx, txn=txn))
        if not recs:
            return values

        # get the params we're looking for
        vtm = emen2.db.datatypes.VartypeManager()
        vt = set()
        vt_iterable = set()
        vt_firstitem = set()
        vt_reduce = set()
        pds = set()
        for rec in recs:
            pds |= set(rec.keys())
        for pd in self.dbenv["paramdef"].cgets(pds, ctx=ctx, txn=txn):
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
        names, items = zip(*self.dbenv[keytype].items(ctx=ctx, txn=txn))
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


    def _make_tables(self, recdefs, rec, markup, ctx, txn):
        """(Internal) Find "out-of-band" parameters."""
        # move built in params to end of table
        #par = [p for p in set(recdefs.get(rec.rectype).paramsK) if p not in builtinparams]
        # Default params
        public = set() | emen2.db.record.Record.attr_public
        show = set(rec.keys()) | recdefs.get(rec.rectype).paramsK | public
        descs = dict((i.name,i.desc_short) for i in self.dbenv['paramdef'].cgets(show, ctx=ctx, txn=txn))
        show -= public
        par = []
        par.extend(sorted(show, key=lambda x:descs.get(x, x)))
        par.extend(sorted(public, key=lambda x:descs.get(x, x)))
        # par = [p for p in recdefs.get(rec.rectype).paramsK if p not in builtinparams]
        # par += [p for p in rec.keys() if p not in par]
        return self._view_kv(par, markup=markup, ctx=ctx, txn=txn)


    def _view_kv(self, params, paramdefs={}, markup=False, ctx=None, txn=None):
        """(Internal) Create an HTML table for rendering.

        :param params: Use these ParamDef names
        :keyword paramdefs: ParamDef cache
        :keyword markup: Use HTML Markup (default=False)
        :return: HTML table of params
        """
        if markup:
            dt = ["""<table class="e2l-kv e2l-shaded">
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



    ######################################
    ###### Begin Public API          #####
    ######################################

    ##### Time #####

    @publicmethod()
    def time_difference(self, t1, t2=None, ctx=None, txn=None):
        """Returns the difference between two times in seconds.
        
        :param t1: The first time.
        :keyword t2: The second time; defaults to now.
        :return: Time difference, in seconds.
        """
        t1 = emen2.db.vartypes.parse_iso8601(t1)[0]

        t2 = t2 or gettime()
        t2 = emen2.db.vartypes.parse_iso8601(t2)[0]

        return t2 - t1
        
        
    @publicmethod()
    def time_now(self, ctx=None, txn=None):
        """Get current time.

        Examples:

        >>> db.time()
        2011-10-10T14:23:11+00:00

        :return: Current time string, YYYY-MM-DDTHH:MM:SS+00:00
        """
        return gettime()



    ###### Version ######

    @publicmethod()
    def version(self, program="API", ctx=None, txn=None):
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



    ##### Utilities #####

    @publicmethod()
    def ping(self, ctx=None, txn=None):
        """Utility method to ensure the server is up

        Examples:

        >>> db.ping()
        'pong'

        :return: Ping? 'pong'
        """
        return 'pong'



    ##### Login and Context Management #####

    @publicmethod(write=True, compat="login")
    def auth_login(self, username, password, host=None, ctx=None, txn=None):
        """Login.

        Returns auth token (ctxid), or fails with AuthenticationError.

        Examples:

        >>> db.auth.login(username='example@example.com', password='foobar')
        654067667525479cba8eb2940a3cf745de3ce608

        >>> db.auth.login(username='ian@example.com', password='foobar')
        AuthenticationError, "Invalid username, email, or password"

        :keyword username: Account name or email address
        :keyword password: Account password
        :keyword host: Bind auth token to this host. This is set by the proxy.
        :return: Auth token (ctxid)
        :exception AuthenticationError: Invalid user username, email, or password
        """
        # Check the password; user.checkpassword will raise Exception if wrong
        try:
            user = self.dbenv["user"].getbyemail(username, filt=False, txn=txn)
            # Allow admins to login to other accounts.
            if ctx.checkadmin():
                pass
            else:
                user.checkpassword(password)
        except SecurityError, e:
            emen2.db.log.security("Login failed, bad password: %s"%(username))                
            raise AuthenticationError, str(e)
        except KeyError, e:
            emen2.db.log.security("Login failed, no such user: %s"%(username))                
            raise AuthenticationError, AuthenticationError.__doc__

        # Create the Context for this user/host
        newcontext = emen2.db.context.Context(username=user.name, host=host)

        # This puts directly, instead of using cput.
        self.dbenv._context.put(newcontext.name, newcontext, txn=txn)
        emen2.db.log.security("Login succeeded: %s -> %s" % (newcontext.username, newcontext.name))

        return newcontext.name


    # This doesn't work until DB restart (the context isn't immediately cleared)?
    @publicmethod(write=True, compat="logout")
    def auth_logout(self, ctx=None, txn=None):
        """Delete context and logout.

        Examples:

        >>> db.auth.logout()
        None
        """
        # Remove the cached context, and delete the stored one.
        self.contexts_cache.pop(ctx.name, None)
        self.dbenv._context.delete(ctx.name, txn=txn)
        self.sync_contexts.set()


    @publicmethod(compat="checkcontext")
    def auth_check_context(self, ctx=None, txn=None):
        """Return basic information about the current Context.

        Examples:

        >>> db.auth.check.context()
        (ian, set(['admin', 'authenticated']))

        :return: (Context User name, set of Context groups)
        """
        return ctx.username, ctx.groups


    @publicmethod(compat="checkadmin")
    def auth_check_admin(self, ctx=None, txn=None):
        """Checks if the user has global write access.

        Examples:

        >>> db.auth.check.admin()
        True

        :return: True if user is an admin
        """
        return ctx.checkadmin()


    @publicmethod(compat="checkreadadmin")
    def auth_check_readadmin(self, ctx=None, txn=None):
        """Checks if the user has global read access.

        Examples:

        >>> db.auth.check.readadmin()
        True

        :return: True if user is a read admin
        """
        return ctx.checkreadadmin()


    @publicmethod(compat="checkcreate")
    def auth_check_create(self, ctx=None, txn=None):
        """Check for permission to create records.

        Examples:

        >>> db.auth.check.create()
        True

        :return: True if the user can create records
        """
        return ctx.checkcreate()



    ##### Generic methods #####

    @publicmethod()
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
        return getattr(self, '%s_get'%(keytype))(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod()
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

        :keyword keytype: Item keytype
        :return: New, uncommitted item
        :exception ExistingKeyError:
        :exception SecurityError:
        :exception ValidationError:
        """
        keytype = kwargs.pop('keytype', 'record')
        return getattr(self, '%s_new'%(keytype))(*args, **kwargs)
        
    
    @publicmethod()
    def exists(self, name, keytype='record', ctx=None, txn=None):
        """Check for the existence of an item.
        
        Examples:
        
        >>> db.exists("root", keytype="user")
        True
        
        :param name: Item name
        :keyword keytype: Item keytype
        :return: True if the item exists
        """
        return self.dbenv[keytype].exists(name, txn=txn)


    @publicmethod(write=True)
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
        return getattr(self, '%s_put'%(keytype))(items, ctx=ctx, txn=txn)


    @publicmethod(write=True)
    def delete(self, names, keytype='record', ctx=None, txn=None):
        keytype = kwargs.pop('keytype', 'record')
        return getattr(self, '%s_delete'%(keytype))(ctx=ctx, txn=txn)


    @publicmethod()
    def names(self, keytype='record', ctx=None, txn=None):
        keytype = kwargs.pop('keytype', 'record')
        return getattr(self, '%s_names'%(keytype))(ctx=ctx, txn=txn)
        
    
    @publicmethod()
    def find(self, keytype='record', ctx=None, txn=None):
        keytype = kwargs.pop('keytype', 'record')
        return getattr(self, '%s_find'%(keytype))(ctx=ctx, txn=txn)


    @publicmethod()
    def query(self, c=None, mode='AND', sortkey='name', pos=0, count=0, reverse=None, subset=None, keytype="record", ctx=None, txn=None, **kwargs):
        """General query.

        Constraints are provided in the following format:
            [param, operator, value]

        Operation and value are optional. An arbitrary number of constraints may be given.

        Operators:
            is            or        ==
            not            or        !=
            gt            or        >
            lt            or        <
            gte            or        >=
            lte            or        <=
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
            names:    Names of records found
            stats:    Query statistics
                length        Number of records found
                time        Execution time

        Examples:

        >>> db.query()
        {'names':[1,2, ...], 'stats': {'time': 0.001, 'length':1234}, 'c': [], ...}

        >>> db.query([['creator', 'is', 'ian']])
        {'names':[1,2,3], 'stats': {'time': 0.002, 'length':3}, 'c': [['creator', 'is', 'ian]], ...}

        >>> db.query([['creator', 'is', 'ian']], sortkey='creationtime', reverse=True)
        {'names':[3,2,1], 'stats': {'time': 0.002, 'length':3}, 'c': [['creator', 'is', 'ian]], 'sortkey': 'creationtime' ...}

        :keyparam c: Constraints
        :keyparam mode: Boolean mode for constraints
        :keyparam sortkey: Sort returned records by this param. Default is creationtime.
        :keyparam pos: Return results starting from (sorted record name) position
        :keyparam count: Return a limited number of results
        :keyparam reverse: Reverse results
        :keyparam subset: Restrict to names
        :keyparam keytype: Key type
        :return: A dictionary containing the original query arguments, and the result in the 'names' key
        :exception KeyError:
        :exception ValidationError:
        :exception SecurityError:

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
            keytype=keytype,
            subset=subset
        )

        # Run the query
        q = self.dbenv[keytype].query(c=c, mode=mode, subset=subset, ctx=ctx, txn=txn)
        q.run()
        ret['names'] = q.sort(sortkey=sortkey, pos=pos, count=count, reverse=reverse)
        ret['stats']['length'] = len(q.result)
        ret['stats']['time'] = q.time
        return ret


    @publicmethod()
    def table(self, c=None, mode='AND', sortkey='name', pos=0, count=100, reverse=None, subset=None, keytype="record", viewdef=None, ctx=None, txn=None, **kwargs):
        """Query results suitable for making a table.

        This method extends query() to include rendered views in the results.
        These are available in the 'rendered' key in the return value. Key is
        the item name, value is a list of the values for each column. The
        headers for each column are in the 'headers' key.

        The maximum number of items returned in the table is 1000.
        
        :keyparam c: Constraints
        :keyparam mode: Boolean mode for constraints
        :keyparam sortkey: Sort returned records by this param. Default is creationtime.
        :keyparam pos: Return results starting from (sorted record name) position
        :keyparam count: Return a limited number of results
        :keyparam reverse: Reverse results
        :keyparam subset: Restrict to names
        :keyparam keytype: Key type
        :keyparam viewdef: View definition.
            
        """
        # Limit tables to 1000 items per page.
        if count < 1 or count > 1000:
            count = 1000

        # Records are shown newest-first by default...
        if keytype == "record" and sortkey in ['name', 'creationtime'] and reverse is None:
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
            keytype=keytype,
            subset=subset
        )

        # Run the query
        q = self.dbenv[keytype].query(c=c, mode=mode, subset=subset, ctx=ctx, txn=txn)
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
                rt = self.record_groupbyrectype(toget, ctx=ctx, txn=txn)
                for k,v in rt.items():
                    for name in v:
                        q.cache[name]['rectype'] = k

            # Update..
            rectypes = set(q.cache[i].get('rectype') for i in q.result)
            rectypes -= set([None])

            # Get the viewdef
            if len(rectypes) == 1:
                rd = self.dbenv["recorddef"].cget(rectypes.pop(), ctx=ctx, txn=txn)
                viewdef = rd.views.get('tabularview', defaultviewdef)
            else:
                try:
                    rd = self.dbenv["recorddef"].cget("root", filt=False, ctx=ctx, txn=txn)
                except (KeyError, SecurityError):
                    viewdef = defaultviewdef
                else:
                    viewdef = rd.views.get('tabularview', defaultviewdef)

        for i in emen2.db.config.get('customization.table_add_columns'):
            viewdef = '%s $$%s'%(viewdef.replace('$$%s'%i, ''), i)

        # Render the table
        table = self.record_render(names, viewdef=viewdef, table=True, edit='auto', ctx=ctx, txn=txn)

        ret['table'] = table
        ret['names'] = names
        ret['stats']['length'] = len(q.result)
        ret['stats']['time'] = q.time + (time.time()-t)
        return ret


    @publicmethod()
    def plot(self, c=None, mode='AND', sortkey='name', pos=0, count=0, reverse=None, subset=None, keytype="record", x=None, y=None, z=None, ctx=None, txn=None, **kwargs):
        """Query results suitable for plotting.

        This method extends query() to help generate a plot. The results are
        not sorted; the sortkey, pos, count, and reverse keyword arguments
        are ignored.

        Provide dictionaries for the x, y, and z keywords. These may have the
        following keys:
            key:    Parameter name for this axis.
            bin:    Number of bins, or date width for time parameters.
            min:    Minimum
            max:    Maximum

        Currently only the 'key' from each x, y, z attribute is used to make
        sure it is part of the query that runs.

        The matching values for each constraint are available in the "items"
        key in the return value. This is a list of stub items.

        :keyparam c: Constraints
        :keyparam mode: Boolean mode for constraints
        :keyparam x: X arguments
        :keyparam y: Y arguments
        :keyparam z: Z arguments
        :keyparam subset: Restrict to names        
        :keyparam keytype: Key type

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
            subset=subset
        )

        qparams = [i[0] for i in c]
        qparams.append('name')
        for axis in [x.get('key'), y.get('key'), z.get('key')]:
            if axis and axis not in qparams:
                c.append([axis, 'any', None])
                
        # Run the query
        q = self.dbenv[keytype].query(c=c, mode=mode, subset=subset, ctx=ctx, txn=txn)
        q.run()

        ret['names'] = q.sort(sortkey=sortkey, pos=pos, count=count, reverse=reverse)
        ret['stats']['length'] = len(q.result)
        ret['stats']['time'] = q.time
        ret['recs'] = q.cache.values()
        return ret



    ##### Relationships #####

    @publicmethod(write=True, compat="pclink")
    def rel_pclink(self, parent, child, keytype='record', ctx=None, txn=None):
        """Link a parent object with a child

        Examples:

        >>> db.rel.pclink(0, 46604)
        None

        >>> db.rel.pclink('physical_property', 'temperature', keytype='paramdef')
        None

        :param parent: Parent name
        :param child: Child name
        :param keytype: Item type
        :keyword filt: Ignore failures
        :return:
        :exception KeyError:
        :exception SecurityError:
        
        """
        return self.dbenv[keytype].pclink(parent, child, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="pcunlink")
    def rel_pcunlink(self, parent, child, keytype='record', ctx=None, txn=None):
        """Remove a parent-child link

        Examples:

        >>> db.rel.pcunlink(0, 46604)
        None

        >>> db.rel.pcunlink('physical_property', 'temperature', keytype='paramdef')
        None

        :param parent: Parent name
        :param child: Child name
        :keyword keytype: Item type
        :keyword filt: Ignore failures
        :return:
        :exception KeyError:
        :exception SecurityError:
        """
        return self.dbenv[keytype].pcunlink(parent, child, ctx=ctx, txn=txn)


    @publicmethod(write=True)
    def rel_relink(self, removerels=None, addrels=None, keytype='record', ctx=None, txn=None):
        """Add and remove a number of parent-child relationships at once.

        Examples:

        >>> db.rel.relink({"0":"136"}, {"100":"136"})
        None

        :keyword removerels: Dictionary of relationships to remove.
        :keyword addrels: Dictionary of relationships to add.
        :keyword keytype: Item keytype
        :keyword filt: Ignore failures
        :return:
        :exception KeyError:
        :exception SecurityError:
        """
        return self.dbenv[keytype].relink(removerels, addrels, ctx=ctx, txn=txn)


    @publicmethod(compat="getsiblings")
    def rel_siblings(self, name, rectype=None, keytype="record", ctx=None, txn=None):
        """Get the siblings of the object as a tree.

        Siblings are any items that share a common parent.

        Examples:

        >>> db.rel.siblings(136, rectype='group')
        set([136, 358307])

        >>> db.rel.siblings('creationtime', keytype='paramdef')
        set([u'website', u'date_start', u'name_first', u'observed_by', ...])

        >>> db.rel.siblings('ccd', keytype='recorddef')
        set([u'ccd', u'micrograph', u'ddd', u'stack', u'scan'])

        :param names: Item name(s)
        :keyword rectype: Filter by RecordDef. Can be single RecordDef or list. Recurse with '*'
        :keyword keytype: Item keytype
        :keyword filt: Ignore failures
        :return: All items that share a common parent
        :exception KeyError:
        :exception SecurityError:
        """
        return self.dbenv[keytype].siblings(name, rectype=rectype, ctx=ctx, txn=txn)


    @publicmethod(compat="getparents")
    @ol('names')
    def rel_parents(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None):
        """Get the parents of an object

        This method is the same as as db.rel(..., rel='parents', tree=False)

        Examples:

        >>> db.rel.parents(0)
        set([])

        >>> db.rel.parents(46604, recurse=-1)
        set([136, 0])

        >>> db.rel.parents('ccd', recurse=-1, keytype='recorddef')
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
        return self.dbenv[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', ctx=ctx, txn=txn)


    @publicmethod(compat="getparenttree")
    @ol('names', output=False)
    def rel_parentstree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None):
        """Get the parents of the object as a tree

        This method is the same as as db.rel(..., rel='parents', tree=True)

        Examples:

        >>> db.rel.parentstree(46604, recurse=-1)
        {136: set([0]), 46604: set([136])}

        >>> db.rel.parentstree([46604, 74547], recurse=-1)
        {136: set([0]), 74547: set([136]), 46604: set([136])}

        >>> db.rel.parentstree([46604, 74547], recurse=-1, rectype='group')
        {74547: set([136]), 46604: set([136])}

        >>> db.rel.parentstree('ccd', recurse=2, keytype='recorddef')
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
        return self.dbenv[keytype].rel(names, recurse=recurse, rectype=rectype, rel='parents', tree=True, ctx=ctx, txn=txn)


    @publicmethod(compat="getchildren")
    @ol('names')
    def rel_children(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None):
        """Get the children of an object.

        This method is the same as db.rel(..., rel='children', tree=False)

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
        return self.dbenv[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', ctx=ctx, txn=txn)


    @publicmethod(compat="getchildtree")
    @ol('names', output=False)
    def rel_childrentree(self, names, recurse=1, rectype=None, keytype='record', ctx=None, txn=None):
        """Get the children of the object as a tree

        This method is the same as as db.rel(..., rel='children', tree=True)

        Examples:

        >>> db.rel.childrentree(0, rectype='group')
        {0: set([136, 358307])}

        >>> db.rel.childrentree([46604, 74547], rectype='subproject')
        {74547: set([75585, 270211, ...]), 46604: set([380432, 57474, ...])}

        >>> db.rel.childrentree(136, recurse=2, rectype=['project*'])
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
        return self.dbenv[keytype].rel(names, recurse=recurse, rectype=rectype, rel='children', tree=True, ctx=ctx, txn=txn)


    @publicmethod()
    @ol('names', output=False)
    def rel_tree(self, names, recurse=1, rectype=None, keytype="record", rel="children", ctx=None, txn=None):        
        return self.dbenv[keytype].rel(names, recurse=recurse, rectype=rectype, rel=rel, tree=True, ctx=ctx, txn=txn)


    @publicmethod()
    @ol('names')
    def rel_rel(self, names, keytype="record", ctx=None, txn=None):
        return self.dbenv[keytype].rel(names, ctx=ctx, txn=txn)



    ##### ParamDef #####

    @publicmethod(compat="getparamdef")
    @ol('names')
    def paramdef_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["paramdef"].cgets(names, filt=filt, ctx=ctx, txn=txn)
        
        
    @publicmethod(compat="newparamdef")
    def paramdef_new(self, vartype=None, name=None, ctx=None, txn=None):
        return self.dbenv["paramdef"].new(vartype=vartype, name=name, ctx=ctx, txn=txn)
                

    @publicmethod(write=True, compat="putparamdef")
    @ol('items')
    def paramdef_put(self, items, ctx=None, txn=None):
        return self.dbenv["paramdef"].cputs(items, ctx=ctx, txn=txn)


    @publicmethod(compat="getparamdefnames")
    def paramdef_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["paramdef"].names(names=names, ctx=ctx, txn=txn)
        
        
    @publicmethod(compat="findparamdef")
    def paramdef_find(self, *args, **kwargs):
        """Find a ParamDef, by general search string, or by searching attributes.

        Keywords can be combined.

        Examples:

        >>> db.paramdef.find(query='temperature')
        [<ParamDef temperature>, <ParamDef temperature_ambient>, <ParamDef temperature_cryoholder>, ...]

        >>> db.paramdef.find(vartype=binary, record='136*')
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
        
    
    @publicmethod(compat="getpropertynames")
    def paramdef_properties(self, ctx=None, txn=None):
        """Get all supported physical properties.

        A number of physical properties are included by default.
        Extensions may extend this by subclassing emen2.db.properties.Property()
        and using the registration decorator. See that module for details.

        >>> db.paramdef.properties()
        set(['transmittance', 'force', 'bytes', 'energy', 'resistance', ...])

        :return: Set of all available properties.
        """
        vtm = emen2.db.datatypes.VartypeManager()
        return set(vtm.getproperties())


    @publicmethod(compat="getpropertyunits")
    def paramdef_units(self, name, ctx=None, txn=None):
        """Returns a list of recommended units for a particular property.
        Other units may be used if they can be converted to the property's
        default units.

        Examples:

        >>> db.paramdef.units('volume')
        set(['nL', 'mL', 'L', 'uL', 'gallon', 'm^3'])

        >>> db.paramdef.units('length')
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


    @publicmethod(compat="getvartypenames")
    def paramdef_vartypes(self, ctx=None, txn=None):
        """Get all supported datatypes.

        A number of parameter data types (vartypes) are included by default.
        Extensions may add extend this by subclassing emen2.db.vartypes.Vartype()
        and using the registration decorator. See that module for details.

        Examples:

        >>> db.paramdef.vartypes()
        set(['text', 'string', 'binary', 'user', ...])

        :return: Set of all available datatypes.
        """
        vtm = emen2.db.datatypes.VartypeManager()
        return set(vtm.getvartypes())



    ##### User #####

    @publicmethod(compat="getuser")
    @ol('names')
    def user_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["user"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod()
    def user_new(self, password=None, email=None, name=None, ctx=None, txn=None):
        raise NotImplementedError, "Use newuser.new() to create new users."
    

    @publicmethod(write=True, compat="putuser")
    @ol('items')
    def user_put(self, items, ctx=None, txn=None):
        return self.dbenv["user"].cputs(items, ctx=ctx, txn=txn)


    @publicmethod(compat="getusernames")
    def user_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["user"].names(names=names, ctx=ctx, txn=txn)


    @publicmethod(compat="finduser")
    def user_find(self, query=None, record=None, count=100, ctx=None, txn=None, **kwargs):
        """Find a user, by general search string, or by name_first/name_middle/name_last/email/name.

        Keywords can be combined.

        Examples:

        >>> db.user.find(name_last='rees')
        [<User ian>, <User kay>, ...]

        >>> db.user.find(record=136)
        [<User ian>, <User steve>, ...]

        >>> db.user.find(email='bcm.edu', record='137*')
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
            foundusers = self.dbenv["user"].names(ctx=ctx, txn=txn)

        cs = []
        for term in query:
            cs.append([['name_first', 'contains', term], ['name_last', 'contains', term]])
        for param in ['name_first', 'name_middle', 'name_last']:
            if kwargs.get(param):
                cs.append([[param, 'contains', kwargs.get(param)]])
        for c in cs:
            # btree.query supports nested constraints,
            # but I don't have the interface finalized.
            q = self.dbenv["record"].query(c=c, mode='OR', ctx=ctx, txn=txn)
            q.run()
            if q.result is None:
                pass
            elif foundrecs is None:
                foundrecs = q.result
            else:
                foundrecs &= q.result

        # Get 'username' from the found records.
        if foundrecs:
            recs = self.dbenv["record"].cgets(foundrecs, ctx=ctx, txn=txn)
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
            q = self.dbenv["user"].query(c=c, ctx=ctx, txn=txn)
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

        return self.dbenv["user"].cgets(foundusers or [], ctx=ctx, txn=txn)
        
        
    @publicmethod(write=True, admin=True, compat="disableuser")
    def user_disable(self, names, filt=True, ctx=None, txn=None):
        """(Admin Only) Disable a User.

        Examples:

        >>> db.user.disable('steve')
        <User steve>

        >>> db.user.disable(['wah', 'steve'])
        [<User wah>, <User steve>]

        :param names: User name(s)
        :keyword filt: Ignore failures
        :return: Updated user(s)
        :exception KeyError:
        :exception SecurityError:
        """
        return self._mapput('user', names, 'disable', ctx=ctx, txn=txn)


    @publicmethod(write=True, admin=True, compat="enableuser")
    def user_enable(self, names, filt=True, ctx=None, txn=None):
        """(Admin Only) Re-enable a User.

        Examples:

        >>> db.user.enable('steve')
        <User steve>

        >>> db.user.enable(['wah', 'steve'])
        [<User wah>, <User steve>]

        :param names: User name(s)
        :keyword filt: Ignore failures
        :return: Updated user(s)
        :exception KeyError:
        :exception SecurityError:
        """
        return self._mapput('user', names, 'enable', ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="setprivacy")
    def user_setprivacy(self, names, state, ctx=None, txn=None):
        """Set privacy level.

        Examples:

        >>> db.user.setprivacy('ian', 2)
        <User ian>

        >>> db.user.setprivacy(names=['ian', 'wah'], state=2)
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


    # These methods sometimes use put instead of cput because they need to modify
    # the user's secret auth token.
    @publicmethod(write=True, compat="setemail")
    def user_setemail(self, name, email, secret=None, password=None, ctx=None, txn=None):
        """Change a User's email address.

        This will require you to verify that you own the account by
        responding with an auth token sent to the new email address.
        Use the received auth token to sign the call using the
        'secret' keyword.

        Note: This method only takes a single User name.

        Note: An Admin can change a user's email without the user's password or auth token.

        Examples:

        >>> db.user.setemail('ian', 'ian@example.com', password='foobar')
        <User ian>

        >>> db.user.setemail('ian', 'ian@example.com', secret='654067667525479cba8eb2940a3cf745de3ce608')
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

        # Verify the email address is owned by the user requesting change.
        # 1. User authenticates they *really* own the account
        #     by providing the acct password
        # 2. An email will be sent to the new account specified,
        #     containing an auth token
        # 3. The user comes back and calls the method with this token
        # 4. Email address is updated and reindexed

        # Check that no other user is currently using this email.
        ind = self.dbenv["user"].getindex('email', txn=txn)
        if ind.get(email, txn=txn):
            time.sleep(2)
            raise SecurityError, "The email address %s is already in use"%(email)

        # Do not use cget; it will strip out the secret.
        user = self.dbenv["user"].get(name, filt=False, txn=txn)
        user_secret = getattr(user, 'secret', None)
        user.setContext(ctx)
        if user_secret:
            user.__dict__['secret'] = user_secret
        
        # Actually change user email.
        oldemail = user.email
        user.setemail(email, secret=secret, password=password)
        user_secret = getattr(user, 'secret', None)

        ctxt = {}
        ctxt['name'] = user.name
        ctxt['email'] = email
        ctxt['oldemail'] = oldemail

        # Send out confirmation or verification email.
        if user.email == oldemail:
            # Need to verify email address change by receiving secret.
            emen2.db.log.security("Sending email verification for user %s to %s"%(user.name, user.email))
            # Note: cputs will always ignore the secret; write directly
            self.dbenv["user"].put(user.name, user, txn=txn)

            # Send the verify email containing the auth token
            ctxt['secret'] = user_secret[2]
            self.dbenv.txncb(txn, 'email', kwargs={'to_addr':email, 'template':'/email/email.verify', 'ctxt':ctxt})

        else:
            # raise Exception, "There is a known issue with this form. I am working on it."
            # Verified with secret.
            # user.setContext(ctx)
            emen2.db.log.security("Changing email for user %s to %s"%(user.name, user.email))
            self.dbenv['user'].cputs([user], ctx=ctx, txn=txn)
            # Note: Since we're putting directly,
            #     have to force the index to update
            # Send the user an email to acknowledge the change
            self.dbenv.txncb(txn, 'email', kwargs={'to_addr':email, 'template':'/email/email.verified', 'ctxt':ctxt})

        return self.dbenv["user"].cget(user.name, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="setpassword")
    def user_setpassword(self, name, oldpassword, newpassword, secret=None, ctx=None, txn=None):
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

        # Try to authenticate using either the password OR the secret!
        # Note: The password will be hidden if ctx.username != user.name
        # user = self.dbenv["user"].cget(name or ctx.username, filt=False, ctx=ctx, txn=txn)
        #ed: odded 'or ctx.username' to match docs
        user = self.dbenv["user"].getbyemail(name, filt=False, txn=txn)
        if not secret:
            user.setContext(ctx)
        user.setpassword(oldpassword, newpassword, secret=secret)

        # ian: todo: evaluate to use put/cput..
        emen2.db.log.security("Changing password for %s"%user.name)
        self.dbenv["user"].put(user.name, user, txn=txn)
        self.dbenv.txncb(txn, 'email', kwargs={'to_addr':user.email, 'template':'/email/password.changed'})
        return self.dbenv["user"].cget(user.name, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="resetpassword")
    def user_resetpassword(self, name, ctx=None, txn=None):
        """Reset User password.

        This is accomplished by sending a password reset auth token to the
        User's currently registered email address. Use this auth token
        to sign a call to db.setpassword() using the 'secret' keyword.

        Note: This method only takes a single User name.

        Examples:

        >>> db.user.resetpassword()
        <User ian>

        :keyword name: User name. Default is the current context user.
        :return: Updated user
        :exception KeyError:
        :exception SecurityError:
        """
        user = self.dbenv["user"].getbyemail(name, filt=False, txn=txn)
        user.resetpassword()

        # Use direct put to preserve the secret
        self.dbenv["user"].put(user.name, user, txn=txn)

        # Absolutely never reveal the secret via any mechanism
        # but email to registered address
        ctxt = {}
        ctxt['secret'] =  user.secret[2]
        ctxt['name'] = user.name
        self.dbenv.txncb(txn, 'email', kwargs={'to_addr':user.email, 'template':'/email/password.reset', 'ctxt':ctxt})
        emen2.db.log.security("Setting resetpassword secret for %s"%user.name)        
        return self.dbenv["user"].cget(user.name, ctx=ctx, txn=txn)



    ##### New Users #####

    @publicmethod(admin=True, compat="getqueueduser")
    @ol('names')
    def newuser_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["newuser"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod()
    def newuser_new(self, password=None, email=None, name=None, ctx=None, txn=None):
        return self.dbenv["newuser"].new(password=password, email=email, name=name, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="adduser")
    @ol('items')
    def newuser_put(self, items, ctx=None, txn=None):
        """Add a new user.

        Note: This only adds the user to the new user queue. The
        account must be processed by an administrator before it
        becomes active.

        Examples:

        >>> db.newuser.put(<NewUser kay>)
        <NewUser kay>

        >>> db.newuser.put({'name':'kay', 'password':'foobar', 'email':'kay@example.com'})
        <NewUser kay>

        :param items: New user(s).
        :return: New user(s)
        :exception KeyError:
        :exception ExistingKeyError:
        :exception SecurityError:
        :exception ValidationError:
        """
        items = self.dbenv["newuser"].cputs(items, ctx=ctx, txn=txn)

        autoapprove = emen2.db.config.get('users.autoapprove')
        if autoapprove:
            rootctx = self._sudo()
            rootctx.db._txn = txn
            self.newuser_approve([user.name for user in items], ctx=rootctx, txn=txn)
        else:
            # Send account request email
            for user in items:
                self.dbenv.txncb(txn, 'email', kwargs={'to_addr':user.email, 'template':'/email/adduser.signup'})

        return items
        

    @publicmethod(admin=True, compat="getuserqueue")
    def newuser_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["newuser"].names(names=names, ctx=ctx, txn=txn)
        

    @publicmethod(admin=True)
    def newuser_find(self, names=None, ctx=None, txn=None):
        return self.dbenv["newuser"].names(names=names, ctx=ctx, txn=txn)
        

    @publicmethod(write=True, admin=True, compat="approveuser")
    @ol('names')
    def newuser_approve(self, names, secret=None, reject=None, filt=True, ctx=None, txn=None):
        """(Admin Only) Approve account in user queue.

        Examples:

        >>> db.newuser.approve('kay')
        <User kay>

        >>> db.newuser.approve(['kay', 'matt'])
        [<User kay>, <User matt>]

        >>> db.newuser.approve('kay', secret='654067667525479cba8eb2940a3cf745de3ce608')
        <User kay>

        :param names: New user queue name(s)
        :keyword secret: User secret for self-approval
        :keyword reject: Also reject new users: see db.newuser.reject(). For convenience.
        :keyword filt: Ignore failures
        :return: Approved User(s)
        :exception ExistingKeyError:
        :exception KeyError:
        :exception SecurityError:
        :exception ValidationError:
        """

        group_defaults = emen2.db.config.get('users.group_defaults')
        autoapprove = emen2.db.config.get('users.autoapprove')

        # Get users from the new user approval queue
        newusers = self.dbenv["newuser"].cgets(names, filt=filt, ctx=ctx, txn=txn)
        cusers = []

        # This will also check if the current username or email is in use
        for newuser in newusers:
            name = newuser.name

            # Delete the pending user
            self.dbenv["newuser"].delete(name, txn=txn)

            user = self.dbenv["user"].new(name=name, email=newuser.email, password=newuser.password, ctx=ctx, txn=txn)
            # Put the new user
            user = self.dbenv["user"].cput(user, ctx=ctx, txn=txn)

            # Update default Groups
            # for group in group_defaults:
            #    gr = self.dbenv["group"].cget(group, ctx=ctx, txn=txn)
            #    gr.adduser(user.name)
            #    self.dbenv["group"].cput(gr, ctx=ctx, txn=txn)

            # Create the "Record" for this user
            rec = self.dbenv["record"].new(rectype='person', ctx=ctx, txn=txn)

            # Are there any child records specified...
            childrec = newuser.signupinfo.pop('child', None)

            # This gets updated with the user's signup info
            rec['username'] = name
            rec.update(newuser.signupinfo)
            rec.adduser(name, level=2)
            rec.addgroup("authenticated")
            rec = self.dbenv["record"].cput(rec, ctx=ctx, txn=txn)

            # Update the User with the Record name and put again
            user.record = rec.name
            user = self.dbenv["user"].cput(user, ctx=ctx, txn=txn)
            cusers.append(user)

            if childrec:
                crec = self.record_new(rectype=childrec.get('rectype'), ctx=ctx, txn=txn)
                crec.adduser(name, level=3)
                crec.parents.add(rec.name)
                crec.update(childrec)
                crec = self.dbenv["record"].cput(crec, ctx=ctx, txn=txn)

        # Send the 'account approved' emails
        for user in cusers:
            user.getdisplayname()
            ctxt = {'name':user.name, 'displayname':user.displayname}
            template = '/email/adduser.approved'
            if autoapprove:
                template = '/email/adduser.autoapproved'
            self.dbenv.txncb(txn, 'email', kwargs={'to_addr':user.email, 'template':template, 'ctxt':ctxt})

        return self.dbenv["user"].cgets(set([user.name for user in cusers]), ctx=ctx, txn=txn)


    @publicmethod(write=True, admin=True, compat="rejectuser")
    @ol('names')
    def newuser_reject(self, names, filt=True, ctx=None, txn=None):
        """(Admin Only) Remove a user from the new user queue.

        Examples:

        >>> db.newuser.reject('spambot')
        set(['spambot'])

        >>> db.newuser.reject(['kay', 'spambot'])
        set(['kay', 'spambot'])

        :param names: New queue name(s) to reject
        :keyword filt: Ignore failures
        :return: Rejected user name(s)
        :exception KeyError:
        :exception SecurityError:
        """
        emails = {}
        users = self.dbenv["newuser"].cgets(names, filt=filt, ctx=ctx, txn=txn)
        for user in users:
            emails[user.name] = user.email

        for    user in users:
            self.dbenv["newuser"].delete(user.name, txn=txn)

	### disabling this for now --steve 9/4/19
        # Send the emails
#        for name, email in emails.items():
#            ctxt = {'name':name}
#            self.dbenv.txncb(txn, 'email', kwargs={'to_addr':email, 'template':'/email/adduser.rejected', 'ctxt':ctxt})

        return set(emails.keys())



    ##### Group #####

    @publicmethod(compat="getgroup")
    @ol('names')
    def group_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["group"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod(compat="newgroup")
    def group_new(self, name=None, ctx=None, txn=None):
        return self.dbenv["group"].new(name=name, ctx=ctx, txn=txn)


    @publicmethod(write=True, admin=True, compat="putgroup")
    @ol('items')
    def group_put(self, items, ctx=None, txn=None):
        return self.dbenv["group"].cputs(items, ctx=ctx, txn=txn)


    @publicmethod(compat="getgroupnames")
    def group_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["group"].names(names=names, ctx=ctx, txn=txn)


    @publicmethod(compat="findgroup")
    def group_find(self, query=None, record=None, count=100, ctx=None, txn=None):
        """Find a group.

        Keywords can be combined.

        Examples:

        >>> db.group.find('admin')
        [<Group admin>, <Group readonlyadmin>]

        >>> db.group.find(record=136)
        [<Group authenticated>, <Group ncmiusers>]

        :keyword query: Find in Group's name or displayname
        :keyword record: Referenced in Record name(s)
        :keyword count: Limit number of results
        :keyword boolmode: AND / OR for each search constraint
        :return: Groups
        """
        # No real indexes yet (small). Just get everything and sort directly.
        items = self.dbenv["group"].cgets(self.dbenv["group"].names(ctx=ctx, txn=txn), ctx=ctx, txn=txn)
        ditems = listops.dictbykey(items, 'name')

        rets = []
        query = unicode(query or '').split()

        # If query is empty, match everything. Do this only for group.find, for now.
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



    ##### RecordDef #####

    @publicmethod(compat="getrecorddef")
    @ol('names')
    def recorddef_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["recorddef"].cgets(names, filt=filt, ctx=ctx, txn=txn)
        

    @publicmethod(compat="newrecorddef")
    def recorddef_new(self, mainview=None, name=None, ctx=None, txn=None):
        return self.dbenv["recorddef"].new(mainview=mainview, name=name, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="putrecorddef")
    @ol('items')
    def recorddef_put(self, items, ctx=None, txn=None):
        return self.dbenv["recorddef"].cputs(items, ctx=ctx, txn=txn)


    @publicmethod(compat="getrecorddefnames")
    def recorddef_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["recorddef"].names(names=names, ctx=ctx, txn=txn)


    @publicmethod(compat="findrecorddef")
    def recorddef_find(self, *args, **kwargs):
        """Find a RecordDef, by general search string, or by searching attributes.

        Keywords can be combined.

        Examples:

        >>> db.recorddef.find(query='CCD')
        [<RecordDef ccd>, <RecordDef image_capture>]

        >>> db.recorddef.find(name='image_capture*')
        [<RecordDef ccd>, <RecordDef scan>, <RecordDef micrograph>, ...]

        >>> db.recorddef.find(mainview='freezing apparatus')
        [<RecordDef freezing], <RecordDef vitrobot>, <RecordDef gatan_cp3>, ...]

        >>> db.recorddef.find(record=[1,2,3])
        [<RecordDef folder>, <RecordDef project>]

        >>> db.recorddef.find(name='project*', record='136*')
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



    ##### Records #####

    @publicmethod(compat="getrecord")
    @ol('names')
    def record_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["record"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod(compat="newrecord")
    def record_new(self, rectype=None, **kwargs):
        return self.dbenv["record"].new(rectype=rectype, **kwargs)


    @publicmethod(write=True, compat="putrecord")
    @ol('items')
    def record_put(self, items, ctx=None, txn=None):
        return self.dbenv["record"].cputs(items, ctx=ctx, txn=txn)


    @publicmethod()
    def record_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["record"].names(names=names, ctx=ctx, txn=txn)


    @publicmethod()
    def record_find(self, **kwargs):
        raise NotImplementedError


    @publicmethod(write=True, compat="hiderecord")
    @ol('names')
    def record_hide(self, names, childaction=None, filt=True, ctx=None, txn=None):
        """Unlink and hide a record; it is still accessible to owner.
        Records are never truly deleted, just hidden.

        Examples:

        >>> db.record.hide(136)
        <Record 136 group>

        >>> db.record.hide([136, 137])
        [<Record 136 group>]

        >>> db.record.hide([136, 137], filt=False)
        SecurityError

        >>> db.record.hide(12345, filt=False)
        KeyError

        :param name: Record name(s) to delete
        :keyword filt: Ignore failures
        :return: Deleted Record(s)
        :exception KeyError:
        :exception SecurityError:
        """
        names = set(names)

        if childaction == 'orphaned':
            names |= self.record_findorphans(names, ctx=ctx, txn=txn)
        elif childaction == 'all':
            c = self.rel_children(names, ctx=ctx, txn=txn)
            for k,v in c.items():
                names |= v
                names.add(k)

        self.dbenv["record"].hide(names, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="putrecordvalues")
    @ol('names')
    def record_update(self, names, update, ctx=None, txn=None):
        """Convenience method to update Records.

        Examples:

        >>> db.record.update([0,136], {'performed_by':'ian'})
        [<Record 0, folder>, <Record 136, group>]

        >>> db.record.update([0,136, 137], {'performed_by':'ian'}, filt=False)
        SecurityError

        :param names: Record name(s)
        :param update: Update Records with this dictionary
        :return: Updated Record(s)
        :exception KeyError:
        :exception SecurityError:
        :exception ValidationError:
        """
        return self._mapput('record', names, 'update', ctx, txn, update)


    @publicmethod(compat="validaterecord")
    @ol('items')
    def record_validate(self, items, ctx=None, txn=None):
        """Check that a record will validate before committing.

        Examples:

        >>> db.record.validate([{'rectype':'folder', 'name_folder':'Test folder'}, {'rectype':'folder', 'name_folder':'Another folder'}])
        [<Record None, folder>, <Record None, folder>]

        >>> db.record.validate([<Record 499177, folder>, <Record 499178, folder>])
        [<Record 499177, folder>, <Record 499178, folder>]

        >>> db.record.validate({'rectype':'folder', 'performed_by':'unknown_user'})
        ValidationError

        >>> db.record.validate({'name':136, 'name_folder':'No permission to edit..'})
        SecurityError

        >>> db.record.validate({'name':12345, 'name_folder':'Unknown record'})
        KeyError

        :param items: Record(s)
        :return: Validated Record(s)
        :exception KeyError:
        :exception SecurityError:
        :exception ValidationError:
        """
        return self.dbenv["record"].validate(items, ctx=ctx, txn=txn)


    # These map to the normal Record methods
    @publicmethod(write=True, compat="addpermission")
    @ol('names')
    def record_adduser(self, names, users, level=0, ctx=None, txn=None):
        """Add users to a Record's permissions.

        >>> db.record.adduser(0, 'ian')
        <Record 0, folder>

        >>> db.record.adduser([0, 136], ['ian', 'steve'])
        [<Record 0, folder>, <Record 136, group>]

        >>> db.record.adduser([0, 136], ['ian', 'steve'], filt=False)
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


    @publicmethod(write=True, compat="removepermission")
    @ol('names')
    def record_removeuser(self, names, users, ctx=None, txn=None):
        """Remove users from a Record's permissions.

        Examples:

        >>> db.record.removeuser(0, 'ian')
        <Record 0, folder>

        >>> db.record.removeuser([0, 136], ['ian', 'steve'])
        [<Record 0, folder>, <Record 136, group>]

        >>> db.record.removeuser([0, 136], ['ian', 'steve'], filt=False)
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


    @publicmethod(write=True, compat="addgroup")
    @ol('names')
    def record_addgroup(self, names, groups, ctx=None, txn=None):
        """Add groups to a Record's permissions.

        Examples:

        >>> db.record.addgroup(0, 'authenticated')
        <Record 0, folder>

        >>> db.record.addgroup([0, 136], 'authenticated')
        [<Record 0, folder>, <Record 136, group>]

        >>> db.record.addgroup([0, 136], ['anon', 'authenticated'])
        [<Record 0, folder>, <Record 136, group>]

        >>> db.record.addgroup([0, 136], 'authenticated', filt=False)
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


    @publicmethod(write=True, compat="removegroup")
    @ol('names')
    def record_removegroup(self, names, groups, ctx=None, txn=None):
        """Remove groups from a Record's permissions.

        Examples:

        >>> db.user.removegroup(0, 'authenticated')
        <Record 0, folder>

        >>> db.user.removegroup([0, 136], 'authenticated')
        [<Record 0, folder>, <Record 136, group>]

        >>> db.user.removegroup([0, 136], ['anon', 'authenticated'])
        [<Record 0, folder>, <Record 136, group>]

        >>> db.user.removegroup([0, 136], 'authenticated', filt=False)
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
    @publicmethod(write=True, compat="setpermissions")
    @ol('names')
    def record_setpermissionscompat(self, names, addumask=None, addgroups=None, removeusers=None, removegroups=None, recurse=None, overwrite_users=False, overwrite_groups=False, filt=True, ctx=None, txn=None):
        """Update a Record's permissions.

        This method is mostly for convenience and backwards compatibility.

        Examples:

        >>> db.record.setpermissionscompat(names=[137, 138], addumask=[['ian'], [], [], []])

        >>> db.record.setpermissionscompat(names=[137], recurse=-1, addumask=[['ian', 'steve'], [], [], ['wah']])

        >>> db.record.setpermissionscompat(names=[137], recurse=-1, removegroups=['anon'], addgroups=['authenticated])

        >>> db.record.setpermissionscompat(names=[137], recurse=-1, addgroups=['authenticated'], overwrite_groups=True)

        >>> db.record.setpermissionscompat(names=[137], recurse=-1, addgroups=['authenticated'], overwrite_groups=True, filt=False)
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
        recs = self.dbenv["record"].cgets(names, ctx=ctx, txn=txn)
        crecs = []

        for rec in recs:
            # Get the record and children
            children = [rec]
            if recurse:
                c = self.dbenv["record"].rel([rec.name], recurse=recurse, ctx=ctx, txn=txn).get(rec.name, set())
                c = self.dbenv["record"].cgets(c, ctx=ctx, txn=txn)
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

        return self.dbenv["record"].cputs(crecs, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="addcomment")
    @ol('names')
    def record_addcomment(self, names, comment, filt=True, ctx=None, txn=None):
        """Add comment to a record.

        Requires comment permissions on that Record.

        Examples:

        >>> db.record.addcomment(136, 'Test comment')
        <Record 136, group>

        >>> db.record.addcomment(137, 'No comment permissions!?')
        SecurityError

        >>> db.record.addcomment(12345, 'Record does not exist')
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


    @publicmethod(compat="findorphans")
    def record_findorphans(self, names, root=0, keytype='record', ctx=None, txn=None):
        """Find orphaned items that would occur if names were hidden.
        @param name Return orphans that would result from deletion of these items
        @return Orphaned items
        """

        names = set(names)

        children = self.rel_childrentree(names, recurse=-1, ctx=ctx, txn=txn)
        allchildren = set()
        allchildren |= names
        for k,v in children.items():
            allchildren.add(k)
            allchildren |= v

        parents = self.rel_tree(allchildren, rel="parents", ctx=ctx, txn=txn)

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
        
        
    @publicmethod(compat="getcomments")
    @ol('names', output=False)
    def record_findcomments(self, names, filt=True, ctx=None, txn=None):
        """Get comments from Records.

        Note: This method always returns a list of items, even if only one record
            is specified, or only one comment is found.

        Examples:

        >>> db.record.findcomments(1)
        [[1, u'root', u'2010/07/19 14:43:03', u'Record marked for deletion and unlinked from parents: 270940']]

        >>> db.record.findcomments([1, 138])
        [[1, u'root', u'2010/07/19 14:43:03', u'Record marked...'], [138, u'ianrees', u'2011/10/01 02:28:51', u'New comment']]

        :param names: Record name(s)
        :keyword filt: Ignore failures
        :return: A list of comments, with the Record ID as the first item@[[record name, username, time, comment], ...]
        :exception KeyError:
        :exception SecurityError:
        """
        recs = self.dbenv["record"].cgets(names, filt=filt, ctx=ctx, txn=txn)

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
        
        
    @publicmethod(compat="getindexbyrectype")
    @ol('names', output=False)
    def record_findbyrectype(self, names, ctx=None, txn=None):
        """Get Record names by RecordDef.

        Note: Not currently filtered for permissions. This is not
        considered sensitive information.

        Examples:

        >>> db.record.findbyrectype('ccd')
        set([4180, 4513, 4514, ...])

        >>> db.record.findbyrectype('image_capture*')
        set([141, 142, 4180, ...])

        >>> db.record.findbyrectype(['scan','micrograph'])
        set([141, 142, 262153, ...])

        :param names: RecordDef name(s)
        :keyword filt: Ignore failures
        :return: Set of Record names
        :exception KeyError: No such RecordDef
        :exception SecurityError: Unable to access RecordDef
        """
        rds = self.dbenv["recorddef"].cgets(names, ctx=ctx, txn=txn)
        ind = self.dbenv["record"].getindex("rectype", txn=txn)
        ret = set()
        for i in rds:
            ret |= ind.get(i.name, txn=txn)
        return ret


    @publicmethod(compat="findvalue")
    def record_findbyvalue(self, param, query='', choices=True, count=100, ctx=None, txn=None):
        """Find values for a parameter.

        This is mostly used for interactive UI elements: e.g. combobox.
        More detailed results can be returned by using db.query directly.

        Examples:

        >>> db.record.findbyvalue('name_pi')
        [['wah', 124], ['steve', 89], ['ian', 43]], ...]

        >>> db.record.findbyvalue('ccd_id', limit=2)
        [['Gatan 4k', 182845], ['Gatan 10k', 48181]]

        >>> db.record.findbyvalue('tem_magnification', choices=True, limit=10)
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
        pd = self.dbenv["paramdef"].cget(param, ctx=ctx, txn=txn)
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


    @publicmethod(compat="groupbyrectype")
    @ol('names')
    def record_groupbyrectype(self, names, filt=True, ctx=None, txn=None):
        """Group Record(s) by RecordDef.

        Examples:

        >>> db.record.groupbyrectype([136,137,138])
        {u'project': set([137]), u'subproject': set([138]), u'group': set([136])}

        >>> db.record.groupbyrectype([<Record instance 1>, <Record instance 2>])
        {u'all_microscopes': set([1]), u'folder': set([2])}

        :param names: Record name(s) or Record(s)
        :keyword filt: Ignore failures
        :return: Dictionary of Record names by RecordDef
        :exception KeyError:
        :exception SecurityError:
        """
        return self.dbenv["record"].groupbyrectype(names, ctx=ctx, txn=txn)
                

    @publicmethod(compat="renderview")
    @ol('names')
    def record_render(self, names, viewname='recname', viewdef=None, edit=False, markup=True, table=False, mode=None, vtm=None, ctx=None, txn=None):
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

        The special view 'kv' will returned a markup=True result with each
        record parameter/value pair rendered as a two-column HTML table.

        Examples:

        >>> db.record.render([0, 136, 137])
        {0: u'EMEN2', 136: u'NCMI', 137: u'A Project'}

        >>> db.record.render([0, 136], viewname="mainview")
        {0: u'<p>Folder: EMEN2</p>...', 136: u'<h1><span class="e2-paramdef">Group</span>: NCMI</h1>...'}

        >>> db.record.render([0, 136], viewdef="$$creator $$creationtime")
        {0: u'<p><a href="/user/root">Admin</a> 2007/07/23 10:30:22</p>', 136: u'<p><a href="/user/ian">Rees, Ian</a> 2008/07/05</p>'}

        >>> db.record.render(0, viewname="defaultview", edit=True, markup=True)
        u'<p>Folder: <span class="e2-edit" data-name="0" data-param="name_folder">EMEN2</span>...'

        >>> db.record.render([0], viewname="tabularview", table=True, markup=True)
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
        #     edit = "auto"

        # Regular expression for parsing views
        regex = VIEW_REGEX

        # VartypeManager manages the rendering methods
        vtm = vtm or emen2.db.datatypes.VartypeManager(db=ctx.db)

        # We'll be working with a list of names
        names, recs, newrecs, other = listops.typepartition(names, basestring, emen2.db.dataobject.BaseDBObject, dict)
        names.extend(other)
        recs.extend(self.dbenv["record"].cgets(names, ctx=ctx, txn=txn))

        for newrec in newrecs:
            rec = self.dbenv["record"].new(name=None, rectype=newrec.get('rectype'), ctx=ctx, txn=txn)
            rec.update(newrec)
            recs.append(rec)

        # Get and pre-process views
        groupviews = {}
        recdefs = listops.dictbykey(self.dbenv["recorddef"].cgets(set([rec.rectype for rec in recs]), ctx=ctx, txn=txn), 'name')

        if viewdef:
            if markup and markdown:
                viewdef = markdown.markdown(viewdef, ['tables'])
            groupviews[None] = viewdef
        elif viewname == "kv":
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

        pds = listops.dictbykey(self.dbenv["paramdef"].cgets(pds, ctx=ctx, txn=txn), 'name')

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
            elif viewname == "kv":
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

        if table:
            ret["headers"] = headers

        return ret                


    @publicmethod(compat="renderchildtree")
    def record_renderchildren(self, name, recurse=3, rectype=None, ctx=None, txn=None):
        """(Deprecated) Convenience method used by some clients to render a bunch of
        records and simple relationships.

        Examples:

        >>> db.record.renderchildren(0, recurse=1, rectype=["group"])
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

        c_all = self.dbenv["record"].rel([name], recurse=recurse, tree=True, ctx=ctx, txn=txn)
        c_rectype = self.dbenv["record"].rel([name], recurse=recurse, rectype=rectype, ctx=ctx, txn=txn).get(name, set())

        endpoints = find_endpoints(c_all) - c_rectype
        while endpoints:
            for k,v in c_all.items():
                c_all[k] -= endpoints
            endpoints = find_endpoints(c_all) - c_rectype

        rendered = self.record_render(listops.flatten(c_all), ctx=ctx, txn=txn)

        c_all = listops.filter_dict_zero(c_all)

        return rendered, c_all



    ##### Binaries #####

    @publicmethod(compat="getbinary")
    @ol('names')
    def binary_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["binary"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod()
    def binary_new(self, ctx=None, txn=None):
        return self.dbenv["binary"].new(name=None, ctx=ctx, txn=txn)


    @publicmethod(write=True, compat="putbinary")
    @ol('items')
    def binary_put(self, items, ctx=None, txn=None):
        """Add or update a Binary (file attachment).

        For new items, data must be supplied using with either
        bdo.get('filedata') or bdo.get('fileobj').

        The contents of a Binary cannot be changed after uploading. The file
        size and md5 checksum will be calculated as the file is written to
        binary storage. Any attempt to change the contents raise a
        SecurityError. Not even admin users may override this.

        Examples:

        >>> db.binary.put({filename='hello.txt', filedata='Hello, world', record=0})
        <Binary bdo:2011101000000>

        >>> db.binary.put({'name':'bdo:2011101000000', 'filename':'newfilename.txt'})
        <Binary bdo:2011101000000>

        >>> db.binary.put({'name':'bdo:2011101000000', 'filedata':'Goodbye'})
        SecurityError

        :param item: Binary
        :exception SecurityError:
        :exception ValidationError:
        """
        bdos = []
        actions = []
        for bdo in items:
            newfile = False
            if not bdo.get('name'):
                handler = bdo
                bdo = self.dbenv["binary"].new(filename=handler.get('filename'), ctx=ctx, txn=txn)
                newfile = bdo.writetmp(filedata=handler.get('filedata', None), fileobj=handler.get('fileobj', None))

            bdo = self.dbenv["binary"].cput(bdo, ctx=ctx, txn=txn)
            bdos.append(bdo)

            if newfile:
                actions.append([bdo, newfile, bdo.filepath])
            
        # Rename the file at the end of the txn.
        for bdo, newfile, filepath in actions:
            self.dbenv.txncb(txn, 'rename', [newfile, filepath])
            self.dbenv.txncb(txn, 'thumbnail', [bdo])
            
        return bdos


    @publicmethod()
    def binary_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["binary"].names(names=names, ctx=ctx, txn=txn)


    # Warning: This can be SLOW!
    @publicmethod(compat="findbinary")
    def binary_find(self, query=None, record=None, count=100, ctx=None, txn=None, **kwargs):
        """Find a binary by filename.

        Keywords can be combined.

        Examples:

        >>> db.binary.find(filename='dm3')
        [<Binary 2011... test.dm3.gz>, <Binary 2011... test2.dm3.gz>]

        >>> db.binary.find(record=136)
        [<Binary 2011... presentation.ppt>, <Binary 2011... retreat_photo.jpg>, ...]

        :keyword query: Contained in any item below
        :keyword name: ... Binary name
        :keyword filename: ... filename
        :keyword record: Referenced in Record name(s)
        :keyword count: Limit number of results
        :keyword boolmode: AND / OR for each search constraint (default: AND)
        :return: Binaries
        """
        # @keyword min_filesize
        # @keyword max_filesize
        def searchfilenames(filename, txn):
            ind = self.dbenv["binary"].getindex('filename', txn=txn)
            ret = set()
            keys = (f for f in ind.keys(txn=txn) if filename in f)
            for key in keys:
                ret |= ind.get(key, txn=txn)
            return ret

        rets = []
        # This would probably work better if we used the sequencedb keys as a first step
        if query or kwargs.get('name'):
            names = self.dbenv["binary"].names(ctx=ctx, txn=txn)

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
        ret = self.dbenv["binary"].cgets(allret, ctx=ctx, txn=txn)
        if count:
            return ret[:count]
        return ret
        
        
    @publicmethod(write=True, compat="binaryaddreference")
    def binary_addreference(self, record, param, name, ctx=None, txn=None):
        bdo = self.dbenv["binary"].cget(name, ctx=ctx, txn=txn)        
        rec = self.dbenv["record"].cget(record, ctx=ctx, txn=txn)
        pd = self.dbenv["paramdef"].cget(param, ctx=ctx, txn=txn)

        if pd.vartype != 'binary':
            raise KeyError, "ParamDef %s does not accept binary references"%pd.name

        if pd.iter:
            v = rec.get(pd.name) or []
            v.append(bdo.name)
        else:
            v = bdo.name

        rec[pd.name] = v
        bdo.record = rec.name

        # Commit the record
        self.dbenv["record"].cput(rec, ctx=ctx, txn=txn)
        self.dbenv["binary"].cput(bdo, ctx=ctx, txn=txn)
    

    @publicmethod()
    @ol('names')    
    def binary_extract(self, names, ctx=None, txn=None):
        # todo: header extraction.
        pass


        
    ##### Temporary binaries #####

    @publicmethod()
    @ol('names')
    def upload_get(self, names, filt=True, ctx=None, txn=None):
        return self.dbenv["upload"].cgets(names, filt=filt, ctx=ctx, txn=txn)


    @publicmethod()
    def upload_new(self, ctx=None, txn=None):
        return self.dbenv["upload"].new(name=None, ctx=ctx, txn=txn)
    
    
    @publicmethod(write=True)
    @ol('items')
    def upload_put(self, items, ctx=None, txn=None):
        tmpdir = emen2.db.config.get('paths.tmp')        
        bdos = []
        rename = []
        for bdo in items:
            newfile = False
            if not bdo.get('name'):
                handler = bdo
                bdo = self.dbenv["upload"].new(filename=handler.get('filename'), ctx=ctx, txn=txn)
                newfile = bdo.writetmp(filedata=handler.get('filedata', None), fileobj=handler.get('fileobj', None), basepath=tmpdir)

            bdo = self.dbenv["upload"].cput(bdo, ctx=ctx, txn=txn)
            bdos.append(bdo)

            if newfile:
                dest = os.path.join(tmpdir, bdo.name)
                rename.append([newfile, dest])
            
        # Rename the file at the end of the txn.
        for newfile, filepath in rename:
            self.dbenv.txncb(txn, 'rename', [newfile, filepath])

        return bdos
        
        
    @publicmethod()
    def upload_names(self, names=None, ctx=None, txn=None):
        return self.dbenv["upload"].names(names=names, ctx=ctx, txn=txn)


    @publicmethod()
    def upload_find(self, **kwargs):
        raise NotImplementedError

    ##### Workflow #####

    # Todo: reimplement workflows.




__version__ = "$Revision: 1.801 $".split(":")[1][:-1].strip()
