import os
import collections
import emen2.db
db = emen2.db.opendb(admin=True)

with db:
	ctx = db._getctx()
	txn = db._gettxn()
	for name, bin in db._db.dbenv["binary"].iteritems(txn=txn):
		bin.setContext(ctx)
		record = bin.get('record')
		creator = 'root'
		creationtime = '1970/01/01'

		if not bin.get('filesize'):
			print 'Checking filepath'
			size = 0
			fp = '/Users/irees/emen2/testscripts/fix_comments.py'
			try:
				size = os.path.getsize(fp)
			except:
				print "Couldnt read:", fp
				pass
			
			print "Setting size to", size
			bin.__dict__['filesize'] = size
		else:
			print 'Already had filesize:', bin.get('filesize')
		
		if bin.get('record'):
			rec = db._db.dbenv["record"].get(record, txn=txn)
			creator = rec['creator']
			creationtime = rec['creationtime']
			if creator.startswith('http'):
				creator = 'root'
		else:
			bin.__dict__['record'] = 0
			
		if not bin.get('creator'):	
			bin.__dict__['creator'] = creator
			bin.__dict__['creationtime'] = creationtime
		
		print bin.name
		# db._db.dbenv["binary"].put(bin.name, bin, txn=txn)
		
