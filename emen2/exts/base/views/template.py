# $Id$
import itertools
from emen2.web import templating
from emen2.web import view
import emen2.db.config
g = emen2.db.config.g()



@view.View.register
class TemplateRender(view.View):
	'''Renders a template given its path.  To be usable, the template must set public to true in the global namespace.

		<%! ... %> defines code in the global namespace in a template
		variables:
			public = True # allow public access
			headers = {} # just in case you want headers
		template defs:
			<%def name='mimetype()'></%def>: set the mime type
	'''

	@view.View.add_matcher(r'^/tmpl-%s/$'%emen2.VERSION, r'^/tmpl/$') #(?P<data>.+)/$')
	def init(self, t='', **kwargs):
		template = g.templates.templates.templates[t]
		makot = template.template
		self.set_context_item('inherit', False)
		if (self.db and self.db._getctx().checkadmin()) or getattr(makot.module, 'public', False):
			try: mimetype = makot.get_def('mimetype').render().strip()
			except AttributeError: mimetype = None

			self.template = t
			if mimetype is not None:
				self.mimetype = mimetype

			self.headers = getattr(makot.module, 'headers', {})

		else:
			self.set_context_item('content', '<b>Error, Private Template</b>')
		self.etag = '"%s"' % template.mtime


#@view.AdminView.register
#class Templates(view.AdminView):
#	@view.AdminView.add_matcher('^/templates/$')
#	def main(self):
#		self.make_raw()
#		self.mimetype = 'text/plain'
#		templates = g.templates.templates.templates.templates.items()
#		self.page = '\n'.join(itertools.chain(
#			('MTIME\tID\tFILEPATH',),
#			('%s\t%s\t%s' % (v.mtime, k, v.path) for k,v in sorted(templates))
#		))
__version__ = "$Revision$".split(":")[1][:-1].strip()
