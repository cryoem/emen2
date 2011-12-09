import time
import emen2.db
db = emen2.db.opendb(admin=True)
with db:
	txn = db._txn
	ctx = db._ctx
	# print db.finduser(name_last='rees', name_first='ian')
	# print db.finduser(record=137)
	# print db.finduser(name='ian')
	print db.findvalue('ctf_bfactor')
