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

# http://blog.enterthefoo.com/2009/02/twisted-sleep.html
def sleep(secs):
    d = Deferred()
    reactor.callLater(secs, d.callback, None)
    return d


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
		'''start the notification systems:

		- register events
		- set self.db
		'''
		self.db = emen2.db.proxy.DBProxy()
		self.register_eventhandlers()
		return self

	def notify(self, ctxid, msg):
		'''send a message to a ctxid (ctxid so that error messages can be sent to a particular user)'''
		self.__getqueue(ctxid).appendleft(msg)
		return self

	def __getqueue(self, ctxid):
		'''get the message queue associated with a given ctxid'''
		if ctxid not in self._notifications_by_ctxid:
			with self.nlock:
				self._notifications_by_ctxid[ctxid] = collections.deque()
		return self._notifications_by_ctxid[ctxid]

	def get_notification(self, ctxid):
		'''Get a notifications, returns None if none found'''
		result = None
		try:
			result = self.__getqueue(ctxid).pop(False)
		except IndexError:
			pass # if the Queue is empty, just return None
		return result

	def get_notifications(self, ctxid):
		'''Get all notifications pending for a given ctxid'''
		q = self.__getqueue(ctxid)

		result = []

		try:
			while True:
				result.append(q.pop(False))
				q.task_done()
		except IndexError: pass
		return result

	##################
	# event handlers #
	##################
	def register_eventhandlers(self):
		'''register event handlers'''
		with self.events.event('notify') as e:
			e.add_cb(self.notify)
		with self.events.event('pub.poll') as e:
			e.add_cb(self.poll)
		with self.events.event('pub.notify') as e:
			e.add_cb(self.pub_notify)
		with self.events.event('pub.get_notifications') as e:
			e.add_cb(self.pub_get_notifications)

	def get_db_instance(self, db):
		'''If db is None, return a new db instance, otherwise return the value of db'''
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
				result = None
				while result is None:
					try:
						result = self.__getqueue(ctxid).pop()
					except IndexError: pass
					time.sleep(.01)
				print 'done'
				return result
			finally:
				pass
				#self.db._clearcontext()



