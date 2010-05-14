from emen2.emen2config2 import *
from emen2.subsystems import routing, macro, templating
from emen2.util import listops
from emen2.util.utils import either
from emen2 import Database

from sets import Set
try:
    Set = set
except:
    pass

from paste.wsgiwrappers import WSGIRequest,WSGIResponse
from paste.cgitb_catcher import make_cgitb_middleware
from paste.httpexceptions import HTTPMovedPermanently, HTTPNotFound
from paste.urlmap import URLMap
from paste.urlparser import URLParser
from paste import lint

import re
# TODO: investigate the need for debug in g
import emen2.Database.globalns
g = emen2.Database.globalns.GlobalNamespace()

def load_views():
    g.templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
    g.TEMPLATEDIR="/Users/edwardlangley/emen2/web/templates"
    g.refresh()
    print "templates: %s" % repr(g.templates)
    templating.get_templates(g.TEMPLATEDIR)
    
def reload_views():
    reload(views)
    load_views()

class add_slash(object):
    def __init__(self, app, global_conf):
        self.__app = app
    def __call__(self, environ, start_response):
        path = environ['SCRIPT_NAME']+environ['PATH_INFO']
        if not path.endswith('/'):
            path = path + '/'
            qs = environ.get('QUERY_STRING', '')
            if qs is not '':
                path = path + '?' + qs
            status, headers, content = HTTPMovedPermanently(detail=path).response(environ).wsgi_response()
            start_response(status, headers)
        else:
            content = self.__app(environ, start_response)
        return content
    

class PublicView(object):
    ##################################################################
    # class methods and data
    redirects = {}
    
    @classmethod
    def __registerurl(cls, name, match, cb):
            '''register a pattern to select urls
    
            arguments:
                    name -- the name of the url to be registered
                    regex -- the regular expression that applies 
                                     as a string
                    cb -- the callback function to call
            '''
            return routing.URL(name, re.compile(match), cb)
    
    @classmethod
    def getredirect(cls, name):
        return cls.redirects.get(name, False)
    
    @classmethod
    def register_redirect(cls, fro, to, *args, **kwargs):
        g.log('REDIRECT: %s, %s' % (fro,to))
        cls.redirects[fro] = routing.URLRegistry.reverselookup(to, *args, **kwargs)
    
    @classmethod
    def register_url(cls, name, match):
            def _reg_inside(cb):
                g.log('%s ::matched by:: %s' % (name,match) )
                cls.__registerurl(name, re.compile(match), cb)
                return cb
            return _reg_inside
    ##################################################################
    # instance methods
    
    def __init__(self):
        self.ctxid = None
        self.db = None

    def authenticate(self, db, request, args):
        "authenticate a user return the auth cookie if different"
        self.ctxid = request.cookies.get('ctxid', '')
        
        if self.ctxid != '':
            user = self.db.checkcontext(self.ctxid, request.host)[0]
        else:
            user = ''
        username = args.get('username', user)
        
        if either(self.ctxid is '', user is not username):
            pw = args.get('pw', '')
            self.ctxid = self.db.login(username, pw, request.host)
            cookie = self.ctxid
        else:
            cookie = None
            
        listops.remove(args, 'pw')
        return cookie
        
    def __call__(self, environ, start_response):
        """Simple WSGI application"""
        request = WSGIRequest(environ)
        redirect = self.getredirect(request.path_info)
        if redirect is not False:
            result = HTTPMovedPermanently(detail=request.script_name+redirect).response(environ)
        else:
            args = listops.combine_dicts(request.GET.mixed(), request.POST.mixed())
            self.db = Database.Database(g.EMEN2DBPATH)
            try:
                auth_cookie = self.authenticate(self.db, request, args)
                
                callback = routing.URLRegistry(default=False).execute(request.path_info, **args)
                if callback is not None:
                    result = callback(db=self.db, ctxid=self.ctxid, host=request.host)
                    if not hasattr(result, '__iter__'):
                        result = result, 'text/html; charset=utf-8'
                    result = WSGIResponse(*result)
                else:
                    result = HTTPNotFound().response(environ)
                
                if auth_cookie is not None:
                    result.set_cookie('ctxid', auth_cookie)
            finally:
                self.db.close()
            
        status, headers, content = result.wsgi_response()
        start_response(status, headers)
        return content
                    
            
        
    
def app_factory(global_config, **local_config):
    """This function wraps our simple WSGI app so it
    can be used with paste.deploy"""
    load_views()
    g.macros = macro.MacroEngine()
    
    application = PublicView()
    middleware = [
                            (lint.make_middleware, (), {}),
                            (add_slash, (), {}),
                            (make_cgitb_middleware, (True,), {}),
                          ]
    for mware, args, kwargs in middleware:
        application = mware(application, global_config, *args, **kwargs)

    result = URLMap()
    result['/db'] = application
    result['/'] = URLParser(global_config, global_config.get('static-dir', './tweb'), 'test')
    
    return result

#necessary in order for imports to work correctly
from emen2.web.public import views
