#import re
#import os
#from sets import Set
#import pickle
#import traceback
#import time
#import random

from emen2 import ts 
from emen2.ts import db
from emen2.TwistSupport_html import html

from twisted.web.resource import Resource


class DBResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""
	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		global db,callbacks

		session=request.getSession()			# sets a cookie to use as a session id
		print "\n-------------------------\nGet: %s"%request.uri

		try:
			ctxid = session.ctxid
		except:
			try:			
				session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
			
				ctxidcookiename = 'TWISTED_SESSION_ctxid'
				request.addCookie(ctxidcookiename, session.ctxid, path='/')
			
#				print "Got ctxid: %s"%session.ctxid
				return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
						<meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest
			except ValueError, TypeError:
				print "Authentication Error"
				print "...original request: %s"%session.originalrequest
				return html.login(session.originalrequest,None,None,None,redir=session.originalrequest,failed=1)
			except:
				print "Need to login..."
				session.originalrequest = request.uri
#				print "...requesting: %s"%request.uri
				return html.login(request.uri,None,None,None,redir=request.uri,failed=0)

		if (len(request.postpath)==0 or request.postpath[0]=="index.html" or len(request.postpath[0])==0) : return html.home()
				
		# This is the one request that doesn't require an existing session, since it sets up the session
		if (request.postpath[0]=="newuser"):
			return html.newuser(request.postpath,request.args,None,request.getClientIP())
					
#		print session.uid
		db.checkcontext(ctxid,request.getClientIP())
#		print "Checked context with ctxid: %s"%ctxid

		# Ok, if we got here, we can actually start talking to the database
		
		method=request.postpath[0]
		host=request.getClientIP()
		
		ret=eval("html."+method)(request.postpath,request.args,ctxid,host)
		
		# JPEG Magic Number
		if ret[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if ret[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		return ret
#		return str(request.__dict__)
#		return callbacks[method](request.postpath,request.args,ctxid,host)

#		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())


