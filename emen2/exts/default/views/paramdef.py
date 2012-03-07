# $Id$
import collections

from emen2.web.view import View


@View.register
class ParamDef(View):

	@View.add_matcher(r'^/paramdef/(?P<name>\w+)/$')
	def main(self, name=None):
		self.paramdef = self.db.getparamdef(name, filt=False)
		self.template = '/pages/paramdef.main'
		self.title = "Parameter: %s"%self.paramdef.desc_short

		parentmap = self.routing.execute('Tree/embed', db=self.db, keytype='paramdef', root=self.paramdef.name, mode='parents', recurse=3)

		units = set()
		if self.paramdef and self.paramdef.property:
			units = self.db.getpropertyunits(self.paramdef.property)

		vartypes = self.db.getvartypenames()
		properties = self.db.getpropertynames()

		self.ctxt.update(dict(
			paramdef = self.paramdef,
			create = self.db.checkcreate(),
			editable = self.paramdef.writable(),
			vartypes = vartypes,
			properties = properties,
			edit = False,
			new = False,
			parentmap = parentmap
			))


	@View.add_matcher(r'^/paramdef/(?P<name>\w+)/edit/$')
	def edit(self, name, **kwargs):
		if self.request_method == 'post':			
			paramdef = self.db.getparamdef(name, filt=False)
			paramdef.update(kwargs)
			pd = self.db.putparamdef(paramdef)
			if pd:
				self.redirect(self.routing.reverse('ParamDef/main', name=pd.name))
				return
				
		self.main(name=name)
		self.template = '/pages/paramdef.edit'
		self.ctxt['edit'] = True
		self.title = 'Edit Parameter: %s'%self.paramdef.desc_short
		
		
	@View.add_matcher(r'^/paramdef/(?P<name>\w+)/new/$')
	def new(self, name, **kwargs):
		if self.request_method == 'post':
			vartype = kwargs.pop('vartype', None)			
			paramdef = self.db.newparamdef(name, vartype=vartype)
			paramdef.update(kwargs)
			pd = self.db.putparamdef(paramdef)
			if pd:
				self.redirect(self.routing.reverse('ParamDef/main', name=pd.name))
				return

		self.main(name=name)
		self.template = '/pages/paramdef.new'
		self.paramdef.parents = set([self.paramdef.name])
		self.paramdef.children = set()
		self.ctxt['edit'] = True
		self.ctxt['new'] = True
		self.title = 'New Parameter based on: %s'%self.paramdef.desc_short


@View.register
class ParamDefs(View):

	@View.add_matcher(r'^/paramdefs/$')
	def main(self, action=None, q=None):
		

		paramdefnames = self.db.getparamdefnames()

		if action == None or action not in ["vartype", "name", "tree", "property"]:
			action = "tree"

		if q:
			action = "name"
			paramdefs = self.db.findparamdef(q)
		else:
			paramdefs = self.db.getparamdef(paramdefnames)



		# Tab Switcher
		pages = collections.OrderedDict()
		pages['tree'] = 'Parameter ontology'
		pages['name'] = 'Parameters by name'
		pages['vartype'] = 'Parameters by data type'
		pages['property'] = 'Parameters by property'
		uris = {}
		for k in pages:
			uris[k] = self.routing.reverse('ParamDefs/%s'%k)
		pages.uris = uris
		pages.active = action
		self.ctxt['pages'] = pages

		self.template = '/pages/paramdefs.%s'%action		
		self.title = pages.get(action)
		
		# Children
		childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="paramdef", root="root", recurse=-1, id='sitemap')

		self.ctxt['paramdefnames'] = paramdefnames
		self.ctxt['paramdefs'] = paramdefs
		self.ctxt['q'] = q
		self.ctxt['childmap'] = childmap
		self.ctxt['create'] = self.db.checkcreate()


	@View.add_matcher(r'^/paramdefs/vartype/$')
	def vartype(self, *args, **kwargs):
		return self.main(action='vartype', *args, **kwargs)


	@View.add_matcher(r'^/paramdefs/tree/$')
	def tree(self, *args, **kwargs):
		return self.main(action='tree', *args, **kwargs)


	@View.add_matcher(r'^/paramdefs/property/$')
	def property(self, *args, **kwargs):
		return self.main(action='property', *args, **kwargs)
		
		
	@View.add_matcher(r'^/paramdefs/name/$')
	def name(self, *args, **kwargs):
		return self.main(action='name', *args, **kwargs)
		






__version__ = "$Revision$".split(":")[1][:-1].strip()
