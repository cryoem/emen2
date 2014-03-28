"""Yes, this view is always a mess and has always been a mess."""

import os
import operator
import datetime
import copy
import urllib

from emen2.web.view import View

cmp_order = [
    ".is.",
    ".not.",
    ".starts.",
    ".gte.",
    ".lte.",
    ".gt.",
    ".lt.",
    ".any.",
    '.none.',
    '.noop.',
    '.name.'
]

def query_to_path(q):
    pass
            
class TooManyFiles(Exception):
    pass

@View.register
class Query(View):
    
    def form_to_options(self, form):
        return
    
    def form_to_constraints(self, form):
        """This is also a mess."""
        form = form or {}
        keys = form.keys()
        c = []
        for k in keys:
            if k.startswith('form_') and hasattr(form[k], 'items'):
                v = form.pop(k)
                param = v.get('param', '')
                comp = v.get('cmp', '')
                value = v.get('value', '')
                if v.get('recurse_v') and value and not value.endswith('*'):
                    value = '%s*'%value            
                i = [param, comp, value]
                if all(i):
                    c.append(i)
        return c
    
    def constraints_to_path(self, constraints):
        path = []
        for c in constraints:
            path.append(urllib.quote_plus("""%s.%s.%s"""%(c[0], c[1], c[2])))
        return "/".join(path)
    
    def path_to_constraints(self, path):
        """This is a mess."""
        constraints = []
        if path == None:
            path = ''
        for constraint in path.split("/"):
            constraint = urllib.unquote(constraint)
            match = []
            foundcomps = filter(lambda x:constraint.partition(x)[1], cmp_order)
            if foundcomps:
                comp = foundcomps[0]
                p1, p2, p3 = constraint.partition(comp)
                p1 = urllib.unquote(p1)
                p2 = urllib.unquote(p2).replace('.','')
                p3 = urllib.unquote(p3)
                if p1:
                    match.append(p1)
                    if p2:
                        match.append(p2)
                        if p3:
                            match.append(p3)
            elif constraint:
                match = [constraint]
            if match:
                constraints.append(match)
        return constraints
    
    def common(self, path=None, q=None, c=None, form=None):
        self.template = '/pages/query.main'
        self.title = "Query"
        q = q or {}
        q.update(form)
        c = c or q.get('c', [])
        c.extend(self.path_to_constraints(path))
        c.extend(self.form_to_constraints(form))
        q['c'] = c
        self.q = q
        self.ctxt['parent'] = None
        self.ctxt['rectype'] = None
        self.ctxt['header'] = True
        self.ctxt['controls'] = True

    @View.add_matcher(
        r'^/query/$',
        r'^/query/form/$',
        r'^/query/form/(?P<path>.+)/$'
        )
    def form(self, path=None, q=None, c=None, **form):
        self.common(path, q, c, form=form)
        self.template = '/pages/query.form'
        self.ctxt['q'] = self.q
        
    @View.add_matcher(r'^/query/redirect/$')
    def form_redirect(self, path=None, q=None, c=None, **form):
        form2 = {}
        for k,v in form.items():
            if v:
                form2[k] = v
        form = form2
        self.common(path, q, c, form=form)
        self.template = '/pages/query.form'
        self.ctxt['q'] = self.q
        self.redirect("%s/query/results/%s/?%s"%(self.ctxt.root, self.constraints_to_path(self.q['c']), urllib.urlencode(form)))

    @View.add_matcher(
        r'^/query/results/$',
        r'^/query/results/(?P<path>.+)/$',
        name='query')
    def main(self, path=None, q=None, c=None, **form):
        self.common(path, q, c, form)
        # print "running:", self.q
        self.q = self.db.table(**self.q)
        self.ctxt['q'] = self.q

    @View.add_matcher(r'^/query/embed/(?P<path>.+)/$', name='embed')
    def embed(self, path=None, q=None, c=None, create=False, rectype=None, parent=None, controls=True, header=True, **form):
        # create/rectype/parent for convenience.
        self.main(path, q, c)
        self.template = '/pages/query'
        # awful hack
        self.ctxt['controls'] = controls
        self.ctxt['header'] = header
        self.ctxt['parent'] = parent
        self.ctxt['rectype'] = rectype

    @View.add_matcher(
        r'^/query/plot/$',
        r'^/query/plot/(?P<path>.+)/$',
        name='plot')
    def plot(self, path=None, q=None, c=None, x=None, y=None, z=None, **form):
        self.common(path, q, c)
        self.q['x'] = x
        self.q['y'] = y
        self.q['z'] = z
        self.template = '/pages/query.plot'
        self.q = self.db.plot(**self.q)
        self.ctxt['q'] = self.q

    # /download/ can't be in the path because of a emen2resource.getchild issue
    @View.add_matcher(r'^/query/attachments/(?P<path>.+)/$', name='attachments')
    def attachments(self, path=None, q=None, c=None, confirm=False, **form):
        self.common(path, q, c)
        self.q['count'] = 1000 # Show the maximum number of files by default...
        self.q = self.db.query(**self.q)        

        # Look up all the binaries
        bdos = self.db.binary.find(record=self.q['names'], count=0)
        names = [i.name for i in bdos]
        self.ctxt['q'] = self.db.table(subset=names, keytype="binary", checkbox=True, view="{{checkbox()}} {{thumbnail}} {{filename}} {{filesize}} {{recname(record)}} {{record}}")

