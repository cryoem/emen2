import re
import os
from sets import Set
import pickle
import traceback
#import timing
import time
import random
import atexit

import cStringIO

DEBUG = 1

from emen2 import ts 
from emen2.emen2config import *

import emen2.TwistSupport_html.html

##import emen2.TwistSupport_html.html.login
#import emen2.TwistSupport_html.html.newuser
#import emen2.TwistSupport_html.html.home
##import emen2.TwistSupport_html.html.error

# Sibling Imports
#from twisted.web import server
#from twisted.web import error
#from twisted.web import resource
#from twisted.web.util import redirectTo

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
		host=request.getClientIP()
		
		if request.args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
			user=ts.db.checkcontext(ctxid,host)[0]			
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				user=ts.db.checkcontext(ctxid,host)[0]
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				raise KeyError	
		
		
		print "\n---- [%s] [%s] [%s] ---- download request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)

		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, ctxid, host)	
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET		
		
		
		
	def RenderWorker(self, path, args, ctxid, host, db=None):
		""" thread worker to get file paths from db; hand back to resource to send """
		# auth...
		
		bids = path[0].split(",")

		ipaths=[]
		for i in bids:
			bname,ipath,bdocounter=db.getbinary(i,ctxid)						
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
			print "open file."
			self.alwaysCreate = False
			f = self.open()
			fsize = size = os.stat(ipath).st_size

#			fsize = size = self.getsize()
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
