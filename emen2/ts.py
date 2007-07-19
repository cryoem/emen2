# ts.py	 Steven Ludtke	06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

#from twisted.web.resource import Resource
from emen2 import Database
from emen2.emen2config import *

import atexit

from twisted.internet import reactor

import threading
import Queue


db=None
DB=Database 

def startup(path):
	global db
	db=Database.Database(EMEN2DBPATH)
	

#######################
# THREAD POOL
#######################
#
# 
# WORKERS = 1
# 
# class Worker(threading.Thread):
# 		def __init__(self, queue):
# 			self.__queue = queue
# 			print "Starting thead.."
# 			self.db = Database.Database(EMEN2DBPATH)
# 			threading.Thread.__init__(self)
# 
# 		def run(self):
# 			while 1:
# 				q = self.__queue.get()
# 
# 				if q is None:
# 					print "Ending thread"
# 					break
# 
# 				q[0](q[1],db=self.db)
# 							
# 							
# queue = Queue.Queue(0)
# threads = []
# 
# for i in range(WORKERS):
# 	Worker(queue).start()
# 
# 		
# print threads
#
#######################
#
#import signal
#import sys
#def threadterminate():
#	print "ending worker queues..."
#	for i in range(WORKERS):
#		queue.put(None)
#	print "ended.."
#
#atexit.register(threadterminate)
#
#######################


from twisted.python import threadpool
from twisted.internet import defer, reactor, threads
from twisted.python import log, runtime, context


class newThreadPool(threadpool.ThreadPool):
	__inited = 0
	min = 5
	max = 10
	joined = 0
	started = 0
	workers = 0
	name = None

	def __init__(self, minthreads=5, maxthreads=10, name=None):
		"""Create a new threadpool.
		@param minthreads: minimum number of threads in the pool
		@param maxthreads: maximum number of threads in the pool
		"""
		assert minthreads >= 0, 'minimum is negative'
		assert minthreads <= maxthreads, 'minimum is greater than maximum'
	
		self.q = Queue.Queue(0)
		self.min = minthreads
		self.max = maxthreads
		self.name = name
		if runtime.platform.getType() != "java":
			self.waiters = []
			self.threads = []
			self.working = []
		else:
			self.waiters = ThreadSafeList()
			self.threads = ThreadSafeList()
			self.working = ThreadSafeList()

	def start(self):
		"""Start the threadpool."""
		print "starting threadpool..."		
		self.joined = 0
		self.started = 1
		# Start some threads.
		self.adjustPoolsize()

	def startAWorker(self):
		print "started twisted thread (newThreadPool)..."
		print "\tworker count: %s"%self.workers
		self.db = Database.Database(EMEN2DBPATH)

		self.workers = self.workers + 1
		name = "PoolThread-%s-%s" % (self.name or id(self), self.workers)
		try:
				firstJob = self.q.get(0)
		except Queue.Empty:
				firstJob = None
				
		newThread = threading.Thread(target=self._worker, name=name, args=(firstJob,))
		self.threads.append(newThread)	
		newThread.start() 
	
	def stopAWorker(self):
		self.q.put(WorkerStop)
		self.workers = self.workers-1
			
	def _worker(self, o):
			print "thread work..."
			print "waiters: %s"%self.waiters
			print "workers: %s"%self.workers
			print "threads: %s"%self.threads
			print "working: %s"%self.working
			
			ct = threading.currentThread()
			while 1:
					if o is threadpool.WorkerStop:
							break
					elif o is not None:
							print "thread working..."
							self.working.append(ct)
							ctx, function, args, kwargs = o
							try:
									# add DB arg to all deferred calls
									args[3]['db']=self.db
									context.call(ctx, function, *args, **kwargs)
							except:
									context.call(ctx, log.deferr)
							self.working.remove(ct)
							del o, ctx, function, args, kwargs
					self.waiters.append(ct)
					o = self.q.get()
					self.waiters.remove(ct)

			self.threads.remove(ct)			

#print "installing new threadpool."
threadpool.ThreadPool = newThreadPool
	
