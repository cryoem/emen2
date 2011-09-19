# $Id$
'''
Module contents:

I. Views
	- class :py:class:`View`

II. View Plugins
	- class :py:class:`ViewPlugin`
	- class :py:class:`AdminView`
	- class :py:class:`AuthView`

III. View loader
	- class :py:class:`ViewLoader`
	
'''

import itertools
import functools
import sys
import os
import os.path
import jsonrpc.jsonutil
import functools
import time
import collections
import contextlib

import emen2.web.routing
import emen2.web.templating
import emen2.web.notifications

import emen2.util.decorators
import emen2.util.listops
import emen2.util.fileops

from emen2.web import routing

import emen2.db.config
g = emen2.db.config.g()

__all__ = ['View', 'ViewPlugin', 'AdminView', 'AuthView', 'Page']


############ ############ ############
# I. Views                           #
############ ############ ############


class TemplateContext(collections.MutableMapping):
	'''Template Context'''
	
	def __init__(self, base=None):
		self.__base = {}
		self.__dict = self.__base.copy()
		self.__dict['ctxt'] = self

	def __getitem__(self, n):
		return self.__dict[n]

	def __setitem__(self, n, v):
		self.__dict[n] = v
		self.__dict.update(self.__base)

	def __delitem__(self, n):
		del self.__dict[n]
		self.__dict.update(self.__base)

	def __len__(self):
		return len(self.__dict)

	def __iter__(self):
		return iter(self.__dict)

	def __repr__(self):
		return '<TemplateContext: %r>' % self.__dict

	def copy(self):
		new = TemplateContext(self.__base)
		new.__dict.update(self.__dict)
		return new

	def set(self, name, value=None):
		self[name] = value


	host = g.watch('EMEN2HOST', 'localhost')
	port = g.watch('EMEN2PORT', 80)

	def reverse(self, _name, *args, **kwargs):
		"""Create a URL given a view Name and arguments"""
		
		full = kwargs.pop('_full', False)

		result = '%s/%s'%(g.EMEN2WEBROOT, emen2.web.routing.URLRegistry.reverselookup(_name, *args, **kwargs))
		result = result.replace('//','/')
		if full:
			result = 'http://%s:%s%s' % (self.host, self.port, result)

		containsqs = '?' in result
		if not result.endswith('/') and not containsqs:
			result = '%s/' % result
		elif containsqs and '/?' not in result:
			result = result.replace('?', '/?', 1)

		return result
		


###NOTE: This class should not access the db in any way, such activity is carried out by
###		the View class below.
class _View(object):
	'''Base Class for views, sets up the instance variables for the class

	Subclasses are required to do four things:
		- Register using View.register as a decorator

		- have a class attribute called __matcher__ which contains either:
			- A Regular Expression representing the url which matches the class
			- A list of Regular Expressions to match against
			- A dictionary of the format { (subviewname or 'main'):matcher }
				- 'main' indicates the default view

		- override the 'init' method, not __init__
			- If __init__ is overridden, it will have to be called in the overriding method

		- define data output methods:
			- define a method named get_data in order to return data for web browsers
			- define a method named get_json in order to return a json representation of the view
	'''

	# A list of methods to call during init (with self)
	preinit = []

	title = property(
		lambda self: self.ctxt.get('title', 'No Title'), 
		lambda self, value: self.ctxt.set('title',value))

	template = property(
		lambda self: self.ctxt.get('template', '/simple'),
		lambda self, value: self.ctxt.set('template', value))

	mimetype = property(
		lambda self: self.get_header('content-type', 'text/html; charset=utf-8'),
		lambda self, value: self.set_header('content-type', value))


	def __init__(self, format=None, method='GET', init=None, reverseinfo=None, request_headers=None, basectxt=None, **extra):
		'''\
		subclasses should not override this method, rather they should define an 'init' method.
		subclasses should remember to call the base classes __init__ method if they override it.

		format governs which method is called to get the view data
		init passes a method to be called to initialize the view
		reverseinfo is the request URI
		request_headers are the request headers
		extra catches arguments to be passed to the 'init' method
		'''
		# template is the template the class renders
		# mimetype is the mimetype returned by the class
		
		# Request headers
		self.__request_headers = request_headers or {}

		# Response headers
		self.__headers = {}
		# self.set_header('Content-Type', mimetype)
		
		# Notifications and errors
		self.__notify = []
		self.__errors = []

		# Template Context
		# Init context with headers, errors, etc.
		# Then update with any extra arguments specified.
		self.ctxt = TemplateContext()
		self.ctxt.update(dict(
			headers = self.__headers,
			notify = self.__notify,
			errors = self.__errors,
			reverseinfo = reverseinfo
		))
		self.ctxt.update(basectxt or {})
		self.ctxt.update(extra)

		# HTTP Method and HTTP ETags (cache control)
		self.method = method
		self.etag = None

		# Set the return format. There must be a get_<format> method.
		if format is not None:
			self.get_data = getattr(self, 'get_%s' % format)

		# Run any init hooks
		preinit = getattr(self, 'preinit', [])
		for hook in preinit:
			hook(self)

		# Run the View subclass' init method
		if init is not None:
			init = functools.partial(init, self)
		else:
			init = self.init
		
		upd = init(**extra)
		self.set_context_items(upd)

		
	def notify(self, msg):
		self.events.event('notify')(id(self), msg)


	def init(self, *_, **__):
		'''define class specific initialization here'''
		pass


	#### Output methods #####################################################################

	def error(self, msg):
		'''Set the output to a simple error message'''
		self.template = "/errors/error"
		self.title = "Error"
		self.ctxt["errmsg"] = msg

	def redirect(self, location):
		self.headers['Location'] = location
		self.template = '/redirect'

	def get_data(self):
		'''Override to change the way it gets the view data'''
		return g.templates.render_template(self.template, self.ctxt)
		# return Page.render_view(self)

	def get_json(self):
		'''Override to define json equivalent'''
		return '{}'

	def __iter__(self):
		'''Returns (result, mimetype)'''
		return iter( (self.get_data(), self.__headers) )

	def __unicode__(self):
		'''Returns the data'''
		return unicode( self.get_data() )

	def __str__(self):
		try:
			return str((unicode(self).encode('utf-8', 'replace')))
		except UnicodeDecodeError:
			return self.get_data()

	#### Metadata manipulation ###############################################################

	# HTTP header manipulation
	headers = property(
		fget=lambda self: self.__headers, 
		fdel=lambda self: self.__headers.clear())

	@headers.setter
	def headers(self, value):
		'''Add a dictionary containing several headers to the HTTP headers'''
		value = dict( (self.normalize_header_name(k),v) for k,v in value.items() )
		self.__headers.update(value)

	def normalize_header_name(self, name):
		return '-'.join(x.capitalize() for x in name.split('-'))

	def set_header(self, name, value):
		'''Set a single header'''
		name = self.normalize_header_name(name)
		self.__headers[name] = value
		return (name, value)

	def get_header(self, name):
		'''Get a HTTP header that this view will return'''
		name = self.normalize_header_name(name)
		return self.__headers[name]

	# template context manipulation
	def get_context_item(self, name, default=None):
		return self.ctxt.get(name, default)

	def set_context_item(self, name, value):
		'''Add a single item to the tempalte context'''
		self.ctxt[name] = value

	def set_context_items(self, __dict_=None, **kwargs):
		'''Add a number of items to the template context'''
		self.ctxt.update(kwargs)
		self.ctxt.update(__dict_ or {})

	# alias update_context to set_context_items
	update_context = set_context_items

	def get_context(self):
		'''Get the view's context'''
		return self.ctxt


	#### View registration methods ###########################################################

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register(cls)
		return cls


	@classmethod
	def add_matcher(cls, *match, **kwmatch):
		'''Decorator used to add a matcher to an already existing class

		Named groups in matcher get passed as keyword arguments
		Other groups in matcher get passed as positional arguments
		Nothing else gets passed

		The new method is called *after* View.__init__ is called
		'''
		if not match: raise ValueError, 'A view must have at least one non-keyword matcher'
		def check_name(name): return 'main' if name.lower() == 'init' else name
		def _i1(func):
			matchers = []
			name = check_name(func.__name__)

			# get the main matcher
			matcher, match_ = match[0], match[1:]
			matchers.append( ('%s' % name, matcher, func) )
			g.debug('REGISTERING %r as %r with %r' % (name, matcher, func) )

			# get alternate matchers
			for k,matcher in itertools.chain(	enumerate(match_, 1),
															kwmatch.iteritems()	):
				name = '%s/%s' % (name, k)
				matchers.append( (name, matcher, func) )
				g.debug('REGISTERING %r as %r with %r' % (name, matcher, func) )

			# save all matchers to the function
			func.matcherinfo = matchers
			return func
		return _i1

	@classmethod
	def __parse_matcher_attribute(self, cls, matchers, urls):
		if hasattr(matchers, '__iter__'):
			if hasattr(matchers, 'items'):
				if not matchers.get('main', False):
					g.warn('Main matcher not specified for (%r) (%r)' % (cls, urls))
				for name, expression in matchers.items():
					name = '%s' % name
					cb = functools.partial(cls, init=cls.init)
					result = functools.wraps(cls)(cb)
					urls.add_matcher(name, expression, cb)

			else:
				urls.add_matcher('main', matchers[0], cls)
				for counter, expression in enumerate(matchers):
					cb = functools.partial(cls, init=cls.init)
					result = functools.wraps(cls)(cb)
					urls.add_matcher('%02d' % counter, expression, cb)

		else:
			cb = functools.partial(cls, init=cls.init)
			result = functools.wraps(cls)(cb)
			urls.add_matcher('main', matchers, cb)

	@classmethod
	def __parse_add_matcher_values(self, cls, matchers, urls):
		for matcher in matchers:
			name, matcher, func = matcher
			func = functools.partial(cls, init=func)
			func = functools.wraps(cls)(func)
			urls.add_matcher(name, matcher, func)


	@classmethod
	def register(self, cls):
		'''Register a view and connect it to a URL

		- registers urls specified in the __matcher__ attribute

			- this attribute can specify more than one matcher in a dictionary, if that is the case, reverse lookup
					can be done by self.ctxt.reverse (in a subclass of View) or ctxt.reverse in a template
					it defaults to the one named 'main', if others exist they can be accessed by '<Classname>/<subname>'

		- this also registers urls defined by the add_matcher decorator

		acceptable __matcher__ values:
			- dictionary
				.. code-block:: python

						__matcher__ = dict(
							main = r'^/some/url/(?P<param1>\d+)/$',
							alt1 = r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$'
						)

				- these can be reversed with self.ctxt.reverse('ClassName/alt1', param1='asd') and such

			- list
				.. code-block:: python

					__matcher__ = [r'^/some/url/(?P<param1>\d+)/$', r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$']

			- string

				.. code-block:: python

					__matcher__ =  r'^/some/url/(?P<param1>\d+)/$'

			- or any object that has an attribute named 'match', and 'groupdict' (if one doesn't want to use regular expressions)

		'''
		with routing.URLRegistry().url(cls.__name__) as url:
			cls.__url = url

			# old style matchers
			if hasattr(cls, '__matcher__'):
				self.__parse_matcher_attribute(cls, cls.__matcher__, url)

			#matchers produced by the add_matcher decorator
			for v in ( getattr(func, 'matcherinfo', None) for func in cls.__dict__.values() ):
				if v is not None:
					self.__parse_add_matcher_values(cls, v, url)

			ur = routing.URLRegistry()
		return cls


	slots = collections.defaultdict(list)
	@classmethod
	def provides(cls, slot):
		'''Decorate a method to indicate that the method provides a certain functionality'''
		def _inner(view):
			cls.slots[slot].append(functools.partial(cls, init=view))
			return view
		return _inner

	@classmethod
	def require(cls, slot):
		'''Use to get a view with a desired functionality'''
		if slot in cls.slots:
			return cls.slots[slot][-1]
		else: raise ValueError, "No such slot"





import emen2.web.events
class View(_View):
	'''Contains DB specific view code'''

	db = property(lambda self: self.__db)
	events = emen2.web.events.EventRegistry()
	notifications = emen2.web.notifications.NotificationHandler()

	def __init__(self, db=None, **extra):
		self.__db = db
		ctx = getattr(self.__db, '_getctx', lambda:None)()
		self.ctxid = ctx and ctx.name
		
		user = {}
		try:
			user = ctx.db.getuser(ctx.username)
		except:
			pass

		basectxt = dict(
			HOST = getattr(ctx, 'host', None),
			USER = user,
			EMEN2WEBROOT = g.EMEN2WEBROOT,
			EMEN2DBNAME = g.EMEN2DBNAME,
			EMEN2LOGO = g.EMEN2LOGO,
			BOOKMARKS = g.BOOKMARKS,
			VERSION = emen2.VERSION
		)

		# Need to pass in the basectxt before the View's init()
		_View.__init__(self, basectxt=basectxt, **extra)


	def notify(self, msg):
		if self.ctxid is not None:
			self.events.event('notify')(self.ctxid, msg)

	def get_data(self, *a, **kw):
		# Get notifications if the user has a ctxid
		if self.ctxid is not None:
			self.__notify.extend(self.notifications.get_notifications(self.ctxid))
		return _View.get_data(self, *a, **kw)




############-############-############
# II. View plugins                   #
############-############-############

class ViewPlugin(object):
	'''Parent class the interface for View plugins

	To write a view plugin, subclass this class and provide a iterable
	classattribute called "preinit" which contains a list of methods
	executed before the view method is called

	.. py:function:: preinit(self)'''

	@classmethod
	def attach(cls, view):
		'''Decorate a class with this method to add a :py:class:`ViewPlugin` to the class'''
		view.preinit = view.preinit[:]
		view.preinit.extend(cls.preinit)
		return view


class AdminView(ViewPlugin):
	'''A :py:class:`ViewPlugin` which only allows Administrators to access a view'''

	preinit = []

	@preinit.append
	def checkadmin(self):
		context = self.db._getctx()
		if not context.checkadmin():
			raise emen2.web.responsecodes.ForbiddenError, 'User %r is not an administrator.' % context.username


class AuthView(ViewPlugin):
	'''A :py:class:`ViewPlugin` which only allows Authenticated Users to access a view'''

	preinit = []

	@preinit.append
	def checkadmin(self):
		context = self.db._getctx()
		if not 'authenticated' in context.groups:
			raise emen2.web.responsecodes.ForbiddenError, 'User %r is not authenticated.' % context.username



############-############-############
# III. View loader                    #
############-############-############

class ViewLoader(object):
	routing_table = g.claim('ROUTING', {})
	redirects = g.claim('REDIRECTS', {})
	extensions = g.claim('EXTS')

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
			g.info(e)
			level = 'ERROR'
			msg[1] = "FAILED:"
			failures.append(viewname)
			g.log.print_exception()

		msg.append(filpath+ext)
		g.log.msg(level, ' '.join(msg))


	def __init__(self):
		self.get_views = emen2.util.fileops.walk_path('.py', self.view_callback)
		self.router = emen2.web.routing.URLRegistry()


	def load_extensions(self):
		# Load exts
		for ext, path in self.extensions.items():
			self.load_extension(ext, path)
		return True


	def load_extension(self, ext, path):
		# We'll be adding the extension paths with a low priority..
		pth = list(reversed(sys.path))
		g.info('Loading extension %s: %s' % (ext, path))

		# ...load views
		viewdir = os.path.join(path, 'views')
		if os.path.exists(viewdir):
			old_syspath = sys.path[:]
			sys.path.append(os.path.dirname(path))
			self.get_views(viewdir, extension_name=ext)
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


__version__ = "$Revision$".split(":")[1][:-1].strip()
