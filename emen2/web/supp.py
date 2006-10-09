################################################### 
## SUPPORT FUNCTIONS ##############################
###################################################

from sets import Set
import re
import os
from emen2.TwistSupport_db import db
import html
import tmpl
#import supp
import plot


# just to keep it in one place
def regexparser():
	re1 = "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))[\s<]?|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))[\s<]?|(?P<name>((\$\#(?P<name1>\w*))\s?))"
	return re1

def macro_processor(macro,macroparameters,recordid,ctxid=None):
	global db
	
	if macro == "childcount":
		queryresult = db.getchildren(int(recordid),ctxid=ctxid)
		mgroups = db.groupbyrecorddef(queryresult,ctxid=ctxid)
		try:
			value = len(mgroups[macroparameters])
		except:
			value = ""
	elif macro == "parentrecname":
		queryresult = db.getparents(recordid,ctxid=ctxid)
		mgroups = db.groupbyrecorddef(queryresult,ctxid=ctxid)
		for j in mgroups[macroparameters]:
			recorddef = db.getrecord(j,ctxid=ctxid)
			try:
				value = recorddef.items_dict()["recname"]
			except:
				value = ""
				
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
	print "Sorting..."
#	print subset

	q = db.getindexdictbyvalue(paramname,None,ctxid,subset=subset)
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

	print "Done sorting.."
#	print sortedlist
	return sortedlist


		
def parent_tree(recordid,ctxid=None):
	"""Get the parent tree of a record. Returns table. Includes html"""
	# 158 - 366
	m = [[int(recordid)]]

	[x,y] = [0,0]
	keepgoing = 1
	while keepgoing:
		lst = []
		if m[y][x]:
			queryresult = db.getparents(m[y][x],ctxid=ctxid)
#			print "Parents for %s: %s"%(m[y][x],queryresult)

			for i in queryresult:
				lst.append(i)

		if len(lst) >= 1:
			m[y].append(lst[0])

		if len(lst) >= 2:
			for i in range(1,len(lst)):
				lst2 = [""]*len(m[0])
				lst2[x+1] = lst[i]
				m.insert(1,lst2)

		x = x + 1

		try:
			test = m[y][x]
		except IndexError:
			x = 0
			y = y + 1
		try:
			keepgoing = len(m[y])
		except IndexError:
			keepgoing = 0

#		print m
		
	# silly but needed -- pad rows to equal length before reversing 
	for i in range(0,len(m)):
		if len(m[0]) > len(m[i]):
			for j in range(len(m[i]),len(m[0])):
				m[i].append("")
		elif len(m[i]) > len(m[0]):
			for j in range(len(m[0]),len(m[i])):
				m[0].append("")
	# requires two passes; reverse now
	for i in range(0,len(m)):			
		m[i].reverse()

	ret = ["\n\n<div class=\"navtree\">\n\n<table cellpadding=\"0\" cellspacing=\"0\" class=\"navtable\">\n"]

	for posy in range(0,len(m)):
		ret.append("\t<tr>\n")
		for posx in range(0,len(m[posy])):
			if m[posy][posx] != "":
				record = db.getrecord(m[posy][posx], ctxid)
				record_dict = record.items_dict()

				pclass="ptree"
	
				# Attempt to get title of record; else use record type
				try:
					text = record_dict['recname']
				except:
					text = "(%s)"%record_dict['rectype']
	
				ret.append("\t\t<td class=\"%s\">"%pclass)

				
				if os.path.exists("tweb/images/icons/%s.gif"%record_dict['rectype']):
					ret.append("<img src=\"/images/icons/%s.gif\" alt=\"\"/>"%record_dict['rectype'])
				
				ret.append("<a href=\"/db/record?name=%s\">%s</a></td>\n"%(m[posy][posx],text))

				ok = ["","","","",""]
				img = ""

				# See which neighbors exist
				# below
				try:
					ok[0] = m[posy+1][posx]
				except:
					pass
				# next
				try:
					ok[1] = m[posy][posx+1]
				except:
					pass
				# below and next
				try:
					ok[2] = m[posy+1][posx+1]
				except:
					pass
				# above
				try:
					ok[3] = m[posy-1][posx]
				except:
					pass
				# above and next
				try:
					ok[4] = m[posy-1][posx+1]	
				except:
					pass

				# Case switch to determine icon based on neighbors
				if ok[0] and not ok[2]:
					img = "branch_next"
				if ok[4] and not ok[1] and not img:
					img = "branch_up"
				if ok[1] and not img:
					img = "next"
				if not img:
					img = "blank"

				ret.append("\t\t<td class=\"ptreeempty\"><img src=\"/images/%s.png\" alt=\"\"/></td>\n"%img)

			else:
				ret.append("\t\t<td></td>\n\t\t<td></td>\n")

		ret.append("\t</tr>\n")
	ret.append("</table>\n\n</div>")

	return " ".join(ret)


	

def render_groupedhead(groupl,ctxid=None):
	"""Render tab switching buttons"""
	ret = []
	for i in groupl.keys():
		ret.append("\t<div class=\"switchbutton\" id=\"button_%s\"><a href=\"javascript:switchid('%s')\">%s (%s)</a></div>\n"%(i,i,i,len(groupl[i])))
	return " ".join(ret)
	
	

def render_groupedlist(path, args, ctxid, host, viewonly=None, sortgroup=None):
	"""Draw tables for parents/children of a record"""
	ret = []
	wf = db.getworkflowitem(int(args["wfid"][0]),ctxid)
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
	ret = []

	if args.has_key("groupname"):
		groupname = args["groupname"][0]

	ret.append("\n\n<div class=\"switchpage\" id=\"page_%s\">"%groupname)
	ret.append("\t<h1 class=\"switchheader\" id=\"header_%s\">%s</h1>\n"%(groupname,groupname))

	r = html.html_render_grouptable(path,args,ctxid,host)
	ret.append("".join(r))

	ret.append("</div>")
	return " ".join(ret)




def get_tile(tilefile,level,x,y):
	"""get_tile(tilefile,level,x,y)
	retrieve a tile from the file"""

#	print "get_tile: %s %s %s %s"%(tilefile,level,x,y)

	tf=file(tilefile,"r")

	td=pickle.load(tf)
	try: a=td[(level,x,y)]
	except: raise KeyError,"Invalid Tile"
	tf.seek(a[0],1)
	ret=tf.read(a[1]) 
	tf.close()

	return ret




def get_tile_dim(tilefile):
	"""This will determine the number of tiles available in
	x and y at each level and return a list of (nx,ny) tuples"""

	tf=file(tilefile,"r")
	td=pickle.load(tf)
	tf.close()

	ret=[]
	for l in range(10): 
		x,y=-1,-1
		for i in td:
			if i[0]==l: x,y=max(x,i[1]),max(y,i[2])
		if x==-1 and y==-1: break
		ret.append((x+1,y+1))

	return ret







	
def html_htable(itmlist,cols,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=['\n\n<table>']

	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("\t<tr>")
		ret.append("\t\t<td><a href=\"%s%s\">%s</a></td>"%(proto,j,j))
		if (i%cols==cols-1) : ret.append("</tr>\n")

	if (len(itmlist)%cols!=0) : ret.append("\t</tr>\n</table>\n")
	else : ret.append("</table>")

	return "".join(ret)



def html_htable2(itmlist,cols,proto):
	"""Produce a table of values and counts in 'cols' columns"""
	ret=['\n\n<table>']

	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("\t<tr>")
		ret.append("\t\t<td><a href=\"%s%s\">%s (%d)</a></td>"%(proto,j[0],j[0],j[1]))
		if (i%cols==cols-1) : ret.append("\t</tr>\n")

	if (len(itmlist)%cols!=0) : ret.append("\t</tr>\n</table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)



def html_dicttable(dict,proto):
	ret = []
	ret.append("\n\n<table class=\"dicttable\" cellspacing=\"0\" cellpadding=\"0\">\n")
	skipped = 0
	for k,v in dict.items():
		item=db.getparamdef(str(k))
		ret.append("\t<tr>\n\t\t<td class=\"pitemname\"><a href=\"%s%s\">%s</a></td>\n\t\t<td>%s</td>\n\t</tr>\n"%(proto,k,item.desc_short,v))
	ret.append("</table>")

	return " ".join(ret)	




def groupsettolist(groups):
	groupl = {}
	for i in groups.keys():
		glist = list(groups[i])
		groupl[i] = glist
	return groupl		





def clearworkflowcache(ctxid):
	global db 

	wflist = db.getworkflow(ctxid)
	for wf in wflist:
		wfdict = wf.items_dict()
		if wfdict["wftype"] == "recordcache" or wfdict["wftype"] == "querycache":
			db.delworkflowitem(wf.wfid,ctxid)





