# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
import emen2.web.config
CVars = emen2.web.config.CVars
from emen2.web.view import View


@View.register
class RecordDef(View):


	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/new/$')	
	def new(self, *args, **kwargs):
		pass
		

	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/edit/$')	
	def edit(self, *args, **kwargs):
		pass

	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/$')	
	def init(self, name=None, action=None, new=0):
		self.template = '/pages/recorddef'
		self.name = name
		self.action = action

		recdef = self.db.getrecorddef(self.name, filt=False)

		edit = 0
		new = 0
		mapmode = "parents"

		if self.action=="edit":
			edit = 1

		if self.action=="new":
			new = 1
			edit = 1

		if self.action=="map":
			mapmode = "children"

		ctxuser = self.db.checkcontext()[0]
		editable = 0
		if self.db.checkadmin() or ctxuser in [recdef.owner, recdef.creator]:
			editable = 1

		create = 0
		if self.db.checkcreate():
			create = 1

		title = "Protocol Viewer: %s"%self.name

		if edit:
			self.template='/pages/recorddef.edit'
			title = "Protocol Editor: %s"%self.name
			if new:
				title = "Protocol Creator: New protocol based on %s"%self.name


		###############

		parentmap = self.routing.execute('Map/embed', db=self.db, keytype='recorddef', root=self.name, mode='parents', recurse=3)

		###############

		displaynames = {}
		try:
			creator = self.db.getuser(recdef.creator, filt=False)
			displaynames[recdef.creator] = creator.displayname
		except:
			pass

		self.update_context(dict(
			parentmap = parentmap.get_data(),
			title = title,
			editable = editable,
			edit = edit,
			new = new,
			keytype = "recorddef",
			mapmode = mapmode,
			recdef = recdef,
			displaynames = displaynames,
			key = self.name,
			create = create
			))



@View.register
class RecordDefs(View):

	@View.add_matcher(r'^/recorddefs/name/$')
	def name(self, *args, **kwargs):
		return self.init(action='name', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/count/$')
	def count(self, *args, **kwargs):
		return self.init(action='count', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/tree/$')
	def tree(self, action=None, q=None):
		return self.init(action='tree', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/$')
	def init(self, action=None, q=None):

		if action == None or action not in ["tree", "name", "count"]:
			action = "tree"

		if q:
			recorddefs = self.db.findrecorddef(q)
			action = "name"
		else:
			recorddefs = self.db.getrecorddef(self.db.getrecorddefnames())


		self.template='/pages/recorddefs.%s'%action
		self.set_context_item('create',self.db.checkcreate())

		pages = {
			'classname':'main',
			'labels':{'tree':"Protocol Ontology", 'name':'Protocols by Name', 'count':'Protocols by Number of Records'},
			'content':{'main':""},
			'href':	{'tree': '%s/recorddefs/tree/'%CVars.webroot, 'name': '%s/recorddefs/name/'%CVars.webroot, 'count': '%s/recorddefs/count/'%CVars.webroot},
			'order': ['tree', 'name', 'count']
		}

		pages['active'] = action
		self.title = pages['labels'].get(action)
		self.set_context_item('pages',pages)

		childmap = self.routing.execute('Map/embed', db=self.db, mode="children", keytype="recorddef", root="root", recurse=-1)

		count = {}
		if action != 'tree':
			for pd in recorddefs:
				count[pd.name] = len(self.db.getindexbyrectype(pd.name))

		self.set_context_item('q', q)
		self.set_context_item('count', count)
		self.set_context_item("recorddefs", recorddefs)
		self.set_context_item("childmap", childmap)





__version__ = "$Revision$".split(":")[1][:-1].strip()
