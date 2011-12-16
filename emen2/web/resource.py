# $Id$

import re
import time
import random
import traceback
import collections
import functools
import Queue
import itertools
import tempfile

import twisted.internet
import twisted.web.static
import twisted.web.resource
import twisted.python.failure

import jsonrpc.jsonutil
import jsonrpc.server

import mako.exceptions

# emen2 imports
import emen2.db.config
import emen2.db.exceptions
import emen2.db.handlers
import emen2.util.loganalyzer
import emen2.util.listops
import emen2.web.events
import emen2.web.routing
import emen2.web.responsecodes
import emen2.web.server




##### Routing Resource #####

class Router(twisted.web.resource.Resource):
	isLeaf = False

	# Find a resource or view
	def getChildWithDefault(self, path, request):
		if path in self.children:
			return self.children[path]

		# Add a final slash.
		# Most of the view matchers expect this.
		path = request.path
		if not path:
			path = '/'
		if path[-1] != "/":
			path = "%s/"%path
		request.path = path

		try:
			view, method = emen2.web.routing.resolve(path=request.path)
		except:
			return self

		# This may move into routing.Router in the future.
		view = view()
		view.render = functools.partial(view.render, method=method)
		return view


	# Resource was not found
	def render(self, request):
		return 'Not found'



##### Base EMEN2 Resource #####

# Special thanks to this Dave Peticolas's blog post for
# helping sort out my deferred cancel/callback/errback situation:
# http://krondo.com/?p=2601

class EMEN2Resource(object):
	"""Base resource for EMEN2. Handles proper parsing of HTTP request arguments
	into a format that plays well with EMEN2, and contains all the common features
	of setting up the deferreds, threadpool, handling errors, etc.
	"""
	# Subclasses should do the following:
	# 	- Register using View.register as a decorator
	#
	# 	- Decorate methods with @View.add_matcher(matcher), where matcher is:
	# 		- A Regular Expression representing the url which matches the class
	# 		- A list of Regular Expressions to match against
	#
	# 	- Optionally define data output methods:
	# 		- define a method named get_data in order to return data for web browsers
	# 		- define a method named get_json in order to return a json representation of the view

	isLeaf = True
	events = emen2.web.events.EventRegistry()
	routing = emen2.web.routing

	def __init__(self, request_location='', request_headers=None, request_method='get'):
		# HTTP Method
		self.request_method = request_method

		# Request headers
		self.request_headers = request_headers or {}

		# Request location
		self.request_location = request_location

		# Any uploaded files
		self.request_files = []

		# HTTP ETags (cache control)
		self.etag = None


	##### Resource interface #####

	def render(self, request, method=None):
		# Override self._render to change how the result is returned
		# The default is to run a supplied method (or default: render_action)
		# wrapped in a DB transaction from the DBPool.
		method = method or self.render_action

		# Update request details
		self.request_method = request.method.lower()
		self.request_headers = request.getAllHeaders()
		self.request_location = request.path
		# In the future the base ctxt will just have a ref to the view..
		self.ctxt['REQUEST_METHOD'] = self.request_method
		self.ctxt['REQUEST_HEADERS'] = self.request_headers
		self.ctxt['REQUEST_LOCATION'] = self.request_location

		# Parse and filter the request arguments
		args = self.parse_args(request)

		# Find the authentication token
		ctxid = args.pop('ctxid', None) or request.getCookie("ctxid")
		host = request.getClientIP()

		# self._render can either return an immediate result,
		# or a deferred that will write to request using callbacks.
		self.events.event('web.request.received')(request, ctxid, args, host)
		return self._render(request, method, ctxid=ctxid, host=host, args=args)


	def _render(self, request, method, ctxid=None, host=None, args=None):
		# Setup deferred rendering using a DB transaction.
		t = time.time()

		# Use the EMEN2 DB thread pool.
		deferred = emen2.web.server.pool.rundb(
			self._render_db,
			method,
			ctxid = ctxid,
			host = host,
			args = args)

		# Callbacks
		deferred.addCallback(self.render_cb, request, t=t)
		deferred.addErrback(self.render_eb, request, t=t)
		request.notifyFinish().addErrback(self._request_broken, request, deferred)
		return twisted.web.static.server.NOT_DONE_YET


	def _render_db(self, method, db=None, ctxid=None, host=None, args=None):
		# Render method
		self.db = db

		# The DBProxy context manager will open a transaction, and abort
		# on an uncaught exception.
		with self.db:
			# Bind the ctxid/host to the DBProxy
			self.db._setContext(ctxid,host)
			# Any View init method is run inside the transaction
			self.init()
			result = method(self, **args)

		return result


	def render_action(self, *args, **kwargs):
		'''Default render method'''
		return 'Rendered %s'%self.__class__.name


	##### Callbacks #####

	def render_cb(self, result, request, t=0, **_):
		# If a result was passed, use that. Otherwise use str(self).
		# Note: the template rendering will occur here,
		# 	outside of the DB transaction.
		if result == None:
			result = str(self)

		# Filter the headers.
		headers = {}
		headers.update(self.headers)
		headers = dict( (k,v) for k,v in headers.iteritems() if v != None )
		if result is not None:
			headers['Content-Length'] = len(result)

		# Redirect if necessary
		if headers.get('Location'):
			request.setResponseCode(302)

		[request.setHeader(key, str(headers[key])) for key in headers]

		# If X-Ctxid (auth token) was supplied as a header,
		# set the client's cookie. This is is used by login, logout
		# and opening a web browser from desktop clients with ?ctxid as
		# a querystring argument.
		setctxid = headers.get('X-Ctxid')
		if setctxid != None:
			request.addCookie("ctxid", setctxid, path='/')

		# Send result to client
		if result is not None:
			request.write(result)

		# Close the request and write to log
		request.finish()
		self.events.event('web.request.succeed')(request, setctxid, headers, result)


	def render_eb(self, failure, request, t=0, **_):
		# Error callback
		e, data = '', ''
		headers = {}

		print "Failure:"
		print failure

		# Raise the exception
		try:
			# This method accepts either a regular Exception or Twisted Failure
			if isinstance(failure, twisted.python.failure.Failure):
				failure.raiseException()
			else:
				raise failure

		# Closed connection error. Nothing to write, and no connection to close.
		except (twisted.internet.defer.CancelledError), e:
			return

		# Expired or invalid session. Remove ctxid and redirect to root.
		except emen2.db.exceptions.SessionError, e:
			data = self.render_error_security(request.uri, e)
			headers['Location'] = '/'
			request.addCookie('ctxid', '', path='/')

		# Authentication exceptions
		except emen2.db.exceptions.SecurityError, e:
			data = self.render_error_security(request.uri, e)

		# HTTP errors
		except emen2.web.responsecodes.HTTPResponseCode, e:
			data = self.render_error_response(request.uri, e)

		# General error
		except BaseException, e:
			data = self.render_error(request.uri, e)

		# Write the response
		headers.update(getattr(e, 'headers', {}))
		request.setResponseCode(getattr(e, 'code', 500))
		[request.setHeader(k, v) for k,v in headers.items()]
		request.write(data)

		request.finish()
		self.events.event('web.request.fail')(request, headers.get('X-Ctxid'), headers, data)


	##### Error handlers #####

	# ian: todo: Use a config value to choose which error pages (mako, or emen2) to use.
	def render_error(self, location, e):
		return mako.exceptions.html_error_template().render()
		# return unicode(emen2.web.routing.execute('Error/main', db=None, error=e, location=location)).encode('utf-8')


	def render_error_security(self, location, e):
		# return mako.exceptions.html_error_template().render()
		return unicode(emen2.web.routing.execute('Error/auth', db=None, error=e, location=location)).encode('utf-8')


	def render_error_response(self, location, e):
		# return mako.exceptions.html_error_template().render()
		return unicode(emen2.web.routing.execute('Error/resp', db=None, error=e, location=location)).encode('utf-8')


	def _request_broken(self, failure, request, deferred):
		# Cancel the deferred.
		# The errback will be called, but not the callback.
		deferred.cancel()


	def _request_canceller(self, deferred, *args, **kwargs):
		# Do nothing -- my deferreds don't support cancellation at the moment
		pass
		# Create a failure to pass to the errback
		# failure = twisted.python.failure.Failure(exc_value=Exception("Cancelled request"))
		# deferred.errback(failure)


	##### Process HTTP request arguments #####

	def parse_args(self, request):
		# Massage the post and querystring arguments

		# Parse the content body for additional args:
		# Upload (twisted is broken), JSON POST, etc.
		args = self.parse_content(request)

		# Twisted provides all args as lists.
		# If we only got one value, pop it
		for k, v in request.args.items():
			if len(v) == 1:
				v = v[0]
			args[k] = v

		# Unicode.. grumble.. Web forms will submit UTF-8 encoded data; decode that
		args = self.parse_coerce_unicode(args)

		# HTTP arguments with '.' will be turned into dicts, e.g. 'child.key' -> child['key']
		args = self.parse_args_dict(args)

		return args


	def parse_args_dict(self, args):
		# Break keys with '.' into child dictionaries, recursively.
		# {'root': 1, 'child.key2': 2, 'child.key1.subkey1': 3, 'child.key1.subkey2':4}
		# ->
		# {'root': 1, 'child': {'key2': 2, key1: {'subkey1': 3, 'subkey2': 4}}}
		newargs = {}
		# Sort by key length so child dictionaries are created in order
		for k,v in sorted(args.items(), key=lambda x:len(x[0])):
			if '.' in k:
				cur = newargs
				s = k.split('.')
				for path in s[:-1]:
					if not cur.get(path):
						# Create child dict
						cur[path] = {}
					# Step down one level
					cur = cur[path]
					parent = path
				# Set the value for the leaf
				cur[s[-1]] = v
			else:
				newargs[k] = v
		return newargs


	def parse_content(self, request):
		'''This is called first, and should parse any content body for relevant View arguments.'''
		# Look for filename; if PUT, add a reference to the request.content file handle.
		files = []
		args = request.args

		if request.method == "PUT":
			# The param?..
			f = emen2.db.handlers.BinaryHandler.get_handler(
				filename=request.getHeader('x-file-name'), 
				param=request.getHeader('x-file-param'), 
				fileobj=request.content
				)
			files.append(f)

		elif request.method == "POST":
			# Fix Twisted's broken handling of multipart/form-data file uploads
			# Look for name=...;filename=... pairs in the multipart data
			request.content.seek(0)
			content = request.content.read()
			b = re.compile('name="(.+)"; filename="(.+)"')
			r = []
			try:
				r = b.findall(content)
			except:
				pass

			# Turn those pairs into emen2 File instances
			for param, filename in r:
				f = emen2.db.handlers.BinaryHandler.get_handler(
					param=param, 
					filename=filename
					)
				files.append(f)

			# And match those up with the parsed data
			isbdo = lambda x:(len(x)==17 and x.startswith('bdo:')) or not x
			for k, v in args.items():
				fs = filter(lambda x:x.param == k, files)
				if not fs:
					continue

				# Filter
				bdos, datas = emen2.util.listops.filter_partition(isbdo, v)
				args[k] = bdos

				if len(datas) != len(fs):
					raise ValueError, "Cannot upload empty file"

				# Move the data into the emen2 Files
				for f, filedata in zip(fs, datas):
					f.filedata = filedata

		# Make available to Views...
		self.request_files = files
		return args

		# Check for any JSON-encoded data in the POST body.
		# You should remove this method in anything that handles
		# big uploads.
		# postargs = {}
		# if request.method.lower() == "post":
		# 	request.content.seek(0)
		# 	content = request.content.read()
		# 	if content:
		# 		try:
		# 			postargs = jsonrpc.jsonutil.decode(content)
		# 		except:
		# 			pass
		# return postargs


	def parse_coerce_unicode(self, args, keyname=''):
		# This is terribly hacky, to recursively deal with various Unicode issues
		# To disable this for a class, override and return {}
		if isinstance(args, unicode):
			return args

		elif keyname == 'filedata':
			# See UploadResource.
			# This requirement might be changed or dropped in the future.
			return args

		elif hasattr(args, 'items'):
			newargs = {}
			for k, v in args.items():
				newargs[k] = self.parse_coerce_unicode(v, keyname=k)
			return newargs

		elif hasattr(args, '__iter__'):
			return [unicode(i, 'utf-8') for i in args]

		return unicode(args, 'utf-8')



	#### Routing registration methods #####

	@classmethod
	def add_matcher(cls, *matchers, **kwargs):
		'''Decorator used to add a matcher to an already existing class

		Named groups in matcher get passed as keyword arguments
		Other groups in matcher get passed as positional arguments
		Nothing else gets passed
		'''
		if not matchers:
			raise ValueError, 'A view must have at least one matcher'

		# Default name (this is usually the method name)
		def check_name(name):
			return 'main' if name.lower() == 'init' else name

		# Inner decorator method
		def inner(func):
			name = kwargs.pop('name', check_name(func.__name__))
			view = kwargs.pop('view', None)
			matcherinfo = getattr(func, 'matcherinfo', [])
			for count, m in enumerate(matchers):
				if count>0:
					name='%s/%s'%(name, count)
				matcherinfo.append((m, name, view))

			# save all matchers to the function
			func.matcherinfo = matcherinfo
			return func

		return inner


	@classmethod
	def register(self, cls):
		'''Register a View and connect it to a URL.
		- Multiple regular expressions can be registered per sub view
		- This also registers urls defined by the add_matcher decorator. In this case, the sub view name will default to the method name.
		- These can be reversed with self.ctxt.reverse('ClassName/alt1', param1='asd') and such
		'''

		# Register mtchers produced by the add_matcher decorator
		for func in cls.__dict__.values():
			for matcher in getattr(func, 'matcherinfo', []):
				matcher, name, view = matcher
				view = view or cls.__name__
				name = '%s/%s'%(view, name)
				with emen2.web.routing.Router().route(name=name, matcher=matcher, cls=cls, method=func) as url:
					pass
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




##### XML-RPC and JSON-RPC Resources #####

class XMLRPCResource(object):
	pass


class JSONRPCServerEvents(jsonrpc.server.ServerEvents):

	q = Queue.Queue()

	def processcontent(self, content, request):
		# Get the host from request
		# Get the ctxid from the post or querystring arguments
		ctxid, host = request.getCookie('ctxid'), request.getClientIP()
		ctxid = content.get('ctxid', ctxid)
		if 'params' in content:
			params = content['params']
			if hasattr(params, 'get'):
				ctxid = params.pop('ctxid', ctxid)
		self.ctxid = ctxid
		self.host = request.getClientIP()
		return content


	def callmethod(self, request, rpcrequest, db=None, ctxid=None, **kw):
		# Lookup the method and call
		if not db:
			raise Exception, "No DBProxy"

		if rpcrequest.method.startswith('_'):
			raise emen2.web.responsecodes.ForbiddenError, 'Method not accessible'

		elif rpcrequest.method == 'pp':
			return self.q.put((rpcrequest.args, rpcrequest.kwargs))

		elif rpcrequest.method == 'gg':
			return self.q.get()

		elif rpcrequest.method not in db._publicmethods:
			e = emen2.web.events.EventRegistry().event('pub.%s'%rpcrequest.method)
			methodresult = e(self.ctxid, request.getClientIP(), db=db, *rpcrequest.args, **rpcrequest.kwargs)

		else:
			# Start the DB with a write transaction
			# db._starttxn(write=db._checkwrite(rpcrequest.method))
			with db:
				db._setContext(self.ctxid, self.host)

				_method = rpcrequest.method.rpartition('.')[2]
				if _method == 'login':
					rpcrequest.kwargs['host'] = self.host

				methodresult = db._callmethod(rpcrequest.method, rpcrequest.args, rpcrequest.kwargs)
				if _method in set(['login', 'logout']):
					request.addCookie('ctxid', methodresult or '')

		return methodresult

	def defer(self, method, *a, **kw):
		# print "Deferring to DB Pool"
		deferred = emen2.web.server.pool.rundb(method, *a, **kw)
		return deferred



class JSONRPCResource(jsonrpc.server.JSON_RPC):
	eventhandler = JSONRPCServerEvents



__version__ = "$Revision$".split(":")[1][:-1].strip()
