from __future__ import with_statement
#import sys
from cgi import escape
from emen2 import Database
from emen2 import ts
from emen2.subsystems import routing
from sets import Set
from twisted.internet import threads
from twisted.web import error
from twisted.web.resource import Resource
from twisted.web.static import server, redirectTo, addSlash
import re
# TODO: investigate the need for debug in g
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

from mako.exceptions import RichTraceback

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
    def register_url(cls, name, match):
            def _reg_inside(cb):
                g.debug('%s ::matched by:: %s' % (name,match) )
                cls.__registerurl(name, re.compile(match), cb)
                return cb
            return _reg_inside
    
    def login(self,uri,msg=""):
            page = """
            <h2>Please login:</h2>
            <h3>%s</h3>
            <div id="zone_login">
    
                <form action="%s" method="POST">
                   <div>
                        <div>Username:</div>
                        <div><input type="text" name="username" /></div>
                    </div>
                    <div>
                        <div>Password:</div>
                        <div><input type="password" name="pw" /></div>
                    </div>
                    <input type="submit" value="submit" />
    
                </form>
            </div>"""%(msg,uri)
            return page, 'text/html'                
    
    def render(self, request):
        print request.args
        
        try:
            if request.uri.split('?')[0][-1] != '/':
                return redirectTo(addSlash(request), request)

            request.postpath = filter(bool, request.postpath)
            if not bool(request.postpath):
                return redirectTo(request.uri+'home/', request)
            
            def make_callback(string):
                cb = lambda *x, **y: string
                return cb
            
            
            
            host = request.getClientIP()
            args = request.args
            
            
            method = request.postpath[0]
            ctxid = request.getCookie("ctxid")
            loginmsg = ""
            callback = make_callback('')
            
            try:
                ts.db.checkcontext(ctxid)
            except Exception, e:
                if ctxid != None:    
                    msg = "Session expired"
                    ctxid = None
                else:
                    g.debug.msg(g.LOG_ERR, "EXCEPTION <%s>" % repr(e) )
            
            msg = None
            if ctxid == None:
                # force login, or generate anonymous context
                if request.args.has_key("username") and request.args.has_key("pw"):
                    try:
                        # login and continue with this ctxid
                        ctxid = ts.db.login(request.args["username"][0], request.args["pw"][0], host)
                        request.addCookie("ctxid", ctxid, path='/')
                        msg=1
                    except:
                        # bad login
                        ctxid = None
                        method = "login"
                        msg = "Please try again."
                else:
                    ctxid = ts.db.login("","",host)
                        
            if method == "login":
                try:            
                    print 'hello'
                    print 'continuing %r, %s' % (callback,callback)
                    callback = routing.URLRegistry().execute('/login/', msg=msg, uri='/db/home/')(db=ts.db, host=request.host, ctxid='')
                    print 'bye\n%r\n%s' % (callback,callback)
                except Exception, e:
                    callback = str(e)
                return str(callback)
            
            elif method == "logout":
                ts.db.deletecontext(ctxid)
                callback = make_callback("""<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                                                            <meta http-equiv="REFRESH" content="0; URL=/db/home?notify=4">""")
            else:
                tmp = self.__parse_args(args)
                
                path = '/%s/' % str.join("/", request.postpath)
                g.debug(path)
                path = self.redirects.get(path, path)
                callback = routing.URLRegistry().execute(path, **tmp)
                                                        
            d = threads.deferToThread(callback, ctxid=ctxid, host=host)
            d.addCallback(self._cbsuccess, request, ctxid)
            d.addErrback(self._ebRender, request, ctxid)
    
            return server.NOT_DONE_YET
        except Exception, e:
            error.ErrorPage(e, str(e), str(e)).render(request)
    
    def _cbsuccess(self, result, request, ctxid):
        "result must be a 2-tuple: (result, mime-type)"
        
        g.debug('RESULT:: %s' % (type(result)))
        
        def set_headers(headers):
            for key in headers:
                request.setHeader(key, headers[key])
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
        g.debug.msg(g.LOG_ERR, failure)
        if isinstance(failure.value, Database.SecurityError):
            if ctxid == None:
                page = self.login(uri=request.uri,msg="Unable to access resource; please login.")
            else:
                page = self.login(uri=request.uri, msg="Insufficient permissions to access resource.")
        elif isinstance(failure.value, Database.SessionError):
            page = self.login(uri=request.uri, msg="Session expired.")
        else:
            page = ('<pre>'  + escape(str(failure)) + '</pre>',)

        request.write(page[0])
        request.finish()
