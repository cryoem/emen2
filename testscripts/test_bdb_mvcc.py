import time
import bsddb3
import sys
import uuid
import json
import functools
import random

HOME = sys.argv[1]

def indexkey(key, data, param=None):
    data = json.loads(data)
    value = str(data.get(param))
    print "index:", key, param, "->", value
    return value

def open(path, cachesize=512):
    print("Open DBENV: %s"%path)
    dbenv = bsddb3.db.DBEnv()
    dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)

    cachesize = cachesize * 1024 * 1024
    txncount = (cachesize / 4096) * 2
    if txncount > 1024*128:
        txncount = 1024*128    
    dbenv.set_cachesize(0, cachesize)

    dbenv.set_tx_max(txncount)
    dbenv.set_lk_max_locks(300000)
    dbenv.set_lk_max_lockers(300000)
    dbenv.set_lk_max_objects(300000)
    dbenv.set_lk_detect(bsddb3.db.DB_LOCK_MINWRITE)
    dbenv.set_timeout(1000000, flags=bsddb3.db.DB_SET_LOCK_TIMEOUT)
    dbenv.set_timeout(120000000, flags=bsddb3.db.DB_SET_TXN_TIMEOUT)

    flags = 0
    flags |= bsddb3.db.DB_CREATE
    flags |= bsddb3.db.DB_INIT_MPOOL
    flags |= bsddb3.db.DB_INIT_TXN
    flags |= bsddb3.db.DB_INIT_LOCK
    flags |= bsddb3.db.DB_INIT_LOG
    flags |= bsddb3.db.DB_THREAD
    # flags |= bsddb3.db.DB_REGISTER
    # flags |= bsddb3.db.DB_RECOVER
    dbenv.open(path, flags)
    return dbenv

def opendb(dbenv, filename):
    # Create the DB handle and set flags
    print("Open DB: %s"%filename)
    db = bsddb3.db.DB(dbenv)
    flags = 0
    flags |= bsddb3.db.DB_AUTO_COMMIT 
    flags |= bsddb3.db.DB_CREATE 
    flags |= bsddb3.db.DB_THREAD
    flags |= bsddb3.db.DB_MULTIVERSION
    db.open(filename="%s.bdb"%filename, dbtype=bsddb3.db.DB_BTREE, flags=flags)

    indexes = {}
    for param in ['name', 'hello', 'time'] + ['test_%s'%i for i in range(10)]:
        index = bsddb3.db.DB(dbenv)
        index.set_flags(bsddb3.db.DB_DUP)
        index.set_flags(bsddb3.db.DB_DUPSORT)
        index.open(filename="%s.%s.index"%(filename, param), dbtype=bsddb3.db.DB_BTREE, flags=flags)
        indexfunc = functools.partial(indexkey, param=param)
        db.associate(index, indexfunc)
        indexes[param] = index
        
    return db, indexes

dbenv = open(HOME)
db, indexes = opendb(dbenv, "test")
count = 0

while True:
    print "\n\n========== Count: %s"%count
    rec = {"name":uuid.uuid1().hex, "hello":"goodbye", "time":time.time()}
    for i in range(10):
        rec['test_%s'%i] = random.random()
    s = bsddb3.db.DB_TXN_SNAPSHOT

    print "Start PUT"
    txn = dbenv.txn_begin()
    print rec
    print db.get(rec['name'], txn=txn, flags=bsddb3.db.DB_RMW)
    db.put(rec['name'], json.dumps(rec), txn=txn)
    print indexes['name'].get(rec['name'], txn=txn)
    txn.commit()

    print "Start GET"
    txn = dbenv.txn_begin(flags=s) #  flags=s
    keys = db.keys(txn)
    print "keys: %s"%len(keys)
    assert rec['name'] in keys
    indexes['name'].get(rec['name'], txn=txn)
    txn.commit()

    count += 1
    
    
