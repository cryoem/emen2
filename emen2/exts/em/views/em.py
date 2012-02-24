# $Id$
import datetime
from operator import itemgetter
import time

import emen2.db.exceptions
import emen2.db.config
from emen2.web.view import View


@View.register
class EMEquipment(View):
	
	@View.add_matcher(r'^/em/equipment/(?P<name>\d+)/$')
	def main(self, name, **kwargs):
		self.title = 'Equipment'
		self.template = '/em/project.main'

	@View.add_matcher(r'^/em/equipment/new/(?P<rectype>\w+)/$')
	def new(self, rectype, **kwargs):
		self.title = 'New Equipment'
		self.template = '/em/project.new'
		


@View.register
class EMRecordPlugin(View):
	# @View.add_matcher(r'^/em/plugin/ccd/(?P<name>\d+)/$', view='RecordPlugin', name='ccd')
	# @View.add_matcher(r'^/em/plugin/ddd/(?P<name>\d+)/$', view='RecordPlugin', name='ddd')
	# @View.add_matcher(r'^/em/plugin/scan/(?P<name>\d+)/$', view='RecordPlugin', name='scan')
	# def image(self, name, **kwargs):
	# 	name = int(name)
	# 	rec = self.db.getrecord(name)
	# 	self.template = '/em/record.plugin.image'
	# 	self.ctxt['rec'] = rec

	@View.add_matcher(r'^/em/plugin/project/(?P<name>\d+)/$', view='RecordPlugin', name='project')
	@View.add_matcher(r'^/em/plugin/subproject/(?P<name>\d+)/$', view='RecordPlugin', name='subproject')
	def project(self, name, **kwargs):
		name = int(name)
		rec = self.db.getrecord(name)
		self.template = '/em/record.plugin.project'

		# Recent records
		recent = set()
		recent.add(name)	

		# Plot
		now = datetime.datetime.utcnow().isoformat()+'+00:00'
		t = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()+'+00:00'
		q = self.db.plot(
			[['children','is','%s*'%name], ['creationtime', '>=', t]], 
			x={'key':'creationtime', 'bin':'day', 'min':t, 'max':now}, 
			y={'stacked':True}
			)
		self.ctxt['recent_activity'] = q

		# Standard parent map
		parentmap = self.routing.execute('Map/embed', db=self.db, root=name, mode='parents', recurse=3)

		# All children
		children = self.db.getchildren(name, recurse=-1)
		children_grouped = self.db.groupbyrectype(children)
		
		# Add in some tabs for all the typical children
		# rd = self.db.getrecorddef(rec.rectype)
		# for k in rd.typicalchld:
		for k in ['ccd', 'grid_imaging', 'progress_report', 'labnotebook', 'manuscript', 'publication', 'publication_abstract', 'presentation', 'purification']:
			if not children_grouped.get(k):
				children_grouped[k] = set()
		
		# Split off subprojects
		recorddefs = set(children_grouped.keys())

		# project_recorddefs = self.db.getchildren('project', recurse=-1, keytype='recorddef')
		# project_recorddefs.add('project')
		# subprojects = set()
		# for rd in project_recorddefs:
		# 	subprojects |= children_grouped.pop(rd, set())
		subprojects = self.db.getchildren(name, rectype=['project*'])
		recent |= subprojects

		# Show the 5 most recent for each type..
		for k,v in children_grouped.items():
			recent |= set(sorted(v)[-3:])

		# Render the record...
		rec_rendered = self.db.renderview(name, viewname='defaultview', edit=True)

		recnames = self.db.renderview(recent)
		rendered_thumb = self.db.renderview(recent, viewdef='$@thumbnail()')

		self.ctxt['groups'] = self.db.getparents(name, recurse=-1, rectype=['group'])
		self.ctxt['rec'] = rec
		self.ctxt['name'] = name
		self.ctxt['rec_rendered'] = rec_rendered
		self.ctxt['recorddefs'] = self.db.getrecorddef(recorddefs)
		self.ctxt['subprojects'] = subprojects
		self.ctxt['children'] = children
		self.ctxt['children_grouped'] = children_grouped
		self.ctxt['recent'] = recent
		self.ctxt['recent_recs'] = self.db.getrecord(recent)
		self.ctxt['recnames'] = recnames
		self.ctxt['rendered_thumb'] = rendered_thumb
		self.ctxt['parentmap'] = parentmap
	
		

@View.register
class EMHome(View):

	@View.add_matcher(r'^/$', view='Root', name='main')
	@View.add_matcher(r'^/em/home/$')
	def main(self, hideinactive=False, sortkey='name', reverse=False):
		self.title = 'Home'
		self.template = '/em/home'

		banner = None
		render_banner = ''
		
		if not self.ctxt['USER']:			
			self.template = '/em/home.noauth'
			try:
				banner = self.db.getrecord(emen2.db.config.get('bookmarks.BANNER_NOAUTH'))
				render_banner = self.db.renderview(banner, viewname="banner")
			except:
				pass
			self.ctxt['banner'] = banner
			self.ctxt['render_banner'] = render_banner
			return


		try:
			banner = self.db.getrecord(emen2.db.config.get('bookmarks.BANNER'))
			render_banner = self.db.renderview(banner, viewname="banner")
		except:
			pass
		self.ctxt['banner'] = banner
		self.ctxt['render_banner'] = render_banner

		
		# Recent records
		# Add 'Z" to datetime.isoformat()
		# t = '2011-01-01T00:00:00+00:00'
		# now = '2011-02-01T00:00:00+00:00'
		now = datetime.datetime.utcnow().isoformat()+'+00:00'
		t = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()+'+00:00'
		q = self.db.plot(
			[['creationtime', '>=', t]], 
			x={'key':'creationtime', 'bin':'day', 'min':t, 'max':now}, 
			y={'stacked':True}
			)
		self.ctxt['recent_activity'] = q

		# Items to render
		recent = set(q['names'])
		torender = set()

		# Groups; filter by NOT DELETED.
		# groups = self.db.query([['rectype','is','group'], ['deleted', 'none']]).get('names')
		groups = self.db.getchildren(0, rectype=['group'])		
		# groups = self.db.getindexbyrectype('group')
		torender |= groups
		
		# Children of groups (any rectype)
		groups_children = self.db.getchildren(groups)
		projs = set()
		for v in groups_children.values():
			projs |= v
		torender |= projs
			
		# Progress reports
		progress_reports = self.db.getindexbyrectype('progress_report')
		torender |= progress_reports

		# Get projects, most recent children, and progress reports
		projects_children = self.db.getchildren(projs, recurse=-1)
		for k,v in projects_children.items():
			# Children past six months
			# r = v & recent
			# Most recent 
			if v:
				torender.add(sorted(v)[-1])

		# Get all the recent records we want to display
		rendered_recs = self.db.getrecord(torender)
		users = self.db.getuser([i.get('creator') for i in rendered_recs])

		rendered_recs = dict([(i.name,i) for i in rendered_recs])
		users = dict([(i.name,i) for i in users])
		recnames = self.db.renderview(torender)
		
		
		self.ctxt['groups_children'] = groups_children
		self.ctxt['recnames'] = recnames
		self.ctxt['rendered_recs'] = rendered_recs
		self.ctxt['users'] = users
		self.ctxt['projects_children'] = projects_children
		self.ctxt['progress_reports'] = progress_reports
		
		self.ctxt['sortkey'] = sortkey
		self.ctxt['hideinactive'] = int(hideinactive)
		self.ctxt['reverse'] = int(reverse)
		
		
		
		
		
		
		
		
