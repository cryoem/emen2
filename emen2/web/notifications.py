import twisted.internet.reactor
import contextlib
import time
import twisted.internet.defer
import thread
import threading
import emen2.web.events
import emen2.db.proxy
import Queue
import collections

class NotificationHandler(object):
	_notifications_by_ctxid = {}
	_nlock = threading.RLock()


	events = emen2.web.events.EventRegistry()

	@contextlib.contextmanager
	def set_db(self, db):
		self.db = self.get_db_instance(db)
		yield self
		if hasattr(self, 'db'):
			del self.db

	def start(self):
		self.db = emen2.db.proxy.DBProxy()
		self.register_eventhandlers()

	def notify(self, ctxid, msg):
		with self._nlock:
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
			print 'creating new db'
			db = emen2.db.proxy.DBProxy()
		return db

	def pub_get_notifications(self, ctxid, host, db=None):
		with self.set_db(db):
			self.db._setContext(ctxid, host)
			try:
				result = self.get_notifications(ctxid)
				print 'get_notifications', result
				return result
			finally:
				self.db._clearcontext()

	def pub_notify(self, ctxid, host, msg, toctxid=None, db=None):
		with self.set_db(db):
			#self.db._setContext(ctxid, host)
			try:
				if toctxid is None:
					toctxid = ctxid
				self.notify(toctxid, msg)
			finally:
				pass #self.db._clearcontext()

	def poll(self, ctxid, host, db=None):
		with self.set_db(db):
			#self.db._setContext(ctxid, host)
			try:
				print 'getting'
				result = self.__getqueue(ctxid).get()
				print 'done'
				return result
			finally:
				pass
				#self.db._clearcontext()



