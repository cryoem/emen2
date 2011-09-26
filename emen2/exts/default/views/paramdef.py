# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
import emen2.web.config
CVars = emen2.web.config.CVars
from emen2.web.view import View
###

import emen2.web.markuputils

from map import Map

@View.register
class ParamDef(View):

	@View.add_matcher(r'^/paramdef/(?P<name>.+)/(?P<action>.+)/$', r'^/paramdef/(?P<name>\w+)/$')
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

		title = "Parameter Viewer: %s"%self.name

		if edit:
			self.template = '/pages/paramdef.edit'
			title = "Parameter Editor: %s"%self.name
			if new:
				title = "Parameter Creator: New parameter based on %s"%self.name


		###############

		parentmap = Map(db=self.db)
		parentmap.init(mode=mapmode, keytype="paramdef", root=self.name, recurse=-1)
		parentmap_ctxt = parentmap.get_context()

		###############

		pages = {
			'classname':'main',
			'labels':{'main':"Parameter Viewer"},
			'content':{'main':""},
			'href':	{'main': '%s/paramdef/%s/'%(CVars.webroot, self.name)}
			}

		if edit:
			pages["labels"]["main"]="Parameter Editor"
		if new:
			pages["labels"]["main"]="Parameter Creator"

		pages = emen2.web.markuputils.HTMLTab(pages)

		pages_map = emen2.web.markuputils.HTMLTab({
			'classname':'map',
			'content':{'parents':parentmap},
			'active':'parents',
			'order':['parents','children'],
			'labels':{'parents':'Parents','children':'Children'}
		})


		creator = self.db.getuser(paramdef.creator) or {}
		displaynames = {}
		displaynames[paramdef.creator] = creator.get('displayname', paramdef.creator)

		units = set()
		if paramdef and paramdef.property:
			units = self.db.getpropertyunits(paramdef.property)

		self.update_context(dict(
			parentmap = parentmap.get_data(),
			title = title,
			editable = editable,
			edit = edit,
			new = new,
			mapmode = mapmode,
			paramdef = paramdef,
			# ian: todo! fix this
			displaynames = displaynames,
			keytype = "paramdef",
			key = self.name,
			pages_map = pages_map,
			pages = pages,
			vartypes = self.db.getvartypenames(),
			properties = self.db.getpropertynames(),
			units = units,
			create = create
			))



@View.register
class ParamDefs(View):

	@View.add_matcher(r'^/paramdefs/$', action=r'^/paramdefs/(?P<action>\w+)/$')
	def init(self, action=None, q=None):

		if action == None or action not in ["vartype", "name", "tree", "property"]:
			action = "tree"

		if q:
			action = "name"
			paramdefs = self.db.findparamdef(q)
		else:
			paramdefs = self.db.getparamdef(self.db.getparamdefnames())

		self.template='/pages/paramdefs.%s'%action
		self.set_context_item('create',self.db.checkcreate())

		pages = {
			'classname':'main',
			'labels':{'tree':"Parameter Ontology", 'name': "Parameters by Name", 'vartype':'Parameters by Variable Type', 'property':'Parameters by Physical Property'},
			'content':{'main':""},
			'href':	{'tree': '%s/paramdefs/tree/'%CVars.webroot, 'name': '%s/paramdefs/name/'%CVars.webroot, 'vartype': '%s/paramdefs/vartype/'%CVars.webroot, 'property': '%s/paramdefs/property/'%CVars.webroot},
			'order': ['tree', 'name', 'vartype', 'property']
		}
		pages['active'] = action
		self.title = pages['labels'].get(action)
		pages = emen2.web.markuputils.HTMLTab(pages)
		self.set_context_item('pages',pages)

		childmap = Map(db=self.db)
		childmap.init(mode="children", keytype="paramdef", root="root", recurse=-1)

		self.set_context_item('q',q)
		self.set_context_item("paramdefs",paramdefs)
		self.set_context_item("childmap",childmap.get_data())






__version__ = "$Revision$".split(":")[1][:-1].strip()
