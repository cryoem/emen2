#!/usr/bin/env python

import sys

import emen2.clients
import emen2.clients.controllers

##################################
# Main()
##################################


def print_help():
	print """%s <action>

Actions available: upload, download

For detailed help: %s <action> --help

	"""%(sys.argv[0],sys.argv[0])




def main():
	parser = emen2.clients.controllers.DBRPCOptions()

	controllers = {
		"download":emen2.clients.controllers.DownloadController,
		"upload":emen2.clients.controllers.UploadController,
		"sync":emen2.clients.controllers.SyncController
	}

	try:
		action = sys.argv[1]
	except:
		action = "help"

	if action in ["-h","--help","help"]:
		return print_help()

	try:
		if len(sys.argv) == 2:
			sys.argv.append("-h")
		controller = controllers.get(action)(args=sys.argv[2:])

	except Exception, inst:
		print "Error: %s"%inst
		sys.exit(0)

	controller.run()



if __name__ == "__main__":
	main()


