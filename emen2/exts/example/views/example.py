from emen2.web.view import View

@View.register
class ExampleView(View):

    @View.add_matcher(r'^/example/square/(?P<name>[^/]*)/$')
    def example_test(self, name):
        self.title = 'Example extension'
        self.template = '/example/example'
        name_square = int(name) ** 2
        self.ctxt['name'] = name
        self.ctxt['name_square'] = name_square
        
    @View.add_matcher(r'^/example/test/$')
    def example_test2(self):
        self.title = 'Example extension'
        self.template = '/example/example'
        self.ctxt['name'] = 123
        self.ctxt['name_square'] = 123**2
                