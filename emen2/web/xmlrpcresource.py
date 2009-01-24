

###########################
# NO LONGER USED
###########################


from twisted.web import server, xmlrpc #, resource
from twisted.internet import threads #, defer, reactor
from emen2.emen2config import *
import emen2.Database
from twisted.web.resource import Resource

import xmlrpclib
import os
import time

Fault = xmlrpclib.Fault




class XMLRPCResource(xmlrpc.XMLRPC):
	isLeaf = True
	
	def _cbRender(self, result, request):
		request.setHeader("content-length", len(result))
		request.setResponseCode(200)
		request.write(result)
		request.finish()		
		return

	def _ebRender(self, result, request):
		print "XMLRPC Error"
		print result
		result=unicode(result.value)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		request.write(result)
		request.finish()
	
	def finish_request(self, result, db, request):
		#request.close()
		request.finish()
		
		
	def getmethod(self, content):
		args, method = xmlrpclib.loads(content)
		return args, method


	def render(self, request):
		request.content.seek(0, 0)
		content = request.content.read()
		args, method = self.getmethod(content)
		host = request.getClientIP()
		kwargs={"host":host}

		print "\n\n=== xmlrpc === %s \n %s : %s"%(method, args, kwargs)


		request.setHeader("content-type", "text/xml")
		
		d = threads.deferToThread(self.action, method, args, kwargs)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET 

		
		


	def action(self, method, args, kwargs, db=None):
		method_ = db.publicmethods.get(method, None)
		if method_ is not None:
			result = method_(db, *args, **kwargs)
		else:
			raise NotImplementedError('remote method %s not implemented' % method)

		allow_none = True

		try:
			result = self.__enc(result)

			if not isinstance(result, tuple):
				result = (result,)
			result = xmlrpclib.dumps(result, methodresponse=1, allow_none=allow_none)
		except Exception, inst:
			print inst


		return result