#import re
#import os
#from sets import Set
#import pickle
#import traceback
#import time
#import random
import timing
import time
import random

DEBUG = 1

from emen2 import ts 
from emen2.ts import db

#from emen2.TwistSupport_html import html

import emen2.TwistSupport_html.html.login
import emen2.TwistSupport_html.html.newuser
import emen2.TwistSupport_html.html.home
import emen2.TwistSupport_html.html.error

# Sibling Imports
from twisted.web import server
from twisted.web import error
from twisted.web import resource
from twisted.web.util import redirectTo

# Twisted Imports
#from twisted.web import http
#from twisted.python import threadable, log, components, failure, filepath
from twisted.python import filepath, log, failure
#from twisted.internet import abstract, interfaces, defer
from twisted.internet import defer, reactor, threads
#from twisted.spread import pb
#from twisted.persisted import styles
#from twisted.python.util import InsensitiveDict
#from twisted.python.runtime import platformType


from twisted.web.resource import Resource
from twisted.web.static import *

class DBResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""

	

	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		global db,callbacks

		t0 = time.time()


		# Redirects
		if (len(request.postpath)==0):
			request.postpath.append("home")
			request.uri = "/db/home"
		if (len(request.postpath[0])==0):
			request.postpath[0] = "home"
			request.uri = "/db/home"
			
		# Startup
		session=request.getSession()			# sets a cookie to use as a session id
		method=request.postpath[0]
		host=request.getClientIP()
		print "\n--------- request ----------------\nGet: %s"%request.uri

#		print request.args
		
		try:
			session.ctxid = request.args["ctxid"][0]
			#		print request.getClientIP()
			db.checkcontext(session.ctxid,request.getClientIP())
			print "Got ctxid from args"
		except:
			pass
#			print request.args["ctxid"][0]
#			print "no ctxid from args"



		try:
			ctxid = session.ctxid
			db.checkcontext(ctxid,request.getClientIP())
		except:
			try:			
				session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
			
				ctxidcookiename = 'TWISTED_SESSION_ctxid'
				request.addCookie(ctxidcookiename, session.ctxid, path='/')
			
				print "ctxid: %s"%session.ctxid
				return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
						<meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest
			except ValueError, TypeError:
				print "Authentication Error"
				print "...original request: %s"%session.originalrequest
				return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,None,None,redir=session.originalrequest,failed=1)
			except KeyError:
				print "Need to login..."

				# Is it a page that does not require authentication?
				if (request.postpath[0] == "home"):
					return emen2.TwistSupport_html.html.home.home(request.postpath,request.args,None,host)
				if (request.postpath[0]=="newuser"):
					return emen2.TwistSupport_html.html.newuser.newuser(request.postpath,request.args,None,request.getClientIP())
	

				if request.uri == "/db/login":
					session.originalrequest = "/db/"
				else:
					session.originalrequest = request.uri
					
#				print "...requesting: %s"%request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)
			
				
#		print session.uid
#		print "Checked context with ctxid: %s"%ctxid

		# Ok, if we got here, we can actually start talking to the database


		exec("import emen2.TwistSupport_html.html.%s"%method)
		
		if DEBUG:
			exec("reload(emen2.TwistSupport_html.html.%s)"%method)



#		ret=eval("emen2.TwistSupport_html.html."+method+"."+method)(request.postpath,request.args,ctxid,host)
#		function = getattr(, method, None)
		exec("function = emen2.TwistSupport_html.html.%s.%s"%(method,method))

#		defer.maybeDeferred(function, request.postpath, request.args, ctxid, host).addErrback(
#			self._ebRender
#		 ).addCallback(
#		 	self._cbRender, request
#		)


		d = threads.deferToThread(function, request.postpath, request.args, ctxid, host)
		d.addCallback(self._cbRender, request, time.time())
		d.addErrback(self._ebRender, request, time.time())


		# JPEG Magic Number
#		if ret[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
#		if ret[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		
		
		# "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)

		return server.NOT_DONE_YET 


	
	def _cbRender(self, result, request, t0):
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()
 		print "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)
		return

	def _ebRender(self, failure, request, t0):
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()
 		print "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)
		return

#		return
#		print "ebRender..."
#		print "request"
#		print request
#		print "failure"
#		request.write(str(failure))
#		request.finish()
#		return ""

class DownloadFile(Resource, filepath.FilePath):

	isLeaf = True


	contentTypes = loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	type = None
#	defaultType="text/html"
	defaultType="application/octet-stream"

	def render(self, request):
		"""You know what you doing."""

		# auth...

		if request.args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				db.checkcontext(ctxid,request.getClientIP())
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)	


		
		bids = request.postpath[0].split(",")

		if len(bids) > 1:
			ipaths=[]
			for i in bids:
				bname,ipath,bdocounter=ts.db.getbinary(i,ctxid)						
				ipaths.append((ipath,bname))


			self.type, self.encoding = "application/octet-stream", None
			fsize = size = 0
			
			request.setHeader('content-type', self.type)
			request.setHeader('content-encoding', self.encoding)

			import tarfile

			# how many *hours* do you think I wasted before realizing I could simply give it the request as the file object?
			tar = tarfile.open(mode="w|", fileobj=request)

			for name in ipaths:
				print "adding %s as %s"%(name[0],name[1])
				tar.add(name[0],arcname=name[1])
			tar.close()

			request.finish()



		else:		
			bid = request.postpath[0]
			bname,ipath,bdocounter=ts.db.getbinary(bid,ctxid)

			self.path = ipath
			self.type, self.encoding = getTypeAndEncoding(bname, self.contentTypes,	self.contentEncodings, self.defaultType)
			f = self.open()
			fsize = size = os.stat(ipath).st_size

	#		fsize = size = self.getsize()
			if self.type:	request.setHeader('content-type', self.type)
			if self.encoding:	request.setHeader('content-encoding', self.encoding)
			if fsize:	request.setHeader('content-length', str(fsize))

			if request.method == 'HEAD':	return ''

			FileTransfer(f, size, request)
			# and make sure the connection doesn't get closed
			return server.NOT_DONE_YET
		
		
		
		