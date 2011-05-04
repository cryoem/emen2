# This Python file is encoding:UTF-8 Encoded

import os

#################################
# Pickle..
#################################

def other_setstate(self, d):
	print "Updating.."
	if not d.has_key('modifyuser'):
		d['modifyuser'] = d.get('creator')
	if not d.has_key('modifytime'):
		d['modifytime'] = d.get('creationtime')
	print d	
	return self.__dict__.update(d)



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



def monkeypatch():
	print "Applying setstate patches"
	import emen2.db.record
	import emen2.db.user
	import emen2.db.group
	import emen2.db.paramdef
	import emen2.db.recorddef
	import emen2.db.binary
	
	emen2.db.paramdef.ParamDef.__setstate__ = other_setstate
	emen2.db.recorddef.RecordDef.__setstate__ = other_setstate
	emen2.db.binary.Binary.__setstate__ = other_setstate

	emen2.db.user.User.__setstate__ = user_setstate
	emen2.db.record.Record.__setstate__ = record_setstate
	emen2.db.group.Group.__setstate__ = group_setstate



def convert_rels(db):
	"""Rels are now regular indexes; parents/children primarily stored inside record
	Convert an existing db to this format
	"""
	print "Converting relationships"
	txn = db._gettxn()
	for keytype in ['paramdef', 'recorddef', 'record']:
		bdb = db._db.bdbs.keytypes[keytype]
		parents = bdb.getindex('parents', txn=txn)
		children = bdb.getindex('children', txn=txn)
		#for name, rec in bdb.iteritems(txn=txn):
		for name in bdb.keys(txn=txn):
			rec = bdb.get(name, txn=txn)
			rec.__dict__['parents'] = parents.get(rec.name, set(), txn=txn)
			rec.__dict__['children'] = children.get(rec.name, set(), txn=txn)
			print name, rec['parents'], rec['children']
			bdb.put(name, rec, txn=txn)
		print "Done with", keytype
	print "Done with everything"
	


def convert_pickle_other(db):
	print "Converting other items"
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


def defs_rename(db):
	ctx = db._getctx()
	txn = db._gettxn()
	root_parameter = db.getparamdef("root_parameter")
	root = db.newparamdef(name='root', vartype='none')
	root.desc_short = "Root Parameter"
	root.children |= root_parameter.children
	root_parameter.children = set()
	db.putparamdef(root)
	db.putparamdef(root_parameter)
	db._db.bdbs.paramdef.delete('root_parameter', txn=txn)

	
	root_protocol = db.getrecorddef('root_protocol')
	root = db.newrecorddef(name='root', mainview='Root Protocol')
	root.desc_short = 'Root Protocol'
	root.children |= root_protocol.children
	root_protocol.children = set()
	db.putrecorddef(root)
	db.putrecorddef(root_protocol)
	db._db.bdbs.recorddef.delete('root_protocol', txn=txn)



def paramdefs_props(db):
	import emen2.db.datatypes
	paramdefs = db.getparamdef(db.getparamdefnames())
	crecs = []
	fixmap = {
		'pixels':'pixel',
		'p/ml':'pfu',
		'kv':'kV',
		'mv':'mV',
		'e/A2':'e/A^2',
		'amp':'A',
		'ul':'uL',
		'A':u'Å',
		'K':'count',
		'C':'degC',
		'A/pix':u'Å/pixel',
		'KDa':'kDa'
	}

	txn = db._gettxn()

	for pd in paramdefs:
		vt = emen2.db.datatypes.VartypeManager(db=db)
		if pd.property:
			try:
				prop = vt.getproperty(pd.property)
			except:
				print pd.name, pd.property
				pd.__dict__['property'] = None

			if pd.name == 'temperature_specimen':
				pd.__dict__['property'] = 'temperature'
				pd.__dict__['defaultunits'] = 'K'

			pd.__dict__['defaultunits'] = fixmap.get(pd.defaultunits, pd.defaultunits)	
			# if pd.defaultunits and pd.defaultunits not in prop.units:
			# 	print pd.name, pd.property, pd.defaultunits, prop.units		
			db._db.bdbs.paramdef.put(pd.name, pd, txn=txn)
	


def main(db):
	monkeypatch()
	add_paramdefs(db)
	convert_pickle_other(db)
	convert_rels(db)
	convert_bdocounter(db)
	defs_rename(db)
	paramdefs_props(db)


def rename():
	import bsddb3
	import emen2.db.config
	import emen2.db.database
	
	# manually open the database for renaming
	# this does not open the db files
	dbenv = emen2.db.database.EMEN2DBEnv(maintenance=True)

	rename = {
		"security/contexts.bdb": "context/context.bdb",
		
		"security/newuserqueue.bdb": "newuser/newuser.bdb",
		
		"security/users.bdb": "user/user.bdb",
		"index/security/usersbyemail.bdb": "user/index/email.index",

		"security/groups.bdb": "group/group.bdb",
		"index/security/groupsbyuser.bdb": "group/index/permissions.index",
		
		"main/workflow.bdb": "workflow/workflow.bdb",
		
		"main/bdocounter.bdb": "binary/binary.bdb",
		"index/bdosbyfilename.bdb": "binary/index/filename.index",
		#"main/bdocounter.sequence.bdb": "binary/binary.sequence.bdb",
		
		"main/records.bdb": "record/record.bdb",
		"main/records.sequence.bdb": "record/record.sequence.bdb",
		"main/records.cp2.bdb": "record/index/parents.index",
		"main/records.pc2.bdb": "record/index/children.index",
		"index/indexkeys.bdb": "record/index/indexkeys.bdb",
		
		"main/paramdefs.bdb": "paramdef/paramdef.bdb",
		"main/paramdefs.cp2.bdb": "paramdef/index/parents.index",
		"main/paramdefs.pc2.bdb": "paramdef/index/children.index",

		"main/recorddefs.bdb": "recorddef/recorddef.bdb",
		"main/recorddefs.cp2.bdb": "recorddef/index/parents.index",
		"main/recorddefs.pc2.bdb": "recorddef/index/children.index",
	}
	
	parampath = os.path.join(dbenv.path, "data/index/params")
	for i in os.listdir(parampath):
		b = os.path.splitext(i)[0]
		rename['index/params/%s'%i] = 'record/index/%s.index'%b
	

	txn = dbenv.newtxn()
	for k,v in rename.items():
		newdir = os.path.dirname(os.path.join(dbenv.path, "data", v))
		try:
			os.makedirs(newdir)
		except:
			pass
			# print "couldn't make %s"%newdir
		
		print "Renaming:", k, v
		dbenv.dbenv.dbrename(file=k, database=None, newname=v, txn=txn)
		# print k,v

	txn.commit()
		


if __name__ == "__main__":
	import emen2.db.config
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--rename', action="store_true", help="Rename files")
	(options, args) = dbo.parse_args()
	if options.rename:
		rename()
	else:
		db = dbo.opendb()
		with db:
			main(db)
	
	
	
	
	
	
	
	
	
