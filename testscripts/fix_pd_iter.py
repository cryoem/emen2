# Older versions of EMEN2 used vartypes such as "stringlist" instead of "string"
# with attribute "iter" = True. This script updates existing ParamDefs to the new
# system.

import collections
import emen2.db
db = emen2.db.opendb(admin=True)

convert = {
    'links':'link',
    'stringlist':'string',
    'binary':'binary',
    'comments':'comments',
    'intlist':'int',
    'intlistlist':'coordinate',
    'groups':'groups',
    'userlist':'user',
    'floatlist':'float',
    'history':'history',
    'choicelist':'choice',
    'acl':'acl',
    'groups':'group',
    'urilist':'uri'
}

with db:
    ctx = db._getctx()
    txn = db._gettxn()
    pds = db.paramdef.get(db.paramdef.find())
    pds = [i[1] for i in db._db['paramdef'].items()]
    byvt = collections.defaultdict(set)
    for i in pds:
        byvt[i.vartype].add(i)

    for k,v in byvt.items(): print "\n", k, v
    print "Initializing pd.iter to False"
    for pd in pds:
        pd.__dict__['iter'] = False
        pd.__dict__['immutable'] = False

    for old, new in convert.items():
        for pd in byvt.get(old) or []:
            print "Converting %s from %s to %s"%(pd.name, old, new)
            pd.__dict__['iter'] = True
            pd.__dict__['vartype'] = new

    for pd in byvt.get('binaryimage') or []:
        print "Changing %s from binaryimage to binary, non-iter"%pd.name
        pd.__dict__['iter'] = False
        pd.__dict__['vartype'] = 'binary'

    for pd in byvt.get('names',set())|byvt.get('name',set()):
        print "Changing %s from names to string, non-iter"%pd.name
        pd.__dict__['iter'] = False
        pd.__dict__['vartype'] = 'string'

    for pd in byvt.get('rectype',set()):
        print "Changing %s from rectype to recorddef, non-iter"%pd.name
        pd.__dict__['iter'] = False
        pd.__dict__['vartype'] = 'recorddef'
        

    print "Truncating"
    db._db["paramdef"].truncate(txn=txn)
            
    print "Committing"
    for pd in pds:
        db._db["paramdef"]._put_data(pd.name, pd, txn=txn)
    db._db['paramdef'].rebuild_indexes(ctx=ctx, txn=txn)
            
    # raise Exception