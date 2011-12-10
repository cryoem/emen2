# $Id$
import datetime
from operator import itemgetter
import time

import emen2.db.exceptions
import emen2.db.config
from emen2.web.view import View


@View.register
class EMHome(View):

	@View.add_matcher(r'^/$', view='Root', name='main')
	@View.add_matcher(r'^/em/home/$')
	def main(self):
		self.title = 'Home'
		self.template = '/em/home'
		
		# Get the banner/welcome message
		bookmarks = emen2.db.config.get('bookmarks.BOOKMARKS', {})
		banner = emen2.db.config.get('customization.EMEN2LOGO')

		try:
			banner = self.db.getrecord(banner)
			render_banner = self.db.renderview(banner, viewname="banner")
		except Exception, inst:
			banner = None
			render_banner = ""

		self.ctxt['projects_map'] = self.routing.execute(
			'Map/embed', 
			db=self.db, 
			root=0, 
			mode='children', 
			recurse=2, 
			rectype=['group', 'project']
			)

		# Recent records
		# Add 'Z" to datetime.isoformat()
		now = datetime.datetime.utcnow().isoformat()+'Z'
		t = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat()+'Z'
		self.ctxt['recent_activity'] = self.db.plot([['creationtime', '>', t]], x={'key':'creationtime', 'bin':'hour', 'min':t, 'max':now})
		
		# List of RecordDefs to show
		rds = self.db.getchildren('project', keytype='recorddef')
		rds.add('project')
		rds -= set(['subproject', 'p41_project'])
		self.ctxt['recorddefs'] = self.db.getrecorddef(rds)

		# recnames = {}
		# equipment = self.db.getchildren(0, rectype=['microscope'])
		# r = self.db.renderview(equipment)
		# recnames.update(r)
		# self.ctxt['equipment'] = equipment
		# self.ctxt['banner'] = banner
		# self.ctxt['render_banner'] = render_banner
		# self.ctxt['recnames'] = recnames	