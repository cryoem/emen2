# $Id$
from emen2.web.view import View

@View.register
class Event(View):

	@View.add_matcher(r'^/event/(?P<name>.+)/$')
	def init(self, name=None):
		self.template = '/pages/event.main'
		self.name = int(name)
		self.rec = self.db.getrecord(self.name)
		allrecs = set([self.name])

		events = self.db.getchildren(self.name)
		allrecs |= events
		events = self.db.getrecord(events)
		events = filter(lambda x:x.get('date_start') or x.get('date_recurrence'), events)
		
		self.set_context_item("events",events)
		self.set_context_item("rec",self.rec)
		self.set_context_item("recnames",self.db.renderview(allrecs))
		self.set_context_item("rendered",self.db.renderview(self.rec, viewtype="mainview"))



__version__ = "$Revision$".split(":")[1][:-1].strip()
