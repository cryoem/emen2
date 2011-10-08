#!/usr/bin/env python
# $Id$

import sys
import thread
import os.path
import atexit
import multiprocessing
import functools
import contextlib
import threading
import thread
import time

import twisted.internet
import twisted.web.static
import twisted.web.server
import twisted.internet.reactor
import twisted.python.threadpool

import jsonrpc.server

try:
	from twisted.internet import ssl
except ImportError:
	ssl = None


import emen2.db.config


##### Simple DB Pool loosely based on twisted.enterprise.adbapi.ConnectionPool #####		

class DBPool(object):
	running = False
	
	def __init__(self, min=0, max=5):
		# Minimum and maximum number of threads
		self.min = min
		self.max = max
		
		# All connections, hashed by Thread ID
		self.dbs = {}
		
		# Generate Thread ID
		self.threadID = thread.get_ident

		# Connect to reactor
		self.reactor = twisted.internet.reactor
		self.threadpool = twisted.python.threadpool.ThreadPool(self.min, self.max)

	def connect(self):
		import emen2.db.database
		# print '# threads: %s'%len(self.dbs)
		tid = self.threadID()
		db = self.dbs.get(tid)
		if not db:
			db = emen2.db.database.DB.opendb()
			self.dbs[tid] = db
		return db

	def disconnect(self, db):
		tid = self.threadID()
		if db is not self.dbs.get(tid):
			raise Exception('Wrong connection for thread')
		if db:
			# db.close()
			del self.dbs[tid]

	def rundb(self, call, *args, **kwargs):
		return twisted.internet.threads.deferToThread(self._rundb, call, *args, **kwargs)

	def _rundb(self, call, *args, **kwargs):
		db = self.connect()
		result = call(db=db, *args, **kwargs)
		return result

	def runtxn(self, call, *args, **kwargs):
		return twisted.internet.threads.deferToThread(self._runtxn, call, *args, **kwargs)
	
	def _runtxn(self, call, *args, **kwargs):
		db = self.connect()
		with db:
			result = call(db=db, *args, **kwargs)
		return result

		

##### Routing Resource #####

class Router(twisted.web.resource.Resource):
	isLeaf = False

	# Find a resource or view
	def getChildWithDefault(self, path, request):
		if path in self.children:
			return self.children[path]

		# Add a final slash. 
		# Most of the view matchers expect this.
		path = request.path
		if not path:
			path = '/'
		if path[-1] != "/":
			path = "%s/"%path
		request.path = path
		
		try:
			view, method = emen2.web.routing.resolve(path=request.path)
		except:
			return self
			
		# This may move into routing.Router in the future.
		view = view()
		view.render = functools.partial(view.render, method=method)
		return view
		

	# Resource was not found
	def render(self, request):
		return 'Not found'
	
		

##### pool and reactor #####

pool = DBPool()
reactor = twisted.internet.reactor		


##### Server ######

class EMEN2Server(object):

	def __init__(self, port=None, dbo=None):
		# Configuration options
		self.dbo = dbo or emen2.db.config.DBOptions()
		self.dbo.add_option('--port', type="int", help="Web server port")
		self.dbo.add_option('--https', action="store_true", help="Use HTTPS")
		self.dbo.add_option('--httpsport', type="int", help="HTTPS Port")
		(self.options, self.args) = self.dbo.parse_args()
		
		self.EMEN2PORT = emen2.db.config.get('network.EMEN2PORT')
		self.EMEN2HTTPS = False
		self.EMEN2PORT_HTTPS = 436

		# Update the configuration
		if self.options.port or port:
			self.EMEN2PORT = self.options.port or port

		if self.options.https:
			self.EMEN2HTTPS = self.options.https

		if self.options.httpsport:
			self.EMEN2PORT_HTTPS = self.options.httpsport




	@contextlib.contextmanager
	def start(self):
		'''Run the server main loop'''
		
		# emen2.db.log.info('starting EMEN2 version: %s'%emen2.db.config.get('params.VERSION')

		# Routing resource. This will look up request.uri in the routing table
		# and return View resources.
		root = Router()
		yield self, root

		# Child resources that do not go through the Router.
		import emen2.web.resource
		import emen2.web.view
		root.putChild('jsonrpc', emen2.web.resource.JSONRPCResource())
		root.putChild('static', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('static-%s'%emen2.db.config.get('params.VERSION'), twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')))
		root.putChild('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/robots.txt')))

		# The Twisted Web server protocol factory,
		#  with our Routing resource as root
		site = twisted.web.server.Site(root)
		
		# Setup the Twisted reactor to listen on web port
		reactor.listenTCP(self.EMEN2PORT, site)

		# Setup the Twisted reactor to listen on the SSL port
		if self.EMEN2HTTPS and ssl:
			reactor.listenSSL(
				self.EMEN2PORT_HTTPS,
				site,
				ssl.DefaultOpenSSLContextFactory(
					os.path.join(self.SSLPATH, "server.key"),
					os.path.join(self.SSLPATH, "server.crt")
					))

		# config._locked = True
		reactor.run()


def start_emen2():
	# Start the EMEN2Server and load the View resources
	with EMEN2Server().start() as (server, root):
		import emen2.web.view
		vl = emen2.web.view.ViewLoader()
		vl.load_extensions()		



if __name__ == "__main__":
	start_emen2()


__version__ = "$Revision$".split(":")[1][:-1].strip()