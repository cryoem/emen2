import os
import os.path

import emen2.util.fileops
from emen2.subsystems import view
from emen2.subsystems import routing
from emen2.subsystems import templating
from emen2.db.config import gg as g

def view_callback(pwd, pth, mtch, name, ext, failures=None):
   if pwd[0] not in sys.path:
      sys.path.append(pwd[0])
   if not hasattr(failures, 'append'): 
      failures = []
   if ext == mtch:
      filpath = os.path.join(pwd[0], name)
      data = emen2.util.fileops.openreadclose(filpath+ext)
      viewname = os.path.join(pwd[0], name).replace(pth,'')
      level = 'LOG_INIT'
      msg = ["VIEW", "LOADED:"]
      try:
         __import__(name)
      except BaseException, e:
         g.log(e)
         level = 'LOG_ERROR'
         msg[1] = "FAILED:"
         failures.append(viewname)

      msg.append(filpath+ext)
      g.log.msg(level, ' '.join(msg))


get_views = emen2.util.fileops.walk_paths('.py', view_callback)


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
	get_views(g.VIEWPATHS)



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


