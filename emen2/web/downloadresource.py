import re
import os
import pickle
import traceback
import time
import random
import cStringIO

DEBUG = 1


from emen2 import ts 
from emen2.emen2config import *
from emen2 import Database, ts
import emen2.TwistSupport_html.html
from emen2.subsystems import routing, auth


# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads
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
				print "got ctxid from kwargs"
				ctxid = request.args.get("ctxid",[None])[0]
		
		username = args.get('username',[''])[0]
		pw = args.get('pw',[''])[0]
		
		authen = auth.Authenticator(db=ts.db, host=host)
		authen.authenticate(username, pw, ctxid)
		ctxid, un = authen.get_auth_info()
		
		print "\n\n=== download request === %s :: %s :: %s"%(request.postpath, args, ctxid)

		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, ctxid, host)	
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET		
		
		
		
	def RenderWorker(self, path, args, ctxid, host, db=None):
		""" thread worker to get file paths from db; hand back to resource to send """
		
		bids = path[0].split(",")

		ipaths=[]
		for i in bids:
			bname,ipath,bdocounter=db.getbinary(i,ctxid)						
			ipath="/Users/irees/emen2/emen2/startup.sh"
			ipaths.append((ipath,bname))
			print "download list: %s  ...  %s"%(ipath,bname)	
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
				print "adding %s as %s"%(name[0],name[1])
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
		print failure
		request.write("Error with request.")
		request.finish()
