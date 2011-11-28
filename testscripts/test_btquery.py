import collections
import time


class Constraint(object):
	def __init__(self, param, op='contains', term=''):
		self.param = param
		self.op = op
		self.term = term
		self.p = None
		self.defer = False
		self.nkeys = 0
	
	def init(self, p):
		self.p = p
		try:
			# Get the number of keys in the index
			ind = self.p.btree.getindex(self.param, txn=self.p.txn)
			self.nkeys = ind.bdb.stat(txn=self.p.txn)['nkeys']
		except Exception, e:
			# Non-indexed params will be deferred until after indexed ones
			self.defer = True

	def run(self):		
		if '*' in self.param:
			# Turn expanded params into a new constraint
			params = self.p.btree.dbenv.paramdef.expand([self.param], ctx=ctx, txn=txn)
			c = Constraints(
				[Constraint(i, op=self.op, term=self.term) for i in params], 
				mode='OR', 
				ctx=self.p.ctx, 
				txn=self.p.txn,
				btree=self.p.btree)				
			return c.run()

		print "running:", self.param, self.op, self.term		
		if self.param.startswith('$@'):
			f = self._run_macro()	
		elif self.param in ['parents', 'children']:
			f = self._run_rel()
		elif self.defer:
			f = self._run_items()
		else:
			f = self._run_index()	

		if self.op == 'noop':
			# Returning None has no constraint
			return None
		elif self.op == 'none':
			# Return all records that don't have a value
			names = self.p.btree.names(ctx=self.p.ctx, txn=self.p.txn)
			f = names - f
	
		return f

	def _run_rel(self):
		ind = self.p.btree.getindex(self.param, txn=self.p.txn)
		return ind.get(ind.typekey(self.term), txn=self.p.txn)
		
	def _run_index(self):
		f = set()
		ind = self.p.btree.getindex(self.param, txn=self.p.txn)
		term = ind.typekey(self.term)
		cfunc = self._op(self.op)
		for key, items in ind.iteritems(txn=self.p.txn):
			if cfunc(term, key):
				f |= items
				for i in items:
					self.p.cache[i][self.param] = key
		return f
		
	def _run_macro(self):
		f = set()
		cfunc = self._op(self.op)
		vtm = emen2.db.datatypes.VartypeManager(db=self.p.ctx.db)
		regex = emen2.db.database.VIEW_REGEX
		k = regex.match(self.param)
		keytype = vtm.getmacro(k.group('name')).getkeytype()
		vtm.macro_preprocess(k.group('name'), k.group('args'), self.p.items)
		for item in self.p.items:
			value = vtm.macro_process(k.group('name'), k.group('args'), item)
			if cfunc(self.term, value):
				f.add(item.name)
				self.p.cache[item.name][self.param] = value
		return f
				
	def _run_items(self):
		f = set()
		cfunc = self._op(self.op)
		for item in self.p.items:
			value = item.get(self.param)
			if cfunc(self.term, value):
				f.add(item.name)
				self.p.cache[item.name][self.param] = value
		return f
		
	def _op(self, op, ignorecase=1):
		"""(Internal) Get a comparison function
		:keyword ignorecase: Use case-insensitive comparison methods
		:return: Comparison function
		"""
		# y is search argument, x is the record's value
		ops = {
			"==": lambda y,x: x == y,
			"!=": lambda y,x: x != y,
			">": lambda y,x: x > y,
			"<": lambda y,x: x < y,
			">=": lambda y,x: x >= y,
			"<=": lambda y,x: x <= y,
			'any': lambda y,x: x != None,
			'none': lambda y,x: x != None,
			"contains": lambda y,x: unicode(y) in unicode(x),
			'noop': lambda y,x: True,
		}
	
		# Synonyms
		synonyms = {
			"is": "==",
			"not": "!=",
			"gte": ">=",
			"lte": "<=",
			"gt": ">",
			"lt": "<"
		}
	
		if ignorecase:
			ops["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			ops['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()
	
		operator = synonyms.get(op, op)
		return ops[operator]
	



		
class Constraints(object):
	def __init__(self, constraints, mode='AND', ctx=None, txn=None, btree=None):
		self.mode = mode
		self.constraints = constraints
		# Items shared between constraints
		self.result = None
		self.items = []
		self.cache = collections.defaultdict(dict)
		self.vtm = None
		# DB
		self.ctx = ctx
		self.txn = txn
		self.btree = btree
	
	def run(self):
		now = []
		defer = []
		for c in self.constraints:
			c.init(self)
			if c.defer:
				defer.append(c)
			else:
				now.append(c)
		
		# Run indexed constraints
		for c in sorted(now, key=lambda x:x.nkeys):
			f = c.run()
			self._join(f)

		# Run non-indexed or macro constraints
		if defer:
			self.items = self.btree.cgets(self.result, ctx=self.ctx, txn=self.txn)
			
		for c in defer:
			f = c.run()
			self._join(f)
		
		items = []
		for name, item in self.cache.items():
			item['name'] = name
			if name in self.result:
				items.append(item)
		
		print "Items:"
		print items
			
		return self.result
		
	def _join(self, f):
		if f is None:
			pass
		elif self.result == None:
			self.result = f
		elif self.mode == 'AND':
			self.result &= f
		else:
			self.result |= f
			
			

import emen2.db
db = emen2.db.opendb(admin=True)
with db:
	txn = db._txn
	ctx = db._ctx	
	c = Constraints(
		[
			Constraint('name_pi', 'contains', 'wah'), 
			Constraint('rectype', 'is', 'project'), 
			# Constraint('core*', 'is', 'lol')
		], 
		ctx=ctx, 
		txn=txn, 
		btree=db._db.bdbs.record
		)
		
	print c.run()

	
	

# import emen2.db
# db = emen2.db.opendb(admin=True)
# with db:
# 	txn = db._txn
# 	ctx = db._ctx
# 	
# 	c = [
# 		# ['children', 'contains', '136'],
# 		['core*', 'contains', '']
# 		# ['name_pi', 'contains', 'wah'],
# 		# ['$@recname()', 'contains', 'pro'],
# 		# ['ctf_bfactor', '>=', '0'],
# 		# ['creationtime', 'contains', ''],
# 		# ['email', 'contains', 'ian'], 
# 		]
# 	
# 	for i in range(3):	
# 		t = time.time()
# 		r = db._db.bdbs.record.query(c=c, sortkey="name_pi", ctx=ctx, txn=txn)
# 		# r = db._db.bdbs.user._query('email', 'ian', ctx=ctx, txn=txn)
# 		print r
# 		print time.time()-t

##### Search and Query #####
# 
# def query(self,
# 		c=None,
# 		pos=0,
# 		count=0,
# 		sortkey="name",
# 		reverse=False,
# 		recs=False,
# 		ignorecase=True,
# 		ctx=None,
# 		txn=None,
# 		**kwargs):
# 	"""General query."""
# 	
# 	c = c or []
# 	cache = collections.defaultdict(dict)
# 	
# 	# Found items
# 	found = None
# 	allnames = None
# 	if 'none' in [i[1] for i in c] or not c:
# 		allnames = self.names(ctx=ctx, txn=txn)
# 	if not c:
# 		found = allnames
# 		
# 	# Sort indexes by the number of keys
# 	nkeys = {}
# 	for param, operator, term in c:
# 		try:
# 			ind = self.getindex(param, txn=txn)
# 			nkeys[param] = ind.bdb.stat(txn=txn)['nkeys']
# 		except:
# 			pass
# 	nkeys['parents'] = -1
# 	nkeys['children'] = -1
# 
# 	for param, op, term in sorted(c, key=lambda x:nkeys.get(x[0])):
# 		cfunc = self._query_op(op)
# 		f = set()
# 		
# 		if param in ['parents', 'children']:
# 			# Always evaluate relationships first
# 			ind = self.getindex(param, txn=txn)
# 			f = ind.get(ind.typekey(term), txn=txn)
# 
# 		elif param == 'rectype':
# 			pass
# 			continue
# 
# 		elif param.startswith('$@'):
# 			pass
# 			continue
# 
# 		else:
# 			# Expand the param
# 			fromitems = set()
# 			for param in self.dbenv.paramdef.expand([param], ctx=ctx, txn=txn):
# 				ind = self.getindex(param, txn=txn)
# 				if not ind:
# 					fromitems.add(param)
# 					continue
# 					
# 				pd = self.dbenv.paramdef.cget(param, ctx=ctx, txn=txn)
# 				term = ind.typekey(term)
# 				for key, items in ind.iteritems(txn=txn):
# 					if cfunc(term, key):
# 						f |= items
# 						for i in items:
# 							cache[i][param] = key
# 
# 			if fromitems:
# 				items = self.cgets(f, ctx=ctx, txn=txn)
# 				for param in fromitems:
# 					for item in items:
# 						if cfunc(term, key):
# 							pass
# 		
# 		# Constrain the results
# 		if op is 'none':
# 			f = allnames - f			
# 		if found is None:
# 			found = f
# 		found &= f
# 		
# 
# 	print items
# 	return len(found)
# 
# def _query_rel(self, c, found=None, cache=None, ctx=None, txn=None):
# 	pass
# 	
# def _query_index(self, c, found=None, cache=None, ctx=None, txn=None):
# 	pass
# 	
# def _query_items(self, c, found=None, cache=None, ctx=None, txn=None):
# 	pass
# 
# def _query_op(self, operator, ignorecase=1):
# 	"""(Internal) Return the list of query constraint operators.
# 	:keyword ignorecase: Use case-insensitive comparison methods
# 	:return: Dict of query methods
# 	"""
# 	# y is search argument, x is the record's value
# 	ops = {
# 		"==": lambda y,x:x == y,
# 		"!=": lambda y,x:x != y,
# 		">": lambda y,x: x > y,
# 		"<": lambda y,x: x < y,
# 		">=": lambda y,x: x >= y,
# 		"<=": lambda y,x: x <= y,
# 		'any': lambda y,x: x != None,
# 		'none': lambda y,x: x != None,
# 		"contains": lambda y,x:unicode(y) in unicode(x),
# 		'contains_w_empty': lambda y,x:unicode(y or '') in unicode(x),
# 		'noop': lambda y,x: True,
# 		'name': lambda y,x: x
# 	}
# 
# 	# Synonyms
# 	synonyms = {
# 		"is": "==",
# 		"not": "!=",
# 		"gte": ">=",
# 		"lte": "<=",
# 		"gt": ">",
# 		"lt": "<"
# 	}
# 
# 	if ignorecase:
# 		ops["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
# 		ops['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()
# 
# 	operator = synonyms.get(operator, operator)
# 	return ops[operator]
# 

# # ... then direct record comparisons, including macros
# if c_items or c_macro:
# 	# todo: change term to correct type
# 	items = self.cgets(found, ctx=ctx, txn=txn)
# 	vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
# 	for macro in [i[0] for i in c_macro]:
# 		regex = emen2.db.database.VIEW_REGEX
# 		k = regex.match(macro)
# 		keytype = vtm.getmacro(k.group('name')).getkeytype()
# 		vtm.macro_preprocess(k.group('name'), k.group('args'), items)
# 		for item in items:
# 			cache[item.name][macro] = vtm.macro_process(k.group('name'), k.group('args'), item)
# 	for param in [i[0] for i in c_items]:
# 		for item in items:
# 			cache[item.name][param] = item.get(param)
# 			
# 	for param, op, term in c_items+c_macro:
# 		f = set()
# 		cfunc = self._query_op(op)
# 		for item in items:
# 			v = cache.get(item.name).get(param)
# 			if cfunc(term, v):
# 				f.add(item.name)
# 				cache[item.name][param] = v
# 		# Constrain
# 		if op is 'none':
# 			allnames -= f
# 			f = allnames
# 		if found is None: found = f
# 		else: found &= f
# 
# items = []
# for name, item in cache.items():
# 	if name in found:
# 		item['name'] = name
# 		items.append(item)
# 
# # Sort
# items = sorted(items, key=lambda x:x.get(sortkey), reverse=reverse or False)
# 
# 
# # Switch to item mode if < 1000 items
# if found is not None and len(found) < 1000:
# 	c_items.append([param, op, term])
# 	continue
# 
