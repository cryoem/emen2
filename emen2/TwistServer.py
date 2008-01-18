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
from util import templating

import emen2.TwistSupport_html.downloadresource
import emen2.TwistSupport_html.publicresource
import emen2.TwistSupport_html.uploadresource
import emen2.TwistSupport_html.webresource
import emen2.TwistSupport_html.xmlrpcresource

import TwistSupport_html.public.views
# Change this to a directory for the actual database files
ts.startup(EMEN2DBPATH)

#############################
# Ed's new view system
#############################
g.templates = templating.TemplateFactory('mako', templating.MakoTemplateEngine())
g.templates.register_template_engine('jinja', templating.JinjaTemplateEngine())
g.templates.add_template('default', 'the folder_name is ${rec["folder_name"]}')
g.templates.add_template('test', 'the folder_name is ${rec["folder_name"]}')
g.templates.add_template('test1', 'another test $@recid()')
g.templates.add_template('form','''<html><head></head><body><form action="/pub/form" method="POST">
                                                    <input type="text"  name="expression" />
                                                    <input type="text"  name="test" />
                                                    <input type="submit" /></form>
                                                ${ctxid}</body></html>''')
g.templates.add_template('qweqwe', 'qweqwe ${rec}')
g.templates.add_template('include', '''hello, ${rec['permissions']} I include qweqwe<br />    
                                                     <%include file="qweqwe" /> <br />and call a def in namespace testns<br /> <%namespace name="testns"  file="testns"  /> ${testns.myfunc(3)}''')
g.templates.add_template('testns', '<%def name="myfunc(x)">this is myfunc, x is ${x}</%def>')

for i in glob.glob('./TwistSupport_html/templates/*.mako'):
	f=open(i)
	name=os.path.splitext(os.path.basename(i))[0]
	data=f.read()
	f.close()
	g.templates.add_template(name,data)

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
        
sys.stderr.writelines(['enter statements, end them with Ctrl-D'])
thread.start_new_thread(code.interact, ('',inp,locals()))

# You can set the port to listen on...
reactor.listenTCP(EMEN2PORT, server.Site(root))
reactor.suggestThreadPoolSize(4)
reactor.run()
