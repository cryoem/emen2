# $Id$
import itertools
#from emen2.web import templating
from emen2.web.view import View
import emen2.db.config
g = emen2.db.config.g()

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

	@View.add_matcher(r'^/tmpl/(?P<template>.+)/', name='main')
	@View.add_matcher(r'^/tmpl-%s/(?P<template>.+)/'%emen2.db.config.CVars.version, name='main/version')
	def init(self, template='/simple', **kwargs):
		makot = g.templates.get_template(template)

		self.set_context_item('inherit', False)
		if (self.db and self.db._getctx().checkadmin()) or getattr(makot.module, 'public', False):
			try:
				mimetype = makot.get_def('mimetype').render().strip()
			except AttributeError:
				mimetype = None

			self.template = template
			if mimetype is not None:
				self.mimetype = mimetype

			self.headers = getattr(makot.module, 'headers', {})

		else:
			self.set_context_item('content', '<b>Error, Private Template</b>')

		# self.etag = '"%s"' % template.mtime


__version__ = "$Revision$".split(":")[1][:-1].strip()
