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

g = emen2.globalns.GlobalNamespace('')



class AuthResource(Resource):

	isLeaf = True
	methods = ["login","logout","chpasswd"]
		
		


		
		
	# switch back to non-ssl	
	def loginredir(self,redirect,request):
		u=urlparse.urlsplit(redirect)
		du=list(u)
		#if u.hostname == None and u.port == None and u.scheme == None:
		du[0]="http"
		du[1]=request.getHeader("host").split(":")[0]
		if g.EMEN2PORT != 80:
			du[1]="%s:%s"%(du[1],g.EMEN2PORT)
		return urlparse.urlunsplit(du)	
		
				
				
	# parse request for params
	def getloginparams(self, request):
		args=request.args
		method = listops.get(request.postpath, 0, '')
		host = request.getClientIP()
		ctxid = request.getCookie("ctxid") or args.get("ctxid",[None])[0]
		username = args.get('username', [None])[0]
		pw = request.args.get('pw', [None])[0]
		newpw = request.args.get('newpw',[None])[0]
		redirect = request.args.get("redirect",[request.uri])[0]
		redirect = self.loginredir(redirect,request)
		if "auth/" in redirect: redirect = "/db/home/"

		return {
			"username":username,
			"pw":pw,
			"newpw":newpw,
			"ctxid":ctxid,
			"host":host,
			"method":method,
			"redirect":redirect
			}
			
	
	
	def render(self, request):
		largs = self.getloginparams(request)

		d = threads.deferToThread(self._action, largs)
		d.addCallback(self._cbrender, request, largs)
		d.addErrback(self._ebrender, request, largs)
		return server.NOT_DONE_YET




	# the meat, raise exception if bad login	
	def _action(self, l, db=None):
		g.debug("auth -> %s"%l)

		if l["method"] == "login":
			cls=emen2.TwistSupport_html.public.login.Login
		elif l["method"] == "logout":
			cls=emen2.TwistSupport_html.public.login.Logout
		elif l["method"] == "chpasswd":
			cls=emen2.TwistSupport_html.public.login.Chpasswd
		else:
			raise Exception,"Unsupported auth method: %s"%method
			
		
		# do work here
#		db._setcontext(l["ctxid"],l["host"])
		p = cls(db=db,**l)
		ctxid = p.get_context()["ctxid"]
		data = unicode(p.get_data()).encode("utf-8")
#		db._clearcontext()
		
		g.debug("->ctxid:%s"%ctxid)

		return ctxid, data
		
		
		
	def _cbrender(self, result, request, largs):		
		ctxid = result[0]
		data = result[1]
		
		msg = None
		if ctxid != largs["ctxid"]:
			g.debug("-> setting ctxid to %s"%ctxid)
			request.addCookie("ctxid", ctxid, path='/')
				
			if largs["redirect"] != None:
				g.debug("redirect->%s"%largs["redirect"])
				request.redirect(largs["redirect"])
				request.finish()
				return
		
		request.write(data)
		request.finish()
		return
		
		
		
	def _ebrender(self, failure, request, largs):
		g.debug("Failure: %s"%failure)
		g.debug("-> unsetting ctxid")
		
		request.setResponseCode(401)
		request.addCookie("ctxid", '', path='/')
		
		#result = self._getpage("Login",str(failure), largs["redirect"])
		result = emen2.TwistSupport_html.public.login.Login(db=ts.db,ctxid=None,host=None,msg=str(failure))
		request.write(unicode(result).encode("utf-8"))
		request.finish()
		return
