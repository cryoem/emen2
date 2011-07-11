# $Id$
import copy
import collections

import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View

def dfs(root, tree, recurse=1):
	def inner(stack, children, depth=0):
		if recurse > 0 and depth >= recurse:
			return

		for child in children:
			newchildren = tree.get(child, set())
			stack |= newchildren
			inner(stack, newchildren, depth=depth+1)

	stack = set()
	inner(stack, tree.get(None))
	return stack



@View.register
class Map(View):

	@View.add_matcher(r'^/sitemap/$', r'^/sitemap/(?P<root>\w+)/$')
	def sitemap(self, root=0, recurse=1, *args, **kwargs):
		self.template = '/pages/sitemap'
		self.title = 'Sitemap: %s'%root
		childmap = Map(mode="children", root=root, db=self.db, recurse=int(recurse))
		self.ctxt['childmap'] = childmap.get_data()
		self.ctxt['root'] = root


	#@View.add_matcher(r'^/sitemap/$', r'^/sitemap/(?P<root>\w+)/$', r'^/sitemap/(?P<root>\w+)/(?P<action>\w+)/$')
	@View.add_matcher(r'^/map/(?P<keytype>\w+)/(?P<root>\w+)/(?P<mode>\w+)/$')
	def init(self, root=None, recurse=1, keytype="record", action=None, mode="children", expandable=True, **kwargs):
		self.template = '/pages/map'
		self.title = 'Sitemap'
		self.root = root
		self.keytype = keytype
		self.recurse = int(recurse)
		self.mode = mode
		self.expandable = expandable

		# Might not be strictly necessary..
		if self.keytype == "record":
			self.root = int(self.root)

		# Expand all nodes. -3 turns into -1...
		if action=="expand" or self.recurse == -1:
			self.recurse = -3

		parents = set()

		# add 1 to recurse to get enough info to draw the next level
		if self.mode == "children":
			self.tree = self.db.getchildtree(self.root, recurse=self.recurse+2, keytype=self.keytype)
			# get one level of parents as well..
			parents = self.db.getparents(self.root, keytype=self.keytype)
		else:
			self.tree = self.db.getparenttree(self.root, recurse=self.recurse+2, keytype=self.keytype)

		# connect the root to "None" to simplify drawing..
		self.tree[None] = [self.root]

		stack = dfs(self.root, self.tree, recurse=self.recurse)
		stack.add(self.root)
		stack |= parents

		recnames = {}
		if self.keytype == "record":
			recnames.update(self.db.renderview(stack))
		elif self.keytype == "paramdef":
			pds = self.db.getparamdef(stack)
			for pd in pds:
				recnames[pd.name] = pd.desc_short
		elif self.keytype == "recorddef":
			rds = self.db.getrecorddef(stack)
			for rd in rds:
				recnames[rd.name] = rd.desc_short

		self.set_context_item('mode',self.mode)
		self.set_context_item('root',self.root)
		self.set_context_item('tree',self.tree)
		self.set_context_item('recurse',self.recurse)
		self.set_context_item('recnames',recnames)
		self.set_context_item('keytype',keytype)
		self.set_context_item('parents',parents)
		self.set_context_item('expandable',expandable)

__version__ = "$Revision$".split(":")[1][:-1].strip()
