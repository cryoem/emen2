import emen2.db.admin
db = emen2.db.config.opendb()


import emen2.db.record
import emen2.db.user
import emen2.db.group

import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.binary



#################################
# Pickle..
#################################

def other_setstate(self, d):
	if not d.has_key('modifyuser'):
		d['modifyuser'] = d['creator']
	if not d.has_key('modifytime'):
		d['modifytime'] = d['creationtime']
	
	return self.__dict__.update(d)


emen2.db.paramdef.ParamDef.__setstate__ = other_setstate
emen2.db.recorddef.RecordDef.__setstate__ = other_setstate
emen2.db.binary.Binary.__setstate__ = other_setstate




def user_setstate(self, d):
	print "Updating user"
	
	if d.has_key('username'):
		d['name'] = d.pop('username')
	d['_userrec'] = {}
	d['_displayname'] = d['name']
	d['_groups'] = set()
	
	if not d.has_key('modifyuser'):
		d['modifyuser'] = d['creator']
	if not d.has_key('modifytime'):
		d['modifytime'] = d['creationtime']
	
	return self.__dict__.update(d)


emen2.db.user.User.__setstate__ = user_setstate



def group_setstate(self, d):
	print "Updating group"

	# Backwards compatibility..
	# This became a regular attribute, instead of self.__permissions
	if d.has_key('_Group__permissions'):
		d['permissions'] = d.pop('_Group__permissions', None)

	# I added some additional attributes..
	if not 'groups' in d:
		d['groups'] = set(['anonymous'])
	if not 'disabled' in d:
		d['disabled'] = False
	if not 'privacy' in d:
		d['privacy'] = 0

	if not d.has_key('modifyuser'):
		d['modifyuser'] = d['creator']
	if not d.has_key('modifytime'):
		d['modifytime'] = d['creationtime']


	return self.__dict__.update(d)



emen2.db.group.Group.__setstate__ = group_setstate




def record_setstate(self, d):
	print "Updating record"
	
	# Backwards compatibility..
	if d.has_key('_params'):
		d['params'] = d.pop('_params')
	
	if d.has_key('_Record__params'):			
		d["modifyuser"] = d["_Record__params"].pop("modifyuser", None)
		d["modifytime"] = d["_Record__params"].pop("modifytime", None)
		d["uri"] = d["_Record__params"].pop("uri", None)

		d["params"] = d["_Record__params"]
		d["history"] = d["_Record__history"]
		d["comments"] = d["_Record__comments"]
		d["permissions"] = d["_Record__permissions"]
		d["groups"] = d["_Record__groups"]

		d["creator"] = d["_Record__creator"]
		d["creationtime"] = d["_Record__creationtime"]
		d["parents"] = set()
		d["children"] = set()

		for i in ["_Record__ptest", 
			"_Record__ptest", 
			"_Record__params", 
			"_Record__history", 
			"_Record__comments", 
			"_Record__permissions", 
			"_Record__groups", 
			"_Record__creator", 
			"_Record__creationtime"]:
			try:
				del d[i]
			except:
				pass		
	
	# recid -> 'name'.
	if d.has_key('recid'):
		d['name'] = d.pop('recid')

	if not d.has_key('modifyuser'):
		d['modifyuser'] = d['creator']
	if not d.has_key('modifytime'):
		d['modifytime'] = d['creationtime']

	return self.__dict__.update(d)


emen2.db.record.Record.__setstate__ = record_setstate




def convert_rels(db):
	"""Rels are now regular indexes; parents/children primarily stored inside record
	Convert an existing db to this format
	"""
	txn = db._gettxn()
	for keytype in ['paramdef', 'recorddef', 'record']:
		bdb = db._db.bdbs.keytypes[keytype]
		pc = bdb.getindex('parents', txn=txn)
		cp = bdb.getindex('children', txn=txn)
		#for name, rec in bdb.iteritems(txn=txn):
		for name in bdb.keys(txn=txn):
			rec = bdb.get(name, txn=txn)
			rec.__dict__['parents'] = pc.get(name, set(), txn=txn)
			rec.__dict__['children'] = cp.get(name, set(), txn=txn)
			# print name, rec['parents'], rec['children']
			bdb.put(name, rec, txn=txn)
		print "Done with", keytype
	print "Done with everything"
	


def convert_pickle_other(db):
	ctx = db._getctx()
	txn = db._gettxn()
	for keytype in ['group', 'user']:
		print "Updating keytype", keytype
		bdb = db._db.bdbs.keytypes[keytype]
		for name in bdb.keys(txn=txn):
			rec = bdb.get(name, txn=txn)
			bdb.put(rec.name, rec, txn=txn)
	print "Done"


def convert_bdocounter(db):
	"""Convert old style bdocounter to new sequenced bdo db"""
	ctx = db._getctx()
	txn = db._gettxn()
	bdb = db._db.bdbs.binary
	seqdb = db._db.bdbs.binary.sequencedb

	for i in bdb.keys(txn=txn):
		d = bdb.get(i, txn=txn)
		dmax = max(d.keys())
		print "Counter is for %s is %s"%(i, dmax)
		for bdo in d.values():
			if bdo.__dict__.has_key('recid'):
				bdo.__dict__['record'] = bdo.__dict__['recid']
				del bdo.__dict__['recid']
			
			# print bdo.name
			bdb.put(bdo.name, bdo, txn=txn)

		bdb.delete(i, txn=txn)

		# print "Putting: ", str(i), str(dmax)
		seqdb.put(str(i), str(dmax+1), txn=txn)	
	


def add_paramdefs(db):
	pd = db.newparamdef(name='filename', vartype='string')
	db.putparamdef(pd)
	
	pd = db.newparamdef(name='name', vartype='name')
	pd.immutable = True
	pd.indexed = False
	db.putparamdef(pd)
	
	pd = db.newparamdef(name='keytype', vartype='string')
	pd.immutable = True
	pd.indexed = False
	db.putparamdef(pd)



with db:
	add_paramdefs(db)
	convert_pickle_other(db)
	convert_rels(db)
	convert_bdocounter(db)
