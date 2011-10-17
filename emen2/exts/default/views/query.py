# $Id$
import os
import operator
import copy
import urllib

import emen2.util.listops
from emen2.web.view import View




cmp_order = [".is.", "==", ".not.", "!=", ".contains.", ".gte.", ">=", ".lte.", "<=", ".gt.", ">", ".lt.", "<", ".any.", '.none.', '.noop.', '.name.']
# lookup = {
# 	"is": "==",
# 	"not": "!=",
# 	"gte": ">=",
# 	"lte": "<=",
# 	"gt": ">",
# 	"lt": "<"
# }



def convert_bytes(bytes):
	bytes = float(bytes)
	if bytes >= 1099511627776:
		terabytes = bytes / 1099511627776
		size = '%.2f TB' % terabytes
	elif bytes >= 1073741824:
		gigabytes = bytes / 1073741824
		size = '%.2f GB' % gigabytes
	elif bytes >= 1048576:
		megabytes = bytes / 1048576
		size = '%.2f MB' % megabytes
	elif bytes >= 1024:
		kilobytes = bytes / 1024
		size = '%.2f KB' % kilobytes
	else:
		size = '%.2f bytes' % bytes
	return size



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

	for k,v in kwargs.items():
		q[urllib.unquote(k)] = urllib.unquote(v)

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
			

	@View.add_matcher(r'^/query/$', name='main')
	@View.add_matcher(r'^/query/(?P<path>.*)/$', name='query')
	def main(self, path=None, q=None, c=None):
		self.initq(path, q, c)
		self.q['count'] = 100
		self.q['table'] = True
		self.q['stats'] = True
		self.q = self.db.query(**self.q)
		self.set_context_item('q', self.q)


	@View.add_matcher(r'^/query/(?P<path>.*)/embed/$')
	def embed(self, path=None, q=None, c=None):
		self.main(path, q, c)
		self.template = '/pages/query'


	@View.add_matcher(r'^/query/(?P<path>.*)/edit/$', name='edit')
	def edit(self, path=None, q=None, c=None):
		self.initq(path, q, c)
		self.template = '/pages/query.edit'
		self.q = self.db.query(**self.q)
		self.set_context_item('q', self.q)


	# /download/ can't be in the path because of a emen2resource.getchild issue
	@View.add_matcher(r'^/query/(?P<path>.*)/attachments/$', name='attachments')
	def attachments(self, path=None, q=None, c=None, confirm=False):
		self.initq(path, q, c)
		self.template = '/pages/query.files'
		self.q = self.db.query(**self.q)
		self.set_context_item('q', self.q)

		# Look up all the binaries
		bdos = self.db.findbinary(record=self.q['names'])
		
		for bdo in bdos:
			if bdo.get('filesize') == None:
				if os.access(bdo.get('filepath'), os.F_OK):
					bdo.filesize = os.stat(bdo.get('filepath')).st_size

		if len(bdos) > 1000:
			raise TooManyFiles, "More than 1000 files returned. Are you sure you want to continue?"

		filesize = sum([(bdo.get('filesize') or 0) for bdo in bdos])

		records = set([i.record for i in bdos])
		users = set([bdo.get('creator') for bdo in bdos])
		users = self.db.getuser(users)
		self.ctxt['users'] = emen2.util.listops.dictbykey(users, 'name')
		self.ctxt['rendered'] = self.db.renderview(records)
		self.ctxt['filesize'] = convert_bytes(filesize)
		self.ctxt['bdos'] = bdos


	# @View.add_matcher(r'^/query/(?P<path>.*)/goupby/$')
	# def groupby(self, path=None, *args, **kwargs):
	# 	self.template = '/pages/query.groupby'
	# 	# if name == None:
	# 	# 	name = g.BOOKMARKS.get("GROUPS", 0)
	# 	# recs = self.db.getchildren(name, recurse=3, rectype="project")
	# 	# recs = self.db.getrecord(recs)			
	# 	if path == None:
	# 		path = "rectype==project"
	# 
	# 	self.q = path_to_query(path, **kwargs)
	# 	self.q = self.db.query(**self.q)
	# 	names = self.q.get('names', [])
	# 	recs = self.db.getrecord(names)
	# 	
	# 	self.title = "Projects"
	# 
	# 	sortitems = collections.defaultdict(set)
	# 	sortkey = kwargs.get('sortkey', 'project_status')
	# 	for rec in recs:
	# 		try:
	# 			sortitems[rec.get(sortkey)].add(rec.name)
	# 		except:
	# 			sortitems[",".join(rec.get(sortkey))].add(rec.name)
	# 
	# 	children = self.db.getchildren([rec.name for rec in recs], recurse=-1)
	# 	grouped = self.db.groupbyrectype(emen2.util.listops.flatten(children))
	# 	grouped_inverse = emen2.util.listops.invert(grouped)
	# 
	# 	mostrecents = set()
	# 
	# 	details = {}
	# 	for rec in recs:
	# 		d = {}
	# 		c = children.get(rec.name)
	# 		d['grouped'] = collections.defaultdict(set)
	# 		for c1 in c:
	# 			d['grouped'][grouped_inverse.get(c1)].add(c1)
	# 
	# 		d['mostrecent'] = {}
	# 		for k,v in d['grouped'].items():
	# 			mr = sorted(v)[-1]
	# 			d['mostrecent'][k] = mr
	# 			mostrecents.add(mr)
	# 		details[rec.name] = d
	# 
	# 
	# 	mostrecents = self.db.getrecord(mostrecents)
	# 	recs.extend(mostrecents)
	# 	rendered = self.db.renderview(recs)
	# 	self.ctxt['recsdict'] = emen2.util.listops.dictbykey(recs, 'name')
	# 
	# 	pages = {
	# 		'classname':'main',
	# 		'labels': {}
	# 	}
	# 
	# 	pages['order'] = sortitems.keys()
	# 	for k,v in sortitems.items():
	# 		pages['labels'][k]='%s (%s)'%(k, len(v))
	# 
	# 	self.set_context_item('pages',pages)
	# 
	# 	self.set_context_item("rendered",rendered)
	# 	self.set_context_item("sortitems",sortitems)
	# 
	# 	self.ctxt["rendered"] = rendered
	# 	self.ctxt["sortitems"] = sortitems
					
					
						
		
__version__ = "$Revision$".split(":")[1][:-1].strip()