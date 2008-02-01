#!/usr/bin/python
# This is the main server program for EMEN2
# ts contains the actual XMLRPC methods
# ts_html contains the HTML methods

import sys
import os
import glob

from emen2.emen2config import *
import g

from TwistSupport_html.public import utils
from emen2 import ts
from twisted.internet import reactor
from twisted.web import static, server
from subsystems import templating
from subsystems import macro

import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.webresource
import emen2.TwistSupport_html.xmlrpcresource
import util.core_macros
import util.fileops
import TwistSupport_html.public.views
# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)

#############################
# Ed's new view system
#############################
def load_views():
    g.templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
    g.TEMPLATEDIR="./TwistSupport_html/templates"
    util.fileops.get_templates(g.TEMPLATEDIR)
def reload_views():
    reload(TwistSupport_html.public.views)
    load_views()

load_views()

g.macros = macro.MacroEngine()

# Setup twist server root Resources
root = static.File(EMEN2ROOT+"/tweb")
root.putChild("db",emen2.TwistSupport_html.publicresource.PublicView())
root.putChild("pub",emen2.TwistSupport_html.publicresource.PublicView())
root.putChild("download",emen2.TwistSupport_html.downloadresource.DownloadResource())
root.putChild("upload",emen2.TwistSupport_html.uploadresource.UploadResource())
root.putChild("RPC2",emen2.TwistSupport_html.xmlrpcresource.XMLRPCResource())


import thread
import code
import time

def inp(banner=''):
    if not sys.stdin.closed:
        sys.stderr.write(banner)
    result = sys.stdin.read()
    if result:
        return result
    else:
        thread.interrupt_main()
        time.sleep(10000000)
        
#sys.stderr.writelines(['enter statements, end them with Ctrl-D'])
#thread.start_new_thread(code.interact, ('',inp,locals()))

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.suggestThreadPoolSize(4)
reactor.run()
