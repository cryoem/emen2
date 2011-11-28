# $Id$
'''
Module contents:

I. Views
	- class :py:class:`TemplateView`
	- class :py:class:`View`

II. View Plugins
	- class :py:class:`ViewPlugin`
	- class :py:class:`AdminView`
	- class :py:class:`AuthView`

III. View loader
	- class :py:class:`ViewLoader`

'''

import sys
import os
import time
import collections
import functools

import jsonrpc.jsonutil

# emen2 imports
import emen2.util.decorators
import emen2.util.listops
import emen2.util.fileops

import emen2.web.routing
import emen2.web.resource
import emen2.web.notifications

import emen2.db.config
import emen2.db.log


# Exported classes
__all__ = ['TemplateView', 'View', 'ViewPlugin', 'AdminView', 'AuthView']


##### I. Views #####

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


	host = emen2.db.config.get('network.EMEN2HOST', 'localhost')
	port = emen2.db.config.get('network.EMEN2PORT', 80)

	def reverse(self, _name, *args, **kwargs):
		"""Create a URL given a view Name and arguments"""

		full = kwargs.pop('_full', False)
		webroot = emen2.db.config.get('network.EMEN2WEBROOT', '')

		result = '%s/%s'%(webroot, emen2.web.routing.reverse(_name, *args, **kwargs))
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
class TemplateView(emen2.web.resource.EMEN2Resource):
	'''An EMEN2Resource class that renders a result using a template.'''

	# Registration methods moved to the new EMEN2resource

	# A list of methods to call during init (with self)
	preinit = []

	# Basic properties
	title = property(
		lambda self: self.ctxt.get('title'),
		lambda self, value: self.ctxt.set('title',value))

	template = property(
		lambda self: self.ctxt.get('template', '/simple'),
		lambda self, value: self.ctxt.set('template', value))


	def __init__(self, db=None, *args, **blargh):
		'''\
		request_method is the HTTP method
		request_headers are the request headers
		request_location is the request URI
		'''

		super(TemplateView, self).__init__()

		#
		self.db = db

		# Response headers
		self._headers = {}

		# Notifications and errors
		self._notify = []
		self._errors = []

		# Template Context
		# Init context with headers, errors, etc.
		# Then update with any extra arguments specified.
		self.ctxt = TemplateContext()
		self.ctxt.update(dict(
			HEADERS = self._headers,
			NOTIFY = self._notify,
			ERRORS = self._errors,
			REQUEST_LOCATION = self.request_location,
			REQUEST_HEADERS = self.request_headers,
			title = 'No Title'
		))

		# ETags
		self.etag = None

	def init(self, *arrgghs, **blarrgghs):
		pass

	# def notify(self, msg):
	# 	self.events.event('notify')(id(self), msg)


	#### Output methods #####

	def __unicode__(self):
		'''Render the View into a string that can be sent to the client'''
		return unicode(self.get_data())

	def __str__(self):
		'''Render the View, encoded as UTF-8'''
		return unicode(self.get_data()).encode('utf-8', 'replace')
		# try:
		#	return str((unicode(self).encode('utf-8', 'replace')))
		# except UnicodeDecodeError:
		# 	return self.get_data()

	def error(self, msg):
		'''Set the output to a simple error message'''
		self.template = "/errors/error"
		self.title = 'Error'
		self.ctxt['errmsg'] = msg

	def redirect(self, location):
		'''Redirect by setting Location header and
		using the redirect template'''
		self.headers['Location'] = location.replace('//','/')
		self.template = '/redirect'

	def get_data(self):
		'''Render the template'''
		return emen2.db.config.templates.render_template(self.template, self.ctxt)


	#### Metadata manipulation #####

	# HTTP header manipulation
	headers = property(
		fget=lambda self: self._headers,
		fdel=lambda self: self._headers.clear())

	@headers.setter
	def headers(self, value):
		'''Add a dictionary containing several headers to the HTTP headers'''
		value = dict( (self._normalize_header_name(k),v) for k,v in value.items() )
		self._headers.update(value)

	def _normalize_header_name(self, name):
		return '-'.join(x.capitalize() for x in name.split('-'))

	# Ian: I may deprecate these methods in favor of the header/ctxt
	# property-style getter/setter.
	def set_header(self, name, value):
		'''Set a single header'''
		name = self._normalize_header_name(name)
		self._headers[name] = value
		return (name, value)

	def get_header(self, name):
		'''Get a HTTP header that this view will return'''
		name = self._normalize_header_name(name)
		return self._headers[name]

	def set_context_item(self, name, value):
		'''Add a single item to the tempalte context'''
		self.ctxt[name] = value




class View(TemplateView):
	'''A View that checks some DB specific details'''

	notifications = emen2.web.notifications.NotificationHandler()

	def init(self, *args, **kwargs):
		'''Run this before the requested view method.'''
		super(View, self).init(*args, **kwargs)
		user = {}
		admin = False
		ctx = getattr(self.db, '_getctx', lambda:None)()
		try:
			user = ctx.db.getuser(ctx.username)
			admin = ctx.checkadmin()
		except:
			pass

		self.ctxt.update(dict(
			HOST = getattr(ctx, 'host', None),
			USER = user,
			ADMIN = admin,
			EMEN2WEBROOT = emen2.db.config.get('network.EMEN2WEBROOT'),
			EMEN2DBNAME = emen2.db.config.get('customization.EMEN2DBNAME'),
			EMEN2LOGO = emen2.db.config.get('customization.EMEN2LOGO'),
			BOOKMARKS = emen2.db.config.get('bookmarks.BOOKMARKS', {}),
			VERSION = emen2.db.config.get('params.VERSION')
		))


	# def notify(self, msg):
	# 	if self.ctxid is not None:
	# 		self.events.event('notify')(self.ctxid, msg)
	#
	# def get_data(self, *a, **kw):
	# 	# Get notifications if the user has a ctxid
	# 	if self.ctxid is not None:
	# 		self._notify.extend(self.notifications.get_notifications(self.ctxid))
	# 	return TemplateView.get_data(self, *a, **kw)




##### II. View plugins #####

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




###### III. View loader #####

class ViewLoader(object):
	routing_table = emen2.db.config.get('config.ROUTING', {})
	redirects = emen2.db.config.get('config.REDIRECTS', {})
	extensions = emen2.db.config.get('extensions.EXTS')

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
			# emen2.db.log.info(e)
			level = 'ERROR'
			msg[1] = "FAILED:"
			failures.append(viewname)
			emen2.db.log.print_exception()

		msg.append(filpath+ext)
		emen2.db.log.msg(level, ' '.join(msg))


	def __init__(self):
		self.get_views = emen2.util.fileops.walk_path('.py', self.view_callback)


	def load_extensions(self):
		# Load exts
		# print self.extensions
		for ext, path in self.extensions.items():
			# print ext, path, 'extension loading'
			self.load_extension(ext, path)
		return True


	def load_extension(self, ext, path):
		# We'll be adding the extension paths with a low priority..
		pth = list(reversed(sys.path))
		emen2.db.log.info('Loading extension %s: %s' % (ext, path))

		# ...add ext path to the python module search
		pythondir = os.path.join(path, 'python')
		if os.path.exists(pythondir):
			pth.insert(-1,pythondir)

		# ...load views
		viewdir = os.path.join(path, 'views')
		if os.path.exists(viewdir):
			old_syspath = sys.path[:]
			sys.path.append(os.path.dirname(path))
			self.get_views(viewdir, extension_name=ext)
			sys.path = old_syspath

		# Restore the original sys.path
		sys.path = list(reversed(pth))


__version__ = "$Revision$".split(":")[1][:-1].strip()
