from __future__ import with_statement
from emen2 import Database, ts
from emen2.Database import exceptions
from emen2.subsystems import routing, auth
from emen2.util import listops
from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
from urllib import quote
import urlparse
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
		
		for key in set(args.keys()) - set(["db","host","user","ctxid"]):
			#name, _, val = key.rpartition('_')
			sdict = {} 
			value=args[key][0]
			
			p=str(key).split("___")
			name=p[0]
			format=None
			pos=None
			
			if key=="":
				continue
			
			if len(p)==3:
				format=p[1]
				pos=p[2]

			if len(p)==2:
				if p[1].isdigit():
					pos=p[1]
				else:
					format=p[1]
			
			sdict = {}
			key=str(key)

			#print "parse key: %s"%key
			#print "...format: %s, pos: %s"%(format, pos)
			#print "...value: %s"%value

			if format=="json":
				value = self.__parse_jsonargs(value)
				if name == 'args':
					sdict = value
					value = None
				result[name]=value

			elif format=="file":
				fn=filenames.get(key)
				value=(fn,value)
				result[name]=value
				
			if pos!=None:
				v2 = result.get(name, [])
				v2.insert(int(pos), value)
				result[name]=v2
			
			if format==None and pos==None:
				result[key]=value

				
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
	
	
	
	def __parse_filenames(self, content):
		b=re.compile('name="(.+)"; filename="(.+)"')
		ret={}
		return dict(b.findall(content))
	
	
	
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
		#if prnt:
		#	g.debug.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
		def _reg_inside(cb):
			#g.debug('MATCH: %s  <->  %s' % (name,match) )
			cls.__registerurl(name, re.compile(match), cb)
			return cb
		return _reg_inside
	
	
	
	def parse_uri(self, uri): 
		base, _, qs = uri.partition('?')
		return base, qs
	
	
	
	def __loginredir(self,request):
		target=request.args.get("redirect",["/db/home/"])[0]
		u=urlparse.urlsplit(target)
		du=list(u)
		#if u.hostname == None and u.port == None and u.scheme == None:
		du[0]="http"
		du[1]=request.getHeader("host").split(":")[0]
		if g.EMEN2PORT != 80:
			du[1]="%s:%s"%(du[1],g.EMEN2PORT)
		return urlparse.urlunsplit(du)		
	
	
	
	def __authenticate(self, db, request):
		'authenticate a user'

		args = request.args

		host = request.getClientIP()
		ctxid = request.getCookie("ctxid") or args.get("ctxid",[None])[0]
		username = args.get('username', [None])[0]
		pw = request.args.get('pw', [''])[0]
		target = None
		
		#authen = auth.Authenticator(db=db, host=host)
		#authen.authenticate(username, pw, ctxid, host=host)
		#ctxid, username = authen.get_auth_info()

		method = listops.get(request.postpath, 0, '')

		if method=="logout":
			request.addCookie("ctxid", '', path='/')	
			ctxid, username, target = None, None, None

		# raise exception if bad login; catch and return _ebRender
		elif method == "login" and username != None:
			ctxid = db.login(username, pw, host=host)
			request.addCookie("ctxid", ctxid, path='/')
			target = self.__loginredir(request)
			#print "LOGIN OK, target is %s"%target
			
		if ctxid == "": ctxid = None
		
		try:
			username, groups = db.checkcontext(ctxid,host)
		except:
			username = None
			ctxid = None

		return username, ctxid, target




	def __getredirect(self, target, request, path):
		redir = self.getredirect(path)
		if redir != None:
			qs = self.parse_uri(request.uri)[1]
			if qs:
				qs = str.join('', ('?', qs))
			
			target = '/%s%s%s' % (str.join('/', request.prepath), redir, qs)
		
		return target
	
	
	

	
	
	def render_POST(self, request):
		request.content.seek(0)
		content=request.content.read()
		return self.render_GET(request, content=content)
	
	
	
	
	def render_GET(self, request, content=None):


		host = request.getClientIP()
		request.postpath = filter(bool, request.postpath)
		router=self.router
		make_callback = lambda string: lambda *x, **y: [string,'text/html;charset=utf8']
		target = None

		try:
			username, ctxid, target = self.__authenticate(ts.db, request)
		except Exception, e:
			self._ebRender(e, request, ctxid=None)
			return server.NOT_DONE_YET


		path = '/%s' % str.join("/", request.postpath)
		if path[-1] != '/': path = '%s/' % path	
		target = self.__getredirect(target, request, path)


		if target is not None:
			#print "REDIR -> %s"%target
			request.redirect(target)
			request.finish()
			return server.NOT_DONE_YET
		
		
		print "\n\n:: web :: %s :: %s@%s"%(request.uri, username, host)

		args = self.__parse_args(request.args, content=content)		
		callback = routing.URLRegistry().execute(path, ctxid=ctxid, host=host, **args)
	
		d = threads.deferToThread(self._action, callback, ctxid=ctxid, host=host)
		d.addCallback(self._cbsuccess, request, ctxid=ctxid, t=time.time())
		d.addErrback(self._ebRender, request, ctxid=ctxid)
		return server.NOT_DONE_YET
	
	
	
	# wrap db with context; view never has to see ctxid/host
	def _action(self, callback, db=None, ctxid=None, host=None):
		db._clearcontext()
		db._setcontext(ctxid,host)
		return callback(db=db)
	
	
	
	def _cbsuccess(self, result, request, ctxid=None, t=0):#, t=0):
		"result must be a 2-tuple: (result, mime-type)"
			
		headers = {"content-type": "text/html; charset=utf-8",
				   "Cache-Control":"no-cache", "Pragma":"no-cache"}

		result, content_headers = result

		try:
			result = unicode(result).encode('utf-8')		
		except:
			result = str(result)		

		headers['content-type'] = content_headers
		headers['content-length'] = len(result)

		request.setResponseCode(200)
		[request.setHeader(key, headers[key]) for key in headers]
		print "::: time total: %s"%(time.time()-t)

		if headers["content-type"] in ["image/jpeg","image/png"]:
			request.write(result)
		else:
			#result = unicode(result).encode('utf-8')
			request.write(result)
			
		request.finish()
		

		
		
	def _ebRender(self, failure, request, ctxid=None):
		g.debug.msg(g.LOG_ERR, failure)
		data = ''

		try:
			if isinstance(failure, BaseException): raise failure
			else: failure.raiseException()
			
		except (Database.exceptions.SecurityError, Database.exceptions.AuthenticationError,
			Database.exceptions.SessionError, Database.exceptions.DisabledUserError), e:
			
			redirect=request.args.get("redirect",[request.uri])[0]
			if redirect == "/db/login/": redirect = "/db/home/"
			
			request.setResponseCode(401)
			args = {
					'redirect': quote(redirect), #str.join('/', request.prepath+request.postpath),  #quote('/%s/' %str.join('/', request.prepath+request.postpath)),
					'msg': 'Error: %s'%e,  #quote( str.join('<br />', [str(failure.value)]) ),
					'db': ts.db,
					'host': request.getClientIP(),
					'ctxid':None
				   }
				
			data = unicode(routing.URLRegistry.call_view('Login', **args)).encode("utf-8")

		except Exception, e:
			request.setResponseCode(500)
			data = g.templates.handle_error(e).encode('utf-8')

		request.setHeader('X-ERROR', ' '.join(str(failure).split()))
		#request.setHeader('X-\x45\x64\x2d\x69\x73\x2d\x43\x6f\x6f\x6c', 
		#			   	'\x45\x64\x20\x69\x73\x20\x56\x65\x72\x79\x20\x43\x6f\x6f\x6c')

		request.write(data)
		request.finish()

		#finally: 
		#	self.finish_request(request)