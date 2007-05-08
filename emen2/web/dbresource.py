#import re
#import os
#from sets import Set
#import pickle
#import traceback
#import time
#import random
import timing
import time

DEBUG = 1

from emen2 import ts 
from emen2.ts import db

#from emen2.TwistSupport_html import html

import emen2.TwistSupport_html.html.login
import emen2.TwistSupport_html.html.newuser
import emen2.TwistSupport_html.html.home


# Sibling Imports
from twisted.web import server
from twisted.web import error
from twisted.web import resource
from twisted.web.util import redirectTo

# Twisted Imports
from twisted.web import http
from twisted.python import threadable, log, components, failure, filepath
from twisted.internet import abstract, interfaces, defer
from twisted.spread import pb
from twisted.persisted import styles
from twisted.python.util import InsensitiveDict
from twisted.python.runtime import platformType


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
#			print request.args["ctxid"][0]
			print "no ctxid from args"



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
			
		ret=eval("emen2.TwistSupport_html.html."+method+"."+method)(request.postpath,request.args,ctxid,host)
		
		# JPEG Magic Number
		if ret[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if ret[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		
		
		print "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)
		
		return ret
#		return str(request.__dict__)
#		return callbacks[method](request.postpath,request.args,ctxid,host)

#		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())


class DownloadFile(Resource, filepath.FilePath):

	isLeaf = True


	contentTypes = loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	type = None
	defaultType="text/html"

	def render(self, request):
		"""You know what you doing."""



		# auth...
		session=request.getSession()			# sets a cookie to use as a session id

		try:
			ctxid = session.ctxid
			db.checkcontext(ctxid,request.getClientIP())
		except:
			print "Need to login..."
			session.originalrequest = request.uri
			return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)	


		
		bid = request.postpath[0]
		print "bid: %s"%bid
		
		bname,ipath,bdocounter=ts.db.getbinary(bid,ctxid)
		print "bname: %s"%bname
		print "ipath: %s"%ipath
		print "bdocounter: %s"%bdocounter

		self.path = ipath

		self.type, self.encoding = getTypeAndEncoding(bname,
																											self.contentTypes,
																											self.contentEncodings,
																											self.defaultType)

		print "content type: %s"%self.type
		print "encoding: %s"%self.encoding

		fsize = size = self.getsize()
		if self.type:
				request.setHeader('content-type', self.type)
		if self.encoding:
				request.setHeader('content-encoding', self.encoding)

		f = self.open()


		request.setHeader('content-length', str(fsize))
		if request.method == 'HEAD':
				return ''

		# return data
		FileTransfer(f, size, request)
		# and make sure the connection doesn't get closed
		return server.NOT_DONE_YET