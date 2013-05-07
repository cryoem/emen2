# $Id$

import collections
import time

import emen2.db.vartypes
import emen2.util.listops

# Tuning options.
# below this number, use the actual items instead of indexes.
INDEXMIN = 1000 
# max number of items that can be searched directly
ITEMSMAX = 1000000 

# Max query time
MAXTIME = 180.0

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
        "==":   lambda y,x: x == y,
        "!=":   lambda y,x: x != y,
        ">":    lambda y,x: x > y,
        "<":    lambda y,x: x < y,
        ">=":   lambda y,x: x >= y,
        "<=":   lambda y,x: x <= y,
        'any':  lambda y,x: x != None,
        'none': lambda y,x: x != None,
        'noop': lambda y,x: True,
        'contains': lambda y,x: unicode(y) in unicode(x),
    }
    if ignorecase:
        ops["contains"] = lambda y,x:unicode(y).lower() in unicode(x).lower()
        ops['contains_w_empty'] = lambda y,x:unicode(y or '').lower() in unicode(x).lower()

    operator = synonyms.get(op, op)
    return ops[operator]


def keyformatconvert(keyformat, term):
    try:
        if keyformat == 'int':
            term = int(term)
        elif keyformat == 'float':
            term = float(term)
        elif keyformat == 'str':
            term = unicode(term)
    except:
        pass
    return term


class QueryTimeOut(Exception):
    pass

class QuerySyntaxError(Exception):
    pass

class QueryMaxItems(Exception):
    pass


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
        self.index = None

                
    def init(self, p):
        """Bind the parent query group."""
        self.p = p

    def run(self):        
        # Run the constraint
        # print "\nrunning:", self.param, self.op, self.term, '(ind:%s)'%self.index, '(prev found:%s)'%len(self.p.result or [])
        # t = time.time()
        f = self._run()
        # print "-> found: %s in %s"%(len(f or []), time.time()-t)

        # Check for negative operators
        if self.op == 'noop':
            # If op is 'noop', return None (no constraint)
            return None
        elif self.op == 'none':
            # If op is 'none', return all records that don't have a value
            names = self.p.btree.filter(None, ctx=self.p.ctx, txn=self.p.txn)
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
            self.paramdef = self.p.btree.dbenv['paramdef'].get(self.param, filt=False, ctx=self.p.ctx, txn=self.p.txn)            
            self.index = self.p.btree.getindex(self.param, txn=self.p.txn)
            # optimize query
            nkeys = self.index.bdb.stat(txn=self.p.txn)['ndata'] or 1 # avoid div by zero
            self.priority = 1.0 - (1.0/nkeys)
        except Exception, e:
            # print "Error opening %s index:"%self.param, e
            pass
            

class ParamConstraint(IndexedConstraint):
    """Constraint based on a ParamDef"""
    
    def _run(self):
        # Use either the items-based search or the index-based search.
        r = self.p.result
        m = self.p.mode
        # (make sure mode is AND if we're going to a more restrictive mode)
        if (m == 'AND' and r and len(r) < INDEXMIN) or not self.index:
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
        term = keyformatconvert(self.index.keyformat, self.term)
        
        # If we're just looking for a single value
        if self.op == '==':
            items = self.index.get(term, txn=self.p.txn)
            f.extend(items)
            for i in items:
                self.p.cache[i][self.param] = term
            return set(f)

        # Otherwise check constraint against all indexed values

        # If the op is gt or gte, only check those keys..
        # It is not necessary to pass more complicated instructions
        # to iteritems because the returned keys will still be checked
        # with the comparison function.
        minkey = None
        maxkey = None
        if self.op in ['>', '>=']:
            minkey = term
        elif self.op in ['<', '<=']:
            maxkey = term

        cfunc = getop(self.op)
        for key, items in self.index.iteritems(minkey=minkey, maxkey=maxkey, txn=self.p.txn):
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
        # if self.term.endswith('*'):
        # terms = self.p.btree.dbenv['recorddef'].expand([self.term], ctx=self.p.ctx, txn=self.p.txn)
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

        term = keyformatconvert(self.p.btree.keyformat, term)
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
        # Get the macro
        macro = emen2.db.macros.Macro.get_macro(k.group('name'))
        # Preprocess
        macro.preprocess(k.group('args'), self.p.items)
        # Convert the term to the right type
        keyformat = macro.keyformat
        term = keyformatconvert(keyformat, self.term)
        # Run the comparison
        cfunc = getop(self.op)
        for item in self.p.items:
            # Run the macro
            value = macro.process(k.group('args'), item)
            if cfunc(term, value):
                f.add(item.name)
                self.p.cache[item.name][self.param] = value
        return f
        
        


class Query(object):
    def __init__(self, constraints, mode='AND', subset=None, ctx=None, txn=None, btree=None):
        self.time = 0.0
        self.maxtime = MAXTIME
        self.starttime = time.time()
        
        # Subset
        self.subset = subset
        
        # None or set() of query result
        self.result = None 
              
        # boolean AND / OR
        self.mode = mode        

        # Items that were fetched for non-indexed constraints
        self.items = []            
        # Cache to hold values from constraint results
        self.cache = collections.defaultdict(dict)

        # Database details
        self.ctx = ctx
        self.txn = txn
        self.btree = btree

        # Constraint Groups can contain sub-groups: see also init(), run()
        self.index = True        
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

        if self.subset is not None:
            # print "Restricting to subset:", self.subset
            self.result = self.btree.filter(set(self.subset), ctx=self.ctx, txn=self.txn)
        
        # Run the constraints
        for c in sorted(self.constraints, key=lambda x:x.priority):
            f = c.run()            
            self._join(f)
            self._checktime()

        # Filter by permissions
        if self.subset is None and not self.constraints:
            self.result = self.btree.filter(None, ctx=self.ctx, txn=self.txn)
        else:
            self.result = self.btree.filter(self.result or set(), ctx=self.ctx, txn=self.txn)

        self._checktime()

        # After all constraints have run, tidy up cache/items
        self._prunecache()
        self._pruneitems()        

        # Update the approx. running time.
        self.time += time.time() - t
        self._checktime()
        
        return self.result

    def sort(self, sortkey='name', reverse=False, pos=0, count=0, rendered=False):
        reverse = bool(reverse)
        if sortkey == 'name':
            # Shortcut.
            # Records are created as increasing integers. However,
            # they are now stored as strings -- so cast to int,
            # then sort.
            # if self.btree.keytype == 'record':
            #     result = sorted(self.result, reverse=reverse, key=lambda x:int(x))
            # else:
            result = sorted(self.result, reverse=reverse)                
                
            if count > 0:
                result = result[pos:pos+count]
            return result

        # print "Sorting by: %s"%sortkey
        t = time.time()

        # Make sure we have the values for sorting
        params = [i.param for i in self.constraints]
        if sortkey not in params:
            # We don't have a constraint that matched the sortkey
            # This does not change the constraint, just gets values.
            c = self._makeconstraint(sortkey, op='noop')
            c.run()
            self._checktime()
            
        # If the param is iterable, we need to get the actual values.
        pd = self.btree.dbenv['paramdef'].get(sortkey, ctx=self.ctx, txn=self.txn)
        if pd and pd.iter:
            self._checkitems(sortkey)

        self._checktime()

        # Make a copy of the results
        result = set() | (self.result or set())

        # Sort function
        sortvalues = {}
        sortfunc = sortvalues.get
        for i in result:
            sortvalues[i] = self.cache[i].get(sortkey)

        # Remove Nones
        nones = set([i for i in result if sortvalues[i] is None])
        result -= nones

        # Get the data type of the paramdef..
        if rendered and pd:
            # Users need to be rendered... ugly hack.
            if pd.vartype == 'user':
                for i in result:
                    vartype = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd, db=self.ctx.db, cache=self.ctx.cache, options={'lnf':1})
                    sortvalues[i] = vartype.render(sortvalues[i])
                    self._checktime()

            # Case-insensitive sort
            vartype = emen2.db.vartypes.Vartype.get_vartype(pd.vartype)  # don't need db/cache; just checking keytype
            if vartype.keyformat == 'str':
                sortfunc = lambda x:sortvalues[x].lower()
        

        # Todo: Sort by the rendered value or the raw actual value?
        result = sorted(result, key=sortfunc, reverse=reverse)        
        
        # Add Nones back in
        nones = sorted(nones, reverse=reverse)
        if reverse:
            nones.extend(result)
            result = nones
        else:
            result.extend(nones)

        if count > 0:
            result = result[pos:pos+count]

        self.time += time.time() - t
        self._checktime()

        return result


    def _checktime(self):
        t = time.time() - self.starttime
        if t > self.maxtime:
            raise QueryTimeOut, "Max allowed query time exceeded: %5.2f seconds"%t
            

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
            raise QuerySyntaxError, "Unknown boolean mode %s"%self.mode

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
            toget = self.btree.filter(None, ctx=self.ctx, txn=self.txn)
        else:
            toget = set() | self.result # copy

        current = set([i.name for i in self.items])
        toget -= current

        if len(toget) > ITEMSMAX:
            raise QueryMaxItems, "This type of constraint has a limit of 100000 items; tried to get %s. Try narrowing the search by adding additional parameters."%(len(toget))

        if toget:
            items = self.btree.gets(toget, ctx=self.ctx, txn=self.txn)
            self.items.extend(items)
        
    def _checkitems(self, param):
        # params where the indexed value is not 1:1 with the item's value
        # (e.g. indexes for iterable params)
        if param == 'name':
            return
        checkitems = set([k for k,v in self.cache.items() if (param in v)])
        items = set([i.name for i in self.items])
        items = self.btree.gets(checkitems - items, ctx=self.ctx, txn=self.txn)
        self.items.extend(items)

    def _keywords(self, op, term):
        # print "Using keywords..", op, term
        vartypes = ['string', 'choice', 'rectype', 'text']
        c = []
        pds = set()
        for n,pd in self.btree.dbenv['paramdef'].items(ctx=self.ctx, txn=self.txn):
            if pd.indexed and pd.vartype in vartypes:
                pds.add(pd.name)

        pds -= set(['recname', 'id_ccd_frame']) # these are too slow and cause problems :(
        for pd in pds:
            c.append([pd, op, term])
            
        return Query(c, mode='OR', ctx=self.ctx, txn=self.txn, btree=self.btree)

            
    def _makeconstraint(self, param, op='noop', term=''):
        op = synonyms.get(op, op)
        
        # Automatically construct the best type of constraint
        constraint = None
        if param.startswith('$@'):
            # Macros
            constraint = MacroConstraint(param, op, term)
        elif param == '*':
            constraint = self._keywords(op, term)
            constraint.cache = self.cache            
        elif param in ['parents', 'children']:
            constraint = RelConstraint(param, op, term)
        elif param == 'rectype':
            constraint = RectypeConstraint(param, op, term)
        else:
            constraint = ParamConstraint(param, op, term)

        # elif param.endswith('*'):
        #     # Turn expanded params into a new constraint group
        #     params = self.btree.dbenv['paramdef'].expand([param], ctx=self.ctx, txn=self.txn)
        #     constraint = Query(
        #         [[i, op, term] for i in params],
        #         mode='OR', 
        #         ctx=self.ctx, 
        #         txn=self.txn,
        #         btree=self.btree)
        #     # Share the same cache
        #     constraint.cache = self.cache

        
        constraint.init(self)
        return constraint







