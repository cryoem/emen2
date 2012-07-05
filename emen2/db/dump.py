import collections

import jsonrpc.jsonutil
import emen2.db
import emen2.util.listops


class Dumper(object):
	
	keytypes = ['paramdef', 'recorddef', 'user', 'group', 'binary', 'record']
	
	def __init__(self, db):
		self.db = db
		self._ref_pds = {}
		self._ref_vts = collections.defaultdict(set)
		
	def dump(self, names=None, keytype='record', **kwargs):
		# Query
		kwargs['keytype'] = keytype
		names = names or self.db.query(**kwargs)['names']
		print "Starting with:"
		print len(names)
		keys = collections.defaultdict(set)
		keys[keytype] |= set(names)

		# Find referenced items.
		for chunk in emen2.util.listops.chunk(keys[keytype], count=1000):
			items = self.db.get(chunk, keytype=keytype)
			print "Processing: %s ... %s"%(items[0].name, items[-1].name)
			# Find paramdefs that reference other items..
			self._findrefs(items)
			# Find other items..
			for kt in self.keytypes:
				keys[kt] |= getattr(self, '_find_%s'%kt)(items)

		return keys
		
	def write(self, keys, outfile='dump.json', uri=None):
		f = open(outfile, 'w')
		for keytype in self.keytypes:
			for chunk in emen2.util.listops.chunk(keys.get(keytype, []), count=100):
				items = self.db.get(chunk, keytype=keytype)
				for item in items:
					if uri:
						item.__dict__['uri'] = '%s/%s/%s'%(uri, keytype, item.name)
					print "%s: %s"%(item.keytype, item.name)
					f.write(jsonrpc.jsonutil.encode(item))
					f.write('\n')
		f.close()
		return outfile		

	def _findrefs(self, items):
		# Get the referencing vartypes from the items.
		pds = self._find_paramdef(items)
		for param in pds - set(self._ref_pds.keys()):
			pd = self.db.get(param, key='paramdef')
			if pd.vartype in self.keytypes:
				self._ref_pds[pd.name] = pd.vartype
				self._ref_vts[pd.vartype].add(pd.name)
	
	def _findvalues(self, vartypes, items):
		# Get the values referenced by a vartype from the items.
		ret = set()
		pds = set()
		for vartype in vartypes:
			pds |= self._ref_vts[vartype]
		for pd in pds:
			pd = self.db.paramdef.get(pd)
			if pd.iter:
				for item in items:
					ret |= set(item.get(pd.name, []))
			else:
				for item in items:
					ret.add(item.get(pd.name))
		ret -= set([None])
		return ret

	def _find_paramdef(self, items):
		r = set()
		for rec in items:
			r |= set(rec.keys())
		return r

	def _find_record(self, items):
		return self._findvalues(['record'], items)
			
	def _find_recorddef(self, items):
		return self._findvalues(['recorddef'], items)
		
	def _find_user(self, items):
		return self._findvalues(['user'], items)
				
	def _find_group(self, items):
		return self._findvalues(['group'], items)

	def _find_binary(self, items):
		return self._findvalues(['binary'], items)





class DumpOptions(emen2.db.config.DBOptions):
	def parseArgs(self, infile):
		self['infile'] = infile


if __name__ == "__main__":
	import emen2.db
	db = emen2.db.opendb(admin=True)
	dumper = Dumper(db=db)
	keys = dumper.dump(c=[['groups','==','publish']])
	keys['paramdef'] = db.paramdef.names()
	keys['user'] = db.user.names()
	dumper.write(keys, uri="http://ncmidb.bcm.edu")
	
	
	
