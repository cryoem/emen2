#!/usr/bin/python
# This is the main server program for EMEN2
# ts contains the actual XMLRPC methods
# ts_html contains the HTML methods

import sys
import os
import glob
import Database
from emen2.emen2config import *
import g
print g.ROOTPW
from subsystems import macro
from subsystems import templating

from twisted.internet import reactor
from twisted.web import static, server
from emen2.TwistSupport_html.public import utils
from emen2 import ts

from emen2.TwistSupport_html import downloadresource
from emen2.TwistSupport_html import publicresource
from emen2.TwistSupport_html import uploadresource
from emen2.TwistSupport_html import webresource
from emen2.TwistSupport_html import xmlrpcresource
from emen2.util import core_macros
from emen2.util import fileops
from emen2 import util
from emen2 import TwistSupport_html
from emen2.TwistSupport_html.public import views
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
root.putChild("db",TwistSupport_html.publicresource.PublicView())
root.putChild("pub",TwistSupport_html.publicresource.PublicView())
root.putChild("download",TwistSupport_html.downloadresource.DownloadResource())
root.putChild("upload",TwistSupport_html.uploadresource.UploadResource())
root.putChild("RPC2",TwistSupport_html.xmlrpcresource.XMLRPCResource())


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
print 'macros(%d): %s' % (id(macro.MacroEngine._macros), macro.MacroEngine._macros)        
#sys.stderr.writelines(['enter statements, end them with Ctrl-D'])
#thread.start_new_thread(code.interact, ('',inp,locals()))

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.suggestThreadPoolSize(4)
reactor.run()
