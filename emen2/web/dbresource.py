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
#import emen2.TwistSupport_html.html.newuser
#import emen2.TwistSupport_html.html.home
import emen2.TwistSupport_html.html.error

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

def checkwebcontext(request):
	session=request.getSession()

class WebResource(Resource):
	isLeaf = True
	
	def render(self,request):
		t0 = time.time()
		session=request.getSession()
		host=request.getClientIP()
		args=request.args

		# pages that do not require login
		anonmethods = ["home","newuser"]

		# home
		if len(request.postpath) < 1:
			request.postpath.append("home")

		method = request.postpath[0]
		if method == "": method = "home"

		# Check if context ID is good, else login or view anon page
		if not hasattr(session,"ctxid"):
			session.ctxid = None
		if args.has_key("ctxid"):
			session.ctxid = args["ctxid"][0]

		try:
			user=ts.db.checkcontext(session.ctxid,host)[0]
		except KeyError:
			user=None
			# only a few methods are available without login
			if method in anonmethods and not args.has_key("username"):
				pass

			else:
				
				print "\n---- [%s] [%s] ---- login request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,request.postpath)					
				
#				if not hasattr(session,"originalrequest"):
				if request.uri == "/db/login":
					session.originalrequest = "/db/home"
				else:
					session.originalrequest = request.uri		
				print "Set originalrequest to %s"%session.originalrequest

				try:
					session.ctxid=ts.db.login(request.args["username"][0],request.args["pw"][0],host=request.getClientIP())

				# Bad login
				except ValueError, TypeError:
					return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,ctxid=None,host=host,redir=session.originalrequest,failed=1)

				# Have not tried to login yet
				except KeyError:
					return emen2.TwistSupport_html.html.login.login(session.originalrequest,None,ctxid=None,host=host,redir=session.originalrequest)
					
				# Ok, good login; redir to requested page
				ctxidcookiename = "TWISTED_SESSION_ctxid"
				request.addCookie(ctxidcookiename, session.ctxid, path='/')
				print "original request: %s"%session.originalrequest
				return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="REFRESH" content="0; URL=%s">"""%session.originalrequest			


		print "\n---- [%s] [%s] [%s] ---- web request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)

		if method == "logout":
			session.ctxid = None
			session.expire()
			ts.db.deletecontext(session.ctxid)
			return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">"""					

		##########################
		# authenticated; run page				
		try:
			exec("import emen2.TwistSupport_html.html.%s"%method)		
		except ImportError:
			method = "home"
			exec("import emen2.TwistSupport_html.html.%s"%method)		

		if DEBUG: exec("reload(emen2.TwistSupport_html.html.%s)"%method)

		module = getattr(emen2.TwistSupport_html.html,method)
		function = getattr(module,method)

		d = threads.deferToThread(function, request.postpath, request.args, ctxid=session.ctxid, host=host)
		d.addCallback(self._cbRender, request, t0=t0)
		d.addErrback(self._ebRender, request, t0=t0)

#		return emen2.TwistSupport_html.html.record.record(request.postpath, request.args, ctxid=ctxid, host=request.getClientIP(),db=ts.db)

		return server.NOT_DONE_YET
		


	def _cbRender(self,result,request,t0=None):		

		try:
			result=result.encode("utf-8")
		except:
			pass


		if result[:3]=="\xFF\xD8\xFF":
			request.setHeader("content-type","image/jpeg")
		elif result[:4]=="\x89PNG":
			request.setHeader("content-type","image/png")
		else:
			try:
				result=result.encode("utf-8")
			except:
				pass
			request.setHeader("content-type","text/html; charset=utf-8")

		request.setHeader("content-length", str(len(result)))
		
		# no caching
		request.setHeader("Cache-Control","no-cache"); #HTTP 1.1
		request.setHeader("Pragma","no-cache"); #HTTP 1.0
		#request.setDateHeader("Expires", 0); #caching en proxy 
		
		request.write(result)
		request.finish()
		if TIME: print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)
		
		
		
	def _ebRender(self,failure,request,t0=None):
		traceback.print_exc()
#		request.write(emen2.TwistSupport_html.html.error.error(inst))
		print failure
		request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()
		if TIME: print ":::ms TOTAL: %i"%((time.time()-t0)*1000000)

		






class UploadResource2(Resource):
	isLeaf = True
	
	def __init__(self):
		Resource.__init__(self)

	def render(self, request):
		request.content.seek(0,0)
		f = file('data.dat','wb')

		f.write(request.content.read())

		return "ok"
#		request.write('OK')
#		request.finish()

##########################################
# Upload Resource

class UploadResource(Resource):
	isLeaf = True

	def render_PUT(self,request):
		return self.render2(request,request.content)

	def render_POST(self,request):
		content = StringIO(args["filedata"][0])
		return self.render2(request,content)

	def render2(self,request,content):

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
		
		print "\n---- [%s] [%s] [%s] ---- upload request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,user,request.postpath)

		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, content, ctxid, host)		
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


	def RenderWorker(self,path,args,content,ctxid,host,db=None):

		param = "file_binary"
		if args.has_key("param"): 
			param = args["param"][0]

		if args.has_key("name"): 
			name = args["name"][0]
		else:
			user=db.checkcontext(ctxid)[0]
			name = user + " " + time.strftime("%Y/%m/%d %H:%M:%S")


		recid = int(path[0])
		rec = db.getrecord(recid,ctxid)
				
				
		###################################		
		# Append to file, or make new file.
		if args.has_key("append"):
			a = db.getbinary(args["append"][0],ctxid)
			print "Appending to %s..."%a[1]
			outputStream = open(a[1], "ab")

			chunk=content.read()
			while chunk:
				outputStream.write(chunk)
				chunk=content.read()
				
			outputStream.close()
			
			return str(a[0])

		###################
		# New file
		print "Get binary..."
		# fixme: use basename and splitext
		a = db.newbinary(time.strftime("%Y/%m/%d %H:%M:%S"),name.split("/")[-1].split("\\")[-1],rec.recid,ctxid)

		print "Writing file... %s"%a[1]
		outputStream = open(a[1], "wb")

		content.seek(0,0)
		chunk=content.read()
		while chunk:
			outputStream.write(chunk)
			chunk=content.read()
		outputStream.close()


		######################
		# Update record
		if param == "file_binary_image":
			rec[param] = "bdo:%s"%a[0]
		else:
			if not rec.has_key(param):
				rec[param] = []
			if type(rec[param]) == str:
				rec[param] = [rec[param]]
			rec[param].append("bdo:%s"%a[0])
			
		db.putrecord(rec,ctxid)

		if args.has_key("redirect"):
			return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
							<meta http-equiv="REFRESH" content="0; URL=/db/record/%s?notify=3">"""%recid

		return str(a[0])


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
