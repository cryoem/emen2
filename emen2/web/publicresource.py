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
import emen2.subsystems.routing
import emen2.subsystems.responsecodes
import emen2.Database.subsystems.exceptions
from authresource import render_security_error

import emen2.ts

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

class PublicView(Resource):

	isLeaf = True
	router = emen2.subsystems.routing.URLRegistry()



	def __init__(self):
		Resource.__init__(self)


	special_keys = set(["db","host","user","ctxid", "username", "pw"])

	def __parse_args(self, args, content=None):
		"""Break the request.args dict into something more usable

		This algorithm takes the list of keys and removes sensitive info, and
		other stuff that is passed in auto-magically decodes any params that end
		in _json with demjson and then groups all the params which end in
		_<number> together as a list.

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

			# split item:
			# e.g.
			# param___01
			# param___01___json
			# dict___key___dict

			p = str(key).split("___")
			name = p[0]

			if key=="":
				continue

			if len(p)==3:
				pos, format = p[1:3]

			elif len(p)==2:
				if p[1].isdigit():
					pos = p[1]
				else:
					format = p[1]

			sdict = {}
			key = str(key)
			value = args[key][0]

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



	# @classmethod
	# def __registerurl(cls, name, match, **methods):
	# 		'register a callback to handle a urls match is a compiled regex'
	# 		result = emen2.subsystems.routing.URL(name, match, **methods)
	# 		cls.router.register(result)
	# 		return result



	redirects = {}
	@classmethod
	def getredirect(cls, name):
		redir = cls.redirects.get(name, False)
		result = None
		if redir != False:
			to, args, kwargs = redir
			result = emen2.subsystems.routing.URLRegistry.reverselookup(to, *args, **kwargs)
		return result


	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		cls.redirects[fro] = (to, args, kwargs)


	# @classmethod
	# def register_url(cls, name, match, method='GET'):
	# 	"""decorator function used to register a function to handle a specified URL

	# 		arguments:
	# 			name -- the name of the url to be registered
	# 			match -- the regular expression that applies
	# 							as a string
	# 			cb -- the callback function to call
	# 	"""
	# 	g.log.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
	# 	def _reg_inside(cb):
	# 		kwargs = {method:cb}
	# 		cls.__registerurl(name, re.compile(match), **kwargs)
	# 		return cb
	# 	return _reg_inside



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
		request.content.seek(0)
		content = request.content.read()
		return self.render_GET(request, content=content)




	def render_GET(self, request, content=None):
		try:

			host = request.getClientIP()
			ctxid = request.getCookie("ctxid") or request.args.get("ctxid",[None])[0]

			request.postpath = filter(bool, request.postpath)
			request.postpath.append('')
			router = self.router
			make_callback = lambda string: lambda *x, **y: [string,'text/html;charset=utf8']

			path = '/%s' % str.join("/", request.postpath)
			target = self.__getredirect(None, request, path)

			if target is not None:
				g.log.msg('LOG_INFO', 'redirected %r to %r' % (request.uri, target))
				raise emen2.subsystems.responsecodes.HTTPMovedPermanently('', target)

			else:
				args = self.__parse_args(request.args, content=content)
				callback = emen2.subsystems.routing.URLRegistry().execute(path, method=request.method, fallback='GET', **args)

				d = threads.deferToThread(self._action, callback, ctxid=ctxid, host=host, path=path, method=request.method)
				d.addCallback(self._cbsuccess, request, t=time.time(), ctxid=ctxid, host=host)
				d.addErrback(self._ebRender, request, t=time.time(), ctxid=ctxid, host=host)

			return server.NOT_DONE_YET

		except BaseException, e:
			self._ebRender(e, request, ctxid=ctxid, host=host)




	# wrap db with context; view never has to see ctxid/host
	#@g.log.debug_func
	def _action(self, callback, db=None, ctxid=None, host=None, path=None, method='GET'):
		'''set db context, call view, and get string result
		put together to minimize amount of blocking code'''

		# this binds the Context to the DBProxy for the duration of the view

		with db._setcontext(ctxid,host):
			ret, headers = callback(db=db, method=method)
			if headers.get('content-type') != "image/jpeg":
				try:
					ret = unicode(ret).encode('utf-8')
				except Exception, e:
					g.log.msg('LOG_ERROR',"couldn't encode ret: mimetype %s, %s"%(headers.get('content-type'), e))

		return ret, headers




	def _cbsuccess(self, result, request, t=0, ctxid=None, host=None):
		"result must be a 2-tuple: (result, mime-type)"

		try:
			headers = {"content-type": "text/html; charset=utf-8",
							"Cache-Control":"no-cache", "Pragma":"no-cache"}

			result, content_headers = result

			headers.update(content_headers)
			#g.debug('headers', headers)
			headers['content-length'] = len(result)

			request.setResponseCode(200)
			[request.setHeader(key, headers[key]) for key in headers]

			g.debug("::: time total: %0.f ms"%(   (time.time()-t)*1000       )      )

			request.write(result)
			g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] "%(method)s %(path)s HTTP/-.-" 200 %(size)d' % dict(
					host = request.getClientIP(),
					time = time.ctime(),
					path = request.uri,
					size = len(result),
					method = request.method,
			))

		except BaseException, e:
			self._ebRender(e, request, ctxid=ctxid, host=host)

		request.finish()




	def _ebRender(self, failure, request, t=0, ctxid=None, host=None):
		g.log.msg('LOG_ERROR', failure)
		data = ''
		headers = {}
		response = 500

		try:
			try:
				if isinstance(failure, BaseException):raise
				else: failure.raiseException()

			except (emen2.Database.subsystems.exceptions.AuthenticationError,
					emen2.Database.subsystems.exceptions.SessionError,
					emen2.Database.subsystems.exceptions.DisabledUserError), e:
						request.addCookie("ctxid", '', path='/')
						response = 401
						data = render_security_error(request.uri, e)

			except (emen2.Database.subsystems.exceptions.SecurityError), e:

				#request.addCookie("ctxid", '', path='/')
				response = 401
				data = render_security_error(request.uri, e)

			except emen2.subsystems.responsecodes.HTTPResponseCode, e:
				response = e.code
				if e.msg:
					data = self.router['TemplateRender'](data='/errors/resp', title=e.title or e.__class__.__name__, msg=e.msg)
					data = unicode(data).encode('utf-8')
				headers.update(e.headers)


		except BaseException, e:
			data = g.templates.handle_error(e).encode('utf-8')


		[request.setHeader(key, headers[key]) for key in headers]

		request.setResponseCode(response)
		request.write(data)

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
