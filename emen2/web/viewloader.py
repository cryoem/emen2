# $Id$
import collections
import os
import os.path
import sys

import emen2.util.fileops
import emen2.web.routing
import emen2.web.templating
import emen2.web.resources.publicresource
import emen2.web.view

import emen2.db.config
config = emen2.db.config.g()

class ViewLoader(object):
	routing_table = config.claim('ROUTING', {})
	redirects = config.claim('REDIRECTS', {})
	extensionpaths = config.claim('paths.EXTPATHS')
	extensions = config.claim('EXTS', ['default'])
	#, [dirent for dirent in os.listdir(default_extensions) if os.path.isdir(dirent) and dirent != 'CVS' ]

	def view_callback(self, pwd, pth, mtch, name, ext, failures=None, extension_name=None):
		if name == '__init__':
			return
		modulename = '.'.join([extension_name, 'views', name])

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
		#config.debug(self.extensionpaths)
		#config.debug(self.extensions)
		if 'default' not in self.extensions:
			self.extensions.insert(0,'default')
		self.get_views = emen2.util.fileops.walk_path('.py', self.view_callback)
		self.router = emen2.web.routing.URLRegistry()


	def load_extensions(self):
		# Load exts
		for ext in self.extensions:
			self.load_extension(ext)
		return True


	def load_extension(self, ext):
		# We'll be adding the extension paths with a low priority..
		pth = list(reversed(sys.path))

		# Find the path to the extension
		path, name = os.path.split(ext)
		# Absolute paths are loaded directly
		if path:
			paths = filter(os.path.isdir, [ext])
		else:
			# Search g.EXTPATHS for a directory matching the ext name
			paths = []
			for p in filter(os.path.isdir, self.extensionpaths):
				for sp in os.listdir(p):
					if os.path.isdir(os.path.join(p, sp)) and ext == sp:
						paths.append(os.path.join(p, sp))

		if not paths:
			config.info('Couldn\'t find extension %s'%ext)
			return
			# continue

		# If a suitable ext was found, load..
		path = paths.pop()
		config.info('Loading extension %s: %s' % (name, path))

		# ...load templates
		templatedir = os.path.join(path, 'templates')
		if os.path.exists(templatedir):
			self.load_templates(templatedir)

		# ...load views
		viewdir = os.path.join(path, 'views')
		if os.path.exists(viewdir):
			old_syspath = sys.path[:]
			sys.path.append(os.path.dirname(path))
			self.get_views(viewdir, extension_name=name)
			sys.path = old_syspath

		# ...add ext path to the python module search
		pythondir = os.path.join(path, 'python')
		if os.path.exists(pythondir):
			pth.insert(-1,pythondir)		

		# Restore the original sys.path
		sys.path = list(reversed(pth))



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
