import twisted.internet.reactor
import contextlib
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
	_listeners = collections.defaultdict(set)
	_notifications_by_ctxid = {}
	_nlock = threading.RLock()


	events = emen2.web.events.EventRegistry()

	@contextlib.contextmanager
	def set_db(self, db):
		self._olddb = getattr(self, 'db', None)
		self.db = self.get_db_instance(db)
		yield self
		self.db = self._olddb
		del self._olddb

	def start(self):
		self.db = emen2.db.proxy.DBProxy()
		self.register_eventhandlers()

	def notify(self, ctxid, msg):
		with self._nlock:
			if ctxid in self._listeners:
				self._listeners[ctxid].pop().callback(msg)
			else:
				self.__getqueue(ctxid).put(msg)
		return self

	def __getqueue(self, ctxid):
		with self._nlock:
			return self._notifications_by_ctxid.setdefault(ctxid, Queue.Queue())

	def get_notification(self, ctxid):
		result = None
		try:
			result = self.__getqueue(ctxid).get(False)
		except Queue.Empty:
			pass # if the Queue is empty, just return None
		return result

	def get_notifications(self, ctxid):
		q = self.__getqueue(ctxid)

		result = []

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
		with self.events.event('pub.poll') as e:
			e.add_cb(self.poll)
		with self.events.event('pub.notify') as e:
			e.add_cb(self.pub_notify)
		with self.events.event('pub.get_notifications') as e:
			e.add_cb(self.pub_get_notifications)

	def get_db_instance(self, db):
		if db is None:
			db = emen2.db.proxy.DBProxy()
		return db

	def pub_get_notifications(self, ctxid, host, db=None):
		with self.set_db(db):
			self.db._setContext(ctxid, host)
			try:
				return self.get_notifications(ctxid)
			finally:
				self.db._clearcontext()

	def pub_notify(self, ctxid, host, msg, toctxid=None, db=None):
		with self.set_db(db):
			self.db._setContext(ctxid, host)
			try:
				if toctxid is None:
					toctxid = ctxid
				self.notify(toctxid, msg)
			finally:
				self.db._clearcontext()

	def poll(self, ctxid, host, db=None):
		with self.set_db(db):
			self.db._setContext(ctxid, host)
			try:
				result = twisted.internet.defer.Deferred()
				n = self.get_notification(ctxid)
				if n is not None:
					result = twisted.internet.defer.succeed(n)
				print 'begin nlock'
				with self._nlock:
					self._listeners[ctxid].add(result)
				print 'end nlock'
				return result
			finally:
				self.db._clearcontext()



