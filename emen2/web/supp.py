################################################### 
## SUPPORT FUNCTIONS ##############################
###################################################

print "...loading %s"%__name__


from sets import Set
import re
import os
#from emen2.ts import db
from emen2 import ts
import html
import tmpl
#import supp
#import plot
import pickle
import timing




def groupsettolist(groups):
	groupl = {}
	for i in groups.keys():
		glist = list(groups[i])
		groupl[i] = glist
	return groupl		


	


# just to keep it in one place
def regexparser():
	re1 =  "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))[\s<]?"    \
				"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))[\s<]?" \
				"|(?P<name>(\$\#(?P<name1>\w*)[\s<]?))"
	return re1

def macro_processor(macro,macroparameters,recordid,ctxid=None):
	global db
	
	if macro == "childcount":
		queryresult = ts.db.getchildren(int(recordid),ctxid=ctxid)
#		mgroups1 = db.groupbyrecorddef(queryresult,ctxid=ctxid)
#		mgroups = db.countchildren(int(recordid),ctxid=ctxid)
		try:
			value = len(queryresult)
#			value = len(mgroups[macroparameters])
#			value = mgroups[macroparameters]
		except:
			return ""
	elif macro == "parentrecname":
		queryresult = ts.db.getparents(recordid,ctxid=ctxid)
		mgroups = ts.db.groupbyrecorddef(queryresult,ctxid=ctxid)
		for j in mgroups[macroparameters]:
			recorddef = ts.db.getrecord(j,ctxid=ctxid)
			try:
				value = recorddef.items_dict()["recname"]
			except:
				return ""
				
				
	return value



def argmap(dict):
	for i in dict: dict[i]=dict[i][0]
		
		

		
def invert(d):
	nd = {}
	returnlist = []
	for k, v in d.iteritems():
		if v == "":
			v = "novalue"
		if nd.has_key(v):
			nd[v].append(k)
		else:
			nd[v] = [k]
	return nd



	
def sortlistbyparamname(paramname,subset,reverse,ctxid):
	global db
#	print "Sorting..."
#	print subset

	q = ts.db.getindexdictbyvalue(paramname,None,ctxid,subset=subset)
	nq = invert(q)
	l = nq.keys()
	l.sort()
	sortedlist = []
	for i in l:
		j = nq[i]
		j.sort()	
		for k in j:
			sortedlist.append(k)
	for c in (Set(subset) - Set(sortedlist)):
		sortedlist.append(c)
	if reverse:
		sortedlist.reverse()

#	print "Done sorting.."
#	print sortedlist
	return sortedlist

		

def render_groupedhead(groupl,ctxid=None):
	"""Render tab switching buttons"""
	ret = []
	for i in groupl.keys():
		ret.append("\t<div class=\"button_main\" id=\"button_main_%s\"><a href=\"javascript:switchin('main','%s')\">%s (%s)</a></div>\n"%(i,i,i,len(groupl[i])))
	return " ".join(ret)
	
		
def htable(itmlist,cols,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=['\n\n<table>']

	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("\t<tr>")
		ret.append("\t\t<td><a href=\"%s%s\">%s</a></td>"%(proto,j,j))
		if (i%cols==cols-1) : ret.append("</tr>\n")

	if (len(itmlist)%cols!=0) : ret.append("\t</tr>\n</table>\n")
	else : ret.append("</table>")

	return "".join(ret)



def htable2(itmlist,cols,proto):
	"""Produce a table of values and counts in 'cols' columns"""
	ret=['\n\n<table>']

	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("\t<tr>")
		ret.append("\t\t<td><a href=\"%s%s\">%s (%d)</a></td>"%(proto,j[0],j[0],j[1]))
		if (i%cols==cols-1) : ret.append("\t</tr>\n")

	if (len(itmlist)%cols!=0) : ret.append("\t</tr>\n</table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)



#def dicttable(dict,proto):
#	ret = []
#	ret.append("\n\n<table class=\"dicttable\" cellspacing=\"0\" cellpadding=\"0\">\n")
#	skipped = 0
#	for k,v in dict.items():
#		item=db.getparamdef(str(k))
#		ret.append("\t<tr>\n\t\t<td class=\"pitemname\"><a href=\"%s%s\">%s</a></td>\n\t\t<td>%s</td>\n\t</tr>\n"%(proto,k,item.desc_short,v))
#	ret.append("</table>")
#	return " ".join(ret)	


def clearworkflowcache(ctxid):

	wflist = ts.db.getworkflow(ctxid)
	for wf in wflist:
		wfdict = wf.items_dict()
		if wfdict["wftype"] == "recordcache" or wfdict["wftype"] == "querycache":
			ts.db.delworkflowitem(wf.wfid,ctxid)



def render_groupedlist(path, args, ctxid, host, viewonly=None, sortgroup=None):
	"""Draw tables for parents/children of a record"""
	ret = []
	wf = ts.db.getworkflowitem(int(args["wfid"][0]),ctxid)
	groupl = wf['appdata']

	for i in groupl.keys():
		# do we want to render this record type?
		if viewonly and viewonly != i:
			pass
		else:
			args["groupname"] = [i]
			table = encapsulate_render_grouptable(path,args,ctxid,host)
	
			ret.append("".join(table))

	return " ".join(ret)


def encapsulate_render_grouptable(path,args,ctxid,host):
	import emen2.TwistSupport_html.html.render_grouptable
	
	ret = []

	if args.has_key("groupname"):
		groupname = args["groupname"][0]

	ret.append("\n\n<div class=\"page_main\" id=\"page_main_%s\">"%groupname)
	ret.append("\t<h1>%s</h1>\n"%(groupname))

	r = emen2.TwistSupport_html.html.render_grouptable.render_grouptable(path,args,ctxid,host)
	ret.append("".join(r))

	ret.append("</div>")
	return " ".join(ret)
	
	


