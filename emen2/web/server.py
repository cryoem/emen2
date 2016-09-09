#!/usr/bin/env python
# $Id: server.py,v 1.105 2013/06/20 23:05:53 irees Exp $
import traceback
import thread
import os.path
import functools
import contextlib
import time
import collections
import sys

# Twisted imports
from twisted.application import internet
import twisted.internet
import twisted.internet.reactor
import twisted.web.static
import twisted.web.server
import twisted.python.threadpool

try:
    from twisted.internet import ssl
except ImportError:
    ssl = None

import emen2.db.config
import emen2.db.log
import emen2.web.routing

class DBPool(object):
    """Simple DB Pool loosely based on twisted.enterprise.adbapi.ConnectionPool."""
    # All connections, key is Thread ID
    dbs = {}
    running = False

    def __init__(self, min=0, max=5):
        # Minimum and maximum number of threads
        self.min = min
        self.max = max
        # Generate Thread ID
        self.threadID = thread.get_ident
        # Connect to reactor
        self.reactor = twisted.internet.reactor
        self.threadpool = twisted.python.threadpool.ThreadPool(self.min, self.max)

    def connect(self):
        """Create a new database connection."""
        import emen2.db.database
        tid = self.threadID()
        # emen2.db.log.info('DBPool info: # threads: %s -- this thread is %s'%(len(self.dbs), tid))
        db = self.dbs.get(tid)
        if not db:
            db = emen2.db.database.opendb()
            self.dbs[tid] = db
        return db

    def disconnect(self, db):
        """Disconnect a database connection."""
        tid = self.threadID()
        if db is not self.dbs.get(tid):
            raise Exception('Wrong connection for thread')
        if db:
            # db.close()
            del self.dbs[tid]

    def rundb(self, call, *args, **kwargs):
        return twisted.internet.threads.deferToThread(self._rundb, call, *args, **kwargs)

    def _rundb(self, call, *args, **kwargs):
        db = self.connect()
        kwargs['db'] = db
        result = call(*args, **kwargs)
        return result


# The thread pool.
pool = DBPool()


##### Web server ######

class WebServerOptions(emen2.db.config.DBOptions):
    optParameters = [
        ['port',      'HTTP port',  None, None, int],
        ['httpsport', 'HTTPS port', None, None, int],
    ]

    optFlags = [
        ['https', None, 'Use HTTPS']
    ]

class EMEN2Site(twisted.web.server.Site):
    def log(self, request):
        # rfc identd used for client supplied session ID
        # userid field is authenticated user name
        # This is a hack to get the session/username
        ctxid = getattr(request, "_log_ctxid", None) or "-"
        username = getattr(request, "_log_username", None) or "-"

        line = '%s %s %s %s "%s" %d %s "%s" "%s"' % (
            request.getClientIP(),
            ctxid,
            username,
            self._logDateTime,
            '%s %s %s' % (self._escape(request.method),
                          self._escape(request.uri),
                          self._escape(request.clientproto)),
            request.code,
            request.sentLength or "-",
            self._escape(request.getHeader("referer") or "-"),
            self._escape(request.getHeader("user-agent") or "-"))

        emen2.db.log.web(line)

class EMEN2BaseServer(object):

    usage = WebServerOptions

    def __init__(self, options=None):
        options = options or {}
        self.port = options.get('port') or emen2.db.config.get('web.port')

    #@contextlib.contextmanager
    def start(self, service=None):
        '''Run the server main loop'''
        # Routing resource. This will look up request.uri in the routing table
        # and return View resources.
        root = emen2.web.routing.Router()

        # Previously this used contextmanager and yield to attach the resources.
        self.attach_resources(root)

        # The Twisted Web server protocol factory,
        #  with our Routing resource as root
        # self.site = twisted.web.server.Site(root)
        self.site = EMEN2Site(root)

        reactor = twisted.internet.reactor
        reactor.suggestThreadPoolSize(emen2.db.config.get('web.threads', 1))

        # Attach to a service, or run standalone.
        if service:
            self.attach_to_service(service)
        else:
            self.attach_standalone()

    def attach_resources(self, root):
        pass
        
    def attach_to_service(self, service):
        emen2_service = internet.TCPServer(self.port, self.site)
        emen2_service.setServiceParent(service)

    def attach_standalone(self):
        reactor = twisted.internet.reactor
        reactor.listenTCP(self.port, self.site)
        reactor.run()

class EMEN2RPCServer(EMEN2BaseServer):
    """Only start the RPC server."""
    def attach_resources(self, root):
        import jsonrpc.server
        from emen2.web.resource import JSONRPCServerEvents
        root.putChild('jsonrpc', jsonrpc.server.JSON_RPC().customize(JSONRPCServerEvents))
    
class EMEN2WebServer(EMEN2BaseServer):
    """Start the full web server."""
    def attach_resources(self, root):
        # Load all View extensions
        import emen2.db.config
        emen2.db.config.load_views()

        # Child resources that do not go through the Router.
        import jsonrpc.server
        import emen2.web.resource

        # if all the JSON_RPC class does is change the eventhandler, it can (and should) be instantiated this way:
        from emen2.web.resource import JSONRPCServerEvents
        root.putChild('jsonrpc', jsonrpc.server.JSON_RPC().customize(JSONRPCServerEvents))
        root.putChild('static', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
        root.putChild('static-%s'%emen2.__version__, twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static')))
        root.putChild('favicon.ico', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/favicon.ico')))
        root.putChild('robots.txt', twisted.web.static.File(emen2.db.config.get_filename('emen2', 'web/static/robots.txt')))
    
def start_standalone():
    opt = emen2.db.config.UsageParser(WebServerOptions)
    server = EMEN2WebServer(opt.options)
    emen2.db.log.info("Web server started")
    server.start()
    
def start_rpc():
    opt = emen2.db.config.UsageParser(WebServerOptions)
    server = EMEN2RPCServer(opt.options)
    emen2.db.log.info("RPC server started")
    server.start()

if __name__ == "__main__":
    start_standalone()

__version__ = "$Revision: 1.105 $".split(":")[1][:-1].strip()