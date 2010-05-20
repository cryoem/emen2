import os
import os.path

from emen2.web import view
from emen2.web import routing
from emen2.web import templating
from emen2.db.config import gg as g

def routes_from_g():
	routing_table = g.getattr('ROUTING', {})
	router = routing.URLRegistry()
	for key, value in routing_table.iteritems():
		for name, regex in value.iteritems():
			print key, name, regex
			view = router.get(key)
			if view:
				view.add_matcher(name, regex, view.get_callback('main'))


def load_views(failures=None):
	g.templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
	templating.get_templates(g.TEMPLATEDIRS, failures=failures)
	view.get_views(g.VIEWPATHS)



def reload_views(view=None):
	reload(view)
	failures = []
	load_views(failures=failures)
	if view != None: values = [routing.URLRegistry.URLRegistry[view]]
	else: values = routing.URLRegistry.URLRegistry.values()
	for view in values:
		try:
			view = view._URL__callback.__module__
			exec 'import %s;reload(%s)' % (view,view)
		except:
			failures.append(str(view))
	return failures




class _LaunchConsole(view.View):
	import thread
	__metaclass__ = view.View.register_view
	__matcher__ = '^/__launch_console/$'
	def __init__(self, db, **kwargs):
		view.View.__init__(self, db=db, **kwargs)
		self.set_context_item('title', 'blahb;ajb')
		if db.checkadmin():
			g.log.interact(globals())
			self.page = 'done'
		else:
			self.page = 'fail'


