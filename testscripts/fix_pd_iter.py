import collections
import emen2.db
db = emen2.db.opendb()

# set([u'binaryimage', u'links', u'int', u'text', u'float', u'datetime', u'boolean', u'stringlist', u'binary', u'comments', u'intlistlist', 'intlist', u'string', u'choice', u'user', u'groups', u'rectype', 'none', u'choicelist', 'name', u'acl', u'userlist', u'recid', u'e2l-float-list', u'history'])

convert = {
	'links':'links',
	'stringlist':'string',
	'binary':'binary',
	'comments':'comments',
	'intlist':'int',
	'intlistlist':'coordinate',
	'groups':'groups',
	'userlist':'user',
	'e2l-float-list':'float',
	'history':'history',
	'choicelist':'choice',
	'acl':'acl'
}



with db:
	ctx = db._getctx()
	txn = db._gettxn()
	pds = db.getparamdef(db.getparamdefnames())
	byvt = collections.defaultdict(set)
	for i in pds:
		byvt[i.vartype].add(i)

	# for k,v in byvt.items(): print "\n", k, v

	print "Initializing pd.iter to False"
	for pd in pds:
		pd.__dict__['iter'] = False
	
	for old, new in convert.items():
		for pd in byvt.get(old, []):
			print "Converting %s from %s to %s"%(pd.name, old, new)
			pd.__dict__['iter'] = True
			pd.__dict__['vartype'] = new
			
	for pd in byvt.get('binaryimage'):
		print "Changing %s from binaryimage to binary, non-iter"%pd.name
		pd.__dict__['iter'] = False
		pd.__dict__['vartype'] = 'binary'
			
	print "Committing"
	for pd in pds:
		db._db.bdbs.paramdef.put(pd.name, pd, txn=txn)
		