# $Id$
import sys
import cgi
import time
import UserDict, collections
collections.Mapping.register(UserDict.DictMixin)

# Twisted imports
from twisted.web import server
from twisted.internet import threads
from twisted.web.resource import Resource

import jsonrpc.jsonutil
from jsonrpc.server import ServerEvents

# emen2 imports
import emen2.db.config
import emen2.web.responsecodes
import emen2.util.loganalyzer
import emen2.db.record
import emen2.db.recorddef
import emen2.db.paramdef
import emen2.db.user

from emen2.web.view import View

import jsonrpc.jsonutil
from jsonrpc.utilities import public
import jsonrpc.common

@View.register
class JSONRPCProxy(View):
	
	def parse_content(self, request):
		pass
		
	
	@View.add_matcher('^/jsonrpc/$')
	def main(self, jsonrequest=None, tm=None):
		print "JSON Request:", jsonrequest
		# jsonrpc.common.InvalidRequest
		# print "JSON-RPC Request:"
		# print jsonrpc, method, params, id
		contents = jsonrpc.common.Request.from_json(jsonrequest)

		islist = (True if isinstance(contents, list) else False)
		if not islist:
			contents = [contents]		
	
		for item in contents:
			item.check()	
		
		results = []
		for request in contents:
			result = self.process(request)
			results.append(result)
			
		return 'Ok!'


	def process(self, request):
		if request.method.startswith('_'):
			raise emen2.web.responsecodes.ForbiddenError, 'Method not Accessible'
		elif rpcrequest.method in set(['gg','pp']):
			if rpcrequest.method == 'pp':
				return self.q.put( (rpcrequest.args, rpcrequest.kwargs) )
			else:
				return self.q.get()
		elif rpcrequest.method not in db._publicmethods:
			try:
				# emen2.db.log.debug('method \'pub.%s\' called' % rpcrequest.method)
				methodresult = emen2.web.events.EventRegistry().event('pub.%s' % rpcrequest.method)(self.ctxid, request.getClientIP(), db=db, *rpcrequest.args, **rpcrequest.kwargs)
			except Exception, e:
				# emen2.db.log.error('Exception:', e)
				print e
				import traceback
				traceback.print_exc()
				raise
		else:
			# print "method/write", method, db._checkwrite(method)
			db._starttxn(write=db._checkwrite(rpcrequest.method))
			with db._autoclean():
				ctxid = self.ctxid #request.getCookie('ctxid')
				#ctxid = rpcrequest.kwargs.pop('ctxid',  rpcrequest.extra['ctxid'])
				if rpcrequest.method.split('.')[-1] == 'login':
					rpcrequest.kwargs['host'] = request.getClientIP()
				else:
					rpcrequest.kwargs.pop('host', None)
					db._setContext(ctxid,request.getClientIP())

				methodresult = db._callmethod(rpcrequest.method, rpcrequest.args, rpcrequest.kwargs)


				method = rpcrequest.method.rpartition('.')[2]
				if method in set(['login', 'logout']):
					request.addCookie('ctxid', methodresult or '')
			# end db access

		return methodresult


class XMLRPCProxy(View):
	pass