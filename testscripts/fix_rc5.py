import emen2.db.admin
db = emen2.db.admin.opendb()

def convert_rels(db):
	"""Rels are now regular indexes; parents/children primarily stored inside record
	Convert an existing db to this format
	"""
	
	with db:
		txn = db._gettxn()
		for keytype in ['paramdef', 'recorddef', 'record']:
			bdb = db._db.bdbs.keytypes[keytype]
			pc = bdb.getindex('parents')
			cp = bdb.getindex('children')
			#for name, rec in bdb.iteritems(txn=txn):
			for name in bdb.keys(txn=txn):
				rec = bdb.get(name, txn=txn)
				rec.__dict__['parents'] = pc.get(name, set(), txn=txn)
				rec.__dict__['children'] = cp.get(name, set(), txn=txn)
				print name, rec['parents'], rec['children']
				bdb.put(name, rec, txn=txn)
			print "Done with", keytype
		print "Done with everything"
	


def convert_bdocounter(db):
	"""Convert old style bdocounter to new sequenced bdo db"""

	with db:
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

			bdb.delete()

			# print "Putting: ", str(i), str(dmax)
			seqdb.put(str(i), str(dmax+1), txn=txn)	
	
	
def convert_bdorecid(db):
	"""Convert 'recid' attribute to 'record' attribute; e.g. like User"""
	with db:
		ctx = db._getctx()
		txn = db._gettxn()
		bdb = db._db.bdbs.binary
		
		for i in bdb.keys(txn=txn):
			bdo = bdb.get(i, txn=txn)
			try:
				record = bdo.__dict__['recid']
				bdo.__dict__['record'] = record
				print "Updating %s to %s"%(bdo.name, record)
				bdb.put(bdo.name, bdo, txn=txn)
			except:
				print "Failed:", i
			
			


# vtm = emen2.db.datatypes.VartypeManager()
# 
# propfix = {
# }
# import collections
# ret = collections.defaultdict(set)
# 
# with db:
# 	for pd in db.getparamdef(db.getparamdefnames()):
# 
# 		if pd.property and pd.property != 'None':
# 			prop = vtm.getproperty(pd.property)
# 			if pd.defaultunits and pd.defaultunits not in prop.units:
# 				print pd.name, pd.defaultunits, prop.units
# 				ret[pd.property].add(pd.defaultunits)
# 
# 		# if pd.defaultunits:
# 		# 	print pd.name, pd.defaultunits, pd.property			
# 		#if pd.property or pd.defaultunits:
# 		#	print pd.name, pd.property, pd.defaultunits
# 
# 
# print "------"
# for k,v in ret.items():
# 	print k, v
