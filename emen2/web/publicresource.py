# $Author$ $Revision$
from __future__ import with_statement

import urllib2
import demjson
import re
import time
import collections

from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server

# emen2 imports
import emen2.web.routing
import emen2.web.responsecodes
import emen2.Database.exceptions
from authresource import render_security_error

# Load our custom threadpool
import emen2.web.threadpool

import emen2.Database.config
g = emen2.Database.config.g()



class PublicView(Resource):

	isLeaf = True
	router = emen2.web.routing.URLRegistry()
	special_keys = set(["db","host","user","ctxid", "username", "pw"])

	def __init__(self):
		Resource.__init__(self)


	def __parse_args(self, args, content=None):
		"""Break the request.args dict into something more usable

		This takes the list of keys and removes context/sensitive info, and
		other stuff that is passed in auto-magically decodes any params that end
		in ___json with demjson and then groups all the params which end in
		___<number> together as a list.

		NOTE: we should probably make sure that the _## parameters have
		sequential numbers
		"""

		result = {}
		filenames = {}
		sdicts = collections.defaultdict(dict)

		if content:
			filenames = self.__parse_filenames(content)

		for key in set(args.keys()) - self.special_keys:
			sdict = {}
			format = None
			pos = None
			key = str(key)
			value = args[key][0]
			p = key.split("___")
			name = p[0]

			if key == "":
				continue

			if len(p) == 3:
				pos, format = p[1:3]

			elif len(p) == 2:
				if p[1].isdigit():
					pos = p[1]
				else:
					format = p[1]

			# print "key: %s, format: %s, filenames: %s, name: %s"%(key, format, filenames, name)

			if format == "json":
				value = self.__parse_jsonargs(value)
				if name == 'args':
					sdict = dict((k.encode('utf-8'), v) for k,v in value.iteritems())
					value = None
				else:
					result[name] = value

			elif format == "file":
				fn = filenames.get(key)
				value = [fn,value]
				result[name] = value
				# print "got POST file: %s, %s MB"%(fn, len(value[1])/float(1024*1024))

			elif format == "dict":
				sdicts[name][pos] = value

			if pos is not None and format != "dict":
				pos = int(pos)
				v2 = result.get(name, [])
				v2.insert(pos, value)
				result[name] = v2

			elif format is None:
				result[key] = value

			result.update(sdict)

		for k,v in sdicts.items():
			result[k] = v

		return result



	def __parse_jsonargs(self,content):
		'decode a json string'
		ret={}
		z=demjson.decode(content)
		if hasattr(z, 'args'):
			for key in set(z.keys()) - self.special_keys:
				ret[str(key)]=z[key]
		else:
			ret = z
		return ret



	def __parse_filenames(self, content):
		b=re.compile('name="(.+)"; filename="(.+)"')
		ret={}
		return dict(b.findall(content))



	redirects = {}
	@classmethod
	def getredirect(cls, name):
		# g.debug(cls.redirects)
		redir = cls.redirects.get(name, False)
		result = None
		if redir != False:
			to, args, kwargs = redir
			result = emen2.web.routing.URLRegistry.reverselookup(to, *args, **kwargs)
		return result



	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		pass
		#cls.redirects[fro] = (to, args, kwargs)



	def parse_uri(self, uri):
		base, _, qs = uri.partition('?')
		return base, qs



	def __getredirect(self, target, request, path):
		npath = None
		base,qs = self.parse_uri(request.uri)

		#no trailing slash
		if base[-1] != '/': npath = '%s/' % path

		#too many slashes
		if urllib2.unquote(base)[3:] != path: npath = path

		#registered redirect
		redir = self.getredirect(npath or path)
		if redir != None: npath = redir

		#redirect if necessary
		if npath is not None:
			if qs: qs = str.join('', ('?', qs))
			target = '%s/%s%s%s' % (g.EMEN2WEBROOT,str.join('/', request.prepath), npath, qs)

		#return new target or None for no redirect
		return target



	def render_POST(self, request):
		"""We want to grab all the info in the request body and pass to render_GET"""
		request.content.seek(0)
		content = request.content.read()
		return self.render_GET(request, content=content)



	def render_GET(self, request, content=None):
		try:

			# Get host/ctxid
			host = request.getClientIP()
			ctxid = request.getCookie("ctxid") or request.args.get("ctxid",[None])[0]

			# Get path
			request.postpath = filter(bool, request.postpath)
			request.postpath.append('')

			path = '/%s' % str.join("/", request.postpath)
			target = self.__getredirect(None, request, path)


			# Redirect if necessary
			if target is not None:
				g.log.msg('LOG_INFO', 'redirected %r to %r' % (request.uri, target))
				raise emen2.web.responsecodes.HTTPMovedPermanently('', target)


			# Parse args and get View class
			args = self.__parse_args(request.args, content=content)
			callback = emen2.web.routing.URLRegistry().execute(path, method=request.method, fallback='GET', **args)

			d = threads.deferToThread(self._action, callback, ctxid=ctxid, host=host, path=path, method=request.method)
			d.addCallback(self._cbsuccess, request, t=time.time(), ctxid=ctxid, host=host)
			d.addErrback(self._ebRender, request, t=time.time(), ctxid=ctxid, host=host)

			# Deferred
			return server.NOT_DONE_YET


		except BaseException, e:
			self._ebRender(e, request, ctxid=ctxid, host=host)




	def _action(self, callback, db=None, ctxid=None, host=None, path=None, method='GET'):
		'''set db context, call view, and get string result
		put together to minimize amount of blocking code'''

		# this binds the Context to the DBProxy for the duration of the view
		with db._setContext(ctxid,host):
			ret, headers = callback(db=db, method=method)
			# ian: todo: fix this
			if headers.get('content-type') != "image/jpeg":
				try:
					ret = unicode(ret).encode('utf-8')
				except Exception, e:
					g.log.msg('LOG_ERROR',"couldn't encode result: mimetype %s, %s"%(headers.get('content-type'), e))

		return ret, headers




	def _cbsuccess(self, result, request, t=0, ctxid=None, host=None):
		"result must be a 2-tuple: (result, mime-type)"

		headers = {
			"content-type": "text/html; charset=utf-8",
			"Cache-Control":"no-cache",
			"Pragma":"no-cache"
			}

		result, content_headers = result
		headers.update(content_headers)
		headers['content-length'] = len(result)
		request.setResponseCode(200)
		[request.setHeader(key, headers[key]) for key in headers]

		# g.debug("Request time: %0.f ms"%((time.time()-t)*1000))

		# send result to client
		request.write(result)

		# write in an access_log like format
		g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] "%(method)s %(path)s HTTP/-.-" 200 %(size)d %(t)d' % dict(
				host = request.getClientIP(),
				time = time.ctime(),
				path = request.uri,
				size = len(result),
				method = request.method,
				t = (time.time()-t)*1000000
		))

		# except BaseException, e:
		# 	self._ebRender(e, request, ctxid=ctxid, host=host)

		request.finish()




	def _ebRender(self, failure, request, t=0, ctxid=None, host=None):
		g.log.msg('LOG_ERROR', failure)
		data = ''
		headers = {}
		response = 500

		try:
			try:
				if isinstance(failure, BaseException):
					raise
				else: failure.raiseException()

			except (emen2.Database.exceptions.AuthenticationError,
					emen2.Database.exceptions.SessionError,
					emen2.Database.exceptions.DisabledUserError), e:
						request.addCookie("ctxid", '', path='/')
						response = 401
						data = render_security_error(request.uri, e)

			except (emen2.Database.exceptions.SecurityError), e:
				response = 401
				data = render_security_error(request.uri, e)

			except emen2.web.responsecodes.HTTPResponseCode, e:
				response = e.code
				if e.msg:
					data = self.router['TemplateRender'](data='/errors/resp', title=e.title or e.__class__.__name__, msg=e.msg)
					data = unicode(data).encode('utf-8')
				headers.update(e.headers)


		except BaseException, e:
			data = g.templates.handle_error(e).encode('utf-8')


		[request.setHeader(key, headers[key]) for key in headers]
		request.setResponseCode(response)

		# write error page to client
		request.write(data)

		# access_log
		g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] "%(method)s %(path)s HTTP/-.-" %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(data),
			method = request.method,
		))

		request.finish()



__version__ = "$Revision$".split(":")[1][:-1].strip()
