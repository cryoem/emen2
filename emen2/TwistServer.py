#!/bin/env python
# This is the main server program for EMEN2
# TwistSupport contains the actual XMLRPC methods
# TwistSupport_html contains the HTML methods

from twisted.internet import reactor
from twisted.web import static, server
from emen2 import TwistSupport
from emen2 import TwistSupport_html

# Change this to a directory for the actual database files
TwistSupport.startup("/home/stevel/emen2test")
TwistSupport_html.db=TwistSupport.db

# Change this to point to static HTML content
root = static.File("/home/stevel/pro/emen2/tweb")

root.putChild("db",TwistSupport_html.DBResource())
root.putChild("RPC2",TwistSupport.DBXMLRPCResource())

# You can set the port to listen on...
reactor.listenTCP(8080, server.Site(root))
reactor.run()
