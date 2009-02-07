#!/usr/bin/python

import sys
sys.path.append('/Users/edwardlangley')
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

# This is the main server program for EMEN2

from twisted.internet import reactor, ssl
from twisted.web import static, server

from emen2 import ts
from emen2 import util

import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
#import emen2.TwistSupport_html.xmlrpcresource
import emen2.TwistSupport_html.rpcresource
import emen2.TwistSupport_html.authresource
import emen2.TwistSupport_html.public.views

#from emen2.TwistSupport_html.public import views

from emen2.emen2config import *

from emen2.Database.subsystems import macro
from emen2.subsystems import templating
from emen2.subsystems import routing

from emen2.util import core_macros
from emen2.util import fileops
from emen2.util import utils

import code
import emen2.Database
import glob
import os
import thread
import time


# Change this to a directory for the actual database files
# ian: remove this sometime
#ts.startup(g.EMEN2DBPATH)


g.macros = macro.MacroEngine()



#############################
# Resources
#############################
root = static.File(g.EMEN2ROOT+"/tweb")



root.putChild("db",emen2.TwistSupport_html.publicresource.PublicView())
root.putChild("auth",emen2.TwistSupport_html.authresource.AuthResource())


root.putChild("download",emen2.TwistSupport_html.downloadresource.DownloadResource())
root.putChild("upload",emen2.TwistSupport_html.uploadresource.UploadResource())

# use new service system
root.putChild("RPC2",emen2.TwistSupport_html.rpcresource.RPCResource(format="xmlrpc"))
root.putChild("json",emen2.TwistSupport_html.rpcresource.RPCResource(format="json"))



CONSOLE=0
if CONSOLE:
	x = {}
	x.update(globals())
	exec "from test import *" in x
	a = code.InteractiveConsole(x, '')
	def interact():
	    while True:
	        a.interact()
	        exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
	        if exit[0] == 'n':
	            thread.interrupt_main()
	            return
        
	thread.start_new_thread(interact, ())

# print 'macros(%d): %s' % (id(macro.MacroEngine._macros), macro.MacroEngine._macros)        

#############################
# Start server
#############################
reactor.listenTCP(g.EMEN2PORT, server.Site(root))
if g.EMEN2HTTPS:
	reactor.listenSSL(g.EMEN2PORT_HTTPS, server.Site(root), ssl.DefaultOpenSSLContextFactory("ssl/server.key", "ssl/server.crt"))

reactor.suggestThreadPoolSize(4)
reactor.run()


