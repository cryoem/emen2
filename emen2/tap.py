import emen2.db.log
from twisted.application import service, internet
import twisted.python.log
import emen2.db.config
import emen2.web.server

server = emen2.web.server.EMEN2Server()

# The 'Options' module attribute is used by twistd as the options
Options = emen2.web.server.EMEN2Server.usage

def makeService(config):
	s = service.MultiService()
	server.start(config=config, service=s)
	return s
