from __future__ import with_statement

import re
import time
import urlparse
import demjson


# Twisted imports
from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
from urllib import quote

# emen2 imports
import emen2.util.listops
import emen2.Database.subsystems.exceptions
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')




#class Null(object): pass



class AuthResource(Resource):

	isLeaf = True
	methods = ["login","logout","chpasswd"]


	# switch back to non-ssl
	def loginredir(self,redirect,request):
		u=urlparse.urlsplit(redirect)
		du=list(u)
		if u.hostname == None and u.port == None and u.scheme == None:
			du[0]="http"
		#du[1]=request.getHeader("host").split(":")[0]
		du[1]=g.EMEN2HOST
		if g.EMEN2EXTPORT != 80:
			du[1]="%s:%s"%(du[1],g.EMEN2EXTPORT)
		
		print "redir is %s"%urlparse.urlunsplit(du)
		
		return urlparse.urlunsplit(du)



	# parse request for params
	def getloginparams(self, request):
		args=request.args
		method = emen2.util.listops.get(request.postpath, 0, '')
		host = request.getClientIP()
		ctxid = request.getCookie("ctxid") or args.get("ctxid",[None])[0]
		username = args.get('username', [None])[0]
		pw = request.args.get('pw', [None])[0]
		newpw = request.args.get('newpw',[None])[0]
		redirect = request.args.get("redirect",[request.uri])[0]
		redirect = self.loginredir(redirect,request)
		if "auth/" in redirect:
			redirect = "%s/db/home/"%(g.EMEN2WEBROOT)

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


		if l["method"] == "login":
			cls = emen2.TwistSupport_html.public.login.Login

		elif l["method"] == "logout":
			cls = emen2.TwistSupport_html.public.login.Logout

		elif l["method"] == "chpasswd":
			cls = emen2.TwistSupport_html.public.login.Chpasswd

		else:
			raise Exception,"Unsupported auth method: %s"%method


		# do work here
		p = cls(db=db, **l)
		ctxid = p.get_context().get("ctxid") #["ctxid"]
		data = unicode(p.get_data()).encode("utf-8")


		return ctxid, data



	def _cbrender(self, result, request, largs):
		ctxid = result[0]
		data = result[1]
				
		msg = None
		if ctxid != largs["ctxid"]:
			request.addCookie("ctxid", ctxid, path='/')

			if largs["redirect"] != None:
				request.redirect(largs["redirect"])
				request.finish()
				return

		request.write(data)
		request.finish()
		return



	def _ebrender(self, failure, request, largs):

		request.setResponseCode(401)
		request.addCookie("ctxid", '', path='/')

		#result = self._getpage("Login",str(failure), largs["redirect"])
		result = emen2.TwistSupport_html.public.login.Login(msg=failure)
		#result = "eb render %s"%failure
		request.write(unicode(result).encode("utf-8"))
		request.finish()
		return
