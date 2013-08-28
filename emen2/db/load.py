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
            children[name] = set(item.pop('children', []))
            parents[name] = set(item.pop('parents', []))
            print "Load: put:", keytype, name
            dbenv[keytype].puts([item], ctx=ctx, txn=txn)
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
            children[name] = set(item.pop('children', []))
            parents[name] = set(item.pop('parents', []))
            r = dbenv[keytype].new(ctx=ctx, txn=txn)
            r.data.update(item)
            dbenv[keytype]._puts([r], ctx=ctx, txn=txn)
            count += 1
            
        keys = set(dbenv[keytype].filter(ctx=ctx, txn=txn))
        
        for k,v in children.items():
            for v2 in v & keys:
                dbenv[keytype].pclink(k, v2, ctx=ctx, txn=txn)
        for k,v in parents.items():
            for v2 in v & keys:
                dbenv[keytype].pclink(v2, k, ctx=ctx, txn=txn)

        t = time.time()-t
        s = float(count) / t
        print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

class LoadOptions(emen2.db.config.DBOptions):
    def parseArgs(self, infile):
        self['infile'] = infile

if __name__ == "__main__":
    import emen2.db
    cmd, db = emen2.db.opendbwithopts(optclass=LoadOptions, admin=True)
    with db._newtxn(write=True):
        loader = RawLoader(db=db, infile=cmd.options['infile'])
        for keytype in ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']:
            loader.load(keytype=keytype)
