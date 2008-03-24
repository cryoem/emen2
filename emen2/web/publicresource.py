from cgi import escape
from emen2 import ts
from emen2.subsystems import routing
from sets import Set
from emen2 import Database
from loglevels import LOG_ERR
# TODO: investigate the need for debug in g
import g
import re

#twisted imports
from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
from twisted.web import error
###


class PublicView(Resource):
	isLeaf = True
	redirects = {}
	
	@classmethod
	def getredirect(cls, name):
		return cls.redirects.get(name, False)
	
	@classmethod
	def register_redirect(cls, fro, to, *args, **kwargs):
		cls.redirects[fro] = routing.URLRegistry.reverselookup(to, *args, **kwargs)
	
	@classmethod
	def __registerurl(cls, name, match, cb):
			'''register a pattern to select urls
	
			arguments:
					name -- the name of the url to be registered
					regex -- the regular expression that applies 
									 as a string
					cb -- the callback function to call
			'''
			return routing.URL(name, re.compile(match), cb)
	
	@classmethod
	def register_url(cls, name, match):
			def _reg_inside(cb):
				g.debug('%s ::matched by:: %s' % (name,match) )
				cls.__registerurl(name, re.compile(match), cb)
				return cb
			return _reg_inside
	
	
	def login(self,uri,msg=""):
			page = """
			<h2>Please login:</h2>
			<h3>%s</h3>
			<div id="zone_login">
	
				<form action="%s" method="POST">
				   <div>
						<div>Username:</div>
						<div><input type="text" name="username" /></div>
					</div>
					<div>
						<div>Password:</div>
						<div><input type="password" name="pw" /></div>
					</div>
					<input type="submit" value="submit" />
	
				</form>
			</div>"""%(msg,uri)
			return page, 'text/html'
				
	
	def render(self, request):
		try:
			if request.uri.split('?')[0][-1] != '/':
				return redirectTo(addSlash(request), request)

			request.postpath = filter(bool, request.postpath)
			if not bool(request.postpath):
				return redirectTo(request.uri+'home/', request)
			
			def make_callback(string):
				cb = lambda *x, **y: string
				return cb
			
			host = request.getClientIP()
			args = request.args
			
			
			method = request.postpath[0]
			ctxid = request.getCookie("ctxid")
			loginmsg = ""
			callback = make_callback('')
			
			try:
				ts.db.checkcontext(ctxid,host)
			except Exception, e:
				if ctxid != None:	
					loginmsg = "Session expired"
					ctxid = None
				else:
					g.debug("EXCEPTION <%s>" % repr(e) )
			
			if ctxid == None:
				# force login, or generate anonymous context
				if request.args.has_key("username") and request.args.has_key("pw"):
					try:
						# login and continue with this ctxid
						ctxid = ts.db.login(request.args["username"][0], request.args["pw"][0], host)
						request.addCookie("ctxid", ctxid, path='/')
					except:
						# bad login
						ctxid = None
						method = "login"
						loginmsg = "Please try again."
				else:
					ctxid = ts.db.login("","",host)
						
			if method == "login":			
				callback = make_callback(self.login(uri=request.uri,msg=loginmsg))
			
			elif method == "logout":
				ts.db.deletecontext(ctxid)
				callback = make_callback("""<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
															<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">""")
			else:
				tmp = {}
				for key in Set(args.keys()) - Set(["db","host","user","ctxid"]):
					tmp.update(  {key:str.join('\t', args[key])} )
				
				path = '/%s/' % str.join("/", request.postpath)
				print path
				path = self.redirects.get(path, path)
				
				g.debug( 'request: %s, args: %s' % (request, tmp) )
				callback = routing.URLRegistry().execute(path, **tmp)

			g.debug('going to thread with context id %s user %s'%(ctxid,ts.db.checkcontext(ctxid,host)))
			d = threads.deferToThread(callback, ctxid=ctxid, host=host)
			d.addCallback(self._cbsuccess, request, ctxid)
			d.addErrback(self._ebRender, request, ctxid)
	
			return server.NOT_DONE_YET
		except Exception, e:
			error.ErrorPage(e, str(e), str(e)).render(request)
	
	def _cbsuccess(self, result, request, ctxid):
		"result must be a 2-tuple: (result, mime-type)"
		
		def set_headers(headers):
			for key in headers:
				request.setHeader(key, headers[key])
		try:
			result, mime_type = result
		except ValueError:
			result = result.encode('utf-8')
			mime_type = 'text/html; charset=utf-8'
		
		headers = {"content-type": mime_type,
		"content-length": str(len(result)),
		"Cache-Control":"no-cache",  
		"Pragma":"no-cache"}
		
		set_headers(headers) 
		request.write(result)
		request.finish()
		
	def _ebRender(self, failure, request, ctxid):
		g.debug(LOG_ERR, failure)
		
		if isinstance(failure.value, Database.SecurityError):
			if ctxid == None:
				page = self.login(uri=request.uri,msg="Unable to access resource; please login.")
			else:
				#user=ts.db.checkcontext(ctxid)[0]
				page = self.login(uri=request.uri, msg="Insufficient permissions to access resource.")
			#print "SECURITY ERROR
		elif isinstance(failure.value, Database.SessionError):
			print 1
			page = self.login(uri=request.uri, msg="Session expired.")
			print 2
		else:
			page = '<pre>'  + escape(str(failure)) + '</pre>'
			
		print page
		request.write(page[0])
		request.finish()

