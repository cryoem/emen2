#!/usr/bin/python
# This is the main server program for EMEN2
from emen2 import TwistSupport_html
from emen2 import ts
from emen2 import util
from emen2.TwistSupport_html import publicresource
from emen2.TwistSupport_html import xmlrpcresource
from emen2.TwistSupport_html.public import views
from emen2.emen2config import *
from emen2.subsystems import macro
from emen2.subsystems import templating
from emen2.subsystems import routing
from emen2.util import core_macros
from emen2.util import fileops
from emen2.util import utils
from twisted.internet import reactor
from twisted.web import static, server
import code
import emen2.Database
import emen2.globalns
import glob
import os
import sys
import thread
import time

g = emen2.globalns.GlobalNamespace('')

# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)

#############################
# Ed's new view system
#############################
def load_views():
    g.templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
    g.TEMPLATEDIR="./TwistSupport_html/templates"
    templating.get_templates(g.TEMPLATEDIR)
    
def reload_views():
    reload(TwistSupport_html.public.views)
    load_views()
    for view in routing.URLRegistry.URLRegistry.values():
        view = view._URL__callback.__module__
        exec 'import %s;reload(%s)' % (view,view)

load_views()

g.macros = macro.MacroEngine()

# Setup twist server root Resources
root = static.File(EMEN2ROOT+"/tweb")
root.putChild("db",TwistSupport_html.publicresource.PublicView())
root.putChild("pub",TwistSupport_html.publicresource.PublicView())
#root.putChild("download",TwistSupport_html.downloadresource.DownloadResource())
#root.putChild("upload",TwistSupport_html.uploadresource.UploadResource())
root.putChild("RPC2",TwistSupport_html.xmlrpcresource.XMLRPCResource())


x = {}
x.update(globals())
exec "from test import *" in x
a = code.InteractiveConsole(x, '')
def interact():
    while True:
        a.interact()
        exit = raw_input('respawn [Y/n]? ').strip().lower() or 'y'
        if exit[0] == 'n':
            thread.interrupt_main()
            return
        
thread.start_new_thread(interact, ())

print 'macros(%d): %s' % (id(macro.MacroEngine._macros), macro.MacroEngine._macros)        

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.suggestThreadPoolSize(4)
reactor.run()
