# $Id$
import urllib
import time

# Standard View imports
import emen2.db.config
from emen2.web.view import View

import emen2.web.config
CVars = emen2.web.config.CVars

import emen2.util.listops as listops
import emen2.web.responsecodes


class RecordNotFoundError(emen2.web.responsecodes.NotFoundError):
	title = 'Record not Found'
	msg = 'Record %s not found'


class RecordBase(View):
	def init(self, name=None, children=True, parents=True, **kwargs):
		"""Main record rendering."""
		recnames = {}
		displaynames = {}
		
		# Get record..
		try:
			self.rec = self.db.getrecord(name, filt=False)
		except (ValueError, KeyError, TypeError), inst: 
			raise RecordNotFoundError, name

		self.name = self.rec.name

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

		# Get RecordDef
		self.recdef = self.db.getrecorddef(self.rec.rectype)

		# User display names
		# These are generally displayed: creator, modifyuser, comments.
		getusers = set([self.rec.get('creator'), self.rec.get('modifyuser')])
		# getusers |= set([i[0] for i in self.rec.get('comments',[])])
		for user in self.db.getuser(getusers):
			displaynames[user.name] = user.displayname


		# Some warnings/alerts
		if self.rec.get('deleted'):
			self.ctxt['ERRORS'].append('Deleted Record')
		if 'publish' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Record marked as published data')
		if 'authenticated' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Any authenticated user can access this record')
		
		
		# Parent map
		if parents:
			parentmap = self.routing.execute('Map/embed', db=self.db, root=self.name, mode='parents', recurse=3)
		else:
			parentmap = ''


		# Children
		# TODO: Finish getting rid of HTMLTab
		if children:
			children = self.db.getchildren(self.name)
			self.childgroups = self.db.groupbyrectype(children)
			pages = {
				'classname':'main',
				'content':{},
				'labels':{'main':'<span data-name="%s" class="e2-view">%s</span>'%(self.name, recnames.get(self.rec.name))},
				'href':	{'main':'%s/record/%s/'%(CVars.webroot,self.name)},
				'active': 'main',
				'order': ['main']
			}
			for k,v in self.childgroups.items():
				pages["order"].append(k)
				pages["labels"][k] = "%s (%s)"%(k,len(v))
				pages["content"][k] = ""
				pages["href"][k] = '%s/record/%s/children/%s/'%(CVars.webroot, self.name, k)

		else:
			pages = None


		# Update context
		self.update_context(
			rec = self.rec,
			recs = {str(self.name):self.rec},
			recdef = self.recdef,
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
	def view(self, name=None, sibling=None):
		self.init(name=name)
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


	#@write
	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/$')
	def edit(self, name=None, **kwargs):
		if self.request_method == 'post' and kwargs:
			rec = self.db.getrecord(name, filt=False)
			try:
				rec.update(kwargs)
				self.db.putrecord(rec)
				self.headers['Location'] = '%s/record/%s/'%(CVars.webroot, name)
			except Exception, e:
				self.ctxt['ERRORS'].append(e)
				
		self.view(name=name)
		self.ctxt["edit"] = True


	#@write
	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/relationships/$', name='edit/relationships')
	def edit_relationships(self, name=None, parents=None, children=None):
		# ian: todo: Check orphans, show orphan confirmation page
		# ian: add map(int) for now..
		parents = set(map(int,listops.check_iterable(parents)))
		children = set(map(int,listops.check_iterable(children)))
		if self.request_method == 'post':
			rec = self.db.getrecord(name, filt=False)
			# print "Parents added:", parents - rec.parents
			# print "Parents removed:", rec.parents - parents
			# print "Children added:", children - rec.children
			# print "Children removed:", rec.children - children
			rec.parents = parents
			rec.children = children
			rec = self.db.putrecord(rec)
		
		self.template = '/redirect'
		self.headers['Location'] = '%s/record/%s/#relationships'%(self.ctxt['EMEN2WEBROOT'], name)



	#@write
	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/permissions/$', name='edit/permissions')
	def edit_permissions(self, name=None, permissions=None, groups=None, action=None, filt=False):
		permissions = permissions or {}
		groups = groups or []
		users = set()
		if hasattr(permissions, 'items'):
			for k,v in permissions.items():
				users |= set(listops.check_iterable(v))
		else:
			for v in permissions:
				users |= set(listops.check_iterable(v))
		
		if self.request_method == 'post':
			if action == 'add':
				self.db.setpermissions(names=name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt)			

			elif action == 'remove':
				self.db.setpermissions(names=name, recurse=-1, removeusers=users, removegroups=groups, filt=filt)			
				
			elif action == 'overwrite':
				self.db.setpermissions(names=name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt, overwrite_users=True, overwrite_groups=True)			
				
			else:
				rec = self.db.getrecord(name, filt=False)
				rec['groups'] = groups
				rec['permissions'] = permissions
				rec = self.db.putrecord(rec)

		self.template = '/redirect'
		self.headers['Location'] = '%s/record/%s/#permissions'%(self.ctxt['EMEN2WEBROOT'], name)
		

	#@write
	@View.add_matcher(r'^/record/(?P<name>\d+)/new/(?P<rectype>\w+)/$')
	def new(self, name=None, rectype=None, _copy=False, _private=False, **kwargs):
		self.init(name=name, children=False)
		self.template = '/pages/record.new'
		viewtype = 'mainview'

		inherit = None
		try:
			inherit = [int(name)]
		except:
			inherit = []

		if _private:
			newrec = self.db.newrecord(rectype)
			newrec.parents = inherit
		else:
			newrec = self.db.newrecord(rectype, inherit=inherit)

		if _copy:
			for rec in self.db.getrecord(inherit):
				newrec.update(rec)
			
		if self.request_method == 'post' and kwargs:
			newrec.update(kwargs)
			newrec = self.db.putrecord(newrec)
			if newrec:
				self.redirect('%s/record/%s/'%(CVars.webroot, newrec.name))
			else:
				self.error('Did not save record')
			return


		recdef = self.db.getrecorddef(newrec.rectype)
		rendered = self.db.renderview(newrec, edit=True, viewtype=viewtype)

		self.title = 'New %s (%s)'%(recdef.desc_short, recdef.name)
		self.update_context(
			recdef = recdef,
			newrec = newrec,
			viewtype = viewtype,
			rendered = rendered
		)
			


	@View.add_matcher('^/record/(?P<name>\d+)/children/(?P<childtype>\w+)/$')
	def children(self, name=None, childtype=None):
		"""Main record rendering."""
		self.init(name=name)
		self.template = "/pages/record.table"
		self.ctxt["create"] = self.db.checkcreate()
		self.ctxt["childtype"] = childtype
		c = [['children', 'name', name], ['rectype', '==', childtype]]
		query = self.routing.execute('Query/embed', db=self.db, c=c)
		self.ctxt['table'] = query
		self.ctxt['q'] = {}
		self.ctxt["pages"].setactive(childtype)


	#@write
	@View.add_matcher("^/record/(?P<name>\d+)/delete/$")
	def delete(self, commit=False, name=None):
		"""Main record rendering."""

		self.init(name=name)
		self.template = "/pages/record.delete"
		self.title = "Delete Record"

		orphans = checkorphans(self.db, self.name)
		recnames = self.db.renderview(orphans)

		if commit:
			self.db.deleterecord(self.name)

		self.set_context_item("commit", commit)
		self.set_context_item("orphans", orphans)
		self.set_context_item("recnames", recnames)


	@View.add_matcher(r'^/record/(?P<name>\d+)/history/$')
	@View.add_matcher(r'^/record/(?P<name>\d+)/history/(?P<revision>.*)/', name='history/revision')
	def history(self, name=None, simple=False, revision=None):
		"""Revision/history/comment viewer"""

		if revision:
			revision = revision.replace("+", " ")

		self.init(name=name, parents=True, children=True)
		self.template = "/pages/record.history"


		users = set()
		paramdefs = set()
		for i in self.rec.get('history',[]) + self.rec.get('comments',[]):
			users.add(i[0])
		for i in self.rec.get('history', []):
			paramdefs.add(i[2])

		users = self.db.getuser(users)
		paramdefs = self.db.getparamdef(paramdefs)

		self.ctxt['users'] = users
		self.ctxt['users_d'] = emen2.util.listops.dictbykey(users, 'name')
		self.ctxt['paramdefs'] = paramdefs
		self.ctxt['paramdefs_d'] = emen2.util.listops.dictbykey(paramdefs, 'name')

		rendered = ""
		self.title = "History"
		self.set_context_item('simple', simple)
		self.set_context_item("revision", revision)
		self.set_context_item("rendered", rendered)


	@View.add_matcher("^/record/(?P<name>\d+)/email/$")
	def email(self, name=None):
		"""Main record rendering."""

		self.init(name=name)
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
				if i.iter:
					users_ref |= set(v)
				else:
					users_ref.add(v)

		users_permissions = set()
		for v in self.rec.get('permissions'):
			users_permissions |= set(v)

		users = self.db.getuser(users_ref | users_permissions, filt=True)
		for user in users:
			user.getdisplayname(lnf=True)

		self.ctxt['users'] = users


	# @View.add_matcher(r'^/record/(?P<name>\d+)/publish/$')
	# def publish(self, name=None):
	# 	self.init(name=name)
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
	# 	self.init(name=name)
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
