"""Load a dumped database

Classes:
    Loader
"""

import os
import sys
import time
import tarfile
import tempfile
import string
import random
import collections
import getpass
import json
import jsonrpc.jsonutil

# EMEN2 imports
import emen2.db.config

class Loader(object):
    """Load database objects from a JSON file."""
    def __init__(self, db=None, infile=None):
        self.infile = infile
        self.db = db

    def load(self, infile=None, keytype=None):
        t = time.time()
        count = 0
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        
        # Pull out parents/children so relationships will
        # be added additively.
        children = collections.defaultdict(set)
        parents = collections.defaultdict(set)
        
        for item in self.readfile(infile=infile, keytype=keytype):
            keytype = item.get('keytype')
            name = item.get('name')
            children[name] = set(item.pop('children', []) or [])
            parents[name] = set(item.pop('parents', []) or [])
            print "Load: put:", keytype, name
            try:
                dbenv[keytype].put(item, ctx=ctx, txn=txn)
            except Exception, e:
                print "Couldn't load %s %s:"%(keytype, name), e
            count += 1
            
        keys = set(dbenv[keytype].filter(ctx=ctx, txn=txn))

        for k,v in children.items():
            missing = v-keys
            if missing:
                print "Missing keys:", missing
                v -= missing
            for v2 in v:
                dbenv[keytype].pclink(k, v2, ctx=ctx, txn=txn)
        for k,v in parents.items():
            missing = v-keys
            if missing:
                print "Missing keys:", missing
                v -= missing
            for v2 in v:
                dbenv[keytype].pclink(v2, k, ctx=ctx, txn=txn)

        t = time.time()-t
        s = float(count) / t
        print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

    def readfile(self, infile=None, keytype=None):
        infile = infile or self.infile
        if not os.path.exists(infile):
            yield
        with open(infile) as f:
            for item in f:
                item = item.strip()
                if item and not item.startswith('/'):
                    item = jsonrpc.jsonutil.decode(item)
                    if keytype:
                        if keytype == item.get('keytype'):
                            yield item
                    else:
                        yield item
                        
class RawLoader(Loader):
    def load(self, infile=None, keytype=None):
        t = time.time()
        count = 0
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        children = collections.defaultdict(set)
        parents = collections.defaultdict(set)

        for item in self.readfile(infile=infile, keytype=keytype):
            keytype = item.get('keytype')
            name = item.get('name')
            children[name] = item.pop('children', []) or []
            parents[name] = item.pop('parents', []) or []
            try:
                r = dbenv[keytype].new(ctx=ctx, txn=txn)
                r.data.update(item)
                dbenv[keytype]._put(r, ctx=ctx, txn=txn)
            except Exception, e:
                print "Couldn't load...", e
            count += 1
            
        for k,v in children.items():
            for v2 in v:
                try:
                    dbenv[keytype].pclink(k, v2, ctx=ctx, txn=txn)
                except Exception, e:
                    print "Couldn't link:", k, v2
        for k,v in parents.items():
            for v2 in v:
                try:
                    dbenv[keytype].pclink(v2, k, ctx=ctx, txn=txn)
                except Exception, e:
                    print "Couldn't link:", v2, k

        t = time.time()-t
        s = float(count) / t
        print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

if __name__ == "__main__":
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument('--raw', action='store_true', help='Raw load; no validation.')
    opts.add_argument('files', nargs='+')
    args = opts.parse_args()
    
    keytypes = ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']

    lc = Loader
    if args.raw:
        lc = RawLoader
    
    import emen2.db
    db = emen2.db.opendb(admin=True)
    for f in args.files:
        with db:
            loader = lc(db=db, infile=f)
            for keytype in keytypes:
                loader.load(keytype=keytype)
        
