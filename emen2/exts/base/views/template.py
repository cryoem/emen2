# $Id: template.py,v 1.16 2012/12/14 05:24:29 irees Exp $
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
    @View.add_matcher(r'^/tmpl-%s/(?P<template>.+)/$'%emen2.__version__, name='main/version')
    def main(self, template='/simple', **kwargs):
        makot = emen2.db.config.templates.get_template(template)

        self.ctxt['inherit'] = False
        if (self.db and self.db._getctx().checkadmin()) or getattr(makot.module, 'public', False):
            self.template = template
            self.headers = getattr(makot.module, 'headers', {})
        else:
            self.ctxt['content'] = '<b>Error, private template</b>'



        

__version__ = "$Revision: 1.16 $".split(":")[1][:-1].strip()
