# $Id$
import urllib
import time

# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View

import emen2.util.listops as listops
import emen2.web.responsecodes

from map import Map, dfs


class RecordNotFoundError(emen2.web.responsecodes.NotFoundError):
	title = 'Record not Found'
	msg = 'Record %s not found'



class RecordBase(View):
	def _init(self, name=None, children=True, parents=True, notify=None):
		"""Main record rendering."""
		self.name = int(name)
		recnames = {}
		displaynames = {}

		####
		# Get record..
		try:
			self.rec = self.db.getrecord(self.name, filt=False)
		except (KeyError, TypeError), inst:
			raise RecordNotFoundError, name

		####
		# Find if this record is in the user's bookmarks
		bookmarks = []
		user = None
		try:
			t = time.time()
			user = self.ctxt['USER']
			brec = self.db.getrecord(sorted(self.db.getchildren(user.record, rectype='bookmarks')))
			if brec:
				bookmarks = brec[-1].get('bookmarks', [])
		except Exception, e:
			pass

		self.ctxt['bookmarks'] = bookmarks

		####
		# Get RecordDef
		self.recdef = self.db.getrecorddef(self.rec.rectype)

		####
		# User display names
		# These are generally displayed: creator, modifyuser, comments.
		getusers = set([self.rec.get('creator'), self.rec.get('modifyuser')])
		# getusers |= set([i[0] for i in self.rec.get('comments',[])])
		for user in self.db.getuser(getusers):
			displaynames[user.name] = user.displayname

		####
		# Parent map
		parentmap = self.db.getparenttree(self.rec.name, recurse=3)
		found = dfs(self.rec.name, parentmap, 3)
		found.add(self.rec.name)
		recnames.update(self.db.renderview(found))

		####
		# Children
		if children:
			children = self.db.getchildren(self.name)
			self.childgroups = self.db.groupbyrectype(children)
			pages = {
				'classname':'main',
				'content':{},
				'labels':{'main':'<span data-name="%s" class="view">%s</span>'%(self.name, recnames.get(self.rec.name))},
				'href':	{'main':'%s/record/%s/'%(g.EMEN2WEBROOT,self.name)},
				'active': 'main',
				'order': ['main']
			}
			for k,v in self.childgroups.items():
				pages["order"].append(k)
				pages["labels"][k] = "%s (%s)"%(k,len(v))
				pages["content"][k] = ""
				pages["href"][k] = self.dbtree.reverse('Record/children', name=self.name, childtype=k)

			pages = emen2.web.markuputils.HTMLTab(pages)
		else:
			pages = None

		# Update context
		self.update_context(
			rec = self.rec,
			recs = {str(self.name):self.rec},
			recdef = self.recdef,
			notify = notify or [],
			title = "Record: %s: %s (%s)"%(self.rec.rectype, recnames.get(self.rec.name), self.name),
			recnames = recnames,
			displaynames = displaynames,
			pages = pages,
			parentmap = parentmap,
			viewtype = "defaultview",
			edit = False,
			key = self.name,
			keytype = "record",
			create = self.db.checkcreate()
		)





@View.register
class Record(RecordBase):

	@View.add_matcher(r'^/record/(?P<name>\w+)/$')
	def main(self, name=None, sibling=None, notify=None):
		self._init(name=name, notify=notify)
		self.template = '/pages/record.main'

		# Siblings
		if sibling == None:
			sibling = self.rec.name
		sibling = int(sibling)
		siblings = self.db.getsiblings(sibling, rectype=self.rec.rectype)

		viewtype = "defaultview"
		if not self.recdef.views.get("defaultview"):
			viewtype = "mainview"

		# Render main view
		rendered = self.db.renderview(self.rec, viewtype=viewtype, edit=self.rec.writable())

		#######################################
		self.update_context(
			viewtype = viewtype,
			rendered = rendered,
			sibling = sibling,
			siblings = sorted(siblings)
		)


	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/$')
	def edit(self, name=None, notify=None):
		self.main(name=name, notify=notify)
		self.ctxt["edit"] = True


	@View.add_matcher(r'^/record/(?P<name>\d+)/new/(?P<rectype>\w+)/$')
	def new(self, name=None, rectype=None, inherit=None, private=False, copy=None, viewtype='mainview', notify=None):
		self._init(name=name, notify=notify, children=False)
		self.template = '/pages/record.new'
		# self.title = "New Record"

		try:
			inherit = int(name)
		except:
			inherit = None

		user = self.db.checkcontext()[0]
		newrec = self.db.newrecord(rectype, inherit=inherit)

		if copy:
			for k in self.rec.getparamkeys():
				newrec[k] = self.rec[k]

		if private:
			private = int(private)

		if private:
			newrec['groups'] = set()
			newrec['permissions'] = [[],[],[],[user]]

		rendered = self.db.renderview(newrec, edit=True, viewtype=viewtype)
		recdef = self.db.getrecorddef(newrec.rectype)
		recorddefnames = self.db.getrecorddefnames()

		# ${recdef.desc_short} (${recdef.name})
		self.title = 'New %s (%s)'%(recdef.desc_short, recdef.name)
		
		self.update_context(
			recdef = recdef,
			newrec = newrec,
			viewtype = viewtype,
			rendered = rendered,
			recorddefnames = recorddefnames
		)


	@View.add_matcher('^/record/(?P<name>\d+)/children/(?P<childtype>\w+)/$')
	def children(self,name=None,childtype=None,notify=None):
		"""Main record rendering."""
		self._init(name=name, notify=notify)
		self.template = "/pages/record.table"
		self.ctxt["create"] = self.db.checkcreate()
		self.ctxt["childtype"] = childtype
		c = [['children', 'name', name], ['rectype', '==', childtype]]
		self.ctxt["q"] = self.db.query(c=c, table=True, count=1000)
		self.ctxt["pages"].setactive(childtype)


	#@write
	@View.add_matcher("^/record/(?P<name>\d+)/delete/$")
	def delete(self, commit=False, name=None, notify=None):
		"""Main record rendering."""

		self._init(name=name, notify=notify)
		self.template = "/pages/record.delete"
		self.title = "Delete Record"

		orphans = checkorphans(self.db, self.name)
		recnames = self.db.renderview(orphans)

		if commit:
			self.db.deleterecord(self.name)

		self.set_context_item("commit", commit)
		self.set_context_item("orphans", orphans)
		self.set_context_item("recnames", recnames)


	@View.add_matcher("^/record/(?P<name>\d+)/history/$", "^/record/(?P<name>\d+)/history/(?P<revision>.*)/")
	def history(self, name=None, notify=None, simple=False, revision=None):
		"""Revision/history/comment viewer"""

		if revision:
			revision = revision.replace("+", " ")

		if simple:
			self._init(name=name, notify=notify, parents=False, children=False)
			self.template = "/pages/record.history"
		else:
			self._init(name=name, notify=notify, children=False)
			self.template = "/pages/record.revision"

		rendered = ""
		self.title = "History"
		self.set_context_item('simple', simple)
		self.set_context_item("revision", revision)
		self.set_context_item("rendered", rendered)


	@View.add_matcher("^/record/(?P<name>\d+)/email/$")
	def email(self, name=None, notify=None):
		"""Main record rendering."""

		self._init(name=name, notify=notify)
		self.template = "/pages/record.email"
		self.title = "Users referenced by record %s"%(self.name)

		# ian: todo: replace!!
		pds = self.db.findparamdef(record=self.rec.keys())
		users_ref = set()
		for i in pds:
			v = self.rec.get(i.name)
			if not v:
				continue
			if i.vartype == "user":
				users_ref.add(v)
			elif i.vartype == "userlist":
				users_ref |= set(v)

		users_permissions = set()
		for v in self.rec.get('permissions'):
			users_permissions |= set(v)

		users = self.db.getuser(users_ref | users_permissions, filt=True)
		for user in users:
			user.getdisplayname(lnf=True)

		self.ctxt['users'] = users


	# @View.add_matcher(r'^/record/(?P<name>\d+)/publish/$')
	# def publish(self, name=None):
	# 	self._init(name=name)
	# 	self.template = '/pages/record.publish'
	# 	self.title = 'Publish Records'
	# 
	# 	status = self.db.getindexbypermissions(groups=["publish"])
	# 	childmap_view = Map(mode="children", keytype="record", recurse=-1, root=self.name, db=self.db)
	# 	childmap = childmap_view.get_data()
	# 
	# 	# print status
	# 
	# 	self.set_context_item("childmap", childmap)
	# 	self.set_context_item("collapsed", childmap_view.collapsed)
	# 	self.set_context_item("children", childmap_view.collapsedchildren)
	# 	self.set_context_item("status", status)


	# @View.add_matcher(r'^/record/(?P<name>\d+)/boxer/$')
	# def boxer(self, name=None):
	# 	self._init(name=name)
	# 	self.template = '/pages/boxer'
	# 	self.title = "web.boxer (EXPERIMENTAL!)"
	# 
	# 	boxrecords = self.db.getchildren(self.rec.name, rectype="box")
	# 	bdo = self.rec.get('file_binary_image')
	# 	bdo = self.db.getbinary(bdo)
	# 	if not bdo:
	# 		self.error("No ccd frames found! Cannot start web.boxer.")
	# 		return
	# 
	# 	self.set_context_item("bdo",bdo)



# moved from db...
def checkorphans(db, name):
	"""Find orphaned records that would occur if name was deleted.

	@param name Return orphans that would result from deletion of this Record

	@return Set of orphaned Record IDs
	"""
	sname = set([name])
	saved = set()

	# this is hard to calculate
	children = db.getchildtree(name, recurse=-1)
	orphaned = reduce(set.union, children.values(), set())
	orphaned.add(name)
	parents = db.getparenttree(orphaned)

	# orphaned is records that will be orphaned if they are not rescued
	# find subtrees that will be rescued by links to other places
	for child in orphaned - sname:
		if parents.get(child, set()) - orphaned:
			saved.add(child)

	children_saved = db.getchildtree(saved, recurse=-1)
	children_saved_set = set()
	for i in children_saved.values() + [set(children_saved.keys())]:
		children_saved_set |= i
	# .union( *(children_saved.values()+[set(children_saved.keys())], set()) )

	orphaned -= children_saved_set

	return orphaned




__version__ = "$Revision$".split(":")[1][:-1].strip()
