# $Id: map.py,v 1.26 2013/05/07 07:22:05 irees Exp $
from emen2.web.view import View
import emen2.db.config


def bfs(root, tree, recurse=1):
    maxrecurse = emen2.db.config.get('params.maxrecurse')
    def inner(stack, children, depth=0):
        if depth >= maxrecurse:
            return
        if recurse > 0 and depth >= recurse:
            return
        for child in children:
            newchildren = tree.get(child, set())
            stack |= newchildren
            inner(stack, newchildren, depth=depth+1)

    stack = set()
    inner(stack, tree.get(None, [root]))
    return stack



@View.register
class Tree(View):
    @View.add_matcher(r'^/tree/(?P<keytype>\w+)/(?P<root>[^/]*)/(?P<mode>\w+)/$', name='embed')
    def embed(self, root=None, recurse=1, keytype="record", action=None, mode="children", rectype=None, expandable=True, collapse_rectype=None, collapsed=None, id='', link=None, showroot=True):
        self.template = '/pages/tree'
        self.title = 'Sitemap'

        root = root
        keytype = keytype
        recurse = int(recurse)
        mode = mode
        expandable = expandable
        collapsed = collapsed or set()

        # Expand all nodes. -3 turns into -1...
        if action=="expand" or recurse == -1:
            recurse = -3

        parents = set()

        # add 2 to recurse to get enough info to draw the next level
        if mode == "children":
            tree = self.db.rel.rel([root], rel="children", recurse=recurse+2, keytype=keytype, tree=True)
            # get one level of parents as well..
            parents = self.db.rel.parents(root, keytype=keytype)
        else:
            tree = self.db.rel.rel([root], rel="parents", recurse=recurse+2, keytype=keytype, tree=True)
        # if collapse_rectype:
        #    collapsed |= self.db.rel.children(root, recurse=-1, rectype=collapse_rectype)

        # connect the root to "None" to simplify drawing..
        tree[None] = [root]
        
        # Get all the names we need to render
        stack = bfs(root, tree, recurse=recurse)
        stack.add(root)
        stack |= parents

        recnames = {}
        if keytype == "record":
            recnames.update(self.db.view(stack))
        elif keytype == "paramdef":
            pds = self.db.paramdef.get(stack)
            for pd in pds:
                recnames[pd.name] = pd.desc_short
        elif keytype == "recorddef":
            rds = self.db.recorddef.get(stack)
            for rd in rds:
                recnames[rd.name] = rd.desc_short

        self.ctxt['mode'] = mode
        self.ctxt['root'] = root
        self.ctxt['tree'] = tree
        self.ctxt['recurse'] = recurse
        self.ctxt['recnames'] = recnames
        self.ctxt['keytype'] = keytype
        self.ctxt['parents'] = parents
        self.ctxt['expandable'] = expandable
        self.ctxt['collapsed'] = collapsed
        self.ctxt['collapse_rectype'] = collapse_rectype
        self.ctxt['id'] = id
        self.ctxt['link'] = link
        self.ctxt['showroot'] = showroot


__version__ = "$Revision: 1.26 $".split(":")[1][:-1].strip()
