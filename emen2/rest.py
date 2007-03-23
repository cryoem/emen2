from twisted.web.resource import Resource
#from emen2 import Database
from twisted.web import xmlrpc
import xmlrpclib
import os
from sets import Set
from emen2.emen2config import *

from emen2 import ts

class DBRESTResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""
	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		global db,callbacks

		method=request.args["method"][0]
		host=request.getClientIP()

		ret=eval("self.rest_"+method)(request.args,request.host)


		return str(ret)
	
	def rest_ping(self,args,host=None):
		return "pong? %s"%args

	def rest_test(self,args,host=None):
		a=Database.WorkFlow()
		b=Database.WorkFlow()
		c=(a,b)
		d=[dict(x.__dict__) for x in c]
		
		return {"a":None,"b":None}
		
	def rest_login(self,args,host=None):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
#		return str(ts.db.login(str(username),str(password),host,maxidle))
		return ""

	def rest_checkcontext(self,args,host=None):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
		try: 
			return ts.db.checkcontext(args["ctxid"][0])
		except Exception, inst:
			return inst