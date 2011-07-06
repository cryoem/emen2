# $Id$
# Standard View imports
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View
###


@View.register
class Help(View):

	@View.add_matcher(r'^/help/$')
	def init(self, **kwargs):
		self.title = "Help"
		self.template = "/pages/help"
		
		
__version__ = "$Revision$".split(":")[1][:-1].strip()
