# $Id$

import cPickle as pickle
import sys
import time
import weakref
import collections

import bsddb3


import emen2.db.config
g = emen2.db.config.g()

try:
	import emen2.db.bulk
	bulk = emen2.db.bulk
except:
	bulk = None
	g.warn("Not using bulk interface")



def n_int(inp):
	'''wrapper for int if keys contain decimal points can be turned on by
		uncommenting lines below
	'''
	try: return int(inp)
	except:
		if isinstance(inp, (str, unicode)) and inp.count('.') == 1:
			return int(inp.split('.', 1)[0])
		else:
			raise
	return result



# Berkeley DB wrapper classes

class BTree(object):
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary.
	Key may be and data may be any pickle-able Python type, but unicode/int/float key and data
	types are also supported with some bonuses."""

	alltrees = weakref.WeakKeyDictionary()
	DBSETFLAGS = []

	def __init__(self, filename=None, dbenv=None, nelem=0, keytype=None, datatype=None, cfunc=True, txn=None):
		"""Main BDB BTree wrapper"""

		# we keep a running list of all trees so we can close everything properly
		BTree.alltrees[self] = 1

		self.__setkeytype(keytype)
		self.__setdatatype(datatype)

		# Set a BTree sort method
		_cfunc = None
		if self.keytype in ("d", "f"):
			_cfunc = self.__num_compare


		self.filename = filename

		if not dbenv:
			raise ValueError, "No DBEnv specified for BTree open"

		self.dbenv = dbenv

		self.bdb = bsddb3.db.DB(self.dbenv)
		for flag in self.DBSETFLAGS:
			self.bdb.set_flags(flag)

		if cfunc and _cfunc:
			self.bdb.set_bt_compare(_cfunc)

		self.__setweakrefopen()

		# g.log.msg("LOG_DEBUG","Opening %s.bdb"%self.filename)
		self.bdb.open(self.filename+".bdb", dbtype=bsddb3.db.DB_BTREE, flags=g.DBOPENFLAGS)


	def __setkeytype(self, keytype):
		if not keytype:
			keytype = "s"

		self.keytype = keytype

		# ian: todo: convert records bdb to use new d format for keys
		if self.keytype == "d":
			self.typekey = int
			self.dumpkey = str
			self.loadkey = int

		elif self.keytype == "f":
			self.typekey = float

		elif self.keytype == "s":
			self.typekey = unicode
			self.dumpkey = lambda x:x.encode("utf-8")
			self.loadkey = lambda x:x.decode("utf-8")


	def __setdatatype(self, datatype):
		self.datatype = datatype

		if self.datatype == "d":
			self.dumpdata = str #lambda x:str(int(x))
			self.loaddata = int

		elif self.datatype == "s":
			self.dumpdata = lambda x:x.encode("utf-8")
			self.loaddata = lambda x:x.decode("utf-8")


	def __num_compare(self, k1, k2):
		if not k1: k1 = 0
		else: k1 = self.loadkey(k1)

		if not k2: k2 = 0
		else:k2 = self.loadkey(k2)

		return cmp(k1, k2)


	# pickle chokes on None; tested 'if data' vs 'if data!=None', simpler is faster
	def __loadpickle(self, data):
		if data: return pickle.loads(data)


	# default key types
	def typekey(self, key):
		"""Convert key to self.keytype"""
		return key

	def dumpkey(self, key):
		"""Convert key to BDB string key"""
		return pickle.dumps(self.typekey(key))

	def loadkey(self, key):
		"""Convert BDB key to self.keytype"""
		return pickle.loads(key)

	# default datatypes
	def typedata(self, data):
		"""Convert data to self.datatype"""
		return data

	def dumpdata(self, data):
		"""Convert data to BDB string data"""
		return pickle.dumps(data)

	def loaddata(self, data):
		"""Convert BDB data to self.datatype"""
		if data != None: return pickle.loads(data)


	# keep track of open BDB's
	def __setweakrefopen(self):
		BTree.alltrees[self] = 1


	def __str__(self):
		return "<emen2.db.btrees2.BTree instance: %s>"%self.filename


	def __del__(self):
		self.close()


	def close(self):
		"""Close BDB and cleanup"""

		if self.bdb is None:
			return

		del self.alltrees[self]

		# g.log.msg("LOG_DEBUG","Closing %s"%self.filename)
		self.bdb.close()

		self.bdb=None


	def truncate(self, txn=None, flags=0):
		"""Truncate BDB (e.g. 'drop table')"""

		self.bdb.truncate(txn=txn)


	def sync(self, txn=None, flags=0):
		"""Flush BDB cache to disk"""

		if self.bdb is not None:
			self.bdb.sync()


	def keys(self, txn=None):
		return map(self.loadkey, self.bdb.keys(txn))


	def values(self, txn=None):
		return [self.loaddata(x) for x in self.bdb.values(txn)]


	def items(self, txn=None):
		return map(lambda x:(self.loadkey(x[0]),self.loaddata(x[1])), self.bdb.items(txn)) #txn=txn


	def has_key(self, key, txn=None):
		return self.bdb.has_key(self.dumpkey(key), txn=txn) #, txn=txn


	def exists(self, key, txn=None, flags=0):
		"""Checks to see if key exists in BDB"""
		return self.bdb.exists(self.dumpkey(key), txn=txn, flags=flags)


	# DB_subscript with txn; passes exception instead of default
	def sget(self, key, txn=None, flags=0):
		"""Raises exception if key does not exists. Used because subscript (e.g. dict["key"]) type access does not accept arguments (e.g. txn)"""
		d = self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		if d == None:
			raise KeyError, "No such key %s"%(key)
		return d


	def gets(self, keys, txn=None, flags=0):
		return map(self.loaddata, [self.bdb.get(self.dumpkey(i), txn=txn, flags=flags) for i in keys])
		
		

	def get(self, key, default=None, txn=None, flags=0):
		"""Same as dict.get, with txn"""
		d = self.loaddata(self.bdb.get(self.dumpkey(key), txn=txn, flags=flags))
		if d == None:
			return default
		return d


	# ian: todo: Why isn't this put?
	def set(self, key, data, txn=None, flags=0):
		"""Set key/value, with txn."""
		if data == None:
			if self.bdb.exists(self.dumpkey(key), txn=txn):
				return self.bdb.delete(self.dumpkey(key), txn=txn, flags=flags)
			return
		return self.bdb.put(self.dumpkey(key), self.dumpdata(data), txn=txn, flags=flags)


	# ian: todo: use cursor for speed?
	def update(self, d, txn=None, flags=0):
		"""Same as dict.update, with txn"""
		d = dict(map(lambda x:self.typekey(x[0]), self.typedata(x[1]), d.items()))
		for i,j in dict.items():
			self.bdb.put(self.dumpkey(i), self.dumpdata(j), txn=txn, flags=flags)






class RelateBTree(BTree):
	"""BTree with parent/child/cousin relationships between keys"""

	def __init__(self, *args, **kwargs):
		sequence = kwargs.pop("sequence", False)

		BTree.__init__(self, *args, **kwargs)

		txn = kwargs.get("txn")
		self.relate = True
		self.sequence = sequence

		if self.sequence:
			self.sequencedb = bsddb3.db.DB(self.dbenv)
			self.sequencedb.open(self.filename+".sequence.bdb", dbtype=bsddb3.db.DB_BTREE, flags=g.DBOPENFLAGS) #

		kt = self.keytype
		dt = self.datatype

		self.pcdb2 = FieldBTree(filename=self.filename+".pc2", keytype=kt, datatype=kt, dbenv=self.dbenv, cfunc=False, bulkmode=None, txn=txn)
		self.cpdb2 = FieldBTree(filename=self.filename+".cp2", keytype=kt, datatype=kt, dbenv=self.dbenv, cfunc=False, bulkmode=None, txn=txn)




	def __str__(self):
		return "<emen2.db.btrees2.RelateBTree instance: %s>"%self.filename


	def get_max(self, txn=None):
		sequence = self.sequencedb.get("sequence", txn=txn)
		if sequence == None: sequence = 0
		val = int(sequence)
		return val

		# sequence = bsddb3.db.DBSequence(self.sequencedb)
		# sequence.open("sequence", flags=bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD, txn=txn)
		# val = sequence.stat()['current']
		# sequence.close()
		#get_range()[1]


	def get_sequence(self, delta=1, txn=None):
		
		# newtxn = self.dbenv.txn_begin(parent=txn, flags=0) #
		# print "Setting sequence += %s, txn: %s, newtxn: %s, flags:%s"%(delta, txn, newtxn, g.RMWFLAGS)		
		# try:
		val = self.sequencedb.get("sequence", txn=txn, flags=g.RMWFLAGS)
		if val == None:
			val = 0
		val = int(val)
		self.sequencedb.put("sequence", str(val+delta), txn=txn)
		# except:
		# 	newtxn.abort()
		# else:
		# 	newtxn.commit()
			
		return val

		# 	 	sequence = bsddb3.db.DBSequence(self.sequencedb)
		# 	 	sequence.open("sequence", flags=bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD, txn=txn)
		# 
		# if not txn or delta < 1:
		# 	raise ValueError, "delta and txn requried for sequence increment"
		# val = sequence.get(delta=delta, txn=txn)
		# 
		# sequence.close()


	def pget(self, key, txn=None, flags=0):
		d = self.sget(key, txn=txn, flags=flags)

		cursor = self.pcdb2.bdb.cursor(txn=txn)
		d["children"] = self.pcdb2.get(key, cursor=cursor)
		cursor.close()

		cursor = self.cpdb2.bdb.cursor(txn=txn)
		d["parents"] = self.cpdb2.get(key, cursor=cursor)
		cursor.close()

		return d


	def close(self):
		if self.bdb is None:
			return

		if self.sequence:
			# self.sequence.close()
			self.sequencedb.close()

		if self.relate:
			self.pcdb2.close()
			self.cpdb2.close()

		self.bdb.close()
		self.bdb = None


	def sync(self):
		self.bdb.sync()

		if self.sequence:
			self.sequencedb.sync()

		if self.relate:
			self.pcdb2.sync()
			self.cpdb2.sync()


	# Relate methods

	def children(self, key, recurse=1, txn=None):
		return self.__getrel(self.pcdb2, key, recurse=recurse, txn=txn)


	def parents(self, key, recurse=1, txn=None):
		return self.__getrel(self.cpdb2, key, recurse=recurse, txn=txn)


	def __getrel(self, rel, key, recurse=1, txn=None):
		"""get parent/child relationships; see: getchildren"""

		#g.log.msg('LOG_DEBUG','getrel: key %s, method %s, recurse %s'%(key, method, recurse))

		if (recurse < 1):
			return {}, set()

		cursor = rel.bdb.cursor(txn=txn)

		new = rel.get(key, cursor=cursor)

		# ian: todo: use collections.queue
		stack = [new]
		result = {key: new}
		visited = set()

		lookups = []

		for x in xrange(recurse-1):

			if not stack[x]:
				break

			stack.append(set())

			# lcount = len(stack[x]-visited)
			# g.log.msg('LOG_DEBUG', "recurse level %s, %s lookups to make this level"%(x, lcount))
			# t = time.time()

			for key in stack[x] - visited:
				new = rel.get(key, cursor=cursor)
				if new:
					stack[x+1] |= new #.extend(new)
					result[key] = new

			# g.log.msg('LOG_DEBUG', "%s lookups per second"%(int(lcount/(time.time()-t))))

			visited |= stack[x]

		visited |= stack[-1]

		cursor.close()

		# we return a tuple of result and visited b/c we had to calculate visited anyway
		return result, visited


	def __putrel(self, links, mode='addrefs', txn=None):
		pc = collections.defaultdict(set)
		cp = collections.defaultdict(set)
		for link in links:
			link = self.typekey(link[0]), self.typekey(link[1])
			if link[0] == link[1]:
				continue
			pc[link[0]].add(link[1])
			cp[link[1]].add(link[0])

		for k,v in pc.items():
			getattr(self.pcdb2, mode)(k, v, txn=txn)
		for k,v in cp.items():
			getattr(self.cpdb2, mode)(k, v, txn=txn)


	def pclinks(self, links, txn=None):
		"""Create parent-child relationships"""
		self.__putrel(links, mode='addrefs', txn=txn)


	def pcunlinks(self, links, txn=None):
		"""Remove parent-child relationships"""
		self.__putrel(links, mode='removerefs', txn=txn)


	def pclink(self, tag1, tag2, txn=None):
		"""Create parent-child relationship"""
		self.__putrel([[tag1, tag2]], mode='addrefs', txn=txn)


	def pcunlink(self, tag1, tag2, txn=None):
		"""Remove parent-child relationship"""
		self.__putrel([[tag1, tag2]], mode='removerefs', txn=txn)





class FieldBTree(BTree):

	DBSETFLAGS = [bsddb3.db.DB_DUP, bsddb3.db.DB_DUPSORT]


	def __init__(self, *args, **kwargs):
		bulkmode = kwargs.pop('bulkmode','bulk')
		BTree.__init__(self, *args, **kwargs)

		# use acceleration module if available
		if bulk:
			if bulkmode=='bulk':
				self.__get_method = emen2.db.bulk.get_dup_bulk
			else:
				self.__get_method = emen2.db.bulk.get_dup_notbulk



	def __str__(self):
		return "<FieldBTree instance: %s>"%self.filename



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

		return addindexitems



	def __get_method(self, cursor, key, dt, flags=0):
		n = cursor.set(key)
		r = set() #[]
		m = cursor.next_dup
		while n:
			r.add(n[1])
			n = m()
		
		return set(self.loaddata(x) for x in r)


	def get(self, key, default=None, cursor=None, txn=None, flags=0):
		key = self.dumpkey(key)
		dt = self.datatype or "p"

		if cursor:
			r = self.__get_method(cursor, key, dt)
			
		else:
			cursor = self.bdb.cursor(txn=txn)
			r = self.__get_method(cursor, key, dt)
			cursor.close()

		# generator expressions will be less pain when map() goes away
		if bulk and dt == 'p':
			r = set(self.loaddata(x) for x in r)

		return r


	def put(self, *args, **kwargs):
		raise Exception, "put not supported on FieldBTree; use addrefs, removerefs"


	def keys(self, txn=None, flags=0):
		keys = set(map(self.loadkey, self.bdb.keys(txn)))
		return list(keys)


	# ian: todo: fix..
	def items(self, txn=None, flags=0):
		# r = self.bdb.items(txn)
		# r2 = collections.defaultdict(set)
		# for k,v in r:
		# 	r2[self.loadkey(k)].add(int(v))
		# return r2.items()
		
		ret = []
		dt = self.datatype or "p"
		cursor = self.bdb.cursor(txn=txn)
		pair = cursor.first()
		while pair != None:
			data = self.__get_method(cursor, pair[0], dt)
			if bulk and dt == "p":
				data = set(map(self.loaddata, data))
			ret.append((self.loadkey(pair[0]), data))
			pair = cursor.next_nodup()
		cursor.close()
		
		return ret


	#def values(self, txn=None, flags=0):
	#	pass


	# def keys(self, txn=None):
	# 	return map(self.loadkey, self.bdb.keys(txn))
	# 	#return map(lambda x: (g.log('-> key: %r' % x), self.loadkey(x))[1], self.bdb.keys(txn))
	#
	#
	# def values(self, txn=None):
	# 	#return reduce(set.union, map(self.loaddata, self.bdb.values())) #(self.loaddata(x) for x in self.bdb.values())) #txn=txn
	# 	# set() needed if empty
	# 	# return reduce(set.union, (self.loaddata(x) for x in self.bdb.values(txn)), set()) #txn=txn
	# 	return [self.loaddata(x) for x in self.bdb.values(txn)]
	#
	#
	# def items(self, txn=None):
	# 	return map(lambda x:(self.loadkey(x[0]),self.loaddata(x[1])), self.bdb.items(txn)) #txn=txn


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
	
	
__version__ = "$Revision$".split(":")[1][:-1].strip()
