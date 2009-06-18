import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

from bsddb3 import db
from cPickle import dumps, loads
import sys
import time
import weakref


dbopenflags=db.DB_CREATE
DEBUG = 0 #TODO consolidate debug flag

class BTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	keys and data may be arbitrary pickleable types"""
	
	alltrees=weakref.WeakKeyDictionary()
	def __init__(self,name,file=None,dbenv=None,nelem=0,relate=0):
		"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		name is required, and will also be used as a filename if none is
		specified. If relate is true, then parent/child and cousin relationships
		between records are also supported. """
		global globalenv,dbopenflags
		BTree.alltrees[self]=1		# we keep a running list of all trees so we can close everything properly
		self.name = name
		self.txn=None	# current transaction used for all database operations
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.open(file,name,db.DB_BTREE,dbopenflags)
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)

		if relate :
			self.relate=1
		
			# Parent keyed list of children
			self.pcdb=db.DB(dbenv)
			self.pcdb.open(file+".pc",name,db.DB_BTREE,dbopenflags)
			
			# Child keyed list of parents
			self.cpdb=db.DB(dbenv)
			self.cpdb.open(file+".cp",name,db.DB_BTREE,dbopenflags)
			
			# lateral links between records (nondirectional), 'getcousins'
			self.reldb=db.DB(dbenv)
			self.reldb.open(file+".rel",name,db.DB_BTREE,dbopenflags)
		else : self.relate=0

	def __str__(self): return "<Database.BTree instance: %s>" % self.name

	def __del__(self):
		self.close()

	def close(self):
		if self.bdb is None: return
		if DEBUG>2: g.debug.msg('LOG_ERROR', '\nbegin')
		try:
			self.pcdb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/pc')
			self.cpdb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/cp')
			self.reldb.close()
			if DEBUG>2: g.debug.msg('LOG_ERROR', '/rel')
		except: pass
		if DEBUG>2: g.debug.msg('LOG_ERROR', 'main')
		self.bdb.close()
		if DEBUG>2: g.debug.msg('LOG_ERROR', '/main')
		self.bdb=None
	
	def sync(self):
		try:
			self.bdb.sync()
			self.pcdb.sync()
			self.cpdb.sync()
			self.reldb.sync()
		except: pass
		
	def set_txn(self,txn):
		"""sets the current transaction. Note that other python threads will not be able to use this
		BTree until it is 'released' by setting the txn back to None"""
		if txn==None: 
			self.txn=None
			return
		if self.txn: g.debug.msg('LOG_WARNING',"Transaction deadlock %s"%str(self))
		while self.txn: time.sleep(.1)
		self.txn=txn

	def rmvlist(self,key,item):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		a=self[key]
		a.remove(item)
		self[key]=a

	def addvlist(self,key,item):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		if (self.has_key(key)):
			self[key]=(self[key]+[item])
		else: self[key]=[item]

	def pclink(self,parenttag,childtag,txn=None):
		"""This establishes a parent-child relationship between two tags.
		The relationship may also be named. That is the parent may
		get a list of children only with a specific paramname. Note
		that empty strings and None cannot be used as tags"""
		if not txn : txn=self.txn
		if not self.relate: raise Exception,"relate option required in BTree"
		if parenttag==None or childtag==None or parenttag=="" or childtag=="" : return
				
		if not self.has_key(childtag,txn) : 
			if DEBUG: print "%s %s"%(childtag,parenttag)
			raise KeyError,"Cannot link nonexistent key '%s'"%childtag
		if not self.has_key(parenttag,txn) : 
			raise KeyError,"Cannot link nonexistent key '%s'"%parenttag
		try:
			o=loads(self.pcdb.get(dumps(parenttag),txn=self.txn))
		except:
			o=[]

		if not childtag in o:
			o.append(childtag)
			self.pcdb.put(dumps(parenttag),dumps(o),txn=txn)
			
			try:
				o=loads(self.cpdb.get(dumps(childtag),txn=self.txn))
			except:
				o=[]
			
			o.append(parenttag)
			self.cpdb.put(dumps(childtag),dumps(o),txn=txn)
#			print self.children(parenttag)
		
	def pcunlink(self,parenttag,childtag,paramname="",txn=None):
		"""Removes a parent-child relationship, returns quietly if relationship did not exist"""
		if not txn : txn=self.txn
		if not self.relate : raise Exception,"relate option required"
		
		try:
			o=loads(self.pcdb.get(dumps(parenttag),txn=self.txn))
		except:
			return
			

		if DEBUG:
			print "trying to unlink parent %s child %s"%(parenttag,childtag)
			print (childtag,paramname)
			print o				
				
						
		if not (childtag,paramname) in o: 
#		if not childtag in o: 
			return

		o.remove((childtag,paramname))
		self.pcdb.put(dumps(parenttag),dumps(o),txn=self.txn)
		
		o=loads(self.cpdb.get(dumps(childtag),txn=self.txn))
		o.remove(parenttag)
		self.cpdb.put(dumps(childtag),dumps(o),txn=self.txn)
		
	def link(self,tag1,tag2,txn=None):
		"""Establishes a lateral relationship (cousins) between two tags"""
		if not txn : txn=self.txn
		if not self.relate : raise Exception,"relate option required"
		
		if not self.has_key(tag1,txn) : raise KeyError,"Cannot link nonexistent key '%s'"%tag1
		if not self.has_key(tag2,txn) : raise KeyError,"Cannot link nonexistent key '%s'"%tag2
		
		try:
			o=loads(self.reldb.get(dumps(tag1),txn=self.txn))
		except:
			o=[]
			
		if not tag2 in o:
			o.append(tag2)
			self.reldb.put(dumps(tag1),dumps(o),txn=self.txn)
	
			try:
				o=loads(self.reldb.get(dumps(tag2),txn=self.txn))
			except:
				o=[]
			
			o.append(tag1)
			self.reldb.put(dumps(tag2),dumps(o),txn=self.txn)
		
			
	def unlink(self,tag1,tag2,txn=None):
		"""Removes a lateral relationship (cousins) between two tags"""
		if not txn : txn=self.txn

		if not self.relate : raise Exception,"relate option required"
		
		try:
			o=loads(self.rekdb.get(dumps(tag1),txn=self.txn))
		except:
			return
			
		if not tag2 in o: return
		o.remove(tag2)
		self.reldb.put(dumps(tag1),dumps(o),txn=self.txn)
		
		o=loads(self.reldb.get(dumps(tag2),txn=self.txn))
		o.remove(tag1)
		self.cpdb.put(dumps(tag2),dumps(o),txn=self.txn)
	
	def parents(self,tag):
		"""Returns a list of the tag's parents"""
		if not self.relate : raise Exception,"relate option required"
		
		try:
			return loads(self.cpdb.get(dumps(tag),txn=self.txn))
		except:
			return []
		
		
	def children(self,tag,paramname=None):
		"""Returns a list of the tag's children. If paramname is
		omitted, all named and unnamed children will be returned"""
		if not self.relate : raise Exception,"relate option required"
#		tag=str(tag)
		
		try:
			
			c=loads(self.pcdb.get(dumps(tag),txn=self.txn))
#			print c
			if paramname :
				return set(x[0] for x in c if x[1]==paramname)
			else: return c
		except:
			return set()
	
	def cousins(self,tag):
		"""Returns a list of tags related to the given tag"""
		if not self.relate : raise Exception,"relate option required"
#		tag=str(tag)
		
		try:
			return loads(self.reldb.get(dumps(tag),txn=self.txn))
		except:
			return []

	def __len__(self):
		return len(self.bdb)

	def __setitem__(self,key,val):

		if (val==None) :
			self.__delitem__(key)
		else : self.bdb.put(dumps(key),dumps(val),txn=self.txn)

	def __getitem__(self,key):
		return loads(self.bdb.get(dumps(key),txn=self.txn))

	def __delitem__(self,key):
		self.bdb.delete(dumps(key),txn=self.txn)

	def __contains__(self,key):
		return self.bdb.has_key(dumps(key),txn=self.txn)

	def keys(self):
		return map(lambda x:loads(x),self.bdb.keys())

	def values(self):
		return map(lambda x:loads(x),self.bdb.values())

	def items(self):
		return map(lambda x:(loads(x[0]),loads(x[1])),self.bdb.items())

	def has_key(self,key,txn=None):
		if not txn : txn=self.txn
		#return self.bdb.has_key(dumps(key),txn=txn)
		return self.bdb.has_key(dumps(key),txn) # hari put this line, commented previous
	def get(self,key,txn=None):
		return loads(self.bdb.get(dumps(key),txn=txn))
	
	def set(self,key,val,txn=None):
		"Alternative to x[key]=val with transaction set"
		if (val==None) :
			self.bdb.delete(dumps(key),txn=txn)
		else : self.bdb.put(dumps(key),dumps(val),txn=txn)

	def update(self,dict):
		for i,j in dict.items(): self[i]=j

	#def create_sequence(self):
		#dbseq = self.bdb.sequence_create()
		#dbseq.init_value()
		#dbseq.set_range(0, 2000000000)
		#dbseq.set_cachesize(1)
		#dbseq.open(None, 'sequence', 0|db.DB_CREATE|db.DB_THREAD)
		#return dbseq
		
class IntBTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	key are integers and data may be an arbitrary pickleable type"""
	alltrees=weakref.WeakKeyDictionary()
	def __init__(self,name,file=None,dbenv=None,nelem=0,relate=0):
		"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		name is required, and will also be used as a filename if none is
		specified. This class is identical to 'BTree', but keys may only be integers.
		This permits a substantial improvement in performance in certain cases.
		If relate is true, then parent/child and cousin relationships
		between records are also supported. """
		global globalenv,dbopenflags
		IntBTree.alltrees[self]=1		# we keep a running list of all trees so we can close everything properly
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.open(file,name,db.DB_BTREE,dbopenflags)
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)
		self.txn=None	# current transaction used for all database operations

		if relate :
			self.relate=1
		
			# Parent keyed list of children
			self.pcdb=db.DB(dbenv)
			self.pcdb.index_open(file+".pc","d",name,db.DB_BTREE,dbopenflags)
			
			# Child keyed list of parents
			self.cpdb=db.DB(dbenv)
			self.cpdb.index_open(file+".cp","d",name,db.DB_BTREE,dbopenflags)
			
			# lateral links between records (nondirectional), 'getcousins'
			self.reldb=db.DB(dbenv)
			self.reldb.index_open(file+".rel","d",name,db.DB_BTREE,dbopenflags)
		else : self.relate=0

	def __del__(self):
		self.close()

	def close(self):
		if self.bdb is None: return
		try:
			self.pcdb.close()
			self.cpdb.close()
			self.reldb.close()
		except: pass
		self.bdb.close()
		self.bdb=None
	
	def sync(self):
		try:
			self.bdb.sync()
			self.pcdb.sync()
			self.cpdb.sync()
			self.reldb.sync()
		except: pass
		
	def set_txn(self,txn):
		"""sets the current transaction. Note that other python threads will not be able to use this
		BTree until it is 'released' by setting the txn back to None"""
		if txn==None: 
			self.txn=None
			return
		if self.txn: g.debug.msg('LOG_WARNING',"Transaction deadlock %s"%str(self))
		while self.txn :
			time.sleep(.1)
		self.txn=txn

	def rmvlist(self,key,item):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		key=int(key)
		a=self[key]
		a.remove(item)
		self[key]=a

	def addvlist(self,key,item):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		key=int(key)
		if (self.has_key(key)):
			self[key]=(self[key]+[item])
		else: self[key]=[item]

	def pclink(self,parenttag,childtag,txn=None):
		"""This establishes a parent-child relationship between two tags.
		Note that empty strings and None cannot be used as tags"""
		if not txn: txn=self.txn
		if not self.relate : raise Exception,"relate option required in BTree"
		if parenttag==None or childtag==None : return
		parenttag=int(parenttag)
		childtag=int(childtag)
		
		if not self.has_key(childtag,txn) : 
			raise KeyError,"Cannot link nonexistent key '%d'"%childtag
		if not self.has_key(parenttag,txn) : 
			raise KeyError,"Cannot link nonexistent key '%d'"%parenttag
		
		self.pcdb.index_append(parenttag,childtag,txn=txn)
		self.cpdb.index_append(childtag,parenttag,txn=txn)

		
	def pcunlink(self,parenttag,childtag,txn=None):
		"""Removes a parent-child relationship, returns quietly if relationship did not exist"""
		if not txn: txn=self.txn
		if not self.relate : raise Exception,"relate option required"
		parenttag=int(parenttag)
		childtag=int(childtag)
		
		self.pcdb.index_remove(parenttag,childtag,txn=txn)
		self.cpdb.index_remove(childtag,parenttag,txn=txn)
		
	def link(self,tag1,tag2,txn=None):
		"""Establishes a lateral relationship (cousins) between two tags"""
		if not txn: txn=self.txn
		if not self.relate : raise Exception,"relate option required"
		tag1=int(tag1)
		tag2=int(tag2)
		
		if not self.has_key(tag1,txn) : raise KeyError,"Cannot link nonexistent key '%s'"%tag1
		if not self.has_key(tag2,txn) : raise KeyError,"Cannot link nonexistent key '%s'"%tag2
		
#		 self.reldb.index_append(tag1,tag2,txn=txn)
#		 self.reldb.index_append(tag2,tag1,txn=txn)
		self.reldb.index_append(tag1,tag2)
		self.reldb.index_append(tag2,tag1)
		
	def unlink(self,tag1,tag2,txn=None):
		"""Removes a lateral relationship (cousins) between two tags"""
		if not txn: txn=self.txn
		if not self.relate : raise Exception,"relate option required"
		tag1=int(tag1)
		tag2=int(tag2)
		
		self.reldb.index_remove(tag1,tag2,txn=txn)
		self.reldb.index_remove(tag2,tag1,txn=txn)
			
	def parents(self,tag):
		"""Returns a list of the tag's parents"""
		if not self.relate : raise Exception,"relate option required"
		
		ret=self.cpdb.index_get(int(tag),txn=self.txn)
		if ret==None: return []
		return ret
		
		
	def children(self,tag):
		"""Returns a list of the tag's children."""
		if not self.relate : raise Exception,"relate option required"
		return  self.pcdb.index_get(int(tag),txn=self.txn)

	
	def cousins(self,tag):
		"""Returns a list of tags related to the given tag"""
		if not self.relate : raise Exception,"relate option required"
		
		ret=self.reldb.index_get(int(tag),txn=self.txn)
		if ret==None: return [ ]
		return ret


	def __len__(self):
		return len(self.bdb)

	def __setitem__(self,key,val):
		key=int(key)
		if (val==None) :
			self.__delitem__(key,txn=self.txn)
		else : self.bdb.put(dumps(key),dumps(val),txn=self.txn)

	def __getitem__(self,key):
		key=int(key)
		#print key
		return loads(self.bdb.get(dumps(key),txn=self.txn))

	def __delitem__(self,key):
		key=int(key)
		self.bdb.delete(dumps(key),txn=self.txn)

	def __contains__(self,key):
		key=int(key)
		return self.bdb.has_key(dumps(key),txn=self.txn)

	def keys(self):
		return map(lambda x:loads(x),self.bdb.keys())

	def values(self):
		return map(lambda x:loads(x),self.bdb.values())

	def items(self):
		return map(lambda x:(loads(x[0]),loads(x[1])),self.bdb.items())

	def has_key(self,key,txn=None):
		if not txn : txn=self.txn
		key=int(key)
		#return self.bdb.has_key(dumps(key),txn=txn)
		return self.bdb.has_key(dumps(key),txn)
	def get(self,key,txn=None):
		if not txn : txn=self.txn
		key=int(key)
		return loads(self.bdb.get(dumps(key),txn=txn))
	
	def set(self,key,val,txn=None):
		"Alternative to x[key]=val with transaction set"
		if not txn : txn=self.txn
		key=int(key)
		if (val==None) :
			self.bdb.delete(dumps(key),txn=txn)
		else : self.bdb.put(dumps(key),dumps(val),txn=txn)

	def update(self,dict):
		for i,j in dict.items(): self[int(i)]=j

	#def create_sequence(self):
		#dbseq = db.DBSequence(self.bdb)
		#dbseq.init_value(0)
		#dbseq.set_range((0, 2000000000))		# technically 64 bit integers are allowed, but we'll stick with 32 bits for now
		#dbseq.set_cachesize(1)
		#dbseq.open(key='sequence', flags=db.DB_CREATE|db.DB_THREAD)
		#return dbseq

		
class FieldBTree(object):
	"""This is a specialized version of the BTree class. This version uses type-specific 
	keys, and supports efficient key range extraction. The referenced data is a python list
	of 32-bit integers with no repeats allowed. The purpose of this class is to act as an
	efficient index for records. Each FieldBTree will represent the global index for
	one Field within the database. Valid dey types are:
	"d" - integer keys
	"f" - float keys (64 bit)
	"s" - string keys
	"""
	alltrees=weakref.WeakKeyDictionary()
	def __init__(self,name,file=None,keytype="s",dbenv=None,nelem=0):
		global globalenv,dbopenflags
		"""
		globalenv=db.DBEnv()
		globalenv.set_cachesize(0,256000000,4)		# gbytes, bytes, ncache (splits into groups)
		globalenv.set_data_dir(".")
		globalenv.open("./data/home" ,db.DB_CREATE+db.DB_INIT_MPOOL)
		"""
		FieldBTree.alltrees[self]=1		# we keep a running list of all trees so we can close everything properly
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.index_open(file,keytype,name,db.DB_BTREE,dbopenflags)
		self.keytype=keytype
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)
		self.txn=None	# current transaction used for all database operations
		self.file=file


	def __del__(self):
		self.close()
#		print("bdb %s close"%self.file)
		
	def close(self):
		if self.bdb is None: return
		self.bdb.close()
		self.bdb=None

	def sync(self):
		try:
			self.bdb.sync()
		except: pass
		
	def set_txn(self,txn):
		"""sets the current transaction. Note that other python threads will not be able to use this
		BTree until it is 'released' by setting the txn back to None"""
		if txn==None: 
			self.txn=None
		else:
			if self.txn: 
				g.debug.msg('LOG_ERROR',"Transaction deadlock %s"%str(self))
			while self.txn: time.sleep(.1)
			self.txn=txn
	
	def typekey(self,key):
		if key==None: return None
		if self.keytype=="f" :
			try: return float(key)
			except: return float()
		if self.keytype=="d" :
			try: return int(key)
			except: return int()
		try: return str(key).lower()
		except: return unicode(key).encode("utf-8").lower()
			
	def removeref(self,key,item,txn=None):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		if not txn : txn=self.txn
		key=self.typekey(key)
		self.bdb.index_remove(key,item,txn=self.txn)
		
	def removerefs(self,key,items,txn=None):
		"""The keyed value must be a list of objects. list of 'items' will be removed from this list"""
		if not txn : txn=self.txn
		key=self.typekey(key)
		self.bdb.index_removelist(key,items,txn=self.txn)

		
	def testref(self,key,item,txn=None):
		"""Tests for the presence if item in key'ed index """
		if not txn : txn=self.txn
		key=self.typekey(key)
		return self.bdb.index_test(key,item,txn=self.txn)
	
	def addref(self,key,item,txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		if not txn : txn=self.txn
		key=self.typekey(key)
		#self.bdb.index_append(key,item,txn=self.txn)
		self.bdb.index_append(key,item)
		
	def addrefs(self,key,items,txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'items' is a list to be added to the list. """
		if not txn : txn=self.txn
		key=self.typekey(key)
		self.bdb.index_extend(key,list(items),txn=self.txn)
	
	def __len__(self):
		"Number of elements in the database. Warning, this isn't transaction protected..."
		return len(self.bdb)
#		if (self.len<0) : self.keyinit()
#		return self.len

	def __setitem__(self,key,val):
		key=self.typekey(key)
		if (val==None) :
			self.__delitem__(key)
		else : self.bdb.index_put(key,val,txn=self.txn)

	def __getitem__(self,key):
		key=self.typekey(key)
		return self.bdb.index_get(key,txn=self.txn)

	def __delitem__(self,key):
		key=self.typekey(key)
		self.bdb.delete(key,txn=self.txn)

	def __contains__(self,key):
		key=self.typekey(key)
		return self.bdb.index_has_key(key,txn=self.txn)

	def keys(self,mink=None,maxk=None,txn=None):
		"""Returns a list of valid keys, mink and maxk allow specification of
		minimum and maximum key values to retrieve"""
		if not txn : txn=self.txn
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_keys(mink,maxk,txn=self.txn)

	def values(self,mink=None,maxk=None,txn=None):
		"""Returns a single list containing the concatenation of the lists of,
		all of the individual keys in the mink to maxk range"""
		if not txn : txn=self.txn
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_values(mink, maxk, txn=self.txn)

	def items(self,mink=None,maxk=None,txn=None):
		if not txn : txn=self.txn
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_items(mink,maxk,txn=self.txn)

	def has_key(self,key,txn=None):
		if not txn : txn=self.txn
		key=self.typekey(key)
		return self.bdb.index_has_key(key,txn=txn)
	
	def get(self,key,txn=None):
		key=self.typekey(key)
		print key
		return self.bdb.index_get(key,txn=txn)
	
	def set(self,key,val,txn=None):
		"Alternative to x[key]=val with transaction set"
		key=self.typekey(key)
		if (val==None) :
			self.bdb.delete(key,txn=txn)
		else : self.bdb.index_put(key,val,txn=txn)

	def update(self,dict):
		self.bdb.index_update(dict,txn=self.txn)

class MemBTree(object):
	"""This class has the same interface as the FieldBTree object above, but is a simple
	python dictionary in ram. This is used for speed in preindexing when importing
	large numbers of records."""
	def __init__(self,name,file=None,keytype="s",dbenv=None,nelem=0):
		"""In this sepcialized ram version, name, file dbenv and nelem are stored but ignored during use"""
		self.bdb={}
		self.keytype=keytype
		self.bdbname=name
		self.bdbfile=file
		self.bdbenv=dbenv
		self.bdbnelem=nelem

	def set_txn(self,txn):
		return

	def typekey(self,key):
		if key==None or key=="None" : return None
		if self.keytype=="f" : 
#			try:
			return float(key)
#			except: 
#				print "Invalid float(%s)"%key
#				return(0.0)
		if self.keytype=="d":
			# try block: ian
#			try:
			return int(key)
#			except:
#				print "Invalid int(%s)"%key
#				return 0
			
		result = str(key)
		#print 'TYPEKEY::: %r' % result
		return result
			
	def removeref(self,key,item,txn=None):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		key=self.typekey(key)
		try: self.bdb[key].remove(item)
		except: pass
		
	def removerefs(self, key, items, txn=None):
		key=self.typekey(key)
		for item in items:
			self.removeref(key, item)
		
	def addref(self,key,item,txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		key=self.typekey(key)
		try: self.bdb[key].append(item)
		except: self.bdb[key]=[item]


	def addrefs(self,key,items,txn=None):
		"""The keyed value must be a list, and is created if nonexistant. 'items' is a list to be added to the list. """
		key=self.typekey(key)
		try:
			self.bdb[key].extend(list(items))
		except:
			self.bdb[key]=list(items)
		#self.bdb.index_extend(key,list(items),txn=self.txn)


	def close(self):
		self.bdb=None

	def __len__(self):
		return len(self.bdb)

	def __setitem__(self,key,val):
		key=self.typekey(key)
		if (val==None) :
			self.__delitem__(key)
		else : self.bdb[key]=[val]

	def __getitem__(self,key):
		key=self.typekey(key)
		return self.bdb[key]

	def __delitem__(self,key):
		key=self.typekey(key)
		del self.bdb[key]

	def __contains__(self,key):
		key=self.typekey(key)
		return self.bdb.has_key(key)

	def keys(self,mink=None,maxk=None,txn=None):
		"""Returns a list of valid keys, mink and maxk allow specification of
		minimum and maximum key values to retrieve"""
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		if mink and maxk : k=[i for i in self.bdb.keys() if i>=mink and i<=maxk]
		elif mink : k=[i for i in self.bdb.keys() if i>=mink]
		elif maxk : k=[i for i in self.bdb.keys() if i<=maxk]
		else: k=self.bdb.keys()
		
		return k

	def values(self,mink=None,maxk=None,txn=None):
		"""Returns a single list containing the concatenation of the lists of,
		all of the individual keys in the mink to maxk range"""
		v=[]
		k=self.keys(mink,maxk)
		for i in k: 
			try: v.extend(self.bdb[i])
			except: pass
		return v

	def items(self,mink=None,maxk=None,txn=None):
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		if mink and maxk : k=[i for i in self.bdb.items() if i[0]>=mink and i[0]<=maxk]
		elif mink : k=[i for i in self.bdb.items() if i[0]>=mink]
		elif maxk : k=[i for i in self.bdb.items() if i[0]<=maxk]
		else: k=self.bdb.items()
		
		return k

	def has_key(self,key,txn=None):
		key=self.typekey(key)
		return self.bdb.has_key(key)

	def get(self,key,txn=None):
		key=self.typekey(key)
		return self[key]

	def set(self,key,val,txn=None):
		key=self.typekey(key)
		return self[key]

	def update(self,dict):
		for i in dict.items():
			try: k,v=(self.typekey(i[0]),list(i[1]))
			except: continue
			self[k]=v
