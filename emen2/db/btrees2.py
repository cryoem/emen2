import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import bsddb3
from cPickle import dumps, loads
import sys
import time
import weakref



dbopenflags=bsddb3.db.DB_CREATE
DEBUG = 0 #TODO consolidate debug flag

# 
# class IndexDB(bsddb3.dbobj.DB):
# 	
# 	def __dumpkey(self, key):
# 		return dumps(self.__keyconv(key))
# 		
# 		
# 	def __dumpvalue(self, value):
# 		return dumps(set([self.__valueconv(i) for i in value]))
# 
# 	
# 	# self.bdb.index_append(key,item,txn=txn)
# 	def index_append(self, key, item, txn=None):
# 		value = self.index_get(key, txn=txn)
# 		value.add(self.__valueconv(value))
# 		return self.index_put(key, value, txn=txn)
# 		
# 		
# 		
# 	# self.bdb.index_extend(key,list(set(items)),txn=self.txn)	
# 	def index_extend(self, key, items, txn=None):
# 		value = self.index_get(key, txn=txn)
# 		value |= set([self.__valueconv(i) for i in items])
# 		return self.index_put(key, value, txn=txn)		
# 
# 
# 	# return self.bdb.index_get(key,txn=txn)
# 	# get(key, default=None, txn=None, flags=0, dlen=-1, doff=-1)
# 	def index_get(self, key, default=None, txn=None, flags=0):
# 		return loads(self.get(self.__dumpkey(key), default=default, txn=txn, flags=flags))
# 
# 
# 	# return self.bdb.index_has_key(key,txn=txn)
# 	# has_key(key, txn=None)
# 	def index_has_key(self, key, txn=None):
# 		return self.has_key(self.__dumpkey(key), txn=txn)
# 		
# 
# 	# return self.bdb.index_items(mink,maxk,txn=self.txn)
# 	# items(txn=None)
# 	def index_items(self, mink=None, maxk=None, txn=None):
# 		return [(loads(k),loads(v)) for k,v in self.items(txn=txn)]
# 
# 
# 	# return self.bdb.index_keys(mink,maxk,txn=self.txn)
# 	# keys(txn=None)
# 	def index_keys(self, mink=None, maxk=None, txn=None):
# 		return [loads(k) for k in self.keys(txn=txn)]
# 
# 
# 
# 	# return self.bdb.index_values(mink, maxk, txn=self.txn)
# 	# values(txn=None)
# 	def index_values(self, mink=None, maxk=None, txn=None):
# 		return [loads(k) for k in self.values(txn=txn)]
# 		
# 
# 	# self.bdb.index_put(key,val,txn=self.txn)
# 	# put(key, data, txn=None, flags=0, dlen=-1, doff=-1)
# 	def index_put(self, key, data, txn=None, flags=0):
# 		return self.put(self.__dumpkey(key), self.__dumpvalue(value), txn=txn, flags=flags)
# 
# 
# 	# self.bdb.index_remove(key,item,txn=self.txn)
# 	# delete(key, txn=None, flags=0)
# 	def index_remove(self, key, item, txn=None):
# 		value = self.index_get(key, txn=txn)
# 		value.remove(self.__valueconv(item))
# 		return self.index_put(key, value, txn=txn)
# 		
# 
# 	# self.bdb.index_removelist(key,items,txn=self.txn)
# 	def index_removelist(self, key, items, txn=None):
# 		value = self.index_get(key, txn=txn)
# 		value -= set([self.__valueconv(i) for i in items])
# 		return self.index_put(key, value, txn=txn)
# 		
# 
# 	# return self.bdb.index_test(key,item,txn=self.txn)
# 	# """Tests for the presence if item in key'ed index """
# 	def index_test(self, key, item, txn=None):
# 		value = self.index_get(key)
# 		return item in value
# 
# 
# 	# self.bdb.index_update(dict,txn=self.txn)
# 	def index_update(self, d, txn=None):
# 		print "Unsupported? DB.index_update"
# 		for k,v in d.items():
# 			self.index_put(k,v)
# 			
# 	
# 	
# 	# self.pcdb.index_open(file+".pc","d",name,db.DB_BTREE,dbopenflags)
# 	# open(filename, dbname=None, dbtype=DB_UNKNOWN, flags=0, mode=0660, txn=None)
# 	def index_open(self, filename, keytype="s", dbname=None, dbtype=None, flags=0, mode=0660, txn=None):
# 		self.keytype = keytype
# 
# 		if keytype == "f":
# 			self.__keyconv = float
# 		elif keytype == "d":
# 			self.__keyconv = int
# 		elif keytype == "s":
# 			self.__keyconv = str
# 		else:
# 			raise Exception, "Invalid index type %s"%keytype
# 				
# 		return self.open(filename, dbname=dbname, dbtype=dbtype, flags=flags, mode=mode, txn=txn)






class BTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	keys and data may be arbitrary pickleable types"""
	
	alltrees=weakref.WeakKeyDictionary()
	
	def __init__(self, name, filename=None, dbenv=None, nelem=0, relate=0):
		"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		name is required, and will also be used as a filename if none is
		specified. If relate is true, then parent/child and cousin relationships
		between records are also supported. """
		
		global globalenv,dbopenflags
		#BTree.alltrees[self] = 1	# we keep a running list of all trees so we can close everything properly
		self.__setweakrefopen()
		
		self.name = name
		self.txn = None	# current transaction used for all database operations
		
		if not dbenv:
			dbenv = globalenv

		self.bdb = bsddb3.db.DB(dbenv)

		if filename == None:
			filename = name+".bdb"

		self.bdb.open(filename, name, bsddb3.db.DB_BTREE, dbopenflags)

		if relate:
			self.relate=1
		
			# Parent keyed list of children
			self.pcdb=bsddb3.db.DB(dbenv)
			self.pcdb.open(filename+".pc", name, bsddb3.db.DB_BTREE, dbopenflags)
			
			# Child keyed list of parents
			self.cpdb=bsddb3.db.DB(dbenv)
			self.cpdb.open(filename+".cp", name, bsddb3.db.DB_BTREE, dbopenflags)
			
			# lateral links between records (nondirectional), 'getcousins'
			self.reldb=bsddb3.db.DB(dbenv)
			self.reldb.open(filename+".rel", name, bsddb3.db.DB_BTREE, dbopenflags)

		else:
			self.relate=0


	def __setweakrefopen(self):
		BTree.alltrees[self] = 1
		

	def __str__(self):
		return "<Database.BTree instance: %s>" % self.name


	def __del__(self):
		self.close()


	def close(self):
		if self.bdb is None:
			return
			
		if DEBUG>2:
			g.debug.msg('LOG_ERROR', '\nbegin')

		try:
			self.pcdb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/pc')
			self.cpdb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/cp')
			self.reldb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/rel')
		except:
			pass

		if DEBUG>2:
			g.debug.msg('LOG_ERROR', 'main')
		self.bdb.close()
		if DEBUG>2:
			g.debug.msg('LOG_ERROR', '/main')

		self.bdb=None

	
	def sync(self):
		#try:
		if self.relate:
			self.bdb.sync()
			self.pcdb.sync()
			self.cpdb.sync()
			self.reldb.sync()
		#except:
		#	pass
		

	def set_txn(self,txn):
		"""sets the current transaction. Note that other python threads will not be able to use this
		BTree until it is 'released' by setting the txn back to None"""
		if txn==None: 
			self.txn=None
			return
		if self.txn:
			g.debug.msg('LOG_WARNING',"Transaction deadlock %s"%str(self))
		while self.txn:
			time.sleep(.1)
		self.txn=txn



	def __relate(self, db1, db2, method, tag1, tag2, txn=None):

		if not self.relate:
			raise Exception,"relate option required in BTree"
		if not txn:	txn = self.txn

		tag1, tag2 = self.__typekey(tag1), self.__typekey(tag2)

		if tag1 == None or tag2 == None:
			return
				
		if not self.has_key(tag2, txn=txn) or not self.has_key(tag1, txn=txn):
			raise KeyError,"Nonexistent key in %s <-> %s"%(tag1, tag2)
		
		try:
			o = loads(db1.get(dumps(tag1), txn=txn))
		except:
			o = set()	
		
		if (method == "add" and tag2 not in o) or (method == "remove" and tag2 in o):	
			getattr(o, method)(tag2)
			db1.put(dumps(tag1), dumps(o), txn=txn)
					
		try:
			o = loads(_db2.get(dumps(tag2), txn=txn))
		except:
			o = set()

		if (method == "add" and tag1 not in o) or (method == "remove" and tag1 in o):
			getattr(o, method)(tag1)
			db2.put(dumps(tag2), dumps(o), txn=txn)
				
					

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
		if not txn:	txn = self.txn	
		tag = self.__typekey(tag)

		try:
			return loads(self.cpdb.get(dumps(tag), txn=txn))
		except:
			return set()
		
		
	def children(self, tag, txn=None):
		"""Returns a list of the tag's children. If paramname is
		omitted, all named and unnamed children will be returned"""
		if not self.relate:
			raise Exception,"relate option required"
		if not txn:	txn = self.txn
		tag = self.__typekey(tag)		
		
		try:
			return loads(self.pcdb.get(dumps(tag), txn=txn))
			#if paramname :
			#	return set(x[0] for x in c if x[1]==paramname)
			#else: return c
		except:
			return set()
	
	
	def cousins(self, tag, txn=None):
		"""Returns a list of tags related to the given tag"""
		if not self.relate:
			raise Exception,"relate option required"
		if not txn:	txn = self.txn
		tag = self.__typekey(tag)
		
		try:
			return loads(self.reldb.get(dumps(tag),txn=txn))
		except:
			return set()


	def __typekey(self, key):
		return key
	

	def __typedata(self, data):
		return data


	def __len__(self):
		return len(self.bdb)


	def __setitem__(self, key, data):
		if data == None:
			self.__delitem__(self.__typekey(key))
		else:
			self.bdb.put(dumps(self.__typekey(key)), dumps(self.__typedata(data)), txn=self.txn)


	def __getitem__(self, key):
		return loads(self.bdb.get(dumps(self.__typekey(key)), txn=self.txn))


	def __delitem__(self, key):
		self.bdb.delete(dumps(self.__typekey(key)), txn=self.txn)


	def __contains__(self, key):
		return self.bdb.has_key(dumps(self.__typekey(key)), txn=self.txn)


	def keys(self, txn=None):
		return map(lambda x:loads(x), self.bdb.keys())


	def values(self, txn=None):
		if not txn: txn=self.txn
		return map(lambda x:loads(x), self.bdb.values()) #txn=txn


	def items(self, txn=None):
		if not txn: txn=self.txn
		return map(lambda x:(loads(x[0]),loads(x[1])), self.bdb.items()) #txn=txn


	def has_key(self, key, txn=None):
		if not txn: txn=self.txn
		return self.bdb.has_key(dumps(self.__typekey(key))) #, txn=txn


	def get(self, key, txn=None):
		if not txn: txn=self.txn
		try:
			return loads(self.bdb.get(dumps(self.__typekey(key)),txn=txn))
		except:
			return None
	

	def set(self, key, data, txn=None):
		"Alternative to x[key]=val with transaction set"
		if not txn: txn=self.txn
		if data == None:
			return self.bdb.delete(dumps(self.__typekey(key)), txn=txn)
		return self.bdb.put(dumps(self.__typekey(key)), dumps(self.__typedata(data)), txn=txn)


	def update(self, d, txn=None):
		if not txn: txn=self.txn
		d = dict(map(lambda x:self.__typekey(x[0]), self.__typedata(x[1]), d.items()))
		for i,j in dict.items():
			self.bdb.put(dumps(i), dumps(j), txn=txn)
			#self.set(i,j,txn=txn)


		
		
		
		
class IntBTree(BTree):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	key are integers and data may be an arbitrary pickleable type"""

	# IntBTree.alltrees[self]=1		# we keep a running list of all trees so we can close everything properly

	def __typekey(self, key):
		return int(key)
	
	def __setweakrefopen(self):
		IntBTree.alltrees[self] = 1




		
		
class FieldBTree(BTree):
	"""This is a specialized version of the BTree class. This version uses type-specific 
	keys, and supports efficient key range extraction. The referenced data is a python list
	of 32-bit integers with no repeats allowed. The purpose of this class is to act as an
	efficient index for records. Each FieldBTree will represent the global index for
	one Field within the database. Valid dey types are:
	"d" - integer keys
	"f" - float keys (64 bit)
	"s" - string keys
	"""

	# def __init__(self, name, filename=None, dbenv=None, nelem=0, relate=0):
	def __init__(self, name, filename=None, keytype="s", dbenv=None, nelem=0):
		BTree.__init__(self, name=name, filename=filename, dbenv=dbenv, nelem=nelem)
					
		if keytype == "d":
			self.__typekey = self.__typekey_int
		elif keytype == "f":
			self.__typekey = self.__typekey_float
		elif keytype == "s":
			self.__typekey = self.__typekey_str
		else:
			raise Exception, "Invalid keytype %s"%keytype

		self.keytype=keytype

			
		
	def __typekey_int(self, key):
		return int(key)

	def __typekey_float(self, key):
		return float(key)	

	def __typekey_str(self, key):
		return unicode(key).lower()
	
	def __typedata(self, data):
		return set(map(int, data))
		
	
			
	def removeref(self, key, item, txn=None):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		if not txn: txn=self.txn
		o = self.get(key, txn=txn) or set()
		o.remove(item)
		return self.set(key, o, txn=txn)
		#self.bdb.index_remove(key,item,txn=self.txn)
		
		
	def removerefs(self, key, items, txn=None):
		"""The keyed value must be a list of objects. list of 'items' will be removed from this list"""
		if not txn: txn=self.txn
		o = self.get(key, txn=txn) or set()
		o -= set(items)
		return self.set(key, o, txn=txn)
		#key=self.typekey(key)
		#self.bdb.index_removelist(key,items,txn=self.txn)

		
	def testref(self, key, item, txn=None):
		"""Tests for the presence if item in key'ed index """
		if not txn: txn=self.txn
		o = self.get(key, txn=txn) or set()
		return item in o
		#key=self.typekey(key)
		#return self.bdb.index_test(key,item,txn=self.txn)
	

	def addref(self, key, item, txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		if not txn: txn=self.txn
		o = self.get(key, txn=txn) or set()
		o.add(item)
		return self.set(key, o, txn=txn)
		#key=self.typekey(key)
		#self.bdb.index_append(key,item,txn=txn)
		

	def addrefs(self, key, items, txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'items' is a list to be added to the list. """
		if not txn: txn=self.txn
		o = self.get(key, txn=txn) or set()
		o |= set(items)
		return self.set(key, o, txn=txn)
		#key=self.typekey(key)
		#self.bdb.index_extend(key,list(set(items)),txn=self.txn)
	
	
# 	def __len__(self):
# 		"Number of elements in the database. Warning, this isn't transaction protected..."
# 		return len(self.bdb)
# #		if (self.len<0) : self.keyinit()
# #		return self.len
# 
# 	def __setitem__(self,key,val):
# 		key=self.typekey(key)
# 		if (val==None) :
# 			self.__delitem__(key)
# 		else : self.bdb.index_put(key,val,txn=self.txn)
# 
# 	def __getitem__(self,key):
# 		key=self.typekey(key)
# 		return self.bdb.index_get(key,txn=self.txn)
# 
# 	def __delitem__(self,key):
# 		key=self.typekey(key)
# 		self.bdb.delete(key,txn=self.txn)
# 
# 	def __contains__(self,key):
# 		key=self.typekey(key)
# 		return self.bdb.index_has_key(key,txn=self.txn)
# 
# 	def keys(self,mink=None,maxk=None,txn=None):
# 		"""Returns a list of valid keys, mink and maxk allow specification of
# 		minimum and maximum key values to retrieve"""
# 		if not txn : txn=self.txn
# 		mink=self.typekey(mink)
# 		maxk=self.typekey(maxk)
# 		return self.bdb.index_keys(mink,maxk,txn=self.txn)
# 
# 	def values(self,mink=None,maxk=None,txn=None):
# 		"""Returns a single list containing the concatenation of the lists of,
# 		all of the individual keys in the mink to maxk range"""
# 		if not txn : txn=self.txn
# 		mink=self.typekey(mink)
# 		maxk=self.typekey(maxk)
# 		return self.bdb.index_values(mink, maxk, txn=self.txn)
# 
# 	def items(self,mink=None,maxk=None,txn=None):
# 		if not txn : txn=self.txn
# 		mink=self.typekey(mink)
# 		maxk=self.typekey(maxk)
# 		return self.bdb.index_items(mink,maxk,txn=self.txn)
# 
# 	def has_key(self,key,txn=None):
# 		if not txn : txn=self.txn
# 		key=self.typekey(key)
# 		return self.bdb.index_has_key(key,txn=txn)
# 	
# 	def get(self,key,txn=None):
# 		key=self.typekey(key)
# 		return self.bdb.index_get(key,txn=txn)
# 	
# 	def set(self,key,val,txn=None):
# 		"Alternative to x[key]=val with transaction set"
# 		key=self.typekey(key)
# 		if (val==None) :
# 			self.bdb.delete(key,txn=txn)
# 		else : self.bdb.index_put(key,val,txn=txn)
# 
# 	def update(self,dict):
# 		self.bdb.index_update(dict,txn=self.txn)