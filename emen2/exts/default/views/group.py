# $Id$
import time

from emen2.web.view import View


@View.register
class Groups(View):

	@View.add_matcher(r'^/groups/$')
	def main(self,q=None):
		self.template="/pages/groups"
		self.title = "Group directory"
		self.set_context_item("q","")
		groupnames = self.db.getgroupnames()
		groups = self.db.getgroup(groupnames)
		admin = self.db.checkadmin()
		self.set_context_item("admin",admin)

		if groups == None:
			self.template="/simple"
			self.set_context_item("content","""No groups found, or insufficient permissions to view group list.""")
			return
		
		self.ctxt['groupnames'] = groupnames
		self.ctxt['groups'] = groups



@View.register
class Group(View):
	
	@View.add_matcher(r'^/group/(?P<name>[\w\- ]+)/$')
	def main(self, name=None):
		group = self.db.getgroup(name)
		self.title = "Group: %s"%(group.displayname)
		self.template = "/pages/group"
		self.ctxt['group'] = group
		self.ctxt['new'] = False
		self.ctxt['edit'] = False


	@View.add_matcher(r'^/group/(?P<name>[\w\- ]+)/edit/$')
	def edit(self, name=None, **kwargs):
		group = self.db.getgroup(name)
		self.title = "Group: %s"%(group.displayname)
		self.template = "/pages/group"
		self.ctxt['group'] = group
		self.ctxt['new'] = False
		self.ctxt['edit'] = True

		if self.request_method != 'post':
			return

		group.update(kwargs)
		group = self.db.putgroup(group)
		self.ctxt['group'] = group
		self.redirect('/group/%s/'%group.name)
		

	# @View.add_matcher(r'^/group/(?P<name>[\w\- ]+)/new/$')
	@View.add_matcher(r'^/groups/new/$')
	def new(self, name=None, **kwargs):
		# We have to supply a group name.. just use a random string.
		name = name or 'newgroup%s'%int(time.time())		
		group = self.db.newgroup(name)		
		self.ctxt['group'] = group
		self.ctxt['new'] = True
		self.ctxt['edit'] = True
		self.title = "New group"
		self.template = "/pages/group"

		if self.request_method != 'post':
			return
			
		group.update(kwargs)
		group = self.db.putgroup(group)
		self.ctxt['group'] = group
		self.redirect('/group/%s/'%group.name)
		
		

		
__version__ = "$Revision$".split(":")[1][:-1].strip()
