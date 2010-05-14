# $Author$ $Revision$
import re
import os
import pickle
import traceback
import time
import random
import atexit
import cStringIO
import urllib
import demjson


# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads
from twisted.web.resource import Resource
from twisted.web.static import *


# emen2 imports
import emen2.globalns

g = emen2.globalns.GlobalNamespace()


class UploadResource(Resource):
	isLeaf = True


	def render_POST(self, request):

		# ian: ugly hack around broken twisted.web post form
		if not request.args.has_key("filename"):
			request.content.seek(0)
			content=request.content.read()
			b=re.compile("filename=\"(.+)\"")
			filename=b.findall(content[:5000])[0]
		else:
			filename=request.args.get("Filename",[''])[0] # ["Filename"][0]

		return self.render_PUT(request, filename=filename, filedata=request.args["filedata"][0])



	def render_PUT(self, request, filename=None, filedata=None):

		host = request.getClientIP()
		args = request.args
		request.postpath = filter(bool, request.postpath)
		ctxid = request.getCookie("ctxid") or args.get('ctxid',[None])[0]
		username = args.get('username',[''])[0]
		pw = args.get('pw',[''])[0]


		# Is a record included? In JSON format, urlencoded...
		# This will call putrecord and attach the binary to the new record
		# "record" as well as "newrecord" for backwards compat... "newrecord" is semantically better
		
		newrecord = args.get('newrecord',[None])[0] or args.get('record',[None])[0]
		if newrecord:
			try:
				newrecord = demjson.decode(urllib.unquote(newrecord))
			except ValueError, e:
				raise ValueError, "Invalid JSON record: %s"%e


		if filename==None:
			if args.has_key("filename"):
				filename=args["filename"][0].split("/")[-1].split("\\")[-1]
			else:
				filename="No_Filename_Specified"

		try:
			recid = int(request.postpath[0])
		except (IndexError, TypeError, ValueError):
			recid = None
			
		param = str(args.get("param",["file_binary"])[0])
		redirect = args.get("redirect",[0])[0]

		g.log.msg("LOG_INFO", "====== uploadresource action: %s, %s, filename=%s, recid=%s, param=%s"%(username, host, filename, recid, param))

		d = threads.deferToThread(self._action, newrecord=newrecord, recid=recid, param=param, filename=filename, filehandle=request.content, filedata=filedata, redirect=redirect, ctxid=ctxid, host=host)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET



	def _action(self, newrecord=None, recid=None, param=None, filename=None, filehandle=None, filedata=None, redirect=None, ctxid=None, host=None, db=None):

		with db._setContext(ctxid,host):
			if newrecord:
				crec = db.putrecord(newrecord, filt=False)
				recid = crec.recid
			bdokey = db.putbinary(filename, recid, param=param, filedata=filedata, filehandle=filehandle)

		if redirect:
			return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="REFRESH" content="0; URL=%s">"""%redirect

		return demjson.encode(bdokey).encode("utf-8")




	def _cbRender(self,result,request):
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()


	# def _ebRender(self,failure,request):
	# 	#request.write(emen2.TwistSupport_html.html.error.error(failure))
	# 	request.setResponseCode(500)
	# 	request.finish()

	def _ebRender(self, result, request, *args, **kwargs):
		g.log.msg("LOG_ERROR", result)
		request.setHeader("X-Error", result.getErrorMessage())	
		result=unicode(result.value)
		result=result.encode('utf-8')
		request.setHeader("content-length", len(result))
		request.setResponseCode(500)
		# g.log.msg('LOG_WEB', '%(host)s - - [%(time)s] %(path)s %(response)s %(size)d' % dict(
		# 	host = request.getClientIP(),
		# 	time = time.ctime(),
		# 	path = request.uri,
		# 	response = request.code,
		# 	size = len(result)
		# ))
		request.write(result)
		request.finish()



__version__ = "$Revision$".split(":")[1][:-1].strip()
