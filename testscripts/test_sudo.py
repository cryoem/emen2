import collections

import emen2.db
db = emen2.db.opendb()

with db:
	db._login("anonymous","")
	print db.checkcontext()
	
	rootctx = db._db._sudo(txn=db._gettxn())
	print rootctx
	
	print "Check admin?"
	print db.checkadmin()
	print rootctx.checkadmin()