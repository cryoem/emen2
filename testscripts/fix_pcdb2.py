# $Id: fix_pcdb2.py,v 1.1 2012/07/31 02:07:06 irees Exp $
import cPickle as pickle
from testc import *

with db:
    pds = {}
    for i in ddb.dbenv["paramdefs"].pcdb2.keys(txn):
        pds[i] = map(pickle.loads, map(str, ddb.dbenv["paramdefs"].pcdb2.get(i, txn)))
    
    rds = {}
    for i in ddb.dbenv["recorddefs"].pcdb2.keys(txn):
        rds[i] = map(pickle.loads, map(str, ddb.dbenv["recorddefs"].pcdb2.get(i, txn)))
    
    ddb.dbenv["recorddefs"].pcdb2.truncate(txn)
    ddb.dbenv["paramdefs"].pcdb2.truncate(txn)

    ddb.dbenv["recorddefs"].cpdb2.truncate(txn)
    ddb.dbenv["paramdefs"].cpdb2.truncate(txn)

    for k,v in pds.items():
        for v2 in v:
            db.pclink(k, v2, keytype="paramdef")

    for k,v in rds.items():
        for v2 in v:
            db.pclink(k, v2, keytype="recorddef")
            
__version__ = "$Revision: 1.1 $".split(":")[1][:-1].strip()
