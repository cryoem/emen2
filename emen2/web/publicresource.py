from __future__ import with_statement
import re
import os
from sets import Set
import pickle
import traceback
import time
import random
import atexit
import cStringIO

import sys
from emen2 import ts
from emen2.emen2config import *


from emen2.TwistSupport_html.public import routing
import emen2.TwistSupport_html.html.error

# Twisted Imports
from twisted.python import filepath, log, failure
from twisted.internet import defer, reactor, threads

from twisted.web.resource import Resource
from twisted.web.static import *

import debugging as debug

DEBUG = 1
from cgi import escape



class PublicView(Resource):
		isLeaf = True
		redirects = {}

		@classmethod
		def getredirect(cls, name):
			return cls.redirects.get(name, False)

		@classmethod
		def register_redirect(cls, fro, to, *args, **kwargs):
			cls.redirects[fro] = routing.URLRegistry.reverselookup(to, *args, **kwargs)

		@classmethod
		def __registerurl(cls, name, match, cb):
				'''register a pattern to select urls

				arguments:
						name -- the name of the url to be registered
						regex -- the regular expression that applies 
										 as a string
						cb -- the callback function to call
				'''
				return routing.URL(name, re.compile(match), cb)

		@classmethod
		def register_url(cls, name, match):
				print "Registering URL:"
				print cls
				print name
				print match
				print ""
				def _reg_inside(cb):
						cls.__registerurl(name, re.compile(match), cb)
						return cb
				return _reg_inside

		def render(self, request):
				response = str(request)



				t0 = time.time()
				session=request.getSession()
				host=request.getClientIP()
				args=request.args

				request.postpath = filter(bool, request.postpath) or ["home"]

				method = request.postpath[0]

				# Check if context ID is good, else login or view anon page
				if not hasattr(session,"ctxid"):
						session.ctxid = None
				if args.has_key("ctxid"):
						session.ctxid = args["ctxid"][0]

				try:
						user=ts.db.checkcontext(session.ctxid,host)[0]

				except KeyError:
						# on failure we do an anonymous login
						user=None
						# only a few methods are available without login
						session.ctxid = ts.db.login(host=request.getClientIP())

						ctxidcookiename = "TWISTED_SESSION_ctxid"
						request.addCookie(ctxidcookiename, session.ctxid, path='/')

				if method == "logout":
						session.ctxid = None
						session.expire()
						ts.db.deletecontext(session.ctxid)
						return """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n<meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">"""


				ctxid = session.ctxid

				callback = routing.URLRegistry().execute('/'+str.join('/', request.postpath))

				print "callback:"
				print callback
				#info = dict(ctxid=session.ctxid, host=host, request=request)

				#def test_func(path, args=(), db=None, info=None, recid=0):
				#@emen2.TwistSupport_html.publicresource.PublicView.register_url('record', '^/record/(?P<recid>\d+)$')
				#def record(path,args,ctxid=None,host=None,db=None):

				d = threads.deferToThread(callback, request.postpath, ctxid, host, info=request.args)
				d.addCallback(self._cbsuccess, request)
				d.addErrback(self._ebRender, request)

				#response = str(result)



		#		 return response

		#		 return escape(response)

				return server.NOT_DONE_YET

		def _cbsuccess(self, result, request):
				print "success"
				request.setHeader("content-type","text/html; charset=utf-8")

				request.setHeader("content-length", str(len(result)))
		
				# no caching
				request.setHeader("Cache-Control","no-cache"); #HTTP 1.1
				request.setHeader("Pragma","no-cache"); #HTTP 1.0				request.write(result)

				#@		<<destroy anonymous sessions>>

				sess = request.session
				ctxid = sess.ctxid

				if ts.db.checkcontext(ctxid) == (-4, -4):
					ts.db.deletecontext(sess.ctxid)
					sess.expire()
					sess.ctxid = None

				result=result.encode("utf-8")
				request.write(result)
				request.finish()

		def _ebRender(self,failure,request):
				request.write(emen2.TwistSupport_html.html.error.error(failure))

				#@		<<destroy anonymous sessions>>
				sess = request.session
				ctxid = sess.ctxid

				if ts.db.checkcontext(ctxid) == (-4, -4):
					ts.db.deletecontext(sess.ctxid)
					sess.expire()
					sess.ctxid = None
				#@-node:<<destroy anonymous sessions>>

				request.finish()
		#@-node:Error Callback -- _ebrender
		#@-others
