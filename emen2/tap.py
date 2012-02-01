import emen2.db.log

import twisted.python.log
from twisted.application import service, internet
from twisted.python import usage

# Take the base DBOptions and add subcommands.
import emen2.db.config
Options = emen2.db.config.DBOptions

def makeService(options):
	# Load the configuration
	import emen2.db.config
	emen2.db.config.UsageParser(options=options)

	# Start the service
	import emen2.web.server
	server = emen2.web.server.EMEN2Server()
	s = service.MultiService()
	server.start(service=s)	
	return s
