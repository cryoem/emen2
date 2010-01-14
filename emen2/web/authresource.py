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



def cookie_expire_time():
	return time.strftime("%a, %d-%b-%Y %H:%M:%S PST", time.localtime(time.time()+604800))



def render_security_error(redirect, e):
	args = {'redirect': redirect, 'msg': str(e)}
	print "sec error"
	print emen2.TwistSupport_html.public.login
	p = emen2.TwistSupport_html.public.login.Login(**args)
	data = unicode(p.get_data()).encode("utf-8")
	return data


#class Null(object): pass



class AuthResource(Resource):

	isLeaf = True


	# switch back to non-ssl
	def loginredir(self,redirect,request):
		u=urlparse.urlsplit(redirect)
		du=list(u)

		#if u.hostname == None and u.port == None and u.scheme == None:
		#	du[0]="http"
			
		requesthost = request.getHeader("host").split(":")[0]

		if g.EMEN2HOST != "localhost":
			du[1] = requesthost
		if g.EMEN2EXTPORT != 80:
			du[1]= "%s:%s"%(requesthost,g.EMEN2EXTPORT)
		
		# print "redir is %s"%urlparse.urlunsplit(du)
		
		return urlparse.urlunsplit(du)



	# parse request for params
	def getloginparams(self, request):

		args = request.args
		
		method = "/".join(filter(None,request.postpath))
		
		host = request.getClientIP()
		ctxid = request.getCookie("ctxid") or args.get("ctxid",[None])[0]
		username = args.get('username', [None])[0]
		pw = request.args.get('pw', [None])[0]

		redirect = request.args.get("redirect",[request.uri])[0]
		redirect = self.loginredir(redirect,request)

		if "auth/" in redirect:
			redirect = "%s/db/home/"%(g.EMEN2WEBROOT)

		return {
			"username":username,
			"pw":pw,
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

		method = l.get("method")
		route = {
			"login": emen2.TwistSupport_html.public.login.Login,
			"logout": emen2.TwistSupport_html.public.login.Logout,
			"password/reset": emen2.TwistSupport_html.public.login.PasswordReset,
			"password/change": emen2.TwistSupport_html.public.login.PasswordChange,
			"context": emen2.TwistSupport_html.public.login.CheckContext
		}
		
		rcls = route.get(method)
		
		p = rcls(db=db, **l)		
		data = unicode(p.get_data()).encode("utf-8")

		ctxid = p.auth_action()		

		return ctxid, data



	def _cbrender(self, result, request, largs):
		
		ctxid = result[0]
		data = result[1]				
		msg = None
		
		if ctxid != None and ctxid != largs["ctxid"]:
			request.addCookie("ctxid", ctxid or "", path='/')
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
		
		data = "There was a problem with your request."
		try:
			if isinstance(failure, BaseException): raise; failure
			else: failure.raiseException()
		except Exception, e:
			data = render_security_error('/', e)

		request.write(unicode(data).encode("utf-8"))
		request.finish()
		return




