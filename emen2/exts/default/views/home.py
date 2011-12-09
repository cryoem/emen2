# $Id$
from operator import itemgetter
import time

import emen2.db.exceptions
import emen2.db.config
from emen2.web.view import View



@View.register
class Home(View):

	@View.add_matcher(r'^/debug/sleep/$')
	def debug_sleep(self, t=5):
		# debug: sleep
		self.template = '/simple'
		self.title = 'Debug'
		self.ctxt['content'] = 'Sleeping...'
		time.sleep(int(t))
	
	
	@View.add_matcher(r'^/debug/error/$')
	def debug_error(self):
		self.template = '/simple'
		self.title = 'Debug'
		self.ctxt['content'] = 'Error'
		raise Exception, "Test Exception"


	@View.add_matcher(r'^/$', view='Root', name='main')
	@View.add_matcher(r'^/home/$')
	def main(self):
			self.title = 'Home'
			self.template = '/pages/home'
			bookmarks = emen2.db.config.get('bookmarks.BOOKMARKS', {})
			
			# Get the banner/welcome message
			banner = emen2.db.config.get('customization.EMEN2LOGO')

			try:
				user, groups = self.db.checkcontext()
			except (emen2.db.exceptions.AuthenticationError, emen2.db.exceptions.SessionError), inst:
				user = "anonymous"
				groups = set(["anon"])
				self.set_context_item("msg",str(inst))

			if user == "anonymous":
				banner = bookmarks.get('BANNER_NOAUTH', banner)

			try:
				banner = self.db.getrecord(banner)
				render_banner = self.db.renderview(banner, viewname="banner")
			except Exception, inst:
				banner = None
				render_banner = ""

			if user == "anonymous":
				self.template = '/pages/home.noauth'
				return

			self.ctxt['projects_map'] = self.routing.execute('Map/embed', db=self.db, root=0, mode='children', recurse=2, rectype=['group', 'project'])

			recnames = {}
			equipment = self.db.getchildren(0, rectype=['microscope'])
			r = self.db.renderview(equipment)
			recnames.update(r)
			self.ctxt['equipment'] = equipment
			self.ctxt['banner'] = banner
			self.ctxt['render_banner'] = render_banner
			self.ctxt['recnames'] = recnames



__version__ = "$Revision$".split(":")[1][:-1].strip()
