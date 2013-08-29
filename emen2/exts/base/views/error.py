from emen2.web.view import View

@View.register
class Error(View):

    @View.add_matcher('/error/')
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
    def expired(self, error='', location='/', **kwargs):
        self.template = '/errors/expired'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location
        self.ctxt['name'] = kwargs.get('name')

    @View.add_matcher('/error/resp')
    def resp(self, error='', location='/', **kwargs):
        self.template = '/errors/resp'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location

    @View.add_matcher('/error/test')
    def test(self, error='', location='/', **kwargs):
        self.template = '/errors/resp'
        self.title = 'Error'
        self.ctxt["error"] = error
        self.ctxt['location'] = location

        
