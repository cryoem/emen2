import os
import cgi
import time
import xmlrpclib
import demjson

# Twisted imports
from twisted.web import server, xmlrpc
from twisted.internet import threads
from twisted.web.resource import Resource

# emen2 imports
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')
import UserDict, collections
collections.Mapping.register(UserDict.DictMixin)


import emen2.Database.dataobjects
import emen2.util.utils




class jsonrpc(Resource):
	isLeaf = True


	def _cbRender(self, result, request):
		request.setHeader("content-length", len(result))
		request.setHeader("content-type", 'application/json')
		request.setResponseCode(200)
		g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		result = demjson.encode(result).encode('utf-8')
		request.write(result)
		request.finish()



	def _ebRender(self, result, request, content, *args, **kwargs):
		result_template = dict(
			jsonrpc='2.0',
			error= dict(
				code=0,
				message='Stub Message',
				data = 'Stub Data'
		))

		g.log_error(result)
		try:
			#request.setHeader("X-Error", ' '.join(str(result).split()))
			request.setHeader("X-Error", result.getErrorMessage())
			result_template['error'].update(
					code=0,
					message=' '.join(str(x) for x in result.value),
					data=content
			)
			if isinstance(content, list):
				result_template['id'] = content[0].get('id', '<NULL>')
				result_template = [result]
			else: result_template['id'] = content.get('id')
		except Exception, e:
			result_template['error'].update(
				code = 0,
				message = 'Error in errorpage: %s' % e,
				data = ''
			)

		result = result_template
		result['error']['message'] = cgi.escape(result['error']['message'])
		result = demjson.encode(result)
		result = result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
			host = request.getClientIP(),
			time = time.ctime(),
			path = request.uri,
			response = request.code,
			size = len(result)
		))
		request.write(result)
		request.finish()



	def render(self, request):
		ctxid = request.getCookie("ctxid") or request.args.get("ctxid", [None])[0]
		host = request.getClientIP()

		request.content.seek(0, 0)
		content = demjson.decode(request.content.read())
		d = threads.deferToThread(self.action, request, content, ctxid=ctxid, host=host)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request, content)
		return server.NOT_DONE_YET


	typemapping = {
		emen2.Database.dataobjects.record.Record: 'record',
		emen2.Database.dataobjects.recorddef.RecordDef: 'recorddef',
		emen2.Database.dataobjects.paramdef.ParamDef: 'paramdef',
		emen2.Database.dataobjects.user.User: 'user',
		set: 'set',
		tuple: 'tuple',
	}
	revmap = dict( (y,x) for x,y in typemapping.iteritems() )

	def create_typemap(self, res):
		result = None
		if isinstance(res, (dict, collections.Mapping)):
			result = self.typemapping.get(type(res)), dict( (k, self.create_typemap(v)) for k,v in res.iteritems() )
		else:
			result = self.typemapping.get(type(res))
		return result



	@g.log.debug_func
	#@emen2.util.utils.return_list_or_single('contents')
	def action(self, request, contents, db=None, ctxid=None, host=None):
		ol = True
		if not isinstance(contents, list):
			contents = [contents]
			ol = False

		g.debug('jsonrpc contents: %r' %contents)
		result = []

		for content in contents:
			if content.get('jsonrpc') != '2.0': raise ValueError, 'wrong JSON-RPC version'
			method = content.get('method')
			kwargs = content.get('params', {})
			args = kwargs.pop('__args', ())
			kwargs = dict( (str(k), v) for k,v in kwargs.items() )

			ctxid = ctxid or kwargs.pop('ctxid', None)
			g.debug('ctxid: %r, host: %r' % (ctxid, host))

			g.log.msg("LOG_INFO", "====== RPCResource action: method %s ctxid %s host %s"%(method, ctxid, host))
			with db._setcontext(ctxid,host):
				methodresult = db._callmethod(method, args, kwargs)

			res = {
				'jsonrpc': '2.0',
				'id': content.get('id'),
				'result': methodresult,
				'type': self.create_typemap(methodresult)
			}

			result.append(res)

		g.debug('jsonrpc result: %r' %result)
		if not ol: result = result[0]
		g.debug('jsonrpc result: %r' %result)
		return result



