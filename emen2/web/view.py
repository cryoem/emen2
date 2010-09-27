# $Author$ $Revision$
import itertools
import functools
import sys
import os
import os.path
import emen2.util.jsonutil
import functools

import emen2.util.decorators
import emen2.web.routing
import emen2.web.extfile

from emen2.util.listops import adjust
from emen2.web import routing

import emen2.db.config
g = emen2.db.config.g()
class Context(object):
	'''Partial context for views that don't need db access'''
	def reverse(self, _name, *args, **kwargs):

		result = '%s/%s'%(g.EMEN2WEBROOT, emen2.web.routing.URLRegistry.reverselookup(_name, *args, **kwargs))
		result = result.replace('//','/')

		containsqs = '?' in result
		if not result.endswith('/') and not containsqs:
			result = '%s/' % result
		elif containsqs and '/?' not in result:
			result = result.replace('?', '/?', 1)

		return result



class View(object):
	'''Base Class for views, sets up the instance variables for the class

	Subclasses are required to do four things:
		- register subclass as a view by either:
			- having a class attribute called __metaclass__ which is equal to View.register_view
		- or using View.register as a decorator

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

	preinit = []
	# use preinit = View.preinit[:] to modify this in a subclass
	# i.e.:
	# class example(View):
	# 	preinit = View.preinit[:]
	# 	@preinit.append
	# 	def _preinithook(self):
	# 		print 'Hello World'

	db = property(lambda self: self.__db)

	headers = property(lambda self: self.__headers)
	dbtree = property(lambda self: self.__dbtree)

	page = None
	ctxt = property(lambda self: self.get_context())
	_ctxt = property(lambda self: self.__ctxt)

	js_files = emen2.web.extfile.BaseJS
	css_files = emen2.web.extfile.BaseCSS

	def __set_mimetype(self, value): self.__headers['content-type'] = value
	mimetype = property(lambda self: self.__headers['content-type'], __set_mimetype)

	def __set_template(self, value): self.__template = value
	template = property(lambda self: self.__template, __set_template)

	def __init__(self, db=None, template='/pages/page_noinherit', mimetype='text/html; charset=utf-8', raw=False, css_files=None, js_files=None, format=None, method='GET', init=None, reverseinfo=None, **extra):
		'''\
		subclasses should not override this method, rather they should define an 'init' method.
		subclasses should remember to call the base classes __init__ method if they override it.

		db is the Database instance for the class to use
		template is the template the class renders
		mimetype is the mimetype returned by the class
		raw governs how the output is processed
		css_files attaches a css library to the view
		js_files attaches a javascript library to the view,
		format governs which method is called to get the view data
		init passes a method to be called to initialize the view
		reverseinfo contains information necessary to reconstruct the url
		extra catches arguments to be passed to the 'init' method
		'''
		self.__db = db
		self.method = method
		self.__headers = {'content-type': mimetype}
		self.__dbtree = Context()#DBTree(db)

		self.__template = template or self.template
		self.__ctxt = adjust({}, extra)

		try:
			LOGINUSER = self.__db._DBProxy__ctx.username
			HOST = self.__db._DBProxy__ctx.host
		except:
			LOGINUSER = None
			HOST = None
			

		self.__basectxt = dict(
			ctxt = self.dbtree,
			headers = self.__headers,
			css_files = (css_files or self.css_files)(self.__dbtree),
			js_files = (js_files or self.js_files)(self.__dbtree),
			EMEN2WEBROOT = g.EMEN2WEBROOT,
			EMEN2DBNAME = g.EMEN2DBNAME,
			EMEN2LOGO = g.EMEN2LOGO,
			BOOKMARKS = g.BOOKMARKS,
			LOGINUSER = LOGINUSER,
			HOST = HOST,
			def_title = 'Untitled',
			reverseinfo = reverseinfo
		)


		self.set_context_items(self.__basectxt)
		notify = emen2.util.jsonutil.decode(extra.pop('notify','[]'))
		if not hasattr(notify, '__iter__'): notify = [notify]
		self.set_context_item('notify', notify)

		self.etag = None

		# call any view specific initialization
		self.__raw = False
		if format is not None:
			self.get_data = getattr(self, 'get_%s' % format)

		preinit = getattr(self, 'preinit', [])
		for hook in preinit: hook(self)

		if init is not None: init=functools.partial(init,self)
		else: init = self.init
		init(**extra)


	def init(self, *_, **__):
		'''define class specific initialization here'''


	def is_raw(self):
		return self.__raw


	def make_raw(self):
		self.__raw = True

	#### Output methods #####################################################################

	def error(self, msg):
		self.template="/errors/error"
		self.ctxt["title"] = "Error"
		self.ctxt["errmsg"] = msg


	def get_data(self):
		'''override to change the way it gets the view data'''
		return Page.render_view(self)

	def get_json(self):
		'override to define json equivalent'
		return '{}'

	def __iter__(self):
		'''returns (result, mimetype)'''
		return iter((self.get_data(), self.__headers))

	def __unicode__(self):
		'''returns the data'''
		return unicode(self.get_data())

	def __str__(self):
		try:
			return str((unicode(self).encode('utf-8', 'replace')))
		except UnicodeDecodeError:
			return self.get_data()

	#### Metadata manipulation ###############################################################

	# HTTP header manipulation
	def set_headers(self, __headers_=None, **hs):
		'add a dictionary containing several headers to the HTTP headers'
		headers = __headers_ or {}
		headers.update(hs)
		self.__headers.update(headers)

	def set_header(self, name, value):
		'set a single header'
		self.__headers[name] = value
		return (name, value)

	def get_headers(self):
		return self.__headers

	def get_header(self, name):
		'get a HTTP header that this view will return'
		return self.__headers[name]

	# template context manipulation
	def get_context_item(self, name, default=None):
		return self.__ctxt.get(name)

	def set_context_item(self, name, value):
		'''add a single item to the tempalte context'''
		if name in self.__basectxt.keys():
			raise ValueError, "%s is a reserved context item" % name
		self.__ctxt[name] = value

	def set_context_items(self, __dict_=None, **kwargs):
		'''add a number of items to the template context'''
		self.__ctxt.update(kwargs)
		self.__ctxt.update(__dict_ or {})
		self.__ctxt.update(self.__basectxt)

	# alias update_context to set_context_items ###TODO: remove this alias
	update_context = set_context_items

	def get_context(self, extra_dict=None):
		'''get the view's context'''
		return self.__ctxt

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

		The new method is called _after_ View.__init__ gets called
		'''
		def _i1(func):
			matchers = []
			if len(match) == 1:
				name = func.__name__
				if name.lower() == 'init': name = 'main'
				matchers.append( (name, match[0], func) )
			else:
				for n,matcher in enumerate(match):
					if n == 0: matchers.append( ('%s/main' % (func.__name__), matcher, func) )
					matchers.append( ('%s/%d' % (func.__name__, n), matcher, func) )
			for k,matcher in kwmatch.iteritems():
				name = []
				if func.__name__.lower() == 'init':
					name.append('main')
				else:
					name.append(func.__name__, k)
				matchers.append( ('/'.join(name), matcher, func) )
			func.matcherinfo = matchers # g.log.note_var(matchers)
			return func
		return _i1

	@staticmethod
	def register(cls):
		'''Register a view and give it a URL
		N.B. this used to call a classmethod of publicresource, this no longer happens

		-> classes can specify more than one matcher in a dictionary, if that is the case, reverse lookup
		     can be done by self.dbtree.reverse (in a subclass of View) or ctxt.reverse in a template
			       it defaults to the one named 'main', if others exist they can be accessed by '<Classname>/<subname>'
		-> this also registers urls defined by the add_matcher decorator
		acceptable __matcher__ values:
			-> __matcher__ = dict(
				  main = r'^/some/url/(?P<param1>\d+)/$',
				  alt1 = r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$'
				)
			--> these can be reversed with self.dbtree.reverse('ClassName/alt1', param1='asd') and such
			-> __matcher__ = [r'^/some/url/(?P<param1>\d+)/$', r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$']
			-> __matcher__ =  r'^/some/url/(?P<param1>\d+)/$'
			-> or any object that has an attribute named 'match', and 'groupdict' (if one doesn't want to use regular expressions)

		'''
		cls.__url = routing.URL(cls.__name__)

		#old style matchers
		if hasattr(cls, '__matcher__'):
			if hasattr(cls.__matcher__, '__iter__'):
				if hasattr(cls.__matcher__, 'items'):
					if not cls.__matcher__.get('main', False):
						g.warn('Main matcher not specified for (%r) (%r)' % (cls, cls.__url))
					for name, expression in cls.__matcher__.items():
						name = '%s' % name
						cb = functools.partial(cls, init=cls.init)
						result = functools.wraps(cls)(cb)
						cls.__url.add_matcher(name, expression, cb)

				else:
					cls.__url.add_matcher('main', cls.__matcher__[0], cls)
					for counter, expression in enumerate(cls.__matcher__):
						cb = functools.partial(cls, init=cls.init)
						result = functools.wraps(cls)(cb)
						cls.__url.add_matcher('%02d' % counter, expression, cb)

			else:
				cb = functools.partial(cls, init=cls.init)
				result = functools.wraps(cls)(cb)
				cls.__url.add_matcher('main', cls.__matcher__, cb)

		#matchers produced by the add_matcher decorator
		for v in (func.matcherinfo for func in cls.__dict__.values() if hasattr(func,'matcherinfo')):
			for matcher in v:
				name, matcher, func = matcher
				func = functools.partial(cls, init=func)
				func = functools.wraps(cls)(func)
				cls.__url.add_matcher(name, matcher, func)

		ur = routing.URLRegistry()
		ur.register(cls.__url)
		return cls

class AdminView(View):
	preinit = View.preinit[:]

	@preinit.append
	def checkadmin(self):
		context = self.db._getctx()
		if not context.checkadmin():
			raise emen2.web.responsecodes.ForbiddenError, 'User %r is not an administrator.' % context.username

class AuthView(View):
	preinit = View.preinit[:]

	@preinit.append
	def checkadmin(self):
		context = self.db._getctx()
		if not 'authenticated' in context.groups:
			raise emen2.web.responsecodes.ForbiddenError, 'User %r is not authenticated.' % context.username


class MatcherInfo(object):
	def __init__(self, args, kwargs):
		self.args, self.kwargs = args, kwargs


class Page(object):
	'''Abstracts template rendering'''
	def __init__(self, template, value_dict=None, **kwargs):
		self.__template = template
		self.__valuedict = adjust(kwargs, value_dict or {})

	def __unicode__(self):
		return g.templates.render_template(self.__template, self.__valuedict)

	def __str__(self):
		return g.templates.render_template(self.__template, self.__valuedict).encode('ascii', 'replace')


	@classmethod
	def render_template(cls, template, modifiers=None):
		modifiers = modifiers or {}
		modifiers['def_title'] = modifiers.get('title', 'No Title')
		return cls(template, value_dict=modifiers)

	@classmethod
	def quick_render(cls,  title='', content='', modifiers=None):
		modifiers = modifiers or {}
		modifiers['content'] = content
		return cls.render_template('/pages/page', modifiers)

	@classmethod
	def render_view(cls, view):
		ctxt = view.get_context()

		if view.get_header('content-type') == 'application/json' and hasattr(view, 'page'):
			result = view.page
		else:
			if view.page is None:
				result = cls.render_template(view.template, modifiers=ctxt)
			else:
				if view.is_raw():
					result = view.page
				else:
					if not ctxt.has_key('title'):
						ctxt['def_title'] = 'No Title'
					result = cls.quick_render(ctxt['def_title'], view.page % ctxt, modifiers=ctxt)
		return result

__version__ = "$Revision$".split(":")[1][:-1].strip()
