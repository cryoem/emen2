# $Id$

import collections
import time

import emen2.db.vartypes
import emen2.util.listops

INDEXMIN = 1000
ITEMSMAX = 100000

# Synonyms
synonyms = {
	"is": "==",
	"not": "!=",
	"gte": ">=",
	"lte": "<=",
	"gt": ">",
	"lt": "<"
}


def getop(op, ignorecase=True):
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
	if ignorecase:
		ops["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
		ops['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

	operator = synonyms.get(op, op)
	return ops[operator]


def keytypeconvert(keytype, term):
	try:
		if keytype == 'd':
			term = int(term)
		elif keytype == 'f':
			term = float(term)
		elif keytype == 's':
			term = unicode(term)
	except:
		pass
	return term



class Constraint(object):
	"""Base Constraint"""
	
	def __init__(self, param, op=None, term=None):
		# The constraint
		self.param = param
		self.op = op or 'contains'
		self.term = term or ''
		# Parent query group
		self.p = None
		self.priority = 10
		# Param details
		self.paramdef = None
		self.ind = None
				
	def init(self, p):
		"""Bind the parent query group."""
		self.p = p

	def run(self):		
		# Run the constraint
		# print "\nrunning:", self.param, self.op, self.term, '(ind:%s)'%self.ind, '(prev found:%s)'%len(self.p.result or [])
		t = time.time()
		f = self._run()
		# print "-> found: %s in %s"%(len(f or []), time.time()-t)

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
	"""Constraint that has an index."""
	
	def init(self, p):
		super(IndexedConstraint, self).init(p)
		self.priority = 1.0
		# If this is a ParamDef index, get all the details and index
		try:
			self.paramdef = self.p.btree.dbenv.paramdef.cget(self.param, filt=False, ctx=self.p.ctx, txn=self.p.txn)			
			self.ind = self.p.btree.getindex(self.param, txn=self.p.txn)
			nkeys = self.ind.bdb.stat(txn=self.p.txn)['ndata'] or 1 # avoid div by zero
			self.priority = 1.0 - (1.0/nkeys)
		except Exception, e:
			# print "Error opening %s index:"%self.param, e
			pass
			

class ParamConstraint(IndexedConstraint):
	"""Constraint based on a ParamDef"""
	
	def _run(self):
		# Use either the items-based search or the index-based search.
		r = self.p.result
		if (r and len(r) < INDEXMIN) or not self.ind:
			return self._run_items()
		return self._run_index()

	def _run_items(self):
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
		# Use the parameter index
		# list seems to be faster than set
		f = []

		# Convert the term to the right type
		term = keytypeconvert(self.ind.keytype, self.term)
		
		# If we're just looking for a single value
		if self.op == '==':
			items = self.ind.get(term, txn=self.p.txn)
			f.extend(items)
			for i in items:
				self.p.cache[i][self.param] = term
			return set(f)

		# Otherwise check constraint against all indexed values
		cfunc = getop(self.op)
		for key, items in self.ind.iteritems(txn=self.p.txn):
			if cfunc(term, key):
				f.extend(items)
				for i in items:
					self.p.cache[i][self.param] = key
		if f is None:
			return f
		return set(f or [])


class RectypeConstraint(ParamConstraint):
	"""Rectype constraints, allows '*' notation in constraint term"""

	def _run(self):
		# Expand the rectype children and run for each term
		# This is essentially a sub-Query, but without creating a new cache/items/etc.
		f = None
		if self.term.endswith('*'):
			terms = self.p.btree.dbenv.recorddef.expand([self.term], ctx=self.p.ctx, txn=self.p.txn)
		else:
			terms = [self.term]
			
		for i in terms:
			self.term = i # ugly; pass as argument in the future
			f2 = super(RectypeConstraint, self)._run()
			if f is None and f2:
				f = list(f2)
			elif f2:
				f.extend(f2)

		# ian: todo: Doesn't work for "not param*"
		return set(f or [])


class RelConstraint(IndexedConstraint):
	"""Relationship constraints, allows '*' notation in constraint term"""
	
	def init(self, p):
		super(RelConstraint, self).init(p)
		self.priority = -1 # run first
	
	def _run(self):
		# Relationships
		recurse = 1
		term = unicode(self.term)
		if term.endswith('*'):
			term = term.replace('*', '')
			recurse = -1			

		term = keytypeconvert(self.p.btree.keytype, term)
		rel = self.p.btree.rel([term], recurse=recurse, ctx=self.p.ctx, txn=self.p.txn)
		return rel.get(term, set())



	
class MacroConstraint(Constraint):
	"""Macro constraints"""
	
	def _run(self):
		# Execute a macro
		f = set()
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
		term = keytypeconvert(keytype, self.term)
		# Run the comparison
		cfunc = getop(self.op)
		for item in self.p.items:
			value = vtm.macro_process(k.group('name'), k.group('args'), item)
			if cfunc(term, value):
				f.add(item.name)
				self.p.cache[item.name][self.param] = value
		return f
		
		


class Query(object):
	def __init__(self, constraints, mode='AND', ctx=None, txn=None, btree=None):
		# Results attributes
		self.time = 0.0
		self.vtm = None			# vartype manager; handles validation, macros
		self.result = None 		# None or set() of query result
		self.mode = mode		# boolean AND / OR

		# Items that were fetched for non-indexed constraints
		self.items = []			
		# Cache to hold values from constraint results
		self.cache = collections.defaultdict(dict)

		# Database details
		self.ctx = ctx
		self.txn = txn
		self.btree = btree

		# Constraint Groups can contain sub-groups: see also init(), run()
		self.ind = True		
		self.param = None	
		self.priority = 1

		# Make constraints
		self.constraints = []
		for c in constraints:
			self.constraints.append(self._makeconstraint(*c))
	
	def init(self, p):
		pass
		
	def run(self):
		# Start the clock
		t = time.time()
		
		# Run the constraints
		for c in sorted(self.constraints, key=lambda x:x.priority):
			f = c.run()
			self._join(f)

		# Filter by permissions
		if not self.constraints:
			self.result = self.btree.names(ctx=self.ctx, txn=self.txn)
		else:
			self.result = self.btree.filter(self.result or set(), ctx=self.ctx, txn=self.txn)
		
		# After all constraints have run, tidy up cache/items
		self._prunecache()
		self._pruneitems()		

		# Update the approx. running time.
		self.time += time.time()-t
		
		return self.result

	def sort(self, sortkey='name', reverse=False, pos=0, count=0, rendered=False):
		# print "Sorting by: %s"%sortkey
		t = time.time()
		# Make sure we have the values for sorting
		params = [i.param for i in self.constraints]
		if sortkey is 'name':
			# Name is inherent
			pass
		elif sortkey not in params:
			# We don't have a constraint that matched the sortkey
			# This does not change the constraint, just gets values.
			c = self._makeconstraint(sortkey, op='noop')
			c.run()

		# If the param is iterable, we need to get the actual values.
		paramdef = self.btree.dbenv.paramdef.cget(sortkey, ctx=self.ctx, txn=self.txn)
		if paramdef and paramdef.iter:
			self._checkitems(sortkey)
			
		# Actually sort..	
		sortvalues = {}
		for i in self.result or []:
			sortvalues[i] = self.cache[i].get(sortkey)
		
		# Todo: Sort by the rendered value or the raw actual value?
		# if rendered:
		# 	rendered = {}
		result = sorted(self.result, key=sortvalues.get, reverse=reverse)
		
		if count > 0:
			result = result[pos:pos+count]

		self.time += time.time()-t

		return result


	##### Results/Cache methods #####
	
	def _join(self, f):
		# Add/remove items from results 
		if f is None:
			pass
		elif self.result is None:
			self.result = f
		elif self.mode == 'AND':
			self.result &= f
		elif self.mode == 'OR':
			self.result |= f
		else:
			raise Exception, "Unknown mode %s"%self.mode

	def _prunecache(self):
		# Prune items from the cache that aren't in result set.
		if self.result is None:
			return
		keys = self.cache.keys()
		for key in keys:
			self.cache[key]['name'] = key
			if key not in self.result:
				del self.cache[key]
			
	def _pruneitems(self):		
		# Prune items that aren't in the result set.
		if self.result is None:
			return
		self.items = [i for i in self.items if i.name in self.result]

	def _cacheitems(self):
		# Get and cache items for direct comparison constraints.
		# In OR constraints, self.items will be the domain of all possible matches
		if self.result is None and not self.items:
			toget = self.btree.names(ctx=self.ctx, txn=self.txn)
		else:
			toget = set() | self.result # copy

		current = set([i.name for i in self.items])
		toget -= current

		if len(toget) > ITEMSMAX:
			raise Exception, "This type of constraint has a limit of 100000 items; tried to get %s. Try narrowing the search by adding additional parameters."%(len(toget))

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
		op = synonyms.get(op, op)
		
		# Automatically construct the best type of constraint
		constraint = None
		if param.startswith('$@'):
			# Macros
			constraint = MacroConstraint(param, op, term)
		elif param.endswith('*'):
			# Turn expanded params into a new constraint group
			params = self.btree.dbenv.paramdef.expand([param], ctx=self.ctx, txn=self.txn)
			constraint = Query(
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







