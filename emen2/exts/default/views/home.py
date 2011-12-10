# $Id$
from operator import itemgetter
import time

import emen2.db.exceptions
import emen2.db.config
from emen2.web.view import View



@View.register
class Home(View):

	@View.add_matcher(r'^/$', view='Root', name='main')
	@View.add_matcher(r'^/home/$')
	def main(self):
		self.title = 'Home'
		self.template = '/pages/home'
		
		# Get the banner/welcome message
		bookmarks = emen2.db.config.get('bookmarks.BOOKMARKS', {})
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

		


__version__ = "$Revision$".split(":")[1][:-1].strip()
