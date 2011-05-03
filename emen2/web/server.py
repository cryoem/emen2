#!/usr/bin/env python
# $Id$

import sys
import thread
import atexit
import signal

from twisted.internet import reactor
from twisted.web import static, server
from twisted.web.resource import Resource


try:
	from twisted.internet import ssl
except:
	print "No SSL support"
	ssl = None

import emen2.web.resources.threadpool
import emen2.db.config
g = emen2.db.config.g()

# Load EMEN2 Twisted Resources
import emen2.web.resources.uploadresource
import emen2.web.resources.downloadresource
import emen2.web.resources.publicresource
import emen2.web.resources.rpcresource
import emen2.web.resources.jsonrpcresource



# Try to import EMAN2..
try:
	import EMAN2
	# We need to steal these handlers from EMAN2...
	signal.signal(2, signal.SIG_DFL)
	signal.signal(15, signal.SIG_DFL)
	atexit.register(emen2.db.database.DB_Close)
except:
	pass


class EMEN2Server(object):

	def __init__(self, port=None):
		# Options
		self.dbo = emen2.db.config.DBOptions()
		self.dbo.add_option('--port', type="int", help="Web server port")
		self.dbo.add_option('--https', action="store_true", help="Use HTTPS")
		self.dbo.add_option('--httpsport', type="int", help="HTTPS Port")
		(self.options, self.args) = self.dbo.parse_args()

		# Update the configuration
		g.EMEN2PORT = self.options.port or g.EMEN2PORT
		g.EMEN2PORT = port or g.EMEN2PORT
		g.EMEN2HTTPS = self.options.https or g.EMEN2HTTPS
		g.EMEN2PORT_HTTPS = self.options.httpsport or g.getattr('EMEN2PORT_HTTPS',443)


		self.root = emen2.web.resources.publicresource.PublicView()
		self.resources = {
			'favicon.ico': static.File(emen2.db.config.get_filename('emen2', 'static/favicon.ico')),
			'robots.txt': static.File(emen2.db.config.get_filename('emen2', 'static/robots.txt')),
			'static': static.File(emen2.db.config.get_filename('emen2', 'static')),
			'download': emen2.web.resources.downloadresource.DownloadResource(),
			'upload': emen2.web.resources.uploadresource.UploadResource(),
			'RPC2': emen2.web.resources.rpcresource.RPCResource(format="xmlrpc"),
			'json': emen2.web.resources.rpcresource.RPCResource(format="json"),
			'jsonrpc': emen2.web.resources.jsonrpcresource.e2jsonrpc(),
		}


		self.site = server.Site(self.root)
		def allHeadersReceived(self, *a, **kw):
			'''hack for allowing 100-Continue to work.......
				not sure if this is the right method to override....'''
			req = self.requests[-1]
			req.parseCookies()
			if req.requestHeaders.getRawHeaders('Expect') == ['100-continue']:
				self.transport.write('HTTP/1.1 100-Continue\n\n')
			self.persistent = self.checkPersistence(req, self._version)
			req.gotLength(self.length)
		self.site.protocol.allHeadersReceived = allHeadersReceived


		# Start the web server
		self.inithttpd()




	def load_resources(self):
		for path, resource in self.resources.items():
			level, msg = 'DEBUG', ['RESOURCE', 'LOADED:', '%s to %s']
			try: self.root.putChild(path, resource)
			except:
				msg[1], level = 'FAILED.', 'CRITICAL'
				del msg[2]
			else:
				msg[2] %= (path, resource)
			g.log.msg(level, ' '.join(msg))


	def interact(self):
		while True:
			a.interact()
			exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
			if exit[0] == 'n':
					thread.interrupt_main()
					return




	def inithttpd(self):
		# This has to go first for metaclasses
		# to register before the templates are cached.
		import emen2.db.database

		# Load views and templates
		import emen2.web.views
		import emen2.web.view
		import emen2.web.viewloader

		emen2.web.viewloader.load_views()
		redirects = g.getattr('REDIRECTS', {})
		emen2.web.viewloader.load_redirects(redirects)
		emen2.web.viewloader.routes_from_g()

		# load EMAN2 resource
		try:
			import emen2.web.resources.eman2resource
			resources.update(eman2 = emen2.web.resources.eman2resource.EMAN2BoxResource())
		except:
			pass


		try:
			extraresources = g.getattr('RESOURCESPECS', {})
			for path, mod in extraresources.items():
				if path in self.resources: raise ValueError, "Cannot override standard resources"
				mod = __import__(mod)
				self.resources[path] = getattr(mod, path)
		except ImportError: pass


		self.load_resources()


		reactor.listenTCP(g.EMEN2PORT, self.site)

		if g.EMEN2HTTPS and ssl:
			reactor.listenSSL(
				g.EMEN2PORT_HTTPS,
				server.Site(self.root),
				ssl.DefaultOpenSSLContextFactory(
					os.path.join(g.SSLPATH, "server.key"),
					os.path.join(g.SSLPATH, "server.crt")
					)
				)


		reactor.suggestThreadPoolSize(g.NUMTHREADS)

		g.info('Listening on port %d ...'%g.EMEN2PORT)
		g._locked = True
		reactor.run()

if __name__ == "__main__":
	EMEN2Server()



__version__ = "$Revision$".split(":")[1][:-1].strip()

