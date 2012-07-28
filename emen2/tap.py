import emen2.db.log

import twisted.python.log
from twisted.application import service, internet
from twisted.python import usage
from twisted.python.log import FileLogObserver
from twisted.python import util, context, reflect

# Take the base DBOptions and add subcommands.
import emen2.db.config
import emen2.web.server
Options = emen2.web.server.WebServerOptions


class Testlog(FileLogObserver):
    def emit(self, event):
        util.untilConcludes(self.write, "%s\n"%(event))
        util.untilConcludes(self.flush)     # Hoorj!        


def logger():
    emen2.db.log.logger.start()
    return emen2.db.log.logger.emit


def makeService(options):
    # Load the configuration
    import emen2.db.config
    emen2.db.config.UsageParser(options=options)

    # Start the service
    s = service.MultiService()
    server = emen2.web.server.EMEN2Server(options)
    server.start(service=s)    
    return s
