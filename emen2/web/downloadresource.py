import re
import os
import pickle
import traceback
import time
import random
import cStringIO


# Twisted Imports
from twisted.python import failure, filepath
from twisted.internet import defer
from twisted.web.resource import Resource
from twisted.web.static import *



##########################################
# Download Resource

class DownloadResource(Resource, File):

	isLeaf = True

	contentTypes = loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	type = None
	defaultType="application/octet-stream"


	def render_GET(self, request):

		host = request.getClientIP()
		args = request.args
		request.postpath = filter(bool, request.postpath)		
		ctxid = request.getCookie("ctxid")
		
		if not ctxid:
			if request.args.get("ctxid"):
				g.debug("got ctxid from kwargs")
				ctxid = request.args.get("ctxid",[None])[0]
		
		#username = args.get('username',[''])[0]
		#pw = args.get('pw',[''])[0]
		
		#authen = auth.Authenticator(db=ts.db, host=host)
		#authen.authenticate(username, pw, ctxid)
		#ctxid, un = authen.get_auth_info()
		
		g.debug("\n\n:: download :: %s :: %s"%(request.uri, host))

		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, ctxid, host)	
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET		
		
		
		
	def RenderWorker(self, path, args, ctxid, host, db=None):
		""" thread worker to get file paths from db; hand back to resource to send """
		
		bids = path[0].split(",")

		ipaths=[]
		for i in bids:
			bname,ipath,bdocounter=db.getbinary(i,ctxid=ctxid,host=host)						
			#ipath="/Users/irees/emen2/emen2/startup.sh"
			ipaths.append((ipath,bname))
			g.debug("download list: %s  ...  %s"%(ipath,bname))	
		return ipaths


	def _cbRender(self, ipaths, request):
		"""You know what you doing."""


		if len(ipaths) > 1:
			self.type, self.encoding = "application/octet-stream", None
			fsize = size = 0
			
			request.setHeader('content-type', self.type)
			request.setHeader('content-encoding', self.encoding)

			import tarfile
			
			tar = tarfile.open(mode="w|", fileobj=request)

			for name in ipaths:
				g.debug("adding %s as %s"%(name[0],name[1]))
				tar.add(name[0],arcname=name[1])
			tar.close()

			request.finish()
			del tarfile
			
		else:
			ipath = ipaths[0][0]
			bname = ipaths[0][1]

			self.path = ipath
			self.type, self.encoding = getTypeAndEncoding(bname, self.contentTypes,	self.contentEncodings, self.defaultType)
			self.alwaysCreate = False

			f = self.open()
			fsize = size = os.stat(ipath).st_size

			if self.type:	request.setHeader('content-type', self.type)
			if self.encoding:	request.setHeader('content-encoding', self.encoding)
			if fsize:	request.setHeader('content-length', str(fsize))

			if request.method == 'HEAD':	return ''

			FileTransfer(f, size, request)
			# and make sure the connection doesn't get closed
		
		
	def _ebRender(self,failure,request):

		errmsg="Test Error"
		errcode=500
		
 		try:
 			failure.raiseException()
 		except IOError,e:
			errcode=404
 			errmsg="File Not Found"
 		except Exception,e:
 			errmsg=str(e)

#		request.setHeader('X-ERROR', ' '.join(str(failure).split()))
		
		data = g.templates.render_template("/errors/error",context={"errmsg":errmsg,"title":"Error"}).encode('utf-8')

		request.setResponseCode(errcode)
		request.setHeader("content-type", "text/html; charset=utf-8")
		request.setHeader('content-length',len(data))
		request.write(data)
		
		request.finish()
		
		
		