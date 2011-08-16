import twisted.internet.reactor
import time
import twisted.internet.defer
import thread
import threading
import emen2.web.events
import emen2.db.config
import emen2.db.proxy
import Queue
import collections
config = emen2.db.config.g()

class NotificationHandler(object):
	_notifications_by_ctxid = {}
	_nlock = threading.RLock()

	events = emen2.web.events.EventRegistry()

	def start(self):
		self.db = emen2.db.proxy.DBProxy()
		self.register_eventhandlers()

	def notify(self, ctxid, msg):
		#self._notifications_by_ctxid.setdefault(ctxid, collections.deque()).append(msg)
		with self._nlock:
			self._notifications_by_ctxid.setdefault(ctxid, Queue.Queue()).put(msg)
		return self

	def get_notifications(self, ctxid):
		with self._nlock:
			q = self._notifications_by_ctxid.get(ctxid)

		result = []

		if q is not None:
			try:
				while True:
					result.append(q.get(False))
					q.task_done()
			except Queue.Empty: pass
		return result

	##################
	# event handlers #
	##################
	def register_eventhandlers(self):
		with self.events.event('notify') as e:
			e.add_cb(lambda ctxid, msg: self.notify(ctxid, msg))
		with self.events.event('pub.notify') as e:
			e.add_cb(self.pub_notify)
		with self.events.event('pub.get_notifications') as e:
			e.add_cb(self.pub_get_notifications)

	def pub_get_notifications(self, ctxid, host):
		db = emen2.db.proxy.DBProxy()
		db._setContext(ctxid, host)
		try:
			return self.get_notifications(ctxid)
		finally:
			db._clearcontext()

	def pub_notify(self, ctxid, host, msg, toctxid=None):
		db = emen2.db.proxy.DBProxy()
		db._setContext(ctxid, host)
		try:
			if toctxid is None:
				toctxid = ctxid
			self.notify(toctxid, msg)
		finally:
			db._clearcontext()


