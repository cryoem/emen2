from __future__ import with_statement
# ts.py	 Steven Ludtke	06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

#from twisted.web.resource import Resource

from emen2.Database.database import DBProxy

from emen2.Database import database
from emen2.emen2config import *
from twisted.internet import defer, reactor, threads, reactor
from twisted.python import log, runtime, context, threadpool, failure
import Queue
import atexit
import threading
import time




#DB=database 

#def startup(path):
#	global db

	
db=database.DBProxy(dbpath=g.EMEN2DBPATH)
	

class newThreadPool(threadpool.ThreadPool):
	counter = 0
	def startAWorker(self):
#		print "started twisted thread (newThreadPool)..."
#		print "\tworker count: %s"%self.workers
#		self.db=database.DBProxy(dbpath=g.EMEN2DBPATH)
		#self.db = database.Database(g.EMEN2DBPATH)
#		self.db = db

		self.workers = self.workers + 1
#		name = "PoolThread-%s-%s" % (self.name or id(self), self.workers)
#		try:
#				firstJob = self.q.get(0)
#		except Queue.Empty:
#				firstJob = None
				
#		print "initializing thread."		
		self.counter += 1
		newThread = threading.Thread(target=self._worker, args=(database.DBProxy(dbpath=g.EMEN2DBPATH),self.counter))
#		newThread = threading.Thread(target=self._worker, args=(firstJob,DBProxy.DBProxy()))
		self.threads.append(newThread)	
		newThread.start() 
	
	def _worker(self, db, count):
		""" 
		Method used as target of the created threads: retrieve task to run
		from the threadpool, run it, and proceed to the next task until
		threadpool is stopped.
		"""
		ct = self.currentThread()
		o = self.q.get()
		while o is not threadpool.WorkerStop:
			self.working.append(ct)
			ctx, function, args, kwargs, onResult = o 
			del o

			try:
				kwargs['db']=db
				result = context.call(ctx, function, *args, **kwargs)
				success = True
			except:
				success = False
				if onResult is None:
					context.call(ctx, log.err)
					result = None
				else:
					result = failure.Failure()

			del function, args, kwargs

			self.working.remove(ct)

			if onResult is not None:
				try:
					context.call(ctx, onResult, success, result)
				except:
					context.call(ctx, log.err)

			del ctx, onResult, result

			self.waiters.append(ct)
			o = self.q.get()
			self.waiters.remove(ct)

		self.threads.remove(ct)

#print "installing new threadpool."
threadpool.ThreadPool = newThreadPool
	
