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
		
		if not self.ctxt['USER']:
			raise emen2.db.exceptions.SecurityError, "Please login."
		
		# Get the banner/welcome message
		bookmarks = emen2.db.config.get('bookmarks.BOOKMARKS', {})
		banner = emen2.db.config.get('customization.EMEN2LOGO')
		try:
			banner = self.db.getrecord(banner)
			render_banner = self.db.renderview(banner, viewname="banner")
		except Exception, inst:
			banner = None
			render_banner = ""

		# Project types
		project_rds = ['project', 'workshop', 'project_software']
		self.ctxt['project_rds'] = self.db.getrecorddef(project_rds)
		self.ctxt['projects_map'] = self.routing.execute(
			'Map/embed', 
			db=self.db, 
			root=0, 
			mode='children', 
			recurse=2, 
			rectype=project_rds
			)

		# Equipment types
		equipment_rds = ['camera', 'microscope', 'scanner', 'vitrification_device']
		self.ctxt['equipment'] = self.db.getrecord(self.db.getchildren(0, rectype='equipment'))
		self.ctxt['equipment_rds'] = self.db.getrecorddef(equipment_rds)

		# Recent records
		# Add 'Z" to datetime.isoformat()
		# t = '2011-01-01T00:00:00+00:00'
		# now = '2011-02-01T00:00:00+00:00'
		now = datetime.datetime.utcnow().isoformat()+'+00:00'
		t = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat()+'+00:00'
		q = self.db.plot(
			[['creationtime', '>', t], ['rectype', 'any', '']], 
			x={'key':'creationtime', 'bin':'day', 'min':t, 'max':now}, 
			y={'stacked':True}
			)

		self.ctxt['recent_activity'] = q
		
