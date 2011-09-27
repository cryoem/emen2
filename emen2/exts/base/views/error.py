# $Id$
import urlparse

# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View
###

@View.register
class Error(View):
	@View.add_matcher('/error/')
	@View.provides('error_handler')
	def init(self, errmsg='', location='/', **kwargs):
		self.template = '/errors/error'
		self.title = 'Error'
		self.set_context_item("errmsg", errmsg)
		self.set_context_item('location', location)
		
__version__ = "$Revision$".split(":")[1][:-1].strip()
