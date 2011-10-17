# $Id$
import itertools

from emen2.web.view import View
import emen2.db.config



@View.register
class TemplateRender(View):
	'''Renders a template given its path.  To be usable, the template must set public to true in the global namespace.

		<%! ... %> defines code in the global namespace in a template
		variables:
			public = True # allow public access
			headers = {} # just in case you want headers
		template defs:
			<%def name='mimetype()'></%def>: set the mime type
	'''

	@View.add_matcher(r'^/tmpl/(?P<template>.+)/$', name='main')
	@View.add_matcher(r'^/tmpl-%s/(?P<template>.+)/$'%emen2.db.config.get('params.VERSION'), name='main/version')
	def main(self, template='/simple', **kwargs):
		makot = emen2.db.config.templates.get_template(template)

		self.set_context_item('inherit', False)
		if (self.db and self.db._getctx().checkadmin()) or getattr(makot.module, 'public', False):
			self.template = template
			self.headers = getattr(makot.module, 'headers', {})

		else:
			self.set_context_item('content', '<b>Error, Private Template</b>')

		# self.etag = '"%s"' % template.mtime







# import twisted.web.static
# 
# @View.register
# class Static(View):
# 	'''Static files'''
# 	
# 	@View.add_matcher(r'^/static/(?P<filename>.+)', name='main')
# 	@View.add_matcher(r'^/static-%s/(?P<filename>.+)'%emen2.db.config.get('params.VERSION'), name='main/version')		
# 	def main(self, filename):
# 		self.filename = emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')		 
# 		
# 	def render_cb(self, result, request, t=0):
# 		a = twisted.web.static.NoRangeStaticProducer(request, open(self.filename))
# 		a.start()
# 		
		

__version__ = "$Revision$".split(":")[1][:-1].strip()
