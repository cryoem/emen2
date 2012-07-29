import twisted.python.log
import twisted.application

import emen2.db.log
import emen2.db.config
import emen2.web.server
Options = emen2.web.server.WebServerOptions


def logger():
    emen2.db.log.logger.start()
    return emen2.db.log.logger.emit


def makeService(options):
    # Load the configuration
    import emen2.db.config
    emen2.db.config.UsageParser(options=options)

    # Start the service
    s = twisted.application.service.MultiService()
    server = emen2.web.server.EMEN2Server(options)
    server.start(service=s)    
    return s
