#!/usr/bin/env python
# $Id$

import traceback
import thread
import os.path
import functools
import contextlib
import time
import collections

# Twisted imports
from twisted.application import internet
import twisted.internet
import twisted.internet.reactor
import twisted.web.static
import twisted.web.server
import twisted.python.threadpool

try:
	from twisted.internet import ssl
except ImportError:
	ssl = None


import emen2.db.config

##### Simple DB Pool loosely based on twisted.enterprise.adbapi.ConnectionPool #####

class DBPool(object):
	running = False

	dbs = {}
	def __init__(self, min=0, max=5):
		# Minimum and maximum number of threads
		self.min = min
		self.max = max

		# All connections, hashed by Thread ID

		# Generate Thread ID
		self.threadID = thread.get_ident

		# Connect to reactor
		self.reactor = twisted.internet.reactor
		self.threadpool = twisted.python.threadpool.ThreadPool(self.min, self.max)

	def connect(self):
		# Create a new database connection
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
		# print 'DBPool', self.dbs
		return twisted.internet.threads.deferToThread(self._rundb, call, *args, **kwargs)

	def _rundb(self, call, *args, **kwargs):
		db = self.connect()
		result = call(db=db, *args, **kwargs)
		return result


##### pool and reactor #####

pool = DBPool()

##### Server ######

import emen2.db.config
class WebServerOptions(emen2.db.config.DBOptions):
	optParameters = [
		['port', 'Web server port', None, None, int],
		['httpsport', 'Web server port', None, None, int],
	]

	optFlags = [
		['https', None, 'Use HTTPS']
	]

import emen2.db.config
import emen2.db.log
import emen2.web.routing

class EMEN2Server(object):

	def __init__(self, port=None, dbo=None):
		if dbo is None:
			self.options = WebServerOptions
		elif issubclass(dbo, WebServerOptions):
			self.options = dbo
		elif issubclass(dbo, twisted.python.usage.Options):
			self.options = type('ServerOptions', (dbo, WebServerOptions), {})
		else:
			raise TypeError("the value of 'dbo' should be a subclass of twisted.python.usage.Options")


		self.port = port


	@contextlib.contextmanager
	def start(self, config=None):
		'''Run the server main loop'''
		if config is not None:
			self.options = config

		emen2.db.log.info('starting EMEN2 version: %s'%emen2.db.config.get('params.VERSION'))
		self.EMEN2PORT = self.port or emen2.db.config.get('network.EMEN2PORT')
		self.EMEN2PORT_HTTPS = 436

		# Update the configuration
		self.EMEN2PORT = self.options['port'] or self.EMEN2PORT

		self.EMEN2HTTPS = self.options.get('https', False)

		self.EMEN2PORT_HTTPS = self.options.get('httpsport', 436)


		# Routing resource. This will look up request.uri in the routing table
		# and return View resources.
		root = emen2.web.routing.Router()

		# yield (self,root) to body of with statement
		# allows this code to be more readable
		yield self, root

		# The Twisted Web server protocol factory,
		#  with our Routing resource as root
		self.site = twisted.web.server.Site(root)

	def listen(self):
		self.site.logPath='/tmp/access.log'
		self.site.noisy=False

		# Setup the Twisted reactor to listen on web port
		reactor = twisted.internet.reactor
		reactor.listenTCP(self.EMEN2PORT, self.site)

		# Setup the Twisted reactor to listen on the SSL port
		if self.EMEN2HTTPS and ssl:
			reactor.listenSSL(
				self.EMEN2PORT_HTTPS,
				self.site,
				ssl.DefaultOpenSSLContextFactory(
					os.path.join(self.SSLPATH, "server.key"),
					os.path.join(self.SSLPATH, "server.crt")
					))

		# config._locked = True
		reactor.run()

	def parse_options(self):
		self.options = self.options()
		self.options.parseOptions()

	def attach_to_service(self, service):
		emen2_service = internet.TCPServer(8080, self.site)
		emen2_service.setServiceParent(service)

		if self.EMEN2HTTPS and ssl:
			pass ##TODO: implement ssl




def init_server():
	server = EMEN2Server()
	server.parse_options()
	return server

import twisted.python.log
import sys
def start_emen2(server, config=None):
	# Start the EMEN2Server and load the View resources

	if config is None:
		server.parse_options()
	else:
		server.options = config

	import emen2.db.config
	emen2.db.config.CommandLineParser('', server.options, lc=True)

	with server.start() as (server, root):
		# You must import the database in the main thread.
		import emen2.db.database

		# Load all View extensions
		emen2.db.config.load_views()

		emen2.db.log.log_init(True)
		emen2.db.log.init('log initialized')
		twisted.python.log.msg('asdasd', a='1')

		# Child resources that do not go through the Router.
		import jsonrpc.server
		import emen2.web.resource
		root.putChild('jsonrpc', emen2.web.resource.JSONRPCResource())
		root.putChild('static', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('static-%s'%emen2.db.config.get('params.VERSION'), twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')))
		root.putChild('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/robots.txt')))

	return server


if __name__ == "__main__":
	twisted.python.log.startLogging(sys.stdout)
	server = init_server()
	start_emen2(server).listen()



__version__ = "$Revision$".split(":")[1][:-1].strip()
