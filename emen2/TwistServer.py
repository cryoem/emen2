#!/bin/env python
# This is the main server program for EMEN2
# ts contains the actual XMLRPC methods
# ts_html contains the HTML methods

from twisted.internet import reactor
from twisted.web import static, server
from emen2 import ts
from emen2 import xmlrpc
from emen2 import rest

#from emen2 import ts_db
from emen2.emen2config import *

# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)
#ts_db.db=ts.db

#from emen2 import web
import emen2.TwistSupport_html.dbresource

# Change this to point to static HTML content
root = static.File(EMEN2ROOT+"/tweb")

root.putChild("db",emen2.TwistSupport_html.dbresource.DBResource())
root.putChild("RPC2",xmlrpc.DBXMLRPCResource())
root.putChild("REST",rest.DBRESTResource())

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.run()
