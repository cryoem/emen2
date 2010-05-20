# $Author$ $Revision$
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
import emen2.db.exceptions
import emen2.db.config
g = emen2.db.config.g()

import emen2.web.views.auth


def cookie_expire_time():
	return time.strftime("%a, %d-%b-%Y %H:%M:%S PST", time.localtime(time.time()+604800))



def render_security_error(redirect, e):
	args = {'redirect': redirect, 'msg': str(e)}
	p = emen2.web.views.auth.Login(**args)
	data = unicode(p.get_data()).encode("utf-8")
	return data




class AuthResource(Resource):

	isLeaf = True


	# ian: todo: if not using SSL, switch back to unencrypted channel
	# ian: todo: HIGH: fix this to get HTTPS and apache proxied behavior working again
	def loginredir(self,redirect,request):
		return redirect
		# u=urlparse.urlsplit(redirect)
		# du=list(u)
		# 
		# requesthost = request.getHeader("host").split(":")[0]
		# 
		# if g.EMEN2HOST != "localhost":
		# 	du[1] = requesthost
		# if g.EMEN2EXTPORT != 80:
		#	du[1]= "%s:%s"%(requesthost,g.EMEN2EXTPORT)
		# # print "redir is %s"%urlparse.urlunsplit(du)
		# 
		# return urlparse.urlunsplit(du)



	# parse request for params
	def getloginparams(self, request):
		# only allowed arguments in authresource:
		# username, pw, ctxid, redirect, opw, on1, on2

		args = request.args

		method = "/".join(filter(None,request.postpath))

		host = request.getClientIP()
		ctxid = request.getCookie("ctxid") or args.get("ctxid",[None])[0]

		username = args.get('username', [None])[0]
		pw = request.args.get('pw', [None])[0]

		opw = request.args.get('opw', [None])[0]
		on1 = request.args.get('on1', [None])[0]
		on2 = request.args.get('on2', [None])[0]

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
			"redirect":redirect,
			"opw":opw,
			"on1":on1,
			"on2":on2
		}



	def render(self, request):
		kwargs = self.getloginparams(request)

		d = threads.deferToThread(self._action, **kwargs)
		d.addCallback(self._cbrender, request, **kwargs)
		d.addErrback(self._ebrender, request, **kwargs)
		return server.NOT_DONE_YET



	# the meat, raise exception if bad login
	def _action(self, db=None, **kwargs):

		# just used a fixed routing table..
		route = {
			"login": emen2.web.views.auth.Login,
			"logout": emen2.web.views.auth.Logout,
			"password/reset": emen2.web.views.auth.PasswordReset,
			"password/change": emen2.web.views.auth.PasswordChange,
			"context": emen2.web.views.auth.CheckContext
		}


		method = kwargs.get("method")
		rcls = route.get(method)

		ctxid = kwargs.get('ctxid')
		host = kwargs.get('host')
		success = True


		with db._setContext(ctxid, host):
			p = rcls(db=db, **kwargs)

			try:
				ctxid = p.auth_action()
			except Exception, e:
				success = False
				# print "Failed: %s"%e

			data = unicode(p.get_data()).encode("utf-8")

		# the action can result in a changed ctxid, which is written to client cookie..
		return success, ctxid, data



	def _cbrender(self, result, request, **kwargs):

		success = result[0]
		ctxid = result[1]
		data = result[2]
		msg = None

		# If the ctxid has changed in the view, update client cookie
		if ctxid != None and ctxid != kwargs.get('ctxid'):
			request.addCookie("ctxid", ctxid or "", path='/')

		# print "success/redir: %s %s"%(success, kwargs.get('redirect'))

		if success and kwargs.get('redirect'):
			request.redirect(kwargs.get('redirect'))
			request.finish()
			return

		request.write(data)
		request.finish()
		return



	def _ebrender(self, failure, request, **kwargs):
		# This should only happen in severe failure, normal errors are caught in action
		# In the event of an authentication failure, kill client cookie

		request.setResponseCode(401)
		request.addCookie("ctxid", '', path='/')

		data = failure

		# try:
		# 	# ian: todo: raise;failure ?
		# 	if isinstance(failure, BaseException): raise; failure
		# 	else:
		# 		failure.raiseException()
		# except Exception, e:
		# 	data = render_security_error('/', e)

		request.write(unicode(data).encode("utf-8"))
		request.finish()
		return


__version__ = "$Revision$".split(":")[1][:-1].strip()
