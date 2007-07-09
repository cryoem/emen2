#import re
#import os
#from sets import Set
#import pickle
#import traceback
#import time
#import random
import timing
import time
import random

DEBUG = 1

from emen2 import ts 
from emen2.ts import db

#from emen2.TwistSupport_html import html

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
#from twisted.web import http
#from twisted.python import threadable, log, components, failure, filepath
from twisted.python import filepath, log, failure
#from twisted.internet import abstract, interfaces, defer
from twisted.internet import defer, reactor, threads
#from twisted.spread import pb
#from twisted.persisted import styles
#from twisted.python.util import InsensitiveDict
#from twisted.python.runtime import platformType


from twisted.web.resource import Resource
from twisted.web.static import *

class DBResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""

	

	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		global db,callbacks

		t0 = time.time()


		# Redirects
		if (len(request.postpath)==0):
			request.postpath.append("home")
			request.uri = "/db/home"
		if (len(request.postpath[0])==0):
			request.postpath[0] = "home"
			request.uri = "/db/home"
			
		# Startup
		session=request.getSession()			# sets a cookie to use as a session id
		method=request.postpath[0]
		host=request.getClientIP()
		print "\n--------- request ----------------\nGet: %s"%request.uri

#		print request.args
		
		try:
			session.ctxid = request.args["ctxid"][0]
			#		print request.getClientIP()
			db.checkcontext(session.ctxid,request.getClientIP())
			print "Got ctxid from args"
		except:
			pass
#			print request.args["ctxid"][0]
#			print "no ctxid from args"



		try:
			ctxid = session.ctxid
			db.checkcontext(ctxid,request.getClientIP())
		except:
			try:			
				session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
			
				ctxidcookiename = 'TWISTED_SESSION_ctxid'
				request.addCookie(ctxidcookiename, session.ctxid, path='/')
			
				print "ctxid: %s"%session.ctxid
				return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
						<meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest
			except ValueError, TypeError:
				print "Authentication Error"
				print "...original request: %s"%session.originalrequest
				return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,None,None,redir=session.originalrequest,failed=1)
			except KeyError:
				print "Need to login..."

				# Is it a page that does not require authentication?
				if (request.postpath[0] == "home"):
					return emen2.TwistSupport_html.html.home.home(request.postpath,request.args,None,host)
				if (request.postpath[0]=="newuser"):
					return emen2.TwistSupport_html.html.newuser.newuser(request.postpath,request.args,None,request.getClientIP())
	

				if request.uri == "/db/login":
					session.originalrequest = "/db/"
				else:
					session.originalrequest = request.uri
					
#				print "...requesting: %s"%request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)
			


		# Ok, if we got here, we can actually start talking to the database

		exec("import emen2.TwistSupport_html.html.%s"%method)		
		if DEBUG:
			exec("reload(emen2.TwistSupport_html.html.%s)"%method)

#		ret=eval("emen2.TwistSupport_html.html."+method+"."+method)(request.postpath,request.args,ctxid,host)
#		function = getattr(, method, None)
		exec("function = emen2.TwistSupport_html.html.%s.%s"%(method,method))

		d = threads.deferToThread(function, request.postpath, request.args, ctxid, host)
		d.addCallback(self._cbRender, request, time.time())
		d.addErrback(self._ebRender, request, time.time())

		return server.NOT_DONE_YET 


	
	def _cbRender(self, result, request, t0):
		# JPEG Magic Number
		if result[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if result[:4]=="\x89PNG" : request.setHeader("content-type","image/png")

		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()
 		print "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)
		return

	def _ebRender(self, failure, request, t0):
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()
 		print "::::microsec for complete request %s"%int((time.time() - t0) * 1000000)
		return

#		return
#		print "ebRender..."
#		print "request"
#		print request
#		print "failure"
#		request.write(str(failure))
#		request.finish()
#		return ""


class UploadFile(Resource):
	isLeaf = True

	def render(self,request):
		print "-------- upload -----------"
#		print request.args
		print request.postpath
		args=request.args

		if args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				db.checkcontext(ctxid,request.getClientIP())
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)	


		binary = 0
		if args.has_key("file_binary_image"): 
			binary = args["file_binary_image"][0]


		fname = db.checkcontext(ctxid)[0] + " " + time.strftime("%Y/%m/%d %H:%M:%S")
		if args.has_key("fname"): 
			fname = args["fname"][0]


		recid=int(request.postpath[0])
		rec = ts.db.getrecord(recid,ctxid)
#		print rec			
				
		# append to file (chunk uploading) or all at once.. 
		if args.has_key("append"):
			a = ts.db.getbinary(args["append"][0],ctxid)
			print "Appending to %s..."%a[1]
			outputStream = open(a[1], "ab")
			outputStream.write(args["filedata"][0])
			outputStream.close()

		# new file
		else:
			print "Get binary..."
			a = ts.db.newbinary(time.strftime("%Y/%m/%d %H:%M:%S"),fname.split("/")[-1].split("\\")[-1],rec.recid,ctxid)

#			can't use basename
#			a = ts.db.newbinary(time.strftime("%Y/%m/%d %H:%M:%S"),os.path.basename(fname),rec.recid,ctxid)

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
	
			ts.db.putrecord(rec,ctxid)

		if args.has_key("rbid"):
			return str(a[0])
		else:
			return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
							<meta http-equiv="REFRESH" content="0; URL=/db/record/%s?notify=3">"""%recid



class DownloadFile(Resource, filepath.FilePath):

	isLeaf = True

	contentTypes = loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	type = None
	defaultType="application/octet-stream"

	def render(self, request):
		"""You know what you doing."""

		# auth...

		if request.args.has_key("ctxid"):
			ctxid = request.args["ctxid"][0]
		else:
			try:
				session=request.getSession()			# sets a cookie to use as a session id
				ctxid = session.ctxid
				db.checkcontext(ctxid,request.getClientIP())
			except:
				print "Need to login..."
				session.originalrequest = request.uri
				return emen2.TwistSupport_html.html.login.login(request.uri,None,None,None,redir=request.uri,failed=0)	


		
		bids = request.postpath[0].split(",")

		if len(bids) > 1:
			ipaths=[]
			for i in bids:
				bname,ipath,bdocounter=ts.db.getbinary(i,ctxid)						
				ipaths.append((ipath,bname))


			self.type, self.encoding = "application/octet-stream", None
			fsize = size = 0
			
			request.setHeader('content-type', self.type)
			request.setHeader('content-encoding', self.encoding)

			import tarfile

			# how many *hours* do you think I wasted before realizing I could simply give it the request as the file object?
			tar = tarfile.open(mode="w|", fileobj=request)

			for name in ipaths:
				print "adding %s as %s"%(name[0],name[1])
				tar.add(name[0],arcname=name[1])
			tar.close()

			request.finish()



		else:		
			bid = request.postpath[0]
			bname,ipath,bdocounter=ts.db.getbinary(bid,ctxid)

			self.path = ipath
			self.type, self.encoding = getTypeAndEncoding(bname, self.contentTypes,	self.contentEncodings, self.defaultType)
			f = self.open()
			fsize = size = os.stat(ipath).st_size

	#		fsize = size = self.getsize()
			if self.type:	request.setHeader('content-type', self.type)
			if self.encoding:	request.setHeader('content-encoding', self.encoding)
			if fsize:	request.setHeader('content-length', str(fsize))

			if request.method == 'HEAD':	return ''

			FileTransfer(f, size, request)
			# and make sure the connection doesn't get closed
			return server.NOT_DONE_YET
		
		
		
		