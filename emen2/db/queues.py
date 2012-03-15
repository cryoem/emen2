# $Id$
"""EMEN2 process and message queues
"""

import time
import random
import subprocess
import threading
import Queue


try:
	import multiprocessing
	CPU_COUNT = multiprocessing.cpu_count()
except:
	CPU_COUNT = 2

##### Subprocess queues #####

# threading.Thread style
class ProcessWorker(object):
	def __init__(self, queue):
		self.queue = queue

	def run(self):
		while True:
			priority, item = self.queue.get()
			if item is None:
				self.queue.add_task(None)
				return
			print "ProcessWorker:", item
			a = subprocess.Popen(item)
			a.wait()
			self.queue.task_done()
			
			

class ProcessQueue(Queue.PriorityQueue):
	"""A queue of processes to run."""
	worker = ProcessWorker
	
	def add_task(self, task, priority=100):
		"""Add a task to the queue. Highest priority is 0, lowest priority is 1000. Default is 100."""
		if priority < 0 or priority > 1000:
			raise ValueError, "Highest priority is 0, lowest priority is 1000"
		return self.put((priority, task))

	def end(self):
		"""Allow all queued jobs to complete, then exit."""
		return self.put((1001, None))

	def stop(self):
		"""Allow running jobs to complete, then exit."""
		return self.put((-1, None))

	def start(self, processes=1):
		for i in range(processes):
			worker = self.worker(self)
			t = threading.Thread(target=worker.run)
			t.daemon = True
			t.start()
			

processqueue = ProcessQueue()
processqueue.start(processes=CPU_COUNT)


if __name__ == "__main__":
	pq = ProcessQueue()
	for i in range(20):
		pq.add_task(['touch', '%s.txt'%i])
	pq.start()
	pq.join()
	# pq.end()


__version__ = "$Revision$".split(":")[1][:-1].strip()