from twisted.internet import reactor
from twisted.web import static, server
from emen2 import TwistSupport

root = static.File("/home/stevel/pro/emen2/tweb")
root.putChild("db",TwistSupport.DBResource())
reactor.listenTCP(8080, server.Site(root))
reactor.run()
