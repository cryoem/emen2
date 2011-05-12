#!/usr/bin/env python
# $Id$

import sys
import thread
import os.path
import atexit

# from twisted.internet import reactor
# from twisted.web import static, server
# from twisted.web.resource import Resource
import twisted.internet
import twisted.web


try:
	from twisted.internet import ssl
except:
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


class ResourceLoader(object):
	def __init__(self, root, **resources):
		self.root = root
		self.add_resources(**resources)

	def add_resource(self, path, resource):
		level, msg = 'DEBUG', ['RESOURCE', 'LOADED:', '%s to %s']
		try: self.root.putChild(path, resource)
		except:
			msg[1], level = 'FAILED.', 'CRITICAL'
			del msg[2]
		else:
			msg[2] %= (path, resource)
		g.log.msg(level, ' '.join(msg))

	def add_resources(self, **resources):
		for k,v in resources.items():
			self.add_resource(k,v)


def allHeadersReceived(self, *a, **kw):
	'''hack for allowing 100-Continue to work.......
		not sure if this is the right method to override....'''
	req = self.requests[-1]
	req.parseCookies()
	if req.requestHeaders.getRawHeaders('Expect') == ['100-continue']:
		self.transport.write('HTTP/1.1 100-Continue\n\n')
	self.persistent = self.checkPersistence(req, self._version)
	req.gotLength(self.length)


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

		self.resource_loader = ResourceLoader(emen2.web.resources.publicresource.PublicView())
		self.load_views()
		self.load_resources()



	def load_views(self):
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



	def load_resources(self):
		try:
			extraresources = g.getattr('RESOURCESPECS', {})
			for path, mod in extraresources.items():
				mod = __import__(mod)
				self.resource_loader.add_resource(path, getattr(mod, path))
		except ImportError:
			pass

		self.resource_loader.add_resources(
			static = twisted.web.static.File(emen2.db.config.get_filename('emen2', 'static')),
			download = emen2.web.resources.downloadresource.DownloadResource(),
			upload = emen2.web.resources.uploadresource.UploadResource(),
			RPC2 = emen2.web.resources.rpcresource.RPCResource(format="xmlrpc"),
			json = emen2.web.resources.rpcresource.RPCResource(format="json"),
			jsonrpc = emen2.web.resources.jsonrpcresource.e2jsonrpc(),
		)
		self.resource_loader.add_resource('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'static/favicon.ico')))
		self.resource_loader.add_resource('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'static/robots.txt')))


	def interact(self):
		while True:
			a.interact()
			exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
			if exit[0] == 'n':
					thread.interrupt_main()
					return


	def start(self):
		'''run the main loop'''
		site = twisted.web.server.Site(self.resource_loader.root)
		site.protocol.allHeadersReceived = allHeadersReceived

		twisted.internet.reactor.listenTCP(g.EMEN2PORT, site)
		g.info('Listening on port %d ...'%g.EMEN2PORT)
		
		# if g.EMEN2HTTPS and ssl:
		# 	reactor.listenSSL(
		# 		g.EMEN2PORT_HTTPS,
		# 		site,
		# 		ssl.DefaultOpenSSLContextFactory(
		# 			os.path.join(g.paths.SSLPATH, "server.key"),
		# 			os.path.join(g.paths.SSLPATH, "server.crt")
		# 			)
		# 		)
		# reactor.suggestThreadPoolSize(g.NUMTHREADS)

		g._locked = True
		twisted.internet.reactor.run()
		


if __name__ == "__main__":
	EMEN2Server().start()



__version__ = "$Revision$".split(":")[1][:-1].strip()

