from __future__ import with_statement
from emen2 import Database, ts
from emen2.subsystems import routing, auth
from emen2.util import listops
from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
from urllib import quote
import demjson
import emen2.globalns
import re
import time

try: set
except:
	from sets import Set as set

g = emen2.globalns.GlobalNamespace('')

class PublicView(Resource):

	isLeaf = True
	router = routing.URLRegistry()
	
	def __init__(self):
		Resource.__init__(self)
	
	def __parse_args(self, args):
		"""Break the request.args dict into something more usable
		
		This algorithm takes the list of keys and removes sensitive info, and 
		other stuff that is passed in auto-magically decodes any params that end 
		in _json with demjson and then groups all the params which end in 
		_<number> together as a list.
		
		NOTE: we should probably make sure that the _## parameters have 
		      sequential numbers
		"""
		result = {}
		def setitem(name, val):
			result[name] = val
		
		for key in set(args.keys()) - set(["db","host","user","ctxid", 
										   "username", "pw"]):
			name, _, val = key.rpartition('_')
			sdict = {}   
			if val.isdigit():
				res = result.get(name, [])
				res.append(args[key][0])
				if len(res) == 1: setitem(name, res)
			elif val == 'json' and name is not '':
				value = self.__parse_jsonargs(args[key][0])
				if name == 'args': sdict = value
				else: result[name] = value
			else:
				result[key] = args[key][0]
			result.update(sdict)
		return result
	
	def __parse_jsonargs(self,content):
		'decode a json string'
		ret={}
		try:
			z=demjson.decode(content)
			for key in set(z.keys()) - set(["db","host","user","ctxid", 
										    "username", "pw"]):
				ret[str(key)]=z[key]
		except: pass	  
		return ret
	
	
	@classmethod
	def __registerurl(cls, name, match, cb):
			'register a callback to handle a urls match is a compiled regex'
			result = routing.URL(name, match, cb)
			cls.router.register(result)
			return result
	
	redirects = {}
	@classmethod
	def getredirect(cls, name): return cls.redirects.get(name, False)
	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		cls.redirects[fro] = cls.router.reverselookup(to, *args, **kwargs)
	
	@classmethod
	def register_url(cls, name, match, prnt=True):
		"""decorator function used to register a function to handle a specified URL
		
		
			arguments:
				name -- the name of the url to be registered
				regex -- the regular expression that applies 
								 as a string
				cb -- the callback function to call
		"""
		if prnt:
			g.debug.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
		def _reg_inside(cb):
			g.debug('%s ::matched by:: %s' % (name,match) )
			cls.__registerurl(name, re.compile(match), cb)
			return cb
		return _reg_inside
	
	def parse_uri(self, uri): 
		base, _, qs = uri.partition('?')
		return base, qs
	
	def __authenticate(self, db, request, ctxid, host, args, router, target):
		'authenticate a user'
		authen = auth.Authenticator(db=db, host=host)
		## if the browser has a ctxid cookie, get it
		ctxid = request.getCookie("ctxid")
		## if the user requested to be logged in as a particular user
		## get the username and the password
		username = args.get('username', [''])[0]
		pw = request.args.get('pw', [''])[0]
		## check credentials
		## if username is not associated with the ctxid passed, log user in
		authen.authenticate(username, pw, ctxid)
		ctxid, un = authen.get_auth_info()
		if username and un != username:
			target = str.join('?', (router.reverselookup('Login'), 'msg=Invalid%%20Login&next=%s' % target))
		else:
			username = un
		if ctxid is not None:
			request.addCookie("ctxid", ctxid, path='/')
		return ctxid, target, authen


	def __getredirect(self, request, path):
		target = None
		
		if not bool(request.postpath):
			url, qs = self.parse_uri(request.uri)
			url = str.join('', (url, 'home/'))
			# get redirection of target if any
			url = self.redirects.get(url, url)
			target = (url, qs)
			target = '%s' % (str.join('?', target))
		
		redir = self.redirects.get(path, None)
		if redir != None:
			qs = self.parse_uri(request.uri)[1]
			if qs:
				qs = str.join('', ('?', qs))
			
			target = '/%s%s%s' % (str.join('/', request.prepath), redir, qs)
		
		return target
	
	def finish_request(self, request): request.finish()
	
	def render(self, request):
		ctxid, host = None, request.getClientIP()
		args = request.args
		
		request.postpath = filter(bool, request.postpath)
		
		router=self.router
		make_callback = lambda string: lambda *x, **y: [string,'text/html;charset=utf8']
		try:
			# redirect special urls
			if self.parse_uri(request.uri)[0][-1] != '/': # special case, hairy to refactor
				target = addSlash(request)
				return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
			
			path = '/%s/' % str.join("/", request.postpath)
			target = self.__getredirect(request, path)
			
			# begin request handling
			method = listops.get(request.postpath, 0, '')
			callback, msg = make_callback(''), ''
			
			
			ctxid, target, authen = self.__authenticate(ts.db, request, ctxid, 
													    host, args, router, 
													    target)
			
			# redirect must occur after authentication so the
			# ctxid cookie can be sent to the browser on a  
			# POST request
			if target is not None:
				#redirects must not be unicode
				#NOTE: should URLS use punycode: http://en.wikipedia.org/wiki/Punycode ?
				return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
			
			print "\n\n=== web request === %s :: %s :: %s"%(method, args, ctxid)
			
			tmp = self.__parse_args(args)
			if method == "logout":
				authen.logout(ctxid)
				return redirectTo('/db/home/', request).encode('utf-8')
			elif method == "login":
				callback = router.execute('/login/', uri=tmp.get('uri', '/db/home/'))
				callback = callback(db=ts.db, host=request.host, ctxid='', msg=tmp.get('msg', msg))
				return str(callback)
			else:
				callback = routing.URLRegistry().execute(path, ctxid=ctxid, host=host, **tmp)
				
			def batch(*args, **kwargs):
				'''
				 helper function for batching... 
				 returns a list (result, mime-type)
				'''
				return list(callback(*args, **kwargs))


			d = threads.deferToThread(batch)
			d.addCallback(self._cbsuccess, request, ctxid, t=time.time())
			d.addErrback(self._ebRender, request, ctxid)
	
			return server.NOT_DONE_YET
		
		except Exception, e:
			self._ebRender(e, request, ctxid)
	
	def _cbsuccess(self, result, request, ctxid, t=0):#, t=0):
		"result must be a 2-tuple: (result, mime-type)"
		try:
#			print "::: time 1 ---- %s"%(time.time()-t)
			t1=time.time()
			headers = {"content-type": "text/html; charset=utf-8",
					   "Cache-Control":"no-cache", "Pragma":"no-cache"}
	
			request.setResponseCode(200)
			[request.setHeader(key, headers[key]) for key in headers]
			try: 
				result, content_headers = result
				headers['content_type'] = content_headers
			except ValueError: pass
			headers['content-length'] = len(result)
	
			print "::: time total: %s"%(time.time()-t)
			request.write(unicode(result).encode('utf-8'))
#			print "::: time 2 ---- %s"%(time.time()-t1)
		finally: self.finish_request(request)
		
		
	def _ebRender(self, failure, request, ctxid):
		try:
			g.debug.msg(g.LOG_ERR, 'ERROR---------------------------')
			g.debug.msg(g.LOG_ERR, failure)
			g.debug.msg(g.LOG_ERR, '---------------------------------')
			request.setResponseCode(500)
			
			try:
				if isinstance(failure, BaseException): raise
				else: failure.raiseException()
			except (Database.SecurityError, Database.SessionError):
				uri = '/%s%s' % ( str.join('/', request.prepath), routing.URLRegistry.reverselookup(name='Login') )
				args = (('uri', quote('/%s/' % str.join('/', request.prepath + request.postpath))),
							  ('msg', quote( str.join('<br />', [str(failure.value)]) ) )
							 )
				args = ( str.join('=', elem) for elem in args )
				args = str.join('&', args)
				uri = str.join('?', (uri,args))
				request.write(redirectTo(uri, request).encode("utf-8"))
	
			except Exception, e:
				request.write(g.templates.handle_error(e).encode('utf-8'))
		finally: self.finish_request(request)

