# $Id: load.py,v 1.37 2012/07/28 06:31:18 irees Exp $
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
    def __init__(self, db=None, infile=None, path=''):
        self.infile = infile
        self.db = db

    def loadfile(self, infile=None, keytype=None):
        infile = infile or self.infile
        if not os.path.exists(infile):
            return

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
    def load(self):
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        for keytype in ['paramdef', 'user', 'group', 'recorddef', 'binary', 'record']:
            names = []
            for item in self.loadfile(keytype=keytype):
                i = dbenv[keytype].dataclass(ctx=ctx)
                i._load(item)
                if dbenv[keytype].exists(i.name, txn=txn):
                    continue
                dbenv[keytype].put(i.name, i, txn=txn)
                names.append(i.name)
            
            for chunk in emen2.util.listops.chunk(names):
                # Get the written items for this chunk.
                items = dbenv[keytype].cgets(chunk, ctx=ctx, txn=txn)

                # Rebuild the indexes for these items.
                # 1. Calculate
                ind = dbenv[keytype].reindex(items, ctx=ctx, txn=txn, reindex=True)
                # 2. Write the index changes
                dbenv[keytype]._reindex_write(ind, ctx=ctx, txn=txn)
                



class LoadOptions(emen2.db.config.DBOptions):
    def parseArgs(self, infile):
        self['infile'] = infile


if __name__ == "__main__":
    import emen2.db
    cmd, db = emen2.db.opendbwithopts(optclass=LoadOptions, admin=True)
    with db:
        loader = Loader(db=db, infile=cmd.options['infile'])
        loader.load()
            


