# $Id$
import collections

from emen2.web.view import View
import emen2.db.config
import emen2.web.config
CVars = emen2.web.config.CVars



@View.register
class ParamDef(View):

	@View.add_matcher(r'^/paramdef/(?P<name>\w+)/$')
	def init(self,name=None, action=None, new=0):
		self.template = '/pages/paramdef'
		self.name = name
		self.action = action

		paramdef = self.db.getparamdef(self.name)
		edit = 0
		new = 0
		mapmode = "parents"

		if self.action == "edit": edit=1

		if self.action == "new":
			new = 1
			edit = 1

		if self.action == "map":
			mapmode = "children"

		editable = 0
		if self.db.checkadmin():
			editable = 1

		create = 0
		if self.db.checkcreate():
			create = 1
		
		title = "Parameter: %s"%paramdef.desc_short

		if edit:
			self.template = '/pages/paramdef.edit'
			title = "Parameter Editor: %s"%paramdef.desc_short
			if new:
				title = "Parameter Creator: New parameter based on %s"%paramdef.desc_short


		parentmap = self.routing.execute('Map/embed', db=self.db, keytype='paramdef', root=self.name, mode='parents', recurse=3)
		
		creator = self.db.getuser(paramdef.creator) or {}

		units = set()
		if paramdef and paramdef.property:
			units = self.db.getpropertyunits(paramdef.property)

		self.ctxt.update(dict(
			parentmap = parentmap,
			title = title,
			editable = editable,
			edit = edit,
			new = new,
			paramdef = paramdef,
			keytype = "paramdef",
			key = self.name,
			create = create
			))


	@View.add_matcher(r'^/paramdef/(?P<name>.+)/edit/$')
	def edit(self, name, **kwargs):
		pass





@View.register
class ParamDefs(View):

	@View.add_matcher(r'^/paramdefs/vartype/$')
	def vartype(self, *args, **kwargs):
		return self.init(action='vartype', *args, **kwargs)


	@View.add_matcher(r'^/paramdefs/tree/$')
	def tree(self, *args, **kwargs):
		return self.init(action='tree', *args, **kwargs)


	@View.add_matcher(r'^/paramdefs/property/$')
	def property(self, *args, **kwargs):
		return self.init(action='property', *args, **kwargs)
		
		
	@View.add_matcher(r'^/paramdefs/name/$')
	def name(self, *args, **kwargs):
		return self.init(action='name', *args, **kwargs)
		

	@View.add_matcher(r'^/paramdefs/$')
	def init(self, action=None, q=None):
		self.title = 'Parameters'
		
		if action == None or action not in ["vartype", "name", "tree", "property"]:
			action = "tree"

		if q:
			action = "name"
			paramdefs = self.db.findparamdef(q)
		else:
			paramdefs = self.db.getparamdef(self.db.getparamdefnames())

		self.template = '/pages/paramdefs.%s'%action

		# Tab Switcher
		pages = collections.OrderedDict()
		pages['tree'] = 'Parameter ontology'
		pages['name'] = 'Parameters by name'
		pages['vartype'] = 'Parameters by vartype'
		pages['property'] = 'Parameters by property'
		uris = {}
		for k in pages:
			uris[k] = self.routing.reverse('ParamDefs/%s'%k)
		pages.uris = uris
		pages.active = action
		self.ctxt['pages'] = pages
		
		# Children
		childmap = self.routing.execute('Map/embed', db=self.db, mode="children", keytype="paramdef", root="root", recurse=-1, id='sitemap')

		self.set_context_item('q',q)
		self.set_context_item("paramdefs", paramdefs)
		self.set_context_item("childmap", childmap)
		self.set_context_item('create',self.db.checkcreate())





__version__ = "$Revision$".split(":")[1][:-1].strip()
