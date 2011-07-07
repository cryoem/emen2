# $Id$
import collections
import os
import os.path
import sys

import emen2.util.fileops
import emen2.web.routing
import emen2.web.templating
import emen2.web.resources.publicresource

import emen2.db.config
config = emen2.db.config.g()


default_plugins = emen2.db.config.get_filename('emen2.web', 'plugins')
class ViewLoader(object):
	routing_table = config.claim('ROUTING', {})
	redirects = config.claim('REDIRECTS', {})
	pluginpaths = config.claim('paths.PLUGINPATHS', [default_plugins, os.path.join(config.EMEN2DBHOME, 'plugins')])
	plugins = config.claim('PLUGINS',
		[dirent for dirent in os.listdir(default_plugins)
			if os.path.isdir(dirent) and dirent != 'CVS'
		]
	)

	def view_callback(self, pwd, pth, mtch, name, ext, failures=None, plugin_name=None):
		if name == '__init__': return
		modulename = '.'.join([plugin_name, 'views', name])

		if not hasattr(failures, 'append'):
			failures = []

		assert ext == mtch

		filpath = os.path.join(pwd[0], name)
		data = emen2.util.fileops.openreadclose(filpath+ext)
		viewname = os.path.join(pwd[0], name).replace(pth,'')
		level = 'DEBUG'
		msg = ["VIEW", "LOADED:"]
		try:
			__import__(modulename)
		except BaseException, e:
			config.info(e)
			level = 'ERROR'
			msg[1] = "FAILED:"
			failures.append(viewname)
			config.log.print_exception()

		msg.append(filpath+ext)
		config.log.msg(level, ' '.join(msg))


	def __init__(self):
		if 'default' not in self.plugins:
			self.plugins.insert(0,'default')
		if default_plugins not in self.pluginpaths:
			self.pluginpaths.insert(0,default_plugins)

		config.debug( self.pluginpaths )
		config.debug( self.plugins )
		self.get_views = emen2.util.fileops.walk_path('.py', self.view_callback)
		self.router = emen2.web.routing.URLRegistry()

	def load_plugins(self):
		pth = list(reversed(sys.path))

		pluginpaths = collections.defaultdict(list)
		for pluginpath in self.pluginpaths:
			if os.path.isdir(pluginpath):
				for dirent in os.listdir(pluginpath):
					dirpath = os.path.join(pluginpath, dirent)
					if os.path.isdir(dirpath):
						pluginpaths[dirent].append(dirpath)

		for plugin in self.plugins:
			plugindir = pluginpaths.pop(plugin, [])
			if plugindir != []:
				plugindir = plugindir.pop()
				config.info('Loading plugin %s from %s' % (plugin, plugindir))

				templatedir = os.path.join(plugindir, 'templates')
				if os.path.exists(templatedir):
					self.load_templates(templatedir)

				viewdir = os.path.join(plugindir, 'views')
				if os.path.exists(viewdir):
					old_syspath = sys.path[:]
					sys.path.append(os.path.dirname(plugindir))
					self.get_views(viewdir, plugin_name = plugin)
					sys.path = old_syspath

				pythondir = os.path.join(plugindir, 'python')
				if os.path.exists(pythondir):
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


	def load_templates(self, path, failures=None):
		template_loader = emen2.util.fileops.walk_path('.mako', emen2.web.templating.template_callback)
		template_loader(path, failures=failures)


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
			config.logger.interact(globals())
			self.page = 'done'
		else:
			self.page = 'fail'




__version__ = "$Revision$".split(":")[1][:-1].strip()
