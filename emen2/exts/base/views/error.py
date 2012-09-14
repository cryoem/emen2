# $Id$
from emen2.web.view import View

@View.register
class Error(View):

    @View.add_matcher('/error/')
    @View.provides('error_handler')
    def main(self, error='', location='/', **kwargs):
        self.template = '/errors/error'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location

    @View.add_matcher('/error/auth')
    def auth(self, error='', location='/', **kwargs):
        self.template = '/errors/auth'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location

    @View.add_matcher('/error/resp')
    def resp(self, error='', location='/', **kwargs):
        self.template = '/errors/resp'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location


        
__version__ = "$Revision$".split(":")[1][:-1].strip()
