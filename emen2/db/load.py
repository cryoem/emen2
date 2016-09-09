# $Id: load.py,v 1.42 2013/05/13 23:33:09 irees Exp $
"""Load a dumped database

Functions:
    random_password

Classes:
    BaseLoader
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
import emen2.util.listops
import emen2.db.config


def random_password(N):
    """Generate a random password of length N."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))

class BaseLoader(object):
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


class Loader(BaseLoader):
    # Speeds:

    # Single txn:
    #   Reading: 25000/s
    #   Instantiating: 10500/s
    #   Loading/validating: 1900/s
    #   Writing: 200/s

    # Separate txns:
    #   Reading file: 25000/s
    #   Opening txn: 8500/s
    #   Instantiating: 6000/s
    #   Loading/validating: 1600/s
    #   Writing: 83/s

    def load(self):
        t = time.time()
        count = 0
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        for item in self.loadfile():
            print "\n======= put count %s"%count
            keytype = item.get('keytype')
            i = dbenv[keytype].dataclass(ctx=ctx) 
            i._load(item)
            dbenv[keytype]._put(i, ctx=ctx, txn=txn)
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
        loader = Loader(db=db, infile=cmd.options['infile'])
        loader.load()
            
