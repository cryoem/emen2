# TwistSupport_html.py	Steven Ludtke  06/2004
# This module provides the resources needed for a HTML server using Twisted

#print "Startup: %s"%dir()
import re
import os
from sets import Set
from emen2 import TwistSupport 
import pickle
import traceback
import time
import random

from emen2.TwistSupport_db import db
from html import *
import tmpl
import supp
import plot


from twisted.web.resource import Resource





#from emen2.TwistSupport_db import db

#print "Global db?? %s"%db



class DBResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""
	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		session=request.getSession()			# sets a cookie to use as a session id
		
#		return "request was '%s' %s"%(str(request.__dict__),request.getClientIP())
		global db,callbacks

		if (len(request.postpath)==0 or request.postpath[0]=="index.html" or len(request.postpath[0])==0) : return html_home()
				
		# This is the one request that doesn't require an existing session, since it sets up the session
		if (request.postpath[0]=='login'):
			session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
#			return "Login Successful %s (%s)"%(str(request.__dict__),session.ctxid)
			return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
				<meta http-equiv="REFRESH" content="2; URL=%s"><title>HTML REDIRECT</title></head>
				<body><h3>Login Successful</h3>"""%request.received_headers["referer"]

		if (request.postpath[0]=="newuser"):
			return html_newuser(request.postpath,request.args,None,request.getClientIP())
				
		# A valid session will have a valid ctxid set
		try:
			ctxid=session.ctxid
		except:
			return loginpage(request.uri)
		
		db.checkcontext(ctxid,request.getClientIP())

		# Ok, if we got here, we can actually start talking to the database
		
		method=request.postpath[0]
		host=request.getClientIP()
		
		ret=eval("html_"+method)(request.postpath,request.args,ctxid,host)
		
		# JPEG Magic Number
		if ret[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if ret[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		return ret
#		return str(request.__dict__)
#		return callbacks[method](request.postpath,request.args,ctxid,host)

#		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())


def loginpage(redir):
	"""Why is this a function ?	 Just because. Returns a simple login page."""
	ret = []
#	print "Loginpage dir: %s"%dir()
	ret.append(tmpl.html_header("EMEN2 Login"))
	ret.append(tmpl.singleheader("EMEN2 Login"))
	page = """
<div class="switchpage" id="page_mainview">
	<h3>Please Login:</h3>
	<div id="zone_login">
		<form action="/db/login" method="POST">
			<input type="hidden" name="fw" value="%s"; />
			<span class="inputlabel">Username:</span> 
			<span class="inputfield"><input type="text" name="username" /></span><br />
			<span class="inputlabel">Password:</span>
			<span class="inputfield"><input type="password" name="pw" /></span><br />
			<span class="inputcommit"><input type="submit" value="submit" /></span>
		</form>
	</div>
</div>
"""%(redir)

	ret.append(page)
	ret.append(tmpl.html_footer())

	return " ".join(ret)


