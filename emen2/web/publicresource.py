from __future__ import with_statement
from emen2 import Database, ts
from emen2.Database import exceptions
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
			key=str(key)
			#print "process key %s"%key
			if val.isdigit():
				res = result.get(name, [])
				res.append(args[key][0])
				if len(res) == 1: setitem(name, res)
			elif val == 'json' and name is not '':
				value = self.__parse_jsonargs(args[key][0])
				#try:
				#	value=demjson.decode(args[key][0])
				#except:
				#	print "error decoding json: %s, %s"%(key, args[key][0])
				#	value=""
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
			for key in set(z.keys()) - set(["db","host","user","ctxid", "username", "pw"]):
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
	def getredirect(cls, name):
		redir = cls.redirects.get(name, False)
		result = None
		if redir != False:
			to, args, kwargs = redir  
			result = routing.URLRegistry.reverselookup(to, *args, **kwargs)
		return result
	
	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		#g.debug.msg('LOG_INIT', 'Redirect Registered::: FROM:',fro, 'TO:', to, args, kwargs)
		cls.redirects[fro] = (to, args, kwargs)
	
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
		#print "AUTH: GET CTXID COOKIE: %s"%ctxid
		## if the user requested to be logged in as a particular user
		## get the username and the password
		#print "cookie ctxid: %s"%ctxid
		username = args.get('username', [''])[0]
		pw = request.args.get('pw', [''])[0]
		## check credentials
		## if username is not associated with the ctxid passed, log user in
		authen.authenticate(username, pw, ctxid, host=host)
		ctxid, un = authen.get_auth_info()
		#print	 "==authen.get_auth_info=="
		#print ctxid,un
		if username and un != username:
			target = str.join('?', (router.reverselookup('Login'), 'msg=Invalid%%20Login&next=%s' % target))
		else:
			username = un
		if ctxid is not None:
			request.addCookie("ctxid", ctxid, path='/')
		target = '/%s/%s' % ('/'.join(request.prepath), target)
		return ctxid, target, authen


	def __getredirect(self, request, path):
		target = None
		redir = self.getredirect(path)
		if redir != None:
			qs = self.parse_uri(request.uri)[1]
			if qs:
				qs = str.join('', ('?', qs))
			
			target = '/%s%s%s' % (str.join('/', request.prepath), redir, qs)
		
		return target
	
	def finish_request(self, request):
		request.finish()
	
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
			
			path = '/%s' % str.join("/", request.postpath)
			if not path.endswith('/'): path = '%s/' % path
			target = self.__getredirect(request, path)
			
			# begin request handling
			method = listops.get(request.postpath, 0, '')
			callback, msg = make_callback(''), ''
			
			
			ctxid, tmp, authen = self.__authenticate(ts.db, request, ctxid, 
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
				callback = callback(db=ts.db, host=host, ctxid='', msg=tmp.get('msg', msg))
				return str(callback)
			else:
				#print tmp
				callback = routing.URLRegistry().execute(path, ctxid=ctxid, host=host, **tmp)
				
			def batch(*args, **kwargs):
				'''
				 helper function for batching... 
				 returns a list (result, mime-type)
				'''
				print "batch"
				a=list(callback(*args, **kwargs))
				print a
				return a

			d = threads.deferToThread(callback)
			d.addCallback(self._cbsuccess, request, ctxid, t=time.time())
			d.addErrback(self._ebRender, request, ctxid)
			return server.NOT_DONE_YET
		
		except Exception, e:
			self._ebRender(e, request, ctxid)
	
	
	
	def _cbsuccess(self, result, request, ctxid, t=0):#, t=0):
		"result must be a 2-tuple: (result, mime-type)"

#		try:
#			print "::: time 1 ---- %s"%(time.time()-t)
#		if 1:

		#very important do not change
		headers = {"content-type": "text/html; charset=utf-8",
				   "Cache-Control":"no-cache", "Pragma":"no-cache"}

		result, content_headers = result

		try:
			result = unicode(result).encode('utf-8')		
		except:
			result = str(result)		

		headers['content-type'] = content_headers
		headers['content-length'] = len(result)

		#print "HEADERS"
		#print headers

		request.setResponseCode(200)
		[request.setHeader(key, headers[key]) for key in headers]
		print "::: time total: %s"%(time.time()-t)


		if headers["content-type"] in ["image/jpeg","image/png"]:
			request.write(result)
		else:
			result = unicode(result).encode('utf-8')
			request.write(result)
			
		#except Exception, inst:
		#	print inst
		#	print "wtf?"

		#finally: 
		#	self.finish_request(request)
		#print "REQUEST FINISH"
		request.finish()
		#request.close()
		
		
	def _ebRender(self, failure, request, ctxid):
		try:
			g.debug.msg(g.LOG_ERR, 'ERROR---------------------------')
			g.debug.msg(g.LOG_ERR, failure)
			g.debug.msg(g.LOG_ERR, '---------------------------------')
			data = ''
			try:
				if isinstance(failure, BaseException): raise
				else: failure.raiseException()
			except (Database.exceptions.SecurityError, 
				Database.exceptions.SessionError, Database.exceptions.DisabledUserError), e:
					
				request.setResponseCode(401)
				args = {'uri':quote('/%s/' % str.join('/', request.prepath + request.postpath)),
						'msg': str(failure.value),  #quote( str.join('<br />', [str(failure.value)]) ),
						'db': ts.db,
						'ctxid': ctxid,
						'host': request.getClientIP()
					   }
				#data = "Permission Denied"
				#print args
				data = unicode(routing.URLRegistry.call_view('Login', **args)).encode("utf-8")
	
			except Exception, e:
				request.setResponseCode(500)
				data = g.templates.handle_error(e).encode('utf-8')

			request.setHeader('X-ERROR', ' '.join(str(failure).split()))
			request.setHeader('X-\x45\x64\x2d\x69\x73\x2d\x43\x6f\x6f\x6c', 
						   	'\x45\x64\x20\x69\x73\x20\x56\x65\x72\x79\x20\x43\x6f\x6f\x6c')
			request.write(data)
		finally: 
			self.finish_request(request)

		

