"""Cassandra Driver."""

import collections
import time
import uuid
import json

# EMEN2 imports
import emen2.db.config
import emen2.db.log
import emen2.db.query
import emen2.util.listops
from emen2.db.exceptions import *

# Base DBEnv and BTree; finish refactoring into more abstract base classes.
import emen2.db.btrees        

# EMEN2 DBObjects
import emen2.db.dataobject
import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group

# Cassandra
import cql

INITCQL = """
DROP KEYSPACE emen2;

CREATE KEYSPACE emen2 WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE record (
    // id uuid,
    id text,
    ts timeuuid,
    user text,
    param text,
    value text,
    PRIMARY KEY (id, ts)
);

CREATE INDEX on record(user);
CREATE INDEX on record(param);
CREATE INDEX on record(value);

CREATE TABLE record_rel (
    source text,
    param text,
    target text,
    ts timeuuid,
    user text,
    PRIMARY KEY (source, param, target)
);

CREATE TABLE binary (
    id text,
    creationtime timeuuid,
    modifytime timeuuid,
    creator text,
    modifyuser text,
    uri text,
    filename text,
    filesize int,
    md5 text,
    compress text,
    record text,
    PRIMARY KEY (id)
);

CREATE TABLE user (
    id text,
    creationtime timeuuid,
    modifytime timeuuid,
    creator text,
    modifyuser text,
    uri text,
    email text,
    password text,    
    PRIMARY KEY (id)
);

CREATE TABLE group (
    id text,
    creationtime timeuuid,
    modifytime timeuuid,
    creator text,
    modifyuser text,
    uri text,
    read set<text>,
    comment set<text>,
    write set<text>,
    owners set<text>,
    PRIMARY KEY (id)
);

CREATE TABLE context (
    id text,
    creationtime timeuuid,
    creator text,
    groups set<text>,
    ttl int,
    PRIMARY KEY (id)
);

CREATE TABLE paramdef (
    id text,
    creationtime timeuuid,
    modifytime timeuuid,
    creator text,
    modifyuser text,
    uri text,
    desc_short text,
    desc_long text,
    vartype text,
    defaultunits text,
    property text,
    indexed boolean,
    iter boolean,
    immutable boolean,
    choices list<text>,
    PRIMARY KEY (id)
);

CREATE TABLE recorddef (
    id text,
    creationtime timeuuid,
    modifytime timeuuid,
    creator text,
    modifyuser text,
    uri text,
    desc_short text,
    desc_long text,
    mainview text,
    views map<text, text>,
    PRIMARY KEY (id)
);

USE emen2;
"""

class CTxn(object):
    """This is for compatibility with BDB code and the transaction commit/fail callbacks."""
    def __init__(self, txnid=0):
        self._txnid = txnid
        
    def id(self):
        return self._txnid
        
    def commit(self):
        pass
        
    def abort(self):
        pass

##### EMEN2 Database Environment #####

class EMEN2DBEnv(emen2.db.btrees.EMEN2DBEnv):
    def __init__(self, host=None, path=None, *args, **kwargs):
        """Cassandra driver."""
        
        # Database environment directory
        self.path = path

        # Databases
        self.keytypes =  {}

        # Pre- and post-commit actions.
        self._txncbs = collections.defaultdict(list)

        # Open connection
        self.dbenv = self.open()

        # Open DBEnv.
        self.init()
            
    def create(self):
        pass
        
    def open(self):
        """Open the Database Environment."""
        emen2.db.log.info("C*: Opening")
        dbenv = cql.connect('localhost', 9160, 'emen2')
        dbenv.set_cql_version('3.0.0')
        return dbenv

    def cursor(self):
        return self.dbenv.cursor()

    def close(self):
        """Close the Database Environment"""
        emen2.db.log.info("C*: Closing")
        self.dbenv.close()
        pass

    def newtxn(self, write=False, flags=0):
        """Start a new transaction."""
        txn = CTxn()
        emen2.db.log.debug("TXN: start: %s flags %s"%(txn, flags))
        return txn

    def init(self):
        # Authentication. These are not public.
        self._context = CollectionDB(dataclass=emen2.db.context.Context, dbenv=self)
        # These are public dbs.
        self.keytypes['paramdef']  = CollectionDB(dataclass=emen2.db.paramdef.ParamDef, dbenv=self)
        self.keytypes['recorddef'] = CollectionDB(dataclass=emen2.db.recorddef.RecordDef, dbenv=self)
        self.keytypes['group']     = CollectionDB(dataclass=emen2.db.group.Group, dbenv=self)
        self.keytypes['record']    = CollectionDB(dataclass=emen2.db.record.Record, dbenv=self)
        self.keytypes['user']      = CollectionDB(dataclass=emen2.db.user.User, dbenv=self)
        self.keytypes['newuser']   = CollectionDB(dataclass=emen2.db.user.NewUser, dbenv=self)
        self.keytypes['binary']    = CollectionDB(dataclass=emen2.db.binary.Binary, dbenv=self)

# Berkeley DB wrapper classes
class BaseDB(object):
    def __init__(self, dataclass=None, dbenv=None):
        self.dbenv = dbenv
        self.dataclass = dataclass
        self.open()

    def open(self):
        pass

    def close(self):
        pass
        
    def truncate(self, txn=None):
        pass
    
class IndexDB(BaseDB):
    def get(self, key, default=None, cursor=None, txn=None):
        return []

    def keys(self, minkey=None, maxkey=None, txn=None):
        return []
        
    def items(self, minkey=None, maxkey=None, txn=None):
        return []

    def removerefs(self, key, items, txn=None):
        return []

    def addrefs(self, key, items, txn=None):
        return []

class CollectionDB(BaseDB):
    def __init__(self, *args, **kwargs):
        dataclass = kwargs.get('dataclass')
        dbenv = kwargs.get('dbenv')
        self.keytype = (kwargs.get('keytype') or dataclass.__name__).lower()
        return super(CollectionDB, self).__init__(*args, **kwargs)

    def exists(self, key, ctx=None, txn=None, flags=0):
        return False
    
    def filter(self, names=None, ctx=None, txn=None):
        return []
    
    def keys(self, ctx=None, txn=None):
        return []
    
    def items(self, ctx=None, txn=None):
        return []
        
    def values(self, ctx=None, txn=None):
        raise []

    def get(self, key, filt=True, ctx=None, txn=None):
        r = self.gets([key], txn=txn, ctx=ctx, filt=filt)
        if not r:
            return None
        return r[0]

    def gets(self, keys, filt=True, ctx=None, txn=None):
        if filt == True:
            filt = (emen2.db.exceptions.SecurityError, KeyError)

        ret = []
        for key in keys:
            try:
                d = self._get_data(key, txn=txn)
                d.setContext(ctx)
                ret.append(d)
            except filt, e:
                pass
        return ret
        
    def _get_data(self, key, txn=None):
        emen2.db.log.info("C*: _get_data: %s"%key)
        q = """SELECT id, ts, user, param, value FROM record WHERE id=:id ORDER BY ts ASC"""
        cur = self.dbenv.cursor()
        cur.execute(q, {'id':key})
        r = {}
        for row in cur:
            if not r:
                r['id'] = row[0]
                r['creationtime'] = row[1]
                r['modifytime'] = row[2]
            r['modifytime'] = row[1]
            r['modifyuser'] = row[2]
            r[row[3]] = json.loads(row[4])
        cur.close()
        return r
        
    def _get_data2(self, keys):
        j = "('%s')"%"','".join(map(str, keys))        
        q = """SELECT id, ts, user, param, value FROM record WHERE id in %s ORDER BY ts ASC"""%j
        ret = {}
        cur = self.dbenv.cursor()
        cur.execute(q, {'id':keys})
        for row in cur:
            r = ret.get(row[0], {})
            if not r:
                r['id'] = row[0]
                r['creationtime'] = row[1]
                r['modifytime'] = row[2]
                ret[row[0]] = r
            r['modifytime'] = row[1]
            r['modifyuser'] = row[2]
            r[row[3]] = json.loads(row[4])
        cur.close()
        return ret
        
        
    def validate(self, items, ctx=None, txn=None):
        return self.puts(items, commit=False, ctx=ctx, txn=txn)

    def put(self, item, commit=True, ctx=None, txn=None):
        ret = self.puts([item], commit=commit, ctx=ctx, txn=txn)
        if not ret:
            return None
        return ret[0]
        
    def puts(self, items, commit=True, ctx=None, txn=None):
        if not commit:
            return items
        return self._put_data(items, ctx=ctx, txn=txn)
        
    def _put(self, item, ctx=None, txn=None):
        return self._puts([item], ctx=ctx, txn=txn)[0]

    def _puts(self, items, ctx=None, txn=None):
        for item in items:
            self._put_data(item.name, item, txn=txn)
        return items

    def _cass_insert(self, key, stream):
        cur = self.dbenv.cursor()
        for ts, user, param, value in stream:
            q = """INSERT INTO record (id, ts, user, param, value) VALUES (:id, :ts, :user, :param, :value);"""
            d = {'id':key, 'ts': uuid.uuid1(), 'user':user, 'param':param, 'value':json.dumps(value)}
            cur.execute(q, d)
        cur.close()

    def _cass_putrel(self, source, param, target):
        cur = self.dbenv.cursor()
        q = """INSERT INTO record_rel (source, param, target) VALUES (:source, :param, :target)"""
        d = {'source':source, 'param':param, 'target':target}
        cur.execute(q, d)
        cur.close()

    def _cass_getrel(self, key, param, cur=None):
        cur.execute(
            """SELECT target FROM record_rel WHERE source = :id AND param = :param;""", 
            {'id':key, 'param':param}
        )
        ret = set()
        for row in cur:
            ret.add(row[0])
        return ret

    def _cass_getrel2(self, keys, param, cur=None):
        # test hack
        j = "('%s')"%"','".join(map(str, keys))
        q = """SELECT source, target FROM record_rel WHERE source in %s AND param = :param"""%j
        cur.execute(
            q,
            {'param':param}
        )
        ret = collections.defaultdict(set)
        for row in cur:
            ret[row[0]].add(row[1])
        return ret

    def _cass_bfs(self, key, param='children', recurse=1):
        # (Internal) Relationships
        # Return a dict of results as well as the nodes visited
        if recurse < 0:
            recurse = emen2.db.config.get('params.maxrecurse')

        cur = self.dbenv.cursor()
        new = self._cass_getrel(key, param, cur)
        result = {key: new}
        tovisit = [new]
        visited = set([key])
        
        for x in xrange(recurse-1):
            if not tovisit[x]:
                break
            tovisit.append(set())
            n = self._cass_getrel2(tovisit[x] - visited, param, cur=cur)
            for k,new in n.items():
                tovisit[x+1] |= new
                result[k] = new

            visited |= tovisit[x]
        cur.close()
        return result
        
    def query(self, c=None, mode='AND', subset=None, ctx=None, txn=None):
        return {}

    def getindex(self, param, txn=None):
        pass

    def rebuild_indexes(self, ctx=None, txn=None):
        pass

    ##### Relationship methods #####

    def expand(self, names, ctx=None, txn=None):
        if not isinstance(names, set):
            names = set(names)
        return names
        
    def parents(self, names, recurse=1, ctx=None, txn=None):
        return self.rel(names, recurse=recurse, rel='parents', ctx=ctx, txn=txn)

    def children(self, names, recurse=1, ctx=None, txn=None):
        return self.rel(names, recurse=recurse, rel='children', ctx=ctx, txn=txn)

    def siblings(self, name, ctx=None, txn=None):
        return set()

    def rel(self, names, recurse=1, rel='children', tree=False, ctx=None, txn=None):
        return {}

    def pclink(self, parent, child, ctx=None, txn=None):
        return

    def pcunlink(self, parent, child, ctx=None, txn=None):
        return

    def relink(self, removerels=None, addrels=None, ctx=None, txn=None):
        pass

class CollectionSliceDB(CollectionDB):
    pass
