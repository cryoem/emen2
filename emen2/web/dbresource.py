import re
import os
from sets import Set
import pickle
import traceback
#import timing
import time
import random
import atexit

DEBUG = 1

from emen2 import ts 
from emen2.emen2config import *

import emen2.TwistSupport_html.html.login
import emen2.TwistSupport_html.html.newuser
import emen2.TwistSupport_html.html.home
import emen2.TwistSupport_html.html.error

# Sibling Imports
from twisted.web import server
from twisted.web import error
from twisted.web import resource
from twisted.web.util import redirectTo

# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads

from twisted.web.resource import Resource
from twisted.web.static import *


class WebResourceDummy(Resource):
	isLeaf = True
	def render(self,request):
		session=request.getSession()
		t0=time.time()
		print "dummy render: %s"%request.postpath[0]
		ret = emen2.TwistSupport_html.html.record.record(["record",request.postpath[0]],{},ctxid="058ce38313e56e89c766ae6d866d5afeec79cc84",host=None,db=ts.db)
		print time.time()-t0
		return ret



class WebResource(Resource):
	isLeaf = True
	
	def render(self,request):
		session=request.getSession()
		t0 = time.time()
		host=request.getClientIP()

		if len(request.postpath) < 1:
			request.postpath.append("")
		method = request.postpath[0]
		if method == "": 
			request.postpath[0] = "home"
			method = "home"

#		ctxid=request.args["ctxid"][0]

		try:
			session.ctxid = request.args["ctxid"][0]
			user=ts.db.checkcontext(session.ctxid,host)[0]
		except:
			pass
 		try:
 			ctxid = session.ctxid
 			user=ts.db.checkcontext(ctxid,host)[0]
 		except:

			################# begin login ###################
			print "\n---- [%s] [%s] ---- login request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,request.postpath)
	
 			# Force login
 			try:			
				if request.args["username"][0] == "":
					raise ValueError
 				session.ctxid=ts.db.login(request.args["username"][0],request.args["pw"][0],host=request.getClientIP())
 			
 				ctxidcookiename = 'TWISTED_SESSION_ctxid'
 				request.addCookie(ctxidcookiename, session.ctxid, path='/')
 			
 				return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
 						<meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest
 			except ValueError, TypeError:
 				print "Authentication Error"
 				print "...original request: %s"%session.originalrequest
				if session.originalrequest==None:
					session.originalrequest="/db/"
 				return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,ctxid=None,host=host,redir=session.originalrequest,failed=1)
 			except KeyError:
 
 				# Is it a page that does not require authentication?
 				if (request.postpath[0] == "home"):
 					return emen2.TwistSupport_html.html.home.home(request.postpath,request.args,ctxid=None,host=host)
 				if (request.postpath[0]=="newuser"):
 					return emen2.TwistSupport_html.html.newuser.newuser(request.postpath,request.args,ctxid=None,host=host)
 				if request.uri == "/db/login":
 					session.originalrequest = "/db/"
 				else:
 					session.originalrequest = request.uri
 								
 				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)
			################# end login ###################
					
		print "\n---- [%s] [%s] [%s] ---- web request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)

		if method == "logout":
			ts.db.deletecontext(ctxid)
			return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">\n<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">"""					

		# authenticated; run page		
		
		exec("import emen2.TwistSupport_html.html.%s"%request.postpath[0])		
		
		module = getattr(emen2.TwistSupport_html.html,method)
		function = getattr(module,method)

		d = threads.deferToThread(function, request.postpath, request.args, ctxid=ctxid, host=host)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)

#		return emen2.TwistSupport_html.html.record.record(request.postpath, request.args, ctxid=ctxid, host=request.getClientIP(),db=ts.db)

		return server.NOT_DONE_YET
		


	def _cbRender(self,result,request,t0=None):
#		print result
		if result[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if result[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()
#		print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)
		
		
		
	def _ebRender(self,failure,request,t0=None):
		traceback.print_exc()
#		request.write(emen2.TwistSupport_html.html.error.error(inst))
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()
#		print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)

		

class UploadResource(Resource):
	isLeaf = True

	def render(self,request):
		d = threads.deferToThread(self.RenderWorker, request)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET		

		
	def _cbRender(self,result,request):
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()
		
	def _ebRender(self,failure,request):
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()	

	def RenderWorker(self,request,db=None):
		host=request.getClientIP()
		args=request.args

		if args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
			user=db.checkcontext(ctxid,host)[0]
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				user=db.checkcontext(ctxid,host)[0]
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)	


		print "\n---- [%s] [%s] [%s] ---- upload request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)


		binary = 0
		if args.has_key("file_binary_image"): 
			binary = args["file_binary_image"][0]


		fname = user + " " + time.strftime("%Y/%m/%d %H:%M:%S")
		if args.has_key("fname"): 
			fname = args["fname"][0]


		recid=int(request.postpath[0])
		rec = db.getrecord(recid,ctxid)
#		print rec			
				
		# append to file (chunk uploading) or all at once.. 
		if args.has_key("append"):
			a = db.getbinary(args["append"][0],ctxid)
			print "Appending to %s..."%a[1]
			outputStream = open(a[1], "ab")
			outputStream.write(args["filedata"][0])
			outputStream.close()

		# new file
		else:
			print "Get binary..."
			a = db.newbinary(time.strftime("%Y/%m/%d %H:%M:%S"),fname.split("/")[-1].split("\\")[-1],rec.recid,ctxid)

			print "Writing file... %s"%a[1]
			outputStream = open(a[1], "wb")
			outputStream.write(args["filedata"][0])
			outputStream.close()

			print "Setting file_binary of recid %s"%rec.recid
	
			if binary:
				rec["file_binary_image"] = "bdo:%s"%a[0]
				
			else:
				key = "file_binary"
				if not rec.has_key(key):
					rec[key] = []
				rec[key].append("bdo:%s"%a[0])
	
			db.putrecord(rec,ctxid)

		if args.has_key("rbid"):
			return str(a[0])
		else:
			return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
							<meta http-equiv="REFRESH" content="0; URL=/db/record/%s?notify=3">"""%recid



class DownloadResource(Resource, File):

	isLeaf = True

	contentTypes = loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	type = None
	defaultType="application/octet-stream"


	def render(self, request):
#		print "\n------ download request: %s ------"%request.postpath
		
		d = threads.deferToThread(self.RenderWorker, request)
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET		
		
		
		
	def RenderWorker(self, request, db=None):
		""" thread worker to get file paths from db; hand back to resource to send """
		# auth...
		
		host=request.getClientIP()
		
		if request.args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
			user=db.checkcontext(ctxid,host)[0]			
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				user=db.checkcontext(ctxid,host)[0]
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				raise KeyError	


		print "\n---- [%s] [%s] [%s] ---- download request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)


		bids = request.postpath[0].split(",")

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

	#		fsize = size = self.getsize()
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
