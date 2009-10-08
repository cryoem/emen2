from __future__ import with_statement

import urlparse
import urllib2
import demjson
import emen2.globalns
import re
import time


from emen2 import Database
from emen2 import ts
from emen2.Database import exceptions
from emen2.subsystems import routing
import emen2.subsystems.responsecodes
from emen2.util import listops


from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
from urllib import quote



g = emen2.globalns.GlobalNamespace('')

class PublicView(Resource):

	isLeaf = True
	router = routing.URLRegistry()



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

		if content:
			filenames = self.__parse_filenames(content)

		for key in set(args.keys()) - self.special_keys:
			sdict = {}
			format=None
			pos=None


			p=str(key).split("___")
			name=p[0]

			if key=="":
				continue

			if len(p)==3:
				format, pos =p[1:3]

			if len(p)==2:
				if p[1].isdigit():
					pos=p[1]
				else:
					format=p[1]

			sdict = {}
			key=str(key)

			value=args[key][0]
			if format=="json":
				value = self.__parse_jsonargs(value)
				if name == 'args':
					sdict = dict((k.encode('utf-8'), v) for k,v in value.iteritems())
					value = None
				else:
					result[name]=value
			# What is the utility of this?
			elif format=="file":
				fn=filenames.get(key)
				value=(fn,value)
				result[name]=value

			if pos is not None:
				v2 = result.get(name, [])
				v2.insert(int(pos), value)
				result[name]=v2
			elif format is None:
				result[key]=value

			result.update(sdict)

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



	@classmethod
	def __registerurl(cls, name, match, cb):
			'register a callback to handle a urls match is a compiled regex'
			result = routing.URL(name, match, cb)
			cls.router.register(result)
			return result



	redirects = {}
	@classmethod
	def getredirect(cls, name):
		redir = cls.redirects.get(name, False)
		result = None
		if redir != False:
			to, args, kwargs = redir
			result = routing.URLRegistry.reverselookup(to, *args, **kwargs)
		return result


	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		cls.redirects[fro] = (to, args, kwargs)


	@classmethod
	def register_url(cls, name, match):
		"""decorator function used to register a function to handle a specified URL

			arguments:
				name -- the name of the url to be registered
				match -- the regular expression that applies
								 as a string
				cb -- the callback function to call
		"""
		g.debug.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
		def _reg_inside(cb):
			cls.__registerurl(name, re.compile(match), cb)
			return cb
		return _reg_inside



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
		#g.debug('npath 2-> (', npath, ') base -> (', base, ') path -> (', path, ')')

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
		content=request.content.read()
		return self.render_GET(request, content=content)




	def render_GET(self, request, content=None):
		try:
			host = request.getClientIP()
			ctxid = request.getCookie("ctxid") or request.args.get("ctxid",[None])[0]
			#g.debug("ctxid is: %s"%ctxid)

			request.postpath = filter(bool, request.postpath)
			request.postpath.append('')
			router=self.router
			make_callback = lambda string: lambda *x, **y: [string,'text/html;charset=utf8']

			path = '/%s' % str.join("/", request.postpath)
			target = self.__getredirect(None, request, path)
			# g.debug('redirect target --> (', target, ')')

			if target is not None:
				#request.redirect(target)
				g.debug.msg('LOG_INFO', 'redirected (%s) to (%s)' % (request.uri, target))
				raise emen2.subsystems.responsecodes.HTTPMovedPermanently('', target)
				request.finish()

			else:
				#g.debug("\n\n:: web :: %s :: %s"%(request.uri, host))

				args = self.__parse_args(request.args, content=content)
				callback = routing.URLRegistry().execute(path, **args)

				d = threads.deferToThread(self._action, callback, ctxid=ctxid, host=host, path=path)
				d.addCallback(self._cbsuccess, request, t=time.time(), ctxid=ctxid, host=host)
				d.addErrback(self._ebRender, request, t=time.time(), ctxid=ctxid, host=host)

			return server.NOT_DONE_YET

		except BaseException, e:
			self._ebRender(e, request, ctxid=ctxid, host=host)




	# wrap db with context; view never has to see ctxid/host
	#@g.debug.debug_func
	def _action(self, callback, db=None, ctxid=None, host=None, path=None):
		'''set db context, call view, and get string result
		put together to minimize amount of blocking code'''

		# this binds the Context to the DBProxy for the duration of the view

		g.debug.msg("LOG_INFO", "====== PublicView action: path %s ctxid %s host %s"%(path, ctxid, host))


		db._starttxn()

		db._setcontext(ctxid,host)

		#g.debug('View transaction started')

		try:
			ret, headers = callback(db=db)
			ret = unicode(ret).encode('utf-8')
		except Exception, e:
			#g.debug('View transaction aborted')
			db._aborttxn()
			raise
		else:
			#g.debug('View transaction committed')
			db._committxn()

		return ret, headers




	def _cbsuccess(self, result, request, t=0, ctxid=None, host=None):
		"result must be a 2-tuple: (result, mime-type)"

		try:
			headers = {"content-type": "text/html; charset=utf-8",
					 "Cache-Control":"no-cache", "Pragma":"no-cache"}

			result, content_headers = result

			headers['content-type'] = content_headers.get('content-type')
			headers['content-length'] = len(result)

			request.setResponseCode(200)
			[request.setHeader(key, headers[key]) for key in headers]
			g.debug("::: time total: %0.f ms"%(   (time.time()-t)*1000       )      )

			request.write(result)
			g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s 200 %(size)d' % dict(
					host = request.getClientIP(),
					time = time.ctime(),
					path = request.uri,
					size = len(result)
			))
		except BaseException, e:
			self._ebRender(e, request, ctxid=ctxid, host=host)

		request.finish()




	def _ebRender(self, failure, request, t=0, ctxid=None, host=None):
		g.debug.msg(g.LOG_ERR, failure)
		data = ''
		headers = {}
		response = 500
		try:
			try:
				if isinstance(failure, BaseException): raise; failure
				else: failure.raiseException()
			except (Database.exceptions.AuthenticationError,
						Database.exceptions.SecurityError,
						Database.exceptions.SessionError,
						Database.exceptions.DisabledUserError), e:
				response = 401
				args = {'redirect': request.uri, 'msg': str(e),
							'db': ts.db, 'ctxid': ctxid,
							'host': request.getClientIP()}

				p = emen2.TwistSupport_html.public.login.Login(**args)
				data = unicode(p.get_data()).encode("utf-8")

			except emen2.subsystems.responsecodes.NotFoundError, e:
					response = e.code
					data = self.router['TemplateRender'](db=ts.db, ctxid=None, host=None, data='/notfound', EMEN2WEBROOT=g.EMEN2WEBROOT, msg=request.uri)
					data = unicode(data).encode('utf-8')

			except emen2.subsystems.responsecodes.HTTPResponseCode, e:
				response = e.code
				headers.update(e.headers)


		except BaseException, e:
			data = g.templates.handle_error(e).encode('utf-8')


		[request.setHeader(key, headers[key]) for key in headers]

		request.setResponseCode(response)
		request.write(data)
		#g.debug.msg('LOG_INFO', 'response -> (%r)' % response)
		g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(data)
		))
		request.finish()
