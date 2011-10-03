# $Id$
from operator import itemgetter
import time

# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
import emen2.web.config
CVars = emen2.web.config.CVars
from emen2.web.view import View

import emen2.db.exceptions


@View.register
class Home(View):

	# @View.add_matcher(r'^/debug/sleep/$')
	# def debug_sleep(self):
	# 	# debug: sleep for 10 seconds
	# 	self.template = '/simple'
	# 	self.title = 'Debug'
	# 	self.ctxt['content'] = 'Sleeping...'
	# 	time.sleep(10)
	# 
	# 
	# @View.add_matcher(r'^/debug/error/$')
	# def debug_error(self):
	# 	self.template = '/simple'
	# 	self.title = 'Debug'
	# 	self.ctxt['content'] = 'Error'
	# 	raise Exception, "Test Exception"

	@View.add_matcher(r'^/$', view='Root', name='main')
	@View.add_matcher(r'^/home/$')
	def init(self):
			self.title = 'Home'
			self.template = '/pages/home'

			# Get the banner/welcome message
			banner = CVars.bookmarks.get('BANNER', 0)
			try:
				user, groups = self.db.checkcontext()
			except (emen2.db.exceptions.AuthenticationError, emen2.db.exceptions.SessionError), inst:
				user = "anonymous"
				groups = set(["anon"])
				self.set_context_item("msg",str(inst))

			if user == "anonymous":
				banner = CVars.bookmarks.get('BANNER_NOAUTH', banner)

			try:
				banner = self.db.getrecord(banner)
				render_banner = self.db.renderview(banner, viewtype="banner")
			except Exception, inst:
				banner = None
				render_banner = ""

			if user == "anonymous":
				self.template = '/pages/home.noauth'
				return

			user = self.db.getuser(user)
			admin = False

			# childtree = self.routing.execute('Map/embed', db=self.db, root=0, recurse=2, rectype=["group","project"], id="projectmap")
			ctroot = CVars.bookmarks.get("GROUPS",0)
			rn, childtree = self.db.renderchildtree(ctroot, recurse=2, rectype=["group","project"])
			recnames = {}
			recnames.update(rn)

			self.set_context_item("banner", banner)
			self.set_context_item("render_banner", render_banner)
			self.set_context_item("user",user)
			self.ctxt.update({"admin":admin, "childtree":childtree, "recnames":recnames, 'ctroot': ctroot})



__version__ = "$Revision$".split(":")[1][:-1].strip()
