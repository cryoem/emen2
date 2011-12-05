import time
import emen2.db
db = emen2.db.opendb(admin=True)
with db:
	txn = db._txn
	ctx = db._ctx
	c = [
		# ['vartype', 'is', 'string'],
		# ['vartype', 'is', 'text'],
		# ['phone_voice*', 'contains', '2011'],
		# ['name_pi', 'contains', 'wah'],
		# ['children', 'contains', '136'],
		# ['rectype', 'not', 'project*'],
		# ['rectype', 'contains', 'ccd'],
		# ['rectype', 'is', 'image_capture*']
		# ['rectype', 'is', 'ccd'],
		# ['$@recname()', 'noop'],
		# ['ctf_bfactor', 'any', ''],
		# ['ctf_defocus_measured', 'any', ''],
		# ['creationtime', 'any', '2011'],
		['name_pi', 'contains', 'r']
	]
	# x = {'key':'creationtime'}
	# y = {'key':'ctf_bfactor'}
	# z = {'key':'rectype'}
	# z = {'key':'$@recname()'}
	# z = {'key':'$@parentvalue(tem_name,-1)'}

	t = time.time()
	q = db.plot(c=c)
	print q
	print "=> total: %s results in %s"%(q['stats']['length'], time.time()-t)


# These are the old query methods
class Blah(object):
	"""General query.
	
	Constraints are provided in the following format:
		[param, operator, value]
	
	Operation and value are optional. An arbitrary number of constraints may be given.
	
	Operators:
		is			or		==
		not			or		!=
		gt			or		>
		lt			or		<
		gte			or		>=
		lte			or		<=
		any
		none
		contains
		contains_w_empty
		noop
		name
					
	Examples constraints:
		[name, '==', 136]
		['creator', '==', 'ian']
		[['modifytime', '>=', '2011'], ['name_pi', 'contains', 'steve']]
		
	For record names, parameter names, and protocol names, a '*' can be used to also match children, e.g:
		[['children', 'name', '136*'], ['rectype', '==', 'image_capture*']]
	Will match all children of record 136, recursively, for any child protocol of image_capture.
	
	The result will be a dictionary containing all the original query arguments, plus:
		names:	Names of records found
		recs:	"Stub records," dictionaries that contain the matching value for each constraint
		stats:	Query statistics, e.g. the number of records for each RecordDef
			length		Number of records found
			rectypes	Results by Protocol
			time		Execution time
	
	Examples:
	
	>>> db.query()
	{'names':[1,2], stats: {...}, time: 0.001, ...}
	
	>>> db.query(c=[['creator', '==', 'ian']], )
	{'names':[1,2], 'recs':{1:{'creator':'ian'}, 2:{'creator':'ian'}}, stats: {...}, time: 0.001, ...}
	
	:keyparam c: Constraints
	:keyparam pos: Return results starting from (sorted record name) position
	:keyparam count: Return a limited number of results
	:keyparam sortkey: Sort returned records by this param. Default is creationtime.
	:keyparam reverse: Reverse results
	:keyparam recs: Return record stubs
	:keyparam table: Return a table
	:keyparam stats: Return statistics
	:keyparam ignorecase: Ignore case when comparing strings
	:keyparam x: X-axis options
	:keyparam y: X-axis options
	:keyparam z: X-axis options
	:return: A dictionary containing the original query arguments, and the result in the 'names' key
	:exception KeyError: Broken constraint
	:exception ValidationError: Broken constraint
	:exception SecurityError: Unable to access specified RecordDefs or other constraint parameters.
	"""
	
	def query(self):
		times = {} 
		t0 = time.time()
		t = time.time()
		
		# return record stubs
		returnrecs = bool(recs) 
		recs = collections.defaultdict(dict)
		
		# return statistics
		returnstats = bool(stats) 
		rectypes = collections.defaultdict(int)
	
		# query result
		names = None 
		
		# Pre-process the query constraints..
		c = c or []
		_c = [] # filtered constraints
		default = [None, 'any', None]
		qparams = set()
		for i in c:
			# constraints with just a param name -> [param, 'any', None]
			if not hasattr(i, "__iter__"):
				i = [i]
			i = i[:len(i)]+default[len(i):3]
			qparams.add(i[0])
			_c.append(i)
	
		# todo: tidy this up.
		x = x or {}
		y = y or {}
		z = z or {}
		for axis in [x.get('key'), y.get('key'), z.get('key')]:
			if axis and axis not in qparams and axis != 'name':
				_c.append([axis, 'any', None])
	
		# Complex constraints that we'll defer, and basic constraints to run immediately
		# A basic constraint is a normal param, with a direct comparison
		# A complex constraint is a macro, an empty value, or a "noop" (no constraint)
		_cm, _cc = listops.filter_partition(lambda x:x[0].startswith('$@') or x[1]=='none' or x[1]=='noop', _c)
	
		##### Step 1: Run basic constraints (no macros or complex constraints)
		t = clock(times, 0, t)
		for searchparam, comp, value in _cc:
			# Matching names for each step
			constraintmatches = self._query(searchparam, comp, value, recs=recs, ctx=ctx, txn=txn)
			if names == None: # For the first constraint..
				names = constraintmatches
			elif constraintmatches != None:
				names &= constraintmatches
	
		##### Step 2: Filter permissions.
		t = clock(times, 1, t)
		# If no constraint, use all records..
		if names == None:
			names = self.bdbs.record.names(ctx=ctx, txn=txn)
		# ... or with constraints, filter results
		if c:
			names = self.bdbs.record.names(names or set(), ctx=ctx, txn=txn)
	
		##### Step 3: Run complex constraints
		t = clock(times, 2, t)
		for searchparam, comp, value in _cm:
			constraintmatches = self._query(searchparam, comp, value, names=names, recs=recs, ctx=ctx, txn=txn)
			if constraintmatches != None:
				names &= constraintmatches
	
		##### Step 4: Generate stats on rectypes
		# Do this before other sorting..
		t = clock(times, 3, t)
		# Did we already get the rectypes?
		rds = set([rec.get('rectype') for rec in recs.values()]) - set([None])
		if len(rds) == 1:
			# Yes, a single type
			rectypes[rds.pop()] = len(names)
		elif len(rds) > 1:
			# Yes, group them directly
			for name, rec in recs.iteritems():
				rectypes[rec.get('rectype')] += 1
		else:
			# No, we need to group the result..
			if returnstats: # don't do this unless we need the records grouped.
				r = self.bdbs.record.groupbyrectype(names, ctx=ctx, txn=txn)
				for k,v in r.items():
					rectypes[k] = len(v)
	
		##### Step 5: Sort and slice to the right range
		# This processes the values for sorting:
		#	running any macros, rendering any user names, checking indexes, etc.
		t = clock(times, 4, t)
		# Sort by the rendered value.. todo: use table= keyword
		keytype, sortvalues = self._query_sort(sortkey, names, recs=recs, c=c, ctx=ctx, txn=txn)
	
		# Create a sort comparison function
		key = sortvalues.get
		if sortkey in ['creationtime', 'recid', 'name']:
			# Use the record name as a proxy for creationtime
			key = None
			# Newest records first by default
			if reverse == None:
				reverse = True
		elif keytype == 's':
			# Sort by lower case for string-type params
			key = lambda name:(sortvalues.get(name) or '').lower()
	
		# Save empty values to place them at the end 
		# (empty values will generally sort first)
		nonenames = set(filter(lambda x:not (sortvalues.get(x) or sortvalues.get(x)==0), names))
		names -= nonenames
	
		# Use the sort function
		# (not using sorted(reverse=reverse) so we can add nonenames at the end)
		names = sorted(names, key=key)
		names.extend(sorted(nonenames))
		if reverse:
			names.reverse()
	
		# Before truncating, turn the recs stub defaultdict into a list
		for name in names:
			recs[name]['name'] = name
	
		recs = [recs[i] for i in names]
		
		# Total number of items found (for statistics)
		length = len(names)
		# Truncate results.
		if count > 0:
			names = names[pos:pos+count]
	
		##### Step 6: Render in table format
		# This is purely a convenience to save a callback
		t = clock(times, 5, t)
	
		def add_to_viewdef(viewdef, param):
			if not param.startswith('$'):
				param = '$$%s'%i
			if param in ['$$children','$$rectype', '$$parents']:
				pass
			elif param not in viewdef:
				viewdef.append(i)
	
		if table:
			defaultviewdef = "$@recname() $@thumbnail() $$rectype $$name"
			addparamdefs = ["creator","creationtime"]
	
			# Get the viewdef
			if len(rectypes) == 1:
				rd = self.bdbs.recorddef.cget(rectypes.keys()[0], ctx=ctx, txn=txn)
				viewdef = rd.views.get('tabularview', defaultviewdef)
			else:
				try:
					rd = self.bdbs.recorddef.cget("root", filt=False, ctx=ctx, txn=txn)
				except (KeyError, SecurityError):
					viewdef = defaultviewdef
				else:
					viewdef = rd.views.get('tabularview', defaultviewdef)
	
			viewdef = [i.strip() for i in viewdef.split()]
	
			for i in addparamdefs:
				if not i.startswith('$'):
					i = '$$%s'%i
				if i in viewdef:
					viewdef.remove(i)
	
			for i in [i[0] for i in c] + addparamdefs:
				if not i.startswith('$'):
					i = '$$%s'%i
				add_to_viewdef(viewdef, i)
	
			viewdef = " ".join(viewdef)
			table = self.renderview(names, viewdef=viewdef, table=True, edit='auto', ctx=ctx, txn=txn)
	
		##### Step 7: Prepare result
		t = clock(times, 6, t)
		stats = {}
		stats['time'] = time.time()-t0
		stats['length'] = length
		if returnstats:
			stats['rectypes'] = rectypes
	
		ret = {
			"c": c,
			"ignorecase": ignorecase,
			"names": names,
			"pos": pos,
			"count": count,
			"sortkey": sortkey,
			"reverse": reverse,
			"stats": stats
		}
	
		if x:
			ret['x'] = x
		if y:
			ret['y'] = y
		if z:
			ret['z'] = z
		if returnrecs:
			ret['recs'] = recs
		if table:
			ret['table'] = table
	
		return ret
	
	
	def _query(self, searchparam, comp, value, names=None, recs=None, ctx=None, txn=None):
		"""(Internal) index-based search. See DB.query()
	
		:param searchparam: Param
		:param comp: Comparison method
		:param value: Comparison value
		:keyword names: Record names (used in some query operations)
		:keyword recs: Record cache dict, by name
		:return: Record names returned by query operation, or None
		"""
	
		# Store found values in the rec stubs dictionary
		if recs == None:
			recs = {}
	
		# Get the comparison function
		cfunc = self._query_cmps(comp)
	
		# These operators are handled specially
		if value == None and comp not in ["any", "none", "contains_w_empty"]:
			return None
	
		# Sadly, will need to run macro on everything.. :(
		# Run these as the last constraints.
		if searchparam.startswith('$@'):
			# todo: Run macro will get all the records; should I update recs...?
			keytype, ret = self._run_macro(searchparam, names or set(), ctx=ctx, txn=txn)
			# *minimal* validation of input.. # todo: catch exceptions
			if keytype == 'd':
				value = int(value)
			elif keytype == 'f':
				value = float(value)
			else:
				value = unicode(value)
			# Filter by comp/value
			r = set()
			for k, v in ret.items():
				if cfunc(value, v): # cfunc(value, v):
					recs[k][searchparam] = v # Update the record cache
					r.add(k)
			return r
	
		# Additional setup..
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		matchkeys = collections.defaultdict(set)
		indparams = set()
		searchnames = set()
	
		if searchparam == 'rectype' and value:
			# Get child protocols, skip the index-index search
			matchkeys['rectype'] = self.bdbs.recorddef.expand([value], ctx=ctx, txn=txn)
	
		elif searchparam == 'children':
			# Get children, skip the other steps
			# ian: todo: integrate this with the other * processing methods
			recurse = 0
			if unicode(value).endswith('*'):
				value = int(unicode(value).replace('*', ''))
				recurse = -1
			recs[value]['children'] = self.bdbs.record.rel([value], recurse=recurse, ctx=ctx, txn=txn).get(value, set())
			searchnames = recs[value]['children']
	
		elif searchparam == 'name':
			# This is useful in a few places
			searchnames.add(int(value))
	
		else:
			# Get the list of indexes to search
			param_stripped = searchparam.replace('*','').replace('$$','')
			if searchparam.endswith('*'):
				indparams |= self.bdbs.paramdef.rel([param_stripped], recurse=-1, ctx=ctx, txn=txn)[param_stripped]
			indparams.add(param_stripped)
	
		# First, search the index index
		indk = self.bdbs.record.getindex('indexkeys', txn=txn)
	
		for indparam in indparams:
			pd = self.bdbs.paramdef.cget(indparam, ctx=ctx, txn=txn)
			ik = indk.get(indparam, txn=txn)
			if not pd:
				continue
	
			# Don't need to validate these
			if comp in ['any', 'none', 'noop']:
				matchkeys[indparam] = ik
				continue
	
			# Validate for comparisons (vartype, units..)
			# ian: todo: When validating for a user, needs
			# to return value if not validated?
			try:
				cargs = vtm.validate(pd, value)
			except ValueError:
				if pd.vartype == 'user':
					cargs = value
				else:
					continue
			except:
				continue
	
			# Special case for nested iterables (e.g. permissions) --
			# 		they validate as list of lists
			if pd.name == 'permissions':
				cargs = listops.combine(*cargs)
	
			r = set()
			for v in listops.check_iterable(cargs):
				r |= set(filter(functools.partial(cfunc, v), ik))
	
			if r:
				matchkeys[indparam] = r
	
		# Now search individual param indexes
		for pp, keys in matchkeys.items():
			ind = self.bdbs.record.getindex(pp, txn=txn)
			for key in keys:
				v = ind.get(key, txn=txn)
				searchnames |= v
				for v2 in v:
					recs[v2][pp] = key
	
		# If the comparison is "value is empty", then we
		# 	return the items we couldn't find in the index
		# 'No constraint' doesn't affect search results -- just store the values.
		if comp == 'noop':
			return None
		elif comp == 'none':
			return (names or set()) - searchnames
	
		return searchnames
	
	
	def _query_sort(self, sortkey, names, recs=None, rendered=False, c=None, ctx=None, txn=None):
		"""(Internal) Sort Records by sortkey
	
		:param sortkey:
		:param names:
		:keyword recs: Record cache, keyed by name
		:keyword rendered: Compare using 'rendered' value
		:param c: Query constraints; used for checking items in cache
		:return: Sortkey keytype ('s'/'d'/'f'/None), and {name:value} of values that can be sorted
		"""
		# No work necessary if sortkey is creationtime
		if sortkey in ['creationtime', 'name', 'recid']:
			return 's', {}
	
		# Setup
		vtm = emen2.db.datatypes.VartypeManager(db=ctx.db)
		inverted = collections.defaultdict(set)
		c = c or []
	
		# Check the paramdef
		pd = self.bdbs.paramdef.cget(sortkey, ctx=ctx, txn=txn)
		sortvalues = {}
		vartype = None
		keytype = None
		iterable = False
		ind = False
		if pd:
			vartype = pd.vartype
			vt = vtm.getvartype(vartype)
			keytype = vt.keytype
			iterable = vt.iterable
			ind = self.bdbs.record.getindex(pd.name, txn=txn)
	
		if sortkey.startswith('$@'):
			# Sort using a macro, and get the right sort function
			keytype, sortvalues = self._run_macro(sortkey, names, ctx=ctx, txn=txn)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v
				# Unghhgh... ian: todo: make a macro_render_sort
				if hasattr(v, '__iter__'):
					v = ", ".join(map(unicode, v))
					sortvalues[k] = v
	
		elif not ind or len(names) < 1000 or iterable:
			# Iterable params are indexed, but the order is not preserved,
			# 	so we must check directly.
			# No index can be very slow! Chunk the record gets to help.
			for chunk in listops.chunk(names):
				for rec in self.bdbs.record.cgets(chunk, ctx=ctx, txn=txn):
					sortvalues[rec.name] = rec.get(sortkey)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v
	
		elif ind:
			# We don't have the value, but there is an index..
			# modifytime is kindof a pathological index.. need to find a better way
			for k,v in ind.iterfind(names, txn=txn):
				inverted[k] = v
			sortvalues = listops.invert(inverted)
			for k,v in sortvalues.items():
				recs[k][sortkey] = v
	
		else:
			raise ValueError, "Don't know how to sort by %s"%sortkey
	
	
		# Use a "rendered" representation of the value,
		#	e.g. user names to sort by user's current last name
		# These will always sort using the rendered value
		if vartype in ["user", "binary"]:
			rendered = True
	
		if rendered:
			# Invert again.. then render. This will save time on users.
			if not inverted:
				for k,v in sortvalues.items():
					try:
						inverted[v].add(k)
					except TypeError:
						# Handle iterable vartypes, e.g. userlist
						inverted[tuple(v)].add(k)
	
			sortvalues = {}
			for k,v in inverted.items():
				r = vtm.param_render_sort(pd, k)
				for v2 in v:
					sortvalues[v2] = r
	
		return keytype, sortvalues
	
	
	def _query_cmps(self, comp, ignorecase=1):
		"""(Internal) Return the list of query constraint operators.
	
		:keyword ignorecase: Use case-insensitive comparison methods
		:return: Dict of query methods
		"""
		# y is search argument, x is the record's value
		cmps = {
			"==": lambda y,x:x == y,
			"!=": lambda y,x:x != y,
			">": lambda y,x: x > y,
			"<": lambda y,x: x < y,
			">=": lambda y,x: x >= y,
			"<=": lambda y,x: x <= y,
			'any': lambda y,x: x != None,
			'none': lambda y,x: x != None,
			"contains": lambda y,x:unicode(y) in unicode(x),
			'contains_w_empty': lambda y,x:unicode(y or '') in unicode(x),
			'noop': lambda y,x: True,
			'name': lambda y,x: x,
			#'rectype': lambda y,x: x,
			# "!contains": lambda y,x:unicode(y) not in unicode(x),
			# "range": lambda x,y,z: y < x < z
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
			cmps["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
			cmps['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()
	
		comp = synonyms.get(comp, comp)
		return cmps[comp]
	