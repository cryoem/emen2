# $Id$

import time
import random
import traceback

import twisted.internet
import twisted.web.static
import twisted.web.resource
import twisted.python.failure

import jsonrpc.jsonutil
import mako.exceptions

# emen2 imports
import emen2.db.config
import emen2.db.exceptions
import emen2.util.loganalyzer
import emen2.web.events
import emen2.web.routing
import emen2.web.responsecodes

# We need the threadpool
import emen2.web.server


##### Manipulation and filter of HTTP arguments #####

def cookie_expire_time(self):
	return time.strftime("%a, %d-%b-%Y %H:%M:%S PST", time.localtime(time.time()+604800))


def parse_args_dict(args):
	# Break keys with '.' into child dictionaries.
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


def parse_content(request):
	# Check for any JSON-encoded data in the POST body.
	# You should remove this method in anything that handles
	# big uploads.
	postargs = {}
	if request.method.lower() == "post":
		request.content.seek(0)
		content = request.content.read()
		if content:
			try:
				postargs = jsonrpc.jsonutil.decode(content)
			except:
				pass
	return {'jsonrequest': postargs}


def coerce_unicode(args, keyname=''):
	# This is terribly hacky, to recursively deal with various Unicode issues
	if isinstance(args, unicode):
		return args

	elif keyname == 'filedata':
		# See UploadResource. 
		# This requirement might be changed or dropped in the future.
		return args

	elif hasattr(args, 'items'):
		newargs = {}
		for k, v in args.items():
			newargs[k] = coerce_unicode(v, keyname=k)
		return newargs

	elif hasattr(args, '__iter__'):
		return [unicode(i, 'utf-8') for i in args]

	return unicode(args, 'utf-8')



# Special thanks to this Dave Peticolas's blog post for 
# helping sort out my deferred cancel/callback/errback situation:
# http://krondo.com/?p=2601

class EMEN2Resource(object):
	"""Base resource for EMEN2. Handles proper parsing of HTTP request arguments
	into a format that plays well with EMEN2, and contains all the common features
	of setting up the deferreds, threadpool, handling errors, etc.
	"""

	isLeaf = True
	events = emen2.web.events.EventRegistry()
	
	##### Process HTTP request arguments #####
	
	def parse_args(self, request):
		# Massage the post and querystring arguments
		args = {}		

		# If we only got one value, pop it
		for k, v in request.args.items():
			if len(v) == 1:
				v = v[0]
			args[k] = v

		args = coerce_unicode(args)
		args = parse_args_dict(args)
		args.update(parse_content(request))
		return args
	
	
	##### Resource interface #####
	
	def render(self, request, method=None):
		# In the future, there may be several emen2resource classes:
		# synchronous, with and without db
		# asynchronous, with and without db	
		method = method or (lambda x:None)
		args = self.parse_args(request)
		ctxid = request.getCookie("ctxid") or args.get('ctxid')
		host = request.getClientIP()
		t = time.time()

		self.events.event('web.request.received')(request, ctxid, args, host)
		
		# print "Render: %s"%request.path		
		deferred = emen2.web.server.pool.runtxn(
			self._render_dbtxn,
			method,
			ctxid = ctxid,
			host = host,
			args = args)
			
		deferred.addCallback(self.render_cb, request, t=t)
		deferred.addErrback(self.render_eb, request, t=t)
		request.notifyFinish().addErrback(self._request_broken, request, deferred)		
		return twisted.web.static.server.NOT_DONE_YET				


	def _render_dbtxn(self, method, db, ctxid, host, args):
		self.db = db
		with self.db:
			self.db._setContext(ctxid,host)
			result = method(self, **args)
		return result
		

	# Success callback
	def render_cb(self, result, request, t=0, **_):
		# If a result was passed, use that. Otherwise use str(self)
		result = str(self)

		# Filter the headers
		headers = {}
		headers.update(self.headers)
		headers = dict( (k,v) for k,v in headers.iteritems() if v != None )
		if result is not None:
			headers['Content-Length'] = len(result)

		# Redirect if necessary
		if headers.get("Location"):
			request.setResponseCode(302)

		[request.setHeader(key, str(headers[key])) for key in headers]

		# Set the session ctxid
		setctxid = headers.get('X-Ctxid')
		if setctxid != None:
			request.addCookie("ctxid", setctxid, path='/')

		# Send result to client
		if result is not None:
			request.write(result)
			
		request.finish()
		self.events.event('web.request.succeed')(request, setctxid, headers, result)

		
	def render_eb(self, failure, request, t=0, **_):		
		e, data = '', ''
		headers = {}

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
		#return unicode(emen2.web.routing.execute('Error/main', db=None, error=e, location=location)).encode('utf-8')


	def render_error_security(self, location, e):
		return mako.exceptions.html_error_template().render()
		# return unicode(emen2.web.routing.execute('Error/auth', db=None, error=e, location=location)).encode('utf-8')
		
		
	def render_error_response(self, location, e):
		return mako.exceptions.html_error_template().render()
		# return unicode(emen2.web.routing.execute('Error/resp', db=None, error=e, location=location)).encode('utf-8')


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



__version__ = "$Revision$".split(":")[1][:-1].strip()
