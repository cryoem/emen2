# ts.py  Steven Ludtke  06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

#from twisted.web.resource import Resource
from emen2 import Database
#from twisted.web import xmlrpc
#import xmlrpclib
#import os
#from sets import Set
from emen2.emen2config import *

import atexit

# we open the database as part of the module initialization
db=None
DB=Database 

def startup(path):
	global db
	db=Database.Database(EMEN2DBPATH)
	


#######################
# THREAD POOL
#######################

import threading
import Queue

WORKERS = 5

class Worker(threading.Thread):
		def __init__(self, queue):
			self.__queue = queue
			print "Starting thead.."
			self.db = Database.Database(EMEN2DBPATH)
			threading.Thread.__init__(self)

		def run(self):
			while 1:
				q = self.__queue.get()

				if q is None:
					print "Ending thread"
					break

				q[0](q[1],db=self.db)
							
							
queue = Queue.Queue(0)
threads = []

for i in range(WORKERS):
	Worker(queue).start()

		
print threads

#######################

import signal
import sys
def threadterminate():
	print "ending worker queues..."
	for i in range(WORKERS):
		queue.put(None)
	print "ended.."

atexit.register(threadterminate)

#######################