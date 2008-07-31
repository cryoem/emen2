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


class UploadBatchResource(Resource):
	isLeaf = True
	
	def render(self, request):
		host=request.getClientIP()
		session=request.getSession()
		args=request.args
		path=request.postpath
		ctxid=None
		
		print "== upload request !! =="
		
		ctxid = request.getCookie("ctxid")

		print "test ctxid: %s"%ctxid

		if hasattr(session,"ctxid"):
			print "Upload ctxid: %s"%session.ctxid
			ctxid=session.ctxid
		else:
			print "No ctxid"
		
		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, ctxid=ctxid, host=host, session=session)		
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET
		
				
		
	def RenderWorker(self,path,args,ctxid=None,host=None,session=None,db=None):

		pass
			


class UploadResource(Resource):
	isLeaf = True


	def render(self,request):
		host=request.getClientIP()
		session=request.getSession()
		args=request.args
		path=request.postpath
		ctxid=None
		
		print "== upload request !! =="
		
		ctxid = request.getCookie("ctxid")

		print "test ctxid: %s"%ctxid

		if hasattr(session,"ctxid"):
			print "Upload ctxid: %s"%session.ctxid
			ctxid=session.ctxid
		else:
			print "No ctxid"
		
		d = threads.deferToThread(self.RenderWorker, request.postpath, request.args, ctxid=ctxid, host=host, session=session)		
		d.addCallback(self._cbRender, request)
		d.addErrback(self._ebRender, request)
		return server.NOT_DONE_YET
		
		
	def RenderWorker(self,path,args,ctxid=None,host=None,session=None,db=None):
		filename=args["Filename"][0]
		filedata=args["Filedata"][0]
		
		recid=int(path[0])
		param = "file_binary"
		if args.has_key("param"): 
			param = args["param"][0]		

		
		print "\n\n========================="
		print filename
		print len(filedata)
		print session
		return "ok"		
		


	def _cbRender(self,result,request):
		request.setHeader("content-length", str(len(result)))
		request.write(result)
		request.finish()
		

	def _ebRender(self,failure,request):
		print failure
		#request.write(emen2.TwistSupport_html.html.error.error(failure))
		request.finish()	

	def render_PUT_OLD(self,request):
		return self.render2(request,request.content)

	def render_POST_OLD(self,request):

		request.content.seek(0,0)
		content = request.content.read()
		request.content.seek(0,0)
		
		headers = request.received_headers
		boundary="--"+headers["content-type"].split("boundary=")[1]
		parts=content.split(boundary)

		#todo: extend support for multiple file upload (this existed at one point in the past.)
		
		re_filename=re.compile("filename=\"(?P<filename>.+)\"")
		# in case there is a large upload, don't regex the entire thing..
		iter = re_filename.finditer(parts[1][:1000])
		for match in iter:
			request.args["name"]= [match.group("filename")]
		
		content = cStringIO.StringIO(request.args["filedata"][0])
		return self.render2(request,content)

	def render2_OLD(self,request,content):

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
		
	def RenderWorker_OLD(self,path,args,content,ctxid,host,db=None):

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