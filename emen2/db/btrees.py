"""BerkeleyDB Driver."""

import collections
import copy
import functools
import os
import shutil
import time
import traceback
import cPickle as pickle
import json
import re

# Berkeley DB
# Note: the 'bsddb' module is not sufficient.
import bsddb3

# EMEN2 imports
import emen2.db.config
import emen2.db.log
import emen2.db.query
import emen2.utils
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
try:
    import emen2.db.bulk
    bulk = emen2.db.bulk
    # emen2.db.log.info("Note: using EMEN2-BerkeleyDB bulk access module")
except ImportError, inst:
    bulk = None

# Don't touch these!
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
        self.path = path or emen2.db.config.get('home')
        self.snapshot = snapshot or (not emen2.db.config.get('bdb.snapshot'))
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
        
    def open(self):
        """Open the Database Environment."""
        emen2.db.log.info("BDB: Opening database environment: %s"%self.path)
        dbenv = bsddb3.db.DBEnv()
        dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
        
        txncount = (self.cachesize / 4096) * 2
        if txncount > 1024*128:
            txncount = 1024*128
            
        dbenv.set_cachesize(0, self.cachesize)
        dbenv.set_tx_max(int(txncount))
        dbenv.set_lk_max_locks(300000)
        dbenv.set_lk_max_lockers(300000)
        dbenv.set_lk_max_objects(300000)
        dbenv.set_lk_detect(bsddb3.db.DB_LOCK_MINWRITE)
        dbenv.set_timeout(1000000, flags=bsddb3.db.DB_SET_LOCK_TIMEOUT)
        dbenv.set_timeout(120000000, flags=bsddb3.db.DB_SET_TXN_TIMEOUT)

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
        self.keytypes['paramdef']  = CollectionDB(dataclass=emen2.db.paramdef.ParamDef, dbenv=self)
        self.keytypes['recorddef'] = CollectionDB(dataclass=emen2.db.recorddef.RecordDef, dbenv=self)
        self.keytypes['group']     = CollectionDB(dataclass=emen2.db.group.Group, dbenv=self)
        self.keytypes['record']    = RecordDB(dataclass=emen2.db.record.Record, dbenv=self)
        self.keytypes['user']      = UserDB(dataclass=emen2.db.user.User, dbenv=self)
        self.keytypes['newuser']   = NewUserDB(dataclass=emen2.db.user.NewUser, dbenv=self)
        self.keytypes['binary']    = CollectionDB(dataclass=emen2.db.binary.Binary, dbenv=self)
        # Private.
        self._user_history         = CollectionDB(dataclass=emen2.db.user.History, keytype='user_history', dbenv=self)
        self._context              = CollectionDB(dataclass=emen2.db.context.Context, dbenv=self)

    # ian: todo: make this nicer.
    def close(self):
        """Close the Database Environment"""
        emen2.db.log.info("BDB: Closing database environment: %s"%self.path)        
        for k,v in self.keytypes.items():
            v.close()
        self.dbenv.close()

    def __getitem__(self, key, default=None):
        """Pass dictionary gets to self.keytypes."""
        return self.keytypes.get(key, default)

    ##### Transaction management #####

    def newtxn(self, write=False):
        """Start a new transaction.
        
        :keyword write: Write transaction; turns off Berkeley DB Snapshot
        :return: New transaction
        """
        write = True
        if write:
            txn = self.dbenv.txn_begin()
        else:
            txn = self.dbenv.txn_begin(flags=bsddb3.db.DB_TXN_SNAPSHOT)
        emen2.db.log.debug("TXN: start: %s, id: %s"%(txn, txn.id()))
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
            raise ValueError("Transaction callback 'when' must be before or after.")
        if condition not in ['commit', 'abort']:
            raise ValueError("Transaction callback 'condition' must be commit or abort.")
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

# Context-aware DB for Database Objects.
# These support a single DB and a single data class.
# Supports sequenced items.
class CollectionDB(object):
    '''Database for items supporting the DBO interface (mapping
    interface, setContext, writable, etc. See BaseDBObject.)

    Most methods require a transaction. Additionally, because
    this class manages DBOs, most methods also require a Context.

    Methods:
        __init__         Opens DBs in a specific directory
        open             Also opens sequencedb
        close            Also cloes sequencdb and indexes

    The following methods that require a context:
        new              New item
        get              Get a single item
        gets             Get items
        put              Put a single item
        puts             Put items
        filter           Context-aware keys
        query            Query
        validate         Validate an item
        exists           Check if an item exists already

    Relationship methods:
        parents          Returns parents
        children         Returns children
        siblings         Item siblings
        rel              General relationship method
        pclink           Add a parent/child relationship
        pcunlink         Remove a parent/child relationship
        relink           Add and remove several relationships

    May be deprecated at some point:
        keys
        values
        items

    Some internal methods:
        _get
        _put

    Sequence methods:
        _update_name    Update items with new names from sequence
        _key_generator

    Index methods:
        _getindex         Open an index
        _getrel           Open a relationship index
    '''
    
    def __init__(self, filename=None, keytype=None, dataclass=None, dbenv=None):
        """Create and open the DB.
        
        :param filename: Base filename to use
        :keyword dbenv: Database environment
        """
        # EMEN2DBEnv and BDB handle
        self.dbenv = dbenv
        self.bdb = None

        # Indexes and relationships        
        self.indexes = {}
        self.rels = {}
        self.sequence = None

        # What are we storing?
        self.keytype = (keytype or dataclass.__name__).lower()        
        self.keydump = lambda x:unicode(x).encode('utf-8')
        self.keyload = lambda x:x.decode('utf-8')
        self.dataclass = dataclass
        self.datadump = lambda x:json.dumps(x.data)
        self.dataload = lambda x:json.loads(x)

        # Make sure the directory exists...
        self.filename = filename or os.path.join(self.keytype, '%s.bdb'%self.keytype)
        try:
            os.makedirs(os.path.join(dbenv.path, 'data', self.keytype))
        except:
            pass

        # Open.
        self.open()

    def open(self):
        """Open the DB. This uses an implicit open transaction."""
        if self.bdb:
            raise Exception("DB already open.")
        emen2.db.log.debug("BDB: %s open"%self.filename)
        flags = 0
        flags |= bsddb3.db.DB_AUTO_COMMIT 
        flags |= bsddb3.db.DB_CREATE 
        flags |= bsddb3.db.DB_THREAD
        flags |= bsddb3.db.DB_MULTIVERSION
        self.bdb = bsddb3.db.DB(self.dbenv.dbenv)
        self.bdb.open(filename=self.filename, dbtype=bsddb3.db.DB_BTREE, flags=flags)

    def close(self):
        """Close the DB."""
        emen2.db.log.debug("BDB: %s close"%self.filename)
        if self.bdb:
            self.bdb.close()
            self.bdb = None
        if self.sequence:
            self.sequence.close()
            self.sequence = None
        for v in self.rels.values():
            v.close()
        for v in self.indexes.values():
            v.close()

    ##### Sequence #####

    def _getseq(self, txn=None):
        if self.sequence:
            return self.sequence
        self.sequence = SequenceDB(keytype=self.keytype, dbenv=self.dbenv)
        return self.sequence

    ##### Indexes #####

    def _getrel(self, param, txn=None):
        if param in self.rels:
            return self.rels.get(param)
        if param not in ['parents', 'children']:
            self.rels[param] = None
            return None
        vtc = emen2.db.vartypes.Vartype.get_vartype(name=param) # Has to be a core param.
        index = IndexDB(keytype=self.keytype, param=param, extension='rel', vtc=vtc, dbenv=self.dbenv)
        self.rels[param] = index
        return index

    def _getindex(self, param, txn=None):
        if param in self.indexes:
            return self.indexes.get(param)   
        try:
            # Check if we've cached the param details
            vtc = emen2.db.vartypes.Vartype.get_vartype(name=param)
        except KeyError:
            # Otherwise get the param details.
            try:
                pd = self.dbenv['paramdef']._get(param, txn=txn)
            except KeyError:
                raise KeyError("Unknown param: %s"%param)
            vtc = emen2.db.vartypes.Vartype.get_vartype(**pd.data)
        
        # Check if it's indexed.
        try:
            vtc.reindex(None)
        except NotImplementedError:
            # print "Not indexed!", param
            self.indexes[param] = None
            return
                    
        # Open the secondary index.
        index = IndexDB(keytype=self.keytype, param=param, vtc=vtc, dbenv=self.dbenv)
        self.indexes[param] = index
        return index

    ##### New items... #####

    def new(self, **kwargs):
        """Returns new DBO. Requires ctx and txn.

        All keyword args will be passed to the constructor.

        :keyword txn: Transaction
        :return: New DBO
        :exception ExistingKeyError:
        """
        # Clean up kwargs.
        txn = kwargs.pop('txn', None)
        ctx = kwargs.pop('ctx', None)
        inherit = kwargs.pop('inherit', [])
        item = self.dataclass.new(ctx=ctx, **kwargs)
        # print item.__dict__
        for i in inherit:
            # Raise an exception if does not exist or cannot read.
            i = self.get(i, filt=False, ctx=ctx, txn=txn)
            if i.get('permissions'):
                item.addumask(i.get('permissions'))
            if i.get('groups'):
                item.addgroup(i.get('groups'))
            # Backwards compat.
            if item.data.get('parents'):
                item.data['parents'].append(i.name)
            else:
                item.data['parents'] = [i.name]
                
        # Acquire a write lock on this name.
        if self.exists(item.name, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError("%s already exists."%item.name)
        return item

    ##### Exists #####
    
    def exists(self, key, ctx=None, txn=None):
        """Check if a key exists."""
        # Note: this method does not check permissions; you could use it to check
        #     if a key exists or not, even if you can't read the value.
        emen2.db.log.debug("BDB: %s exists: %s"%(self.filename, key))
        if key is None or key < 0:
            return False
        return self.bdb.exists(self.keydump(key), txn=txn, flags=bsddb3.db.DB_RMW)
        
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
    
    ##### Keys, values, items #####
    
    def keys(self, ctx=None, txn=None):
        # emen2.db.log.info("BDB: %s keys: Deprecated method!"%self.filename)
        return map(self.keyload, self.bdb.keys(txn))
    
    def items(self, ctx=None, txn=None):
        raise NotImplementedError
        
    def values(self, ctx=None, txn=None):
        raise NotImplementedError

    ##### Filtered context gets.. #####

    def get(self, key, filt=True, ctx=None, txn=None):
        """Get a single item, with a Context. Requires ctx and txn."""
        r = self.gets([key], txn=txn, ctx=ctx, filt=filt)
        if not r:
            return None
        return r[0]

    def gets(self, keys, filt=True, ctx=None, txn=None):
        """Get a list of items, with a Context. Requires ctx and txn.

        The filt keyword, if True, will ignore KeyError and PermissionsError.
        Alternatively, it can be set to a list of Exception types to ignore.

        :param key: Items to get
        :keyword filt: Ignore KeyError, PermissionsError
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: DBOs with bound Context
        :exception KeyError:
        :exception PermissionsError:
        """
        if filt == True:
            filt = (emen2.db.exceptions.PermissionsError, KeyError)
        ret = []
        for key in keys:
            try:
                d = self._get(key, txn=txn)
                d.setContext(ctx)
                ret.append(d)
            except filt, e:
                pass
        return ret
        
    def _get(self, key, txn=None):
        emen2.db.log.debug("BDB: %s get: %s"%(self.filename, key))        
        d = self.bdb.get(self.keydump(key), txn=txn)
        if d is None:
            raise KeyError("No such key: %s"%(key))
        return self.dataclass.load(json.loads(d))

    ##### Write methods #####

    def validate(self, item, ctx=None, txn=None):
        # Get the existing item or create a new one.
        name = item.get('name')
        if self.exists(name, txn=txn):
            # Get the existing item.
            orec = self._get(name, txn=txn)
            # May raise a PermissionsError if you can't read it.
            orec.setContext(ctx)
            orec.update(item)
        else:
            # Create a new item.
            orec = self.new(ctx=ctx, txn=txn, **item)
        # Update the item.
        orec.validate()
        return orec

    def put(self, item, ctx=None, txn=None):
        """Update a single item. Requires ctx and txn.

        :param item: DBO, or similar (e.g. dict)
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Updated DBO
        :exception KeyError:
        :exception PermissionsError:
        :exception ValidationError:
        """
        return self._put(self.validate(item, ctx=ctx, txn=txn), ctx=ctx, txn=txn)
    
    def puts(self, items, ctx=None, txn=None):
        """Update a list of items. Requires ctx and txn."""
        return [self.put(item, ctx=ctx, txn=txn) for item in items]    
        
    def _put(self, item, ctx=None, txn=None):
        emen2.db.log.debug("BDB: %s put: %s"%(self.filename, item.data))        
        namemap = self._update_name(item, txn=txn)
        parents = item.data.pop('parents', [])
        children = item.data.pop('children', [])
        try:
            old = self._get(item.name, txn=txn)
        except:
            old = {}
            
        # Put
        self.bdb.put(self.keydump(item.name), self.datadump(item), txn=txn)

        # Reindex
        okw = set()
        nkw = set()
        for k in set(old.keys() + item.keys()):
            ind = self._getindex(k, txn=txn)
            if not ind:
                continue
            a, b = ind.reindex(item.name, old.get(k), item.get(k), txn=txn)
            if ind.param not in ['creationtime', 'modifytime']:
                okw |= a
                nkw |= b

        ind = self._getindex('keywords', txn=txn)
        if ind:
            ind.removerefs(item.name, okw - nkw, txn=txn)
            ind.addrefs(item.name, nkw - okw, txn=txn)        
        
        # Link
        for k in parents:
            self._putrel(k, item.name, ctx=ctx, txn=txn)
        for k in children:
            self._putrel(item.name, k, ctx=ctx, txn=txn)
        return item
        
    def query(self, c=None, keywords=None, mode='AND', subset=None, ctx=None, txn=None):
        """Return a Query Constraint Group.

        You will need to call constraint.run() to execute the query,
        and constraint.sort() to sort the values.
        """
        return emen2.db.query.Query(constraints=c, keywords=keywords, mode=mode, subset=subset, ctx=ctx, txn=txn, btree=self)
    
    def find(self, param, key, maxkey=None, op='==', count=100, ctx=None, txn=None):
        index = self._getindex(param, txn=txn) 
        if index is None:
            return None
        return index.find(key=key, maxkey=maxkey, op=op, txn=txn) 

    def find_both(self, param, key, maxkey=None, op='==', count=100, ctx=None, txn=None):
        index = self._getindex(param, txn=txn) 
        if index is None:
            return None
        return index.find_both(key=key, maxkey=maxkey, op=op, txn=txn)

    ##### Sequences #####

    # Todo: Simplify this. Maybe move it somewhere else.
    def _update_name(self, item, txn=None):
        """Update items with new names. Requires txn.

        :param items: Items to update.
        :keyword txn: Transaction.
        """
        namemap = {}
        if not self.exists(item.name, txn=txn):
            # Get a new name.
            newname = self._key_generator(item, txn=txn)
            # Check the name is still available, and acquire lock.
            if self.exists(newname, txn=txn):
                raise emen2.db.exceptions.ExistingKeyError("%s already exists."%newname)
            # Update the item's name.
            item.data['name'] = newname
            namemap[item.name] = newname
        else:
            namemap[item.name] = item.name                
        return namemap

    def _key_generator(self, item, txn=None):
        # Set name policy in this method.
        return unicode(item.name or emen2.utils.timeuuid())

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
        keys = set()
        for key in names:
            if key.endswith('*'):
                key = key.replace('*','')
                keys |= self.rel([key], rel='children', recurse=-1, ctx=ctx, txn=txn).get(key, set())
            keys.add(key)
        return keys

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

        If tree keyword is False, the returned value will be an adjacency list
        with dictionary with DBO names as keys, and their children (up to the
        specified recursion depth) as values.

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
        :keyword tree: Set return type to adjacency list or set
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Return an adjacency list if tree=True, otherwise a set
        """
        result = {}
        visited = {}
        t = time.time()
        
        # Get the index, and create a cursor here (slightly faster)
        rel = self._getrel(rel, txn=txn)
        for i in names:
            result[i], visited[i] = rel.bfs(i, recurse=recurse, txn=txn)

        # Flatten the dictionary to get all touched names
        allr = set()
        for v in visited.values():
            allr |= v

        # Filter by permissions
        allr = self.filter(allr, ctx=ctx, txn=txn)

        # If Tree=True, we're returning the adjacency list... Filter for permissions.
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
        return []

    def _putrel(self, parent, child, mode='addrefs', ctx=None, txn=None):
        emen2.db.log.debug("BDB: %s _putrel %s: %s %s "%(self.filename, mode, parent, child))        
        parent = self.get(parent, ctx=ctx, txn=txn)
        child = self.get(child, ctx=ctx, txn=txn)
        if not (parent.writable() or child.writable()):
            raise emen2.db.exceptions.SecurityError("Insufficient permissions to edit relationship.")

        ind_parents = self._getrel('parents', txn=txn)
        ind_children = self._getrel('children', txn=txn)
        if mode == 'addrefs':
            ind_parents.addrefs(parent.name, [child.name], txn=txn)    
            ind_children.addrefs(child.name, [parent.name], txn=txn)    
        elif mode == 'removerefs':
            ind_parents.removerefs(parent.name, [child.name], txn=txn)
            ind_children.removerefs(child.name, [parent.name], txn=txn)

class RecordDB(CollectionDB):
    def _key_generator(self, item, txn=None):
        if emen2.db.config.get('record.sequence'):
            seq = self._getseq()
            return unicode(seq.next(txn=txn))
        return unicode(item.name or emen2.utils.timeuuid())

    # Todo: integrate with main filter method.
    def filter(self, names=None, ctx=None, txn=None):
        """Filter for permissions.
        :param names: Record name(s).
        :returns: Readable Record names.
        """
        if names is None:
            if ctx.checkreadadmin():
                if emen2.db.config.get('record.sequence'):
                    seq = self._getseq()
                    return set(map(unicode, range(0, seq.max(txn=txn))))
                return set(self.keys(txn=txn))  
            ret = self.find('permissions', ctx.user, txn=txn)
            ret |= self.find('creator', ctx.user, txn=txn) 
            for group in sorted(ctx.groups, reverse=True):
                ret |= self.find('groups', group, txn=txn)
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
        find -= self.find('permissions', ctx.user, txn=txn)
        find -= self.find('creator', ctx.user, txn=txn) 
        for group in sorted(ctx.groups):
            if find:
                find -= self.find('groups', group, txn=txn)
        return names - find

class UserDB(CollectionDB):
    def new(self, *args, **kwargs):
        # Check  if this email already exists.
        txn = kwargs.get('txn', None)
        user = super(UserDB, self).new(*args, **kwargs)
        if self.find('email', user.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError
        return user
    
    def filter(self, names=None, ctx=None, txn=None):
        # You need to be logged in to view this.
        if not ctx or ctx.user == 'anonymous':
            return set()
        return super(UserDB, self).filter(names, ctx=ctx, txn=txn)

class NewUserDB(CollectionDB):
    def delete(self, key, ctx=None, txn=None):
        if not ctx.checkadmin():
            raise emen2.db.exceptions.PermissionsError("Only admin can delete keys.")
        self.bdb.delete(self.keydump(key), txn=txn)

    def new(self, *args, **kwargs):
        # Check  if this email already exists.
        txn = kwargs.get('txn', None)
        newuser = super(NewUserDB, self).new(*args, **kwargs)
        if self.find('email', newuser.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError
        if self.dbenv["user"].exists(newuser.name, txn=txn) or self.dbenv['user'].find('email', newuser.email, txn=txn):
            raise emen2.db.exceptions.ExistingKeyError
        return newuser

    def filter(self, names=None, ctx=None, txn=None):
        # This requires admin access
        if not ctx or not ctx.checkadmin():
            raise emen2.db.exceptions.PermissionsError("Admin rights needed to view user queue.")
        return super(NewUserDB, self).filter(names, ctx=ctx, txn=txn)

class SequenceDB(object):
    # Sequences.
    def __init__(self, filename=None, keytype=None, dbenv=None):
        # Filename, DBENV, BDB handle.
        self.keytype = keytype
        self.filename = filename or os.path.join(self.keytype, '%s.sequence'%keytype)
        self.dbenv = dbenv
        self.bdb = None
        self.open()    

    def open(self):
        """Open the DB. This uses an implicit open transaction."""
        if self.bdb:
            raise Exception("DB already open.")
        emen2.db.log.debug("BDB: %s open"%self.filename)
        flags = 0
        flags |= bsddb3.db.DB_AUTO_COMMIT 
        flags |= bsddb3.db.DB_CREATE 
        flags |= bsddb3.db.DB_THREAD
        flags |= bsddb3.db.DB_MULTIVERSION        
        self.bdb = bsddb3.db.DB(self.dbenv.dbenv)
        self.bdb.open(filename=self.filename, dbtype=bsddb3.db.DB_BTREE, flags=flags)

    def close(self):
        """Close the DB."""
        emen2.db.log.debug("BDB: %s close"%self.filename)
        self.bdb.close()
        self.bdb = None
        
    def next(self, key='sequence', txn=None):
        # Update a sequence key. Requires txn.
        # The Sequence DB can handle multiple keys -- e.g., for
        # binaries, each day has its own sequence key.
        delta = 1
        
        val = self.bdb.get(key, txn=txn, flags=bsddb3.db.DB_RMW)
        if val == None:
            val = 0
        val = int(val)
        
        self.bdb.put(key, str(val+delta), txn=txn)
        emen2.db.log.debug("BDB: %s sequence: %s -> %s"%(self.filename, val, val+delta))
        return val

    def max(self, key="sequence", txn=None):
        """Return the current maximum item in the sequence. Requires txn.

        :keyword txn: Transaction
        """
        sequence = self.bdb.get(key, txn=txn)
        if sequence == None:
            sequence = 0
        val = int(sequence)
        return val

class IndexDB(object):
    # A secondary index. Also used for relationships.
    def __init__(self, filename=None, keytype=None, param=None, extension='index', vtc=None, dbenv=None):
        # Filename, DBENV, BDB handle.
        self.keytype = keytype
        self.param = param
        self.filename = filename or os.path.join(self.keytype, '%s.%s.%s'%(keytype, param, extension))
        self.dbenv = dbenv
        self.bdb = None

        # Index settings.
        self.vtc = vtc
        self.keydump = lambda x:unicode(x).lower().encode('utf-8')
        self.keyload = self.vtc.keyclass # lambda x:self.vtc.keyclass(x)
        self.open()    

    def open(self):
        """Open the DB. This uses an implicit open transaction."""
        if self.bdb:
            raise Exception("DB already open.")
        emen2.db.log.debug("BDB: %s open"%self.filename)
        flags = 0
        flags |= bsddb3.db.DB_AUTO_COMMIT 
        flags |= bsddb3.db.DB_CREATE 
        flags |= bsddb3.db.DB_THREAD
        flags |= bsddb3.db.DB_MULTIVERSION        
        self.bdb = bsddb3.db.DB(self.dbenv.dbenv)
        self.bdb.set_flags(bsddb3.db.DB_DUP)
        self.bdb.set_flags(bsddb3.db.DB_DUPSORT)
        # A little magicky but works.
        if self.vtc.keyclass in [float, int]:
            # print "setting comparison function for %s: %s"%(self.param, self.vtc.keyclass)
            self.bdb.set_bt_compare(self._cmpfunc)
        self.bdb.open(filename=self.filename, dbtype=bsddb3.db.DB_BTREE, flags=flags)

    def close(self):
        """Close the DB."""
        emen2.db.log.debug("BDB: %s close"%self.filename)
        self.bdb.close()
        self.bdb = None
    
    def reindex(self, key, old, new, txn=None):
        key = str(key)
        old = self.vtc.reindex(old)
        new = self.vtc.reindex(new)
        self.removerefs(key, old - new, txn=txn)
        self.addrefs(key, new - old, txn=txn)
        return old, new
    
    def addrefs(self, key, values, txn=None):
        if not values:
            return
        emen2.db.log.debug(u"BDB: %s addrefs: %s %s"%(self.filename, key, values))
        cursor = self.bdb.cursor(txn=txn)
        for i in values:
            try:
                cursor.put(self.keydump(i), unicode(key).encode('utf-8'), flags=bsddb3.db.DB_KEYFIRST)
            except bsddb3.db.DBKeyExistError, e:
                pass
        cursor.close()
            
    def removerefs(self, key, values, txn=None):
        if not values:
            return
        emen2.db.log.debug(u"BDB: %s removerefs: %s %s"%(self.filename, key, values))
        cursor = self.bdb.cursor(txn=txn)
        for i in values:
            if cursor.set_both(self.keydump(i), unicode(key).encode('utf-8')):
                cursor.delete()       
        cursor.close()

    def _cmpfunc(self, k1, k2):
        # Numeric comparison function, for BTree sorting.
        return cmp(self.keyload(k1 or '0'), self.keyload(k2 or '0'))

    def bfs(self, key, recurse=1, txn=None):
        # (Internal) Relationships
        # Check max recursion depth
        maxrecurse = emen2.db.config.get('params.maxrecurse')
        if recurse < 0:
            recurse = maxrecurse
        if recurse > maxrecurse:
            recurse = maxrecurse

        # Starting items
        cursor = self.bdb.cursor(txn=txn)
        new = set(self._get_cursor(key, cursor))
        tovisit = [new]
        result = {key: new}
        visited = set()
        lookups = []
        for x in xrange(recurse-1):
            if not tovisit[x]:
                break
            tovisit.append(set())
            for key in tovisit[x] - visited:
                new = set(self._get_cursor(key, cursor))
                if new:
                    tovisit[x+1] |= new
                    result[key] = new
            visited |= tovisit[x]

        visited |= tovisit[-1]
        cursor.close()
        return result, visited        

    def find(self, key, maxkey=None, op='==', count=100, txn=None):
        r = self.find_both(key=key, maxkey=maxkey, op=op, count=count, txn=txn)
        return set(i[1] for i in r)
    
    def find_both(self, key, maxkey=None, op='==', count=100, txn=None):
        # I don't like this method name, but whatevs.
        emen2.db.log.debug("BDB: %s %s index %s %s"%(self.filename, self.param, op, key))        
        if key is None:
            return set()
        r = []
        cursor = self.bdb.cursor(txn=txn)
        if op == 'starts':
            r = self._get_starts(key, cursor)
        elif op == 'range':
            r = self._get_range(key, maxkey, cursor)
        elif op == '>=':
            r = self._get_gte(key, cursor)            
        elif op == '>':
            r = self._get_gt(key, cursor)            
        elif op == '<=':
            r = self._get_lte(key, cursor)            
        elif op == '<':
            r = self._get_lt(key, cursor)            
        elif op == '==':
            r = self._get_is(key, cursor)
        elif op == '!=':
            r = self._get_not(key, cursor)        
        elif op == 'any':
            r = self._get_any(key, cursor)
        elif op == 'noop':
            r = self._get_any(key, cursor)
        else:
            raise Exception("Unsupported operator.")
        cursor.close()
        # print "find_both: param %s, key %s, maxkey %s, op %s, count %s"%(self.param, key, maxkey, op, count)
        return [(self.keyload(i[0]), i[1]) for i in r]
    
    def get(self, key, txn=None):
        cursor = index.cursor(txn=txn)        
        r = []
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET)
        m = cursor.next_dup
        while c:
            r.append(c)
            n = m()
        cursor.close()
        return r
    
    ##### Begin a bunch of repetitive code to iterate through cursor in various ways #####

    def _get_cursor(self, key, cursor):        
        r = []
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET)
        m = cursor.next_dup
        while c:
            r.append(c[1]) # Just want values here.
            c = m()
        return r

    def _get_is(self, key, cursor):
        r = []
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET)
        while c:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT_DUP)
        return r
    
    def _get_starts(self, key, cursor):
        r = []
        # This only works with strings.
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET_RANGE)
        k = self.keydump(key)
        while c and c[0].startswith(k):
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r
        
    def _get_range(self, minkey, maxkey, cursor):
        r = []
        c = cursor.get(self.keydump(minkey), flags=bsddb3.db.DB_SET_RANGE)
        while c and self.keyload(c[0]) <= maxkey:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

    def _get_gte(self, key, cursor):
        r = []
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET_RANGE)
        while c:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

    def _get_gt(self, key, cursor):
        r = []
        c = cursor.get(self.keydump(key), flags=bsddb3.db.DB_SET_RANGE)
        while c:
            if self.keyload(c[0]) > key:
                r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

    def _get_lte(self, key, cursor):
        r = []
        c = cursor.get(flags=bsddb3.db.DB_FIRST)
        while c and self.keyload(c[0]) <= key:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

    def _get_lt(self, key, cursor):
        r = []
        c = cursor.get(flags=bsddb3.db.DB_FIRST)
        while c and self.keyload(c[0]) < key:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r
    
    def _get_not(self, key, cursor):
        r = []
        c = cursor.get(flags=bsddb3.db.DB_FIRST)
        kd = self.keydump(key)
        while c:
            if c[0] != kd:
                r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

    def _get_any(self, key, cursor):
        r = []
        c = cursor.get(flags=bsddb3.db.DB_FIRST)
        while c:
            r.append(c)
            c = cursor.get(flags=bsddb3.db.DB_NEXT)
        return r

