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

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

#twisted imports
###


class PublicView(Resource):
    isLeaf = True
    redirects = {}
    
    def __parse_args(self, args):
        dict_ = {}
        def setitem(name, val):
            dict_[name] = val
            
        for key in set(args.keys()) - set(["db","host","user","ctxid", "username", "pw"]):
            name, sep, val = key.rpartition('_')
            if val.isdigit():
                res = dict_.get(name, [])
                if res != []:
                    setitem(name, res)
                res.append(args[key][0])
            elif len(args[key]) > 1:
                dict_[key] = args[key]
            else:
                dict_[key] = args[key][0]
        return dict_
    
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
        cls.redirects[fro] = routing.URLRegistry.reverselookup(to, *args, **kwargs)
    
    @classmethod
    def register_url(cls, name, match, prnt=True):
            if prnt:
                g.debug.msg(g.LOG_INIT, 'REGISTERING: %r as %s' % (name, match))
            def _reg_inside(cb):
                g.debug('%s ::matched by:: %s' % (name,match) )
                cls.__registerurl(name, re.compile(match), cb)
                return cb
            return _reg_inside
    
    def parse_uri(self, uri):
        result = uri.split('?')
        url = uri[0]
        if len(result) > 1:
            qs = str.join('?', result[1:])
        else:
            qs = ''
        return [url, qs]
    
    def render(self, request):
        ctxid = None
        request.postpath = filter(bool, request.postpath)
        host = request.getClientIP()
        args = request.args
        def make_callback(string):
            cb = lambda *x, **y: string
            return cb
        try:
            # redirect special urls
            target = None
            if request.uri.split('?')[0][-1] != '/':
                target = addSlash(request)
                return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
            
            if not bool(request.postpath):
                target = self.parse_uri(request.uri)
                target[0] = str.join('', (target[0], 'home/'))
                # get redirection of target if any
                target[0] = self.redirects.get(target[0], target[0])
                while not target[-1]: 
                    g.debug('\t-> %s %r' % (target, target.pop())) 
                if len(target) > 1:
                    target = (target[0], str.join('?', target[1:]))
                target = '/%s%s' % (str.join('/',request.prepath), str.join('?', target))
            
            path = '/%s/' % str.join("/", request.postpath)
            redir = self.redirects.get(path, None)
            
            if redir != None:
                print redir != None, redir,
                qs = self.parse_uri(request.uri)[1]
                if qs: qs = str.join('', ('?', qs))
                target = '/%s%s%s' % (str.join('/',request.prepath), redir, qs)
            
            
            # begin request handling
            method = request.postpath[0]
            callback, msg = make_callback(''), ''
            
            #security ###################################################
            ##get ctxid
            ctxid = request.getCookie("ctxid")
            print 'COOKIE CTXID: %s' % ctxid
            ##set null username
            
            ## initialize Authenticator
            authen = auth.Authenticator(db=ts.db, host=host)
            
            
            print dir(request)
            ##get request username if any        
            username = args.get('username', [''])[0]
            print 'USERNAME: %s' % username
            ##get request password if any
            pw = request.args.get('pw', [''])[0]
            
            authen.authenticate(username, pw, ctxid)
                
            ctxid, username  = authen.get_auth_info()
            if ctxid is not None:
                request.addCookie("ctxid", ctxid, path='/')
            
            # redirect must occur after authentication so the
            # ctxid cookie can be sent to the browser
            if target is not None:
                #redirects must not be unicode
                return redirectTo(target.encode('ascii', 'xmlcharrefreplace'), request)
            
            tmp = self.__parse_args(args)
            print tmp
            if method == "logout":
                authen.logout(ctxid)
                callback = make_callback(redirectTo('/db/home/', request))
            elif method == "login":
                callback = routing.URLRegistry().execute('/login/', 
                                                                           uri=tmp.get('uri', '/db/home/'))
                callback = callback(db=ts.db, host=request.host, ctxid='', 
                                             msg=tmp.get('msg', msg))
                return str(callback)
            else:
                callback = routing.URLRegistry().execute(path, **tmp)
            #end security ################################################

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
