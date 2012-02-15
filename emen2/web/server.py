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

##### Simple DB Pool loosely based on twisted.enterprise.adbapi.ConnectionPool #####

class DBPool(object):
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
		['port', 'HTTP port', None, None, int],
		['httpsport', 'HTTPS port', None, None, int],
	]

	optFlags = [
		['https', None, 'Use HTTPS']
	]


class EMEN2Server(object):

	usage = WebServerOptions

	def __init__(self, port=None):
		self.port = port

	#@contextlib.contextmanager
	def start(self, service=None):
		'''Run the server main loop'''

		# Update the configuration
		self.EMEN2PORT = self.port or emen2.db.config.get('network.EMEN2PORT')
		self.EMEN2PORT_HTTPS = 436
		self.EMEN2HTTPS = False # self.options.get('https', False)
		self.EMEN2PORT_HTTPS = 436 # self.options.get('httpsport', 436)

		# Routing resource. This will look up request.uri in the routing table
		# and return View resources.
		root = emen2.web.routing.Router()

		# Previously this used contextmanager and yield to attach the resources.
		self.attach_resources(root)

		# The Twisted Web server protocol factory,
		#  with our Routing resource as root
		self.site = twisted.web.server.Site(root)

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
		
	def attach_to_service(self, service):
		emen2_service = internet.TCPServer(self.port, self.site)
		emen2_service.setServiceParent(service)

		if self.EMEN2HTTPS and ssl:
			pass ##TODO: implement ssl

	def attach_standalone(self):
		reactor = twisted.internet.reactor		
		reactor.listenTCP(self.port, self.site)
		reactor.run()



if __name__ == "__main__":
	# Fix
	# twisted.python.log.startLogging(sys.stdout)
	emen2.db.config.UsageParser(WebServerOptions)
	server = EMEN2Server(port=8080)
	server.start()



__version__ = "$Revision$".split(":")[1][:-1].strip()
