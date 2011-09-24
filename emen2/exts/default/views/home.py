# $Id$
from operator import itemgetter
import time

# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View

import emen2.db.exceptions


@View.register
class Home(View):

	@View.add_matcher(r'^/sleep/$')
	def sleep(self):
		# debug: sleep for 10 seconds
		self.template = '/simple'
		self.title = 'Debug'
		self.ctxt['content'] = 'Sleeping...'
		time.sleep(10)


	@View.add_matcher(r'^/$', r'^/home/$')
	def init(self, showsubproject=0, **kwargs):
			self.update_context(args=kwargs, title="Home")
			self.set_context_item("action_login","%s/auth/login/"%(g.EMEN2WEBROOT))
			self.set_context_item("action_logout","%s/auth/logout"%(g.EMEN2WEBROOT))
			self.set_context_item("action_chpasswd","%s/auth/password/change/"%(g.EMEN2WEBROOT))
			self.set_context_item("msg",'')

			banner = g.BOOKMARKS.get('BANNER', 0)

			try:
				user, groups = self.db.checkcontext()
			except (emen2.db.exceptions.AuthenticationError, emen2.db.exceptions.SessionError), inst:
				user = "anonymous"
				groups = set(["anon"])
				self.set_context_item("msg",str(inst))


			if user == "anonymous":
				banner = g.BOOKMARKS.get('BANNER_NOAUTH', banner)

			try:
				banner = self.db.getrecord(banner)
				render_banner = self.db.renderview(banner, viewtype="banner")
			except Exception, inst:
				banner = None
				render_banner = ""


			self.set_context_item("banner", banner)
			self.set_context_item("render_banner", render_banner)

			bannermap = ''
			self.set_context_item("bannermap", bannermap)

			recnames = {}
			if user == "anonymous":
				self.template = '/pages/home.noauth'
				return


			# This will run a generic "new record" query
			# q = self.db.query(count=10, table=True)
			# self.set_context_item('q',  q)

			ctroot = g.BOOKMARKS.get("GROUPS",0)
			rn, childtree = self.db.renderchildtree(ctroot, recurse=2, rectype=["group","project"])
			recnames.update(rn)

			self.template = "/pages/home"
			self.set_context_item("msg","")
			user = self.db.getuser(user)
			self.set_context_item("user",user)


			#############################

			admin = self.db.checkreadadmin()
			if admin:
				admin_queue = {}
				for i in self.db.getuserqueue():
					admin_queue[i]=self.db.getqueueduser(i)

				self.set_context_item("admin_queue",admin_queue)

			#############################

			self.ctxt.update({"admin":admin, "childtree":childtree, "recnames":recnames, "ctroot":ctroot})



__version__ = "$Revision$".split(":")[1][:-1].strip()
