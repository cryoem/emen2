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
import codecs

# EMEN2 imports
import jsonrpc.jsonutil
import emen2.db.config

class Loader(object):
    """Load database objects from a JSON file."""
    def __init__(self, db=None):
        self.db = db

    def load(self, infile=None, keytype=None):
        t = time.time()
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn
        count = 0
        for item in self.readfile(infile=infile):
            keytype = item.get('keytype')
            name = item.get('name')
            print "Load: put:", keytype, name
            r = dbenv[keytype].put(item, ctx=ctx, txn=txn)
            count += 1
            
        t = time.time()-t
        s = float(count) / t
        print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

    def readfile(self, infile):
        if not os.path.exists(infile):
            yield
        with codecs.open(infile, 'r', 'utf-8') as f:
            for item in f:
                item = item.strip()
                if item and not item.startswith('/'):
                    yield json.loads(item)

if __name__ == "__main__":
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    # opts.add_argument('--raw', action='store_true', help='Raw load; no validation.')
    opts.add_argument('--keytype', action='append')
    opts.add_argument('--update_record_max', action='store_true')    
    opts.add_argument('files', nargs='*')
    args = opts.parse_args()
    
    keytypes = ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']
    if args.keytype:
        keytypes = args.keytype

    lc = Loader
    # if args.raw:
    #     lc = RawLoader
    
    import emen2.db
    db = emen2.db.opendb(admin=True)
    for f in args.files:
        with db:
            loader = lc(db=db)
            for keytype in keytypes:
                loader.load(infile=f, keytype=keytype)
    
    if args.update_record_max:
        # Hacky... :(
        with db:
            keys = db._db.dbenv['record'].keys(txn=db._txn)
            ki = []
            for key in keys:
                try: ki.append(int(key))
                except: pass
            print "Max key?", max(ki)
            db._db.dbenv['record']._getseq(txn=db._txn).set('sequence', max(ki))
        
