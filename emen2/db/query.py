# $Id$

import collections
import time

import emen2.db.vartypes
import emen2.util.listops


def getop(op, ignorecase=1):
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
		'contains': lambda y,x: unicode(y) in unicode(x),
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



class Constraint(object):
	"""Base Constraint"""
	
	def __init__(self, param, op=None, term=None):
		# The constraint
		self.param = param
		self.op = op or 'contains'
		self.term = term or ''
		# Parent Constraints Group
		self.p = None
		# Param details
		self.paramdef = None
		self.priority = 100
		self.typekey = unicode
		self.ind = None
				
	def init(self, p):
		"""Bind the parent Constraints group."""
		self.p = p

	def run(self):		
		# Run the constraint
		print "\nrunning:", self.param, self.op, self.term, '(ind:%s)'%self.ind
		t = time.time()
		f = self._run()
		print "-> found: %s in %s"%(len(f or []), time.time()-t)
			
		# Check for negative operators
		if self.op == 'noop':
			# If op is 'noop', return None (no constraint)
			return None
		elif self.op == 'none':
			# If op is 'none', return all records that don't have a value
			names = self.p.btree.names(ctx=self.p.ctx, txn=self.p.txn)
			f = names - (f or set())

		return f

	def _run(self):
		return None


class IndexedConstraint(Constraint):
	def init(self, p):
		super(IndexedConstraint, self).init(p)
		# If this is a ParamDef index, get all the details and index
		try:
			self.paramdef = self.p.btree.dbenv.paramdef.cget(self.param, filt=False, ctx=self.p.ctx, txn=self.p.txn)			
			self.ind = self.p.btree.getindex(self.param, txn=self.p.txn)
			nkeys = self.ind.bdb.stat(txn=self.p.txn)['nkeys'] or 1 # avoid div by zero
			self.priority = 1.0 - (1.0/nkeys)
		except Exception, e:
			# Unindexed item, low priority.
			print "Error opening %s index:"%self.param, e
			self.priority = 2 
			pass
			

class ParamConstraint(IndexedConstraint):
	"""Constraints based on a ParamDef"""
	
	def _run(self):
		r = self.p.result
		if r and len(r) < 1000:
			return self._run_items()
		return self._run_index()

	def _run_items(self):
		print "(using items)"
		self.p._cacheitems()
		f = set()
		cfunc = getop(self.op)
		for item in self.p.items:
			value = item.get(self.param)
			if cfunc(self.term, value):
				f.add(item.name)
				self.p.cache[item.name][self.param] = value
		return f
	
	def _run_index(self):
		print "(using index)"
		# Use the parameter index
		f = set()
		cfunc = getop(self.op)
		# Get the index
		ind = self.p.btree.getindex(self.param, txn=self.p.txn)
		# Convert the term to the right type
		try:
			term = ind.typekey(self.term)
		except:
			term = self.term
		
		# If we're just looking for a single value
		if self.op is 'is':
			items = ind.get(term, txn=self.p.txn)
			f |= items
			for i in items:
				self.p.cache[i][self.param] = term
			return f

		# Otherwise check constraint against all indexed values
		for key, items in ind.iteritems(txn=self.p.txn):
			if cfunc(term, key):
				f |= items
				for i in items:
					self.p.cache[i][self.param] = key
		return f


class RelConstraint(IndexedConstraint):
	"""Relationship constraints, allows '*' notation in constraint term"""
	
	def init(self, p):
		super(RelConstraint, self).init(p)
		self.priority = -1 # run first
	
	def _run(self):
		# Relationships
		# self.bdbs.record.rel([value], recurse=recurse, ctx=ctx, txn=txn).get(value, set())
		ind = self.p.btree.getindex(self.param, txn=self.p.txn)
		try:
			return ind.get(ind.typekey(self.term), txn=self.p.txn)
		except:
			return None


class RectypeConstraint(IndexedConstraint):
	"""Rectype constraints, allows '*' notation in constraint term"""
	
	def _run(self):
		f = set()
		rectypes = self.p.btree.dbenv.recorddef.expand([self.term], ctx=self.p.ctx, txn=self.p.txn)
		for rectype in rectypes:
			f |= self.ind.get(rectype, txn=self.p.txn)
		return f

	
class MacroConstraint(Constraint):
	"""Macro constraints"""
	
	def _run(self):
		# Execute a macro
		f = set()
		cfunc = getop(self.op)
		# Fetch the items we need in the parent group.
		self.p._cacheitems()		
		# Parse the macro and get the Macro class
		regex = emen2.db.database.VIEW_REGEX
		k = regex.match(self.param)
		vtm = emen2.db.datatypes.VartypeManager(db=self.p.ctx.db)
		# Run the macro
		vtm.macro_preprocess(k.group('name'), k.group('args'), self.p.items)
		# Convert the term to the right type
		keytype = vtm.getmacro(k.group('name')).getkeytype()
		if keytype == 'd':
			term = int(self.term)
		elif keytype == 'f':
			term = float(self.term)
		else:
			term = unicode(self.term)
		# Run the comparison
		for item in self.p.items:
			value = vtm.macro_process(k.group('name'), k.group('args'), item)
			if cfunc(term, value):
				f.add(item.name)
				self.p.cache[item.name][self.param] = value
		return f
		
		


class Constraints(object):
	def __init__(self, constraints, mode='AND', ctx=None, txn=None, btree=None):
		# Results attributes
		self.vtm = None
		self.result = None
		self.items = []
		self.cache = collections.defaultdict(dict)
		# Query boolean mode
		self.mode = mode
		# Database details
		self.ctx = ctx
		self.txn = txn
		self.btree = btree
		# Constraint Groups can contain sub-groups
		self.ind = True
		self.param = None
		self.priority = 0
		# Make constraints
		self.constraints = []
		for c in constraints:
			self.constraints.append(self._makeconstraint(*c))
	
	def init(self, p):
		pass
		
	def run(self):
		for c in sorted(self.constraints, key=lambda x:x.priority):
			f = c.run()
			self._join(f)
			self._prune()
		
		return self.result

	def sort(self, sortkey='name', reverse=False, pos=0, count=100):
		# print "Sorting by: %s"%sortkey
		# Make sure we have the values for sorting
		params = [i.param for i in self.constraints]
		if sortkey is 'name':
			pass
		elif sortkey not in params:
			# This does not change the constraint, just gets values.
			c = self._makeconstraint(sortkey, op='noop')
			c.run()

		# If the param is iterable, we need to get the actual values.
		paramdef = self.btree.dbenv.paramdef.cget(sortkey, ctx=self.ctx, txn=self.txn)
		if paramdef and paramdef.iter:
			self._checkitems(sortkey)

		#for k,v in self.cache.items():
		#	print k, v


	##### Results/Cache methods #####
	
	def _join(self, f):
		# Add/remove items from results 
		if f is None:
			pass
		elif self.result == None:
			self.result = f
		elif self.mode == 'AND':
			self.result &= f
		elif self.mode == 'OR':
			self.result |= f
		else:
			raise Exception, "Unknown mode %s"%self.mode

	def _prune(self):		
		# Prune items that won't be used again.
		# Make sure that we have a result, and have fetched items
		if self.mode == 'AND' and self.result and self.items:
			print "pruning %s items down to %s"%(len(self.items), len(self.result))
			self.items = [i for i in self.items if i.name in self.result]
			print "    -> %s"%(len(self.items))		

	def _cacheitems(self):
		# Cache items to run an direct comparison constraint.
		# In OR constraints, self.items will be the domain of all possible matches
		toget = self.result
		if toget is None and not self.items:
			toget = self.btree.names(ctx=self.ctx, txn=self.txn)

		current = set([i.name for i in self.items])
		toget -= current

		if len(toget) > 10000:
			raise Exception, "This type of constraint has a limit of 10,000 items; tried %s"%(len(toget))

		# for chunk in emen2.util.listops.chunk(self.result):
		if toget:
			items = self.btree.cgets(toget, ctx=self.ctx, txn=self.txn)
			self.items.extend(items)
		
	def _checkitems(self, param):
		# params where the indexed value is not 1:1 with the item's value
		# (e.g. indexes for iterable params)
		if param == 'name':
			return
		checkitems = set([k for k,v in self.cache.items() if (param in v)])
		items = set([i.name for i in self.items])
		items = self.btree.cgets(checkitems - items, ctx=self.ctx, txn=self.txn)
		self.items.extend(items)

	def _makeconstraint(self, param, op='noop', term=''):
		# Automatically construct the best type of constraint
		constraint = None
		if param.startswith('$@'):
			# Macros
			constraint = MacroConstraint(param, op, term)
		elif param.endswith('*'):
			# Turn expanded params into a new constraint group
			params = self.btree.dbenv.paramdef.expand([param], ctx=self.ctx, txn=self.txn)
			constraint = Constraints(
				[[i, op, term] for i in params],
				mode='OR', 
				ctx=self.ctx, 
				txn=self.txn,
				btree=self.btree)
			# Share the same cache
			constraint.cache = self.cache
		elif param in ['parents', 'children']:
			constraint = RelConstraint(param, op, term)
		elif param == 'rectype':
			constraint = RectypeConstraint(param, op, term)
		else:
			constraint = ParamConstraint(param, op, term)
		
		constraint.init(self)
		return constraint







