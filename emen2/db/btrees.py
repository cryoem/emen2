# $Id$
"""Berkeley-DB BTree wrappers."""

import sys
import time
import weakref
import collections
import copy
import bsddb3
import traceback
import os
import functools
import cPickle as pickle

# EMEN2 imports
import emen2.db.config
import emen2.db.log
import emen2.util.listops
import emen2.db.query
from emen2.db.exceptions import *

try:
    import emen2.db.bulk
    bulk = emen2.db.bulk
    # emen2.db.log.info("Note: using EMEN2-BerkeleyDB bulk access module")
except ImportError, inst:
    bulk = None


# Berkeley DB wrapper classes
class BDBBase(object):
    """BerkeleyDB Btree Wrapper.

    This class uses BerkeleyDB to create an object much like a persistent
    Python Dictionary.

    :attr filename: Filename of BDB on disk
    :attr dbenv: EMEN2 Database Environment
    :attr bdb: Berkeley DB instance
    :attr cache: In memory DB
    :attr cache_parents: Relationships of cached items
    :attr cache_children: Relationships of cached items
    :attr DBOPENFLAGS: Berkeley DB flags for opening database
    :attr DBSETFLAGS: Additional flags
    """

    extension = 'bdb'

    def __init__(self, filename, keyformat='str', dataformat='str', dataclass=None, dbenv=None, autoopen=True):
        """Main BDB DB wrapper

        :param filename: Base filename to use
        :keyword dbenv: Database environment
        :keyword autoopen: Automatically open DB

        """
        # Filename
        self.filename = filename
        self.extension = extension
        
        # EMEN2DBEnv
        self.dbenv = dbenv

        # What are we storing?
        self._setkeyformat(keyformat)
        self._setdataformat(dataformat, dataclass)

        # BDB handle and open flags
        self.bdb = None
        self.DBOPENFLAGS = bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE
        self.DBSETFLAGS = []

        # Cached items
        self.cache = None
        self.cache_parents =  collections.defaultdict(set) # temporary patch
        self.cache_children = collections.defaultdict(set) # temporary patch

        self.init()
        if autoopen:
            self.open()

    def init(self):
        """Subclass init hook."""
        pass

    ##### DB methods #####

    def open(self):
        """Open the DB. This uses an implicit open transaction."""
        if self.bdb or self.cache:
            raise Exception, "DB already open"

        # Create the DB handle and set flags
        self.bdb = bsddb3.db.DB(self.dbenv.dbenv)

        # Create a memory only DB
        self.cache = bsddb3.db.DB(self.dbenv.dbenv)

        # Set DB flags, e.g. duplicate keys allowed
        for flag in self.DBSETFLAGS:
            self.bdb.set_flags(flag)
            self.cache.set_flags(flag)

        # Open the DB with the correct flags.
        fn = '%s.%s'%(self.filename, self.extension)
        self.bdb.open(filename=fn, dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)
        self.cache.open(filename=None, dbtype=bsddb3.db.DB_BTREE, flags=bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE)

    def close(self):
        """Close the DB."""
        self.bdb.close()
        self.bdb = None
        self.cache.close()
        self.cache = None

    # Dangerous!
    def truncate(self, txn=None, flags=0):
        """Truncate BDB (e.g. 'drop table'). Transaction required.
        :keyword txn: Transaction
        """
        # todo: Do more checking before performing a dangerous operation.
        self.bdb.truncate(txn=txn)
        self.cache.truncate()
        self.cache_children = {}
        self.cache_parents = {}
        emen2.db.log.commit("%s.truncate"%self.filename)

    ##### Key and data formats #####
    
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
            self.keydump = lambda x:pickle.dumps(data)
            self.keyload = lambda x:pickle.loads(data or 'N.')
        else:
            raise ValueError, "Invalid key format: %s. Supported: str, int, float"%keyformat
        self.keyformat = keyformat

    def _setdataformat(self, dataformat, dataclass=None):
        # Set the DB data type. This will bind the correct
        # dataclass attribute, and datadump and dataload methods.
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
            self.datadump = lambda x:pickle.dumps(data)
            self.dataload = lambda x:pickle.loads(data or 'N.')
        elif dataformat == 'pickle':
            # This DB stores a DBO as a pickle.
            self.dataclass = dataclass
            self.datadump = lambda x:pickle.dumps(data)
            self.dataload = lambda x:pickle.loads(data or 'N.')
        else:
            # Unknown dataformat.
            raise Exception, "Invalid data format: %s. Supported: str, int, float, pickle"%dataformat
        self.dataformat = dataformat
    

# Context-aware DB for DBO's.
# These support a single DB and a single data class.
# Supports sequenced items.
class Collection(BDBBase):
    '''Database for items supporting the DBO interface (mapping
    interface, setContext, writable, etc. See BaseDBObject.)

    Most methods require a transaction. Additionally, because
    this class manages DBOs, most methods also require a Context.

    Adds a "keytype" attribute that is used as the DB name.

    Extends the following methods:
        __init__         Changes the filename slightly
        open             Also opens sequencedb
        close            Also cloes sequencdb and indexes

    And adds the following methods that require a context:
        new              New item factory
        get              Get a single item
        gets             Get items
        put              Put a single item
        puts             Put items
        expand           Process '*' operators in names to parents/children
        names            Context-aware keys
        items            Context-aware items
        query            Query
        validate         Validate an item
        exists           Check if an item exists already
        
    Methods I plan to deprecate:
        keys
        values
        items

    Some internal methods:
        _get
        _gets
        _put
        _puts
        _put_raw
        _get_max         Return the current maximum item in the sequence
        _update_names    Update items with new names from sequence

    Index methods:
        openindex        Open an index, and store the handle in self.index
        getindex         Get an already open index, or open if necessary
        closeindex       Close an index
        _reindex         Calculate index updates
        _reindex_*       Write index updates
    
    Relationship methods:
        tree             Returns relationships, one recurse level per key
        parents          Returns parents, multiple recurse levels per key
        children         Returns children, multiple recurse levels per key
        siblings         Item siblings
        rel              General purpose relationship method
        pclink           Add a parent/child relationship
        pcunlink         Remove a parent/child relationship
        relink           Add and remove relationships at once

    '''
    
    def __init__(self, *args, **kwargs):
        # Change the filename slightly
        dataclass = kwargs.get('dataclass')
        dbenv = kwargs.get('dbenv')
        self.keytype = str(dataclass.__name__).lower()
        
        # Sequences
        self.sequencedb = None
        
        # Indexes
        self.index = {}
        self._truncate_index = False

        filename = os.path.join(self.keytype, self.keytype)
        d1 = os.path.join(dbenv.path, 'data', self.keytype)
        d2 = os.path.join(dbenv.path, 'data', self.keytype, 'index')
        for i in [d1, d2]:
            try: os.makedirs(i)
            except: pass  
        return super(DBODB, self).__init__(filename, *args, **kwargs)

    def open(self):
        """Open DB, and sequence."""
        super(DBODB, self).open()
        self.sequencedb = bsddb3.db.DB(self.dbenv.dbenv)
        self.sequencedb.open(os.path.join('%s.sequence.bdb'%self.filename), dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)

    def close(self):
        """Close DB, sequence, and indexes."""
        super(DBODB, self).close()
        self.sequencedb.close()
        self.sequencedb = None
        for k in self.index:
            self.closeindex(k)

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
        # Check if a key exists.
        # Names that are None or a negative int will be automatically assigned.
        # In this case, return immediately and don't acquire any locks.
        if key < 0 or key is None:
            return False
        return self._exists(key, txn=txn, flags=flags)

    def _exists(self, key, txn=None, flags=0):
        return self.bdb.exists(self.keydump(key), txn=txn, flags=flags) or self.cache.exists(self.keydump(key), flags=flags)
        
    ##### Keys, values, items #####
    
    def names(self, names=None, ctx=None, txn=None, **kwargs):
        """Context-aware keys(). Requires ctx and txn.

        :keyword names: Subset of items to check
        :keyword ctx: Context
        :keyword txn: Transaction
        :return: Set of keys that are accessible by the Context

        """
        if names is not None:
            if ctx.checkadmin():
                return names
            items = self.gets(names, ctx=ctx, txn=txn)
            return set([i.name for i in items])
        return set(self.keys(txn=txn))
        
    # def _keys()...
    
    # def _iterkeys()...

    # def items(self, ctx=None, txn=None):
    #     """Context-aware items. Requires ctx and txn.
    # 
    #     :keyword ctx: Context
    #     :keyword txn: Transaction
    #     :return: (key, value) items that are accessible by the Context
    #     """
    #     ret = []
    #     for k,v in self.bdb.items(txn)+self.cache.items():
    #         i = self.dataload(v)
    #         i.setContext(ctx)
    #         ret.append((self.keyload(k), i))
    #     return ret
    
    # def iteritems(self, ctx=None, txn=None):

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
        for key in self.expand(keys, ctx=ctx, txn=txn):
            try:
                d = self._get(key, txn=txn, flags=flags)
                d.setContext(ctx)
                ret.append(d)
            except filt, e:
                pass
        return ret
        
    def _get(self, key, txn=None, flags=0):
        kd = self.keydump(key)
        d = self.dataload(
            self.cache.get(kd, flags=flags)
            or
            self.bdb.get(kd, txn=txn, flags=flags) 
            )
        if d:
            return d
        raise KeyError, "No such key %s"%(key)    

    ##### Write methods #####

    def validate(self, items, ctx=None, txn=None):
        return self.puts(items, commit=False, ctx=ctx, txn=txn)

    def put(self, item, *args, **kwargs):
        """See puts(). This works the same, but for a single DBO."""
        ret = self.puts([item], *args, **kwargs)
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
                orec = self.get(name, txn=txn, flags=bsddb3.db.DB_RMW)
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
        # Assign names for new items.
        # This will also update any relationships to uncommitted records.
        self._update_names(crecs, txn=txn)

        # Now that names are assigned, calculate the index updates.
        ind = self._reindex(crecs, ctx=ctx, txn=txn)

        # Write the items "for real."
        for crec in crecs:
            self._put_raw(crec.name, crec, txn=txn)
            
        # Write index updates
        self._reindex_write(ind, ctx=ctx, txn=txn)

        emen2.db.log.info("Committed %s items"%(len(crecs)))
        return crecs

    def _put_raw(self, name, item, txn=None, flags=0):
        self.bdb.put(self.keydump(name), self.datadump(item), txn=txn)
        emen2.db.log.commit("%s.put: %s"%(self.filename, crec.name))        
    
    ##### Query #####

    def query(self, c=None, mode='AND', subset=None, ctx=None, txn=None):
        """Return a Query Constraint Group.

        You will need to call constraint.run() to execute the query,
        and constraint.sort() to sort the values.
        """
        return emen2.db.query.Query(constraints=c, mode=mode, subset=subset, ctx=ctx, txn=txn, btree=self)

    ##### Changes to indexes #####
    
    def _reindex(self, items, reindex=False, ctx=None, txn=None):
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
        for crec in items:
            # Get the current record for comparison of updated values.
            # Use an empty dict for new records so all keys
            # will seen as new (or if reindexing)
            if crec.isnew() or reindex:
                orec = {}
            else:
                orec = self._get(crec.name, txn=txn) or {}

            for param in crec.changedparams(orec):
                ind[param].append((crec.name, crec.get(param), orec.get(param)))

        # Return the index changes.
        return ind

    # .... the actual items need to be written ^^^ between these two vvv steps.

    def _reindex_write(self, ind, ctx=None, txn=None):
        """(Internal) Write index updates."""
        # Parent/child relationships are a special case.
        # The other side of the relationship needs to be updated. 
        # Calculate the correct changes here, but do not
        # update the indexes yet. 
        parents = ind.pop('parents', None)
        children = ind.pop('children', None)

        # Update the parent child relationships.
        self._reindex_relink(parents, children, ctx=ctx, txn=txn)

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
        if ind == None:
            return

        # Check that this key is currently marked as indexed
        pd = self.dbenv['paramdef'].get(param, filt=False, ctx=ctx, txn=txn)
        vt = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd, db=ctx.db, cache=ctx.cache)

        # Process the changes into index addrefs / removerefs
        try:
            addrefs, removerefs = vt.reindex(changes)
        except Exception, e:
            # print "Could not reindex param %s: %s"%(pd.name, e)
            # print changes
            return

        # Write!
        for oldval, recs in removerefs.items():
            ind.removerefs(oldval, recs, txn=txn)
        for newval,recs in addrefs.items():
            ind.addrefs(newval, recs, txn=txn)

    ##### Open, close, and rebuild indexes. #####

    def openindex(self, param, txn=None):
        """Open a parameter index. Requires txn.

        The base DBODB class provides no indexes. The subclass must implement
        this method if it wants to provide any indexes. This can be either
        one or two attributes that are indexed, such as filename/md5 in
        BinaryDB, or a complete and general index system as in RecordDB.

        If an index for a parameter isn't returned by this method, the reindex
        method will just skip it.

        :param param: Parameter
        :param txn: Transaction
        :return: IndexDB

        """
        if param in ['children', 'parents']:
            filename = os.path.join(self.keytype, 'index', param)
            ind = IndexDB(filename=filename, keyformat=self.keyformat, dataformat=self.keyformat, dbenv=self.dbenv, autoopen=False)
            ind._setbulkmode(False)
            ind.open()
        return ind

    # def openindex(self, param, txn=None):
    #     # Parents / children
    #     ind = super(RecordDB, self).openindex(param, txn=txn)
    #     if ind:
    #         return ind
    # 
    #     # Check the paramdef to see if it's indexed.
    #     pd = self.dbenv["paramdef"]._get(param, txn=txn)
    #     
    #     # Check the key format.
    #     vartype = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd)
    #     tp = vartype.keyformat
    #     if not pd.indexed or not tp:
    #         return None
    # 
    #     # Open the index
    #     ind = emen2.db.btrees.IndexDB(filename=self._indname(param), keyformat=tp, dataformat=self.keyformat, dbenv=self.dbenv)
    #     return ind

    # def openindex(self, param, txn=None):
    #     """Index on filename (and possibly MD5 in the future.)"""
    #     if param == 'filename':
    #         ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
    #     elif param == 'md5':
    #         ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
    #     else:
    #         ind = super(BinaryDB, self).openindex(param, txn=txn)
    #     return ind

    # def openindex(self, param, txn=None):
    #     if param == 'permissions':
    #         ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
    #     else:
    #         ind = super(GroupDB, self).openindex(param, txn=txn)
    #     return ind

    # def openindex(self, param, txn=None):
    #     if param == 'email':
    #         ind = emen2.db.btrees.IndexDB(filename=self._indname(param), keyformat='str', dataformat='str', dbenv=self.dbenv)
    #     elif param == 'record':
    #         ind = emen2.db.btrees.IndexDB(filename=self._indname(param), keyformat='int', dataformat='str', dbenv=self.dbenv)            
    #     else:
    #         ind = super(UserDB, self).openindex(param, txn=txn)
    #     return ind

    def _indname(self, param):
        # (Internal) Get the index filename
        return os.path.join(self.keytype, 'index', param)

    def getindex(self, param, txn=None):
        """Return an open index, or open if necessary. Requires txn.

        A successfully opened IndexDB will be cached in self.index[param] and
        reused on subsequent calls.

        :param param: Parameter
        :keyword txn: Transaction
        :return: IndexDB

        """
        if param in self.index:
            return self.index.get(param)

        ind = self.openindex(param, txn=txn)
        self.index[param] = ind
        if self._truncate_index and ind:
            ind.truncate(txn=txn)
        return ind

    def closeindex(self, param):
        """Close an index. Uses an implicit transaction for close.

        :param param: Parameter
        """
        ind = self.index.get(param)
        if ind:
            ind.close()
            self.index[param] = None

    def rebuild_indexes(self, ctx=None, txn=None):
        emen2.db.log.info("Rebuilding indexes: Start")
        # ugly hack..
        self._truncate_index = True
        for k in self.index:
            self.index[k].truncate(txn=txn)

        # Do this in chunks of 1,000 items
        # Get all the keys -- do not include cached items
        keys = sorted(map(self.keyload, self.bdb.keys(txn)), reverse=True)
        for chunk in emen2.util.listops.chunk(keys, 1000):
            if chunk:
                emen2.db.log.info("Rebuilding indexes: %s ... %s"%(chunk[0], chunk[-1]))
            items = self.gets(chunk, ctx=ctx, txn=txn)
            # Use self.reindex() instead of self.puts() -- the data should
            # already be validated, so we can skip that step.
            # self.puts(items, ctx=ctx, txn=txn)
            ind = self.reindex(items, reindex=True, ctx=ctx, txn=txn)
            self._reindex_write(ind, ctx=ctx, txn=txn)

        self._truncate_index = False
        emen2.db.log.info("Rebuilding indexes: Done")

    ##### Sequences #####

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
            item.__dict__['parents'] = set([namemap.get(i,i) for i in item.parents])
            item.__dict__['children'] = set([namemap.get(i,i) for i in item.children])

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
        emen2.db.log.commit("%s.sequence: %s"%(self.filename, val+delta))
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
                add |= self.children([newkey], recurse=-1, ctx=ctx, txn=txn).get(newkey, set())
            remove.add(key)
            add.add(newkey)
        names -= remove
        names |= add
        return names

    # Commonly used rel() variants
    def tree(self, names, recurse=1, rel='children', ctx=None, txn=None, **kwargs):
        """See rel(), tree=True. Requires ctx and txn.

        Returns a tree structure of relationships. This will be a dict, with DBO
        names as keys, and one level of relationship for the value. It will
        recurse to the level specified by the recurse keyword.

        :return: Tree structure of relationships

        """
        return self.rel(names, recurse=recurse, rel=rel, tree=True, ctx=ctx, txn=txn, **kwargs)

    def parents(self, names, recurse=1, ctx=None, txn=None, **kwargs):
        """See rel(), with rel='parents", tree=False. Requires ctx and txn.

        This will return a dict of parents to the specified recursion depth.

        :return: Dict with names as keys, and their parents as values

        """
        return self.rel(names, recurse=recurse, rel='parents', ctx=ctx, txn=txn, **kwargs)

    def children(self, names, recurse=1, ctx=None, txn=None, **kwargs):
        """See rel(), with rel="children", tree=False. Requires ctx and txn.

        This will return a dict of children to the specified recursion depth.

        :return: Dict with names as keys, and their children as values

        """
        return self.rel(names, recurse=recurse, rel='children', ctx=ctx, txn=txn, **kwargs)

    # Siblings
    def siblings(self, name, ctx=None, txn=None, **kwargs):
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
        children = self.rel(allparents, ctx=ctx, txn=txn, **kwargs)
        for k,v in children.items():
            siblings |= v
        return siblings

    # Checks permissions, return formats, etc..
    def rel(self, names, recurse=1, rel='children', tree=False, ctx=None, txn=None, **kwargs):
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

        # Filter by permissions (pass rectype= for optional Record filtering)
        allr = self.names(allr, ctx=ctx, txn=txn, **kwargs)

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

    def _putrel(self, parent, child, mode='addrefs', ctx=None, txn=None):
        # (Internal) Add or remove a relationship.
        # Mode is addrefs or removerefs; it maps to the IndexDB method.

        # Check that we have enough permissions to write to one item
        # Use raw get; manually setContext. Allow KeyErrors to raise.
        p = self.get(parent, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
        c = self.get(child, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
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
        self._reindex_relink([], [[p.name, newvalue, p.children]], ctx=ctx, txn=txn)

    # Handle the reindexing...
    def _reindex_relink(self, parents, children, ctx=None, txn=None):
        # (Internal) Relink relationships
        # This method will grab both items, and add or remove the rels from
        # each item, and then update the parents/children IndexDBs.

        indc = self.getindex('children', txn=txn)
        indp = self.getindex('parents', txn=txn)
        if not indc or not indp:
            raise KeyError, "Relationships not supported"

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

        # print "p_add", p_add
        # print "p_remove", p_remove
        # print "c_add", c_add
        # print "c_remove", c_remove
        
        #if not indexonly:
        if True:
            # Go and fetch other items that we need to update
            names = set(p_add.keys()+p_remove.keys()+c_add.keys()+c_remove.keys())
            # print "All affected items:", names
            # Get and modify the item directly w/o Context:
            # Linking only requires write permissions
            # on ONE of the items.
            for name in names:
                try:
                    rec = self.get(name, filt=False, txn=txn)
                except:
                    # print "Couldn't link to missing item:", name
                    continue

                rec.__dict__['parents'] -= p_remove[rec.name]
                rec.__dict__['parents'] |= p_add[rec.name]
                rec.__dict__['children'] -= c_remove[rec.name]
                rec.__dict__['children'] |= c_add[rec.name]
                self.put(rec.name, rec, txn=txn)

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

        # Cached items..
        if rel == 'children':
            cache = self.cache_children
        elif rel == 'parents':
            cache = self.cache_parents
        else:
            cache = {}

        # Get the index, and create a cursor (slightly faster)
        rel = self.getindex(rel, txn=txn)
        cursor = rel.bdb.cursor(txn=txn)

        # Starting items

        # NOTE: I am using this ugly direct call 'rel._get_method' to the C module because it saves 10-20% time.
        new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) #
        if key in cache:
            new |= cache.get(key, set())

        stack = [new]
        result = {key: new}
        visited = set()
        lookups = []

        for x in xrange(recurse-1):
            if not stack[x]:
                break

            stack.append(set())
            for key in stack[x] - visited:
                new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) # rel.get(key, cursor=cursor)
                if key in cache:
                    new |= cache.get(key, set())

                if new:
                    stack[x+1] |= new #.extend(new)
                    result[key] = new

            visited |= stack[x]

        visited |= stack[-1]
        cursor.close()
        return result, visited



class IndexDB(BDBBase):
    '''EMEN2DB optimized for indexes.

    IndexDB uses the Berkeley DB facility for storing multiple values for a
    single key (DB_DUPSORT). The Berkeley DB API has a method for
    quickly reading these multiple values.

    This class is intended for use with an OPTIONAL C module, _bulk.so, that
    accelerates reading from the index. The Berkeley DB bulk reading mode
    is not fully implemented in the bsddb3 package; the C module does the bulk
    reading in a single C function call, greatly speeding up performance, and
    returns the correct native Python type. The C module is totally optional
    and is transparent; the only change is read speed.

    In the DBEnv directory, IndexDBs will have a ".index" extension.

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

    #: The filename extension
    extension = 'index'

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

        delindexitems = []

        cursor = self.bdb.cursor(txn=txn)

        key = self.keyclass(key)
        items = map(self.dataclass, items)

        dkey = self.keydump(key)
        ditems = map(self.datadump, items)

        for ditem in ditems:
            if cursor.set_both(dkey, ditem):
                cursor.delete()

        if not cursor.set(dkey):
            delindexitems.append(key)

        cursor.close()
        emen2.db.log.index("%s.removerefs: %s -> %s"%(self.filename, key, len(items)))
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
        if not items: return []

        addindexitems = []

        key = self.keyclass(key)
        items = map(self.dataclass, items)
        
        dkey = self.keydump(key)
        ditems = map(self.datadump, items)
        
        cursor = self.bdb.cursor(txn=txn)

        if not cursor.set(dkey):
            addindexitems.append(key)

        for ditem in ditems:
            try:
                cursor.put(dkey, ditem, flags=bsddb3.db.DB_KEYFIRST)
            except bsddb3.db.DBKeyExistError, e:
                pass

        cursor.close()

        emen2.db.log.index("%s.addrefs: %s -> %s"%(self.filename, key, len(items)))
        return addindexitems


__version__ = "$Revision$".split(":")[1][:-1].strip()