import os
import time

from twisted.web import server, xmlrpc
from twisted.internet import threads
from twisted.web.resource import Resource

from emen2 import Database
from emen2.Database import database

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import xmlrpclib
import demjson


Fault = xmlrpclib.Fault


class RPCFormatJSON:
	def __init__(self):
		pass

	def decode(self, content, kw):
		args=demjson.decode(content)
		kwargs={}
		for k,v in kw.items():
			try:
				kwargs[str(k)]=demjson.decode(v[0])
			except demjson.JSONDecodeError:
				pass

		if hasattr(args,"items"):
			for k,v in args.items():
				kwargs[str(k)]=v
			args=[]

		return None, tuple(args), kwargs

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
		#if isinstance(args[-1],dict):
		#	kwargs = args.pop()

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
			g.debug.msg("LOG_ERROR","Problem w/ XML-RPC Encoding:")
			g.debug.msg("LOG_ERROR", inst)
			value = "Error"

		return value


	def encode_serialize(self, value):
		"""Serializes in UTF-8 DB instances for unsophisticated encoders (e.g. xmlrpc)"""
		# convert to dict using class method
		if isinstance(value, (database.Record, database.RecordDef, database.ParamDef, database.User, database.WorkFlow)):
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

class RPCChain(Resource):
	isLeaf = True

	def render(self, request):
		request.content.seek(0,0)
		data = request.content.read()
		d = threads.deferToThread(self.action, data)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET

	def action(self, data, db=None, ctxid=None):
		data = demjson.decode(data)
		method = data['method']
		args = data['args']
		kwargs = dict( (key.encode('utf-8'), value) for key, value in data['kwargs'].iteritems() )
		result = db._callmethod(method, args, kwargs)
		method = data['next']
		arg = data['next_arg']
		result = db._callmethod(method, (), {arg.encode('utf-8'):result})
		return demjson.encode(result).encode('utf-8')

	def _cbRender(self, result, request):
		request.setHeader("content-length", len(result))
		request.setHeader("content-type", 'application/json')
		request.setResponseCode(200)
		g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		request.write(result)
		request.finish()

	def _ebRender(self, result, request):
		g.debug.msg("LOG_ERROR", result)
		request.setHeader("X-Error", ' '.join(str(result).split()))
		result=unicode(result.value)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		request.write(result)
		request.finish()





class RPCResource(Resource):
	isLeaf = True


	def __init__(self,format="xmlrpc"):
		Resource.__init__(self)
		self.format = format
		if format=="json":
			self.handler = RPCFormatJSON()
			self.fmt = 'application/json'
		elif format=="xmlrpc":
			self.handler = RPCFormatXMLRPC()
			self.fmt = 'text/xml'



	def _cbRender(self, result, request, fmt):
		request.setHeader("content-length", len(result))
		request.setHeader("content-type", fmt)
		request.setResponseCode(200)
		g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		request.write(result)
		request.finish()



	def _ebRender(self, result, request, *args, **kwargs):
		g.debug.msg("LOG_ERROR", result)
		request.setHeader("X-Error", ' '.join(str(result).split()))
		result=unicode(result.value)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		g.debug.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		request.write(result)
		request.finish()



	def render(self, request):
		ctxid = request.getCookie("ctxid")
		host = request.getClientIP()

		d = threads.deferToThread(self.action, request, ctxid=ctxid, host=host)
		d.addCallback(self._cbRender, request, self.fmt)
		d.addErrback(self._ebRender, request, self.fmt)
		return server.NOT_DONE_YET




	def action(self, request, db=None, ctxid=None, host=None):
		# this binds the Context to the DBProxy for the duration of the view

		request.content.seek(0, 0)
		content = request.content.read()
		method, args, kwargs = self.handler.decode(content,request.args)

		if kwargs.has_key("method"):
			method = kwargs["method"]
		if method==None:
			method = request.uri.split("/")[-1]


		g.debug.msg("LOG_INFO", "====== RPCResource action: method %s ctxid %s host %s"%(method, ctxid, host))


		db._starttxn()

		db._setcontext(ctxid,host)

		try:
			result = db._callmethod(method, args, kwargs)
		except Exception, e:
			db._aborttxn()
			raise
		else:
			db._committxn()



		return self.handler.encode(method, result)



