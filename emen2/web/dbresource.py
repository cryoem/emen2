import re
import os
from sets import Set
import pickle
import traceback
import timing
import time
import random
import atexit

DEBUG = 1

from emen2 import ts 
from emen2.emen2config import *
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
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads


from twisted.web.resource import Resource
from twisted.web.static import *






class WebResource(Resource):
	isLeaf = True
	
	def render(self,request):
# Ok, if we got here, we can actually start talking to the database
		ts.queue.put((self.WebWorker,request))
#		self.WebWorker(request,db=ts.db)
		return server.NOT_DONE_YET 


	def WebWorker(self,request,db=None):
		print "\n------ web request: %s ------"%request.postpath
		session=request.getSession()
		t0 = time.time()

		try:
			ctxid = session.ctxid
		except:
			if request.args.has_key("ctxid"):
				ctxid=request.args["ctxid"][0]
			else:
				try:
					session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
					ctxid = session.ctxid
					ctxidcookiename = 'TWISTED_SESSION_ctxid'
					request.addCookie(ctxidcookiename, session.ctxid, path='/')	
					return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
                    <meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest									
				except ValueError, TypeError:
					print "Authentication Error"
					return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,None,None,redir=session.originalrequest,failed=1)
				except:
					print "Need to login..."

					# Is it a page that does not require authentication?
#					if (request.postpath[0] == "home"):
#						return emen2.TwistSupport_html.html.home.home(request.postpath,request.args,None,request.getClientIP())
#					if (request.postpath[0]=="newuser"):
#						return emen2.TwistSupport_html.html.newuser.newuser(request.postpath,request.args,None,request.getClientIP())

#					if request.uri == "/db/login":
#						session.originalrequest = "/db/"
#					else:
#						session.originalrequest = request.uri

					request.write(emen2.TwistSupport_html.html.login.login(None,None,None,None,redir=request.uri))
					request.finish()
					return

		# authenticated; run page
		try:
			method = request.postpath[0]
			
			exec("import emen2.TwistSupport_html.html.%s"%request.postpath[0])		
			module = getattr(emen2.TwistSupport_html.html,method)
			function = getattr(module,method)


			result = function( request.postpath, request.args, ctxid=ctxid, host=request.getClientIP(),db=db)

			if result[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
			if result[:4]=="\x89PNG" : request.setHeader("content-type","image/png")


			request.setHeader("content-length", str(len(result)))
			request.write(result)
			request.finish()

		except Exception, inst:
			traceback.print_exc()
			request.write(emen2.TwistSupport_html.html.error.error(inst))
			request.write("failure")
			request.finish()

		print ":::ms: %i"%((time.time()-t0)*1000000)
		return




class UploadResource(Resource):
	isLeaf = True

	def render(self,request):
		ts.queue.put((self.UploadWorker,request))
		return server.NOT_DONE_YET 


	def UploadWorker(self,request,db=None):
		print "\n-------- upload -----------"
		args=request.args


		try:
			ctxid = request.getSession().ctxid
		except:
			if request.args.has_key("ctxid"):
				ctxid=request.args["ctxid"][0]
			else:
				try:
					request.getSession().ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
					ctxid = request.getSession().ctxid
				except:
					print "need to login..."						
					request.write(emen2.TwistSupport_html.html.login.login(None,None,None,None))
					request.finish()
					return


		binary = 0
		if request.args.has_key("file_binary_image"): 
			binary = args["file_binary_image"][0]

		fname = db.checkcontext(ctxid)[0] + " " + time.strftime("%Y/%m/%d %H:%M:%S")
		if request.args.has_key("fname"): 
			fname = args["fname"][0]

		recid=int(request.postpath[0])
		rec = db.getrecord(recid,ctxid)
			
		# append to file (chunk uploading) or all at once.. 
		if request.args.has_key("append"):
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

		if request.args.has_key("rbid"):
			request.write(str(a[0]))
		else:
			request.write("""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
							<meta http-equiv="REFRESH" content="0; URL=/db/record/%s?notify=3">"""%recid)

		request.finish()



class DownloadResource(Resource,filepath.FilePath):
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
		ts.queue.put((self.DownloadWorker,request))
		return server.NOT_DONE_YET

	def DownloadWorker(self,request,db=None):
		# auth...
		try:
			ctxid = request.getSession().ctxid
		except:
			if request.args.has_key("ctxid"):
				ctxid=request.args["ctxid"][0]
			else:
				try:
					request.getSession().ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
					ctxid = request.getSession().ctxid
				except:
					print "need to login..."						
					request.write(emen2.TwistSupport_html.html.login.login(None,None,None,None))
					request.finish()
					return
					
					
		bids = request.postpath[0].split(",")

		if len(bids) > 1:
			ipaths=[]
			for i in bids:
				bname,ipath,bdocounter=db.getbinary(i,ctxid)						
				ipaths.append((ipath,bname))


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

		else:		
			bid = request.postpath[0]
			bname,ipath,bdocounter=db.getbinary(bid,ctxid)

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
			
		
		
		
		