# $Id$
import collections

from emen2.web.view import View


@View.register
class ParamDef(View):

	@View.add_matcher(r'^/paramdef/(?P<name>.+)/$')
	def main(self, name=None):
		self.template = '/pages/paramdef'
		
		paramdef = self.db.getparamdef(name)

		editable = 0
		if self.db.checkadmin():
			editable = 1

		create = 0
		if self.db.checkcreate():
			create = 1
		
		self.title = "Parameter: %s"%paramdef.desc_short

		parentmap = self.routing.execute('Map/embed', db=self.db, keytype='paramdef', root=paramdef.name, mode='parents', recurse=3)

		units = set()
		if paramdef and paramdef.property:
			units = self.db.getpropertyunits(paramdef.property)

		vartypes = self.db.getvartypenames()

		self.ctxt.update(dict(
			paramdef = paramdef,
			create = create,
			vartypes = vartypes,
			editable = editable,
			edit = False,
			new = False,
			parentmap = parentmap
			))


	@View.add_matcher(r'^/paramdef/(?P<name>.+)/edit/$')
	def edit(self, name, **kwargs):
		if self.request_method == 'post':			
			paramdef = self.db.getparamdef(name)
			paramdef.update(kwargs)
			pd = self.db.putparamdef(paramdef)
			if pd:
				self.redirect(self.routing.reverse('ParamDef/view', name=pd.name))
				return
				
		self.main(name=name)
		self.ctxt['edit'] = True
		




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
