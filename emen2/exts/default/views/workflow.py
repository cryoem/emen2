# $Id$
import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View

class Workflow(View):
	__metaclass__ = View.register_view
	__matcher__ = r'^/workflow/$'

	def __init__(self,*_, **__):
		self.template = "/pages/page"
		self.title = "User Queries &amp; Workflows"
		self.set_context_item("content","Workflow:<br /><br />")

		wf = self.db.getworkflow()
		self.set_context_item("content", self.ctxt["content"] + str(wf))


__version__ = "$Revision$".split(":")[1][:-1].strip()
