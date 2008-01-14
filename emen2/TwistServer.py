#!/usr/bin/python
# This is the main server program for EMEN2
# ts contains the actual XMLRPC methods
# ts_html contains the HTML methods

import sys
from debug import *

import debug
debug = debug.DebugState(-1, file('log.log', 'a'), sys.stdout, False)
sys.modules['debugging'] = debug



from twisted.internet import reactor
from twisted.web import static, server
from emen2 import ts
#from emen2 import rest

#from emen2 import ts_db



from emen2.emen2config import *

# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)


#from emen2 import web
import emen2.TwistSupport_html.webresource
import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.downloadresource

import emen2.TwistSupport_html.publicresource
import emen2.TwistSupport_html.xmlrpcresource

#############################
# Ed's new view system
#############################

from TwistSupport_html.public import utils
from functools import partial
from emen2.TwistSupport_html.supp import renderpreparse
from sets import Set
EscapeAndReturnString = utils.MultiDecorate(decs=[utils.EscapedFun, utils.ReturnString])

EscapeAndReturnPreformattedString = utils.MultiDecorate(decs=[EscapeAndReturnString, utils.PreformattedOutp])

emen2.TwistSupport_html.publicresource.PublicView.register_redirect('^/test','root', recid='2')

@emen2.TwistSupport_html.publicresource.PublicView.register_url('root', '^/(?P<recid>\d+)/recinfo$')
@EscapeAndReturnPreformattedString
def test_func(path, ignore, args=(), db=None, info=None, recid=0):
        debug.msg(LOG_INIT, 'test_func->args::: ', info, path, args, info)
        debug( args )
        print path
        ctxid=info['ctxid']
        getrecord = partial(db.getrecord, ctxid=ctxid)
        getrecorddef = partial(db.getrecorddef, ctxid=ctxid)
        return str(getrecord(int(recid)))

@emen2.TwistSupport_html.publicresource.PublicView.register_url('root1', '^/(?P<recid>\d+)$')
@utils.ReturnString
def test_func1(path, ctxid, host, recid=0, db=None, info=None):
        debug.msg(LOG_INIT, path, info)
        getrecord = partial(db.getrecord, ctxid=ctxid)
        getrecorddef = partial(db.getrecorddef, ctxid=ctxid)
        record = getrecord(int(recid))
        recdef = getrecorddef(record.rectype)
        params = (Set(record.keys()) | Set(recdef.params.keys()))
        paramdefs = db.getparamdefs(list(params))
        publicview = recdef.views.get('publicview', 'No Public View')
        preparse = renderpreparse(record, publicview, 
															paramdefs=paramdefs, db=db, ctxid=ctxid)
        return db.renderview(record,viewdef=preparse,paramdefs=paramdefs,ctxid=ctxid)

@emen2.TwistSupport_html.publicresource.PublicView.register_url('exec', '^/exec/(?P<expression>.+)$')
@EscapeAndReturnString
def execc(path, args=(), *arg, **kwargs):
		return str(eval(kwargs.get('expression', '')))

######################
# End Ed's system
######################


# Setup twist server root Resources
root = static.File(EMEN2ROOT+"/tweb")
root.putChild("db",emen2.TwistSupport_html.webresource.WebResource())
root.putChild("pub",emen2.TwistSupport_html.publicresource.PublicView())
root.putChild("download",emen2.TwistSupport_html.downloadresource.DownloadResource())
root.putChild("upload",emen2.TwistSupport_html.uploadresource.UploadResource())
root.putChild("RPC2",emen2.TwistSupport_html.xmlrpcresource.XMLRPCResource())

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))

reactor.suggestThreadPoolSize(4)

reactor.run()
