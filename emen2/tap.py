from twisted.application import service, internet
import emen2.web.server

class Variables:
	server = emen2.web.server.EMEN2Server()

import emen2.db.config
Options = Variables.server.options


def makeService(config):
	s = service.MultiService()

	emen2.web.server.start_emen2(Variables.server, config=config).attach_to_service(s)

	return s
