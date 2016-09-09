# $Id: routing.py,v 1.56 2013/03/21 06:18:38 irees Exp $
import re
import sre_parse
import urllib
import cgi
import contextlib
import time
import functools
import urllib

from functools import partial
from itertools import izip

import twisted.web.resource

import emen2.util.registry
from emen2.db.exceptions import *
from emen2.web import responsecodes
from emen2.util import listops


def resolve(name=None, path=None):
    """Resolve a route using either a route name or path URI."""
    return _Router.resolve(name=name, path=path)


def execute(_execute_name, db=None, *args, **kwargs):
    """Find and execute a route by name.
    The route name (e.g. 'Home/main') must be the first positional argument.
    """
    view, method = _Router.resolve(name=_execute_name)
    view = view(db=db)
    view.init()
    method(view, *args, **kwargs)
    return view


def reverse(*args, **kwargs):
    return _Router.reverse(*args, **kwargs)


def add(*args, **kwargs):
    pass


def force_unicode(string):
    result = string
    if isinstance(result, unicode):
        return result
    elif hasattr(result, '__unicode__'):
        return unicode(result)
    else:
        return unicode(result, 'utf-8', errors='replace')



##### Routing Resource #####

class Router(twisted.web.resource.Resource):
    """Twisted Resource router.

    This is a Twisted Resource with a modified getChild method that will
    search for a View based on the request's path.
    """
    
    isLeaf = False

    # Find a resource or view
    def getChildWithDefault(self, path, request):
        d = request.notifyFinish()
        d.addCallback(self.logrequest, request, t=time.time())

        if path in self.children:
            return self.children[path]

        # Add a final slash.
        # Most of the view matchers expect this.
        path = request.path
        if not path:
            path = '/'
        if path[-1] != "/":
            path = "%s/"%path
        # request.path = path

        try:
            view, method = resolve(path=path)
        except:
            return self

        # This may move into routing.Router in the future.
        view = view()
        view.render = functools.partial(view.render, method=method)
        return view

    def logrequest(self, x, request, t=0.0, *args, **kwargs):
        ctxid = None
        headers = request.responseHeaders.getAllRawHeaders()
        tmp = {}
        for k, v in headers:
            k = k.lower()
            if k not in tmp and k in set(['x-username', 'content-length', 'x-resource']):
                tmp[k] = v

    # Resource was not found
    def render(self, request):
        return unicode(
            emen2.web.routing.execute(
                'Error/resp', 
                db=None,
                error=responsecodes.NotFoundError(request.uri), 
                location=request.uri)
            ).encode('utf-8')
        



class Route(object):
    """Private"""
    def __init__(self, name, matcher, cls=None, method=None, write=False):
        self.name = name
        if not hasattr(matcher, 'match'):
            matcher = re.compile(matcher)
        self.matcher = matcher
        self.cls = cls
        self.method = method

        # Hint that this route will cause writes
        self.write = write


    def match(self, path):
        result = None
        match = self.matcher.match(path)
        if match:
            # url unquote
            result = {}
            for k,v in match.groupdict().items():
                result[urllib.unquote_plus(k)] = urllib.unquote_plus(v)
        return result



@emen2.util.registry.Registry.setup
class _Router(emen2.util.registry.Registry):
    """Private"""

    _prepend = ''
    child_class = Route

    def __init__(self, prepend='', default=True):
        self._prepend = prepend or self._prepend
        self._default = default

    # Default route
    def get_default(self):
        return self._default

    def set_default(self, value):
        self._default = bool(value)

    default = property(get_default, set_default)


    # Not Found
    @staticmethod
    def onfail(inp):
        raise responsecodes.NotFoundError(inp)


    # Find a match for a path
    @classmethod
    def resolve(cls, path=None, name=None):
        """Resolve a route by either request path or route name.
        Returns (class, method) of the matching route.
        Keywords found in the match will be bound to the method.
        """

        if (not path and not name) or (path and name):
            raise ValueError, "You must specify either a path or a name"

        # Return a callback and found arguments
        result = None, None

        # Look at all the routes in the registry
        for route in cls.registry.values():
            # Return a result if found
            if path:
                tmp = route.match(path)
                if tmp != None:
                    f = partial(route.method, **tmp)
                    # Temporary hack: since we don't return the full Route instance,
                    # copy the write attribute to the partial
                    f.write = getattr(route, 'write', False)
                    return route.cls, f
            elif name:
                if name == route.name:
                    # Temporary hack; see above. We should return the actual Route instance.
                    f = route.method
                    f.write = getattr(route, 'write', False)
                    return route.cls, f
        
        # Try to find a public template.
        try:
            template = path[:-1]
            makot = emen2.db.config.templates.get_template(template)
            route = cls.registry.get('TemplateRender/main')
            f = partial(route.method, template=template)
            return route.cls, f
        except:
            pass
            
        # Raise a 404.
        raise responsecodes.NotFoundError(path or name)


    # Test resolve a route
    @classmethod
    def is_reachable(cls, route):
        cb, groups = cls.resolve(route)
        return cb != None and groups != None


    # Registration
    @classmethod
    def register(cls, route):
        '''Add a Route object to the registry.  If a Route with the same "name" is already
        registered, merge the two into the previously registered one.

        @returns true if a Route was already registered with the same name
        '''
        p = cls()
        route = emen2.util.registry.Registry.register(p, route)
        return route


    # Reverse lookup
    @classmethod
    def reverse(cls, *args, **kwargs):
        '''Take a route name and arguments, and return a Route'''
        root = emen2.db.config.get('web.root')
        result = '/error'
        anchor = kwargs.pop('anchor', '')
        if anchor:
            anchor = '#%s'%(anchor)

        name = args[0].split('/',1)
        if len(name) == 1:
            name.append('main')
        name = '/'.join(name)
        
        route = cls.get(name, None)
        if route:
            result = cls._reverse_helper(route.matcher, *args, **kwargs)
            result = str.join('', (cls._prepend, result))
            # temp hack
            if root not in result+anchor:
                return root+result+anchor

        return result+anchor


    @classmethod
    def _reverse_helper(cls, regex, *args, **kwargs):
        mc = MatchChecker(args, kwargs)
        result = re.sub(r'\(([^)]+)\)', mc, regex.pattern)
        qs = '&'.join( '%s=%s' % (urllib.quote_plus(k),urllib.quote_plus(v)) for k,v in mc.get_unused_kwargs().items() )
        result = [result.replace('^', '').replace('$', ''),qs]
        if qs == '':
            result.pop()
        
        return '?'.join(result)




################################
# Modified code from Django

class NoReverseMatch(Exception):
    pass


class MatchChecker(object):
    "Class used in reverse lookup."
    def __init__(self, args, kwargs):
        # Don't forget to quote the values.
        self.args = _IndexedListIterator( (urllib.quote_plus(x) for x in args) )
        self.kwargs = dict(  ( x, urllib.quote_plus(y) ) for x, y in kwargs.items()  )
        self.used_kwargs = set([])

    def get_arg(self, name):
        result = self.kwargs.get(name)
        if result is None:
            result = self.args.next()
        else:
            self.used_kwargs.add(name)
        return result

    def get_unused_kwargs(self):
        return dict( (k,v) for k,v in self.kwargs.iteritems() if k not in self.used_kwargs )

    NAMED_GROUP = re.compile(r'^\?P<(\w+)>(.*?)$', re.UNICODE)

    def __call__(self, match_obj):
        grouped = match_obj.group(1)
        m = self.NAMED_GROUP.search(grouped)

        if m:
            value, test_regex = self.get_arg(m.group(1)), m.group(2)
        else:
            value, test_regex = self.args.next(), grouped

        if value is None:
            raise NoReverseMatch('Not enough arguments passed in')

        if not re.match(test_regex + '$', value, re.UNICODE):
            raise NoReverseMatch("Value %r didn't match regular expression %r" % (value, test_regex))

        return force_unicode(value)


class _IndexedListIterator(object):
    def __init__(self, lis):
        self.lis = tuple(lis)

        # public
        self.pos = 0

    def next(self, delta = 1):
        try:
            result = self.lis[self.pos]
            self.pos += delta
            self.pos %= len(self.lis)
        except IndexError:
            result = None
        return result

    def prev(self, delta = 1):
        self.pos -= delta
        return self.lis[self.pos]

    def __getitem__(self, arg):
        return self.lis[arg]
        

__version__ = "$Revision: 1.56 $".split(":")[1][:-1].strip()
