# $Id$
import collections

from emen2.web.view import View



@View.register
class RecordDef(View):

	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/new/$')	
	def new(self, *args, **kwargs):
		pass

	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/edit/$')	
	def edit(self, *args, **kwargs):
		if self.request_method == 'post':			
			recorddef = self.db.recorddef(name, filt=False)
			recorddef.update(kwargs)
			rd = self.db.recorddef(recorddef)
			if rd:
				self.redirect(self.routing.reverse('RecordDef/main', name=rd.name))
				return
				
		self.main(name=name)
		self.template = '/pages/recorddef.edit'
		self.ctxt['edit'] = True
		self.title = 'Edit Protocol: %s'%self.paramdef.desc_short

	@View.add_matcher(r'^/recorddef/(?P<name>\w+)/$')	
	def main(self, name=None):
		self.recorddef = self.db.getrecorddef(name, filt=False)
		self.template = '/pages/recorddef'
		self.title = "Protocol: %s"%self.recorddef.desc_short

		parentmap = self.routing.execute('Tree/embed', db=self.db, keytype='recorddef', root=self.recorddef.name, mode='parents', recurse=3)

		self.ctxt.update(dict(
			parentmap = parentmap,
			editable = self.recorddef.writable(),
			create = self.db.checkcreate(),
			recorddef = self.recorddef,
			edit = False,
			new = False,
		))



@View.register
class RecordDefs(View):

	@View.add_matcher(r'^/recorddefs/name/$')
	def name(self, *args, **kwargs):
		return self.main(action='name', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/count/$')
	def count(self, *args, **kwargs):
		return self.main(action='count', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/tree/$')
	def tree(self, action=None, q=None, *args, **kwargs):
		return self.main(action='tree', *args, **kwargs)


	@View.add_matcher(r'^/recorddefs/$')
	def main(self, action=None, q=None):
		recorddefnames = self.db.getrecorddefnames()
		
		if action == None or action not in ["tree", "name", "count"]:
			action = "tree"

		if q:
			recorddefs = self.db.findrecorddef(q)
			action = "name"
		else:
			recorddefs = self.db.getrecorddef(recorddefnames)

		# Tab Switcher
		pages = collections.OrderedDict()
		pages['tree'] = 'Protocol ontology'
		pages['name'] = 'Protocols by name'
		pages['count'] = 'Protocols by number of records'
		uris = {}
		for k in pages:
			uris[k] = self.routing.reverse('RecordDefs/%s'%k)
		pages.uris = uris
		pages.active = action
		self.ctxt['pages'] = pages

		self.template = '/pages/recorddefs.%s'%action		
		self.title = pages.get(action)

		# Children
		childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="recorddef", root="root", recurse=-1, id='sitemap')

		# Record counts
		count = {}
		if action != 'tree':
			for pd in recorddefs:
				count[pd.name] = len(self.db.getindexbyrectype(pd.name))

		self.ctxt['recorddefnames'] = recorddefnames
		self.set_context_item('q',q)
		self.set_context_item('count', count)
		self.set_context_item("recorddefs", recorddefs)
		self.set_context_item("childmap", childmap)
		self.set_context_item('create', self.db.checkcreate())




__version__ = "$Revision$".split(":")[1][:-1].strip()
