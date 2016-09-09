# $Id: btrees.py,v 1.167 2013/06/20 23:37:06 irees Exp $
"""BerkeleyDB Driver."""

import collections
import copy
import functools
import os
import shutil
import time
import traceback
import cPickle as pickle

# Berkeley DB
# Note: the 'bsddb' module is not sufficient.
import bsddb3

# EMEN2 imports
import emen2.db.config
import emen2.db.log
import emen2.db.query
import emen2.util.listops
from emen2.db.exceptions import *

# EMEN2 DBObjects
import emen2.db.dataobject
import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group

Record = emen2.db.record.Record
Binary = emen2.db.binary.Binary
ParamDef = emen2.db.paramdef.ParamDef
RecordDef = emen2.db.recorddef.RecordDef
User = emen2.db.user.User
NewUser = emen2.db.user.NewUser
Group = emen2.db.group.Group
Context = emen2.db.context.Context

try:
    import emen2.db.bulk
    bulk = emen2.db.bulk
    # emen2.db.log.info("Note: using EMEN2-BerkeleyDB bulk access module")
except ImportError, inst:
    bulk = None


# ian: todo: move this to EMEN2DBEnv
DB_CONFIG = """\
# Don't touch these
set_data_dir data
set_lg_dir journal
set_lg_regionmax 1048576
set_lg_max 8388608
set_lg_bsize 2097152
"""


##### EMEN2 Database Environment #####

class EMEN2DBEnv(object):
    def __init__(self, path=None, snapshot=False):
        """BerkeleyDB Database Environment.
        
        :keyword path: Directory containing environment.
        :keyword snapshot: Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
        """
        
        # Database environment directory
        self.path = path
        self.snapshot = snapshot or (not emen2.db.config.get('params.snapshot'))
        self.cachesize = emen2.db.config.get('bdb.cachesize') * 1024 * 1024l

        # Make sure the data and journal directories exists.
        paths = [
            os.path.join(self.path, 'data'),
            os.path.join(self.path, 'journal')
        ]
        for p in paths:
            if not os.path.exists(p):
                os.makedirs(p)

        # Make sure the DB_CONFIG is present.
        configpath = os.path.join(self.path, "DB_CONFIG")
        exists = os.path.exists(configpath)
        if not exists:
            emen2.db.log.debug("BDB: Copying default DB_CONFIG file: %s"%configpath)
            f = open(configpath, "w")
            f.write(DB_CONFIG)
            f.close()

        # Databases
        self.keytypes =  {}

        # Pre- and post-commit actions.
        # These are used for things like renaming files during the commit phase.
        # TODO: The details of this are highly likely to change,
        #     or be moved to a different place.
        self._txncbs = collections.defaultdict(list)

        # Open DBEnv and main tables.
        self.dbenv = self.open()
        self.init()
        
    def _load_json(self, infile, keytypes=None, ctx=None, txn=None):
        """Load a JSON file containing DBOs."""
        # Create a special root context to load the items
        loader = emen2.db.load.BaseLoader(infile=infile)
        keytypes = keytypes or ['paramdef', 'user', 'group', 'recorddef', 'binary', 'record']
        for keytype in keytypes:
            for item in loader.loadfile(keytype=keytype):
                emen2.db.log.debug("BDB: Load %s %s"%(keytype, item.get('name')))
                i = self[keytype].dataclass(ctx=ctx)
                i._load(item)
                self[keytype]._put_data(i.name, i, txn=txn)

    def create(self):
        """Load database parameters and protocols from JSON."""
        # Start txn
        ctx = emen2.db.context.SpecialRootContext()
        txn = self.newtxn(write=True)
        keytypes = ['paramdef', 'recorddef']
        
        # Load core ParamDefs... Items defined in base.json are required.
        infile = emen2.db.config.get_filename('emen2', 'db/base.json')
        self._load_json(infile, keytypes=keytypes, ctx=ctx, txn=txn)

        # Load DBOs from extensions.
        emen2.db.config.load_jsons(cb=self._load_json, keytypes=keytypes, ctx=ctx, txn=txn)

        # Commit txn
        self.txncommit(txn=txn)
        
        # self._load_json does not update indexes; do this manually.
        self['paramdef'].rebuild_indexes(ctx=ctx, txn=txn)
        self['recorddef'].rebuild_indexes(ctx=ctx, txn=txn)

    
    def open(self):
        """Open the Database Environment."""
        emen2.db.log.info("BDB: Opening database environment: %s"%self.path)
        dbenv = bsddb3.db.DBEnv()

        if self.snapshot:
            dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
        
        txncount = (self.cachesize / 4096) * 2
        if txncount > 1024*128:
            txncount = 1024*128
            
        dbenv.set_cachesize(0, self.cachesize)
        dbenv.set_tx_max(txncount)
        dbenv.set_lk_max_locks(300000)
        dbenv.set_lk_max_lockers(300000)
        dbenv.set_lk_max_objects(300000)

        flags = 0
        flags |= bsddb3.db.DB_CREATE
        flags |= bsddb3.db.DB_INIT_MPOOL
        flags |= bsddb3.db.DB_INIT_TXN
        flags |= bsddb3.db.DB_INIT_LOCK
        flags |= bsddb3.db.DB_INIT_LOG
        flags |= bsddb3.db.DB_THREAD
        dbenv.open(self.path, flags)
        return dbenv

    def init(self):
        # Authentication. These are not public.
        self._context = CollectionDB(dataclass=Context, dbenv=self)
        # These are public dbs.
        self.keytypes['paramdef']  = CollectionDB(dataclass=ParamDef, dbenv=self)
        self.keytypes['recorddef'] = CollectionDB(dataclass=RecordDef, dbenv=self)
        self.keytypes['group']     = CollectionDB(dataclass=Group, dbenv=self)
        self.keytypes['record']    = RecordDB(dataclass=Record, dbenv=self)
        self.keytypes['user']      = UserDB(dataclass=User, dbenv=self)
        self.keytypes['newuser']   = NewUserDB(dataclass=NewUser, dbenv=self)
        self.keytypes['binary']    = BinaryDB(dataclass=Binary, dbenv=self)

    # ian: todo: make this nicer.
    def close(self):
        """Close the Database Environment"""
        for k,v in self.keytypes.items():
            v.close()
        self.dbenv.close()

    def __getitem__(self, key, default=None):
        """Pass dictionary gets to self.keytypes."""
        return self.keytypes.get(key, default)

    ##### Transaction management #####

    def newtxn(self, write=False):
        """Start a new transaction.
        
        :keyword write: Transaction will be likely to write data; turns off Berkeley DB Snapshot
        :return: New transaction
        """
        flags = bsddb3.db.DB_TXN_SNAPSHOT
        if write:
            flags = 0

        txn = self.dbenv.txn_begin(flags=flags)
        emen2.db.log.debug("TXN: start: %s flags %s"%(txn, flags))
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
        emen2.db.log.debug("TXN: abort: %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'abort', 'before')
        txn.abort()
        self._txncb(txnid, 'abort', 'after')
        self._txncbs.pop(txnid, None)

    def txncommit(self, txn):
        """Commit a transaction.

        :param txn: An existing open transaction
        :exception: KeyError if transaction was not found
        """
        emen2.db.log.debug("TXN: commit: %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'commit', 'before')
        txn.commit()
        self._txncb(txnid, 'commit', 'after')
        self._txncbs.pop(txnid, None)

    ##### Pre- and post-commit hooks. #####

    def txncb(self, txn, action, args=None, kwargs=None, condition='commit', when='before'):
        # Add a pre- or post-commit hook.
        if when not in ['before', 'after']:
            raise ValueError, "Transaction callback 'when' must be before or after"
        if condition not in ['commit', 'abort']:
            raise ValueError, "Transaction callback 'condition' must be commit or abort"
        item = [condition, when, action, args or [], kwargs or {}]
        self._txncbs[txn.id()].append(item)

    # This is still being developed. Do not touch.
    def _txncb(self, txnid, condition, when):
        # Note: this takes txnid, not a txn. This
        # is because txn.id() is null after commit.
        actions = self._txncbs.get(txnid, [])
        for c, w, action, args, kwargs in actions:
            if w == when and c == condition:
                if action == 'rename':
                    self._txncb_rename(*args, **kwargs)
                elif action == 'email':
                    self._txncb_email(*args, **kwargs)
                elif action == 'thumbnail':
                    self._txncb_thumbnail(*args, **kwargs)
    
    def _txncb_rename(self, source, dest):
        emen2.db.log.info("TXN CB: Renaming file: %s -> %s"%(source, dest))
        try:
            shutil.move(source, dest)
        except Exception, e:
            emen2.db.log.error("TXN CB: Couldn't rename file %s -> %s"%(source, dest))

    def _txncb_email(self, *args, **kwargs):
        try:
            emen2.db.database.sendmail(*args, **kwargs)
        except Exception, e:
            emen2.db.log.error("TXN CB: Couldn't send email: %s"%e)
            
    def _txncb_thumbnail(self, bdo):
        try:
            emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
        except Exception, e:
            emen2.db.log.error("TXN CB: Couldn't start thumbnail builder")
    
    ##### Log archive #####

    def checkpoint(self, txn=None):
        """Checkpoint the database environment."""
        return self.dbenv.txn_checkpoint()

    def journal_archive(self, remove=True, checkpoint=True, txn=None):
        """Archive completed log files.

        :keyword remove: Remove the log files after moving them to the backup location
        :keyword checkpoint: Run a checkpoint first; this will allow more files to be archived
        """
        outpath = emen2.db.config.get('paths.journal_archive')

        if checkpoint:
            emen2.db.log.info("BDB: Log Archive: Checkpoint")
            self.dbenv.txn_checkpoint()

        archivefiles = self.dbenv.journal_archive(bsddb3.db.DB_ARCH_ABS)

        emen2.db.log.info("BDB: Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

        if not os.access(outpath, os.F_OK):
            os.makedirs(outpath)

        outpaths = []
        for archivefile in archivefiles:
            dest = os.path.join(outpath, os.path.basename(archivefile))
            emen2.db.log.info('BDB: Log Archive: %s -> %s'%(archivefile, dest))
            shutil.move(archivefile, dest)
            outpaths.append(dest)

        return outpaths     

    ##### Rebuild indexes #####
    
    def rebuild_indexes(self, ctx=None, txn=None):
        for k,v in self.keytypes.items():
            v.rebuild_indexes(ctx=ctx, txn=txn)
        

# Berkeley DB wrapper classes
class BaseDB(object):
    """BerkeleyDB base class.
        
    :attr filename: Filename of BDB on disk
    :attr dbenv: EMEN2 Database Environment
    :attr bdb: Berkeley DB instance
    :attr DBOPENFLAGS: Berkeley DB flags for opening database
    :attr DBSETFLAGS: Additional flags
    """

    def __init__(self, filename, keyformat='str', dataformat='str', dataclass=None, dbenv=None, extension='bdb'):
        """Create and open the DB.
        
        :param filename: Base filename to use
        :keyword dbenv: Database environment
        """
        # Filename
        self.filename = filename
        self.extension = extension
        
        # EMEN2DBEnv
        self.dbenv = dbenv

        # What are we storing?
        # This sets formatters and types for keys and data.
        self._setkeyformat(keyformat)
        self._setdataformat(dataformat, dataclass)

        # BDB handle and open flags.
        self.bdb = None
        self.DBOPENFLAGS = bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE
        self.DBSETFLAGS = []

        # Init and open.
        self.init()
        self.open()

    def init(self):
        """Subclass init hook."""
        pass

    ##### DB methods #####

    def open(self):
        """Open the DB. This uses an implicit open transaction."""
        if self.bdb:
            raise Exception, "DB already open"

        # Create the DB handle and set flags
        self.bdb = bsddb3.db.DB(self.dbenv.dbenv)

        # Set DB flags, e.g. duplicate keys allowed
        for flag in self.DBSETFLAGS:
            self.bdb.set_flags(flag)

        # Open the DB with the correct flags.
        emen2.db.log.debug("BDB: %s open"%self.filename)
        fn = '%s.%s'%(self.filename, self.extension)
        self.bdb.open(filename=fn, dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)

    def close(self):
        """Close the DB."""
        emen2.db.log.debug("BDB: %s close"%self.filename)
        self.bdb.close()
        self.bdb = None

    # Dangerous!
    def truncate(self, txn=None, flags=0):
        """Truncate BDB (e.g. 'drop table'). Transaction required.
        :keyword txn: Transaction
        """
        # todo: Do more checking before performing a dangerous operation.
        emen2.db.log.debug("BDB: %s truncate"%self.filename)
        self.bdb.truncate(txn=txn)
    
    ##### load/dump methods for keys and data #####

    # DO NOT TOUCH THIS!!!!
    def _cfunc_numeric(self, k1, k2):
        # Numeric comparison function, for key sorting.
        if not k1:
            k1 = 0
        else:
            k1 = self.keyload(k1)

        if not k2:
            k2 = 0
        else:
            k2 = self.keyload(k2)
        return cmp(k1, k2)

    def _setkeyformat(self, keyformat):
        # Set the DB key type. This will bind the correct
        # keyclass, keydump, keyload methods.
        if keyformat == 'str':
            self.keyclass = unicode
            self.keydump = lambda x:unicode(x).encode('utf-8')
            self.keyload = lambda x:x.decode('utf-8')
        elif keyformat == 'int':
            self.keyclass = int
            self.keydump = str
            self.keyload = int
        elif keyformat == 'float':
            self.keyclass = float
            self.keydump = lambda x:pickle.dumps(x)
            self.keyload = lambda x:pickle.loads(x or 'N.')
        else:
            raise ValueError, "Invalid key format: %s. Supported: str, int, float"%keyformat
        self.keyformat = keyformat

    def _setdataformat(self, dataformat, dataclass=None):
        # Set the DB data type. This will bind the correct
        # dataclass attribute, and datadump and dataload methods.
        if dataclass:
            dataformat = 'pickle'
        if dataformat == 'str':
            # String dataformat; use UTF-8 encoded strings.
            self.dataclass = unicode
            self.datadump = lambda x:unicode(x).encode('utf-8')
            self.dataload = lambda x:x.decode('utf-8')
        elif dataformat == 'int':
            # Decimal dataformat, use str encoded ints.
            self.dataclass = int
            self.datadump = str
            self.dataload = int
        elif dataformat == 'float':
            # Float dataformat; these do not sort natively, so pickle them.
            self.dataclass = float
            self.datadump = lambda x:pickle.dumps(x)
            self.dataload = lambda x:pickle.loads(x or 'N.')
        elif dataformat == 'pickle':
            # This DB stores a DBO as a pickle.
            self.dataclass = dataclass
            self.datadump = lambda x:pickle.dumps(x)
            self.dataload = lambda x:pickle.loads(x or 'N.')
        else:
            # Unknown dataformat.
            raise Exception, "Invalid data format: %s. Supported: str, int, float, pickle"%dataformat
        self.dataformat = dataformat
    

class IndexDB(BaseDB):
    '''EMEN2DB optimized for indexes.

    Security is not checked here, so do not expose indexes directly to 
    untrusted clients. A user could query values they could not otherwise
    access.

    IndexDB uses the Berkeley DB mechanism for storing multiple values for a
    single key (DB_DUPSORT). The Berkeley DB API has a method for
    quickly reading these multiple values.

    This class is intended for use with an OPTIONAL C module, _bulk.so, that
    accelerates reading from the index. The Berkeley DB bulk reading mode
    is not fully implemented in the bsddb3 package; the C module does the bulk
    reading in a single function call, greatly speeding up performance, and
    returns the correct native Python type. The C module is totally optional
    and is transparent; the only change is read speed.

    Index references are added using addrefs() and removerefs(). These both
    take a single key, and a list of references to add or remove.

    Extends or overrides the following methods:
        init        Checks bulk mode
        get         Returns all values found.
        keys        Index keys
        items       Index items; (key, [value1, value2, ...])
        iteritems   Index iteritems

    Adds the following indexing methods:
        addrefs        Add (key, [values]) references to the index
        removerefs    Remove (key, [values]) references from the index
    '''

    def init(self):
        """Open DB with support for duplicate keys."""
        self.DBSETFLAGS = [bsddb3.db.DB_DUPSORT]
        self._setbulkmode(True)
        super(IndexDB, self).init()

    def _setbulkmode(self, bulkmode):
        # Use acceleration C module if available
        self._get_method = self._get_method_nonbulk
        if bulk:
            if bulkmode:
                self._get_method = emen2.db.bulk.get_dup_bulk
            else:
                self._get_method = emen2.db.bulk.get_dup_notbulk

    def _get_method_nonbulk(self, cursor, key, dt, flags=0):
        # Get without C module. Uses an already open cursor.
        n = cursor.set(key)
        r = set() #[]
        m = cursor.next_dup
        while n:
            r.add(n[1])
            n = m()
        return set(self.dataload(x) for x in r)

    # Default get method used by get()
    _get_method = _get_method_nonbulk

    def get(self, key, default=None, cursor=None, txn=None, flags=0):
        """Return all the values for this key.

        Can be passed an already open cursor, or open one if necessary.
        Requires a transaction. The real get method is _get_method, which
        is set during init based on availability of the C module.

        :param key: Key
        :keyword default: Default value if key not found
        :keyword cursor: Use this cursor
        :keyword txn: Transaction
        :return: Values for key
        """
        emen2.db.log.debug("BDB: %s get: %s"%(self.filename, key))        
        if cursor:
            r = self._get_method(cursor, self.keydump(key), self.dataformat)
        else:
            cursor = self.bdb.cursor(txn=txn)
            r = self._get_method(cursor, self.keydump(key), self.dataformat)
            cursor.close()
        if bulk and self.dataformat == 'pickle':
            r = set(self.dataload(x) for x in r)
        return r

    # ian: todo: allow min/max
    def keys(self, minkey=None, maxkey=None, txn=None, flags=0):
        """Keys. Transaction required.

        :keyword txn: Transaction
        """
        keys = set(map(self.keyload, self.bdb.keys(txn)))
        return list(keys)

    # ian: todo: allow min/max
    def items(self, minkey=None, maxkey=None, txn=None, flags=0):
        """Accelerated items. Transaction required.

        :keyword txn: Transaction
        """
        ret = []
        cursor = self.bdb.cursor(txn=txn)
        pair = cursor.first()
        while pair != None:
            data = self._get_method(cursor, pair[0], self.dataformat)
            if bulk and self.dataformat == "pickle":
                data = set(map(self.dataload, data))
            ret.append((self.keyload(pair[0]), data))
            pair = cursor.next_nodup()
        cursor.close()
        return ret

    def iteritems(self, minkey=None, maxkey=None, txn=None, flags=0):
        """Iteritems. Transaction required.

        :keyword minkey: Minimum key
        :keyword maxkey: Maximum key
        :keyword txn: Transaction
        :yield: (key, value)
        """
        ret = []
        cursor = self.bdb.cursor(txn=txn)
        pair = cursor.first()

        # Start a minimum key.
        # This only works well if the keys are sorted properly.
        if minkey is not None:
            pair = cursor.set_range(self.keydump(minkey))
        while pair != None:
            data = self._get_method(cursor, pair[0], self.dataformat)
            k = self.keyload(pair[0])
            if bulk and self.dataformat == "pickle":
                data = set(map(self.dataload, data))
            yield (k, data)
            pair = cursor.next_nodup()
            if maxkey is not None and k > maxkey:
                pair = None
        cursor.close()

    ##### Write Methods #####

    def removerefs(self, key, items, txn=None):
        '''Remove references.

        :param key: Key
        :param items: References to remove
        :keyword txn: Transaction
        :return: Keys that no longer have any references
        '''
        if not items: return []
        emen2.db.log.debug("BDB: %s removerefs: %s -> %s"%(self.filename, key, items))
        delindexitems = []

        try:
            key = self.keyclass(key)
            dkey = self.keydump(key)
            ditems = [self.datadump(self.dataclass(i)) for i in items]
        except:
            emen2.db.log.debug("BDB: Could not reindex due to encoding errors!!")
            return []

        cursor = self.bdb.cursor(txn=txn)
        
        for ditem in ditems:
            if cursor.set_both(dkey, ditem):
                cursor.delete()

        if not cursor.set(dkey):
            delindexitems.append(key)

        cursor.close()
        return delindexitems

    def addrefs(self, key, items, txn=None):
        """Add references.

        A list of keys that are new to this index are returned. This can be
        used to maintain other indexes.

        :param key: Key
        :param items: References to add
        :keyword txn: Transaction
        :return: Keys that are new to this index

        """
        if not items:
            return []
        emen2.db.log.debug("BDB: %s addrefs: %s -> %s"%(self.filename, key, items))
        addindexitems = []

        try:
            key = self.keyclass(key)
            dkey = self.keydump(key)
            ditems = [self.datadump(self.dataclass(i)) for i in items]
        except:
            emen2.db.log.debug("BDB: Could not reindex due to encoding errors!!")
            return []
        
        cursor = self.bdb.cursor(txn=txn)

        if not cursor.set(dkey):
            addindexitems.append(key)

        for ditem in ditems:
            try:
                cursor.put(dkey, ditem, flags=bsddb3.db.DB_KEYFIRST)
            except bsddb3.db.DBKeyExistError, e:
                pass

        cursor.close()

        return addindexitems



# Context-aware DB for Database Objects.
# These support a single DB and a single data class.
# Supports sequenced items.
class CollectionDB(BaseDB):
    '''Database for items supporting the DBO interface (mapping
    interface, setContext, writable, etc. See BaseDBObject.)

    You may consider terms collection, bucket, keytype, and table to be
    interchangeable.

    Most methods require a transaction. Additionally, because
    this class manages DBOs, most methods also require a Context.

    Extends the following methods:
        __init__         Opens DBs in a specific directory
        open             Also opens sequencedb
        close            Also cloes sequencdb and indexes

    And adds the following methods that require a context:
        new              New item
        get              Get a single item
        gets             Get items
        put              Put a single item
        puts             Put items
        filter           Context-aware keys
        query            Query
        validate         Validate an item
        exists           Check if an item exists already

    May be deprecated, since they're unbounded:
        keys
        values
        items

    Some internal methods:
        _get_data
        _put
        _puts
        _put_data
        _exists

    Sequence methods:
        _update_names    Update items with new names from sequence
        _key_generator
        _incr_sequence
        _get_max

    Index methods:
        getindex         Open an index
        _reindex         Calculate index updates
        _reindex_*       Write index updates
    
    Relationship methods:
        parents          Returns parents
        children         Returns children
        siblings         Item siblings
        rel              General relationship method
        pclink           Add a parent/child relationship
        pcunlink         Remove a parent/child relationship
        relink           Add and remove several relationships
    '''
    
    def __init__(self, *args, **kwargs):
        # Change the filename slightly
        dataclass = kwargs.get('dataclass')
        dbenv = kwargs.get('dbenv')
        self.keytype = (kwargs.get('keytype') or dataclass.__name__).lower()
        
        # Sequences
        self.sequencedb = None
        
        # Indexes
        self.indexes = {}
        self._truncate_index = False

        filename = os.path.join(self.keytype, self.keytype)
        d1 = os.path.join(dbenv.path, 'data', self.keytype)
        d2 = os.path.join(dbenv.path, 'data', self.keytype, 'index')
        for i in [d1, d2]:
            try: os.makedirs(i)
            except: pass  
        return super(CollectionDB, self).__init__(filename, *args, **kwargs)

    def open(self):
        """Open DB, and sequence."""
        super(CollectionDB, self).open()
        self.sequencedb = bsddb3.db.DB(self.dbenv.dbenv)
        self.sequencedb.open(os.path.join('%s.sequence.bdb'%self.filename), dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)

    def close(self):
        """Close DB, sequence, and indexes."""
        super(CollectionDB, self).close()
        self.sequencedb.close()
        self.sequencedb = None
        for k,v in self.indexes.items():
            if v:
                ind.close()
        self.indexes = {}

    ##### New items.. #####

    def new(self, *args, **kwargs):
        """Returns new DBO. Requires ctx and txn.

        All the method args and keywords will be passed to the constructor.

        :keyword txn: Transaction
        :return: New DBO
        :exception ExistingKeyError:
        
        """
        txn = kwargs.pop('txn', None) # Don't pass the txn..
        ctx = kwargs.get('ctx', None)
        kwargs['keytype'] = self.keytype
        inherit = kwargs.pop('inherit', [])
        item = self.dataclass(*args, **kwargs)

        for i in inherit:
            # Allow to raise an exception if does not exist or cannot read.
            i = self.get(i, filt=False, ctx=ctx, txn=txn)
            if i.get('permissions'):
                item.addumask(i.get('permissions'))
            if i.get('groups'):
                item.addgroup(i.get('groups'))
            item['parents'].add(i.name)

        # Acquire a write lock on this name.
        if self.exists(item.name, txn=txn, flags=bsddb3.db.DB_RMW):
            raise emen2.db.exceptions.ExistingKeyError, "%s already exists"%item.name

        return item

    ##### Exists #####
    
    def exists(self, key, ctx=None, txn=None, flags=0):
        """Check if a key exists."""
        # Names that are None or a negative int will be automatically assigned.
        # In this case, return immediately and don't acquire any locks.
        # Note: this method does not check permissions; you could use it to check
        #     if a key exists or not, even if you can't read the value.
        emen2.db.log.debug("BDB: %s exists: %s"%(self.filename, key))        
        if key < 0 or key is None:
            return False
        return self.bdb.exists(self.keydump(key), txn=txn, flags=flags)
        
    ##### Keys, values, items #####
    
    def filter(self, names=None, ctx=None, txn=None):
        """Filter a set of keys for read permission.

        :keyword names: Subset of items to check
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Set of keys that are accessible by the Context

        """
        if names is not None:
            if ctx.checkreadadmin():
                return names
            items = self.gets(names, ctx=ctx, txn=txn)
            return set([i.name for i in items])
        return set(self.keys(txn=txn))
    
    def keys(self, ctx=None, txn=None):
        emen2.db.log.warn("BDB: %s keys: Deprecated method!"%self.filename)
        return map(self.keyload, self.bdb.keys(txn))
    
    def items(self, ctx=None, txn=None):
        emen2.db.log.warn("BDB: %s items: Deprecated method!"%self.filename)
        ret = []
        for k,v in self.bdb.items(txn):
            i = self.dataload(v)
            i.setContext(ctx)
            ret.append((self.keyload(k), i))
        return ret
        
    def values(self, ctx=None, txn=None):
        raise NotImplementedError

    ##### Filtered context gets.. #####

    def get(self, key, filt=True, ctx=None, txn=None, flags=0):
        """See cgets(). This works the same, but for a single key."""
        r = self.gets([key], txn=txn, ctx=ctx, filt=filt, flags=flags)
        if not r:
            return None
        return r[0]

    def gets(self, keys, filt=True, ctx=None, txn=None, flags=0):
        """Get a list of items, with a Context. Requires ctx and txn.

        The filt keyword, if True, will ignore KeyError and SecurityError.
        Alternatively, it can be set to a list of Exception types to ignore.

        :param key: Items to get
        :keyword filt: Ignore KeyError, SecurityError
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: DBOs with bound Context
        :exception KeyError:
        :exception SecurityError:

        """
        if filt == True:
            filt = (emen2.db.exceptions.SecurityError, KeyError)

        ret = []
        for key in keys:
            try:
                d = self._get_data(key, txn=txn, flags=flags)
                d.setContext(ctx)
                ret.append(d)
            except filt, e:
                pass
        return ret
        
    def _get_data(self, key, txn=None, flags=0):
        emen2.db.log.debug("BDB: %s get: %s"%(self.filename, key))        
        kd = self.keydump(key)
        d = self.dataload(self.bdb.get(kd, txn=txn, flags=flags))
        if d:
            return d
        raise KeyError, "No such key %s"%(key)    

    def _get_data_items(self, txn=None, flags=0):
        # items() without ctx.
        for k,v in self.bdb.items(txn=txn, flags=flags):
            k = self.keyload(key)
            v = self.dataload(v)
            yield k,v

    ##### Write methods #####

    def validate(self, items, ctx=None, txn=None):
        return self.puts(items, commit=False, ctx=ctx, txn=txn)

    def put(self, item, commit=True, ctx=None, txn=None):
        """See puts(). This works the same, but for a single DBO."""
        ret = self.puts([item], commit=commit, ctx=ctx, txn=txn)
        if not ret:
            return None
        return ret[0]
        
    def puts(self, items, commit=True, ctx=None, txn=None):
        """Update DBOs. Requires ctx and txn.

        :param item: DBOs, or similar (e.g. dict)
        :keyword commit: Actually commit (e.g. for validation only)
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Updated DBOs
        :exception KeyError:
        :exception SecurityError:
        :exception ValidationError:

        """
        # Updated items
        crecs = []
        for updrec in items:
            name = updrec.get('name')
            
            # Get the existing item or create a new one.
            if self.exists(name, txn=txn, flags=bsddb3.db.DB_RMW):
                # Get the existing item.
                orec = self._get_data(name, txn=txn, flags=bsddb3.db.DB_RMW)
                # May raise a SecurityError if you can't read it.
                orec.setContext(ctx)
                orec.update(updrec)
            else:
                # Create a new item.
                orec = self.new(ctx=ctx, txn=txn, **updrec)

            # Update the item.
            orec.validate()
            crecs.append(orec)

        # If we just wanted to validate the changes, return before writing changes.
        if commit:
            return self._puts(crecs, ctx=ctx, txn=txn)
        return crecs
        
    def _put(self, item, ctx=None, txn=None):
        return self._puts([item], ctx=ctx, txn=txn)[0]

    def _puts(self, items, ctx=None, txn=None):
        # TODO: ctx used only for cache.
        # Assign names for new items.
        # This will also update any relationships to uncommitted records.
        self._update_names(items, txn=txn)

        # Now that names are assigned, calculate the index updates.
        ind = self._reindex(items, txn=txn)

        # Write the items "for real."
        for item in items:
            self._put_data(item.name, item, txn=txn)

        # Write index updates
        self._reindex_write(ind, ctx=ctx, txn=txn)
        emen2.db.log.debug("BDB: Committed %s items"%(len(items)))
        return items

    def _put_data(self, name, item, txn=None, flags=0):
        emen2.db.log.debug("BDB: %s put: %s"%(self.filename, item.name))        
        self.bdb.put(self.keydump(name), self.datadump(item), txn=txn, flags=flags)
    
    # def delete(self, name, ctx=None, txn=None, flags=0):
    #     emen2.db.log.debug("BDB: %s put: %s"%(self.filename, item.name))        
    #     self.bdb.delete(self.keydump(name), txn=txn, flags=flags)


    def query(self, c=None, mode='AND', subset=None, ctx=None, txn=None):
        """Return a Query Constraint Group.

        You will need to call constraint.run() to execute the query,
        and constraint.sort() to sort the values.
        """
        return emen2.db.query.Query(constraints=c, mode=mode, subset=subset, ctx=ctx, txn=txn, btree=self)

    ##### Changes to indexes #####
    
    def _reindex(self, items, reindex=False, txn=None):
        """Update indexes.

        The original items will be retrieved and compared to the updated
        items. A set of index changes will be calculated, and then handed off
        to the _reindex_* methods. In some cases, these will be overridden
        or extended to handle special indexes -- such as parent/child
        relationships in RelateDB.
        
        :param items: Updated DBOs
        :keyword reindex:
        :keyword ctx: Context
        :keyword txn: Transaction

        """
        # Updated indexes
        ind = collections.defaultdict(list)

        # Get changes as param:([name, newvalue, oldvalue], ...)
        for item in items:
            # Get the current record for comparison of updated values.
            # Use an empty dict for new records so all keys
            # will seen as new (or if reindexing)
            if item.isnew() or reindex:
                orec = {}
            else:
                orec = self._get_data(item.name, txn=txn) or {}

            for param in item.changedparams(orec):
                ind[param].append((item.name, item.get(param), orec.get(param)))

        # Return the index changes.
        return ind

    # .... the actual items need to be written ^^^ between these two vvv steps for relationships to be updated ....

    def _reindex_write(self, ind, ctx=None, txn=None):
        """(Internal) Write index updates."""
        # Parent/child relationships are a special case.
        # The other side of the relationship needs to be updated. 
        # Calculate the correct changes here, but do not
        # update the indexes yet. 
        # Update the parent child relationships.
        
        parents = ind.pop('parents', None)
        children = ind.pop('children', None)
        self._reindex_relink(parents, children, txn=txn)

        # Now, Update indexes.
        for k,v in ind.items():
            self._reindex_param(k, v, ctx=ctx, txn=txn)

    def _reindex_param(self, param, changes, ctx=None, txn=None):
        """(Internal) Reindex changes to a single parameter."""
        # If nothing changed, skip.
        if not changes:
            return

        # If we can't access the index, skip. (Raise Exception?)
        ind = self.getindex(param, txn=txn)
        indkeywords = self.getindex('keywords', txn=txn)
        if ind == None:
            return

        # Check the cache for the param
        hit, pd = ctx.cache.check(('paramdef', param))
        if not hit:
            pd = self.dbenv['paramdef']._get_data(param, txn=txn)
            ctx.cache.store(('paramdef', param), pd)
        vt = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd, db=ctx.db, cache=ctx.cache)

        # Process the changes into index addrefs / removerefs
        try:
            addrefs, removerefs = vt.reindex(changes)
            addkeywords, removekeywords = vt.reindex_keywords(changes)
        except Exception, e:
           print "Could not reindex param %s: %s"%(pd.name, e)
           return

        # Write!
        for oldval, recs in removerefs.items():
            ind.removerefs(oldval, recs, txn=txn)
        for newval,recs in addrefs.items():
            ind.addrefs(newval, recs, txn=txn)
        for oldval, recs in removekeywords.items():
            indkeywords.removerefs(oldval, recs, txn=txn)
        for newval,recs in addkeywords.items():
            indkeywords.addrefs(newval, recs, txn=txn)



    ##### Manage indexes. #####

    def getindex(self, param, txn=None):
        """Open a parameter index. Requires txn.

        A successfully opened IndexDB will be cached in self.indexes[param] and
        reused on subsequent calls.

        If an index for a parameter isn't returned by this method, the reindex
        method will just skip it.

        :param param: Parameter
        :param txn: Transaction
        :return: IndexDB

        """
        if param in self.indexes:
            return self.indexes.get(param)

        # Check the paramdef to see if it's indexed.
        try:
            pd = self.dbenv["paramdef"]._get_data(param, txn=txn)
        except KeyError:
            self.indexes[param] = None
            return None
        
        # Check the key format.
        vartype = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd)
        tp = vartype.keyformat
        if not pd.indexed or not tp:
            self.indexes[param] = None
            return None
            
        # Open the index
        indname = os.path.join(self.keytype, 'index', param)
        ind = emen2.db.btrees.IndexDB(filename=indname, extension='index', keyformat=tp, dataformat=self.keyformat, dbenv=self.dbenv)

        # Cache the open index.
        self.indexes[param] = ind
        
        # Careful; truncate all indexes if this is set. Used for rebuilding all indexes.
        if self._truncate_index and ind:
           ind.truncate(txn=txn) 

        return ind

    def rebuild_indexes(self, ctx=None, txn=None):
        # Use our own txn
        txn2 = self.dbenv.newtxn(write=True)

        emen2.db.log.info("BDB: Rebuilding indexes: Start")
        # ugly hack..
        self._truncate_index = True
        for k in self.indexes:
            self.indexes[k].truncate(txn=txn2)

        keys = sorted(map(self.keyload, self.bdb.keys(txn2)), reverse=True)
        self.dbenv.txncommit(txn2)

        for chunk in emen2.util.listops.chunk(keys, 1000):
            txn3 = self.dbenv.newtxn(write=True)
            if chunk:
                emen2.db.log.info("BDB: Rebuilding indexes: %s ... %s"%(chunk[0], chunk[-1]))
            items = [self._get_data(i, txn=txn3) for i in chunk]
            ind = self._reindex(items, reindex=True, txn=txn3)
            self._reindex_write(ind, ctx=ctx, txn=txn3)
            self.dbenv.txncommit(txn3)

        self._truncate_index = False
        emen2.db.log.info("BDB: Rebuilding indexes: Done")

    ##### Sequences #####

    # Todo: Simplify this. Maybe move it somewhere else.
    def _update_names(self, items, txn=None):
        """Update items with new names. Requires txn.

        :param items: Items to update.
        :keyword txn: Transaction.

        """
        namemap = {}
        for item in items:
            if not self.exists(item.name, txn=txn):
                # Get a new name.
                newname = self._key_generator(item, txn=txn)
                try:
                    newname = self.keyclass(newname)
                except:
                    raise Exception, "Invalid name: %s"%newname
                # Check the name is still available, and acquire lock.
                if self.exists(newname, txn=txn, flags=bsddb3.db.DB_RMW):
                    raise emen2.db.exceptions.ExistingKeyError, "%s already exists"%newname
                # Update the item's name.
                namemap[item.name] = newname
                item.__dict__['name'] = newname

        # Update all the record's links
        for item in items:
            item.__dict__['parents'] = set([namemap.get(i,i) for i in item.get('parents', [])])
            item.__dict__['children'] = set([namemap.get(i,i) for i in item.get('children', [])])

        return namemap

    def _key_generator(self, item, txn=None):
        # Set name policy in this method.
        return unicode(item.name or emen2.db.database.getrandomid())

    def _incr_sequence(self, key='sequence', txn=None):
        # Update a sequence key. Requires txn.
        # The Sequence DB can handle multiple keys -- e.g., for
        # binaries, each day has its own sequence key.
        delta = 1
        
        val = self.sequencedb.get(key, txn=txn, flags=bsddb3.db.DB_RMW)
        if val == None:
            val = 0
        val = int(val)
        
        self.sequencedb.put(key, str(val+delta), txn=txn)
        emen2.db.log.debug("BDB: %s sequence: %s -> %s"%(self.filename, val, val+delta))
        return val

    def _get_max(self, key="sequence", txn=None):
        """Return the current maximum item in the sequence. Requires txn.

        :keyword txn: Transaction
        """
        sequence = self.sequencedb.get(key, txn=txn)
        if sequence == None:
            sequence = 0
        val = int(sequence)
        return val

    ##### Relationship methods #####

    def expand(self, names, ctx=None, txn=None):
        """Expand names.

        This allows 'name*' to serve as shorthand for "name, and all
        children recursively." This is useful for specifying items in queries.

        :param names: DBO names, with optional '*' to include children.
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Expanded DBO names.
        """
        if not isinstance(names, set):
            names = set(names)

        # Expand *'s
        remove = set()
        add = set()
        for key in (i for i in names if isinstance(i, basestring)):
            try:
                newkey = self.keyclass(key.replace('*', ''))
            except:
                raise KeyError, "Invalid key: %s"%key

            if key.endswith('*'):
                add |= self.rel([newkey], rel='children', recurse=-1, ctx=ctx, txn=txn).get(newkey, set())
            remove.add(key)
            add.add(newkey)

        names -= remove
        names |= add
        return names

    def parents(self, names, recurse=1, ctx=None, txn=None):
        """See rel(), with rel='parents", tree=False. Requires ctx and txn.

        This will return a dict of parents to the specified recursion depth.

        :return: Dict with names as keys, and their parents as values

        """
        return self.rel(names, recurse=recurse, rel='parents', ctx=ctx, txn=txn)

    def children(self, names, recurse=1, ctx=None, txn=None):
        """See rel(), with rel="children", tree=False. Requires ctx and txn.

        This will return a dict of children to the specified recursion depth.

        :return: Dict with names as keys, and their children as values

        """
        return self.rel(names, recurse=recurse, rel='children', ctx=ctx, txn=txn)

    # Siblings
    def siblings(self, name, ctx=None, txn=None):
        """Siblings. Note this only takes a single name. Requries ctx and txn.

        :keyword name: DBO name
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Set of siblings

        """
        parents = self.rel([name], rel='parents', ctx=ctx, txn=txn)
        allparents = set()
        for k,v in parents.items():
            allparents |= v
        siblings = set()
        children = self.rel(allparents, ctx=ctx, txn=txn)
        for k,v in children.items():
            siblings |= v
        return siblings

    # Checks permissions, return formats, etc..
    def rel(self, names, recurse=1, rel='children', tree=False, ctx=None, txn=None):
        """Find relationships. Requires context and transaction.

        Find relationships to a specified recusion depth. This supports any
        type of relationship that has a correctly setup index available;
        currently parents and children are supported. In the future, it will
        support any IndexDB that has names for keys, and the relationships
        as values.

        This method is public because it is sometimes convenient to find
        relationships based on a supplied argument without a case switch
        or duplication of code. However, it switches return types based on
        the tree keyword. Because of this complexity, it is usually called
        through the following convenience methods:
            parents, children, tree

        If tree keyword is True, the returned value will be a tree structure.
        This will have each specified DBO name as a key, and one level of
        children as values. These children will in turn have their own keys,
        and their own children as values, up to the specified recursion depth.

        If tree keyword is False, the returned value will be a dictionary
        with DBO names as keys, and their children (up to the specified
        recursion depth) as values.

        Example edges:
            1: 2, 3
            2: 3
            3: 4
            4: None

        ...with names = [1,2,3] and tree=True and recurse=-1:
            {1: [2,3], 2: [3], 3:[4], 4:[]}

        ...with names = [1,2,3], tree=False, and recurse=-1:
            {1: [2,3,4], 2: [3,4], 3:[4]}

        :keyword names: DBO names
        :keyword recurse: Recursion depth (default is 1)
        :keyword rel: Relationship type (default is children)
        :keyword tree: Set return type to tree or set
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Return a tree structure if tree=True, otherwise a set

        """
        result = {}
        visited = {}
        t = time.time()
        for i in names:
            result[i], visited[i] = self._bfs(i, rel=rel, recurse=recurse)

        # Flatten the dictionary to get all touched names
        allr = set()
        for v in visited.values():
            allr |= v

        # Filter by permissions
        allr = self.filter(allr, ctx=ctx, txn=txn)

        # If Tree=True, we're returning the tree... Filter for permissions.
        if tree:
            outret = {}
            for k, v in result.iteritems():
                for k2 in v:
                    outret[k2] = result[k][k2] & allr
            return outret

        # Else we're just ruturning the total list of all children,
        # keyed by requested record name
        for k in visited:
            visited[k] &= allr

        return visited

    def pclink(self, parent, child, ctx=None, txn=None):
        """Create parent-child relationship. Requires ctx and txn.

        Both items will have their parent/child attributes updated
        to reflect the new relationship. You must specify a Context, and
        have READ permissions on BOTH items, and WRITE permission on AT LEAST
        ONE item.

        :param parent: Parent
        :param child: Child
        :keyword ctx: Context
        :keyword txn: Transaction

        """
        self._putrel(parent, child, mode='addrefs', ctx=ctx, txn=txn)

    def pcunlink(self, parent, child, ctx=None, txn=None):
        """Remove parent-child relationship. Requires ctx and txn.

        Both items will have their parent/child attributes updated
        to reflect the deleted relationship. You must specify a Context, and
        have READ permissions on BOTH items, and WRITE permission on AT LEAST
        ONE item.

        :param parent: Parent
        :param child: Child
        :keyword ctx: Context
        :keyword txn: Transaction

        """
        self._putrel(parent, child, mode='removerefs', ctx=ctx, txn=txn)

    def relink(self, removerels=None, addrels=None, ctx=None, txn=None):
        """Add and remove a number of parent-child relationships at once."""
        removerels = removerels or []
        addrels = addrels or []
        remove = collections.defaultdict(set)
        add = collections.defaultdict(set)
        ci = emen2.util.listops.check_iterable

        for k,v in removerels.items():
            for v2 in ci(v):
                remove[self.keyclass(k)].add(self.keyclass(v2))
        for k,v in addrels.items():
            for v2 in ci(v):
                add[self.keyclass(k)].add(self.keyclass(v2))

        items = set(remove.keys()) | set(add.keys())
        items = self.gets(items, ctx=ctx, txn=txn)
        for item in items:
            item.children -= remove[item.name]
            item.children |= add[item.name]

        return self.puts(items, ctx=ctx, txn=txn)

    def _putrel(self, parent, child, mode='addrefs', txn=None):
        # (Internal) Add or remove a relationship.
        # Mode is addrefs or removerefs; it maps to the IndexDB method.

        # Check that we have enough permissions to write to one item
        # Use raw get; manually setContext. Allow KeyErrors to raise.
        p = self._get_data(parent, txn=txn, flags=bsddb3.db.DB_RMW)
        c = self._get_data(child, txn=txn, flags=bsddb3.db.DB_RMW)
        perm = []

        # Both items must exist, and we need to be able to write to one
        try:
            p.setContext(ctx)
            perm.append(p.writable())
        except emen2.db.exceptions.SecurityError:
            pass

        try:
            c.setContext(ctx)
            perm.append(c.writable())
        except emen2.db.exceptions.SecurityError:
            pass

        if not any(perm):
            raise emen2.db.exceptions.SecurityError, "Insufficient permissions to add/remove relationship"

        # Transform into the right format for _reindex_relink..
        newvalue = set() | p.children # copy
        if mode == 'addrefs':
            newvalue |= set([c.name])
        elif mode == 'removerefs':
            newvalue -= set([c.name])

        # The values will actually be set on the records
        #  during the relinking method..
        self._reindex_relink([], [[p.name, newvalue, p.children]], txn=txn)

    # Handle the reindexing...
    def _reindex_relink(self, parents, children, txn=None):
        # (Internal) Relink relationships
        # This method will grab both items, and add or remove the rels from
        # each item, and then update the parents/children IndexDBs.
        indc = self.getindex('children', txn=txn)
        indp = self.getindex('parents', txn=txn)

        # The names of new items.
        names = []

        # Process change sets into new and removed links
        add = []
        remove = []
        for name, new, old in (parents or []):
            old = set(old or [])
            new = set(new or [])
            for i in new - old:
                add.append((i, name))
            for i in old - new:
                remove.append((i, name))
            names.append(name)

        for name, new, old in (children or []):
            old = old or set()
            new = new or set()
            for i in new - old:
                add.append((name, i))
            for i in old - new:
                remove.append((name, i))
            names.append(name)

        p_add = collections.defaultdict(set)
        p_remove = collections.defaultdict(set)
        c_add = collections.defaultdict(set)
        c_remove = collections.defaultdict(set)

        for p,c in add:
            p_add[c].add(p)
            c_add[p].add(c)
        for p,c in remove:
            p_remove[c].add(p)
            c_remove[p].add(c)

        # Go and fetch other items that we need to update
        names = set(p_add.keys()+p_remove.keys()+c_add.keys()+c_remove.keys())
        # print "All affected items:", names
        # Get and modify the item directly w/o Context:
        # Linking only requires write permissions
        # on ONE of the items.
        for name in names:
            try:
                rec = self._get_data(name, txn=txn)
            except:
                continue
            rec.__dict__['parents'] -= p_remove[rec.name]
            rec.__dict__['parents'] |= p_add[rec.name]
            rec.__dict__['children'] -= c_remove[rec.name]
            rec.__dict__['children'] |= c_add[rec.name]
            self._put_data(rec.name, rec, txn=txn)
        for k,v in p_remove.items():
            if v:
                indp.removerefs(k, v, txn=txn)
        for k,v in p_add.items():
            if v:
                indp.addrefs(k, v, txn=txn)
        for k,v in c_remove.items():
            if v:
                indc.removerefs(k, v, txn=txn)
        for k,v in c_add.items():
            if v:
                indc.addrefs(k, v, txn=txn)
        return

    ##### Search tree-like indexes (e.g. parents/children) #####

    def _bfs(self, key, rel='children', recurse=1, ctx=None, txn=None):
        # (Internal) Tree search
        # Return a dict of results as well as the nodes visited (saves time)
        
        # Check max recursion depth
        if recurse == -1:
            recurse = emen2.db.config.get('params.maxrecurse')

        # Get the index, and create a cursor (slightly faster)
        rel = self.getindex(rel, txn=txn)
        cursor = rel.bdb.cursor(txn=txn)

        # Starting items

        # NOTE: I am using this ugly direct call because it saves 10-20% time.
        new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) #

        stack = [new]
        result = {key: new}
        visited = set()
        lookups = []

        for x in xrange(recurse-1):
            if not stack[x]:
                break

            stack.append(set())
            for key in stack[x] - visited:
                new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) 
                if new:
                    stack[x+1] |= new #.extend(new)
                    result[key] = new

            visited |= stack[x]

        visited |= stack[-1]
        cursor.close()
        return result, visited


class BinaryDB(CollectionDB):
    """CollectionDB for Binaries"""
    def _key_generator(self, item, txn=None):
        """Assign a name based on date, and the counter for that day."""
        # Get the current date and counter.
        dkey = emen2.db.binary.Binary.parse('')
        # Increment the day's counter.
        counter = self._incr_sequence(key=dkey['datekey'], txn=txn)
        # Make the new name.
        newdkey = emen2.db.binary.Binary.parse(dkey['name'], counter=counter)
        # Update the item's filepath..
        item.__dict__['_filepath'] = newdkey['filepath']
        # Return the new name.
        return newdkey['name']


ALLOW_RECORD_NAMES = False
class RecordDB(CollectionDB):
    def _key_generator(self, item, txn=None):
        # Set name policy in this method.
        if ALLOW_RECORD_NAMES:
            return unicode(item.name or emen2.db.database.getrandomid())
        return unicode(self._incr_sequence(txn=txn))

    # Todo: integrate with main filter method, since this works
    # for all permission-defined items.
    def filter(self, names, ctx=None, txn=None):
        """Filter for permissions.
        :param names: Record name(s).
        :returns: Readable Record names.
        """
        if names is None:
            if ctx.checkreadadmin():
                m = self._get_max(txn=txn)
                return set(map(unicode, range(0, m)))
                # return set(self.keys(txn=txn))
            ind = self.getindex("permissions", txn=txn)
            indc = self.getindex('creator', txn=txn)
            indg = self.getindex("groups", txn=txn)
            ret = ind.get(ctx.username, set(), txn=txn)
            ret |= indc.get(ctx.username, set(), txn=txn)
            for group in sorted(ctx.groups, reverse=True):
                ret |= indg.get(group, set(), txn=txn)
            return ret            

        names = set(names)

        if ctx.checkreadadmin():
            return names

        # If less than a thousand items, get directly.
        if len(names) <= 1000:
            items = self.gets(names, ctx=ctx, txn=txn)
            return set([i.name for i in items])

        # Make a copy
        find = copy.copy(names)

        # Use the permissions/groups index
        ind = self.getindex('permissions', txn=txn)
        indc = self.getindex('creator', txn=txn)
        indg = self.getindex('groups', txn=txn)

        find -= ind.get(ctx.username, set(), txn=txn)
        find -= indc.get(ctx.username, set(), txn=txn)
        for group in sorted(ctx.groups):
            if find:
                find -= indg.get(group, set(), txn=txn)

        return names - find


class UserDB(CollectionDB):
    def new(self, *args, **kwargs):
        txn = kwargs.get('txn', None)

        # DB.new. This will check the main bdb for an existing name.
        user = super(UserDB, self).new(*args, **kwargs)

        # Check  if this email already exists
        indemail = self.getindex('email', txn=txn)
        if indemail.get(user.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError

        return user

    def filter(self, names=None, ctx=None, txn=None):
        # You need to be logged in to view this.
        if not ctx or ctx.username == 'anonymous':
            return set()
        return super(UserDB, self).filter(names, ctx=ctx, txn=txn)


class NewUserDB(CollectionDB):
    def delete(self, key, ctx=None, txn=None, flags=0):
        if not ctx.checkadmin():
            raise emen2.db.exceptions.SecurityError, "Only admin can delete keys."
        self.bdb.delete(self.keydump(key), txn=txn, flags=flags)

    def new(self, *args, **kwargs):
        txn = kwargs.get('txn', None)
        newuser = super(NewUserDB, self).new(*args, **kwargs)

        # Check if any pending accounts have this email address
        # for k,v in self._get_data_items(txn=txn):
        #    if newuser.email == v.email:
        #        raise emen2.db.exceptions.ExistingKeyError

        # Check  if this email already exists
        indemail = self.getindex('email', txn=txn)
        if indemail.get(newuser.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError

        # Check if this email already exists
        indemail = self.dbenv["user"].getindex('email', txn=txn)
        if self.dbenv["user"].exists(newuser.name, txn=txn) or indemail.get(newuser.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError

        return newuser

    def filter(self, names=None, ctx=None, txn=None):
        # This requires admin access
        if not ctx or not ctx.checkadmin():
            raise emen2.db.exceptions.SecurityError, "Admin rights needed to view user queue"
        return super(NewUserDB, self).filter(names, ctx=ctx, txn=txn)


__version__ = "$Revision: 1.167 $".split(":")[1][:-1].strip()