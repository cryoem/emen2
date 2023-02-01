# $Id: resource.py,v 1.48 2012/10/03 07:30:34 irees Exp $

import re
import time
import cgi
import traceback
import collections
import functools
import Queue
import itertools

import twisted.internet
import twisted.web.static
import twisted.web.resource
import twisted.python.failure

import jsonrpc.jsonutil
import jsonrpc.server

import mako.exceptions

# emen2 imports
import emen2.db.config
import emen2.db.log
import emen2.db.exceptions
import emen2.db.handlers
import emen2.util.listops
import emen2.web.events
import emen2.web.routing
import emen2.web.responsecodes
import emen2.web.server

##### Base EMEN2 Resource #####

# Special thanks to this Dave Peticolas's blog post for
# helping sort out my deferred cancel/callback/errback situation:
# http://krondo.com/?p=2601

class RoutedResource(object):
    #### Routing registration methods #####
    routing = emen2.web.routing
    isLeaf = True

    def render(self, request):
        return "No content"

    @classmethod
    def add_matcher(cls, *matchers, **kwargs):
        '''Decorator used to add a matcher to an already existing class

        Named groups in matcher get passed as keyword arguments
        Other groups in matcher get passed as positional arguments
        Nothing else gets passed

        write=True will hint to the database that writes will occur.
        This may do things like disable snapshot transactions.
        '''
        if not matchers:
            raise ValueError, 'A view must have at least one matcher'

        # Default name (this is usually the method name)
        def check_name(name):
            return 'main' if name.lower() == 'init' else name

        # Inner decorator method
        def inner(func):
            name = kwargs.pop('name', check_name(func.__name__))
            view = kwargs.pop('view', None)
            write = kwargs.pop('write', False)
            matcherinfo = getattr(func, 'matcherinfo', [])
            for count, m in enumerate(matchers):
                if count>0:
                    name='%s/%s'%(name, count)
                matcherinfo.append((m, name, view, write))

            # save all matchers to the function
            func.matcherinfo = matcherinfo
            return func

        return inner

    @classmethod
    def register(self, cls):
        '''Register a View and connect it to a URL.
        - Multiple regular expressions can be registered per sub view
        - This also registers urls defined by the add_matcher decorator. In this case, the sub view name will default to the method name.
        - These can be reversed with self.ctxt.reverse('ClassName/alt1', param1='asd') and such
        '''
        # Register mtchers produced by the add_matcher decorator
        for func in cls.__dict__.values():
            if not callable(func): continue

            for matcher in getattr(func, 'matcherinfo', []):
                matcher, name, view, write = matcher
                view = view or cls.__name__
                name = '%s/%s'%(view, name)
                # These will be set as attributes on the Route instance
                with emen2.web.routing._Router().route(name=name, matcher=matcher, cls=cls, method=func, write=write) as url:
                    pass

        return cls

    slots = collections.defaultdict(list)
    @classmethod
    def provides(cls, slot):
        '''Decorate a method to indicate that the method provides a certain functionality'''
        def _inner(view):
            cls.slots[slot].append(functools.partial(cls, init=view))
            return view
        return _inner

    @classmethod
    def require(cls, slot):
        '''Use to get a view with a desired functionality'''
        if slot in cls.slots:
            return cls.slots[slot][-1]
        else: raise ValueError, "No such slot"


class FixedArgsResource(object):
    
    def render(self, request):
        return "No content."
    
    ##### Process request arguments #####

    def parse_args(self, request):
        # Massage the post and querystring arguments
        # ... PUT requests, and twistd's handling of POST is broken
        args = self._parse_content(request)

        # Twisted provides all args as lists.
        # If we only got one value, pop it
        for k, v in args.items():
            if len(v) == 1:
                v = v[0]
            args[k] = v

        # Unicode.. grumble.. Web forms will submit UTF-8 encoded data; decode that
        args = self._parse_coerce_unicode(args)

        # HTTP arguments with '.' will be turned into dicts, e.g. 'child.key' -> child['key']
        args = self._parse_args_dict(args)

        # Redirect...?
        self._redirect = args.pop('_redirect', None)

        return args

    def _parse_content(self, request):
        # Fixes file uploads.
        files = []
        args = request.args

        if request.method == "PUT":
            # The param?..
            f = emen2.db.handlers.BinaryHandler.get_handler(
                filename=request.getHeader('x-file-name'),
                param=request.getHeader('x-file-param'),
                fileobj=request.content
                )
            files.append(f)

        elif request.method == "POST":
            # Fix Twisted's broken handling of multipart/form-data file uploads
            headers = request.getAllHeaders()
            img = cgi.FieldStorage(
                fp = request.content,
                headers = headers,
                keep_blank_values = True,
                environ = {
                    'REQUEST_METHOD':'POST',
                    'CONTENT_TYPE': headers.get('content-type'),
                }
            )

            # Rebuild the request args.
            # args = {}
            for param in img:
                # img.getlist() only returns the values.
                newvalues = []
                values = img[param]
                # grumble.. hasattr(__iter__) doesn't work.
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if getattr(value, 'filename', None):
                        f = emen2.db.handlers.BinaryHandler.get_handler(
                            param=param,
                            filename=value.filename,
                            fileobj=value.file or value.value
                            )
                        files.append(f)
                    else:
                        newvalues.append(value.value)
                args[param] = newvalues

        # Fix Unicode filename... Arrrgghghh..
        for f in files:
            f.filename = f.filename.decode('utf-8')

        # Make available to Views...
        self.request_files = files
        return args

    def _parse_args_dict(self, args):
        # Break keys with '.' into child dictionaries, recursively.
        # {'root': 1, 'child.key2': 2, 'child.key1.subkey1': 3, 'child.key1.subkey2':4}
        # ->
        # {'root': 1, 'child': {'key2': 2, key1: {'subkey1': 3, 'subkey2': 4}}}
        test = {}
        newargs = {}
        # Sort by key length so child dictionaries are created in order
        for k,v in sorted(args.items(), key=lambda x:len(x[0])):
            if '.' in k:
                cur = newargs
                s = k.split('.')
                for path in s[:-1]:
                    if not cur.get(path):
                        # Create child dict
                        cur[path] = {}
                    # Step down one level
                    cur = cur[path]
                    parent = path

                # Set the value for the leaf
                cur[s[-1]] = v
            elif ':' in k:
                i, _, j = k.partition(':')
                if not test.get(i):
                    test[i] = {}
                test[i][j] = v

            else:
                newargs[k] = v

        # Transform :-keyed items back into dict
        for k,v in test.items():
            v2 = zip(v.get('keys', []), v.get('values', []))
            newargs[k] = dict(v2)

        return newargs

    def _parse_coerce_unicode(self, args, keyname=''):
        # This is terribly hacky, to deal with various Unicode issues
        # To disable this for a class, override and return {}
        if isinstance(args, unicode):
            return args

        elif keyname == 'filedata':
            # Ignore
            return args

        elif hasattr(args, 'items'):
            newargs = {}
            for k, v in args.items():
                newargs[k] = self._parse_coerce_unicode(v, keyname=k)
            return newargs

        elif hasattr(args, '__iter__'):
            return [unicode(i, 'utf-8') for i in args]

        return unicode(args, 'utf-8')



class EMEN2Resource(RoutedResource, FixedArgsResource):
    """Base resource for EMEN2. 
    
    Handles proper parsing of HTTP request arguments
    into a format that plays well with EMEN2, and contains all the common features
    of setting up the deferreds, threadpool, handling errors, etc.
    """

    def __init__(self):
        # Response headers
        self.headers = {}

        # HTTP Method
        self.request_method = None # request_method

        # Request headers
        self.request_headers = {}

        # Request host
        self.request_host = None
        
        # Request location
        self.request_location = ''
        
        # Redirect...
        self._redirect = None
        
        # Any uploaded files
        self.request_files = []

        # HTTP ETags (cache control)
        self.etag = None

    def __unicode__(self):
        '''Render the resource into a string that can be sent to the client'''
        return unicode(self.get_data())

    def __str__(self):
        '''Render the resource, encoded as UTF-8'''
        return self.get_data().encode('utf-8', 'replace')


    ##### Headers #####
    
    def _normalize_header_name(self, name):
        return '-'.join(x.capitalize() for x in name.split('-'))

    def set_header(self, name, value):
        '''Set a single header'''
        name = self._normalize_header_name(name)
        self.headers[name] = value

    def _set_ctxid(self, request, ctxid):
        request.addCookie("ctxid", ctxid, path='/')

    ##### Resource interface #####

    def get_json(self):
        return None

    def get_data(self):
        return ""
        
    def render(self, request, method=None):
        # The default is to run a supplied method
        # wrapped in a DB transaction from the DBPool.
        method = method or (lambda x:None)

        # Update request details
        self.request_method = request.method.lower()
        self.request_headers = request.getAllHeaders()
        self.request_location = request.path
        self.request_host = request.getClientIP()
        
        # Parse and filter the request arguments
        args = self.parse_args(request)

        # Authentication token -- if supplied as an argument, send it back as a cookie.
        ctxid = args.pop('ctxid', None)
        if ctxid:
            self._set_ctxid(request, str(ctxid))
        ctxid = ctxid or request.getCookie("ctxid")

        # _render will setup the deferred response
        return self._render(request, method, ctxid=ctxid, host=self.request_host, args=args)

    def _render(self, request, method, ctxid=None, host=None, args=None):
        # Setup deferred rendering using a DB transaction.
        t = time.time()

        # Use the EMEN2 DB thread pool.
        deferred = emen2.web.server.pool.rundb(
            self._render_db,
            method,
            ctxid = ctxid,
            host = host,
            args = args)

        # Callbacks
        deferred.addCallback(self.render_cb, request, t=t)
        deferred.addErrback(self.render_eb, request, t=t)
        request.notifyFinish().addErrback(self._request_broken, request, deferred)
        return twisted.web.static.server.NOT_DONE_YET

    def _render_db(self, method, db=None, ctxid=None, host=None, args=None):
        # Render method
        self.db = db

        # Result
        result = None
        
        # Hack to log username and ctxid
        self._log_username = None
        self._log_ctxid = ctxid

        # The DBProxy context manager will open a transaction, and abort
        # on an uncaught exception.
        write = getattr(method, "write", False)
        with self.db._newtxn(write=write):
            # Bind the ctxid/host to the DBProxy
            self.db._setContext(ctxid, host)
            self._log_username = self.db._ctx.username
            
            # Any View init method is run inside the transaction
            self.init()
            result = method(self, **args)
 
             # If the method returns a value, it uses that as the value
            # otherwise, calls str() on the View.
            if result is None:
                result = str(self)

        self.db = None

        return result


    ##### Callbacks #####

    def render_cb(self, result, request, t=0, **_):
        # Render callback -- setup basic headers

        # This is a hack to log the ctxid and username
        request._log_username = self._log_username
        request._log_ctxid = self._log_ctxid
        
        # Filter the headers.
        headers = {}
        headers.update(self.headers)
        headers = dict( (k,v) for k,v in headers.iteritems() if v != None )

        # Redirect if necessary
        if self._redirect:
            headers['Location'] = self._redirect
        if headers.get('Location'):
            request.setResponseCode(303)

        # If X-Ctxid (auth token) was supplied as a header,
        # set the client's cookie. This is is used by login, logout
        # and opening a web browser from desktop clients with ?ctxid as
        # a querystring argument.
        setctxid = headers.pop('X-Ctxid', None)
        if setctxid != None:
            self._set_ctxid(request, setctxid)

        # Set the remaining headers
        [request.setHeader(key, str(headers[key])) for key in headers]

        # Send result to client
        self.render_result(result, request)

    def render_result(self, result, request):
        """Write the result to the client and close the request."""
        # if result is not None:
        length = len(result)
        request.setHeader("Content-Length", length)
        request.write(result)
        
        # Close the request and write to log
        request.finish()

    def render_eb(self, failure, request, t=0, **_):
        # This method accepts either a regular Exception or Twisted Failure
        print failure
        e, data = '', ''
        headers = {}

        # Raise the exception
        try:
            if isinstance(failure, twisted.python.failure.Failure):
                failure.raiseException()
            else:
                raise failure

        # Closed connection error. Nothing to write, and no connection to close.
        except (twisted.internet.defer.CancelledError), e:
            return

        # Expired or invalid session. Remove ctxid and redirect to root.
        except emen2.db.exceptions.SessionError, e:
            data = self.render_error_security(request.uri, e)
            request.addCookie('ctxid', '', path='/')
            emen2.db.log.security(e)

        # Authentication exceptions
        except emen2.db.exceptions.SecurityError, e:
            data = self.render_error_security(request.uri, e)
            emen2.db.log.security(e)

        # HTTP errors
        except emen2.web.responsecodes.HTTPResponseCode, e:
            data = self.render_error_response(request.uri, e)
            emen2.db.log.error(e)

        # General error
        except BaseException, e:
            data = self.render_error(request.uri, e)
            emen2.db.log.error(e)

        # Write the response
        headers.update(getattr(e, 'headers', {}))
        request.setResponseCode(getattr(e, 'code', 500))
        [request.setHeader(k, v) for k,v in headers.items()]
        request.write(data)

        request.finish()


    ##### Error handlers #####

    # ian: todo: Use a config value to choose which error pages (mako, or emen2) to use.
    # ed: Couldn't that be based on the DEBUG flag?
    def render_error(self, location, e):
        # return unicode(emen2.web.routing.execute('Error/main', db=None, error=e, location=location)).encode('utf-8')
        return mako.exceptions.html_error_template().render()

    def render_error_security(self, location, e):
        return unicode(emen2.web.routing.execute('Error/auth', db=None, error=e, location=location)).encode('utf-8')
        # return mako.exceptions.html_error_template().render()

    def render_error_response(self, location, e):
        return unicode(emen2.web.routing.execute('Error/resp', db=None, error=e, location=location)).encode('utf-8')
        # return mako.exceptions.html_error_template().render()

    def _request_broken(self, failure, request, deferred):
        # Cancel the deferred.
        # The errback will be called, but not the callback.
        deferred.cancel()

    def _request_canceller(self, deferred, *args, **kwargs):
        # Do nothing -- my deferreds don't support cancellation at the moment
        pass
        # Create a failure to pass to the errback
        # failure = twisted.python.failure.Failure(exc_value=Exception("Cancelled request"))
        # deferred.errback(failure)








##### XML-RPC and JSON-RPC Resources #####

class XMLRPCResource(object):
    pass


class JSONRPCServerEvents(jsonrpc.server.ServerEvents):
    q = Queue.Queue()

    def processcontent(self, content, request):
        # Get the host from request
        # Get the ctxid from the post or querystring arguments
        ctxid, host = request.getCookie('ctxid'), request.getClientIP()
        ctxid = content.get('ctxid', ctxid)
        if 'params' in content:
            params = content['params']
            if hasattr(params, 'get'):
                ctxid = params.pop('ctxid', ctxid)
        self.ctxid = ctxid
        self.host = request.getClientIP()
        return content

    def callmethod(self, request, rpcrequest, db=None, ctxid=None, **kw):
        # Lookup the method and call
        if not db:
            raise Exception, "No DBProxy"

        # Hack to log username and ctxid
        request._log_username = None
        request._log_ctxid = self.ctxid

        methodresult = None
        if rpcrequest.method.startswith('_'):
            raise emen2.web.responsecodes.ForbiddenError, 'Method not accessible'

        elif rpcrequest.method in db._publicmethods:
            # Start the DB with a write transaction
            # db._starttxn(write=db._checkwrite(rpcrequest.method))
            with db:
                db._setContext(self.ctxid, self.host)
                request._log_username = db._ctx.username
                
                _method = rpcrequest.method.rpartition('.')[2]
                if _method == 'login':
                    rpcrequest.kwargs['host'] = self.host

                methodresult = db._callmethod(rpcrequest.method, rpcrequest.args, rpcrequest.kwargs)
                
                if _method in set(['login', 'logout']):
                    request.addCookie('ctxid', methodresult or '')

        else:
            if rpcrequest.method == 'queue_put':
                methodresult = self.q.put((rpcrequest.args, rpcrequest.kwargs))
            elif rpcrequest.method == 'queue_get':
                methodresult = self.q.get()
            else:
                # Call an event, these can be added and removed through the event registry in emen2.web.events
                #   Useful for setting up views to deliver results/notifications via JSON-RPC
                #     This should work for COMET-style long-polling, but that results in server hangs on exit :)
                e = emen2.web.events.EventRegistry().event('pub.%s'%rpcrequest.method)
                methodresult = e(self.ctxid, request.getClientIP(), db=db, *rpcrequest.args, **rpcrequest.kwargs)
        return methodresult

    def defer(self, method, *a, **kw):
        deferred = emen2.web.server.pool.rundb(method, *a, **kw)
        return deferred

    def log(self, response, txrequest, error=False):
        if error:
            traceback.print_exc()
        else:
            pass





__version__ = "$Revision: 1.48 $".split(":")[1][:-1].strip()
