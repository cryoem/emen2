#standard imports
from sets import Set
import re
import os
from operator import itemgetter
import time
import math
import copy

#standard emen2 imports
from emen2.emen2config import *
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


#special imports
import demjson


###### ian
import emen2.TwistSupport_html.supp
from emen2.TwistSupport_html.public.views import View, Page
from emen2.TwistSupport_html.publicresource import PublicView
import operator

import smtplib
from email.mime.text import MIMEText


def sendmailtemplate(recipient,template,ctxt=None):
	if ctxt==None: ctxt={}
	ctxt["recipient"]=recipient
	ctxt["MAILADMIN"]=g.MAILADMIN
	msg = g.templates.render_template(template, ctxt)
	sendmailraw(recipient,msg)	




def sendmail(recipient,subject,msgtxt,ctxid=None,host=None,db=None):

	msg=MIMEText(msgtxt)
	msg['Subject'] = subject
	msg['From'] = g.MAILADMIN
	msg['To'] = recipient

	#return
	# Send the message via our own SMTP server, but don't include the
	# envelope header.

	s = smtplib.SMTP(g.MAILHOST)
	s.set_debuglevel(1)
	s.sendmail(g.MAILADMIN, [recipient], msg.as_string())

	
	
	
def sendmailraw(recipient,content):
	#return
	s = smtplib.SMTP(g.MAILHOST)
	s.set_debuglevel(1)
	s.sendmail(g.MAILADMIN, [recipient], content)		



def commonareas(ctxid=None,host=None,db=None):
	ret = {136:"NCMI Common Area"}
	return ret



def projecttree(ctxid=None,host=None,db=None,subs=1):
	# walk GROUP -> PROJECT -> SUBPROJECT
	recnames={}
	q_groups=db.groupbyrecorddeffast(db.getchildren(g.GROUPROOT,ctxid=ctxid,host=host),ctxid=ctxid,host=host).get("group",set())
	for group in q_groups:				
		group_name=db.renderview(group,ctxid=ctxid,host=host,viewdef="$$name_group") #viewtype="recname"
		q_projects=db.groupbyrecorddeffast(db.getchildren(group,ctxid=ctxid,host=host),ctxid=ctxid,host=host).get("project",set())
		for project in q_projects:
			project_name=db.renderview(project,ctxid=ctxid,host=host,viewdef="$$name_project")#viewtype="recname"
			recnames[project]="%s / %s"%(group_name, project_name)
			if subs:
				q_subprojects=db.groupbyrecorddeffast(db.getchildren(project,ctxid=ctxid,host=host),ctxid=ctxid,host=host).get("subproject",set())
				for subproject in q_subprojects:
					subproject_name=db.renderview(subproject,ctxid=ctxid,host=host,viewtype="recname")
					recnames[subproject]="%s / %s / %s"%(group_name, project_name, subproject_name)
				
	#subproject_sorted=[i[0] for i in sorted(recnames.items(), key=itemgetter(1))]
	#for i in subproject_sorted: print recnames[i]
	
	return recnames