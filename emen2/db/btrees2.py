import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import bsddb3
import cPickle as pickle
import sys
import time
import weakref



# Berkeley DB wrapper classes


class BTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	keys and data may be arbitrary pickleable types"""

	alltrees=weakref.WeakKeyDictionary()

	def __init__(self, name, filename=None, dbenv=None, nelem=0, keytype=None, cfunc=None, txn=None):
		#"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		#name is required, and will also be used as a filename if none is
		#specified. If relate is true, then parent/child and cousin relationships
		#between records are also supported. """
		BTree.alltrees[self] = 1	# we keep a running list of all trees so we can close everything properly

		self.name = name
		self.__setkeytype(keytype)

		cfunc = None
		if self.keytype in ("d", "f"):
			cfunc = self.__num_compare


		#else:
		#	raise Exception, "Invalid keytype %s"%keytype

		if filename == None:
			filename = name+".bdb"

		#global globalenv#, dbDBOPENFLAGS
		self.txn = None	# current transaction used for all database operations

		if not dbenv:
			dbenv = globalenv


		self.bdb = bsddb3.db.DB(dbenv)

		if cfunc is not None:
			self.bdb.set_bt_compare(cfunc)

		self.__setweakrefopen()


		self.bdb.open(filename, name, dbtype=bsddb3.db.DB_BTREE, flags=emen2.Database.database.DBOPENFLAGS)


	def __setkeytype(self, keytype):
		self.keytype = keytype

		if self.keytype == "d":
			self.set_typekey(self.__typekey_int)

		elif self.keytype == "f":
			self.set_typekey(self.__typekey_float)

		elif self.keytype == "s":
			self.set_typekey(self.__typekey_unicode)
			self.dumpkey = self.__dumpkey_unicode
			self.loadkey = self.__loadkey_unicode

		elif self.keytype == "ds":
			self.set_typekey(self.__typekey_unicode_int)
			self.dumpkey = self.__dumpkey_unicode_int
			self.loadkey = self.__loadkey_unicode_int


	def __num_compare(self, k1, k2):
		if not k1: k1 = 0
		else: k1 = pickle.loads(k1)

		if not k2: k2 = 0
		else: k2 = pickle.loads(k2)

		return cmp(k1, k2)


	# optional keytypes
	def __typekey_int(self, key):
		if key is None: key = 0
		return int(key)


	def __typekey_float(self, key):
		if key is None: key = 0
		return float(key)


	def __typekey_unicode(self, key):
		if key is None: key = ''
		return unicode(key)


	def __typekey_unicode_int(self, key):
		if key is None: key = 0
		try: return int(key)
		except: return unicode(key)


	# special key dumps
	def __dumpkey_unicode(self, key):
		return key.encode("utf-8")


	def __dumpkey_unicode_int(self, key):
		if isinstance(key, int): return pickle.dumps(int(key))
		return pickle.dumps(unicode(key).encode("utf-8"))


	# special key loads
	def __loadkey_unicode(self, key):
		return key.decode("utf-8")


	def __loadkey_unicode_int(self, key):
		key = pickle.loads(key)
		if isinstance(key,int): return key
		return key.encode("utf-8")


	# enforce key types
	def typekey(self, key):
		return key

	def dumpkey(self, key):
		return pickle.dumps(self.typekey(key))

	def loadkey(self, key):
		return pickle.loads(key)


	# default keytypes and datatypes
	def typedata(self, data):
		return data

	def dumpdata(self, data):
		return pickle.dumps(self.typedata(data))

	def loaddata(self, data):
		return pickle.loads(data)



	# change key/data behavior
	def set_typekey(self, func):
		self.typekey = func

	def set_typedata(self, func):
		self.typedata = func




	def __setweakrefopen(self):
		BTree.alltrees[self] = 1


	def __str__(self):
		return "<Database.BTree instance: %s>" % self.name


	def __del__(self):
		self.close()


	def close(self):
		if self.bdb is None:
			return

		if g.DEBUG>2:
			g.log.msg('LOG_DEBUG', '\nbegin')

		#g.log.msg('LOG_DEBUG', 'main')
		del self.alltrees[self]
		self.bdb.close()
		#g.log.msg('LOG_DEBUG', '/main')

		self.bdb=None


	def truncate(self, txn=None, flags=0):
		self.bdb.truncate(txn=txn)


	def sync(self, txn=None, flags=0):
		if self.bdb is not None:
			self.bdb.sync()


	def set_txn(self,txn):
		"""sets the current transaction. Note that other python threads will not be able to use this
		BTree until it is 'released' by setting the txn back to None"""
		if txn==None:
			self.txn=None
			return
		if self.txn:
			g.log.msg('LOG_WARNING',"Transaction deadlock %s"%unicode(self))
		counter = 0
		while self.txn:
			time.sleep(.1)
			counter += 1
			g.log.msg('LOG_INFO', 'thread sleeping on transaction msg #%d' % counter)
		self.txn=txn



	# these methods temp. disabled due to difficulty passing txn
	#
	# def __len__(self, txn=txn):
	# 	return len(self.bdb, txn=txn)
	#
	#
	# def __setitem__(self, key, data, txn=txn):
	# 	if data == None:
	# 		self.__delitem__(self.typekey(key), txn=txn)
	# 	else:
	# 		#self.bdb.put(pickle.dumps(self.typekey(key)), pickle.dumps(self.typedata(data)), txn=self.txn)
	# 		self.bdb.put(self.dumpkey(key), self.dumpdata(data), txn=txn)
	#
	#
	# def __getitem__(self, key, txn=txn):
	# 	data = self.bdb.get(self.dumpkey(key), txn=self.txn)
	# 	if data is None:
	# 		#Ed: for Backwards compatibility raise TypeError, should be KeyError
	# 		raise TypeError, 'Key Not Found: %r' % key
	# 		# raise KeyError, 'Key Not Found: %r' % key
	# 	else:
	# 		return self.loaddata(data)
	#
	#
	# def __delitem__(self, key, txn=txn):
	# 	self.bdb.delete(self.dumpkey(key), txn=txn)
	#
	#
	# def __contains__(self, key, txn=txn):
	# 	return self.bdb.has_key(self.dumpkey(key), txn=txn)


	def keys(self, txn=None):
		# ian: todo: submit bug report for bdb.keys not accepting kwargs, despite documentation
		return map(self.loadkey, self.bdb.keys(txn))


	def values(self, txn=None):
		#return reduce(set.union, map(self.loaddata, self.bdb.values())) #(self.loaddata(x) for x in self.bdb.values())) #txn=txn
		# set() needed if empty
		return reduce(set.union, (self.loaddata(x) for x in self.bdb.values(txn)), set()) #txn=txn


	def items(self, txn=None):
		return map(lambda x:(self.loadkey(x[0]),self.loaddata(x[1])), self.bdb.items(txn)) #txn=txn


	def has_key(self, key, txn=None):
		return self.bdb.has_key(self.dumpkey(key), txn=txn) #, txn=txn


	def exists(self, key, txn=None, flags=0):
		return self.bdb.exists(self.dumpkey(key), txn=txn, flags=flags)


	# DB_subscript with txn; passes exception instead of default
	def sget(self, key, txn=None, flags=0):
		try:
			return self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		except Exception, inst:
			raise KeyError, "No such key %s (%s)"%(key,inst)


	def get(self, key, default=None, txn=None, flags=0):
		#print "get: key is %s %s -> %s %s -> %s %s"%(type(key), key, type(self.typekey(key)), self.typekey(key), type(self.dumpkey(key)), self.dumpkey(key))
		try:
			return self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		except:
			return default


	def set(self, key, data, txn=None, flags=0):
		"Alternative to x[key]=val with transaction set"
		if data == None:
			return self.bdb.delete(self.dumpkey(key), txn=txn, flags=flags)
		return self.bdb.put(self.dumpkey(key), self.dumpdata(data), txn=txn, flags=flags)


	def update(self, d, txn=None, flags=0):
		d = dict(map(lambda x:self.typekey(x[0]), self.typedata(x[1]), d.items()))
		for i,j in dict.items():
			self.bdb.put(self.dumpkey(i), self.dumpdata(j), txn=txn, flags=flags)
			#self.set(i,j,txn=txn)







class RelateBTree(BTree):
	"""BTree with parent/child/cousin relationships between keys"""


 	def __init__(self, *args, **kwargs):
 		BTree.__init__(self, *args, **kwargs)
		self.relate = 1
		txn = kwargs.get("txn")

		dbenv = kwargs.get("dbenv")
		filename = kwargs.get("filename")
		name = kwargs.get("name")

		# Parent keyed list of children
		self.pcdb = bsddb3.db.DB(dbenv)
		self.pcdb.open(filename+".pc", name, dbtype=bsddb3.db.DB_BTREE, flags=emen2.Database.database.DBOPENFLAGS)

		# Child keyed list of parents
		self.cpdb = bsddb3.db.DB(dbenv)
		self.cpdb.open(filename+".cp", name, dbtype=bsddb3.db.DB_BTREE, flags=emen2.Database.database.DBOPENFLAGS)

		# lateral links between records (nondirectional), 'getcousins'
		self.reldb = bsddb3.db.DB(dbenv)
		self.reldb.open(filename+".rel", name, dbtype=bsddb3.db.DB_BTREE, flags=emen2.Database.database.DBOPENFLAGS)


	def __str__(self):
		return "<Database.RelateBTree instance: %s>" % self.name



	def close(self):
		if self.bdb is None:
			return

		#try:
		self.pcdb.close()
		self.cpdb.close()
		self.reldb.close()
		#except Exception, e:

		self.bdb.close()
		self.bdb = None



	def sync(self):
		#try:
		self.bdb.sync()
		self.pcdb.sync()
		self.cpdb.sync()
		self.reldb.sync()
		#except:
		#	pass


	def __relate(self, db1, db2, method, tag1, tag2, txn=None):

		# key = normal key
		# data = set of keys

		if not self.relate:
			raise Exception,"relate option required in BTree"

		tag1, tag2 = self.typekey(tag1), self.typekey(tag2)

		if tag1 == None or tag2 == None:
			return

		if not self.has_key(tag2, txn=txn) or not self.has_key(tag1, txn=txn):
			raise KeyError,"Nonexistent key in %s <-> %s"%(tag1, tag2)



		try:
			o = pickle.loads(db1.get(self.dumpkey(tag1), txn=txn, flags=bsddb3.db.DB_RMW))
		except:
			o = set()



		if (method == "add" and tag2 not in o) or (method == "remove" and tag2 in o):
			getattr(o, method)(tag2)
			db1.put(self.dumpkey(tag1), pickle.dumps(o), txn=txn)




		try:
			o = pickle.loads(db2.get(self.dumpkey(tag2), txn=txn, flags=bsddb3.db.DB_RMW))
		except:
			o = set()

		if (method == "add" and tag1 not in o) or (method == "remove" and tag1 in o):
			getattr(o, method)(tag1)
			db2.put(self.dumpkey(tag2), pickle.dumps(o), txn=txn)



	def pclink(self, parenttag, childtag, txn=None):
		"""This establishes a parent-child relationship between two tags.
		The relationship may also be named. That is the parent may
		get a list of children only with a specific paramname. Note
		that empty strings and None cannot be used as tags"""
		self.__relate(self.pcdb, self.cpdb, "add", parenttag, childtag, txn=txn)


	def pcunlink(self, parenttag, childtag, txn=None):
		"""Removes a parent-child relationship, returns quietly if relationship did not exist"""
		self.__relate(self.pcdb, self.cpdb, "remove", parenttag, childtag, txn=txn)


	def link(self, tag1, tag2, txn=None):
		"""Establishes a lateral relationship (cousins) between two tags"""
		self.__relate(self.reldb, self.reldb, "add", parenttag, childtag, txn=txn)


	def unlink(self, tag1, tag2, txn=None):
		"""Removes a lateral relationship (cousins) between two tags"""
		self.__relate(self.reldb, self.reldb, "remove", parenttag, childtag, txn=txn)


	def parents(self, tag, txn=None):
		"""Returns a list of the tag's parents"""
		if not self.relate:
			raise Exception,"relate option required"


		try:
			return pickle.loads(self.cpdb.get(self.dumpkey(tag), txn=txn))
		except:
			return set()


	def children(self, tag, txn=None):
		"""Returns a list of the tag's children. If paramname is
		omitted, all named and unnamed children will be returned"""
		if not self.relate:
			raise Exception,"relate option required"


		try:
			return pickle.loads(self.pcdb.get(self.dumpkey(tag), txn=txn))
			#if paramname :
			#	return set(x[0] for x in c if x[1]==paramname)
			#else: return c
		except:
			return set()


	def cousins(self, tag, txn=None):
		"""Returns a list of tags related to the given tag"""
		if not self.relate:
			raise Exception,"relate option required"

		try:
			return pickle.loads(self.reldb.get(self.dumpkey(tag),txn=txn))
		except:
			return set()











class FieldBTree(BTree):
	"""This is a specialized version of the BTree class. This version uses type-specific
	keys, and supports efficient key range extraction. The referenced data is a python list
	of 32-bit integers with no repeats allowed. The purpose of this class is to act as an
	efficient index for records. Each FieldBTree will represent the global index for
	one Field within the database. Valid key types are:
	"d" - integer keys
	"f" - float keys (64 bit)
	"s" - string keys
	"""
	def __init__(self, *args, **kwargs):
		self.__indexkeys = kwargs.pop("indexkeys", None)
		#self.__indexkeys = None
		kwargs.pop('keyindex', None)
		BTree.__init__(self, *args, **kwargs)



	def __str__(self):
		return "<Database.FieldBTree instance: %s>" % self.name


	def typedata(self, data):
		return set(map(int, data))


	def removeref(self, key, item, txn=None):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		o.remove(item)
		if not o and self.__indexkeys != None:
			self.__indexkeys.removeref(self.name, key, txn=txn)
		return self.set(key, o or None, txn=txn)


	def removerefs(self, key, items, txn=None):
		"""The keyed value must be a list of objects. list of 'items' will be removed from this list"""

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		o -= set(items)
		if not o and self.__indexkeys != None:
			self.__indexkeys.removeref(self.name, key, txn=txn)
		return self.set(key, o or None, txn=txn)


	def testref(self, key, item, txn=None):
		"""Tests for the presence if item in key'ed index """
		o = self.get(key, txn=txn) or set()
		return item in o


	def addref(self, key, item, txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		if self.__indexkeys != None and not o:
			self.__indexkeys.addref(self.name, key, txn=txn)
		o.add(item)
		return self.set(key, o, txn=txn)


	def addrefs(self, key, items, txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'items' is a list to be added to the list. """

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		if self.__indexkeys != None and not o:
			self.__indexkeys.addref(self.name, key, txn=txn)
		o |= set(items)
		return self.set(key, o, txn=txn)


	def items(self, mink=None, maxk=None, txn=None):

		if mink is None and maxk is None:
			items = BTree.items(self)
		elif mink is not None and maxk is None:
			mink = self.typekey(mink)
			items = [(mink, self.get(mink, txn=txn))]
		else:
			print "cur"
			cur = self.bdb.cursor(txn=txn)
			items = []
			if mink is not None:
				mink=self.typekey(mink)
				entry = cur.set_range(pickle.pickle.dumps(mink))
			else:
				entry = cur.first()

			print "entry"

			if maxk is not None:
				maxk=self.typekey(maxk)

				while entry is not None:
					key, value = entry
					key = key.decode('utf-8')
					value = pickle.loads(value)
					if maxk is not None and key >= maxk:
						break
					items.append((key,value))
					entry = cur.next()
			cur.close()

		return items


	def keys(self, mink=None, maxk=None, txn=None):
		"""Returns a list of valid keys, mink and maxk allow specification of
 		minimum and maximum key values to retrieve"""
		if mink == None and maxk == None:
			return BTree.keys(self, txn)
		return set(x[0] for x in self.items(mink, maxk, txn=txn))


	def values(self, mink=None, maxk=None, txn=None):
		"""Returns a single list containing the concatenation of the lists of,
 		all of the individual keys in the mink to maxk range"""
		if mink == None and maxk == None: return BTree.values(self)
		return reduce(set.union, (set(x[1] or []) for x in self.items(mink, maxk, txn=txn)), set())





class IndexKeyBTree(FieldBTree):
	"""index of all param keys for quick searching (in 2-stages: find param/keys, then lookup recids)"""

	def __str__(self):
		return "<Database.IndexKeyBTree instance: %s>" % self.name


	def keys(self, txn=None):
		return map(self.loadkey, self.bdb.keys(txn))

	def values(self, txn=None):
		return map(self.loaddata, self.bdb.values(txn=txn))

	def typedata(self, data):
		return set(data)


	def removeref(self, key, item, txn=None):
		"""like FieldBTree method, but doesn't delete key if empty"""

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		o.remove(item)
		return self.set(key, o, txn=txn)


	def addref(self, key, item, txn=None):
		"""like FieldBTree method, but doesn't delete key if empty"""

		o = self.get(key, txn=txn, flags=bsddb3.db.DB_RMW) or set()
		o.add(item)
		return self.set(key, o, txn=txn)


