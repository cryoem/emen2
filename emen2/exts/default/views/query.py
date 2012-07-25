# $Id$
import os
import operator
import copy
import urllib

import emen2.util.listops
from emen2.web.view import View

cmp_order = [
	".is.",
	"==",
	".not.",
	"!=",
	".contains.",
	".gte.",
	">=",
	".lte.",
	"<=",
	".gt.",
	">",
	".lt.",
	"<",
	".any.",
	'.none.',
	'.noop.'
]


def query_to_path(q):
	pass



def path_to_query(path, **kwargs):
	q = {}
	q['c'] = []
	if path == None:
		path = ''
	c = path.split("/")

	for constraint in c:
		constraint = urllib.unquote(constraint)
		match = []
		foundcomps = filter(lambda x:constraint.partition(x)[1], cmp_order)
		if foundcomps:
			comp = foundcomps[0]
			p1, p2, p3 = constraint.partition(comp)
			p1 = urllib.unquote(p1)
			p2 = urllib.unquote(p2).replace('.','')
			p3 = urllib.unquote(p3)

			if p1:
				match.append(p1)
				if p2:
					match.append(p2)
					if p3:
						match.append(p3)

		elif constraint:
			match = [constraint]

		if match:
			q['c'].append(match)

			
	# General query...
	keywords = kwargs.pop('keywords', None)
	if keywords:
		q['c'].append(['*','contains',keywords])

	q.update(kwargs)
	return q



class TooManyFiles(Exception):
	pass


@View.register
class Query(View):

	def initq(self, path=None, q=None, c=None, **kwargs):
		self.template = '/pages/query.main'
		self.title = "Query"
		if q:
			self.q = q
		else:
			self.q = path_to_query(path, **kwargs)
		if c:
			self.q['c'] = c

		self.ctxt['parent'] = None
		self.ctxt['rectype'] = None
		self.ctxt['header'] = True
		self.ctxt['controls'] = True
		

	@View.add_matcher(r'^/query/$', name='main')
	@View.add_matcher(r'^/query/(?P<path>.*)/$', name='query')
	def main(self, path=None, q=None, c=None, **kwargs):
		self.initq(path, q, c, **kwargs)
		self.q = self.db.table(**self.q)
		self.set_context_item('q', self.q)


	@View.add_matcher(r'^/query/(?P<path>.*)/embed/$')
	def embed(self, path=None, q=None, c=None, create=False, rectype=None, parent=None, controls=True, header=True, **kwargs):
		# create/rectype/parent for convenience.
		self.main(path, q, c)
		self.template = '/pages/query'
		# awful hack
		self.ctxt['controls'] = controls
		self.ctxt['header'] = header
		self.ctxt['parent'] = parent
		self.ctxt['rectype'] = rectype
		

	@View.add_matcher(r'^/query/(?P<path>.*)/edit/$', name='edit')
	def edit(self, path=None, q=None, c=None, **kwargs):
		self.initq(path, q, c)
		self.template = '/pages/query.edit'
		self.q = self.db.table(**self.q)
		self.set_context_item('q', self.q)


	@View.add_matcher(r'^/plot/(?P<path>.*)/edit/$', name='edit')
	def edit(self, path=None, q=None, c=None, **kwargs):
		self.initq(path, q, c)
		self.template = '/pages/query.plot'
		self.q = self.db.plot(**self.q)
		self.set_context_item('q', self.q)


	# /download/ can't be in the path because of a emen2resource.getchild issue
	@View.add_matcher(r'^/query/(?P<path>.*)/attachments/$', name='attachments')
	def attachments(self, path=None, q=None, c=None, confirm=False, **kwargs):
		self.initq(path, q, c)
		self.template = '/pages/query.files'
		self.q = self.db.query(**self.q)
		self.set_context_item('q', self.q)

		# Look up all the binaries
		bdos = self.db.binary.find(record=self.q['names'], count=0)
		if len(bdos) > 100000 and not confirm:
			raise TooManyFiles, "More than 100,000 files returned. Please see the admin if you need to download the complete set."

		records = set([i.record for i in bdos])
		users = set([bdo.get('creator') for bdo in bdos])
		users = self.db.user.get(users)
		self.ctxt['users'] = users
		self.ctxt['recnames'] = self.db.record.render(records)
		self.ctxt['bdos'] = bdos





__version__ = "$Revision$".split(":")[1][:-1].strip()
