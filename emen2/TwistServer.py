#!/bin/env python
# This is the main server program for EMEN2
# TwistSupport contains the actual XMLRPC methods
# TwistSupport_html contains the HTML methods

from twisted.internet import reactor
from twisted.web import static, server
from emen2 import TwistSupport
from emen2 import TwistSupport_db
from emen2.emen2config import *

# Change this to a directory for the actual database files
TwistSupport.startup(EMEN2DBPATH)
TwistSupport_db.db=TwistSupport.db

from emen2 import TwistSupport_html

# Change this to point to static HTML content
root = static.File(EMEN2ROOT+"/tweb")

root.putChild("db",TwistSupport_html.DBResource())
root.putChild("RPC2",TwistSupport.DBXMLRPCResource())

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.run()
