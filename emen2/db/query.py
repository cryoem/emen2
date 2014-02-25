"""Query system."""

import collections
import time
import re
import emen2.db.vartypes
import emen2.utils

# Tuning options.
# below this number, use the actual items instead of indexes.
INDEXMIN = 1000 
# max number of items that can be searched directly
ITEMSMAX = 1000000 

# Max query time
MAXTIME = 180.0

# Synonyms
SYNONYMS = {
    "is": "==",
    "not": "!=",
    "gte": ">=",
    "lte": "<=",
    "gt": ">",
    "lt": "<"
}

def getop(op):
    """(Internal) Get a comparison function
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
        'noop': lambda y,x: True,
        'starts': lambda y,x: unicode(y).lower() in unicode(x).lower(),
    }
    return ops[SYNONYMS.get(op, op)]

class QueryTimeOut(Exception):
    pass

class QuerySyntaxError(Exception):
    pass

class QueryMaxItems(Exception):
    pass

class Constraint(object):
    """Base Constraint."""
    def __init__(self, param, op=None, term=None):
        # The constraint
        self.param = param
        self.op = op or '=='
        self.term = term
        # Parent query group
        self.p = None
        self.priority = 10
        self.init()

    def init(self):
        pass

    def setparent(self, p):
        self.p = p
    
    def run(self):        
        return None
        
class NoopConstraint(Constraint):
    def run(self):
        return None

class RelConstraint(Constraint):
    """Relationship constraints."""
    def init(self):
        self.priority = 0 # run first
    
    def run(self):
        # Relationships
        recurse = 1
        term = unicode(self.term)
        if term.endswith('*'):
            term = term.replace('*', '')
            recurse = -1 
        rel = self.p.btree.rel([term], recurse=recurse, ctx=self.p.ctx, txn=self.p.txn)
        return rel.get(term, set())

class ParamConstraint(Constraint):
    """Constraint based on a ParamDef."""
    def init(self):
        self.priority = 1

    def run(self):
        return self.p.btree.find(self.param, self.term, op=self.op, txn=self.p.txn)

class RectypeConstraint(Constraint):
    """Rectype constraints."""
    def init(self):
        self.priority = 2
        
    def run(self):
        f = set()
        recorddefs = [self.term]
        term = unicode(self.term)
        if term.endswith('*'):
            recorddefs = self.p.btree.dbenv['recorddef'].expand([self.term], ctx=self.p.ctx, txn=self.p.txn)
        for recorddef in recorddefs:
            f |= self.p.btree.find('rectype', recorddef, txn=self.p.txn)
        return f

class MacroConstraint(Constraint):
    """Macro constraints"""
    def run(self):
        # Execute a macro
        f = set()
        # Fetch the items we need in the parent group.
        items = self.p.btree.gets(self.p.result, ctx=self.p.ctx, txn=self.p.txn)
        
        # Parse the macro and get the Macro class
        regex_k = re.compile(emen2.db.database.VIEW_REGEX_P, re.VERBOSE)
        k = regex_k.search(self.param)
        macro = emen2.db.macros.Macro.get_macro(k.group('name'), db=self.p.ctx.db, cache=self.p.ctx.cache)
        # Preprocess
        macro.preprocess(k.group('args') or '', items)
        # Convert the term to the right type
        term = macro.keyclass(self.term) 
        # Run the comparison
        cfunc = getop(self.op)
        for item in items:
            # Run the macro
            value = macro.process(k.group('args') or '', item)
            if cfunc(term, value):
                f.add(item.name)
                self.p.vcache[item.name][self.param] = value
        return f
        
class Query(object):
    def __init__(self, constraints, keywords=None, mode='AND', subset=None, ctx=None, txn=None, btree=None):
        self.time = 0.0
        self.maxtime = MAXTIME
        self.starttime = time.time()
        
        # Subset
        self.subset = subset    
        # None or set() of query result
        self.result = None 
        # boolean AND / OR
        self.mode = mode        
        # Cache to hold values from constraint results
        self.vcache = collections.defaultdict(dict)

        # Database details
        self.ctx = ctx
        self.txn = txn
        self.btree = btree

        # Constraint Groups can contain sub-groups: see also init(), run()
        self.param = None    
        self.priority = 1
        # Make constraints
        self.constraints = []        
        if keywords:
            self.constraints.append(self._makeconstraint('keywords','starts',keywords))
        for c in constraints:
            self.constraints.append(self._makeconstraint(*c))
            
    def run(self):
        # Start the clock
        t = time.time()
        
        if self.subset is not None:
            # print "Restricting to subset:", self.subset
            self.result = self.btree.filter(set(self.subset), ctx=self.ctx, txn=self.txn)
                    
        # Run the constraints
        for c in sorted(self.constraints, key=lambda x:x.priority):
            f = c.run()            
            self._bool(f)

        # Filter by permissions
        if self.subset is None and not self.constraints:
            self.result = set()
        else:
            self.result = self.btree.filter(self.result or set(), ctx=self.ctx, txn=self.txn)

        # Update the approx. running time.
        self.time += time.time() - t    
        return self.result

    def sort(self, sortkey='name', reverse=False, pos=0, count=0, rendered=False):
        reverse = bool(reverse)
        # Shortcut.
        if sortkey == 'name':
            sequence = emen2.db.config.get('record.sequence')
            if self.btree.keytype == 'record' and sequence:
                result = sorted(self.result, reverse=reverse, key=lambda x:int(x))
            else:
                result = sorted(self.result, reverse=reverse)                
            if count > 0:
                result = result[pos:pos+count]
            return result

        # print "Sorting by: %s"%sortkey
        t = time.time()

        # We don't have a constraint that matched the sortkey
        # This does not change the constraint, just gets values.
        params = [i.param for i in self.constraints]
        if sortkey not in params:
            c = self._makeconstraint(sortkey, op='noop')
            c.run()

        pd = self.btree.dbenv['paramdef'].get(sortkey, ctx=self.ctx, txn=self.txn)
        if pd:
            if pd.vartype == 'string':
                sortfunc = lambda x:unicode(self.vcache.get(x, '')).lower()
            # Fetch all the items... fix this.
            # Also, fix lowercase.
            items = self.btree.gets(self.result, ctx=self.ctx, txn=self.txn)
            for i in items:
                self.vcache[i.name][sortkey] = i.get(sortkey, '')
        else:
            # Macro?
            pass

        # ian: todo: fix...
        sortfunc = lambda x:x
        result = sorted(self.result, key=sortfunc, reverse=reverse)
        if count > 0:
            result = result[pos:pos+count]

        self.time += time.time() - t
        return result

    ##### Results / Cache methods #####
    
    def _bool(self, f):
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
            raise QuerySyntaxError("Unknown boolean mode %s."%self.mode)
        
    def _makeconstraint(self, param, op='noop', term=''):
        op = SYNONYMS.get(op, op)
        constraint = None
        # if param.startswith('$@'):
        if param.endswith(')'): # hacky
            # Macros
            constraint = MacroConstraint(param, op, term)
        elif param in ['parents', 'children']:
            constraint = RelConstraint(param, op, term)
        elif param == 'rectype':
            constraint = RectypeConstraint(param, op, term)
        else:
            constraint = ParamConstraint(param, op, term)
        constraint.setparent(self)
        return constraint
