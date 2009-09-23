import re
import os
import pickle
import traceback
import time
import random
import atexit
import cStringIO

# emen2 imports
from emen2 import ts
from emen2.Database import exceptions
import emen2.Database.database
import emen2.globalns
g = emen2.globalns.GlobalNamespace()


from emen2.subsystems import routing#, auth

# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads
from twisted.web.resource import Resource
from twisted.web.static import *


DEBUG = 1


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

		#authen = auth.Authenticator(db=ts.db, host=host)
		#authen.authenticate(username, pw, ctxid, host=host)
		#ctxid, un = authen.get_auth_info()

		if filename==None:
			if args.has_key("name"):
				filename=args["name"][0].split("/")[-1].split("\\")[-1]
			else:
				filename="No_Filename_Specified"

		recid = int(request.postpath[0])
		param = str(args.get("param",["file_binary"])[0]) #.strip().lower()
		redirect = args.get("redirect",[0])[0]


		#print "Request headers"
		#print request.getAllHeaders()

		if not filedata:
			filedata = ""
			content.seek(0,0)
			chunk = content.read()
			while chunk:
				chunk = content.read()
				filedata += chunk

		g.debug.msg("LOG_INFO", "====== uploadresource action: %s, %s, filename=%s, len=%s, recid=%s, param=%s"%(username, host, filename, len(filedata), recid, param))

		d = threads.deferToThread(self._action, recid=recid, param=param, filename=filename, content=request.content, filedata=filedata, redirect=redirect, ctxid=ctxid, host=host)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET



	def _action(self, recid=None, param=None, filename=None, content=None, filedata=None, redirect=None,ctxid=None,host=None,db=None):
		db._starttxn()
		db._setcontext(ctxid,host)

		try:
			bdokey = db.putbinary(filename, recid, filedata=filedata)
		except Exception, e:
			db._aborttxn()
			raise
		else:
			db._committxn()

		if redirect:
			return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="REFRESH" content="0; URL=%s">"""%redirect

		return bdokey




	def _cbRender(self,result,request):
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()


	def _ebRender(self,failure,request):
		print failure
		#request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()



