# $Id$
import urllib


import emen2.db.config
g = emen2.db.config.g()
from emen2.web.view import View




@View.register
class Event(View):

	@View.add_matcher(r'^/event/(?P<name>.+)/$')
	def event(self, name=None):
		self.template = '/pages/event.main'

		self.name = int(name)
		self.rec = self.db.getrecord(self.name)
		allrecs = set([self.name])

		events = self.db.getchildren(self.name)
		allrecs |= events
		events = self.db.getrecord(events)
		events = filter(lambda x:x.get('date_start') and x.get('date_end'), events)


		self.set_context_item("events",events)
		self.set_context_item("rec",self.rec)
		self.set_context_item("recnames",self.db.renderview(allrecs))
		self.set_context_item("rendered",self.db.renderview(self.rec, viewtype="mainview"))
		self.set_context_item("TIMESTR",g.TIMESTR)



__version__ = "$Revision$".split(":")[1][:-1].strip()
