# $Id$
import urllib
import time
import collections

import emen2.db.exceptions
import emen2.util.listops as listops
import emen2.web.responsecodes
from emen2.web.view import View


class RecordNotFoundError(emen2.web.responsecodes.NotFoundError):
	title = 'Record not Found'
	msg = 'Record %s not found'




@View.register
class Record(View):
	
	def initr(self, name=None, children=True, parents=True, **kwargs):
		"""Main record rendering."""

		# Get record..
		self.rec = self.db.record.get(name, filt=False)
		self.name = self.rec.name
		recnames = {}
		recnames = self.db.record.render([self.rec])

		# Find if this record is in the user's bookmarks
		bookmarks = []
		user = None
		try:
			t = time.time()
			user = self.ctxt['USER']
			brec = self.db.record.get(sorted(self.db.rel.children(user.record, rectype='bookmarks')))
			if brec:
				bookmarks = brec[-1].get('bookmarks', [])
		except Exception, e:
			pass
		self.ctxt['bookmarks'] = bookmarks

		# Get RecordDef
		self.recdef = self.db.recorddef.get(self.rec.rectype)

		# User display names
		# These are generally displayed: creator, modifyuser, comments.
		users = set([self.rec.get('creator'), self.rec.get('modifyuser')])
		users = self.db.user.get(users)

		# Some warnings/alerts
		if self.rec.get('deleted'):
			self.ctxt['ERRORS'].append('Hidden record')
		if 'publish' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Record marked as published data')
		if 'authenticated' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Any authenticated user can read this record')
		if 'anon' in self.rec.get('groups', []):
			self.ctxt['NOTIFY'].append('Anyone may access this record anonymously')

		# Parent map
		parentmap = self.routing.execute('Tree/embed', db=self.db, root=self.name, mode='parents', recurse=-1, expandable=False)

		# Children
		pages = collections.OrderedDict()
		pages.uris = {}
		pages['main'] = recnames.get(self.rec.name, self.rec.name)
		pages.uris['main'] = self.routing.reverse('Record/main', name=self.rec.name)
		for k,v in self.db.record.groupbyrectype(self.rec.children).items():
			pages[k] = "%s (%s)"%(k,len(v))
			pages.uris[k] = self.routing.reverse('Record/children', name=self.rec.name, childtype=k)

		# Update context
		self.ctxt.update(
			rec = self.rec,
			recs = {str(self.name):self.rec},
			recdef = self.recdef,
			title = "Record: %s: %s (%s)"%(self.rec.rectype, recnames.get(self.rec.name), self.name),
			pages = pages,
			users = users,
			recnames = recnames,
			parentmap = parentmap,
			viewname = "defaultview",
			edit = False,
			key = self.name,
			keytype = "record",
			create = self.db.auth.check.create()
		)	
	
	
	@View.add_matcher(r'^/record/(?P<name>\w+)/$')
	def main(self, name=None, sibling=None, viewname='defaultview', **kwargs):
		self.initr(name=name)
		
		# Look for any recorddef-specific template.
		template = '/record/rectypes/%s'%self.rec.rectype
		try:
			emen2.db.config.templates.get_template(template)
		except:
			template = '/record/rectypes/root'
		self.template = template
		
		# Find siblings
		if sibling == None:
			sibling = self.rec.name
		siblings = self.db.rel.siblings(sibling, rectype=self.rec.rectype)

		# Render main view
		rendered = self.db.record.render(self.rec, viewname=viewname, edit=self.rec.writable())
			
		self.ctxt.update(
			viewname = viewname,
			rendered = rendered,
			sibling = sibling,
			siblings = sorted(siblings)
		)


	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/$', write=True)
	def edit(self, name=None, _location=None, **kwargs):
		# Edit page and requests
		if self.request_method not in ['post', 'put']:
			# Show the form and return
			self.main(name=name)
			self.ctxt["edit"] = True
			return

		# Get the record
		rec = self.db.record.get(name, filt=False)
		if not rec.writable():
			raise emen2.db.exceptions.SecurityError, "No write permission for record %s"%rec.name

		# Update the record
		if kwargs:
			rec.update(kwargs)
			self.db.record.put(rec)

		for f in self.request_files:
			param = f.get('param', 'file_binary')
			bdo = self.db.binary.put(f)
			self.db.binary.addreference(rec.name, param, bdo.name)

		# Redirect
		if _location:
			self.redirect(_location)
		else:
			self.redirect(self.routing.reverse('Record/main', name=name))


	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/attachments/$', name='edit/attachments', write=True)
	def edit_attachments(self, name=None, **kwargs):
		self.edit(name=name, **kwargs)
		self.redirect(self.routing.reverse('Record/main', name=name, anchor='attachments'))


	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/relationships/$', name='edit/relationships', write=True)
	def edit_relationships(self, name=None, parents=None, children=None):
		# ian: todo: Check orphans, show orphan confirmation page
		parents = set(map(unicode,listops.check_iterable(parents)))
		children = set(map(unicode,listops.check_iterable(children)))
		if self.request_method == 'post':
			rec = self.db.record.get(name, filt=False)
			rec.parents = parents
			rec.children = children
			rec = self.db.record.put(rec)

		self.template = '/redirect'
		self.headers['Location'] = '%s/record/%s/#relationships'%(self.ctxt['EMEN2WEBROOT'], name)


	@View.add_matcher(r'^/record/(?P<name>\d+)/edit/permissions/$', name='edit/permissions', write=True)
	def edit_permissions(self, name=None, permissions=None, groups=None, action=None, filt=True):
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
				self.db.record.setpermissionscompat(names=name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt)

			elif action == 'remove':
				self.db.record.setpermissionscompat(names=name, recurse=-1, removeusers=users, removegroups=groups, filt=filt)

			elif action == 'overwrite':
				self.db.record.setpermissionscompat(names=name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt, overwrite_users=True, overwrite_groups=True)

			else:
				rec = self.db.record.get(name, filt=False)
				rec['groups'] = groups
				rec['permissions'] = permissions
				rec = self.db.record.put(rec)

		self.template = '/redirect'
		self.headers['Location'] = '%s/record/%s/#permissions'%(self.ctxt['EMEN2WEBROOT'], name)



	@View.add_matcher(r'^/record/(?P<name>\d+)/new/(?P<rectype>\w+)/$', write=True)
	def new(self, name=None, rectype=None, _location=None, **kwargs): 
		viewname = 'mainview'
		inherit = [name]

		newrec = self.db.record.new(rectype, inherit=inherit)
		
		if self.request_method not in ['post', 'put']:
			# Show the form
			self.template = '/record/record.new'
			recnames = self.db.record.render(inherit)
			parentrec = self.db.record.get(name)
			parentmap = self.routing.execute('Tree/embed', db=self.db, root=name, mode='parents', recurse=-1)
			recdef = self.db.recorddef.get(newrec.rectype)
			rendered = self.db.record.render(newrec, edit=True, viewname=viewname)
			self.title = 'New %s (%s)'%(recdef.desc_short, recdef.name)
			self.ctxt.update(
				parentmap = parentmap,
				recnames = recnames,
				rec = parentrec,
				recdef = recdef,
				newrec = newrec,
				viewname = viewname,
				rendered = rendered
			)
			return

		# Save the new record
		newrec.update(kwargs)
		newrec = self.db.record.put(newrec)

		for f in self.request_files:
			param = f.get('param', 'file_binary')
			bdo = self.db.binary.put(f)
			self.db.binary.addreference(newrec.name, param, bdo.name)



		# Redirect
		if _location:
			self.redirect(_location)
		else:
			self.redirect(self.routing.reverse('Record/main', name=newrec.name), content=newrec.name)



	@View.add_matcher('^/record/(?P<name>\d+)/children/(?P<childtype>\w+)/$')
	def children(self, name=None, childtype=None):
		"""Main record rendering."""
		self.initr(name=name)
		self.template = "/record/record.table"

		c = [['children', '==', name], ['rectype', '==', childtype]]
		query = self.routing.execute('Query/embed', db=self.db, c=c, parent=name, rectype=childtype)

		# ian: awful hack
		query.request_location = self.request_location
		query.ctxt['REQUEST_LOCATION'] = self.request_location

		self.ctxt['table'] = query
		self.ctxt['q'] = {}
		self.ctxt["pages"].active = childtype


	@View.add_matcher("^/record/(?P<name>\d+)/hide/$", write=True)
	def hide(self, commit=False, name=None, childaction=None):
		"""Main record rendering."""

		self.initr(name=name)
		self.template = "/record/record.hide"
		self.title = "Hide record"

		orphans = self.db.record.findorphans([self.name])
		recnames = {} #self.db.record.render([self.name])
		children = self.db.rel.children(self.name, recurse=-1)

		if commit:
			self.db.record.hide(self.name, childaction=childaction)

		self.ctxt['name'] = name
		self.ctxt['children'] = children
		self.ctxt['commit'] = commit
		self.ctxt['orphans'] = orphans
		self.ctxt['recnames'] = recnames


	@View.add_matcher(r'^/record/(?P<name>\d+)/history/$')
	@View.add_matcher(r'^/record/(?P<name>\d+)/history/(?P<revision>.*)/', name='history/revision')
	def history(self, name=None, simple=False, revision=None):
		"""Revision/history/comment viewer"""

		if revision:
			revision = revision.replace("+", " ")

		self.initr(name=name, parents=True, children=True)
		self.template = "/record/record.history"


		users = set()
		paramdefs = set()
		for i in self.rec.get('history',[]) + self.rec.get('comments',[]):
			users.add(i[0])
		for i in self.rec.get('history', []):
			paramdefs.add(i[2])

		users = self.db.user.get(users)
		paramdefs = self.db.paramdef.get(paramdefs)

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

		self.initr(name=name)
		self.template = "/record/record.email"
		self.title = "Users"

		# ian: todo: replace!!
		pds = self.db.paramdef.find(record=self.rec.keys())
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

		users = self.db.user.get(users_ref | users_permissions)
		for user in users:
			user.getdisplayname(lnf=True)

		self.ctxt['users'] = users


	@View.add_matcher(r'^/record/(?P<name>\d+)/publish/$', write=True)
	def publish(self, name=None, state=None):
		self.initr(name=name)
		self.template = '/record/record.publish'
		self.title = 'Publish Records'
	
		# published = self.db.query([['children', '==', '%s'%self.name], ['groups', 'contains', 'publish']])['names']	
		names = self.db.rel.children(self.name, recurse=-1)
		names.add(self.name)

		published = set()
		state = set(map(unicode, state or [])) & names

		recs = self.db.record.get(names)
		
		for rec in recs:
			if 'publish' in rec.groups:
				published.add(rec.name)
		
		# Convert to dict
		recs_d = emen2.util.listops.dictbykey(recs)

		if self.request_method == 'post':
			add = state - published
			remove = published - state
			commit = []
			print "Adding:", len(add)
			print "Removing:", len(remove)
			
			for i in remove:
				recs_d[i].removegroup('publish')
				commit.append(recs_d[i])
			for i in add:
				recs_d[i].addgroup('publish')
				commit.append(recs_d[i])
				
			self.db.record.put(commit)

			# Update the published list
			recs = self.db.record.get(names)
			published = set()
			for rec in recs:
				if 'publish' in rec.groups:
					published.add(rec.name)
			
			
		
		childmap = self.routing.execute('Tree/embed', db=self.db, root=self.name, mode='children', recurse=-1, collapse_rectype='grid_imaging')
	
		self.set_context_item("childmap", childmap)
		self.set_context_item("published", published)




	# @View.add_matcher(r'^/record/(?P<name>\d+)/boxer/$')
	# def boxer(self, name=None):
	# 	self.initr(name=name)
	# 	self.template = '/pages/boxer'
	# 	self.title = "web.boxer (EXPERIMENTAL!)"
	#
	# 	boxrecords = self.db.rel.children(self.rec.name, rectype="box")
	# 	bdo = self.rec.get('file_binary_image')
	# 	bdo = self.db.binary.get(bdo)
	# 	if not bdo:
	# 		self.error("No ccd frames found! Cannot start web.boxer.")
	# 		return
	#
	# 	self.set_context_item("bdo",bdo)





@View.register
class Records(View):

	@View.add_matcher("^/records/edit/$", write=True)
	def edit(self, *args, **kwargs):
		location = kwargs.pop('_location', None)
		comments = kwargs.pop('comments', '')

		if self.request_method == 'post':
			for k,v in kwargs.items():
				# print "Record/Values:", k, v
				v['name'] = k

			recs = self.db.record.put(kwargs.values())
			if comments:
				for rec in recs:
					rec.addcomment(comments)
				self.db.record.put(recs)

			if location:
				self.redirect(location)
				return

			self.template = '/simple'
			self.ctxt['content'] = "Saved %s records"%(len(recs))







__version__ = "$Revision$".split(":")[1][:-1].strip()
