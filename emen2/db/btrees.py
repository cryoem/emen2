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
from emen2.db.exceptions import *

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

	*ALL READ/WRITE METHODS REQUIRE A TRANSACTION*, specified in
	the txn keyword. Generally, the flags keyword is only used internally; it
	is passed to the Berkeley DB API method.

	:attr filename: Filename of BDB on disk
	:attr dbenv: EMEN2 Database Environment
	:attr index: Open indexes
	:attr bdb: Berkeley DB instance
	:attr cache: In memory DB
	:attr cache_parents: Relationships of cached items
	:attr cache_children: Relationships of cached items
	:attr DBOPENFLAGS: Berkeley DB flags for opening database
	:attr DBSETFLAGS: Additional flags
	"""
	
	#: Data format of DB keys: s(tring), f(loat), d(ecimal)
	keyformat = 's'
	keyclass = None

	#: Data format of DB values: s(tring), f(loat), d(ecimal), p(ickle)
	dataformat = 's'
	dataclass = None

	#: classattr Comparison function. Do not use touch this.
	cfunc = True

	#: The filename extension to use: bdb or index
	extension = 'bdb'

	def __init__(self, filename, keyformat=None, dataformat=None, dataclass=None, dbenv=None, autoopen=True):
		"""Main BDB DB wrapper

		:param filename: Base filename to use
		:keyword keyformat: Overrides cls.keyformat
		:keyword dataformat: Overrides cls.dataformat
		:keyword dataclass: Overrides cls.dataclass
		:keyword dbenv: Database environment
		:keyword autoopen: Automatically open DB

		"""
		# Filename
		self.filename = filename

		# EMEN2DBEnv
		self.dbenv = dbenv

		# Indexes
		self.index = {}
		self._truncate_index = False

		# BDB handle and open flags
		self.bdb = None
		self.DBOPENFLAGS = bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE
		self.DBSETFLAGS = []

		# Cached items
		self.cache = None
		self.cache_parents = collections.defaultdict(set) # temporary patch
		self.cache_children = collections.defaultdict(set) # temporary patch

		# What are we storing?
		self._setkeyformat(keyformat or self.keyformat)
		self._setdataformat(dataformat or self.dataformat)

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
			k1 = self.keyload(k1)

		if not k2:
			k2 = 0
		else:
			k2 = self.keyload(k2)

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

	def _setkeyformat(self, keyformat):
		# Set the DB key type. This will bind the correct
		# keyclass, keydump, keyload methods.
		if keyformat == 's':
			self.keyclass = unicode
			self.keydump = lambda x:str(x).encode('utf-8')
			self.keyload = lambda x:x.decode('utf-8')
		elif keyformat == 'd':
			self.keyclass = int
			self.keydump = str
			self.keyload = int
		elif keyformat == 'f':
			self.keyclass = float
			self.keydump = self._pickledump
			self.keyload = self._pickleload
		else:
			raise ValueError, "Invalid keyformat: %s. Supported: s(tring), d(ecimal), f(loat)"%keyformat

		self.keyformat = keyformat

	def _setdataformat(self, dataformat):
		# Set the DB data type. This will bind the correct
		# dataclass attribute, and datadump and dataload methods.
		if dataformat == 's':
			# String dataformat; use UTF-8 encoded strings.
			self.dataclass = unicode
			self.datadump = lambda x:x.encode('utf-8')
			self.dataload = lambda x:x.decode('utf-8')
		elif dataformat == 'd':
			# Decimal dataformat, use str encoded ints.
			self.dataclass = int
			self.datadump = str
			self.dataload = int
		elif dataformat == 'f':
			# Float dataformat; these do not sort natively, so pickle them.
			self.dataclass = float
			self.datadump = self._pickledump
			self.dataload = self._pickleload
		elif dataformat == 'p':
			# This DB stores a DBO as a pickle.
			if not self.dataclass:
				raise ValueError, "Data class required for pickled data."
			self.datadump = self._pickledump
			self.dataload = self._pickleload
		else:
			# Unknown dataformat.
			raise ValueError, "Invalid dataformat: %s. Supported: s(tring), d(ecimal), f(loat), p(ickle)"%dataformat

		self.dataformat = dataformat



	##### DB methods #####

	def open(self):
		"""Open the DB.	This is uses an implicit open transaction."""

		if self.bdb or self.cache:
			raise Exception, "DB already open"

		# Create the DB handle and set flags
		self.bdb = bsddb3.db.DB(self.dbenv.dbenv)

		# Create a memory only DB
		self.cache = bsddb3.db.DB(self.dbenv.dbenv)

		# Set DB flags, e.g. duplicate keys allowed
		for flag in self.DBSETFLAGS:
			self.bdb.set_flags(flag)
			self.cache.set_flags(flag)

		# Set a sort method
		if self.cfunc and self.keyformat in ['d', 'f']:
			self.bdb.set_bt_compare(self._cfunc_numeric)
			self.cache.set_bt_compare(self._cfunc_numeric)

		# Open the DB with the correct flags.
		fn = '%s.%s'%(self.filename, self.extension)
		self.bdb.open(filename=fn, dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)
		self.cache.open(filename=None, dbtype=bsddb3.db.DB_BTREE, flags=bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE)

	def close(self):
		"""Close the DB, and remove the BerkeleyDB handle."""
		self.bdb.close()
		self.bdb = None
		self.cache.close()
		self.cache = None



	##### Mapping methods #####

	def keys(self, txn=None):
		"""Mapping interface: keys. Requires txn.

		:keyword txn: Transaction
		:return: All keys in database, and cached keys.

		"""
		# Returns all keys in the database, plus keys in the cache
		return map(self.keyload, self.bdb.keys(txn)+self.cache.keys())

	def values(self, txn=None):
		"""Mapping interface: values. Requires txn.

		:keyword txn: Transaction
		:return: All values in database, and cached values.

		"""
		# Returns all values in the database, plus all cached items
		return [self.dataload(x) for x in self.bdb.values(txn)+self.cache.values()]

	def items(self, txn=None):
		"""Mapping interface: items. Requires txn.

		:keyword txn: Transaction
		:return: All items in database, and cached items.

		"""
		# Returns all the data in the database, plus all cached items
		return map(lambda x:(self.keyload(x[0]),self.dataload(x[1])), self.bdb.items(txn)+self.cache.items())

	def iteritems(self, txn=None, flags=0):
		"""Mapping interface: iteritems. Requires txn.

		:keyword txn: Transaction
		:yield: (key, value) for all items in database.

		"""
		# Scan accross the database, yielding key/value pairs.
		ret = []
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			yield (self.keyload(pair[0]), self.dataload(pair[1]))
			pair = cursor.next_nodup()
		cursor.close()

		for pair in self.cache.items():
			yield (self.keyload(pair[0]), self.dataload(pair[1]))

	def exists(self, key, txn=None, flags=0):
		"""Checks to see if key exists in BDB. Requires txn.

		Override this method to set a name policy. For instance, allowed
		or disallowed names, minimum length, maximum length, format, etc.

		:param key: Key
		:keyword txn: Transaction
		:return: True if key exists
		"""
		return self.bdb.exists(self.keydump(key), txn=txn, flags=flags) or self.cache.exists(self.keydump(key), flags=flags)

	# Compatibility.
	has_key = exists



	##### Cache items #####

	def addcache(self, item, txn=None):
		"""Add an item to the cache; used for loading from JSON/XML.

		These items will work normally (get, put, relationships, items, etc.)
		but exist in memory only, not in the DB.

		Requires the DB to be open and requires a txn.

		:keyword txn: Transaction
		:param item: Item to cache. Should be an instantiated DBObject.

		"""
		# if item.name in self.cache:
		# 	# raise KeyError, "Warning: Item %s already in cache, skipping"%item.name
		# 	pass
		# if self.get(item.name, txn=txn):
		# 	# raise emen2.db.exceptions.ExistingKeyError, "Item %s already in exists in database, skipping"%item.name
		# 	pass

		# Update parent/child relationships
		# print "Checking parents/children for %s"%item.name
		p = self.getindex('parents', txn=txn)
		c = self.getindex('children', txn=txn)
		if p and c:
			item.parents |= p.get(item.name)
			item.children |= c.get(item.name)
		
			for child in item.children:
				if self.cache.get(self.keydump(child)):
					i = self.dataload(self.cache.get(self.keydump(child)))
					i.parents.add(item.name)
					self.cache.put(self.keydump(i.name), self.datadump(i)) #, txn=txn
		
			for parent in item.parents:
				if self.cache.get(self.keydump(parent)):
					i = self.dataload(self.cache.get(self.keydump(parent)))
					i.children.add(item.name)
					self.cache.put(self.keydump(i.name), self.datadump(i)) #, txn=txn
		
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
		self.cache.put(self.keydump(item.name), self.datadump(item)) #, txn=txn



	##### Read #####

	def get(self, key, default=None, filt=True, txn=None, flags=0):
		"""Mapping interface: get.

		:param key: Key
		:keyword default: Default value if key not found
		:keyword filt: Flag to ignore KeyErrors
		:keyword txn: Transaction
		:return: Found value or default

		"""
		
		# Check BDB
		d = self.dataload(
			self.bdb.get(self.keydump(key), txn=txn, flags=flags) 
			or 
			self.cache.get(self.keydump(key), flags=flags)
			)
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
		self.bdb.put(self.keydump(key), self.datadump(data), txn=txn, flags=flags)
		emen2.db.log.commit("%s.put: %s"%(self.filename, key))

	# Dangerous!
	def truncate(self, txn=None, flags=0):
		"""Truncate BDB (e.g. 'drop table'). Transaction required.

		:keyword txn: Transaction

		"""
		# todo: Do more checking before performing a dangerous operation.
		self.bdb.truncate(txn=txn)
		self.cache.truncate()
		self.cache_children = {}
		self.cache_parents = {}
		emen2.db.log.commit("%s.truncate"%self.filename)

	# Also dangerous!
	def delete(self, key, txn=None, flags=0):
		"""Delete item; not supported on all DB types. Transaction required.

		:param key: Key to delete
		:keyword txn: Transaction

		"""
		# Read-only items can't be removed.
		# if key in self.cache:
		#	raise KeyError, "Cannot delete read-only item %s"%key
		# If the item exists, remove it.
		if self.exists(key, txn=txn):
			ret = self.bdb.delete(self.keydump(key), txn=txn, flags=flags)
			emen2.db.log.commit("%s.delete: %s"%(self.filename, key))





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
		return set(self.dataload(x) for x in r)

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
			r = self._get_method(cursor, self.keydump(key), self.dataformat)
		else:
			cursor = self.bdb.cursor(txn=txn)
			r = self._get_method(cursor, self.keydump(key), self.dataformat)
			cursor.close()

		if bulk and self.dataformat == 'p':
			r = set(self.dataload(x) for x in r)

		return r

	def put(self, *args, **kwargs):
		"""Not supported on indexes; use addrefs, removerefs."""
		raise Exception, "put not supported; use addrefs, removerefs"

	# ian: todo: allow min/max
	def keys(self, txn=None, flags=0):
		"""Accelerated keys. Transaction required.

		:keyword txn: Transaction

		"""
		keys = set(map(self.keyload, self.bdb.keys(txn)))
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
			data = self._get_method(cursor, pair[0], self.dataformat)
			if bulk and self.dataformat == "p":
				data = set(map(self.dataload, data))
			ret.append((self.keyload(pair[0]), data))
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
			pair = cursor.set_range(self.keydump(minkey))

		while pair != None:
			data = self._get_method(cursor, pair[0], self.dataformat)
			k = self.keyload(pair[0])
			if bulk and self.dataformat == "p":
				data = set(map(self.dataload, data))
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
			# processed += 1
			data = self._get_method(cursor, pair[0], self.dataformat)
			if bulk and self.dataformat == "p":
				data = set(map(self.dataload, data))

			c = data & itemscopy
			if c:
				itemscopy -= c
				found += len(c)
				# print "processed %s keys, %s items left to go"%
				#	(processed, lenitems-found)
				# ret[self.keyload(pair[0])] = c
				yield (self.keyload(pair[0]), c)

			if found >= lenitems:
				break
			else:
				pair = cursor.next_nodup()

		# print "Done; processed %s keys"%processed
		cursor.close()



	##### Write Methods #####

	def removerefs(self, key, items, txn=None):
		'''Remove references.

		:param key: Key
		:param items: References to remove
		:keyword txn: Transaction
		:return: Keys that no longer have any references

		'''
		if not items: return []

		delindexitems = []

		cursor = self.bdb.cursor(txn=txn)

		key = self.keyclass(key)
		items = map(self.dataclass, items)

		dkey = self.keydump(key)
		ditems = map(self.datadump, items)

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

		key = self.keyclass(key)
		items = map(self.dataclass, items)

		dkey = self.keydump(key)
		ditems = map(self.datadump, items)

		cursor = self.bdb.cursor(txn=txn)

		if not cursor.set(dkey):
			addindexitems.append(key)

		for ditem in ditems:
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
	string as the keyformat, except RecordDB, which uses ints.

	The sequence class attribute, if True, will allow sequence support for
	this DB. This is currently implemented using a separate BDB (to minimize
	locks), although at some point the
	BerkeleyDB Sequence may be used,

	Like EMEN2DB, most methods require a transaction. Additionally, because
	this class manages DBOs, most methods also require a Context.

	Adds a "keytype" attribute that is used as the DB name.

	Extends the following methods:
		__init__ 		Changes the filename slightly
		init			Supports sequences if allowed
		open			Also opens sequencedb
		close			Also cloes sequencdb and indexes
		exists			Handles items that will have automatically assigned names

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
		reindex			Calculate index updates
		_reindex		Write index updates
		openindex		Open an index, and store the handle in self.index
		getindex		Get an already open index, or open if necessary
		closeindex		Close an index

	'''

	dataformat = 'p'
	dataclass = None
	keytype = None


	def __init__(self, keytype=None, path=None, dataclass=None, *args, **kwargs):
		# Change the filename slightly
		dataclass = dataclass or self.dataclass
		keytype = keytype or self.dataclass.__name__
		path = path or keytype

		dbenv = kwargs.get('dbenv')
		self.path = str(path).lower()
		self.keytype = str(keytype).lower()
		self.dataclass = dataclass

		# Tell the data class what the keytype is.
		if self.keytype and self.dataclass:
			self.dataclass.keytype = keytype

		filename = os.path.join(self.path, self.keytype)

		d1 = os.path.join(dbenv.path, 'data', self.path)
		d2 = os.path.join(dbenv.path, 'data', self.path, 'index')
		for i in [d1, d2]:
			try: os.makedirs(i)
			except: pass

		return super(DBODB, self).__init__(filename, *args, **kwargs)

	def init(self):
		"""Add support for sequences."""
		self.sequencedb = None
		return super(DBODB, self).init()

	def open(self):
		"""Open the sequence with the main DB."""
		super(DBODB, self).open()
		self.sequencedb = bsddb3.db.DB(self.dbenv.dbenv)
		self.sequencedb.open(os.path.join('%s.sequence.bdb'%self.filename), dbtype=bsddb3.db.DB_BTREE, flags=self.DBOPENFLAGS)

	def close(self):
		"""Close the sequence, and any open indexes, with the main DB."""
		super(DBODB, self).close()
		self.sequencedb.close()
		self.sequencedb = None
		for k in self.index:
			self.closeindex(k)

	def exists(self, key, txn=None, flags=0):
		# Check if a key exists.
		# Names that are None or a negative int will be automatically assigned.
		# In this case, return immediately and don't acquire any locks.
		if key < 0 or key is None:
			return False
		return super(DBODB, self).exists(key, txn=txn, flags=flags)



	##### Sequences #####

	def update_names(self, items, txn=None):
		"""Update items with new names. Requires txn.

		:param items: Items to update.
		:keyword txn: Transaction.

		"""
		namemap = {}
		
		for item in items:
			if not self.exists(item.name, txn=txn):
				# Get a new name.
				newname = self._name_generator(item, txn=txn)

				try:
					newname = self.keyclass(newname)
				except:
					raise Exception, "Invalid name: %s"%newname

				# Check the name is still available, and acquire lock.
				if self.exists(newname, txn=txn, flags=bsddb3.db.DB_RMW):
					raise emen2.db.exceptions.ExistingKeyError, "%s already exists"%newname

				# Update the item's name.
				namemap[item.name] = newname
				item.__dict__['name'] = newname

		return namemap

	def _name_generator(self, item, txn=None):
		# Set name policy in this method.
		return unicode(item.name or emen2.db.database.getrandomid())

	def _incr_sequence(self, key='sequence', txn=None):
		# Update a sequence key. Requires txn.
		# The Sequence DB can handle multiple keys -- e.g., for
		# binaries, each day has its own sequence key.
		delta = 1
		
		val = self.sequencedb.get(key, txn=txn, flags=bsddb3.db.DB_RMW)
		if val == None:
			val = 0
		val = int(val)

		# Protect against overwriting items that might have been manually inserted.
		# counter = 0
		# while True:
		# 	if counter > 100000:
		# 		raise Exception, "Problem with counter. Please contact the administrator."
		# 	if self.bdb.exists(self.keydump(val), txn=txn):
		# 		print "Found item %s! Increasing counter."%val
		# 		val += 1
		# 		counter += 1
		# 	else:
		# 		break

		self.sequencedb.put(key, str(val+delta), txn=txn)
		emen2.db.log.commit("%s.sequence: %s"%(self.filename, val+delta))
		return val

	def get_max(self, key="sequence", txn=None):
		"""Return the current maximum item in the sequence. Requires txn.

		:keyword txn: Transaction
		"""
		sequence = self.sequencedb.get(key, txn=txn)
		if sequence == None:
			sequence = 0
		val = int(sequence)
		return val



	##### New items.. #####

	def new(self, *args, **kwargs):
		"""Returns new DBO. Requires ctx and txn.

		All the method args and keywords will be passed to the constructor.

		:keyword txn: Transaction
		:return: New DBO
		:exception ExistingKeyError:
		"""
		txn = kwargs.pop('txn', None) # Don't pass the txn..
		ctx = kwargs.get('ctx', None)
		inherit = kwargs.pop('inherit', [])

		item = self.dataclass(*args, **kwargs)

		for i in inherit:
			try:
				i = self.cget(i, filt=False, ctx=ctx, txn=txn)
			except (KeyError, SecurityError), inst:
				emen2.db.log.warn("Couldn't get inherited permissions from %s: %s"%(inherit, inst))
				continue				
			if i.get('permissions'):
				item.addumask(i.get('permissions'))
			if i.get('groups'):
				item.addgroup(i.get('groups'))
			item['parents'].add(i.name)

		# Acquire a write lock on this name.
		if self.exists(item.name, txn=txn, flags=bsddb3.db.DB_RMW):
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

	def items(self, ctx=None, txn=None):
		"""Context-aware items. Requires ctx and txn.

		:keyword ctx: Context
		:keyword txn: Transaction
		:return: (key, value) items that are accessible by the Context
		"""
		ret = []
		for k,v in self.bdb.items(txn)+self.cache.items():
			i = self.dataload(v)
			i.setContext(ctx)
			ret.append((self.keyload(k), i))
		return ret
	
	# def iteritems(self, ctx=None, txn=None):
		
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
		# Time and validation helper.
		t = emen2.db.database.gettime()
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db, keytype=self.keytype)

		# Updated items
		crecs = []
		
		# Updated indexes
		ind = collections.defaultdict(list)

		for updrec in items:
			name = updrec.get('name')
			
			# Get the existing item or create a new one.
			# Names can be unassigned (None, negative integer) or assigned (a string).
			# Some BDOs require names (paramdef, recorddef); 
			#	others (e.g. record, user) will assign the name in update_names.
			# This will acquire a write lock if there is an assigned name.
			if self.exists(name, txn=txn, flags=bsddb3.db.DB_RMW):
				# Get the existing item.
				orec = self.get(name, txn=txn, flags=bsddb3.db.DB_RMW)
				orec.setContext(ctx)
				if orec.get('uri'):
					raise emen2.db.exceptions.SecurityError, "Cannot modify read-only item %s"%orec.name
			else:
				# Create a new item.
				p = dict((k,updrec.get(k)) for k in self.dataclass.attr_required)
				orec = self.new(name=name, t=t, ctx=ctx, txn=txn, **p)

			# Update the item.
			orec.update(updrec, vtm=vtm, t=t)
			orec.validate()
			crecs.append(orec)

		# If we just wanted to validate the changes, return before writing changes.
		if not commit or not crecs:
			return crecs

		# Assign names for new items.
		# This will also update any relationships to uncommitted records.
		self.update_names(crecs, txn=txn)

		# Now that names are assigned, calculate the index updates.
		ind = self.reindex(crecs, ctx=ctx, txn=txn)

		# Write the items "for real."
		for crec in crecs:
			self.put(crec.name, crec, txn=txn)

		# Write index updates
		self._reindex_write(ind, ctx=ctx, txn=txn)

		emen2.db.log.info("Committed %s items"%(len(crecs)))
		return crecs

	def reindex(self, items, reindex=False, ctx=None, txn=None):
		"""Update indexes. This is really a private method.

		The original items will be retrieved and compared to the updated
		items. A set of index changes will be calculated, and then handed off
		to the _reindex_* methods. In some cases, these will be overridden
		or extended to handle special indexes -- such as parent/child
		relationships in RelateDB.
		
		:param items: Updated DBOs
		:keyword reindex:
		:keyword ctx: Context
		:keyword txn: Transaction

		"""
		# Updated indexes
		ind = collections.defaultdict(list)

		# Get changes as param:([name, newvalue, oldvalue], ...)
		for crec in items:
			# Get the current record for comparison of updated values.
			# Use an empty dict for new records so all keys
			# will seen as new (or if reindexing)
			# ian: todo: get or cget?
			if crec.isnew() or reindex:
				orec = {}
			else:
				orec = self.cget(crec.name, ctx=ctx, txn=txn) or {}

			for param in crec.changedparams(orec):
				# print "REINDEX:", param, crec.name, crec.get(param), orec.get(param)
				ind[param].append((crec.name, crec.get(param), orec.get(param)))

		# Return the index changes.
		return ind

	# .... the actual items need to be written ^^^ between these two vvv steps.

	def _reindex_write(self, ind, ctx=None, txn=None):
		"""(Internal) Write index updates."""
		# Parent/child relationships are a special case.
		# The other side of the relationship needs to be updated. 
		# Calculate the correct changes here, but do not
		# update the indexes yet. 
		parents = ind.pop('parents', None)
		children = ind.pop('children', None)

		# Update the parent child relationships.
		self._reindex_relink(parents, children, ctx=ctx, txn=txn)

		# Now, Update indexes.
		for k,v in ind.items():
			self._reindex_param(k, v, ctx=ctx, txn=txn)

	def _reindex_relink(self, parents, children, reindex=False, ctx=None, txn=None):
		"""(Internal) see RelateDB."""
		return

	def _reindex_param(self, param, changes, ctx=None, txn=None):
		"""(Internal) Reindex changes to a single parameter."""
		# If nothing changed, skip.
		if not changes:
			return

		# If we can't access the index, skip. (Raise Exception?)
		ind = self.getindex(param, txn=txn)
		if ind == None:
			return

		# Check that this key is currently marked as indexed
		pd = self.dbenv['paramdef'].cget(param, filt=False, ctx=ctx, txn=txn)
		vtm = emen2.db.datatypes.VartypeManager()
		vt = vtm.getvartype(pd.vartype)
		vt.pd = pd

		# Process the changes into index addrefs / removerefs
		try:
			addrefs, removerefs = vt.reindex(changes)
		except Exception, e:
			# print "Could not reindex param %s: %s"%(pd.name, e)
			# print changes
			return

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
		BinaryDB, or a complete and general index system as in RecordDB.

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
		emen2.db.log.info("Rebuilding indexes: Start")
		# ugly hack..
		self._truncate_index = True
		for k in self.index:
			self.index[k].truncate(txn=txn)

		# Do this in chunks of 10,000 items
		# Get all the keys -- do not include cached items
		keys = sorted(map(self.keyload, self.bdb.keys(txn)), reverse=True)
		for chunk in emen2.util.listops.chunk(keys, 10000):
			if chunk:
				emen2.db.log.info("Rebuilding indexes: %s ... %s"%(chunk[0], chunk[-1]))
			items = self.cgets(chunk, ctx=ctx, txn=txn)
			# Use self.reindex() instead of self.cputs() -- the data should
			# already be validated, so we can skip that step.
			# self.cputs(items, ctx=ctx, txn=txn)
			ind = self.reindex(items, reindex=True, ctx=ctx, txn=txn)
			self._reindex_write(ind, ctx=ctx, txn=txn)

		self._truncate_index = False
		emen2.db.log.info("Rebuilding indexes: Done")
	


	##### Query #####

	def query(self, c=None, mode='AND', subset=None, ctx=None, txn=None):
		"""Return a Query Constraint Group.

		You will need to call constraint.run() to execute the query,
		and constraint.sort() to sort the values.
		"""
		return emen2.db.query.Query(constraints=c, mode=mode, subset=subset, ctx=ctx, txn=txn, btree=self)



class RelateDB(DBODB):
	"""DBO DB with parent/child relationships between keys.

	Adds a maxrecuse attribute, which controls the maximum recursion level
	in relationships before giving up. If this is removed, problems may arise
	with circular relationships.

	Extends the following methods:
		openindex		Adds parent/child indexes
		expand			Adds support for "*" in names()

	Adds the following methods:
		tree			Returns relationship dict, one recurse level per key
		parents			Returns parents, multiple recurse levels per key
		children		Returns children, multiple recurse lvls per key
		siblings		Item siblings
		rel				General purpose relationship method
		pclink			Add a parent/child relationship
		pcunlink		Remove a parent/child relationship

	"""

	maxrecurse = emen2.db.config.get('params.MAXRECURSE', 50)

	def update_names(self, items, txn=None):
		# Update all the record's links
		namemap = super(RelateDB, self).update_names(items, txn=txn)
		for item in items:
			item.__dict__['parents'] = set([namemap.get(i,i) for i in item.parents])
			item.__dict__['children'] = set([namemap.get(i,i) for i in item.children])

	def openindex(self, param, txn=None):
		"""Extends openindex to add support for parents and children."""
		if param in ['children', 'parents']:
			filename = os.path.join(self.path, 'index', param)
			ind = IndexDB(filename=filename, keyformat=self.keyformat, dataformat=self.keyformat, dbenv=self.dbenv, autoopen=False)
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
				newkey = self.keyclass(key.replace('*', ''))
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
	def tree(self, names, recurse=1, rel='children', ctx=None, txn=None, **kwargs):
		"""See rel(), tree=True. Requires ctx and txn.

		Returns a tree structure of relationships. This will be a dict, with DBO
		names as keys, and one level of relationship for the value. It will
		recurse to the level specified by the recurse keyword.

		:return: Tree structure of relationships

		"""
		return self.rel(names, recurse=recurse, rel=rel, tree=True, ctx=ctx, txn=txn, **kwargs)

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
			parents, children, tree

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

	def relink(self, removerels=None, addrels=None, ctx=None, txn=None):
		"""Add and remove a number of parent-child relationships at once."""
		removerels = removerels or []
		addrels = addrels or []
		remove = collections.defaultdict(set)
		add = collections.defaultdict(set)
		ci = emen2.util.listops.check_iterable

		for k,v in removerels.items():
			for v2 in ci(v):
				remove[self.keyclass(k)].add(self.keyclass(v2))
		for k,v in addrels.items():
			for v2 in ci(v):
				add[self.keyclass(k)].add(self.keyclass(v2))

		items = set(remove.keys()) | set(add.keys())
		items = self.cgets(items, ctx=ctx, txn=txn)
		for item in items:
			item.children -= remove[item.name]
			item.children |= add[item.name]

		return self.cputs(items, ctx=ctx, txn=txn)

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
	def _reindex_relink(self, parents, children, ctx=None, txn=None):
		# (Internal) Relink relationships
		# This method will grab both items, and add or remove the rels from
		# each item, and then update the parents/children IndexDBs.

		indc = self.getindex('children', txn=txn)
		indp = self.getindex('parents', txn=txn)
		if not indc or not indp:
			raise KeyError, "Relationships not supported"

		# The names of new items.
		names = []

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
			names.append(name)

		for name, new, old in (children or []):
			old = old or set()
			new = new or set()
			for i in new - old:
				add.append((name, i))
			for i in old - new:
				remove.append((name, i))
			names.append(name)

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

		# print "p_add", p_add
		# print "p_remove", p_remove
		# print "c_add", c_add
		# print "c_remove", c_remove
		
		#if not indexonly:
		if True:
			# Go and fetch other items that we need to update
			names = set(p_add.keys()+p_remove.keys()+c_add.keys()+c_remove.keys())
			# print "All affected items:", names
			# Get and modify the item directly w/o Context:
			# Linking only requires write permissions
			# on ONE of the items.
			for name in names:
				try:
					rec = self.get(name, filt=False, txn=txn)
				except:
					# print "Couldn't link to missing item:", name
					continue

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
		new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) # rel.get(key, cursor=cursor)
		if key in cache:
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
				new = rel._get_method(cursor, rel.keydump(key), rel.dataformat) # rel.get(key, cursor=cursor)
				if key in cache:
					new |= cache.get(key, set())

				if new:
					stack[x+1] |= new #.extend(new)
					result[key] = new

			visited |= stack[x]

		visited |= stack[-1]
		cursor.close()
		return result, visited




__version__ = "$Revision$".split(":")[1][:-1].strip()
