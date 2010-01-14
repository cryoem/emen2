import sys
import thread

from twisted.internet import reactor, ssl
from twisted.web import static, server

import emen2.config.config
import emen2.globalns
g = emen2.globalns.GlobalNamespace()

# This is the main server program for EMEN2


def prepare_web():
	g.log.msg(g.LOG_INIT, "Adjusting EMEN2WEBROOT in static files")
	f=open(g.EMEN2ROOT+"/tweb/index.html","w")
	f.write("""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
	<meta http-equiv="REFRESH" content="0; URL=%s/db/">"""%g.EMEN2WEBROOT)
	f.close()


def load_resources(root, resources):
	for path, resource in resources.items():
		root.putChild(path, resource)


def interact():
	while True:
		a.interact()
		exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
		if exit[0] == 'n':
				thread.interrupt_main()
				return



def inithttpd():
	import emen2.TwistSupport_html.uploadresource
	import emen2.TwistSupport_html.downloadresource
	import emen2.TwistSupport_html.publicresource
	import emen2.TwistSupport_html.rpcresource
	import emen2.TwistSupport_html.authresource

	import emen2.TwistSupport_html.html
	import emen2.TwistSupport_html.public.record
	import emen2.TwistSupport_html.public.template_render

	import emen2.TwistSupport_html.public.views
	emen2.TwistSupport_html.public.views.load_views()

	root = static.File(g.STATICPATH)

	resources = dict(
		db = emen2.TwistSupport_html.publicresource.PublicView(),
		auth = emen2.TwistSupport_html.authresource.AuthResource(),
		download = emen2.TwistSupport_html.downloadresource.DownloadResource(),
		upload = emen2.TwistSupport_html.uploadresource.UploadResource(),
		RPC2 = emen2.TwistSupport_html.rpcresource.RPCResource(format="xmlrpc"),
		json = emen2.TwistSupport_html.rpcresource.RPCResource(format="json"),
		chain = emen2.TwistSupport_html.rpcresource.RPCChain(),
	)

	prepare_web()

	load_resources(root, resources)


	# Start server
	g.log.msg(g.LOG_INIT, 'Listening ...')

	reactor.listenTCP(g.EMEN2PORT, server.Site(root))

	if g.EMEN2HTTPS:
		reactor.listenSSL(g.EMEN2PORT_HTTPS, server.Site(root), ssl.DefaultOpenSSLContextFactory("ssl/server.key", "ssl/server.crt"))

	reactor.suggestThreadPoolSize(1)
	reactor.run()




if __name__ == "__main__":
	parser = emen2.config.config.DBOptions()
	parser.parse_args()
	inithttpd()


