# $Id$
"""
Core Database classes
These serve as wrappers around Berkeley DB / bsddb3 BTrees. 
"""

import cPickle as pickle
import sys
import time
import weakref
import collections
import copy
import bsddb3
import traceback

import emen2.db.config
g = emen2.db.config.g()
import emen2.util.listops


try:
	import emen2.db.bulk
	bulk = emen2.db.bulk
	g.warn("Note: using EMEN2-BerkeleyDB bulk access module")
except:
	bulk = None


# Berkeley DB wrapper classes
class BTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary.
	Key may be and data may be any pickle-able Python type, but unicode/int/float key and data
	types are also supported with some acceleration."""

	def __init__(self, filename, dbenv, keytype=None, datatype=None, cfunc=True, bdbs=None, autoopen=True):
		"""Main BDB BTree wrapper"""
		
		# Base filename; the actual BDBs will be filename.bdb, filename/index.bdb, etc.
		self.filename = filename 

		# Berkeley DB Environment
		self.dbenv = dbenv 
		
		# EMEN2DBEnv
		self.bdbs = bdbs 

		# BDB Handle
		self.bdb = None
		
		# What are we storing?
		self.setkeytype(keytype, cfunc=cfunc)
		self.setdatatype(datatype)
		
		# Sequence database
		self.sequence = False
		
		# Child databases
		self.index = {}		

		# Flags to set on opened DB's
		self.DBOPENFLAGS = bsddb3.db.DB_CREATE | bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_THREAD
		self.DBSETFLAGS = []
		
		# Subclass init
		self.init()
		
		# Open the database
		if autoopen:
			self.open()


	def init(self):
		pass
		
		
	def __str__(self):
		return "<emen2.db.btrees2.BTree instance: %s>"%self.filename


	def __del__(self):
		self.close()
			


	#########################################
	# load/dump methods for keys and data
	#########################################

	# Don't touch this!!!
	def cfunc_numeric(self, k1, k2):
		if not k1:
			k1 = 0
		else:
			k1 = self.loadkey(k1)

		if not k2:
			k2 = 0
		else: 
			k2 = self.loadkey(k2)

		return cmp(k1, k2)


	def _pickledump(self, data):
		return pickle.dumps(data)
		
		
	def _pickleload(self, data):
		if data != None: return pickle.loads(data)


	def setkeytype(self, keytype, cfunc=True):	
		if self.bdb:
			raise Exception, "Cannot set keytype after DB has been opened"

		keytype = keytype or 's'

		if keytype not in ('s', 'd', 'f'):
			raise ValueError, "Invalid keytype: %s. Supported: s(tring), d(ecimal), f(loat)"%keytype

		self.keytype = keytype

		self.cfunc = None
		if cfunc and self.keytype in ('d', 'f'):
			self.cfunc = self.cfunc_numeric

		# Default
		self.typekey = unicode
		self.dumpkey = lambda x:x.encode('utf-8')
		self.loadkey = lambda x:x.decode('utf-8')
		
		# ian: todo: convert records bdb to use new d format for keys
		if self.keytype == 'd':
			self.typekey = int
			self.dumpkey = str
			self.loadkey = int

		elif self.keytype == 'f':
			self.typekey = float
			self.dumpkey = self._pickledump
			self.loadkey = self._pickleload
			

	def setdatatype(self, datatype, dataclass=None):
		if self.bdb:
			raise Exception, "Cannot set datatype after DB has been opened"
		
		datatype = datatype or 'p'
		
		if datatype not in ('s', 'd', 'f', 'p'):
			raise ValueError, "Invalid datatype: %s. Supported: s(tring), d(ecimal), f(loat), p(ickle)"%datatype
		
		self.datatype = datatype

		# Default
		self.typedata = lambda x:x
		self.dumpdata = self._pickledump
		self.loaddata = self._pickleload

		if self.datatype == 'd':
			self.typedata = int
			self.dumpdata = str
			self.loaddata = int
			
		elif self.datatype == 'f':
			self.typedata = float
		
		elif self.datatype == 's':
			self.typedata = unicode
			self.dumpdata = lambda x:x.encode('utf-8')
			self.loaddata = lambda x:x.decode('utf-8')			
						
		elif self.datatype == 'p':
			# This record stores a class
			self.typedata = dataclass
			
			
		
	#########################################
	# Indexes.
	# You must provide an openindex method.
	#########################################

	def openindex(self, param, txn=None):
		# raise KeyError, "No index available for %s"%param
		return


	def getindex(self, param, txn=None):
		ind = self.index.get(param)
		if ind:
			return ind

		ind = self.openindex(param, txn=txn)
		self.index[param] = ind
		return ind


	def closeindex(self, param):
		ind = self.index.get(param)
		if ind:
			ind.close()
			self.index[param] = None



	#################
	# DB methods
	#################

	def open(self):	
		if self.bdb:
			raise Exception, "DB already open"

		# Create the DB handle and set flags
		self.bdb = bsddb3.db.DB(self.dbenv)
		for flag in self.DBSETFLAGS:
			self.bdb.set_flags(flag)

		# Set a BTree sort method
		if self.cfunc:
			self.bdb.set_bt_compare(self.cfunc)

		# Open DB
		self.bdb.open(self.filename+'.bdb', dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)

		# If this DB supports sequence assignment..
		if self.sequence:
			self.sequencedb = bsddb3.db.DB(self.dbenv)
			self.sequencedb.open(self.filename+'.sequence.bdb', dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)


	def close(self):
		"""Close BDBs and cleanup"""
		if self.bdb is None:
			return			
		for k in self.index:
			self.closeindex(k)
		if self.sequence:
			self.sequencedb.close()	
			
		self.bdb.close()
		self.bdb = None
		

	def sync(self, flags=0):
		"""Flush BDB cache to disk"""
		if self.bdb is None:
			return
		for k,v in self.index.items():
			v.sync()
		if self.sequence:
			self.sequencedb.sync()
			
		self.bdb.sync()



	############################
	# Mapping methods. Should be generators?
	############################

	def keys(self, txn=None):
		return map(self.loadkey, self.bdb.keys(txn))


	def values(self, txn=None):
		return [self.loaddata(x) for x in self.bdb.values(txn)]


	def items(self, txn=None):
		return map(lambda x:(self.loadkey(x[0]),self.loaddata(x[1])), self.bdb.items(txn)) #txn=txn


	def iteritems(self, txn=None, flags=0):
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			yield (self.loadkey(pair[0]), self.loaddata(pair[1]))
			pair = cursor.next_nodup()
		cursor.close()


	def has_key(self, key, txn=None):
		return self.bdb.has_key(self.dumpkey(key), txn=txn) #, txn=txn


	def exists(self, key, txn=None, flags=0):
		"""Checks to see if key exists in BDB"""
		if key == None:
			return False
		return self.bdb.exists(self.dumpkey(key), txn=txn, flags=flags)



	############################
	# Read
	############################

	def get(self, key, default=None, filt=True, txn=None, flags=0):
		"""Same as dict.get, with txn"""
		# Check BDB
		d = self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		if d:
			return d
		if not filt:
			raise KeyError, "No such key %s"%(key)
		return default


	############################
	# Write
	############################

	def put(self, key, data, txn=None, flags=0):
		"""Write key/value, with txn."""		
		g.log("%s.put: %s"%(self.filename, key), 'COMMIT')
		return self.bdb.put(self.dumpkey(key), self.dumpdata(data), txn=txn, flags=flags)			


	# Dangerous!
	def truncate(self, txn=None, flags=0):
		"""Truncate BDB (e.g. 'drop table')"""
		self.bdb.truncate(txn=txn)
		g.log("%s.truncate"%self.filename, 'COMMIT')


	# Also dangerous!	
	def delete(self, key, txn=None, flags=0):
		if self.bdb.exists(self.dumpkey(key), txn=txn):
			ret = self.bdb.delete(self.dumpkey(key), txn=txn, flags=flags)
			g.log("%s.delete: %s"%(self.filename, key), 'COMMIT')
			return ret



	###############################
	# Sequence (this is just used by Record for now)
	###############################

	def get_max(self, txn=None):
		if not self.sequence:
			return

		sequence = self.sequencedb.get("sequence", txn=txn)
		if sequence == None: sequence = 0
		val = int(sequence)
		return val
		# sequence = bsddb3.db.DBSequence(self.sequencedb)
		# sequence.open("sequence", flags=bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD, txn=txn)
		# val = sequence.stat()['current']
		# sequence.close()
		#get_range()[1]


	def get_sequence(self, delta=1, key='sequence', txn=None):
		if not self.sequence:
			return

		# This can handle any number of sequences -- e.g. for binary dates.
		# 'sequence' is the default key.
		# print "Setting sequence += %s, txn: %s, newtxn: %s, flags:%s"%(delta, txn, newtxn, bsddb3.db.DB_RMW)
		val = self.sequencedb.get(key, txn=txn, flags=bsddb3.db.DB_RMW)
		if val == None:
			val = 0
		val = int(val)
		self.sequencedb.put(key, str(val+delta), txn=txn)
		g.log("%s.sequencedb.put: %s"%(self.filename, val+delta), 'COMMIT')
		return val

		# BDB DBSequence was never very stable.
		# sequence = bsddb3.db.DBSequence(self.sequencedb)
		# sequence.open("sequence", flags=bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD, txn=txn)
		# if not txn or delta < 1:
		# 	raise ValueError, "delta and txn requried for sequence increment"
		# val = sequence.get(delta=delta, txn=txn)
		# sequence.close()


	def update_sequence(self, items, txn=None):
		namemap = {}
		for i in items:
			if not self.exists(i.name, txn=txn):
				namemap[i.name] = i.name
		return namemap



	##############################
	# Load built-in items
	##############################
	
	# Private method to load config
	# def load_builtins(self, t):
	# 	infile = emen2.db.config.get_filename('emen2', 'skeleton/%s.json'%t)
	# 	f = open(infile)
	# 	ret = emen2.util.jsonutil.decode(f.read())
	# 	f.close()
	# 	for k in ret:
	# 		k = self.datatype(k)
	# 		self.builtins[k.get('name')] = k





class IndexBTree(BTree):

	def init(self):
		self.DBSETFLAGS = [bsddb3.db.DB_DUP, bsddb3.db.DB_DUPSORT]
		self.setbulkmode(True)
		super(IndexBTree, self).init()


	def setbulkmode(self, bulkmode):
		# use acceleration module if available
		self._get_method = self._get_method_nonbulk
		if bulk:
			if bulkmode:
				self._get_method = emen2.db.bulk.get_dup_bulk
			else:
				self._get_method = emen2.db.bulk.get_dup_notbulk


	def removerefs(self, key, items, txn=None):
		if not items: return []

		delindexitems = []

		cursor = self.bdb.cursor(txn=txn)

		key = self.typekey(key)
		items = map(self.typedata, items)

		dkey = self.dumpkey(key)
		ditems = map(self.dumpdata, items)

		for ditem in ditems:
			if cursor.set_both(dkey, ditem):
				cursor.delete()

		if not cursor.set(dkey):
			delindexitems.append(key)

		cursor.close()

		g.log("%s.removerefs: %s -> %s"%(self.filename, key, len(items)), 'INDEX')
		return delindexitems


	def addrefs(self, key, items, txn=None):
		if not items: return []

		addindexitems = []

		key = self.typekey(key)
		items = map(self.typedata, items)

		dkey = self.dumpkey(key)
		ditems = map(self.dumpdata, items)

		#print "new cursor"
		cursor = self.bdb.cursor(txn=txn)

		#print "cursor checking"
		if not cursor.set(dkey):
			addindexitems.append(key)

		for ditem in ditems:
			#print "cursor put %s %s"%(dkey, ditem)
			try:
				cursor.put(dkey, ditem, flags=bsddb3.db.DB_KEYFIRST)
			except bsddb3.db.DBKeyExistError, e:
				pass

		cursor.close()

		g.log("%s.addrefs: %s -> %s"%(self.filename, key, len(items)), 'INDEX')
		return addindexitems


	def _get_method_nonbulk(self, cursor, key, dt, flags=0):
		n = cursor.set(key)
		r = set() #[]
		m = cursor.next_dup
		while n:
			r.add(n[1])
			n = m()

		return set(self.loaddata(x) for x in r)


	_get_method = _get_method_nonbulk



	def get(self, key, default=None, cursor=None, txn=None, flags=0):
		# print "%s.get index/datatype:"%self.filename, key, self.datatype
		key = self.dumpkey(key)

		if cursor:
			r = self._get_method(cursor, key, self.datatype)

		else:
			cursor = self.bdb.cursor(txn=txn)
			r = self._get_method(cursor, key, self.datatype)
			cursor.close()

		# generator expressions will be less pain when map() goes away
		if bulk and self.datatype == 'p':
			r = set(self.loaddata(x) for x in r)

		return r


	def put(self, *args, **kwargs):
		raise Exception, "put not supported; use addrefs, removerefs"


	def keys(self, txn=None, flags=0):
		keys = set(map(self.loadkey, self.bdb.keys(txn)))
		return list(keys)


	def items(self, txn=None, flags=0):
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			data = self._get_method(cursor, pair[0], self.datatype)
			if bulk and self.datatype == "p":
				data = set(map(self.loaddata, data))
			ret.append((self.loadkey(pair[0]), data))
			pair = cursor.next_nodup()
		cursor.close()

		return ret


	def iteritems(self, minkey=None, txn=None, flags=0):
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			data = self._get_method(cursor, pair[0], self.datatype)
			if bulk and dt == "p":
				data = set(map(self.loaddata, data))
			yield (self.loadkey(pair[0]), data)
			pair = cursor.next_nodup()

		cursor.close()


	def iterfind(self, items, minkey=None, maxkey=None, txn=None, flags=0):
		"""Searches the index until it finds all specified items"""
		itemscopy = copy.copy(items)
		lenitems = len(itemscopy)

		processed = 0
		found = 0
		ret = {}

		dt = self.datatype or "p"
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			processed += 1
			data = self._get_method(cursor, pair[0], dt)
			if bulk and dt == "p":
				data = set(map(self.loaddata, data))

			c = data & itemscopy
			if c:
				itemscopy -= c
				found += len(c)				
				# print "processed %s keys, %s items left to go"%(processed, lenitems-found)
				# ret[self.loadkey(pair[0])] = c
				yield (self.loadkey(pair[0]), c)

			if found >= lenitems:
				break
			else:
				pair = cursor.next_nodup()

		# print "Done; processed %s keys"%processed
		cursor.close()		
		# return ret


	# 	def keys(self, mink=None, maxk=None, txn=None):
	# 		"""Returns a list of valid keys, mink and maxk allow specification of
	#  		minimum and maximum key values to retrieve"""
	# 		if mink == None and maxk == None:
	# 			return BTree.keys(self, txn)
	# 		return set(x[0] for x in self.items(mink, maxk, txn=txn))
	#
	#
	# 	def values(self, mink=None, maxk=None, txn=None):
	# 		"""Returns a single list containing the concatenation of the lists of,
	#  		all of the individual keys in the mink to maxk range"""
	# 		if mink == None and maxk == None: return BTree.values(self)
	# 		return reduce(set.union, (set(x[1] or []) for x in self.items(mink, maxk, txn=txn)), set())





# Context-aware BTree for DBO's

class DBOBTree(BTree):

	#################
	# New items..
	#################

	# Return a new instance of this BTree's datatype.
	# All arguments will be passed to the constructor.
	def new(self, *args, **kwargs):
		"""Return a new instance of the type of item this BTree stores.."""
		txn = kwargs.pop('txn', None) # don't pass the txn..
		name = kwargs.get('name')
		if name: 
			if self.exists(name, txn=txn):
				raise KeyError, "%s already exists"%name
		return self.typedata(*args, **kwargs)	



	##############################
	# Filtered context gets..
	##############################
	
	# Get an item and set Context
	def cget(self, key, filt=True, ctx=None, txn=None, flags=0):
		"""Same as dict.get, with txn"""
		r = self.cgets([key], txn=txn, ctx=ctx, filt=filt, flags=flags)
		if not r:
			return None
		return r[0]
		
		
	# Takes an iterable..
	def cgets(self, keys, filt=True, ctx=None, txn=None, flags=0):
		ret = []
		for key in self.expand(keys, ctx=ctx, txn=txn):
			try:
				d = self.get(key, filt=False, txn=txn, flags=flags)
				d.setContext(ctx)
				ret.append(d)
			except (emen2.db.exceptions.SecurityError, AttributeError, KeyError), e: # TypeError?
				if filt:
					pass
				else:
					raise
		return ret
		
			
	def expand(self, names, ctx=None, txn=None):
		"""See RelateBTree"""
		if not isinstance(names, set):
			names = set(names)
		return names


	# An alternative to .keys()
	def names(self, names=None, ctx=None, txn=None, **kwargs):
		if names is not None:
			if ctx.checkadmin():
				return names
			items = self.cgets(names, ctx=ctx, txn=txn)
			return set([i.name for i in items])
			
		return set(map(self.loadkey, self.bdb.keys(txn)))

		
	def validate(self, items, ctx=None, txn=None):
		return self.puts(items, commit=False, ctx=ctx, txn=txn)
		


	############################
	# Write
	############################		
	
	def cput(self, item, *args, **kwargs):
		ret = self.cputs([item], *args, **kwargs)
		if not ret:
			return None
		return ret[0]
		
	
	def cputs(self, items, clone=False, commit=True, indexonly=False, ctx=None, txn=None):
		t = emen2.db.database.gettime()
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)		
		# Return values
		crecs = []

		# Note: children/parents used to be handled specially,
		#	but now they are considered "more or less" regular params, with slightly tweaked indexes
		
		# Process the items
		for name, updrec in enumerate(items, start=1):
			# Get the name; use recid as a backup for compatibility for now..
			name = updrec.get('name') # or (name * -1)
			cp = set()
			
			# Get the existing item or create a new one. Security error will be raised.
			try:
				# Acquire the lock immediately (DB_RMW) because are we are going to change the record
				orec = self.get(name, txn=txn, flags=bsddb3.db.DB_RMW)
				orec.setContext(ctx)
				print type(orec.get('uri')), orec.get('uri')
				if orec.get('uri'):
					raise emen2.db.exceptions.SecurityError, "This is a read-only object"

			except (TypeError, AttributeError, KeyError), inst: 
				# AttributeError might have been raised if the key was the wrong type
				p = dict((k,updrec.get(k)) for k in self.typedata.param_required)
				orec = self.new(name=name, t=t, ctx=ctx, txn=txn, **p)
				cp.add('name')
			
			# Update the item.
			if clone:
				cp |= orec.clone(updrec, vtm=vtm, t=t)
			else:
				cp |= orec.update(updrec, vtm=vtm, t=t)			
			orec.validate() 

			# If values changed, cache those, and add to the commit list
			if cp:
				crecs.append(orec)

		# If we just wanted to validate the changes.
		if not commit:
			return crecs

		
		# Assign new names based on the DB sequence.
		namemap = self.update_sequence(crecs, txn=txn)
		
		# Calculate all changed indexes
		self.reindex(crecs, indexonly=indexonly, namemap=namemap, ctx=ctx, txn=txn)
		
		if indexonly:
			return

		# Commit "for real"
		for crec in crecs:
			self.put(crec.name, crec, txn=txn)

		g.log("Committed %s items"%(len(crecs)))
		
		return crecs	
		

	# Calculate and write index changes
	# if indexonly, assume items are new, to rebuild all params.
	def reindex(self, items, indexonly=False, namemap=None, ctx=None, txn=None):
		"""Update indexes"""
		ind = collections.defaultdict(list)
				
		# Get changes as param:([name, newvalue, oldvalue], ...)
		for crec in items:
			# Get the current record for comparison of updated values.
			# Use an empty dict for new records so all keys will seen as new (or if reindexing)
			orec = self.cget(crec.name, ctx=ctx, txn=txn) or {}
			if indexonly:
				orec = {}
			for param in crec.changedparams(orec):
				ind[param].append((crec.name, crec.get(param), orec.get(param)))
		
		# These are complex changes, so pass them off to different reindex method
		# _reindex_relink does nothing for base DBOBTree; see RelateBTree
		parents = ind.pop('parents', None)
		children = ind.pop('children', None)
		self._reindex_relink(parents, children, namemap=namemap, indexonly=indexonly, ctx=ctx, txn=txn)

		for k,v in ind.items():
			self._reindex_param(k, v, ctx=ctx, txn=txn)


	def _reindex_relink(self, parents, children, namemap=None, indexonly=False, ctx=None, txn=None):
		"""See RelateBTree"""
		return


	# reindex a single parameter
	def _reindex_param(self, param, changes, ctx=None, txn=None):
		# If nothing changed, skip.
		if not changes:
			return
		
		# If we can't access the index, skip. (Raise Exception?)
		ind = self.getindex(param, txn=txn)
		if ind == None:
			# print "No index for %s, skipping"%param
			return

		# Check that this key is currently marked as indexed
		pd = self.bdbs.paramdef.get(param, txn=txn)
		vtm = emen2.db.datatypes.VartypeManager()
		vt = vtm.getvartype(pd.vartype)

		# Process the changes into index addrefs / removerefs
		addindexkeys = []
		removeindexkeys = []
		addrefs, removerefs = vt.reindex(changes)
		# print "reindexing", pd.name
		# print "changes:", changes
		# print "addrefs:", addrefs
		# print "remove:", removerefs
		
		# Write!
		for oldval, recs in removerefs.items():
			# Not necessary to map temp names to final names, 
			# as reindexing is now done after assigning names
			removeindexkeys.extend(ind.removerefs(oldval, recs, txn=txn))

		for newval,recs in addrefs.items():
			addindexkeys.extend(ind.addrefs(newval, recs, txn=txn))
				
		# Update the index-index
		indk = self.index.get('indexkeys')
		if not indk or pd.name in ['parents', 'children']:
			return
		
		# Update index-index, a necessary evil..
		if removeindexkeys:
			indk.removerefs(pd.name, removeindexkeys, txn=txn)
		
		if addindexkeys:
			indk.addrefs(pd.name, addindexkeys, txn=txn)
	
	
	##############################
	# Delete and rename
	##############################
	

	# def rename(self, name, ctx=None, txn=None):
	# 	raise emen2.db.exceptions.SecurityError, "No permission to rename."








class RelateBTree(DBOBTree):
	"""BTree with parent/child/cousin relationships between keys"""

	def init(self):				
		c = IndexBTree(filename=self.filename+".pc2", keytype=self.keytype, datatype=self.keytype, cfunc=False, dbenv=self.dbenv, autoopen=False)
		c.setbulkmode(False)
		c.open()
		self.index['children'] = c
				
		p = IndexBTree(filename=self.filename+".cp2", keytype=self.keytype, datatype=self.keytype, cfunc=False, dbenv=self.dbenv, autoopen=False)
		p.setbulkmode(False)
		p.open()
		self.index['parents'] = p

		super(RelateBTree, self).init()


	###############################
	# Relationship methods
	###############################

	def expand(self, names, ctx=None, txn=None):
		"""Expand names, e.g. expanding * into children, or using an email address for a user"""
		if not isinstance(names, set):
			names = set(names)

		# Expand *'s
		remove = set()
		add = set()
		for key in (i for i in names if isinstance(i, basestring)):
			newkey = self.typekey(key.replace('*', ''))
			if key.endswith('*'):
				add |= self.children([newkey], recurse=-1, ctx=ctx, txn=txn).get(newkey, set())
			remove.add(key)
			add.add(newkey)

		names -= remove
		names |= add
		return names

	
	# Commonly used rel() variants
	def parenttree(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		return self.rel(names, recurse=recurse, rel='parents', tree=True, ctx=ctx, txn=txn, **kwargs)
	

	def childtree(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		return self.rel(names, recurse=recurse, rel='children', tree=True, ctx=ctx, txn=txn, **kwargs)


	def parents(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		return self.rel(names, recurse=recurse, rel='parents', ctx=ctx, txn=txn, **kwargs)


	def children(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		return self.rel(names, recurse=recurse, rel='children', ctx=ctx, txn=txn, **kwargs)
		
	
	# Siblings
	def siblings(self, name, ctx=None, txn=None, **kwargs):
		parents = self.rel([name], rel='parents', ctx=ctx, txn=txn)
		allparents = set()
		for k,v in parents.items():
			allparents |= v
		siblings = set()
		children = self.rel(allparents, ctx=ctx, txn=txn, **kwargs)
		for k,v in children.items():
			siblings |= v
		return siblings


	# Nice wrapper around the basic self.dfs. Checks permissions, return formats, etc..
	def rel(self, names, recurse=1, rel='children', tree=False, ctx=None, txn=None, **kwargs):
		result = {}
		visited = {}

		for i in names:
			result[i], visited[i] = self.dfs(i, rel=rel, recurse=recurse)
		
		# Flatten the dictionary to get all touched names
		allr = set()
		for v in visited.values():
			allr |= v
		
		# Filter by permissions (pass rectype= for optional Record filtering)
		allr = self.names(allr, ctx=ctx, txn=txn, **kwargs)

		# If Tree=True, we're returning the tree... Filter for permissions.
		if tree:
			outret = {}
			for k, v in result.iteritems():
				for k2 in v:
					outret[k2] = result[k][k2] & allr		
			return outret
		
		# Else we're just ruturning the total list of all children, keyed by requested record name
		for k in visited:
			visited[k] &= allr
		
		return visited


	def relink(self, parent, child, ctx=None, txn=None):
		pass


	# def pcrelink(self, remove, add, keytype="record", ctx=None, txn=None):
	# 	def conv(link):
	# 		pkey, ckey = link
	# 		if keytype=="record":
	# 			return int(pkey), int(ckey)
	# 		return unicode(pkey), unicode(ckey)
	# 	remove = set(map(conv, remove))
	# 	add = set(map(conv, add))		
	# 	common = remove & add
	# 	remove -= common
	# 	add -= common
	# 	self._link("pcunlink", remove, keytype=keytype, ctx=ctx, txn=txn)
	# 	self._link("pclink", add, keytype=keytype, ctx=ctx, txn=txn)


	def pclink(self, parent, child, ctx=None, txn=None):
		"""Create parent-child relationship"""
		self._putrel(parent, child, mode='addrefs', ctx=ctx, txn=txn)


	def pcunlink(self, parent, child, ctx=None, txn=None):
		"""Remove parent-child relationship"""
		self._putrel(parent, child, mode='removerefs', ctx=ctx, txn=txn)

	
	def _putrel(self, parent, child, mode='addrefs', ctx=None, txn=None):
		# Check that we have enough permissions to write to one item
		# Use raw get; manually setContext. Allow KeyErrors to raise.
		p = self.get(parent, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
		c = self.get(child, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
		perm = []
		try:
			p.setContext(ctx)
			perm.append(p.writable())
		except:
			pass
		try:
			c.setContext(ctx)
			perm.append(c.writable())
		except:
			pass
		
		if not any(perm):
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to add/remove relationship"
		
		# Transform into the right format for _reindex_relink..
		newvalue = set() | p.children # copy
		if mode == 'addrefs':
			newvalue |= set([c.name])
		elif mode == 'removerefs':
			newvalue -= set([c.name])
		
		self._reindex_relink([], [[p.name, newvalue, p.children]], ctx=ctx, txn=txn)


	# Handle the reindexing...
	def _reindex_relink(self, parents, children, namemap=None, indexonly=False, ctx=None, txn=None):
		""""Update relationships using the regular commit/cput method."""

		namemap = namemap or {}
		indc = self.getindex('children', txn=txn)
		indp = self.getindex('parents', txn=txn)
		if not indc or not indp:
			raise KeyError, "Relationships not supported"
			
		# print "parent changeset:", parents
		# print "children changeset:", children

		# Process change sets into new and removed links
		add = []
		remove = []		
		for name, new, old in (parents or []):
			old = set(old or [])
			new = set(new or [])
			for i in new - old:
				add.append((i, name))
			for i in old - new:
				remove.append((i, name))
		
		for name, new, old in (children or []):
			old = old or set()
			new = new or set()
			for i in new - old:
				add.append((name, i))
			for i in old - new:
				remove.append((name, i))
		
		nmi = set()
		for v in namemap.values():
			nmi.add(v)

		# print "Add links:", add
		# print "Remove links:", remove

		p_add = collections.defaultdict(set)
		p_remove = collections.defaultdict(set)
		c_add = collections.defaultdict(set)
		c_remove = collections.defaultdict(set)

		for p,c in add:
			p_add[c].add(p)
			c_add[p].add(c)
		for p,c in remove:
			p_remove[c].add(p)
			c_remove[p].add(c)

		# print "p_add:", p_add
		# print "p_remove:", p_remove
		# print "c_add:", c_add
		# print "c_remove:", c_remove
		
		if not indexonly:
			# Go and fetch other items that we need to update
			names = set(p_add.keys()+p_remove.keys()+c_add.keys()+c_remove.keys())
			# print "All affected items:", names
			# print "New items:", nmi
			for name in names-nmi:
				# Get and modify the item directly w/o Context:
				#	Linking only requires write permissions on ONE of the items
				# This might be changed in the future.
				rec = self.get(name, filt=False, txn=txn)
				rec.__dict__['parents'] -= p_remove[rec.name]
				rec.__dict__['parents'] |= p_add[rec.name]
				rec.__dict__['children'] -= c_remove[rec.name]
				rec.__dict__['children'] |= c_add[rec.name]
				self.put(rec.name, rec, txn=txn)
	
		for k,v in p_remove.items():
			if v:
				indp.removerefs(k, v, txn=txn)
		for k,v in p_add.items():
			if v:
				indp.addrefs(k, v, txn=txn)
		for k,v in c_remove.items():
			if v:
				indc.removerefs(k, v, txn=txn)
		for k,v in c_add.items():
			if v:
				indc.addrefs(k, v, txn=txn)
	
		return


	##############################
	# Search tree-like indexes (e.g. parents/children)
	##############################

	def dfs(self, key, rel='children', recurse=1, ctx=None, txn=None):
		# Return a dict of results as well as the nodes visited (saves time)
		if recurse == -1:
			recurse = g.MAXRECURSE

		# Get the index, and create a cursor (slightly faster)
		rel = self.index[rel]
		cursor = rel.bdb.cursor(txn=txn)

		# Starting items
		new = rel.get(key, cursor=cursor)
		stack = [new]
		result = {key: new}
		visited = set()
		lookups = []

		for x in xrange(recurse-1):
			if not stack[x]:
				break

			stack.append(set())
			for key in stack[x] - visited:
				new = rel.get(key, cursor=cursor)
				if new:
					stack[x+1] |= new #.extend(new)
					result[key] = new
			visited |= stack[x]

		visited |= stack[-1]
		cursor.close()
		return result, visited









__version__ = "$Revision$".split(":")[1][:-1].strip()
