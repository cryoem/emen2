#!/usr/bin/python
# This is the main server program for EMEN2
# ts contains the actual XMLRPC methods
# ts_html contains the HTML methods

import sys
from debug import *
import debug
debug = debug.DebugState(-1, file('log.log', 'a'), sys.stdout, False)
sys.modules['debugging'] = debug

from TwistSupport_html.public import utils
from emen2 import ts
from emen2.TwistSupport_html.supp import renderpreparse
from emen2.emen2config import *
from functools import partial
from sets import Set
from twisted.internet import reactor
from twisted.web import static, server
from util import templating
import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.webresource
import emen2.TwistSupport_html.xmlrpcresource

# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)

EscapeAndReturnString = utils.MultiDecorate(decs=[utils.EscapedFun, utils.ReturnString])
EscapeAndReturnPreformattedString = utils.MultiDecorate(decs=[EscapeAndReturnString, utils.PreformattedOutp])

#############################
# Ed's new view system
#############################
templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
templates.register_template_engine('jinja', templating.JinjaTemplateEngine())
templates.add_template('default', 'the folder_name is ${folder_name}')
templates.add_template('test', 'the folder_name is ${folder_name}')

emen2.TwistSupport_html.publicresource.PublicView.register_redirect('^/test','root', recid='2')

@emen2.TwistSupport_html.publicresource.PublicView.register_url('root', '^/(?P<recid>\d+)/recinfo$')
@EscapeAndReturnPreformattedString
def test_func(path, args, ctxid, host, db=None, info=None, recid=0):
        debug.msg(LOG_INIT, 'test_func->args::: ', info, path, args, info)
        debug( args )
        print path
        ctxid=info['ctxid']
        getrecord = partial(db.getrecord, ctxid=ctxid)
        getrecorddef = partial(db.getrecorddef, ctxid=ctxid)
        return str(getrecord(int(recid)))

@emen2.TwistSupport_html.publicresource.PublicView.register_url('root1', '^/(?P<recid>\d+)$')
@utils.ReturnString
def test_func1(path, args, ctxid, host, recid=0, db=None, info=None):
        debug.msg(LOG_INIT, path, info)
        getrecord = partial(db.getrecord, ctxid=ctxid)
        getrecorddef = partial(db.getrecorddef, ctxid=ctxid)
        record = getrecord(int(recid))
        recdef = getrecorddef(record.rectype)
        params = (Set(record.keys()) | Set(recdef.params.keys()))
        paramdefs = db.getparamdefs(list(params))
        
        result1 = templates.render_template(record['template_name'] or 'default', dict(record))
        debug('the result is: %s' % result1)
        return result1
#        preparse = renderpreparse(record, result1, paramdefs=paramdefs, db=db, ctxid=ctxid)
#        return  db.renderview(record,viewdef=preparse,paramdefs=paramdefs,ctxid=ctxid)

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


import thread
import code
thread.start_new_thread(code.interact, ('',raw_input,locals()))

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.suggestThreadPoolSize(4)
reactor.run()
