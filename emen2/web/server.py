#!/usr/bin/env python

# $Id$

import sys
import thread

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

if not g.getattr('CONFIG_LOADED', False):
	try:
		parser = emen2.db.config.DBOptions()
		parser.parse_args()
	except:
		raise
		pass


def load_resources(root, resources):
	for path, resource in resources.items():
		level = 'LOG_INIT'
		msg = ['RESOURCE', 'LOADED:', '%s to %s']
		try:
			root.putChild(path, resource)
		except:
			msg[1] = 'FAILED.'
			level = 'LOG_CRITICAL'
			del msg[2]
		else:
			msg[2] %= (path, resource)
		# g.log.msg(level,' '.join(msg))


def interact():
	while True:
		a.interact()
		exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
		if exit[0] == 'n':
				thread.interrupt_main()
				return




class RootResource(Resource):
	def getChild(self, path, request):
		print "->", path
		return self.children.get(request.path.split("/")[0], self)



def inithttpd():
	import emen2.web.resources.uploadresource
	import emen2.web.resources.downloadresource
	import emen2.web.resources.publicresource
	import emen2.web.resources.rpcresource
	import emen2.web.resources.jsonrpcresource
	# ed: added later
	# import emen2.web.resources.eman2resource

	import emen2.web.views
	import emen2.web.view
	import emen2.web.viewloader

	emen2.web.viewloader.load_views()
	redirects = g.getattr('REDIRECTS', {})
	emen2.web.viewloader.load_redirects(redirects)
	emen2.web.viewloader.routes_from_g()

	root = emen2.web.resources.publicresource.PublicView()

	resources = {
		'favicon.ico': static.File(emen2.db.config.get_filename('emen2', 'static/favicon.ico')),
		'robots.txt': static.File(emen2.db.config.get_filename('emen2', 'static/robots.txt')),
		'static': static.File(emen2.db.config.get_filename('emen2', 'static')),
		'download': emen2.web.resources.downloadresource.DownloadResource(),
		'upload': emen2.web.resources.uploadresource.UploadResource(),
		'RPC2': emen2.web.resources.rpcresource.RPCResource(format="xmlrpc"),
		'json': emen2.web.resources.rpcresource.RPCResource(format="json"),
		'jsonrpc': emen2.web.resources.jsonrpcresource.jsonrpc()
	}

	# load EMEN2 resource
	try:
		import EMAN2
		import emen2.web.resources.eman2resource
		resources.update(eman2 = emen2.web.resources.eman2resource.EMAN2BoxResource())
	except: pass
	#	EMAN2 = False

	try:
		extraresources = g.getattr('RESOURCESPECS', {})
		for path, mod in extraresources.items():
			if path in resources: raise ValueError, "Cannot override standard resources"
			mod = __import__(mod)
			resources[path] = mod.resource
	except ImportError: pass


	load_resources(root, resources)
	rr = server.Site(root)
	reactor.listenTCP(g.EMEN2PORT, rr)

	if g.EMEN2HTTPS and ssl:
		reactor.listenSSL(g.EMEN2PORT_HTTPS, server.Site(root), ssl.DefaultOpenSSLContextFactory(os.path.join(g.SSLPATH, "server.key"), os.path.join(g.SSLPATH, "server.crt")))

	reactor.suggestThreadPoolSize(g.NUMTHREADS)

	g.log.msg(g.LOG_INIT, 'Listening on port %d ...' % g.EMEN2PORT)
	g._locked = True
	reactor.run()



if __name__ == "__main__":
	inithttpd()


__version__ = "$Revision$".split(":")[1][:-1].strip()
