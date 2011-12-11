import emen2.db
db = emen2.db.opendb(admin=True)


with db:
	ctx = db._ctx
	txn = db._txn
	for i in ['user', 'group', 'paramdef', 'recorddef', 'record']:
		db._db.bdbs.keytypes[i].rebuild_indexes(ctx=ctx, txn=txn)
