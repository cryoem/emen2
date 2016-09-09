# $Id: reverse.py,v 1.6 2012/07/28 06:31:18 irees Exp $
import collections
import jsonrpc.jsonutil

from emen2.web.view import View

# for python >= 2.6
@View.register
class ReverseURI(View):
    # for python < 2.6 do this:

    __matcher__ = dict(
        main=r'^/url/(?P<name>\w+)/$',
        execute=r'^/url/(?P<name>\w+)/(?P<exe>execute)/$',
        alt=r'^/url/$'
    )

    def main(self, arg='', name=None, arguments='', kwargs='', exe=False):
        self.make_raw()
        self.set_header('content-type', 'application/json')

        if name is None and isinstance(arg, (str, unicode)):
            arg = jsonrpc.jsonutil.decode(arg)
        elif name is not None:
            if isinstance(arguments, (str, unicode)):
                arguments = jsonrpc.jsonutil.decode(arguments)
            if isinstance(kwargs, (str, unicode)):
                kwargs = jsonrpc.jsonutil.decode(kwargs)
            arg = [name, arguments, kwargs]

        if exe:
            self.execute_url(name, arguments, kwargs)
        else: self.get_url(arg)

    def get_url(self, arg):
        ret_list = True
        if arg and isinstance(arg[0], (str, unicode) ): arg, ret_list = [arg], False

        arg = [ (name, args, dict( (k.encode('utf-8'),v) for k,v in kwargs.iteritems() ))
                    for name, args, kwargs in arg]

        arg = [(name, self.ctxt.reverse(name, *args, **kwargs)) for name, args, kwargs in arg]

        if ret_list is False:
            if arg: arg = arg[0][1]
            else: arg = ''
        else:
            tmp = collections.defaultdict(list)
            for key, value in arg: tmp[key].append(value)
            arg = tmp

        self.page = jsonrpc.jsonutil.encode(arg)

    def execute_url(self, name, arguments, kwargs):
        kwargs = dict( (k.encode('utf-8'), v) for k,v in kwargs.iteritems() )
        self.page = self.ctxt.render_template_view(name, *arguments, **kwargs)
        
__version__ = "$Revision: 1.6 $".split(":")[1][:-1].strip()
