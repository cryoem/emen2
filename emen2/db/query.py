# $Id$

import collections
import time

import emen2.db.vartypes

class Constraint(object):
	def __init__(self, param, op=None, term=None):
		self.param = param
		self.op = op or 'contains'
		self.term = term or ''
		self.p = None
		self.ind = False
		self.nkeys = 0
	
	def init(self, p):
		"""Bind the parent Constraints group, and check the index."""
		self.p = p
		try:
			# Get the number of keys in the index
			self.ind = self.p.btree.getindex(self.param, txn=self.p.txn)
			self.nkeys = self.ind.bdb.stat(txn=self.p.txn)['nkeys']
		except Exception, e:
			# Non-indexed params will be deferred until after indexed ones
			self.ind = None

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

		print "running:", self.param, self.op, self.term, "(ind:%s)"%self.ind
		if self.param.startswith('$@'):
			f = self._run_macro()	
		elif self.param in ['parents', 'children']:
			f = self._run_rel()
		elif self.ind:
			f = self._run_index()	
		else:
			f = self._run_items()

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
		# items = filter(lambda x:x.name in self.p.result, self.p.items)
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
		self.constraints = []
		for c in constraints:
			c = Constraint(*c)
			self.constraints.append(c)
		
		self.mode = mode
		# Items shared between constraints
		self.result = None
		self.items = []
		self.cache = collections.defaultdict(dict)
		self.vtm = None
		# Database details
		self.ctx = ctx
		self.txn = txn
		self.btree = btree
	
	def run(self):
		c_index = []
		c_items = []
		for c in self.constraints:
			c.init(self)
			if c.ind:
				c_index.append(c)
			else:
				c_items.append(c)
		
		# Run indexed constraints
		for c in sorted(c_index, key=lambda x:x.nkeys):
			if self.result and len(self.result) < 1000:
				c.ind = False
				c_items.append(c)
				continue
			f = c.run()
			self._join(f)

		# Run non-indexed or macro constraints
		if c_items:
			self.items = self.btree.cgets(self.result, ctx=self.ctx, txn=self.txn)
		for c in c_items:
			f = c.run()
			self._join(f)
		
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
	
	def sort(self, sortkey='creationtime', reverse=False, pos=0, count=100):
		print "Sorting by: %s"%sortkey
		params = [i.param for i in self.constraints]
		if sortkey not in params:
			c = Constraint(param=sortkey)
			c.init(self)
			c.run()

		items = []
		for name, item in self.cache.items():
			item['name'] = name
			if name in self.result:
				items.append(item)			
		
		






