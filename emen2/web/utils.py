#standard imports
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
from emen2.TwistSupport_html.public.views import View, Page
from emen2.TwistSupport_html.publicresource import PublicView



# from: http://basicproperty.sourceforge.net
def flatten(l, ltypes=(set, list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)



def commonareas(ctxid=None,host=None,db=None):
	ret = {136:"NCMI Common Area"}
	return ret



def projecttree(ctxid=None,host=None,db=None,subs=1):
	# walk GROUP -> PROJECT -> SUBPROJECT

	children=db.getchildren(g.KEYRECORDS["grouproot"],recurse=2,filter=1,tree=1)
	all=set(flatten(children.values()))

	rectypes=["group","project"]
	if subs: rectypes.append("subproject")
	
	groups={}
	for i in rectypes:
		groups[i]=db.getindexbyrecorddef(i) & all
		
	recnames={}	
	ret={}
	recnames.update(db.renderview(all & groups["group"],viewdef="$$name_group"))
	recnames.update(db.renderview(all & groups["project"],viewdef="$$name_project"))
	if subs:
		recnames.update(db.renderview(all & groups["subproject"],viewtype="recname"))
	
	for group in children[g.KEYRECORDS["grouproot"]] & groups["group"]:
		for project in children[group] & groups["project"]:

			if subs:
				for subproject in children[project] & groups["subproject"]:
					ret[subproject]="%s / %s / %s"%(recnames[group],recnames[project],recnames[subproject])

			else:
				ret[project]="%s / %s"%(recnames[group],recnames[project])

	return ret