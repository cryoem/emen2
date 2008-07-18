# ts.py	 Steven Ludtke	06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

#from twisted.web.resource import Resource
from emen2 import DBProxy, Database
from emen2.emen2config import *
from twisted.internet import defer, reactor, threads, reactor
from twisted.python import log, runtime, context, threadpool
import Queue
import atexit
import threading
import time




db=None
DB=Database 

def startup(path):
	global db
	db=Database.Database(g.EMEN2DBPATH)
	

#######################
# (old version; doesn't work well with twisted.web) THREAD POOL
#######################
#
# 
# WORKERS = 4
# # 
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
# 				r = q[0][0](q[0][1], q[0][2], q[0][3], q[0][4], db=self.db)
# 				q[1][0](result=r,request=q[1][1])
# 							
# queue = Queue.Queue(0)
# threads = []
# 
# for i in range(WORKERS):
# 	Worker(queue).start()
# 		
# print threads
# #
# #######################
# #
# import signal
# import sys
# def threadterminate():
# 	print "ending worker queues..."
# 	for i in range(WORKERS):
# 		queue.put(None)
# 	print "ended.."
# 
# atexit.register(threadterminate)
#
#######################




class newThreadPool(threadpool.ThreadPool):

	def startAWorker(self):
#		print "started twisted thread (newThreadPool)..."
#		print "\tworker count: %s"%self.workers
#		self.db = Database.Database(EMEN2DBPATH)
#		self.db = db

		self.workers = self.workers + 1
#		name = "PoolThread-%s-%s" % (self.name or id(self), self.workers)
		try:
				firstJob = self.q.get(0)
		except Queue.Empty:
				firstJob = None
				
#		print "initializing thread."		
		newThread = threading.Thread(target=self._worker, args=(firstJob,Database.Database(g.EMEN2DBPATH)))
#		newThread = threading.Thread(target=self._worker, args=(firstJob,DBProxy.DBProxy()))
		self.threads.append(newThread)	
		newThread.start() 
	
	def _worker(self, o, db):		
			ct = threading.currentThread()
			while 1:
					if o is threadpool.WorkerStop:
							break
					elif o is not None:
							self.working.append(ct)

#							print "workers: %s"%self.workers
#							print "waiters: %s"%self.waiters
#							print "threads: %s"%self.threads
#							print "working: %s"%self.working
#							print "btrees: %s"%len(DB.BTree.alltrees)
#							print "intbtrees: %s"%len(DB.IntBTree.alltrees)
#							print "fieldbtrees: %s"%len(DB.FieldBTree.alltrees)
							t1 = time.time(); g.debug.msg('LOG_INFO', '---Time 1 :: %r' % t1)
							ctx, function, args, kwargs = o
							try:
									# add DB arg to all deferred calls
									#args[3]['db']=db
									context.call(ctx, function, *args, **kwargs)
							except:
									context.call(ctx, log.deferr)
							t2 = time.time(); g.debug.msg('LOG_INFO', '---Time 2 :: %r' % t2)
							g.debug.msg('LOG_INFO', 'Total Time (t2-t1) == %r' % (t2-t1))
							self.working.remove(ct)
							del o, ctx, function, args, kwargs
					self.waiters.append(ct)
					o = self.q.get()
					self.waiters.remove(ct)

			self.threads.remove(ct)			

#print "installing new threadpool."
threadpool.ThreadPool = newThreadPool
	
