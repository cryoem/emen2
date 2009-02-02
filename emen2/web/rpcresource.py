from twisted.web import server, xmlrpc
from twisted.internet import threads
from emen2.emen2config import *
from emen2 import Database
from twisted.web.resource import Resource

import os
import time

import xmlrpclib
import demjson

Fault = xmlrpclib.Fault


class RPCFormatJSON:
	def __init__(self):
		pass
		
	def decode(self, content, kw):
		#method=None
		args=demjson.decode(content)
		kwargs={}
		
		for k,v in kw.items():
			kwargs[str(k)]=demjson.decode(v[0])

		if hasattr(args,"items"):
			for k,v in args.items():
				kwargs[str(k)]=v
			args=[]
		
		return None, args, kwargs

	def encode(self, method, value):
		value = demjson.encode(value, escape_unicode=True)			
		return value.encode("utf-8", 'replace')	




class RPCFormatXMLRPC:
	def __init__(self):
		pass
		
	def decode(self, content, kw):
		args, method = xmlrpclib.loads(content)
		
		args=list(args)
		kwargs = {}
		# add kwargs support to xmlrpc:: if last arg is dict...
		if isinstance(args[-1],dict):
			kwargs = args.pop()
		
		# not really supported... no decode; values limited to strings.
		for k,v in kw.items():
			kwargs[str(k)]=v[0]
		
		if hasattr(args,"items"):
			for k,v in args.items():
				kwargs[str(k)]=v
			args=[]
			
		return method, args, kwargs

	def encode(self, method, value):
		try:
			value = self.encode_serialize(value)

			if not isinstance(value, tuple):
				value = (value,)
			value = xmlrpclib.dumps(value, methodresponse=1, allow_none=True)

		except Exception, inst:
			print "Problem w/ XML-RPC Encoding:"
			print inst
			value = "Error"
		
		return value		


	def encode_serialize(self, value):
		"""Serializes in UTF-8 DB instances for unsophisticated encoders (e.g. xmlrpc)"""
		# convert to dict using class method
		if isinstance(value, (Database.Record, Database.RecordDef, Database.ParamDef, Database.User, Database.WorkFlow)):
			return self.encode_serialize(dict(value))

		elif hasattr(value,"items"):
			v2={}
			for k,v in value.items():
				v2[str(k)]=self.encode_serialize(v)
			return v2

		elif hasattr(value,"__iter__"):
			ret=[]
			for i in value:
				ret.append(self.encode_serialize(i))
			return ret

		elif type(value)==unicode:
			value=value.encode("utf-8")

		return value



class RPCResource(Resource):
	isLeaf = True
	
	
	def __init__(self,format="xmlrpc"):
		Resource.__init__(self)
		self.format = format
		if format=="json":
			self.handler = RPCFormatJSON()
		elif format=="xmlrpc":
			self.handler = RPCFormatXMLRPC()
	

	
	def _cbRender(self, result, request):
		request.setHeader("content-length", len(result))
		request.setResponseCode(200)
		request.write(result)
		request.finish()		



	def _ebRender(self, result, request):
		print result
		result=unicode(result.value)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		request.write(result)
		request.finish()
		


	def render(self, request):

		request.content.seek(0, 0)
		content = request.content.read()
		method, args, kwargs = self.handler.decode(content,request.args)

		if kwargs.has_key("method"):
			method = kwargs["method"]
		if method==None:
			method = request.uri.split("/")[-1]			

		kwargs["host"] = request.getClientIP()
		if not kwargs.get("ctxid"):
			kwargs["ctxid"] = request.getCookie("ctxid")			

		print "\n\n:: rpc :: %s :: %s :: %s"%(method,kwargs["host"],self.format)
		print "\targs, kwargs: %s, %s"%(args, kwargs)	

		request.setHeader("content-type", "text/xml")
		
		d = threads.deferToThread(self.action, method, args, kwargs)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET 




	def action(self, method, args, kwargs, db=None, host=None):
		#method_ = db.publicmethods.get(method, None)
		#db._setcontext(ctxid,host)		
		#if not db._ismethod(method):
		#	raise NotImplementedError('remote method %s not implemented' % method)
		result = db._callmethod(method, args, kwargs)
		return self.handler.encode(method, result)



