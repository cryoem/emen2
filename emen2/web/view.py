import demjson
import functools

from emen2.util.listops import adj_dict
import emen2.web.publicresource
import emen2.util.db_manipulation
import emen2.util.utils
import emen2.util.filelib
import emen2.util.fileops

from emen2.subsystems import routing
from emen2.subsystems.view import *

import emen2.db.config
g = emen2.Database.config.g()


import emen2.web.templating


class _LaunchConsole(View):
	import thread
	__metaclass__ = view.View.register_view
	__matcher__ = '^/__launch_console/$'
	def __init__(self, db, **kwargs):
		emen2.web.view.View.__init__(self, db=db, **kwargs)
		self.set_context_item('title', 'blahb;ajb')
		if db.checkadmin():
			g.log.interact(globals())
			self.page = 'done'
		else:
			self.page = 'fail'


class _ReloadViews(View):
	import thread
	__metaclass__ = view.View.register_view
	__matcher__ = dict(main='^/__reload_views/$',
								one='^/__reload_views/(?P<name>\w+)',
								templ='^/(?P<templ>__reload_templates)')
	def __init__(self, db,  name=None, templ=None, **kwargs):
		emen2.web.view.View.__init__(self, db=db,**kwargs)
		self.set_context_item('title', 'Reloading Views...')
		if db.checkadmin():
			if templ is None:
				fails=reload_views(name)
			else:
				fails = []
				load_views(fails)
			self.page = 'done<br/><h1>Fails:</h1><br/>%s' % '<br/>'.join(fails)
		else:
			self.page = 'fail miserably!!!'



class TEST(View):
	__metaclass__ = emen2.web.view.View.register_view
	__matcher__ = '^/__db_test/$'
	def __init__(self, db, **kwargs):

		emen2.web.view.View.__init__(self, db=db, **kwargs)

		self.set_context_item('title', 'testing')


	def get_data(self):

		return 'some data'

	def __iter__(*args):

		result = emen2.web.view.View.__iter__(*args)

		return result

