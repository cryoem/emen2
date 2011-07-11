# $Id$
'''
Module contents:

I. Views
	- class :py:class:`View`

II. View Plugins
	- class :py:class:`ViewPlugin`
	- class :py:class:`AdminView`
	- class :py:class:`AuthView`

III. Template Rendering
	- class :py:class:`Page`
'''
import itertools
import functools
import sys
import os
import os.path
import jsonrpc.jsonutil
import functools
import collections

import emen2.util.decorators
import emen2.web.routing
import emen2.web.templating

from emen2.util.listops import adjust
from emen2.web import routing
import emen2.web.extfile

import emen2.db.config
g = emen2.db.config.g()

__all__ = ['View', 'ViewPlugin', 'AdminView', 'AuthView', 'Page']




############ ############ ############
# I. Views                           #
############ ############ ############

class TemplateContext(object):
	#'''Partial context for views that don't need db access'''
	def reverse(self, _name, *args, **kwargs):

		result = '%s/%s'%(g.EMEN2WEBROOT, emen2.web.routing.URLRegistry.reverselookup(_name, *args, **kwargs))
		result = result.replace('//','/')

		containsqs = '?' in result
		if not result.endswith('/') and not containsqs:
			result = '%s/' % result
		elif containsqs and '/?' not in result:
			result = result.replace('?', '/?', 1)

		return result


class ViewContext(collections.MutableMapping):
	def __init__(self, base):
		self.__base = base
		self.__dict = base.copy()
	def __getitem__(self, n):
		return self.__dict[n]
	def __setitem__(self, n, v):
		self.__dict[n] = v
		self.__dict.update(self.__base)
	def __delitem__(self, n):
		del self.__dict[n]
		self.__dict.update(self.__base)
	def __len__(self): return len(self.__dict)
	def __iter__(self): return iter(self.__dict)
	def __repr__(self): return '<ViewContext: %r>' % self.__dict

	def copy(self):
		new = ViewContext(self.__base)
		new.__dict.update(self.__dict)
		return new

	def set(self, name, value=None):
		self[name] = value



###NOTE: This class should not access the db in any way, such activity is carried out by
###		the View class below.
class _View(object):
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

	ctxt = property(lambda self: self.get_context())
	dbtree = property(lambda self: self.__dbtree)
	js_files = emen2.web.templating.BaseJS
	css_files = emen2.web.templating.BaseCSS
	page = None

	def __settitle(self, t):
		self.__ctxt['title'] = t

	title = property(lambda self: self.__ctxt.get('title'), __settitle)

	def __set_mimetype(self, value): self.__headers['content-type'] = value
	mimetype = property(lambda self: self.__headers['content-type'], __set_mimetype)

	def __set_template(self, value): self.__template = value
	template = property(lambda self: self.__template, __set_template)

	def __init__(self, template='/pages/page', mimetype='text/html; charset=utf-8', raw=False, css_files=None, js_files=None, format=None, method='GET', init=None, reverseinfo=None, **extra):
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

		self.__headers = {'content-type': mimetype}
		self.__dbtree = TemplateContext()

		self.__template = template or self.template

		notify = jsonrpc.jsonutil.decode(extra.pop('notify','[]'))
		basectxt = extra.pop('_basectxt', {})
		basectxt.update(
			ctxt = self.dbtree,
			headers = self.__headers,
			css_files = (css_files or self.css_files)(self.__dbtree),
			js_files = (js_files or self.js_files)(self.__dbtree),
			notify = notify,
			def_title = 'Untitled',
			reverseinfo = reverseinfo
		)

		self.__ctxt = ViewContext(basectxt)
		self.__ctxt.update(extra)
		# print self.__ctxt

		#self.set_context_items(self._basectxt)

		if not hasattr(notify, '__iter__'): notify = [notify]


		self.method = method
		self.etag = None

		# call any view specific initialization
		self.__raw = False
		if format is not None:
			self.get_data = getattr(self, 'get_%s' % format)

		preinit = getattr(self, 'preinit', [])
		for hook in preinit: hook(self)

		if init is not None: init=functools.partial(init,self)
		else: init = self.init

		ctxt_items = init(**extra)
		self.set_context_items(ctxt_items)



	def init(self, *_, **__):
		'''define class specific initialization here'''


	def is_raw(self):
		return self.__raw


	def make_raw(self):
		self.__raw = True



	#### ian: add JS/CSS include
	#### ed: this looks either unfinished or corrupted
	def add_js(self, f):
		self._basectxt['js_files']

	#### Output methods #####################################################################

	def error(self, msg):
		self.template="/errors/error"
		self.title = "Error"
		self.ctxt["errmsg"] = msg


	def get_data(self):
		'''override to change the way it gets the view data'''
		return Page.render_view(self)

	def get_json(self):
		'override to define json equivalent'
		return '{}'

	def __iter__(self):
		'''returns (result, mimetype)'''
		return iter( (self.get_data(), self.__headers) )

	def __unicode__(self):
		'''returns the data'''
		return unicode( self.get_data() )

	def __str__(self):
		try:
			return str((unicode(self).encode('utf-8', 'replace')))
		except UnicodeDecodeError:
			return self.get_data()

	#### Metadata manipulation ###############################################################

	# HTTP header manipulation
	headers = property(fget=lambda self: self.__headers, fdel=lambda self: self.__headers.clear())
	@headers.setter
	def headers(self, value):
		'add a dictionary containing several headers to the HTTP headers'
		self.__headers.update(value)

	def set_header(self, name, value):
		'set a single header'
		self.__headers[name] = value
		return (name, value)

	def get_header(self, name):
		'get a HTTP header that this view will return'
		return self.__headers[name]

	# template context manipulation
	def get_context_item(self, name, default=None):
		return self.__ctxt.get(name, default)

	def set_context_item(self, name, value):
		'''add a single item to the tempalte context'''
		self.__ctxt[name] = value

	def set_context_items(self, __dict_=None, **kwargs):
		'''add a number of items to the template context'''
		self.__ctxt.update(kwargs)
		self.__ctxt.update(__dict_ or {})

	# alias update_context to set_context_items
	update_context = set_context_items

	def get_context(self):
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
					can be done by self.dbtree.reverse (in a subclass of View) or ctxt.reverse in a template
					it defaults to the one named 'main', if others exist they can be accessed by '<Classname>/<subname>'

		- this also registers urls defined by the add_matcher decorator

		acceptable __matcher__ values:
			- dictionary
				.. code-block:: python

						__matcher__ = dict(
							main = r'^/some/url/(?P<param1>\d+)/$',
							alt1 = r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$'
						)

				- these can be reversed with self.dbtree.reverse('ClassName/alt1', param1='asd') and such

			- list
				.. code-block:: python

					__matcher__ = [r'^/some/url/(?P<param1>\d+)/$', r'^/some/url/(?P<param1>[a-zA-Z]{3,}/$']

			- string

				.. code-block:: python

					__matcher__ =  r'^/some/url/(?P<param1>\d+)/$'

			- or any object that has an attribute named 'match', and 'groupdict' (if one doesn't want to use regular expressions)

		'''
		cls.__url = routing.URL(cls.__name__)

		# old style matchers
		if hasattr(cls, '__matcher__'):
			self.__parse_matcher_attribute(cls, cls.__matcher__, cls.__url)

		#matchers produced by the add_matcher decorator
		for v in ( getattr(func, 'matcherinfo', None) for func in cls.__dict__.values() ):
			if v is not None:
				self.__parse_add_matcher_values(cls, v, cls.__url)

		ur = routing.URLRegistry()
		ur.register(cls.__url)
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





class View(_View):
	'''Contains DB specific view code'''

	db = property(lambda self: self.__db)
	def __init__(self, db=None, notify='', **extra):
		self.__db = db
		ctx = getattr(self.__db, '_getctx', lambda:None)()
		HOST = getattr(ctx, 'host', None)

		user = None
		try:
			user = ctx.db.getuser(ctx.username)
		except:
			pass

		basectxt = dict(
			HOST = HOST,
			EMEN2WEBROOT = g.EMEN2WEBROOT,
			EMEN2DBNAME = g.EMEN2DBNAME,
			EMEN2LOGO = g.EMEN2LOGO,
			BOOKMARKS = g.BOOKMARKS,
			USER = user
		)

		_View.__init__(self, _basectxt=basectxt, **extra)

		self.set_context_item('notify', notify)





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


############ ############ ############
# III. template rendering            #
############ ############ ############

class Page(object):
	'''Helper class which renders templates for a :py:class:`View`'''

	def __init__(self, template, value_dict=None, **kwargs):
		self.__template = template
		self.__valuedict = adjust(kwargs, value_dict or {})

	def __repr__(self):
		vd = '{%s}'
		l = ','.join( '%r:%r' % (k,v) for k,v in self.__valuedict.items() )
		m = l[:20]
		if l!=m: m = ''.join([m, '...'])
		vd %= m
		return '<Page template=%s values=%s>' % (self.__template, vd)
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
		modifiers['def_title'] = title or modifiers.pop('title', None)
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
					result = cls.quick_render(ctxt['def_title'], view.page % ctxt, modifiers=ctxt)
		return result





__version__ = "$Revision$".split(":")[1][:-1].strip()
