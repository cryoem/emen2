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
from operator import itemgetter



def groupsettolist(groups):
	for i in groups.keys():
		groups[i] = list(groups[i])
	return groups		


	


# just to keep it in one place
def regexparser():
	re1 =  "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))[\s<]?"    \
				"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))[\s<]?" \
				"|(?P<name>(\$\#(?P<name1>\w*)[\s<]?))"
	return re1



def macro_processor(macro,macroparameters,recordid,ctxid=None,db=None):
	
	if macro == "childcount":
		queryresult = db.getchildren(int(recordid),recurse=5,ctxid=ctxid)

		# performance optimization
		if len(queryresult) < 1000:
			mgroups = db.groupbyrecorddeffast(queryresult,ctxid)
		else:
			mgroups = db.groupbyrecorddef(queryresult,ctxid)

###		mgroups = db.countchildren(int(recordid),recurse=0,ctxid=ctxid)
		if mgroups.has_key(macroparameters):
			return len(mgroups[macroparameters])
		else:
			return

	elif macro == "parentrecname":
		queryresult = db.getparents(recordid,ctxid=ctxid)
		mgroups = db.groupbyrecorddef(queryresult,ctxid=ctxid)
		for j in mgroups[macroparameters]:
			recorddef = db.getrecord(j,ctxid=ctxid)
			try:
				value = recorddef.items_dict()["recname"]
			except:
				return ""
				
				
	return value



def argmap(dict):
	for i in dict: dict[i]=dict[i][0]
		


# much simpler; itemgetter new in python 2.4
#def sortlistbyparamname(paramname,subset,reverse,ctxid):
#	q = db.getindexdictbyvalue(paramname,None,ctxid,subset=subset)
#	q = [i[0] for i in sorted(q.items(), key=itemgetter(1), reverse=True)]
	
#	global db
#	print "Sorting..."
#	print subset
#	q = db.getindexdictbyvalue(paramname,None,ctxid,subset=subset)
#	nq = invert(q)
#	l = nq.keys()
#	l.sort()
#	sortedlist = []
#	for i in l:
#		j = nq[i]
#		j.sort()	
#		for k in j:
#			sortedlist.append(k)
#	for c in (Set(subset) - Set(sortedlist)):
#		sortedlist.append(c)
#	if reverse:
#		sortedlist.reverse()

#	print "Done sorting.."
#	print sortedlist
#	return sortedlist
#
#def invert(d):
#	nd = {}
#	returnlist = []
#	for k, v in d.iteritems():
#		if v == "":
#			v = "novalue"
#		if nd.has_key(v):
#			nd[v].append(k)
#		else:
#			nd[v] = [k]
#	return nd

def render_groupedhead(groupl,ctxid=None,recid=None,wfid=None):
	"""Render tab switching buttons"""
	ret = []
	for i in groupl.keys():
#		ret.append("\t<div class=\"button_main\" id=\"button_main_%s\"><a href=\"javascript:switchin('main','%s')\">%s (%s)</a></div>\n"%(i,i,i,len(groupl[i])))
#db/render_grouptable?&name=135&groupname=project&reverse_project=1&zone=zone_project
		if not wfid:
			req = "/db/render_grouptable?name=%s&groupname=%s&zone=zone_%s"%(recid,i,i)
		else:
			req = "/db/render_grouptable?wfid=%s&groupname=%s&zone=zone_%s"%(wfid,i,i)
			#makeRequest('%s','zone_%s');
		ret.append("""
		<div class="button_main" id="button_main_%s">
			<span class="jslink" onclick="javascript:switchin('main','%s')">
				%s (%s)
			</span>
		</div>
			"""%(i,i,i,len(groupl[i])))

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





	
	


