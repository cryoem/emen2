from twisted.internet import reactor
from twisted.web import static, server
from emen2 import TwistSupport
from emen2 import TwistSupport_html

root = static.File("/home/stevel/pro/emen2/tweb")
root.putChild("db",TwistSupport_html.DBResource())
root.putChild("RPC2",TwistSupport.DBXMLRPCResource())
reactor.listenTCP(8080, server.Site(root))
reactor.run()
