import sys
import thread

from twisted.internet import reactor, ssl
from twisted.web import static, server


import emen2.Database.config
import emen2.Database.globalns
g = emen2.Database.globalns.GlobalNamespace()
parser = emen2.Database.config.DBOptions()
parser.parse_args()
# g.log.capturestdout()

# This is the main server program for EMEN2


# def prepare_web():
# 	g.log.msg(g.LOG_INIT, "Adjusting EMEN2WEBROOT in static files")
# 	f=open(g.EMEN2ROOT+"/tweb/index.html","w")
# 	f.write("""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
# 	<meta http-equiv="REFRESH" content="0; URL=%s/db/">"""%g.EMEN2WEBROOT)
# 	f.close()


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



def inithttpd():
	import emen2.web.uploadresource
	import emen2.web.downloadresource
	import emen2.web.publicresource
	import emen2.web.rpcresource
	import emen2.web.authresource
	import emen2.web.jsonrpcresource

	import emen2.web.views

	#import emen2.web.public.record
	
	import emen2.web.template_render
	import emen2.web.view

	emen2.web.view.load_views()
	emen2.web.view.routes_from_g()

	root = static.File("tweb")

	resources = dict(
		db = emen2.web.publicresource.PublicView(),
		auth = emen2.web.authresource.AuthResource(),
		download = emen2.web.downloadresource.DownloadResource(),
		upload = emen2.web.uploadresource.UploadResource(),
		RPC2 = emen2.web.rpcresource.RPCResource(format="xmlrpc"),
		json = emen2.web.rpcresource.RPCResource(format="json"),
		chain = emen2.web.rpcresource.RPCChain(),
		json2 = emen2.web.jsonrpcresource.jsonrpc(),
	)

	# prepare_web()

	load_resources(root, resources)


	# Start server
	# g.log_init('Starting Connection ...')

	rr = server.Site(root)
	#rr.requestFactory = g.log.debug_func(rr.requestFactory)

	reactor.listenTCP(g.EMEN2PORT, rr)

	if g.EMEN2HTTPS:
		reactor.listenSSL(g.EMEN2PORT_HTTPS, server.Site(root), ssl.DefaultOpenSSLContextFactory("ssl/server.key", "ssl/server.crt"))

	reactor.suggestThreadPoolSize(1) #g.NUMTHREADS

	g.log.msg(g.LOG_INIT, 'Listening on port %d ...' % g.EMEN2PORT)
	reactor.run()




if __name__ == "__main__":
	inithttpd()


