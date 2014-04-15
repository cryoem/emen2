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
    def __init__(self, db=None, infile=None):
        self.infile = infile
        self.db = db

    def load(self, infile=None, keytype=None):
        t = time.time()
        dbenv = self.db._db.dbenv
        ctx = self.db._ctx
        txn = self.db._txn

        count = 0        
        for item in self.readfile(infile=infile, keytype=keytype):
            keytype = item.get('keytype')
            name = item.get('name')
            print "Load: put:", keytype, name
            # try:
            r = dbenv[keytype].put(item, ctx=ctx, txn=txn)
            # except Exception, e:
            #   print "Could not load %s %s:"%(keytype, name), e
            count += 1

        t = time.time()-t
        s = float(count) / t
        print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

    def readfile(self, infile=None, keytype=None):
        infile = infile or self.infile
        if not os.path.exists(infile):
            yield
        with codecs.open(infile, 'r', 'utf-8') as f:
            for item in f:
                item = item.strip()
                if item and not item.startswith('/'):
                    item = json.loads(item)
                    if keytype:
                        if keytype == item.get('keytype'):
                            yield item
                    else:
                        yield item
                        
# class RawLoader(Loader):
#     def load(self, infile=None, keytype=None):
#         t = time.time()
#         count = 0
#         dbenv = self.db._db.dbenv
#         ctx = self.db._ctx
#         txn = self.db._txn
#         children = collections.defaultdict(set)
#         parents = collections.defaultdict(set)
# 
#         for item in self.readfile(infile=infile, keytype=keytype):
#             print "Starting:", keytype
#             keytype = item.get('keytype')
#             name = item.get('name')
#             children[name] = item.pop('children', []) or []
#             parents[name] = item.pop('parents', []) or []
#             try:
#                 r = dbenv[keytype].new(ctx=ctx, txn=txn)
#                 r.data.update(item)
#                 r = dbenv[keytype]._put(r, txn=txn)
#                 # print r.data
#             except Exception, e:
#                 print "Could not load...", e
#             count += 1
#             
#         for k,v in children.items():
#             for v2 in v:
#                 try:
#                     dbenv[keytype].pclink(k, v2, ctx=ctx, txn=txn)
#                 except Exception, e:
#                     print "Could not link:", k, v2
#         for k,v in parents.items():
#             for v2 in v:
#                 try:
#                     dbenv[keytype].pclink(v2, k, ctx=ctx, txn=txn)
#                 except Exception, e:
#                     print "Could not link:", v2, k
# 
#         t = time.time()-t
#         s = float(count) / t
#         print "Load: total time: %0.2f, %0.2f put/sec"%(t, s)

if __name__ == "__main__":
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument('--raw', action='store_true', help='Raw load; no validation.')
    opts.add_argument('--keytype', action='append')
    opts.add_argument('--update_record_max', action='store_true')    
    opts.add_argument('files', nargs='*')
    args = opts.parse_args()
    
    keytypes = ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']
    if args.keytype:
        keytypes = args.keytype

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
        
