# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View
###


@View.register
class Groups(View):

	@View.add_matcher(r'^/groups/$')
	def multiple(self,q=None):
		self.template="/pages/groups"
		self.title = "Wtf"
		self.title = "Group Directory"
		self.set_context_item("q","")
		groups = self.db.getgroup(self.db.getgroupnames())
		admin = self.db.checkadmin()
		self.set_context_item("admin",admin)

		if groups == None:
			self.template="/pages/page"
			self.set_context_item("content","""No groups found, or insufficient permissions to view group list.""")
			return

		self.set_context_item("groups",groups)





@View.register
class Group(View):


	@View.add_matcher(r'^/group/(?P<groupname>[\w\- ]+)/$')
	def main(self, groupname=None):
		group = self.db.getgroup(groupname)
		admin = group.isowner()
		edit = False
		self.set_context_item("admin",admin)
		self.set_context_item("edit",edit)
		self.set_context_item("new",False)
		self.title = "Group: %s"%(groupname)
		self.set_context_item("group",group)
		self.template = "/pages/group"


	@View.add_matcher(r'^/group/(?P<groupname>[\w\- ]+)/edit/$')
	def edit(self, groupname=None):
		self.main(groupname=groupname)
		self.set_context_item("edit",True)



	@View.add_matcher(r'^/group/(?P<groupname>[\w\- ]+)/new/$', r'^/groups/new/$')
	def new(self, groupname=None):


		admin = self.db.checkadmin()

		if groupname:
			group = self.db.getgroup(groupname)
		else:
			group = self.db.newgroup()

		group.name = "None"

		self.set_context_item("admin",admin)
		self.set_context_item("edit",True)
		self.title = "New Group"
		self.set_context_item("group",group)
		self.set_context_item("new",True)
		self.template = "/pages/group"
__version__ = "$Revision$".split(":")[1][:-1].strip()
