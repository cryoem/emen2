# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View

import emen2.web.markuputils



class RecordDef(View):
	__metaclass__ = View.register_view
	__matcher__ = {
		'action': r'^/recorddef/(?P<name>.+)/(?P<action>.+)/$',
		'main': r'^/recorddef/(?P<name>\w+)/$'
		}


	def init(self, name=None, action=None, new=0, notify=[]):
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

		parentmap = emen2.web.views.map.Map(mode=mapmode, keytype="recorddef", root=self.name, recurse=-1, db=self.db)
		parentmap_ctxt = parentmap.get_context()

		###############

		labels = {"mainview":"Protocol","tabularview":"Table","recname":"Record Title","defaultview":"Default"}

		pages = {
			'classname':'main',
			'labels':{'main':"Protocol Viewer"},
			'content':{'main':""},
			'href':	{'main': self.dbtree.reverse(self.__class__.__name__, name=self.name)}
			}

		if edit:
			pages["labels"]["main"]="Protocol Editor"
		if new:
			pages["labels"]["main"]="Protocol Creator"

		pages = emen2.web.markuputils.HTMLTab(pages)

		pages_map = emen2.web.markuputils.HTMLTab({
			'classname':'map',
			'content':{'parents':parentmap},
			'active':'parents',
			'order':['parents','children'],
			'labels':{'parents':'Parents','children':'Children'}
		})

		pages_recdefviews = {
			'classname':'recdefviews',
			'active': 'recname',
			'content':{},
			'labels':{}
			}

		for k,v in recdef.views.items():
			pages_recdefviews["content"][k]=v
			pages_recdefviews["labels"][k]=labels.get(k,k)


		if edit:
			pages_recdefviews['labels']['new']='Add View [+]'
			pages_recdefviews['js']={'new':'void(0)'}
			pages_recdefviews["order"]=sorted(pages_recdefviews["content"].keys())+['new']
			if len(recdef.views) == 0:
				pages_recdefviews["active"]='new'

			#self.ctxt["pages_recdefviews"]["content"]["new"]="No additional views defined; why not add some?"

		displaynames = {}
		try:
			creator = self.db.getuser(recdef.creator, filt=False)
			displaynames[recdef.creator] = creator.displayname
		except:
			pass

		pages_recdefviews = emen2.web.markuputils.HTMLTab(pages_recdefviews)

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
			pages_recdefviews = pages_recdefviews,
			pages_map = pages_map,
			pages = pages,
			create = create
			))



@View.register
class RecordDefs(View):
	@View.add_matcher(r'^/recorddefs/$', r'^/recorddefs/(?P<action>\w+)/$')
	def init(self, action=None, q=None):

		if action == None or action not in ["vartype", "name", "count"]:
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
			'href':	{'tree': '%s/recorddefs/tree/'%g.EMEN2WEBROOT, 'name': '%s/recorddefs/name/'%g.EMEN2WEBROOT, 'count': '%s/recorddefs/count/'%g.EMEN2WEBROOT},
			'order': ['tree', 'name', 'count']
		}

		pages['active'] = action
		self.title = pages['labels'].get(action)
		pages = emen2.web.markuputils.HTMLTab(pages)
		self.set_context_item('pages',pages)

		childmap = emen2.web.views.map.Map(mode="children", keytype="recorddef", root="root", recurse=-1, db=self.db)

		count = {}
		if action != 'tree':
			for pd in recorddefs:
				count[pd.name] = len(self.db.getindexbyrectype(pd.name))

		self.set_context_item('q',q)
		self.set_context_item('count',count)
		self.set_context_item("recorddefs",recorddefs)
		self.set_context_item("childmap",childmap.get_data())





__version__ = "$Revision$".split(":")[1][:-1].strip()
