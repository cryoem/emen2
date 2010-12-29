# $Id$
import os
import os.path
import sys

import emen2.util.fileops
import emen2.web.routing
import emen2.web.templating
import emen2.web.resources.publicresource

import emen2.db.config
g = emen2.db.config.g()


def view_callback(pwd, pth, mtch, name, ext, failures=None):
	if pwd[0] not in sys.path:
		sys.path.append(pwd[0])
	if not hasattr(failures, 'append'): 
		failures = []
	assert ext == mtch#:
	filpath = os.path.join(pwd[0], name)
	data = emen2.util.fileops.openreadclose(filpath+ext)
	viewname = os.path.join(pwd[0], name).replace(pth,'')
	level = 'LOG_DEBUG'
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
	router = emen2.web.routing.URLRegistry()
	for key, value in routing_table.iteritems():
		for name, regex in value.iteritems():
			# print key, name, regex
			view = router.get(key)
			if view:
				view.add_matcher(name, regex, view.get_callback('main'))


def load_views(failures=None):
	g.templates = emen2.web.templating.TemplateFactory('mako', emen2.web.templating.MakoTemplateEngine())
	#ed: deprecated -- use TEMPLATEPATHS
	r = reversed(getattr(g.paths, 'TEMPLATEDIRS', []))
	emen2.web.templating.get_templates(r, failures=failures)
	#new name
	r = reversed(getattr(g.paths, 'TEMPLATEPATHS', []))
	emen2.web.templating.get_templates(r, failures=failures)
	get_views(getattr(g.paths, 'VIEWPATHS', []))
	g.debug(getattr(g.paths, 'VIEWPATHS', []))

def load_redirects(dict_):
	for fro,v in dict_.iteritems():
		to, kwargs = v
		emen2.web.resources.publicresource.PublicView.register_redirect(fro, to, **kwargs)




def reload_views(view=None):
	reload(view)
	failures = []
	load_views(failures=failures)
	if view != None: values = [emen2.web.routing.URLRegistry.URLRegistry[view]]
	else: values = emen2.web.routing.URLRegistry.URLRegistry.values()
	for view in values:
		try:
			view = view._URL__callback.__module__
			exec 'import %s;reload(%s)' % (view,view)
		except:
			failures.append(str(view))
	return failures



class _LaunchConsole(emen2.web.view.View):
	import thread
	__metaclass__ = emen2.web.view.View.register_view
	__matcher__ = '^/__launch_console/$'
	def __init__(self, db, **kwargs):
		emen2.web.view.View.__init__(self, db=db, **kwargs)
		self.set_context_item('title', '')
		if db.checkadmin():
			g.log.interact(globals())
			self.page = 'done'
		else:
			self.page = 'fail'


__version__ = "$Revision$".split(":")[1][:-1].strip()
