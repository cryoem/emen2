import time
import threading
import emen2.web.events
import emen2.db.config
import emen2.db.proxy
import Queue
config = emen2.db.config.g()

class Notification(object):
	def __init__(self, ctxid, msg):
		self.ctxid = ctxid
		self.msg = msg
	@classmethod
	def from_dict(cls, dct):
		return cls(dct.get('ctxid'), dct['msg'])

class NotificationHandler(object):
	_notification_queue = Queue.Queue()

	_notifications_by_ctxid = {}
	_nlock = threading.RLock()

	events = emen2.web.events.EventRegistry()

	def start(self):
		self.db = emen2.db.proxy.DBProxy()
		with self.events.event('notify') as e:
			e.add_cb(lambda ctxid, msg: self.push_notification(Notification(ctxid, msg)))
		with self.events.event('pub.notify') as e:
			e.add_cb(self.pub_notify)
		with self.events.event('pub.get_notifications') as e:
			e.add_cb(self.pub_get_notifications)
		with self.events.event('pub.poll_notifications') as e:
			e.add_cb(self.poll)

	def poll(self, ctxid, host):
		db = emen2.db.proxy.DBProxy()
		db._setContext(ctxid, host)
		try:
			q = self._notifications_by_ctxid.get(ctxid)
			if q is not None:
				return q.get(True, 100)
			else:
				return ''
		finally:
			db._clearcontext()


	def push_notification(self, notification):
		self._notification_queue.put(notification)

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
			self.push_notification(Notification(toctxid, msg))
		finally:
			db._clearcontext()

	def sort_notifications(self):
		while True:
			notification = self._notification_queue.get()
			if notification.ctxid == 'ALL':
				for q in self._notifications_by_ctxid.values():
					q.put(notification.msg)
			else:
				with self._nlock:
					print 'sort lock'
					q = self._notifications_by_ctxid.setdefault(notification.ctxid, Queue.Queue())
				print 'sort unlock'
				q.put(notification.msg)

	def get_notifications(self, ctxid):
		with self._nlock:
			q = self._notifications_by_ctxid.get(ctxid)

		result = []
		if q is not None:
			try:
				while True:
					result.append(q.get(False))
			except Queue.Empty: pass
		return result

