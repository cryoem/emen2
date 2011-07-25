#!/usr/bin/env python
# $Id$

import sys
import thread
import os.path
import atexit
import multiprocessing
import twisted.internet
import twisted.web.static
import twisted.web.server
import twisted.internet.reactor


try:
	from twisted.internet import ssl
except ImportError:
	ssl = None


import emen2.web.resources.threadpool
import emen2.db.config
import emen2.web.templating
config = emen2.db.config.g()

# Load EMEN2 Twisted Resources
import emen2.web.resources.uploadresource
import emen2.web.resources.downloadresource
import emen2.web.resources.publicresource
import emen2.web.resources.rpcresource
import emen2.web.resources.jsonrpcresource
import jsonrpc.server
import contextlib


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
		config.log.msg(level, ' '.join(msg))

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

	#: Use HTTPS?
	EMEN2HTTPS = config.claim('EMEN2HTTPS', False, lambda v: isinstance(v, bool))
	#: Which port to receive HTTPS request?
	EMEN2PORT_HTTPS = config.claim('EMEN2PORT_HTTPS', 443, lambda v: isinstance(v, (int,long)))
	#: Where to find the SSL info
	SSLPATH = config.claim('paths.SSLPATH', '', validator=lambda v: isinstance(v, (str, unicode)))

	#: Extra resources to load
	EXTRARESOURCES = config.claim('RESOURCESPECS', {}, lambda v: isinstance(v, dict))
	#: How many threads to load, defaults to :py:func:`multiprocessing.cpu_count`+1
	NUMTHREADS = config.claim('NUMTHREADS', multiprocessing.cpu_count()+1, lambda v: (v < (multiprocessing.cpu_count()*2)) )
	#: Which port to listen on
	PORT = config.claim('EMEN2PORT', 8080, lambda v: isinstance(v, (int,long)))

	def __init__(self, port=None, dbo=None):
		# Options
		self.dbo = dbo or emen2.db.config.DBOptions()
		self.dbo.add_option('--port', type="int", help="Web server port")
		self.dbo.add_option('--https', action="store_true", help="Use HTTPS")
		self.dbo.add_option('--httpsport', type="int", help="HTTPS Port")
		(self.options, self.args) = self.dbo.parse_args()

		# Update the configuration
		if self.options.port or port:
			self.EMEN2PORT = self.options.port or port

		if self.options.https:
			self.EMEN2HTTPS = self.options.https

		if self.options.httpsport:
			self.EMEN2PORT_HTTPS = self.options.httpsport




	@contextlib.contextmanager
	def start(self):
		'''run the main loop'''
		root = emen2.web.resources.publicresource.PublicView()
		yield self, root
		site = twisted.web.server.Site(root)
		site.protocol.allHeadersReceived = allHeadersReceived

		twisted.internet.reactor.listenTCP(self.PORT, site)
		config.info('Listening on port %d ...'%self.PORT)

		if self.EMEN2HTTPS and ssl:
			twisted.internet.reactor.listenSSL(
				self.EMEN2PORT_HTTPS,
				site,
				ssl.DefaultOpenSSLContextFactory(
					os.path.join(self.SSLPATH, "server.key"),
					os.path.join(self.SSLPATH, "server.crt")
					)
				)

		twisted.internet.reactor.suggestThreadPoolSize(self.NUMTHREADS)

		config._locked = True
		twisted.internet.reactor.run()



	def load_resources(self, rl):
		for path, mod in self.EXTRARESOURCES.items():
			try:
				mod = __import__(mod)
				rl.add_resource(path, getattr(mod, path))
			except ImportError:
				config.error('failed to attach resource %r to path %r' % (mod, path))
				if config.DEBUG:
					config.log.print_exception()

		rl.add_resources(
			static = twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')),
			download = emen2.web.resources.downloadresource.DownloadResource(),
			upload = emen2.web.resources.uploadresource.UploadResource(),
			RPC2 = emen2.web.resources.rpcresource.RPCResource(format="xmlrpc"),
			json = emen2.web.resources.rpcresource.RPCResource(format="json"),
			jsonrpc = jsonrpc.server.JSON_RPC().customize(emen2.web.resources.jsonrpcresource.e2jsonrpc),
		)
		rl.add_resource('static-%s'%emen2.VERSION, twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
		rl.add_resource('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')))
		rl.add_resource('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/robots.txt')))



#NOTE: this MUST be imported here
import emen2.web.viewloader
def start_emen2():
	with EMEN2Server().start() as (server, root):
		# This has to go first for metaclasses
		# to register before the templates are cached.
		import emen2.db.database

		# Load views and templates
		#import emen2.web.views
		import emen2.web.view


		config.templates = emen2.web.templating.TemplateFactory('mako', emen2.web.templating.MakoTemplateEngine())

		vl = emen2.web.viewloader.ViewLoader()
		vl.load_extensions()
		vl.load_redirects()
		vl.routes_from_g()

		rl = ResourceLoader(root)
		server.load_resources(rl)


if __name__ == "__main__":
	start_emen2()
__version__ = "$Revision$".split(":")[1][:-1].strip()

