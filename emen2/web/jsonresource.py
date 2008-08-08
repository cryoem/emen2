from twisted.web import server#, resource
from twisted.internet import threads#, defer, reactor
from emen2.emen2config import *
from emen2 import Database
from twisted.web.resource import Resource

import os
import demjson
import time

#from emen2 import ts


class JSONResource(Resource):
	isLeaf = True
	
	def _cbRender(self, result, request):
		#result=demjson.encode(result)
		request.setHeader("content-length", len(result))
		request.setResponseCode(200)
		request.write(result)
		request.finish()		
		return

	def _ebRender(self, result, request):
		print result
		result=unicode(result)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		request.write(result)
		request.finish()
	
	def finish_request(self, result, db, request):
		db.close()
		request.finish()
		

	def render(self, request):
		request.content.seek(0, 0)
		content = request.content.read()
		method = request.uri.split("/")[2]
		#args = simplejson.loads(content)
		args = demjson.decode(content)
		host = request.getClientIP()
		kwargs={"host":host}

#		print content
#		print method
#		print args
#		print host

		print "\n\n=== jsonrpc === %s \n %s \n %s"%(method, args, kwargs)


		request.setHeader("content-type", "text/xml")
		
		d = threads.deferToThread(self.action, method, args, **kwargs)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET 


	def action(self, method, args, db=None, host=None):
		print 'json request'
		method_ = db.publicmethods.get(method, None)
		if method_ is not None:
			result = method_(db, *args)
			result = demjson.encode(result, escape_unicode=True)
		else:
			raise NotImplementedError('remote method %s not implemented' % method)
		return result.encode("utf-8", 'replace')
