#!/usr/bin/python
import sys
sys.path.append('/Users/edwardlangley')
import emen2.emen2config
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

# This is the main server program for EMEN2
from twisted.internet import reactor, ssl
from twisted.web import static, server

import demjson
import operator

# emen2 imports
from emen2.subsystems import templating
from emen2.subsystems import routing

import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
import emen2.TwistSupport_html.rpcresource
import emen2.TwistSupport_html.authresource


import emen2.TwistSupport_html.public.views
emen2.TwistSupport_html.public.views.load_views()

import emen2.TwistSupport_html.html


def prepare_properties(outfile):
	vtm=emen2.Database.subsystems.datatypes.VartypeManager()
	properties={}
	for prop in vtm.getproperties():
		p=vtm.getproperty(prop)
		properties[prop]=[p.defaultunits,[i[0] for i in sorted(p.units.items(), key=operator.itemgetter(1), reverse=True)]]
	
	print "Writing Properties files"
	f=open(outfile,"w")
	f.write("var valid_properties=%s;\n\n"%demjson.encode(properties))
	f.write("var valid_vartypes=%s;\n\n"%demjson.encode(vtm.getvartypes()))
	f.write("var EMEN2WEBROOT=%s;\n\n"%demjson.encode(g.EMEN2WEBROOT))
	f.close()

prepare_properties(g.EMEN2ROOT+"/tweb/js/datatypes.js")


#############################
# Resources
#############################
import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
#import emen2.TwistSupport_html.xmlrpcresource
import emen2.TwistSupport_html.rpcresource
import emen2.TwistSupport_html.authresource


## g.STATICPATH = g.EMEN2ROOT+"/tweb"

def load_resources(root, resources):
	for path, resource in resources.items():
		root.putChild(path, resource)

def interact():
	if g.CONSOLE:
		while True:
			 a.interact()
			 exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
			 if exit[0] == 'n':
					 thread.interrupt_main()
					 return


def main():
	root = static.File(g.STATICPATH)
	
	resources = dict(
		db = emen2.TwistSupport_html.publicresource.PublicView(),
		auth = emen2.TwistSupport_html.authresource.AuthResource(),
		download = emen2.TwistSupport_html.downloadresource.DownloadResource(),
		upload = emen2.TwistSupport_html.uploadresource.UploadResource(),
		RPC2 = emen2.TwistSupport_html.rpcresource.RPCResource(format="xmlrpc"),
		json = emen2.TwistSupport_html.rpcresource.RPCResource(format="json")
	)
	
	load_resources(root, resources)
	
	if g.CONSOLE:
		x = {}
		x.update(globals())
		exec "from test import *" in x
		a = code.InteractiveConsole(x, '')
		thread.start_new_thread(interact, ())

	
	#############################
	# Start server
	#############################
	reactor.listenTCP(g.EMEN2PORT, server.Site(root))
	if g.EMEN2HTTPS:
		reactor.listenSSL(g.EMEN2PORT_HTTPS, server.Site(root), ssl.DefaultOpenSSLContextFactory("ssl/server.key", "ssl/server.crt"))
	
	reactor.suggestThreadPoolSize(4)
	reactor.run()


main()

