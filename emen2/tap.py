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
		# text = textFromEventDict(eventDict)
		# if text is None:
		# 	return
		# 
		# timeStr = self.formatTime(eventDict['time'])
		# fmtDict = {'system': eventDict['system'], 'text': text.replace("\n", "\n\t")}
		# msgStr = _safeFormat("[%(system)s] %(text)s\n", fmtDict)
		# 
		# util.untilConcludes(self.write, "%s - %s\n"%(event['system'], event['message']))
		util.untilConcludes(self.write, "%s\n"%(event))
		util.untilConcludes(self.flush)	 # Hoorj!		


def logger():
	return Testlog(open("test.log", "w")).emit



def makeService(options):
	# Load the configuration
	import emen2.db.config
	emen2.db.config.UsageParser(options=options)

	# Start the service
	s = service.MultiService()
	server = emen2.web.server.EMEN2Server(options)
	server.start(service=s)	
	return s
