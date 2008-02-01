from __future__ import with_statement
from g import *
from loglevels import LOG_ERR
import re
import os
from sets import Set
import pickle
import traceback
import time
import random
import atexit
import cStringIO

import sys
from emen2 import ts
import Database

from subsystems import routing
import emen2.TwistSupport_html.html.error

# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads

from twisted.web.resource import Resource
from twisted.web.static import *

#import debugging as debug
from functools import partial

from cgi import escape

class custpartial(partial):
	keywords = {}

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
#				print "Registering URL:"
				print cls
				print name
				print match
				print ""
				def _reg_inside(cb):
						cls.__registerurl(name, re.compile(match), cb)
						return cb
				return _reg_inside


		def login(self,uri,msg=""):
				page = """
				<h2>Please login:</h2>
				<h3>%s</h3>
				<div id="zone_login">

					<form action="%s" method="POST">
						<table><tr>
							<td>Username:</td>
							<td><input type="text" name="username" /></td>
						</tr><tr>
							<td>Password:</td>
							<td><input type="password" name="pw" /></td>
						</tr></table>

						<input type="submit" value="submit" />

					</form>
				</div>"""%(msg,uri)
				return page
					

		def render(self, request):
#				print "----------------------------"

				response = str(request)			
				host=request.getClientIP()
				args=request.args
				request.postpath = filter(bool, request.postpath) or ["home"]
				method = request.postpath[0]
				ctxid = request.getCookie("ctxid")
				user=None
				debug("ctxid: %s"%ctxid)
				loginmsg=""

				tmp = {}
				for key in Set(args.keys()) - Set(["db","host","user","ctxid"]):
					tmp[key] = str.join('\t', args[key])

				try:
					user = ts.db.checkcontext(ctxid)[0]
				except KeyError:
					if ctxid != None:	loginmsg = "Session expired"
					user = None
					ctxid = None
				
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
						method = "login"
							
				if method == "login":			
					page = self.login(uri=request.uri,msg=loginmsg)
					request.write(page)
					request.finish()
					return
			
				if method == "logout":
					ts.db.deletecontext(ctxid)
					redir = """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">"""
					request.write(redir)
					request.finish()
					return

				path="/"+"/".join(request.postpath)
				if path[-1] != "/":
					path+="/"
					
				debug(path)
				debug( 'request: %s, args: %s' % (request, tmp) )
				debug(type(tmp))

				callback = routing.URLRegistry().execute(path, **tmp)
									
				d = threads.deferToThread(callback, ctxid=ctxid, host=host)
				d.addCallback(self._cbsuccess, request, ctxid)
				d.addErrback(self._ebRender, request, ctxid)


				return server.NOT_DONE_YET

		def _cbsuccess(self, result, request, ctxid):
				request.setHeader("content-type","text/html; charset=utf-8")
				request.setHeader("content-length", str(len(result)))
		
				# no caching
				request.setHeader("Cache-Control","no-cache"); #HTTP 1.1
				request.setHeader("Pragma","no-cache"); #HTTP 1.0				request.write(result)

				result=result.encode("utf-8")
				request.write(result)
				request.finish()
				return

		@debug.debug_func
		def _ebRender(self, failure, request, ctxid):
				
				if isinstance(failure.value,emen2.Database.SecurityError):
					if ctxid == None:
						page = self.login(uri=request.uri,msg="Unable to access resource; please login.")
					else:
						#user=ts.db.checkcontext(ctxid)[0]
						page = self.login(uri=request.uri,msg="Insufficient permissions to access resource.")
					request.write(page)
					request.finish()
					return
					
				debug(LOG_ERR, failure)
				if isinstance(failure.value,emen2.Database.SessionError):
					page = self.login(uri=request.uri,msg="Session expired.")
					request.write(page)
					request.finish()
					return

				request.write('<pre>'  + escape(str(failure)) + '</pre>')
				request.finish()
				return
