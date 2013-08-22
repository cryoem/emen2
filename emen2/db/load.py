"""Load a dumped database

Classes:
    Loader
    RegularLoader
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

    def load(self):
        pass

    def loadfile(self, infile=None, keytype=None):
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

class RegularLoader(Loader):
    def load(self):
        t = time.time()
        count = 0
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        for item in self.loadfile():
            keytype = item.get('keytype')
            name = item.get('name')
            # print "===== %s: %s"%(keytype, name)
            # print item
            # i = dbenv[keytype].dataclass(ctx=ctx) 
            # i._load(item)
            try:
                dbenv[keytype].puts([item], ctx=ctx, txn=txn)
            except Exception, e:
                print "Could not put", keytype, name, ":", e
            count += 1
        t = time.time()-t
        s = float(count) / t
        print "total time: %s, %s put/sec"%(t, s)

class LoadOptions(emen2.db.config.DBOptions):
    def parseArgs(self, infile):
        self['infile'] = infile

if __name__ == "__main__":
    import emen2.db
    cmd, db = emen2.db.opendbwithopts(optclass=LoadOptions, admin=True)
    with db._newtxn(write=True):
        loader = RegularLoader(db=db, infile=cmd.options['infile'])
        loader.load()
            
            
            
            
