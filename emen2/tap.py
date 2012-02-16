import emen2.db.log

import twisted.python.log
from twisted.application import service, internet
from twisted.python import usage

# Take the base DBOptions and add subcommands.
import emen2.db.config
import emen2.web.server
Options = emen2.web.server.WebServerOptions


def makeService(options):
	# Load the configuration
	import emen2.db.config
	emen2.db.config.UsageParser(options=options)

	# Start the service
	s = service.MultiService()
	server = emen2.web.server.EMEN2Server(options)
	server.start(service=s)	
	return s
