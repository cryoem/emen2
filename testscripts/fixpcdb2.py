import cPickle as pickle
from testc import *

db._starttxn()

txn = db._DBProxy__txn
ddb = db._DBProxy__db


pds = {}
for i in ddb.bdbs.paramdefs.pcdb2.keys(txn):
	pds[i] = map(pickle.loads, map(str, ddb.bdbs.paramdefs.pcdb2.get(i, txn)))
	
rds = {}
for i in ddb.bdbs.recorddefs.pcdb2.keys(txn):
	rds[i] = map(pickle.loads, map(str, ddb.bdbs.recorddefs.pcdb2.get(i, txn)))
	

print pds
print rds


ddb.bdbs.recorddefs.pcdb2.truncate(txn)
ddb.bdbs.paramdefs.pcdb2.truncate(txn)

ddb.bdbs.recorddefs.cpdb2.truncate(txn)
ddb.bdbs.paramdefs.cpdb2.truncate(txn)

for k,v in pds.items():
	for v2 in v:
		db.pclink(k, v2, keytype="paramdef")

for k,v in rds.items():
	for v2 in v:
		db.pclink(k, v2, keytype="recorddef")

db._committxn()
#db._aborttxn()