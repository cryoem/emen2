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


default_extensions = emen2.db.config.get_filename('emen2.web', 'extensions')
class ViewLoader(object):
	routing_table = config.claim('ROUTING', {})
	redirects = config.claim('REDIRECTS', {})
	extensionpaths = lambda _: config.claim('paths.EXTENSIONPATHS')
	extensions = config.claim('EXTENSIONS',
		[dirent for dirent in os.listdir(default_extensions)
			if os.path.isdir(dirent) and dirent != 'CVS'
		]
	)

	def view_callback(self, pwd, pth, mtch, name, ext, failures=None, extension_name=None):
		if name == '__init__': return
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

		if 'default' not in self.extensions:
			self.extensions.insert(0,'default')
		#self.extensionpaths.append(os.path.join(config.EMEN2DBHOME, 'extensions'))
		if default_extensions not in self.extensionpaths:
			self.extensionpaths.insert(0,default_extensions)

		# ian: temp hack..
		self.extensions.append('Char')
		self.extensionpaths.append('/Volumes/Home/irees/Dropbox')
		print "--"
		print self.extensions
		print self.extensionpaths

		config.debug( self.extensionpaths )
		config.debug( self.extensions )
		self.get_views = emen2.util.fileops.walk_path('.py', self.view_callback)
		self.router = emen2.web.routing.URLRegistry()

	def load_extensions(self):
		pth = list(reversed(sys.path))

		extensionpaths = collections.defaultdict(list)
		for extensionpath in self.extensionpaths:
			if os.path.isdir(extensionpath):
				for dirent in os.listdir(extensionpath):
					dirpath = os.path.join(extensionpath, dirent)
					if os.path.isdir(dirpath):
						extensionpaths[dirent].append(dirpath)

		for extension in self.extensions:
			extensiondir = extensionpaths.pop(extension, [])
			if extensiondir != []:
				extensiondir = extensiondir.pop()
				config.info('Loading extension %s from %s' % (extension, extensiondir))

				templatedir = os.path.join(extensiondir, 'templates')
				if os.path.exists(templatedir):
					self.load_templates(templatedir)

				viewdir = os.path.join(extensiondir, 'views')
				if os.path.exists(viewdir):
					old_syspath = sys.path[:]
					sys.path.append(os.path.dirname(extensiondir))
					self.get_views(viewdir, extension_name = extension)
					sys.path = old_syspath

				pythondir = os.path.join(extensiondir, 'python')
				if os.path.exists(pythondir):
					pth.insert(-1,pythondir)

		# so that extensions cannot override built-in modules
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
