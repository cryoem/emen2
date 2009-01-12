import re
import os
from sets import Set
import pickle
import traceback
#import timing
import time
import random
import atexit

import cStringIO

DEBUG = 1

from emen2 import ts 
from emen2.emen2config import *

import emen2.TwistSupport_html

##import emen2.TwistSupport_html.login
#import emen2.TwistSupport_html.newuser
#import emen2.TwistSupport_html.home
##import emen2.TwistSupport_html.error

# Sibling Imports
#from twisted.web import server
#from twisted.web import error
#from twisted.web import resource
#from twisted.web.util import redirectTo

# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads

from twisted.web.resource import Resource
from twisted.web.static import *

class WebResource(Resource):
	isLeaf = True
	
	
	def getfilenames(self,content):
		if not request.args.has_key("filename"):
			request.content.seek(0)
			content=request.content.read()
			b=re.compile("filename=\"(.+)\"")		
			filename=b.findall(content[:5000])[0]
		else:
			filename=request.args["Filename"][0]		
	
	
	
	def render(self,request):
		t0 = time.time()
		session=request.getSession()
		host=request.getClientIP()
		args=request.args

		# pages that do not require login
		anonmethods = ["home","newuser"]

		# home
		if len(request.postpath) < 1:
			request.postpath.append("home")

		method = request.postpath[0]
		if method == "": method = "home"

		# Check if context ID is good, else login or view anon page
		if not hasattr(session,"ctxid"):
			session.ctxid = None
		if args.has_key("ctxid"):
			session.ctxid = args["ctxid"][0]

		try:
			user=ts.db.checkcontext(ctxid=session.ctxid,host=host)[0]
		except KeyError:
			user=None
			# only a few methods are available without login
			if method in anonmethods and not args.has_key("username"):
				pass

			else:
				
				print "\n---- [%s] [%s] ---- login request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,request.postpath)					
				
#				if not hasattr(session,"originalrequest"):
				if request.uri == "/db/login":
					session.originalrequest = "/db/home"
				else:
					session.originalrequest = request.uri		
				print "Set originalrequest to %s"%session.originalrequest

				try:
					session.ctxid=ts.db.login(request.args["username"][0],request.args["pw"][0],ctxid=None,host=request.getClientIP())

				# Bad login
				except ValueError, TypeError:
					return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,ctxid=None,host=host,redir=session.originalrequest,failed=1)

				# Have not tried to login yet
				except KeyError:
					return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,ctxid=None,host=host,redir=session.originalrequest)
					
				# Ok, good login; redir to requested page
				ctxidcookiename = "TWISTED_SESSION_ctxid"
				request.addCookie(ctxidcookiename, session.ctxid, path='/')
				print "original request: %s"%session.originalrequest
				return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest			


		print "\n---- [%s] [%s] [%s] ---- web request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)

		if method == "logout":
			session.ctxid = None
			session.expire()
			ts.db.deletecontext(ctxid=session.ctxid,host=host)
			return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">"""					

		module = getattr(emen2.TwistSupport_html.html,method)
		function = getattr(module,method)

		d = threads.deferToThread(function, request.postpath, request.args, ctxid=session.ctxid, host=host)
		d.addCallback(self._cbRender, request, t0=t0)
		d.addErrback(self._ebRender, request, t0=t0)


		return server.NOT_DONE_YET
		


	def _cbRender(self,result,request,t0=None):		

		try:
			result=result.encode("utf-8")
		except:
			pass


		if result[:3]=="\xFF\xD8\xFF":
			request.setHeader("content-type","image/jpeg")
		elif result[:4]=="\x89PNG":
			request.setHeader("content-type","image/png")
		else:
			try:
				result=result.encode("utf-8")
			except:
				pass
			request.setHeader("content-type","text/html; charset=utf-8")

		request.setHeader("content-length", str(len(result)))
		
		# no caching
		request.setHeader("Cache-Control","no-cache"); #HTTP 1.1
		request.setHeader("Pragma","no-cache"); #HTTP 1.0
		#request.setDateHeader("Expires", 0); #caching en proxy 
		
		request.write(result)
		request.finish()
		if TIME: print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)
		
		
		
	def _ebRender(self,failure,request,t0=None):
		traceback.print_exc()
#		request.write(TwistSupport_html.html.error.error(inst))
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()
		if TIME: print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)