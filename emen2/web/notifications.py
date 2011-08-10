import time
import threading
import emen2.web.eventhandler
import emen2.db.config
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

	events = emen2.web.eventhandler.EventRegistry()

	def start(self):
		with self.events.event('notify') as e:
			e.add_cb(lambda ctxid, msg: self.push_notification(Notification(ctxid, msg)))

	def push_notification(self, notification):
		self._notification_queue.put(notification)

	def sort_notifications(self):
		while True:
			time.sleep(.5)
			notification = self._notification_queue.get()
			with self._nlock:
				q = self._notifications_by_ctxid.setdefault(notification.ctxid, Queue.Queue())
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

