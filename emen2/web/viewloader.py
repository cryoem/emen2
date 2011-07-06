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


class ViewLoader(object):
	templates = g.claim('templates')
	templatepaths = g.claim('paths.TEMPLATEPATHS', [])
	viewpaths = g.claim('paths.VIEWPATHS', [])
	routing_table = g.claim('ROUTING', {})
	redirects = g.claim('REDIRECTS', {})
	plugindir = g.claim('paths.PLUGINDIR', os.path.join(g.EMEN2DBHOME, 'plugins'))
	plugins = g.claim('PLUGINS', [])

	def view_callback(self, pwd, pth, mtch, name, ext, failures=None):
		if pwd[0] not in sys.path:
			sys.path.append(pwd[0])
		if not hasattr(failures, 'append'):
			failures = []
		assert ext == mtch#:
		filpath = os.path.join(pwd[0], name)
		data = emen2.util.fileops.openreadclose(filpath+ext)
		viewname = os.path.join(pwd[0], name).replace(pth,'')
		level = 'DEBUG'
		msg = ["VIEW", "LOADED:"]
		try:
			__import__(name)
		except BaseException, e:
			g.info(e)
			level = 'ERROR'
			msg[1] = "FAILED:"
			failures.append(viewname)
			g.log.print_exception()

		msg.append(filpath+ext)
		g.log.msg(level, ' '.join(msg))


	def __init__(self):
		self.get_views = emen2.util.fileops.walk_paths('.py', self.view_callback)
		self.router = emen2.web.routing.URLRegistry()

	def load_plugins(self):
		pth = list(reversed(sys.path))

		print self.plugindir
		print os.path.isdir(self.plugindir)
		if not os.path.isdir(self.plugindir):
			return False

		for dir_ in reversed(self.plugins):
			dir_ = os.path.join(self.plugindir, dir_)
			g.debug ('dir_', dir_)
			if os.path.isdir(dir_):
				templatedir = os.path.join(dir_, 'templates')
				viewdir = os.path.join(dir_, 'views')
				pythondir = os.path.join(dir_, 'python')
				if os.path.exists(templatedir):
					g.debug ('templatedir', templatedir)
					self.templatepaths.insert(-1,templatedir)
				if os.path.exists(viewdir):
					g.debug ('viewdir', viewdir)
					self.viewpaths.insert(-1,viewdir)
				if os.path.exists(pythondir):
					g.debug ('pythondir', pythondir)
					pth.insert(-1,pythondir)

		# so that plugins cannot override built-in modules
		sys.path = list(reversed(pth))
		return True


	def routes_from_g(self):
		for key, value in self.routing_table.iteritems():
			for name, regex in value.iteritems():
				view = self.router.get(key)
				if view:
					view.add_matcher(name, regex, view.get_callback('main'))


	def load_templates(self, failures=None):
		print 'templatepaths', list(self.templatepaths)
		r = reversed(self.templatepaths)
		emen2.web.templating.get_templates(r, failures=failures)


	def load_views(self, failures=None):
		self.get_views(self.viewpaths)



	def load_redirects(self):
		for fro,v in self.redirects.iteritems():
			to, kwargs = v
			emen2.web.resources.publicresource.PublicView.register_redirect(fro, to, **kwargs)



	def reload_views(self, view=None):
		reload(view)
		failures = []
		self.load_templates(failures=failures)
		self.load_views(failures=failures)
		if view != None: values = [emen2.web.routing.URLRegistry.URLRegistry[view]]
		else: values = emen2.web.routing.URLRegistry.URLRegistry.values()
		for view in values:
			try:
				view = view._callback.__module__
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
			g.logger.interact(globals())
			self.page = 'done'
		else:
			self.page = 'fail'




__version__ = "$Revision$".split(":")[1][:-1].strip()
