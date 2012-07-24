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
	
	def common(self, name=None, children=True, parents=True, viewname="defaultview", **kwargs):
		"""Main record rendering."""
		# Get record..
		self.rec = self.db.record.get(name, filt=False)
		recnames = self.db.record.render([self.rec])

		# Look for any recorddef-specific template.
		template = '/record/rectypes/%s'%self.rec.rectype
		try:
			emen2.db.config.templates.get_template(template)
		except:
			template = '/record/rectypes/root'
		self.template = template

		# Render main view
		rendered = self.db.record.render(self.rec, viewname=viewname, edit=self.rec.writable())

		# Some warnings/alerts
		if self.rec.get('deleted'):
			self.ctxt['ERRORS'].append('Hidden record')
		if 'publish' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Record marked as published data')
		if 'authenticated' in self.rec.get('groups',[]):
			self.ctxt['NOTIFY'].append('Any authenticated user can read this record')
		if 'anon' in self.rec.get('groups', []):
			self.ctxt['NOTIFY'].append('Anyone may access this record anonymously')

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
		users = self.db.user.get([self.rec.get('creator'), self.rec.get('modifyuser')])

		# Parent map
		parentmap = self.routing.execute('Tree/embed', db=self.db, root=self.rec.name, mode='parents', recurse=-1, expandable=False)

		# Children
		children = self.db.record.get(self.rec.children)

		pages = {}

		# Update context
		self.ctxt.update(
			tab = "main",
			rec = self.rec,
			children = children,
			recdef = self.recdef,
			title = recnames.get(self.rec.name, self.rec.name),
			users = users,
			recnames = recnames,
			parentmap = parentmap,
			edit = False,
			create = self.db.auth.check.create(),
			rendered = rendered,
			viewname = viewname,
			table = ""
		)	
		
	
	@View.add_matcher(r'^/record/(?P<name>\w+)/$')
	def main(self, name=None, sibling=None, viewname='defaultview', **kwargs):
		self.common(name=name, viewname=viewname)
		
		# Find siblings
		if sibling == None:
			sibling = self.rec.name
		siblings = self.db.rel.siblings(sibling, rectype=self.rec.rectype)

		self.ctxt.update(
			viewname = viewname,
			sibling = sibling,
			siblings = sorted(siblings)
		)


	@View.add_matcher(r'^/record/(?P<name>\w+)/edit/$', write=True)
	def edit(self, name=None, _location=None, **kwargs):
		self.main(name=name)
		# Edit page and requests
		if self.request_method not in ['post', 'put']:
			# Show the form and return
			self.ctxt["edit"] = True
			return

		# Get the record
		if not self.rec.writable():
			raise emen2.db.exceptions.SecurityError, "No write permission for record %s"%self.rec.name

		# Update the record
		if kwargs:
			self.rec.update(kwargs)
			self.rec = self.db.record.put(self.rec)

		for f in self.request_files:
			param = f.get('param', 'file_binary')
			bdo = self.db.binary.put(f)
			self.db.binary.addreference(self.rec.name, param, bdo.name)

		# Redirect
		self.redirect(_location or self.routing.reverse('Record/main', name=self.rec.name))


	@View.add_matcher(r'^/record/(?P<name>\w+)/edit/attachments/$', name='edit/attachments', write=True)
	def edit_attachments(self, name=None, **kwargs):
		self.edit(name=name, **kwargs)
		self.redirect(self.routing.reverse('Record/main', name=name, anchor='attachments'))


	@View.add_matcher(r'^/record/(?P<name>\w+)/edit/relationships/$', name='edit/relationships', write=True)
	def edit_relationships(self, name=None, parents=None, children=None):
		# ian: todo: Check orphans, show orphan confirmation page
		self.rec = self.db.record.get(name)
		parents = set(map(unicode,listops.check_iterable(parents)))
		children = set(map(unicode,listops.check_iterable(children)))
		if self.request_method == 'post':
			self.rec.parents = parents
			self.rec.children = children
			self.rec = self.db.record.put(self.rec)

		self.redirect('%s/record/%s/#relationships'%(self.ctxt['EMEN2WEBROOT'], self.rec.name))


	@View.add_matcher(r'^/record/(?P<name>\w+)/edit/permissions/$', name='edit/permissions', write=True)
	def edit_permissions(self, name=None, permissions=None, groups=None, action=None, filt=True):
		self.rec = self.db.record.get(name)
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
				self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt)

			elif action == 'remove':
				self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, removeusers=users, removegroups=groups, filt=filt)

			elif action == 'overwrite':
				self.db.record.setpermissionscompat(names=self.rec.name, recurse=-1, addumask=permissions, addgroups=groups, filt=filt, overwrite_users=True, overwrite_groups=True)

			else:
				self.rec['groups'] = groups
				self.rec['permissions'] = permissions
				self.rec = self.db.record.put(self.rec)

		self.redirect('%s/record/%s/#permissions'%(self.ctxt['EMEN2WEBROOT'], self.rec.name))


	@View.add_matcher(r'^/record/(?P<name>\w+)/new/(?P<rectype>\w+)/$', write=True)
	def new(self, name=None, rectype=None, _location=None, **kwargs): 
		"""Create a new record."""
		self.common(name=name)
		viewname = 'mainview'
		inherit = [self.rec.name]
		newrec = self.db.record.new(rectype, inherit=inherit)
		
		if self.request_method in ['post', 'put']:
			# Save the new record
			newrec.update(kwargs)
			newrec = self.db.record.put(newrec)

			for f in self.request_files:
				param = f.get('param', 'file_binary')
				bdo = self.db.binary.put(f)
				self.db.binary.addreference(newrec.name, param, bdo.name)

			# Redirect
			self.redirect(_location or self.routing.reverse('Record/main', name=newrec.name), content=newrec.name)
			return
			
		self.template = '/record/record.new'
		recdef = self.db.recorddef.get(newrec.rectype)
		rendered = self.db.record.render(newrec, edit=True, viewname=viewname)
		self.title = 'New %s'%(recdef.desc_short)
		self.ctxt.update(
			newrec = newrec,
			viewname = viewname,
			rendered = rendered
		)
		return




	# @View.add_matcher('^/record/(?P<name>\w+)/query/$')
	# def query(self, name=None, childtype=None):
	



	@View.add_matcher('^/record/(?P<name>\w+)/children/(?P<childtype>\w+)/$')
	def children(self, name=None, childtype=None):
		"""Main record rendering."""
		self.common(name=name)

		# Child table
		c = [['children', '==', self.rec.name], ['rectype', '==', childtype]]
		query = self.routing.execute('Query/embed', db=self.db, c=c, parent=self.rec.name, rectype=childtype)

		# ian: awful hack
		query.request_location = self.request_location
		query.ctxt['REQUEST_LOCATION'] = self.request_location

		# Update context
		self.ctxt['table'] = query
		self.ctxt['tab'] = 'children-%s'%childtype
		self.ctxt['childtype'] = childtype
		

	@View.add_matcher("^/record/(?P<name>\w+)/hide/$", write=True)
	def hide(self, name=None, commit=False, childaction=None):
		"""Main record rendering."""
		self.common(name=name)
		self.template = "/record/record.hide"
		self.title = "Hide record"

		orphans = self.db.record.findorphans([self.rec.name])
		children = self.db.rel.children(self.rec.name, recurse=-1)

		if self.request_method == 'post' and commit:
			self.db.record.hide(self.rec.name, childaction=childaction)

		# Update context
		self.ctxt['commit'] = commit
		self.ctxt['orphans'] = orphans


	@View.add_matcher(r'^/record/(?P<name>\w+)/history/$')
	@View.add_matcher(r'^/record/(?P<name>\w+)/history/(?P<revision>.*)/', name='history/revision')
	def history(self, name=None, simple=False, revision=None):
		"""Revision/history/comment viewer"""
		self.common(name=name, parents=True, children=True)
		self.template = "/record/record.history"
		self.title = "History"

		if revision:
			revision = revision.replace("+", " ")

		users = set()
		paramdefs = set()
		users.add(self.rec.get('creator'))
		users.add(self.rec.get('modifyuser'))
		for i in self.rec.get('history',[]) + self.rec.get('comments',[]):
			users.add(i[0])
		for i in self.rec.get('history', []):
			paramdefs.add(i[2])

		users = self.db.user.get(users)
		paramdefs = self.db.paramdef.get(paramdefs)

		# Update context
		self.ctxt['users'] = users
		self.ctxt['users_d'] = emen2.util.listops.dictbykey(users, 'name') # do this in template
		self.ctxt['paramdefs'] = paramdefs
		self.ctxt['paramdefs_d'] = emen2.util.listops.dictbykey(paramdefs, 'name') # do this in template
		self.ctxt['simple'] = simple
		self.ctxt['revision'] = revision


	@View.add_matcher("^/record/(?P<name>\w+)/email/$")
	def email(self, name=None):
		"""Email referenced users."""
		self.common(name=name)
		self.template = "/record/record.email"
		self.title = "Email users"

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


	@View.add_matcher(r'^/record/(?P<name>\w+)/publish/$', write=True)
	def publish(self, name=None, state=None):
		self.common(name=name)
		self.template = '/record/record.publish'
		self.title = 'Managed published records'

		names = self.db.rel.children(self.rec.name, recurse=-1)
		names.add(self.rec.name)

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
		
		childmap = self.routing.execute('Tree/embed', db=self.db, root=self.rec.name, mode='children', recurse=-1, collapse_rectype='grid_imaging')
		self.set_context_item("childmap", childmap)
		self.set_context_item("published", published)




@View.register
class Records(View):
	
	@View.add_matcher(r"^/records/$")
	def main(self, root="0", removerels=None, addrels=None, **kwargs):
		kwargs['recurse'] = kwargs.get('recurse', 2)
		childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="record", root=root, recurse=kwargs.get('recurse'), id='sitemap')
		self.template = '/pages/records.tree'
		self.title = 'Record relationships'
		self.ctxt['root'] = root
		self.ctxt['childmap'] = childmap
		self.ctxt['create'] = self.db.auth.check.create()


	@View.add_matcher(r"^/records/edit/relationships/$", write=True)
	def edit_relationships(self, root="0", removerels=None, addrels=None, **kwargs):
		self.title = 'Edit record relationships'

		if self.request_method == 'post' and removerels and addrels:
			self.db.rel.relink(removerels=removerels, addrels=addrels)
			self.redirect('%s/records/edit/relationships/?root=%s'%(self.ctxt['EMEN2WEBROOT'], root), title=self.title, content="Your changes were saved.", auto=True)
			return

		kwargs['recurse'] = kwargs.get('recurse', 2)
		childmap = self.routing.execute('Tree/embed', db=self.db, mode="children", keytype="record", root=root, recurse=kwargs.get('recurse'), id='sitemap')
		self.template = '/pages/records.tree.edit'
		self.ctxt['root'] = root
		self.ctxt['childmap'] = childmap
		self.ctxt['create'] = self.db.auth.check.create()


	@View.add_matcher("^/records/edit/$", write=True)
	def edit(self, *args, **kwargs):
		location = kwargs.pop('_location', None)
		comments = kwargs.pop('comments', '')

		if self.request_method == 'post':
			for k,v in kwargs.items():
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
