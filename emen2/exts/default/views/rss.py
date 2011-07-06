# $Id$
from emen2.web.view import View, Page
from emen2.web import routing
from emen2.web import responsecodes
import time
import datetime
import calendar
import emen2.db.config
g = emen2.db.config.g()


class Item(object):
	def __init__(self, title, rec):
		self.title = title
		self.data = rec
		self.name = rec.name
		self.date = rec['creationtime']


class RSS(View):
	__metaclass__ = View.register_view
	__matcher__ = dict(
		main=r'^/rss/(?P<begin>\d+)/(?P<end>\d+)/$',
		to_now=r'^/rss/(?P<begin>\d+)/$',
		past_x_time=r'^/rss/-(?P<amount>\d+)(?P<unit>[ymdHMS])/$'
	)

	time_map = {'y': ('Year',  365),
				'm': ('Month', '%m'),
				'd': ('Day',   '%d'),
				'H': ('Hour',  '%H'),
				'M': ('Minute','%M'),
				'S': ('Second','%S')}

	def __init__(self, ctxid, host, db, begin='', end='', amount='', unit=''):
		View.__init__(self, ctxid, host, db, template='/user/rss', mimetype='text/xml')
		if begin != '':
			self.get_data = self.render
			self._begin = time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(begin, '%Y%m%d%H%M%S'))
		# should worok, but broken
		#elif amount != '':
		#	self.get_data = self._get_amount
		#	self._amount = int(amount)
		#	self._unit=unit
		if end != '':
			self._end = time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(end, '%Y%m%d%H%M%S'))
		else:
			self._end = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

	def _get_amount(self):
		delta = None
		if self._unit == 'y':
			delta = datetime.timedelta(days=self._amount*365)
		elif self._unit == 'm':
			days = 0
			for c in range(self._amount):
				dys = calendar.mdays[((datetime.date.today().month - c) % 12) + 1]
				g.info(dys)
				days += dys
			delta = datetime.timedelta(days=days)
		elif self._unit == 'd':
			delta = datetime.timedelta(days=self._amount)
		elif self._unit == 'H':
			delta = datetime.timedelta(seconds=self._amount*3600)
		elif self._unit == 'M':
			delta = datetime.timedelta(seconds=self._amount*60)
		elif self._unit == 'S':
			delta = datetime.timedelta(seconds=self._amount)
		self._begin = datetime.datetime.strptime(self._end, "%Y/%m/%d %H:%M:%S") - delta
		self._begin = self._begin.strftime("%Y/%m/%d %H:%M:%S")
		return self.render()

	def render(self):
		g.info('begin -> %r' % self._begin)
		g.info('end -> %r' % self._end)
		recs = self.db.getindexbyvalue('modifytime', (self._begin, self._end))
		recs = self.db.getrecord(recs)
		items = []
		for x in recs:
			items.append(Item(x.name, x))
		self.set_context_item('items', items)
		self.title = '%s Record Feed - %s to %s' % (g.EMEN2DBNAME, self._begin, self._end)
		return View.get_data(self)
__version__ = "$Revision$".split(":")[1][:-1].strip()
