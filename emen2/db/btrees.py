# $Id$
"""Berkeley-DB BTree wrappers.

Classes:
	EMEN2DB: BerkeleyDB BTree wrapper
	IndexDB: Index DB
	DBODB: DB for items implementing DBO interface
	RelateDB: DBODB that supports parent-child relationships

"""

import sys
import time
import weakref
import collections
import copy
import bsddb3
import traceback
import os
import functools
import cPickle as pickle

# EMEN2 imports
import emen2.db.config
import emen2.db.log
import emen2.util.listops
import emen2.db.query

try:
	import emen2.db.bulk
	bulk = emen2.db.bulk
	# emen2.db.log.info("Note: using EMEN2-BerkeleyDB bulk access module")
except ImportError, inst:
	bulk = None


# Berkeley DB wrapper classes
class EMEN2DB(object):
	"""BerkeleyDB Btree Wrapper.

	This class uses BerkeleyDB to create an object much like a persistent
	Python Dictionary. Key may be and data may be any pickle-able Python type,
	but unicode/int/float key and data types are also supported with some
	acceleration.

	*ALMOST ALL READ/WRITE METHODS REQUIRE A TRANSACTION*, specified in
	the txn keyword. Generally, the flags keyword is only used internally; it
	is passed to the Berkeley DB API method.

	:attr filename: Filename of BDB on disk
	:attr dbenv: EMEN2 Database Environment
	:attr cache: Cached items loaded from JSON. These do not exist in the BDB.
	:attr cache_parents: Relationships of cached items
	:attr cache_children: Relationships of cached items
	:attr index: Open indexes
	:attr bdb: Berkeley DB instance
	:attr DBOPENFLAGS: Berkeley DB flags for opening database
	:attr DBSETFLAGS: Additional flags


	"""
	#: Data type of DB keys: s(tring), f(loat), d(ecimal)
	keytype = 's'

	#: Data type of DB values: s(tring), f(loat), d(ecimal)
	datatype = 's'

	#: The subclass of :py:class:`~.dataobjects.BaseDBObject` that this BTree stores
	dataclass = None

	#: classattr Comparison function. Do not use touch this.
	cfunc = True

	#: The filename extension to use: bdb or index
	extension = 'bdb'

	def __init__(self, filename, keytype=None, datatype=None, dataclass=None, dbenv=None, autoopen=True):
		"""Main BDB DB wrapper

		:param filename: Base filename to use
		:keyword keytype: Overrides cls.keytype
		:keyword datatype: Overrides cls.datatype
		:keyword dataclass: Overrides cls.dataclass
		:keyword dbenv: Database environment
		:keyword autoopen: Automatically open DB

		"""
		# Filename
		self.filename = filename

		# EMEN2DBEnv
		self.dbenv = dbenv

		# Cached items
		self.cache = {}
		self.cache_parents = collections.defaultdict(set) # temporary patch
		self.cache_children = collections.defaultdict(set) # temporary patch

		# Indexes
		self.index = {}
		self._truncate_index = False

		# BDB Handle
		self.bdb = None
		self.DBOPENFLAGS = bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE
		self.DBSETFLAGS = []

		# What are we storing?
		self._setkeytype(keytype or self.keytype)
		self._setdatatype(datatype or self.datatype, dataclass=dataclass or self.dataclass)

		self.init()
		if autoopen:
			self.open()


	def init(self):
		"""Subclass init hook."""
		pass


	def __str__(self):
		return "<EMEN2DB instance: %s>"%self.filename



	##### load/dump methods for keys and data #####

	# DO NOT TOUCH THIS!!!!
	def _cfunc_numeric(self, k1, k2):
		# Numeric comparison function, for key sorting.
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
		# Dump a pickled DBO.
		# See BaseDBObject.__getstate__
		return pickle.dumps(data)


	def _pickleload(self, data):
		# Load a pickled DBO.
		if data != None: return pickle.loads(data)
		
		
	def _timedump(self, data):
		pass


	def _setkeytype(self, keytype):
		# Set the DB key type. This will bind the correct
		# typekey, dumpkey, loadkey methods.
		if keytype == 's':
			self.typekey = unicode
			self.dumpkey = lambda x:x.encode('utf-8')
			self.loadkey = lambda x:x.decode('utf-8')
		elif keytype == 'd':
			self.typekey = int
			self.dumpkey = str
			self.loadkey = int
		elif keytype == 'f':
			self.typekey = float
			self.dumpkey = self._pickledump
			self.loadkey = self._pickleload
		else:
			raise ValueError, "Invalid keytype: %s. Supported: s(tring), d(ecimal), f(loat)"%keytype

		self.keytype = keytype


	def _setdatatype(self, datatype, dataclass=None):
		# Set the DB data type. This will bind the correct
		# dataclass attribute, and dumpdata and loaddata methods.
		if datatype == 's':
			# String datatype; use UTF-8 encoded strings.
			self.dataclass = unicode
			self.dumpdata = lambda x:x.encode('utf-8')
			self.loaddata = lambda x:x.decode('utf-8')
		elif datatype == 'd':
			# Decimal datatype, use str encoded ints.
			self.dataclass = int
			self.dumpdata = str
			self.loaddata = int
		elif datatype == 'f':
			# Float datatype; these do not sort natively, so pickle them.
			# This will make a not very fast index :(
			# Todo: find a float representation that is very fast and has
			# 	lexicographical sorting.
			self.dataclass = float
			self.dumpdata = self._pickledump
			self.loaddata = self._pickleload
		elif datatype == 'p':
			# This DB stores a DBO as a pickle.
			if dataclass:
				self.dataclass = dataclass
			else:
				self.dataclass = lambda x:x
			self.dumpdata = self._pickledump
			self.loaddata = self._pickleload
		else:
			# Unknown datatype.
			raise ValueError, "Invalid datatype: %s. Supported: s(tring), d(ecimal), f(loat), p(ickle)"%datatype

		self.datatype = datatype


	##### DB methods #####

	def open(self):
		"""Open the DB.

		Store the BerkeleyDB handle in self.bdb.
		This is uses an implicit open transaction.

		"""
		if self.bdb:
			raise Exception, "DB already open"

		# Create the DB handle and set flags
		self.bdb = bsddb3.db.DB(self.dbenv.dbenv)

		# Set DB flags, e.g. duplicate keys allowed
		for flag in self.DBSETFLAGS:
			self.bdb.set_flags(flag)

		# Set a sort method
		if self.cfunc and self.keytype in ['d', 'f']:
			self.bdb.set_bt_compare(self._cfunc_numeric)

		# Open the Berkeley DB with the correct flags.
		self.bdb.open('%s.%s'%(self.filename, self.extension), dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)


	def close(self):
		"""Close the DB, and remove the BerkeleyDB handle."""
		self.bdb.close()
		self.bdb = None



	##### Mapping methods #####

	def keys(self, txn=None):
		"""Mapping interface: keys. Requires txn.

		:keyword txn: Transaction
		:return: All keys in database, and cached keys.

		"""
		# Returns all keys in the database, plus keys in the cache
		return map(self.loadkey, self.bdb.keys(txn)) + self.cache.keys()


	def values(self, txn=None):
		"""Mapping interface: values. Requires txn.

		:keyword txn: Transaction
		:return: All values in database, and cached values.

		"""
		# Returns all values in the database, plus all cached items
		return [self.loaddata(x) for x in self.bdb.values(txn)] + map(pickle.loads, self.cache.values())


	def items(self, txn=None):
		"""Mapping interface: items. Requires txn.

		:keyword txn: Transaction
		:return: All items in database, and cached items.

		"""
		# Returns all the data in the database, plus all cached items
		return map(lambda x:(self.loadkey(x[0]),self.loaddata(x[1])), self.bdb.items(txn)) + [(k, pickle.loads(v)) for k,v in self.cache.items()]


	def iteritems(self, txn=None, flags=0):
		"""Mapping interface: iteritems. Requires txn.

		This does not currently support cached items, but probably will soon.

		:keyword txn: Transaction
		:yield: (key, value) for all items in database.

		"""
		# todo: support cached items
		# Scan accross the database, yielding key/value pairs.
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			yield (self.loadkey(pair[0]), self.loaddata(pair[1]))
			pair = cursor.next_nodup()
		cursor.close()

		for k,v in self.cache.items():
			yield (k, pickle.loads(v))


	def has_key(self, key, txn=None):
		"""Mapping interface: has_key. Requires txn.

		:param key: Key
		:keyword txn: Transaction
		:return: True if key exists

		"""
		return self.bdb.has_key(self.dumpkey(key), txn=txn) or self.cache.has_key(key)


	def exists(self, key, txn=None, flags=0):
		"""Checks to see if key exists in BDB. Requires txn.

		:param key: Key
		:keyword txn: Transaction
		:return: True if key exists

		"""
		if key == None:
			return False
		return self.bdb.exists(self.dumpkey(key), txn=txn, flags=flags) or self.cache.has_key(key)


	##### Cache items #####

	def addcache(self, item, txn=None):
		"""Add an item to the cache; used for loading from JSON/XML.

		These items will work normally (get, put, relationships, items, etc.)
		but exist in memory only, not in the DB.

		Requires the DB to be open and requires a txn.

		:keyword txn: Transaction
		:param item: Item to cache. Should be an instantiated DBObject.

		"""
		#if not self.bdb:
		#	raise Exception, "DB not open."
		# print "Adding %s to cache"%item.name

		if item.name in self.cache:
			# raise KeyError, "Warning: Item %s already in cache, skipping"%item.name
			pass
		if self.get(item.name, txn=txn):
			# raise emen2.db.exceptions.ExistingKeyError, "Item %s already in exists in database, skipping"%item.name
			pass


		# Update parent/child relationships
		# print "Checking parents/children for %s"%item.name
		item.parents |= self.getindex('parents', txn=txn).get(item.name)
		item.children |= self.getindex('children', txn=txn).get(item.name)

		for child in item.children:
			if self.cache.get(child):
				i = pickle.loads(self.cache[unicode(child)])
				i.parents.add(item.name)
				self.cache[unicode(i.name)] = pickle.dumps(i)

		for parent in item.parents:
			if self.cache.get(parent):
				i = pickle.loads(self.cache[unicode(parent)])
				i.children.add(item.name)
				self.cache[unicode(i.name)] = pickle.dumps(i)

		# Also update the other side of the relationship, using cache_parents
		# and cache_children
		self.cache_parents[item.name] |= item.parents
		self.cache_children[item.name] |= item.children
		for parent in item.parents:
			self.cache_children[parent].add(item.name)
		for child in item.children:
			self.cache_parents[child].add(item.name)

		# Final check
		item.parents |= self.cache_parents[item.name]
		item.children |= self.cache_children[item.name]

		# Store the item pickled, so it works with get, and
		# returns new instances instead of globally shared ones...
		self.cache[unicode(item.name)] = pickle.dumps(item)



	##### Read #####

	def get(self, key, default=None, filt=True, txn=None, flags=0):
		"""Mapping interface: get.

		:param key: Key
		:keyword default: Default value if key not found
		:keyword filt: Flag to ignore KeyErrors
		:keyword txn: Transaction
		:return: Found value or default

		"""
		if key in self.cache:
			return pickle.loads(self.cache[key])

		# Check BDB
		d = self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		if d:
			return d
		if not filt:
			raise KeyError, "No such key %s"%(key)
		return default


	##### Write #####

	def put(self, key, data, txn=None, flags=0):
		"""Write key/value, with txn.

		:param key: Key
		:param data: Data
		:keyword txn: Transaction

		"""
		# Check cache; these are read-only
		if key in self.cache:
			raise emen2.db.exceptions.SecurityError, "Cannot modify read-only item %s"%key
		# Write item to database
		emen2.db.log.msg('COMMIT', "%s.put: %s"%(self.filename, key))
		# print data.__dict__
		self.bdb.put(self.dumpkey(key), self.dumpdata(data), txn=txn, flags=flags)


	# Dangerous!
	def truncate(self, txn=None, flags=0):
		"""Truncate BDB (e.g. 'drop table'). Transaction required.

		:keyword txn: Transaction

		"""
		# todo: Do more checking before performing a dangerous operation.
		self.bdb.truncate(txn=txn)
		emen2.db.log.msg('COMMIT', "%s.truncate"%self.filename)


	# Also dangerous!
	def delete(self, key, txn=None, flags=0):
		"""Delete item; not supported on all DB types. Transaction required.

		:param key: Key to delete
		:keyword txn: Transaction

		"""
		# Read-only items can't be killed.
		if key in self.cache:
			raise KeyError, "Cannot delete read-only item %s"%key
		# If the item exists, remove it.
		if self.bdb.exists(self.dumpkey(key), txn=txn):
			ret = self.bdb.delete(self.dumpkey(key), txn=txn, flags=flags)
			emen2.db.log.msg('COMMIT', "%s.delete: %s"%(self.filename, key))







class IndexDB(EMEN2DB):
	'''EMEN2DB optimized for indexes.

	IndexDB uses the Berkeley DB facility for storing multiple values for a
	single key (DB_DUPSORT). The Berkeley DB API has a method for
	quickly reading these multiple values.

	This class is intended for use with an OPTIONAL C module, _bulk.so, that
	accelerates reading from the index. The Berkeley DB bulk reading mode
	is not fully implemented in the bsddb3 package; the C module does the bulk
	reading in a single C function call, greatly speeding up performance, and
	returns the correct native Python type. The C module is totally optional
	and is transparent; the only change is read speed.

	In the DBEnv directory, IndexDBs will have a ".index" extension.

	Index references are added using addrefs() and removerefs(). These both
	take a single key, and a list of references to add or remove.

	Extends or overrides the following methods:
		init		Checks bulk mode
		get			Returns all values found.
		put			Not allowed, use addrefs/removerefs
		keys		Index keys
		items		Index items; (key, [value1, value2, ...])
		iteritems	Index iteritems

	Adds the following indexing methods:
		addrefs		Add (key, [values]) references to the index
		removerefs	Remove (key, [values]) references from the index
		iterfind	Search the index until all items are found

	'''

	#: The filename extension
	extension = 'index'

	def init(self):
		"""Open DB with support for duplicate keys."""
		self.DBSETFLAGS = [bsddb3.db.DB_DUPSORT]
		self._setbulkmode(True)
		super(IndexDB, self).init()


	def _setbulkmode(self, bulkmode):
		# Use acceleration C module if available
		self._get_method = self._get_method_nonbulk
		if bulk:
			if bulkmode:
				self._get_method = emen2.db.bulk.get_dup_bulk
			else:
				self._get_method = emen2.db.bulk.get_dup_notbulk


	def _get_method_nonbulk(self, cursor, key, dt, flags=0):
		# Get without C module. Uses an already open cursor.
		n = cursor.set(key)
		r = set() #[]
		m = cursor.next_dup
		while n:
			r.add(n[1])
			n = m()
		return set(self.loaddata(x) for x in r)

	# Default get method used by get()
	_get_method = _get_method_nonbulk

	def get(self, key, default=None, cursor=None, txn=None, flags=0):
		"""Return all the values for this key.

		Can be passed an already open cursor, or open one if necessary.
		Requires a transaction. The real get method is _get_method, which
		is set during init based on availability of the C module.

		:param key: Key
		:keyword default: Default value if key not found
		:keyword cursor: Use this cursor
		:keyword txn: Transaction
		:return: Values for key

		"""
		if cursor:
			r = self._get_method(cursor, self.dumpkey(key), self.datatype)
		else:
			cursor = self.bdb.cursor(txn=txn)
			r = self._get_method(cursor, self.dumpkey(key), self.datatype)
			cursor.close()

		if bulk and self.datatype == 'p':
			r = set(self.loaddata(x) for x in r)

		return r


	def put(self, *args, **kwargs):
		"""Not supported on indexes; use addrefs, removerefs."""
		raise Exception, "put not supported; use addrefs, removerefs"


	# ian: todo: allow min/max
	def keys(self, txn=None, flags=0):
		"""Accelerated keys. Transaction required.

		:keyword txn: Transaction

		"""
		keys = set(map(self.loadkey, self.bdb.keys(txn)))
		return list(keys)


	# ian: todo: allow min/max
	def items(self, txn=None, flags=0):
		"""Accelerated items. Transaction required.

		:keyword txn: Transaction

		"""
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


	def iteritems(self, minkey=None, maxkey=None, txn=None, flags=0):
		"""Accelerated iteritems. Transaction required.

		:keyword minkey: Minimum key
		:keyword maxkey: Maximum key
		:keyword txn: Transaction
		:yield: (key, value)

		"""
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		
		# Start a minimum key. 
		# This only works well if the keys are sorted properly.
		if minkey is not None:
			pair = cursor.set_range(self.dumpkey(minkey))
		
		while pair != None:
			data = self._get_method(cursor, pair[0], self.datatype)
			k = self.loadkey(pair[0])
			if bulk and self.datatype == "p":
				data = set(map(self.loaddata, data))
			yield (k, data)
			pair = cursor.next_nodup()
			if maxkey is not None and k > maxkey:
				pair = None

		cursor.close()


	def iterfind(self, items, minkey=None, maxkey=None, txn=None, flags=0):
		"""Searches the index. Transaction required.

		Iterate until all requested items or found, or all keys have
		been searched, or maxkey has been reached.

		:keyword minkey: Planned support for starting key
		:keyword maxkey: Planned support for end key
		:keyword txn: Transaction
		:yield: (key, value)

		"""
		itemscopy = copy.copy(items)
		lenitems = len(itemscopy)

		processed = 0
		found = 0
		ret = {}

		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			processed += 1
			data = self._get_method(cursor, pair[0], self.datatype)
			if bulk and self.datatype == "p":
				data = set(map(self.loaddata, data))

			c = data & itemscopy
			if c:
				itemscopy -= c
				found += len(c)
				# print "processed %s keys, %s items left to go"%
				#	(processed, lenitems-found)
				# ret[self.loadkey(pair[0])] = c
				yield (self.loadkey(pair[0]), c)

			if found >= lenitems:
				break
			else:
				pair = cursor.next_nodup()

		# print "Done; processed %s keys"%processed
		cursor.close()


	##### Write Methods #####

	def removerefs(self, key, items, txn=None):
		'''Remove references.

		A list of keys that are no longer present in the index with any values
		is returned; this can be used to maintain other indexes.

		:param key: Key
		:param items: References to remove
		:keyword txn: Transaction
		:return: Keys that no longer have any references

		'''
		if not items: return []

		delindexitems = []

		cursor = self.bdb.cursor(txn=txn)

		key = self.typekey(key)
		items = map(self.dataclass, items)

		dkey = self.dumpkey(key)
		ditems = map(self.dumpdata, items)

		for ditem in ditems:
			if cursor.set_both(dkey, ditem):
				cursor.delete()

		if not cursor.set(dkey):
			delindexitems.append(key)

		cursor.close()

		emen2.db.log.index("%s.removerefs: %s -> %s"%(self.filename, key, len(items)))
		return delindexitems


	def addrefs(self, key, items, txn=None):
		"""Add references.

		A list of keys that are new to this index are returned. This can be
		used to maintain other indexes.

		:param key: Key
		:param items: References to add
		:keyword txn: Transaction
		:return: Keys that are new to this index

		"""
		if not items: return []

		addindexitems = []

		key = self.typekey(key)
		items = map(self.dataclass, items)

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

		emen2.db.log.index("%s.addrefs: %s -> %s"%(self.filename, key, len(items)))
		return addindexitems





# Context-aware DB for DBO's.
# These support a single DB and a single data class.
# Supports sequenced items.
class DBODB(EMEN2DB):
	'''Database for items supporting the DBO interface (mapping
	interface, setContext, writable, etc. See BaseDBObject.)

	These DBs will generally used pickle as the data type; most will use
	string as the keytype, except RecordDB, which uses ints.

	The sequence class attribute, if True, will allow sequence support for
	this DB. This is currently implemented using a separate BDB (to minimize
	locks), although at some point the
	BerkeleyDB Sequence may be used (it caused problems last time I tried.)

	Like EMEN2DB, most methods require a transaction. Additionally, because
	this class manages DBOs, most methods also require a Context.

	Extends the following methods:
		__init__ 		Changes the filename slightly
		init			Supports sequences if allowed
		open			Also opens sequencedb
		close			Also cloes sequencdb and indexes

	And adds the following methods:
		get_max			Return the current maximum item in the sequence
		update_names	Update items with new names from sequence
		new				Dataclass factory
		cget			Get a single item, with a Context
		cgets			Get items, with a Context
		cput			Put a single item, with a Context
		cputs			Put items, with a Context
		expand			Process '*' operators in names to parents/children
		names			Similar to keys, but Context aware
		items			Context-aware items
		validate		Validate an item
		reindex			Reindex a changed parameter value
		openindex		Open an index, and store the handle in self.index
		getindex		Get an already open index, or open if necessary
		closeindex		Close an index

	'''

	datatype = 'p'
	sequence = False
	dataclass = None

	def __init__(self, path='', *args, **kwargs):
		# Change the filename slightly
		self.path = path
		name = self.dataclass.__name__
		filename = os.path.join(self.path, name).lower()
		super(DBODB, self).__init__(filename, *args, **kwargs)


	def init(self):
		"""Add support for sequences."""
		self.sequence = self.sequence
		self.sequencedb = None
		super(DBODB, self).init()


	def open(self):
		"""Open the sequence with the main DB."""
		super(DBODB, self).open()
		if self.sequence:
			self.sequencedb = bsddb3.db.DB(self.dbenv.dbenv)
			self.sequencedb.open(os.path.join('%s.sequence.bdb'%self.filename), dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)


	def close(self):
		"""Close the sequence, and any open indexes, with the main DB."""
		super(DBODB, self).close()
		if self.sequencedb:
			self.sequencedb.close()
			self.sequencedb = None
		for k in self.index:
			self.closeindex(k)



	##### Sequence #####

	def get_max(self, txn=None):
		"""Return the current maximum item in the sequence. Requires txn.

		:keyword txn: Transaction

		"""
		if not self.sequence:
			raise ValueError, "Sequences not supported"
		sequence = self.sequencedb.get("sequence", txn=txn)
		if sequence == None:
			sequence = 0
		val = int(sequence)
		return val


	def update_names(self, items, namemap=None, txn=None):
		"""Update items with new names. Requires txn.
	
		:param items: Items to update.
		:keyword txn: Transaction
	
		"""
		namemap = namemap or {}
		# for i in items:
		# 	if not self.exists(i.name, txn=txn):
		# 		namemap[i.name] = i.name
		
		# New items will have 'None' or a negative integer as name
		

		return namemap



	# Update the database sequence.. Probably move this to the parent class.
	# def update_names(self, items, txn=None):
	# 	# Which items are new?
	# 	newrecs = [i for i in items if i.name < 0] # also valid for None
	# 	namemap = {}
	# 
	# 	# Reassign new record IDs and update record counter
	# 	if newrecs:
	# 		basename = self._set_sequence(delta=len(newrecs), txn=txn)
	# 
	# 	# We have to manually update the rec.__dict__['name'] because this is normally considered a reserved attribute.
	# 	for offset, newrec in enumerate(newrecs):
	# 		oldname = newrec.name
	# 		newrec.__dict__['name'] = offset + basename
	# 		namemap[oldname] = newrec.name
	# 
	# 	# Update all the record's links
	# 	for item in items:
	# 		# ian: TODO: directly update the dict, to avoid item._setrel(). However, this is not the proper way to do it. 
	# 		# It should see if item exists, or is new; otherwise, raise exception.
	# 		item.__dict__['parents'] = set([namemap.get(i,i) for i in item.parents])
	# 		item.__dict__['children'] = set([namemap.get(i,i) for i in item.children])
	# 
	# 	return namemap



	def _set_sequence(self, delta=1, key='sequence', txn=None):
		# Update the sequence. Requires txn.
		# The Sequence DB can handle multiple sequences -- e.g., for
		# binaries, each day has its own sequence item.
		if not self.sequence:
			raise ValueError, "Sequences not supported"

		# print "Setting sequence += %s, txn: %s, newtxn: %s, flags:%s"%
		# (delta, txn, newtxn, bsddb3.db.DB_RMW)
		val = self.sequencedb.get(key, txn=txn, flags=bsddb3.db.DB_RMW)
		if val == None:
			val = 0
		val = int(val)
		self.sequencedb.put(key, str(val+delta), txn=txn)
		emen2.db.log.msg('COMMIT', "%s.sequence: %s"%(self.filename, val+delta))
		return val


	##### New items.. #####

	def new(self, *args, **kwargs):
		"""Returns new DBO. Requires ctx and txn.

		All the method args and keywords will be passed to the constructor.

		:keyword txn: Transaction
		:return: New DBO
		:exception ExistingKeyError:

		"""
		txn = kwargs.pop('txn', None) # don't pass the txn..
		item = self.dataclass(*args, **kwargs)
		if self.exists(item.name, txn=txn):
			raise emen2.db.exceptions.ExistingKeyError, "%s already exists"%item.name
		return item



	##### Filtered context gets.. #####

	# Get an item and set Context
	def cget(self, key, filt=True, ctx=None, txn=None, flags=0):
		"""See cgets(). This works the same, but for a single key."""
		r = self.cgets([key], txn=txn, ctx=ctx, filt=filt, flags=flags)
		if not r:
			return None
		return r[0]


	# Takes an iterable..
	def cgets(self, keys, filt=True, ctx=None, txn=None, flags=0):
		"""Get a list of items, with a Context. Requires ctx and txn.

		The filt keyword, if True, will ignore KeyError and SecurityError.
		Alternatively, it can be set to a list of Exception types to ignore.

		:param key: Items to get
		:keyword filt: Ignore KeyError, SecurityError
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: DBOs with bound Context
		:exception KeyError:
		:exception SecurityError:

		"""
		# filt can be an exception type, a list of exception types
		# or True, which defaults to SecurityError, KeyError
		# KeyError if item doesn't exist; SecurityError if no access
		if filt == True:
			filt = (emen2.db.exceptions.SecurityError, KeyError)

		ret = []
		for key in self.expand(keys, ctx=ctx, txn=txn):
			try:
				d = self.get(key, filt=False, txn=txn, flags=flags)
				d.setContext(ctx)
				ret.append(d)
			except filt, e:
				pass

		return ret


	def expand(self, names, ctx=None, txn=None):
		"""Process a list of names. Requires ctx and txn.

		see RelateDB for complete implementation.

		:param names:
		:param ctx: Context
		:param txn: Transaction
		:return: set of names

		"""
		if not isinstance(names, set):
			names = set(names)
		return names


	def names(self, names=None, ctx=None, txn=None, **kwargs):
		"""Context-aware keys(). Requires ctx and txn.

		:keyword names: Subset of items to check
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: Set of keys that are accessible by the Context

		"""
		if names is not None:
			if ctx.checkadmin():
				return names
			items = self.cgets(names, ctx=ctx, txn=txn)
			return set([i.name for i in items])

		return set(self.keys(txn=txn))
		# return set(map(self.loadkey, self.bdb.keys(txn)))


	def items(self, items=None, rt=None, ctx=None, txn=None, **kwargs):
		"""Context-aware items. Requires ctx and txn.

		:keyword items: Subset of items
		:keyword rt: Return type. Deprecated.
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: (key, value) items that are accessible by the Context

		"""
		oitems = items

		# Return type
		if hasattr(items, 'next'):
			rt = list
		else:
			if rt is None:
				if items is None:
					rt = list
				else:
					rt = type(items)

		# Use iter if available
		if hasattr(items, 'iteritems'):
			items = items.iteritems()
		elif hasattr(items, 'items'):
			items = items.items()

		# Get the cached items
		cacheditems = [(k, pickle.loads(v)) for k,v in self.cache.items()]

		# Restrict to a subset
		if items is not None:
			if ctx.checkadmin(): return oitems
			return rt( (k,v) for k,v in items if (self.cget(k, ctx=ctx, txn=txn) is not None) ) + cacheditems

		# Return all items
		return rt( (self.loadkey(k), self.loaddata(v)) for k,v in self.bdb.items(txn) ) + cacheditems


	def validate(self, items, ctx=None, txn=None):
		return self.cputs(items, commit=False, ctx=ctx, txn=txn)



	##### Write methods #####

	def cput(self, item, *args, **kwargs):
		"""See cputs(). This works the same, but for a single DBO."""
		ret = self.cputs([item], *args, **kwargs)
		if not ret:
			return None
		return ret[0]


	def cputs(self, items, commit=True, ctx=None, txn=None):
		"""Update DBOs. Requires ctx and txn.

		:param item: DBOs, or similar (e.g. dict)
		:keyword commit: Actually commit (e.g. for validation only)
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: Updated DBOs
		:exception KeyError:
		:exception SecurityError:
		:exception ValidationError:

		"""
		t = emen2.db.database.gettime()
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		crecs = []
		namemap = {}

		# Get the existing records, or create new records.
		for name, updrec in enumerate(items, start=1):
			name = updrec.get('name')
			cp = set()

			# Get the existing item or create a new one.
			# Acquire the write lock immediately (DB_RMW).
			# Names can be unassigned (None, negative integer) or assigned (a string).
			# Some BDOs require names (paramdef, recorddef); 
			#	others (e.g. user) will assign the name in update_names.
			# Note: this used to just be a try/except, with new items on KeyError.
			if name < 0 or not self.exists(name, txn=txn, flags=bsddb3.db.DB_RMW):
				p = dict((k,updrec.get(k)) for k in self.dataclass.attr_required)
				orec = self.new(name=name, t=t, ctx=ctx, txn=txn, **p)
				namemap[name] = orec.name
				cp.add('name')
			else:
				orec = self.get(name, txn=txn, flags=bsddb3.db.DB_RMW)
				orec.setContext(ctx)

			# Update the item.
			cp |= orec.update(updrec, vtm=vtm, t=t)
			orec.validate()

			# If values changed, cache those, and add to the commit list
			if cp:
				crecs.append(orec)

		# If we just wanted to validate the changes, return before writing changes.
		if not commit or not crecs:
			return crecs

		# Assign names for new items.
		# This will also update any relationships to uncommitted records.
		namemap = self.update_names(crecs, txn=txn)

		# Calculate all changed indexes
		self.reindex(crecs, namemap=namemap, ctx=ctx, txn=txn)

		# Commit "for real"
		for crec in crecs:
			self.put(crec.name, crec, txn=txn)

		emen2.db.log.info("Committed %s items"%(len(crecs)))

		# Return the updated items.
		return crecs


	# Calculate and write index changes
	# if indexonly, assume items are new, to rebuild all params.
	def reindex(self, items, indexonly=False, namemap=None, ctx=None, txn=None):
		"""Update indexes. This is really a private method.

		The original items will be retrieved and compared to the updated
		items. A set of index changes will be calculated, and then handed off
		to the _reindex_* methods. In some cases, these will be overridden
		or extended to handle special indexes -- such as parent/child
		relationships in RelateDB. There is not a complete interface for
		doing this, although it may be so in the future.

		:param items: Updated DBOs
		:keyword indexonly:
		:keyword namemap:
		:keyword ctx: Context
		:keyword txn: Transaction

		"""
		ind = collections.defaultdict(list)

		# Get changes as param:([name, newvalue, oldvalue], ...)
		for crec in items:
			# Get the current record for comparison of updated values.
			# Use an empty dict for new records so all keys
			# will seen as new (or if reindexing)
			# ian: todo: get or cget?
			orec = self.cget(crec.name, ctx=ctx, txn=txn) or {}
			if indexonly:
				orec = {}
			for param in crec.changedparams(orec):
				ind[param].append((crec.name, crec.get(param), orec.get(param)))

		# These are complex changes, so pass them off to different reindex method
		parents = ind.pop('parents', None)
		children = ind.pop('children', None)
		# If the BTree supports permissions...
		self._reindex_relink(parents, children, namemap=namemap, indexonly=indexonly, ctx=ctx, txn=txn)

		for k,v in ind.items():
			self._reindex_param(k, v, ctx=ctx, txn=txn)


	def _reindex_relink(self, parents, children, namemap=None, indexonly=False, ctx=None, txn=None):
		# (Internal) see RelateDB
		return


	def _reindex_param(self, param, changes, ctx=None, txn=None):
		# (Internal) Reindex changes to a single parameter.

		# If nothing changed, skip.
		if not changes:
			return

		# If we can't access the index, skip. (Raise Exception?)
		ind = self.getindex(param, txn=txn)
		if ind == None:
			# print "No index for %s, skipping"%param
			return

		# Check that this key is currently marked as indexed
		# ian: use the context.
		pd = ctx.db.getparamdef(param, filt=False)
		vtm = emen2.db.datatypes.VartypeManager()
		vt = vtm.getvartype(pd.vartype)
		vt.pd = pd

		# Process the changes into index addrefs / removerefs
		try:
			addrefs, removerefs = vt.reindex(changes)
		except Exception, e:
			print "Could not reindex param %s: %s"%(pd.name, e)
			print changes
			return
		# print "reindexing", pd.name
		# print "changes:", changes
		# print "addrefs:", addrefs
		# print "remove:", removerefs

		# Write!
		for oldval, recs in removerefs.items():
			# Not necessary to map temp names to final names,
			# as reindexing is now done after assigning names
			ind.removerefs(oldval, recs, txn=txn)

		for newval,recs in addrefs.items():
			ind.addrefs(newval, recs, txn=txn)


	##### Indexes. #####
	# Subclasses should provide an openindex method.

	def openindex(self, param, txn=None):
		"""Open a parameter index. Requires txn.

		The base DBODB class provides no indexes. The subclass must implement
		this method if it wants to provide any indexes. This can be either
		one or two attributes that are indexed, such as filename/md5 in
		BinaryDB, or a complete and general index system in RecordDB.

		If an index for a parameter isn't returned by this method, the reindex
		method will just skip it.

		:param param: Parameter
		:param txn: Transaction
		:return: IndexDB

		"""
		return


	def _indname(self, param):
		# (Internal) Get the index filename
		return os.path.join(self.path, 'index', param)


	def getindex(self, param, txn=None):
		"""Return an open index, or open if necessary. Requires txn.

		A successfully opened IndexDB will be cached in self.index[param] and
		reused on subsequent calls.

		:param param: Parameter
		:keyword txn: Transaction
		:return: IndexDB

		"""
		if param in self.index:
			return self.index.get(param)

		ind = self.openindex(param, txn=txn)
		self.index[param] = ind
		if self._truncate_index and ind:
			ind.truncate(txn=txn)
		return ind


	def closeindex(self, param):
		"""Close an index. Uses an implicit transaction for close.

		:param param: Parameter
		"""
		ind = self.index.get(param)
		if ind:
			ind.close()
			self.index[param] = None


	def rebuild_indexes(self, ctx=None, txn=None):
		# ugly hack..
		self._truncate_index = True
		for k in self.index:
			self.index[k].truncate(txn=txn)
		
		# Do this in chunks of 10,000 items
		# Get all the keys -- do not include cached items
		keys = sorted(map(self.loadkey, self.bdb.keys(txn)), reverse=True)
		for chunk in emen2.util.listops.chunk(keys, 10000):
			if chunk:
				print chunk[0], "...", chunk[-1]
			items = self.cgets(chunk, ctx=ctx, txn=txn)
			# Use self.reindex() instead of self.cputs() -- the data should
			# already be validated, so we can skip that step.
			# self.cputs(items, ctx=ctx, txn=txn)
			self.reindex(items, indexonly=True, ctx=ctx, txn=txn)
		
		self._truncate_index = False

	##### Query #####
	
	def query(self, c=None, mode='AND', ctx=None, txn=None):
		"""Return a Query Constraint Group.
		
		You will need to call constraint.run() to execute the query, 
		and constraint.sort() to sort the values.
		"""
		return emen2.db.query.Query(constraints=c, mode=mode, ctx=ctx, txn=txn, btree=self)



class RelateDB(DBODB):
	"""DBO DB with parent/child relationships between keys.

	Adds a maxrecuse attribute, which controls the maximum recursion level
	in relationships before giving up. If this is removed, problems may arise
	with circular relationships.

	Extends the following methods:
		openindex		Adds parent/child indexes
		expand			Adds support for "*" in names()

	Adds the following methods:
		parenttree		Returns parents dict, one recurse level per key
		childtree		Returns children dict, one recurse level per key
		parents			Returns parents, multiple recurse levels per key
		children		Returns children, multiple recurse lvls per key
		siblings		Item siblings
		rel				General purpose relationship method
		pclink			Add a parent/child relationship
		pcunlink		Remove a parent/child relationship

	"""
	maxrecurse = emen2.db.config.get('params.MAXRECURSE', 50)

	def openindex(self, param, txn=None):
		"""Extends openindex to add support for parents and children."""
		if param in ['children', 'parents']:
			filename = os.path.join(self.path, 'index', param)
			ind = IndexDB(filename=filename, keytype=self.keytype, datatype=self.keytype, dbenv=self.dbenv, autoopen=False)
			ind.cfunc = False # Historical
			ind._setbulkmode(False)
			ind.open()
		else:
			ind = super(RelateDB, self).openindex(param, txn)
		return ind


	##### Relationship methods #####

	def expand(self, names, ctx=None, txn=None):
		"""Expand names.

		This allows 'name*' to serve as shorthand for "name, and all
		children recursively." This is useful for specifying items in queries.

		:param names: DBO names, with optional '*' to include children.
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: Expanded DBO names.

		"""

		if not isinstance(names, set):
			names = set(names)

		# Expand *'s
		remove = set()
		add = set()
		for key in (i for i in names if isinstance(i, basestring)):
			try:
				newkey = self.typekey(key.replace('*', ''))
			except:
				raise KeyError, "Invalid key: %s"%key

			if key.endswith('*'):
				add |= self.children([newkey], recurse=-1, ctx=ctx, txn=txn).get(newkey, set())
			remove.add(key)
			add.add(newkey)

		names -= remove
		names |= add
		return names


	# Commonly used rel() variants
	def parenttree(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		"""See rel(), with rel='parents", tree=True. Requires ctx and txn.

		Returns a tree structure of parents. This will be a dict, with DBO
		names as keys, and one level of parents for the value. It will
		recurse to the level specified by the recurse keyword.

		:return: Tree structure of parents

		"""
		return self.rel(names, recurse=recurse, rel='parents', tree=True, ctx=ctx, txn=txn, **kwargs)


	def childtree(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		"""See rel(), with rel='children", tree=True. Requires ctx and txn.

		Returns a tree structure of children. This will be a dict, with DBO
		names as keys, and one level of children for the value. It will
		recurse to the level specified by the recurse keyword.

		:return: Tree structure of children

		"""
		return self.rel(names, recurse=recurse, rel='children', tree=True, ctx=ctx, txn=txn, **kwargs)


	def parents(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		"""See rel(), with rel='parents", tree=False. Requires ctx and txn.

		This will return a dict of parents to the specified recursion depth.

		:return: Dict with names as keys, and their parents as values

		"""
		return self.rel(names, recurse=recurse, rel='parents', ctx=ctx, txn=txn, **kwargs)


	def children(self, names, recurse=1, ctx=None, txn=None, **kwargs):
		"""See rel(), with rel="children", tree=False. Requires ctx and txn.

		This will return a dict of children to the specified recursion depth.

		:return: Dict with names as keys, and their children as values

		"""
		return self.rel(names, recurse=recurse, rel='children', ctx=ctx, txn=txn, **kwargs)


	# Siblings
	def siblings(self, name, ctx=None, txn=None, **kwargs):
		"""Siblings. Note this only takes a single name. Requries ctx and txn.

		:keyword name: DBO name
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: Set of siblings

		"""
		parents = self.rel([name], rel='parents', ctx=ctx, txn=txn)
		allparents = set()
		for k,v in parents.items():
			allparents |= v
		siblings = set()
		children = self.rel(allparents, ctx=ctx, txn=txn, **kwargs)
		for k,v in children.items():
			siblings |= v
		return siblings


	# Checks permissions, return formats, etc..
	def rel(self, names, recurse=1, rel='children', tree=False, ctx=None, txn=None, **kwargs):
		"""Find relationships. Requires context and transaction.

		Find relationships to a specified recusion depth. This supports any
		type of relationship that has a correctly setup index available;
		currently parents and children are supported. In the future, it will
		support any IndexDB that has names for keys, and the relationships
		as values.

		This method is public because it is sometimes convenient to find
		relationships based on a supplied argument without a case switch
		or duplication of code. However, it switches return types based on
		the tree keyword. Because of this complexity, it is usually called
		through the following convenience methods:
			parents, children, parenttree, childtree

		If tree keyword is True, the returned value will be a tree structure.
		This will have each specified DBO name as a key, and one level of
		children as values. These children will in turn have their own keys,
		and their own children as values, up to the specified recursion depth.

		If tree keyword is False, the returned value will be a dictionary
		with DBO names as keys, and their children (up to the specified
		recursion depth) as values.

		Example edges:
			1: 2, 3
			2: 3
			3: 4
			4: None

		...with names = [1,2,3] and tree=True and recurse=-1:
			{1: [2,3], 2: [3], 3:[4], 4:[]}

		...with names = [1,2,3], tree=False, and recurse=-1:
			{1: [2,3,4], 2: [3,4], 3:[4]}

		:keyword names: DBO names
		:keyword recurse: Recursion depth (default is 1)
		:keyword rel: Relationship type (default is children)
		:keyword tree: Set return type to tree or set
		:keyword ctx: Context
		:keyword txn: Transaction
		:return: Return a tree structure if tree=True, otherwise a set

		"""
		result = {}
		visited = {}
		t = time.time()
		for i in names:
			result[i], visited[i] = self._dfs(i, rel=rel, recurse=recurse)

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

		# Else we're just ruturning the total list of all children,
		# keyed by requested record name
		for k in visited:
			visited[k] &= allr

		return visited


	def pclink(self, parent, child, ctx=None, txn=None):
		"""Create parent-child relationship. Requires ctx and txn.

		Both items will have their parent/child attributes updated
		to reflect the new relationship. You must specify a Context, and
		have READ permissions on BOTH items, and WRITE permission on AT LEAST
		ONE item.

		:param parent: Parent
		:param child: Child
		:keyword ctx: Context
		:keyword txn: Transaction

		"""
		self._putrel(parent, child, mode='addrefs', ctx=ctx, txn=txn)


	def pcunlink(self, parent, child, ctx=None, txn=None):
		"""Remove parent-child relationship. Requires ctx and txn.

		Both items will have their parent/child attributes updated
		to reflect the deleted relationship. You must specify a Context, and
		have READ permissions on BOTH items, and WRITE permission on AT LEAST
		ONE item.

		:param parent: Parent
		:param child: Child
		:keyword ctx: Context
		:keyword txn: Transaction

		"""
		self._putrel(parent, child, mode='removerefs', ctx=ctx, txn=txn)


	def _putrel(self, parent, child, mode='addrefs', ctx=None, txn=None):
		# (Internal) Add or remove a relationship.
		# Mode is addrefs or removerefs; it maps to the IndexDB method.

		# Check that we have enough permissions to write to one item
		# Use raw get; manually setContext. Allow KeyErrors to raise.
		p = self.get(parent, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
		c = self.get(child, filt=False, txn=txn, flags=bsddb3.db.DB_RMW)
		perm = []

		# Both items must exist, and we need to be able to write to one
		try:
			p.setContext(ctx)
			perm.append(p.writable())
		except emen2.db.exceptions.SecurityError:
			pass

		try:
			c.setContext(ctx)
			perm.append(c.writable())
		except emen2.db.exceptions.SecurityError:
			pass

		if not any(perm):
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to add/remove relationship"

		# Transform into the right format for _reindex_relink..
		newvalue = set() | p.children # copy
		if mode == 'addrefs':
			newvalue |= set([c.name])
		elif mode == 'removerefs':
			newvalue -= set([c.name])

		# The values will actually be set on the records
		#  during the relinking method..
		self._reindex_relink([], [[p.name, newvalue, p.children]], ctx=ctx, txn=txn)


	# Handle the reindexing...
	def _reindex_relink(self, parents, children, namemap=None, indexonly=False, ctx=None, txn=None):
		# (Internal) Relink relationships
		# This method will grab both items, and add or remove the rels from
		# each item, and then update the parents/children IndexDBs.

		namemap = namemap or {}
		indc = self.getindex('children', txn=txn)
		indp = self.getindex('parents', txn=txn)
		if not indc or not indp:
			raise KeyError, "Relationships not supported"
	
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

		nmi = set(namemap.keys()) | set(namemap.values())
		# print "p_add:", p_add
		# print "p_remove:", p_remove
		# print "c_add:", c_add
		# print "c_remove:", c_remove
		# print "nmi:", nmi

		if not indexonly:
			# Go and fetch other items that we need to update
			names = set(p_add.keys()+p_remove.keys()+c_add.keys()+c_remove.keys())
			# print "All affected items:", names
			for name in names:
				# Get and modify the item directly w/o Context:
				# Linking only requires write permissions
				# on ONE of the items. This might be changed
				# in the future.
				try:
					rec = self.get(name, filt=False, txn=txn)
					rec.__dict__['parents'] -= p_remove[rec.name]
					rec.__dict__['parents'] |= p_add[rec.name]
					rec.__dict__['children'] -= c_remove[rec.name]
					rec.__dict__['children'] |= c_add[rec.name]
					self.put(rec.name, rec, txn=txn)
				except KeyError:
					# If we're trying to update an item that isn't a new item in the current commit, raise.
					if name not in nmi:
						raise
						

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


	##### Search tree-like indexes (e.g. parents/children) #####

	def _dfs(self, key, rel='children', recurse=1, ctx=None, txn=None):
		# (Internal) Tree search
		# Return a dict of results as well as the nodes visited (saves time)
		if recurse == -1:
			recurse = self.maxrecurse

		# Cached items..
		if rel == 'children':
			cache = self.cache_children
		elif rel == 'parents':
			cache = self.cache_parents
		else:
			cache = {}

		# Get the index, and create a cursor (slightly faster)
		rel = self.getindex(rel, txn=txn)
		cursor = rel.bdb.cursor(txn=txn)

		# Starting items
		
		# NOTE: I am using this ugly direct call 'rel._get_method' to the C module because it saves 10-20% time.		
		new = rel._get_method(cursor, rel.dumpkey(key), rel.datatype) # rel.get(key, cursor=cursor)
		if key in self.cache:
			new |= cache.get(key, set())

		stack = [new]
		result = {key: new}
		visited = set()
		lookups = []

		for x in xrange(recurse-1):
			if not stack[x]:
				break

			stack.append(set())
			for key in stack[x] - visited:
				new = rel._get_method(cursor, rel.dumpkey(key), rel.datatype) # rel.get(key, cursor=cursor)
				if key in self.cache:
					new |= cache.get(key, set())

				if new:
					stack[x+1] |= new #.extend(new)
					result[key] = new

			visited |= stack[x]

		visited |= stack[-1]
		cursor.close()
		return result, visited




__version__ = "$Revision$".split(":")[1][:-1].strip()
