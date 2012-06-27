#!/usr/bin/env python
# $Id$

import traceback
import thread
import os.path
import functools
import contextlib
import time
import collections
import sys

# Twisted imports
from twisted.application import internet
import twisted.python.log
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


class DBPool(object):
	"""Simple DB Pool loosely based on twisted.enterprise.adbapi.ConnectionPool."""
	# All connections, key is Thread ID
	dbs = {}
	running = False

	def __init__(self, min=0, max=5):
		# Minimum and maximum number of threads
		self.min = min
		self.max = max
		# Generate Thread ID
		self.threadID = thread.get_ident
		# Connect to reactor
		self.reactor = twisted.internet.reactor
		self.threadpool = twisted.python.threadpool.ThreadPool(self.min, self.max)

	def start(self):
		"""Start a database connection on startup to run recovery, setup, etc."""
		self.connect()

	def connect(self):
		"""Create a new database connection."""
		import emen2.db.database
		tid = self.threadID()
		# print '# threads: %s -- this thread is %s'%(len(self.dbs), tid)
		db = self.dbs.get(tid)
		if not db:
			db = emen2.db.database.DB.opendb()
			self.dbs[tid] = db
		return db

	def disconnect(self, db):
		"""Disconnect a database connection."""
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
		kwargs['db'] = db
		result = call(*args, **kwargs)
		return result


pool = DBPool()


##### Web server ######

import emen2.db.log
import emen2.web.routing

class WebServerOptions(emen2.db.config.DBOptions):
	optParameters = [
		['port',      'HTTP port',  None, None, int],
		['httpsport', 'HTTPS port', None, None, int],
	]

	optFlags = [
		['https', None, 'Use HTTPS']
	]


class EMEN2Server(object):

	usage = WebServerOptions

	def __init__(self, options=None):
		options = options or {}
		self.port = options.get('port') or emen2.db.config.get('network.EMEN2PORT')

	#@contextlib.contextmanager
	def start(self, service=None):
		'''Run the server main loop'''

		pool.start()

		# Routing resource. This will look up request.uri in the routing table
		# and return View resources.
		root = emen2.web.routing.Router()

		# Previously this used contextmanager and yield to attach the resources.
		self.attach_resources(root)

		# The Twisted Web server protocol factory,
		#  with our Routing resource as root
		self.site = twisted.web.server.Site(root)

		reactor = twisted.internet.reactor
		reactor.suggestThreadPoolSize(emen2.db.config.get('network.NUMTHREADS', 1))

		# Attach to a service, or run standalone.
		if service:
			self.attach_to_service(service)
		else:
			self.attach_standalone()

	def attach_resources(self, root):
		# Load all View extensions
		import emen2.db.config
		emen2.db.config.load_views()

		# Init log system
		import emen2.db.log
		emen2.db.log.init('log initialized')

		# Child resources that do not go through the Router.
		import jsonrpc.server
		import emen2.web.resource

		# if all the JSON_RPC class does is change the eventhandler, it can (and should) be instantiated this way:
		from emen2.web.resource import JSONRPCServerEvents
		root.putChild('jsonrpc', jsonrpc.server.JSON_RPC().customize(JSONRPCServerEvents))

		root.putChild('static', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('static-%s'%emen2.VERSION, twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		root.putChild('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')))
		root.putChild('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/robots.txt')))

	def attach_to_service(self, service):
		emen2_service = internet.TCPServer(self.port, self.site)
		emen2_service.setServiceParent(service)
		# if self.EMEN2HTTPS and ssl:
		#	pass

	def attach_standalone(self):
		reactor = twisted.internet.reactor
		reactor.listenTCP(self.port, self.site)
		reactor.run()



def start_standalone():
	# twisted.python.log.startLogging(sys.stdout)
	opt = emen2.db.config.UsageParser(WebServerOptions)
	server = EMEN2Server(opt.options)
	server.start()


if __name__ == "__main__":
	start_standalone()



__version__ = "$Revision$".split(":")[1][:-1].strip()
