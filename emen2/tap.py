import emen2.db.log

import twisted.python.log
from twisted.application import service, internet
from twisted.python import usage

import emen2.db.config
import emen2.web.server

class CommandStart(emen2.web.server.WebServerOptions):
	def postOptions(self):
		print "Starting with postOptions"

class CommandStop(emen2.web.server.WebServerOptions):
	pass

class CommandRestart(emen2.web.server.WebServerOptions):
	pass

class CommandCreate(usage.Options):
	pass
	
class CommandPasswd(usage.Options):
	pass
	
class CommandRecover(usage.Options):
	pass
	
class CommandReindex(usage.Options):
	pass
	
class CommandLoad(usage.Options):
	pass
	
class CommandDump(usage.Options):
	pass


# Take the base DBOptions and add subcommands.
class Options(emen2.db.config.DBOptions):
	subCommands = [
		['start', None, CommandStart, 'Start web server'],
		['stop', None, CommandStart, 'Stop web server'],
		['restart', None, CommandStart, 'Restart web server'],
		['create', None, CommandStart, 'Create new database'],
		['passwd', None, CommandStart, 'Change a password'],
		['recover', None, CommandStart, 'Run database recovery'],
		['reindex', None, CommandStart, 'Rebuild indexes'],
		['load', None, CommandStart, 'Import data'],
		['dump', None, CommandStart, 'Export data']
		]

def makeService(config):
	server = emen2.web.server.EMEN2Server()
	s = service.MultiService()
	sc = config.subCommand
	
	if sc in ['stop', 'restart']:
		print "Stopping service"

	if sc in ['start', 'restart']:
		print "Starting service"
		server.start(config=config, service=s)		
	elif sc == 'create':
		print "Creating new database"
	elif sc == 'passwd':
		print "Changing password"
	elif sc == 'recover':
		print "Running recovery"
	elif sc == 'reindex':
		print "Reindexing database"
	elif sc == 'load':
		print "Loading data"
	elif sc == 'dump':
		print "Dumping data"
	
	
	return s
