from __future__ import with_statement
#import sys
import sys
import cgitb
from urllib import quote
from emen2 import Database
from emen2 import ts
from emen2.subsystems import routing, auth
try:
    set
except:
    from sets import Set as set
from twisted.internet import threads
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
import re
from emen2.util import listops
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

#import demjson

class PublicView(Resource):

    isLeaf = True
    router = routing.URLRegistry()
    
    def __init__(self):
        Resource.__init__(self)
    
    def __parse_args(self, args):
        """Break the request.args dict into something more usable
        
        This algorithm takes the list of keys and removes sensitive info, and other stuff that is
        passed in auto-magically and then groups all the params which end in _<number>
        together as a list.
        
        NOTE: we should probably make sure that the _## parameters have sequential numbers
        """
        result = {}
        def setitem(name, val):
            result[name] = val
        
        for key in set(args.keys()) - set(["db","host","user","ctxid", "username", "pw"]):
            name, _, val = key.rpartition('_')   
            if val.isdigit():
                res = result.get(name, [])
                res.append(args[key][0])
                if len(res) == 1: setitem(name, res)
            else:
                result[key] = args[key][0]
        return result
    
    @classmethod
    def __registerurl(cls, name, match, cb):
            '''register a callback to handle a urls 
            
            match is a compiled regex'''
            result = routing.URL(name, match, cb)
            cls.router.register(result)
            return result
    
    @classmethod
    def getredirect(cls, name):
        return cls.redirects.get(name, False)
    
    @classmethod
    def register_redirect(cls, fro, to, *args, **kwargs):
        cls.redirects[fro] = cls.router.reverselookup(to, *args, **kwargs)
    redirects = {}
    
    @classmethod
    def register_url(cls, name, match, prnt=True):
        """decorator function used to register a function to handle a specified URL
        
        
            arguments:
                name -- the name of the url to be registered
                regex -- the regular expression that applies 
                                 as a string
                cb -- the callback function to call
        """
        if prnt:
            g.debug.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
        def _reg_inside(cb):
            g.debug('%s ::matched by:: %s' % (name,match) )
            cls.__registerurl(name, re.compile(match), cb)
            return cb
        return _reg_inside
    
    @g.debug.debug_func
    def parse_uri(self, uri):
        url, _, qs = uri.partition('?')
        return [url, qs]
    
    def __authenticate(self, request, ctxid, host, args, router, target):
        authen = auth.Authenticator(db=ts.db, host=host)
        ##get request ctxid if any
        ctxid = request.getCookie("ctxid")
        ##get request username if any
        username = args.get('username', [''])[0]
        ##get request password if any
        pw = request.args.get('pw', [''])[0]
        ##do login,
        authen.authenticate(username, pw, ctxid)
        ctxid, un = authen.get_auth_info()
        if username and un != username:
            target = str.join('?', (router.reverselookup('Login'), 'msg=Invalid%%20Login&next=%s' % target))
        else:
            username = un
        if ctxid is not None:
            request.addCookie("ctxid", ctxid, path='/')
        return ctxid, target, authen


    def __getredirect(self, request, path):
        target = None
       
        if not bool(request.postpath):
            url, qs = self.parse_uri(request.uri)
            url = str.join('', (url, 'home/'))
            # get redirection of target if any
            url = self.redirects.get(url, url)
            target = (url, qs)
            target = '%s' % (str.join('?', target))
        
        redir = self.redirects.get(path, None)
        if redir != None:
            qs = self.parse_uri(request.uri)[1]
            if qs:
                qs = str.join('', ('?', qs))
            
            target = '/%s%s%s' % (str.join('/', request.prepath), redir, qs)
        
        return target
    
    def render(self, request):
        ctxid, host = None, request.getClientIP()
        args = request.args
        
        request.postpath = filter(bool, request.postpath)
        
        router=self.router
        make_callback = lambda string: (lambda *x, **y: string)
        try:
            # redirect special urls
            if self.parse_uri(request.uri)[0][-1] != '/': # special case, hairy to refactor
                target = addSlash(request)
                return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
            
            path = '/%s/' % str.join("/", request.postpath)
            target = self.__getredirect(request, path)
            
            # begin request handling
            method = listops.get(request.postpath, 0, '')
            callback, msg = make_callback(''), ''
            
            ctxid, target, authen = self.__authenticate(request, ctxid, host, args, router, target)
            
            # redirect must occur after authentication so the
            # ctxid cookie can be sent to the browser on a  
            # POST request
            if target is not None:
                #redirects must not be unicode
                #NOTE: should URLS use punycode: http://en.wikipedia.org/wiki/Punycode ?
                return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
            
            tmp = self.__parse_args(args)
            if method == "logout":
                authen.logout(ctxid)
                callback = make_callback(redirectTo('/db/home/', request))
            elif method == "login":
                callback = router.execute('/login/', uri=tmp.get('uri', '/db/home/'))
                callback = callback(db=ts.db, host=request.host, ctxid='', msg=tmp.get('msg', msg))
                return str(callback)
            else:
                callback = routing.URLRegistry().execute(path, **tmp)

            d = threads.deferToThread(callback, ctxid=ctxid, host=host)
            d.addCallback(self._cbsuccess, request, ctxid)
            d.addErrback(self._ebRender, request, ctxid)
    
            return server.NOT_DONE_YET
        
        except Exception, e:
            self._ebRender(e, request, ctxid)
    
    def _cbsuccess(self, result, request, ctxid):
        "result must be a 2-tuple: (result, mime-type)"
        def set_headers(headers):
            for key in headers:
                request.setHeader(key, headers[key])
       
 
        g.debug('RESULT:: %s' % (type(result)))
        try:
            result, mime_type = result
        except ValueError:
            mime_type = 'text/html; charset=utf-8'

        if mime_type.split('/')[0] == 'text':
            if type(result) != unicode:
                result = unicode(result)
            result = result.encode('utf-8')
        else:
            result = str(result)

        headers = {"content-type": mime_type,
                   "content-length": str(len(result)),
                   "Cache-Control":"no-cache",  
                   "Pragma":"no-cache"}

        set_headers(headers) 
        request.write(result)
        request.finish()
        
    def _ebRender(self, failure, request, ctxid):
        g.debug.msg(g.LOG_ERR, 'ERROR---------------------------')
        g.debug.msg(g.LOG_ERR, failure)
        g.debug.msg(g.LOG_ERR, '---------------------------------')
        request.setResponseCode(500)
        try:
            if isinstance(failure, Database.SecurityError) \
             or isinstance(failure, Database.SessionError) \
             or isinstance(failure, KeyError):
                uri = '/%s%s' % ( str.join('/', request.prepath), routing.URLRegistry.reverselookup(name='Login') )
                args = (('uri', quote('/%s/' % str.join('/', request.prepath + request.postpath))), 
                            ('msg', quote( str.join('<br />', [str(failure)]) ) ) 
                           )
                args = ( str.join('=', elem) for elem in args )
                args = str.join('&', args)
                uri = str.join('?', (uri,args))
                request.write(redirectTo(uri, request))
        except Exception:
            request.write(cgitb.html(sys.exc_info()))
        request.finish()
