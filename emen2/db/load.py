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
        children = collections.defaultdict(set)
        parents = collections.defaultdict(set)
        
        for item in self.readfile(infile=infile, keytype=keytype):
            keytype = item.get('keytype')
            name = item.get('name')
            children[name] = set(item.pop('children', []))
            parents[name] = set(item.pop('parents', []))
            try:
                dbenv[keytype].puts([item], ctx=ctx, txn=txn)
            except Exception, e:
                print "Could not put", keytype, name, ":", e
            count += 1

        for k,v in children.items():
            for v2 in v:
                dbenv[keytype].pclink(k, v2, ctx=ctx, txn=txn)
        for k,v in parents.items():
            for v2 in v:
                dbenv[keytype].pclink(v2, k, ctx=ctx, txn=txn)

        t = time.time()-t
        s = float(count) / t
        print "total time: %s, %s put/sec"%(t, s)

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

class LoadOptions(emen2.db.config.DBOptions):
    def parseArgs(self, infile):
        self['infile'] = infile

if __name__ == "__main__":
    import emen2.db
    cmd, db = emen2.db.opendbwithopts(optclass=LoadOptions, admin=True)
    with db._newtxn(write=True):
        loader = Loader(db=db, infile=cmd.options['infile'])
        for keytype in ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']:
            loader.load(keytype=keytype)
