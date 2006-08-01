# TwistSupport_html.py	Steven Ludtke  06/2004
# This module provides the resources needed for a HTML server using Twisted

from twisted.web.resource import Resource
from emen2 import TwistSupport 
from sets import Set
import pickle
#from twebutil import *
import os
import traceback
import re

import time
import random

try:
	import matplotlib
	matplotlib.use('Agg')
	from matplotlib import pylab, font_manager
	from matplotlib.ticker import FormatStrFormatter
	from matplotlib import colors
except:
	print "No matplotlib, plotting will fail"

# we open the database as part of the module initialization
db=None
DB=TwistSupport.DB

class DBResource(Resource):
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""
	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_POST(self,request):
		return self.render_GET(request)
		
	def render_GET(self,request):
		session=request.getSession()			# sets a cookie to use as a session id
		
#		return "request was '%s' %s"%(str(request.__dict__),request.getClientIP())
		global db,callbacks

		if (len(request.postpath)==0 or request.postpath[0]=="index.html" or len(request.postpath[0])==0) : return html_home()
				
		# This is the one request that doesn't require an existing session, since it sets up the session
		if (request.postpath[0]=='login'):
			session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
#			return "Login Successful %s (%s)"%(str(request.__dict__),session.ctxid)
			return """<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
				<meta http-equiv="REFRESH" content="2; URL=%s"><title>HTML REDIRECT</title></head>
				<body><h3>Login Successful</h3>"""%request.received_headers["referer"]

		if (request.postpath[0]=="newuser"):
			return html_newuser(request.postpath,request.args,None,request.getClientIP())
				
		# A valid session will have a valid ctxid set
		try:
			ctxid=session.ctxid
		except:
			return loginpage(request.uri)
		
		db.checkcontext(ctxid,request.getClientIP())

		# Ok, if we got here, we can actually start talking to the database
		
		method=request.postpath[0]
		host=request.getClientIP()
		
		ret=eval("html_"+method)(request.postpath,request.args,ctxid,host)
		
		# JPEG Magic Number
		if ret[:3]=="\xFF\xD8\xFF" : request.setHeader("content-type","image/jpeg")
		if ret[:4]=="\x89PNG" : request.setHeader("content-type","image/png")
		return ret
#		return str(request.__dict__)
#		return callbacks[method](request.postpath,request.args,ctxid,host)

#		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())



################################################### 
## SUPPORT FUNCTIONS ##############################
###################################################

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
	q = db.getindexdictbyvalue(paramname,None,ctxid,subset=subset)

#	print "\n q: %s \n"%q
#	print len(subset)

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

#	print "sortedlist: %s"%sortedlist

	return sortedlist


		
def parent_tree(recordid,ctxid=None):
	"""Get the parent tree of a record. Returns table."""
	# 158 - 366
	m = [[int(recordid)]]

	[x,y] = [0,0]
	keepgoing = 1
	while keepgoing:
		list = []
		if m[y][x]:
			queryresult = db.getparents(m[y][x],ctxid=ctxid)
#			print "Parents for %s: %s"%(m[y][x],queryresult)

			for i in queryresult:
				list.append(i)

		if len(list) >= 1:
			m[y].append(list[0])

		if len(list) >= 2:
			for i in range(1,len(list)):
				list2 = [""]*len(m[0])
				list2[x+1] = list[i]
				m.insert(1,list2)

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




def parse_view_group(groupname, ctxid=None):
	"""Get view, parse it, return constructed view"""
	
	viewtype = "tabularview"
	viewdef=db.getrecorddef(groupname,ctxid).views[viewtype]

	viewtype = "tabularview"

	preparse = []

	#
	# Pre-parsing
	#
	parse_split = viewdef.split(' ')
	for i in range(0,len(parse_split)):
		isplit = parse_split[i].split('=')

		try:
			count = isplit[1].count('"')
		except IndexError:
			count = 0
		if count:
			tmp = isplit[1] + " " + parse_split[i+1]
			isplit[1] = tmp
			parse_split[i+1] = ""

		preparse.append(isplit)
	#	print "i: %s	 v: %s"%(i,isplit)

	# remove this sometime
	preparse2 = []
	for i in preparse:
		if i[0] != "":
			preparse2.append(i)
	preparse = preparse2
	
#	print "Preparse.. %s"%preparse

	#
	# Main parsing
	#
	out = []
	vartypes = []
	vardescs = []
	for i in preparse:
		if i[0].count("$") == 2:
			# j is the parameter name
			j = i[0].replace("$$","")
			try: 
				#text = record_dict[j.lower()]
				# hit the database to get the type and description of the parameter j
				item = db.getparamdef(j.lower())
				vt = item.vartype
				vd = item.desc_short
			except:
				text = ''
				vt = ''
				vd = ''
			out.append(j)
			vartypes.append(vt)
			vardescs.append(vd)
		elif i == "":
			pass
		else:
			out.append(str(i[0]))
			vartypes.append('')
			vardescs.append('')

	return out,vartypes,vardescs
	#
	# View parsing
	#
	#if viewtype == "onelineview":
	#	onelineview = render_onelineview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=ctxid)
	#	ret.append(" ".join(onelineview))


	#if viewtype == "tabularview":	


	return ret



def render_onelineview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=None):
	ret = []
	ret.append("\t\t<td><a href=\"/db/record?name=%s\">%s</a> -- %s -- \n"%(recordid,recordid,record_dict['rectype']))
	ret.append(" ".join(out))
	ret.append("</td>")
	return ret


#def render_tabularviewheader(groupname,out,vartypes,vardescs,ctxid=None):


	# tdclass is for shaded/non-shaded row
	# tdclass2 is for first-item on row
#	else:

def render_tabularview(id,out,vartypes,vardescs,modulo=0,ctxid=None):
	maxtextlength=500
	ret = []

#	print "render_tabularview: \nout:%s\nvartypes:%s\nvardescs:%s\n\n"%(out,vartypes,vardescs)

	record=db.getrecord(id,ctxid)
	record_dict = record.items_dict()

	skipped = []
	ret.append("\t<tr>\n")

	if modulo % 2:
		tdclass = ""
	else:
		tdclass = "shaded"

	tdclass2 = "firstitem"
	for i in range(0,len(out)):
		if vartypes[i] == "text":
			skipped.append(i)
		else:
			try:
				string = record_dict[out[i]]
			except:
#				string = "(%s)"%out[i]
				string = ""
				
			if vartypes[i] == "float" and vardescs[i]:
				if string == 0:
					string = "0"
				else:
					try:
						string = "%0.2f"%string
					except TypeError:
						string = "%s"%string
				
			ret.append("\t\t<td class=\"%s %s\"><!--  --><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,tdclass2,id,string))
			tdclass2 = ""

	tdclass2 = "firstitem"
	for i in skipped:

		try:
			string = record_dict[out[i]]
		except:
#			string = "(%s)"%out[i]
			string = ""
			
		if len(string) >= maxtextlength:
			string = string[0:maxtextlength] + " <a href=\"/db/record?name=%s\">(view more)</a>..."%id

		ret.append("\t</tr>\n\t<tr>\n\t\t<td class=\"%s %s\"></td><td class=\"%s\" colspan=\"%s\"><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,tdclass2,tdclass,len(out)-1,id,string))
		tdclass2 = ""

	ret.append("\t</tr>\n")

	return ret
	

def render_groupedhead(groupl,ctxid=None):

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


# Include recordids in definition because record_dicts may contain extra definitions..
def html_render_grouptable(path,args,ctxid,host,groupname=None):
	"""Make a div page with table for items with a common view definition"""

	perpage = 100
	direct = 0
	recordids = []
	ret = []

	groupname = str(args["groupname"][0])

	if args.has_key("pos"):
		pos = int(args["pos"][0])
		perpage = int(args["perpage"][0])
	elif args.has_key("pos_%s"%groupname):
		pos = int(args["pos_%s"%groupname][0])
	else:
		pos = 0
		
#	if not args.has_key("reverse_%s"%groupname):
#		reverse = bool(0)
#		args["reverse_%s"%groupname] = [str(reverse)]
#	else:
#		reverse = not bool(args["reverse_%s"%groupname][0])
#		args["reverse_%s"%groupname] = [str(reverse)]

	wf = db.getworkflowitem(int(args["wfid"][0]),ctxid)
	recordids = wf["appdata"][groupname]

	if args.has_key("sort_%s"%groupname):
		sortby = args["sort_%s"%groupname][0]
		reverse = int(args["reverse_%s"%groupname][0])
		recordids = sortlistbyparamname(sortby,recordids,reverse,ctxid)
		reverse = int(not reverse)
	else:
		reverse = "0"

	ret.append("<div id=\"zone_%s\">"%groupname)

	
	# Navigation arrows
	if perpage:
		
		nav = []
		key = "pos_%s"%groupname

		baseurl=["/db/render_grouptable","?"]
		if args.has_key(key):
			ipos = int(args[key][0])
		else:
			ipos = 0

		pos = ipos

		for j in args.keys():
			if j != key and j != "viewinit":
				baseurl.append("&%s=%s"%(j,args[j][0]))
		baseurlstr = "".join(baseurl)
		
		nav.append("<div class=\"table_arrows\">")
		if (ipos - perpage) >= 0:
			nav.append("""<span class="table_span" onclick="makeRequest('%s&%s=%s&zone=%s&viewinit=%s','%s')">&laquo;</span>"""%(baseurlstr,key,ipos - perpage,"zone_%s"%groupname,groupname,"zone_%s"%groupname))

		end = pos+perpage
		count = len(recordids)
		if end > count:
			end = count
		nav.append("""<span class="table_span"> (%s-%s of %s) </span>"""%(pos,end,count))

		if (ipos + perpage) <= len(recordids):
			nav.append("""<span class="table_span" onclick="makeRequest('%s&%s=%s&zone=%s&viewinit=%s','%s')">&raquo;</span>"""%(baseurlstr,key,ipos + perpage,"zone_%s"%groupname,groupname,"zone_%s"%groupname))

		nav.append("</div>")
	
	ret.append(" ".join(nav))
	
	# end nav arrows
	
	ret.append("\n\n<table class=\"groupview\" cellspacing=\"0\" cellpadding=\"0\">\n")

	out,vartypes,vardescs = parse_view_group(groupname,ctxid=ctxid)
	
	
	ret.append("\t<tr>\n")
	for i in range(0,len(out)):
		if vartypes[i] != "text":

			baseurl=["/db/render_grouptable","?"]							
			baseurl.append("&groupname=%s"%groupname)
			baseurl.append("&pos_%s=0"%groupname)
			baseurl.append("&wfid=%s"%args["wfid"][0])
			baseurl.append("&%s=%s"%("sort_%s"%groupname,out[i]))
			baseurl.append("&%s=%s"%("reverse_%s"%groupname,reverse))
			baseurlstr = "".join(baseurl)

			r = "javascript:makeRequest('%s&%s=%s&zone=%s&viewinit=%s','%s')"%(baseurlstr,key,ipos - perpage,"zone_%s"%groupname,groupname,"zone_%s"%groupname)

			if vartypes[i] != "":				
				ret.append("\t\t<th><span class=\"table_span\" onclick=\"%s\">%s</span></th>\n"%(r,vardescs[i]))
			else:
				ret.append("\t\t<th><a href=\"%s\">(%s)</a></th>\n"%(r,out[i]))

	ret.append("\t</tr>\n")
	
	modulo=0
	
	if not perpage:
		perpage = len(recordids)
	
	for id in recordids[pos:pos+perpage]:
		tabularview = render_tabularview(id,out,vartypes,vardescs,modulo=modulo,ctxid=ctxid)
		ret.append(" ".join(tabularview))
		modulo=modulo+1

	ret.append("</table>\n")
	
#	ret.append(" ".join(nav))
	
	ret.append("</div>\n\n")

	ret.append("</div>")
	
#	if direct:
#		return ret
#	else:
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
	
	
	
def singleheader(title):
	ret = """
	
	<div class="navtree">

	<table cellpadding="0" cellspacing="0" class="navtable">
	</table>

	</div>
	
	<div class="switchcontainer">

		<div class="switchbutton" id="button_mainview"><a href="">%s</a></div>

	</div>"""%title
	return ret
	
################################################### 
## HTML FUNCTIONS #################################
###################################################

def loginpage(redir):
	"""Why is this a function ?	 Just because. Returns a simple login page."""
	ret = []
	ret.append(html_header("EMEN2 Login"))
	ret.append(singleheader("EMEN2 Login"))
	page = """
<div class="switchpage" id="page_mainview">
	<h3>Please Login:</h3>
	<div id="zone_login">
		<form action="/db/login" method="POST">
			<input type="hidden" name="fw" value="%s"; />
			<span class="inputlabel">Username:</span> 
			<span class="inputfield"><input type="text" name="username" /></span><br />
			<span class="inputlabel">Password:</span>
			<span class="inputfield"><input type="password" name="pw" /></span><br />
			<span class="inputcommit"><input type="submit" value="submit" /></span>
		</form>
	</div>
</div>
"""%(redir)

	ret.append(page)
	ret.append(html_footer())

	return " ".join(ret)


def html_header(name,init=None):
	"""Common header block, includes <body>"""
	
	ret = []
	
	ret.append("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">	
	
<html>

<head>

<title>
%s
</title>

<link rel="StyleSheet" href="/main.css" type="text/css" />


<script type="text/JavaScript" src="/niftycube.js"></script>
<script type="text/javascript" src="/switch.js"></script>
<script type="text/javascript" src="/ajax.js"></script>
<script type="text/javascript" src="/tile.js"></script>


</head>

<body onLoad="javascript:init();"""%name)

	if init:
		ret.append(str(init))
		
	ret.append("""">

<div id="title">
	<a href="/db/">
	<img id="toplogo" src="/images/logo_trans.png" alt="NCMI" /> National Center for Macromolecular Imaging
	</a>
</div>


<div class="nav_table"> 
	<div class="nav_tableli" id="nav_first"><a href="/db/record?name=0">Browse Database</a></div>
	<div class="nav_tableli" id="nav_middle1"><a href="/db/queryform">Query Database</a></div>
	<div class="nav_tableli" id="nav_middle2"><a href="/db/workflow">My Workflow</a></div>
	<div class="nav_tableli" id="nav_middle3"><a href="/db/paramdefs">Parameters</a></div>
	<div class="nav_tableli" id="nav_last"><a href="/db/recorddefs">Protocols</a></div>
</div>


<div id="content">
	""")
	
	return " ".join(ret)

def html_navbar():
	"""Top navigation bar"""
	return """
	"""

def html_footer():
	"""Common header block, includes </body>"""
	return """

</div>

<div id="bottom">

<img id="bottomlogo" src="/images/logo_alt_sm.gif" alt="Baylor College of Medicine" />	

<!-- -->

Loggged in as: <br />

Hosted by <a href="http://ncmi.bcm.tmc.edu">NCMI</a>&nbsp;&nbsp;Phone: 713-798-6989 &nbsp;&nbsp;Fax: 713-798-1625<br />
Room N421 Alkek Building, One Baylor Plaza, Houston, TX, 77030<br />
Please mail comments/suggestions to: <a href="mailto:htu@bcm.tmc.edu">WEBMASTER</a><br /><br />

</div>

</body>
</html>
	"""



def html_workflow(path,args,ctxid,host):
	global db

	ftn=db.getparamdefnames()

	ret=[html_header("EMEN2 Workflow")]

	ret.append(singleheader("Workflow"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Workflow</h2><br />")	

	all = []
	wf = db.getworkflow(ctxid)
	
	for i in wf:
		wfdict = i.items_dict()
		ret.append("workflow: %s <br />query: %s<br />results: %s<br />\n\n"%(wfdict["wfid"],wfdict["longdesc"],wfdict["resultcount"]))

		ret.append("<a href=\"javascript:toggle('workflowdict_%s');\">+ contents:</a><br /><div id=\"workflowdict_%s\" style=\"display:none\">"%(wfdict["wfid"],wfdict["wfid"]))
		ret.append(str(i.items_dict()))
		ret.append("</div><br />")
			
#	for i in all:
#		ret.append("<br />%s<br />"%i)
	
	# stuff goes here

	ret.append("</div>")

	ret.append(html_footer())
	return "".join(ret)


def html_stub(path,args,ctxid,host):
	global db

	ftn=db.getparamdefnames()

	ret=[html_header("EMEN2")]

	ret.append(singleheader("Page"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Page Title</h2><br />") 

	# stuff goes here

	ret.append("</div>")

	ret.append(html_footer())
	return "".join(ret)


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
	
def html_record_dicttable(dict,proto,viewdef,missing=0):
	"""Produce a table of values in 'cols' columns"""

#	print "dict: %s \n %s"%(dict.recid,dict)

	ret = []
	# fixme: removed comments_text
	special = ["rectype","creator","creationtime","permissions","title","identifier","modifytime","modifyuser","parent","comments_text","comments","file_image_binary"]
	
	# Standard fields for all records
	ret.append("\n\n<div class=\"standardfields\">\n")
	ret.append("<a href=\"javascript:toggle('standardtable')\">&raquo;</a><br />")

	ret.append("<table class=\"standardtable\" id=\"standardtable\" cellspacing=\"0\" cellpadding=\"5\">")

	ret.append("<tr><td class=\"standardtable_shaded\" id=\"standardtable_rightborder\">Created: %s (%s)</td></tr>"%(dict["creationtime"],dict["creator"]))

	ret.append("<tr><td class=\"standardtable_shaded\">Modified: %s (%s)</td></tr>"%(dict["modifytime"],dict["modifyuser"]))

	if dict["comments_text"]: ret.append("<tr><td colspan=\"2\"><span id=\"comments_main\">Comments: %s</span></td></tr>"%dict["comments_text"])

	ret.append("<tr><td colspan=\"2\"><a href=\"javascript:toggle('comments_history')\">+ History:</a><br /><span id=\"comments_history\">")
	comments = dict["comments"]
	for i in comments: 
		ret.append("%s<br />"%str(i))
	ret.append("</span></td></tr>")

	ret.append("<tr><td colspan=\"2\"><a href=\"javascript:toggle('comments_permissions')\">+ Permissions:</a><br /><span id=\"comments_permissions\">")
	perm_labels = ["read","write","full","admin"]
	count = 0
	try:
		for i in dict["permissions"]:
			ret.append("%s: %s<br />"%(str(perm_labels[count]),str(i))) 
			count = count+1
	except:
		pass
	ret.append("</span></td></tr>")

#	ret.append("<tr><td colspan=\"2\"></td></tr>")

	ret.append("<tr><td colspan=\"2\">+ Views: ")
	ret.append("<a href=\"javascript:hideclass('recordview');qshow('dicttable');\">params</a> ")

	k = viewdef.keys()
	k.reverse()
	for i in k:
		j = re.sub("view","",i)
		ret.append("<a href=\"javascript:qhide('dicttable');hideclass('recordview');qshow('recordview_%s');\">%s</a> "%(i,j))
	ret.append("</td></tr>")


	ret.append("<tr><td colspan=\"2\"><a href=\"\">+ Append comment</a></td></tr>")
	
	ret.append("<tr><td colspan=\"2\"><a href=\"\"><a href=\"javascript:toggle('addchild')\">+ Add child</a>")
	ret.append("<span style=\"display:none\" id=\"addchild\"><ul>")
	ftn=db.getrecorddefnames()
	for i in ftn:
		ret.append("<li><a href=\"/db/newrecord?rdef=%s&parent=%s\">%s</a></li>"%(i,dict.recid,i))
		
	ret.append("</span></td></tr>")

	ret.append("</table>")

	bdo = dict["file_image_binary"]
	if bdo:
		if bdo[0:3] == "bdo":
			ret.append("<div class=\"viewbinary\"><a href=\"/db/tileimage/%s\">View Binary Data</a></div>"%bdo[4:])
		else:
			ret.append("<div class=\"viewbinary\"><a href=\"\">Download Binary Data</a></div>")

	for k,v in dict.items():
		try: item=db.getparamdef(str(k))
		except: continue
		ret.append("""\n\n
		<div id="tooltip_%s" class="tooltip">
		Parameter Name: %s<br />Variable type: %s<br />Description: %s<br />Property: %s
		</div>\n\n"""%(item.name,item.name,item.vartype,item.desc_short,item.property))

	ret.append("</div>")

# VIEWS 
	re1 = "(\$\$(\w*)(?:=\"(.*)\")?)[\s<]?"
	re2 = "(\$\#(\w*))\s"
	p = re.compile(re1)
	p2 = re.compile(re2)

#	print re2

#	viewdef["mainview"]

	for viewtype in viewdef.keys():
		q = viewdef[viewtype]
		regexresultvalues = p.findall(q)
		regexresultnames = p2.findall(q)

		#print "rrn: %s"%regexresultnames
		#print "rrv: %s"%regexresultvalues

		for i in regexresultnames:
			try: item=db.getparamdef(str(i[1]))
			except: continue
			#print "n: " + i[0]
			#print "item.desc_short for %s: %s \n\n%s\n\n"%(i[1],item.desc_short,q)
			q = re.sub(re.sub("\$","\$",i[0]),item.desc_short,q)
				
				
		for i in regexresultvalues:
			print "v: %s"%i[0]
			
			try:
				value = dict[i[1]]
			except:
				value = i[2]
			if not value:
				value = ""

			popup = "onmouseover=\"tooltip_show('tooltip_%s');\" onmouseout=\"tooltip_hide('tooltip_%s');\""%(i[1],i[1])

			repl = re.sub("\$","\$",i[0])
			q = re.sub(repl + r"\b","<span class=\"viewparam\" %s>%s</span>"%(popup,value),q)


		if viewtype != "defaultview":
			hidden = "style=\"display:none\""
		else:
			hidden = ""
			
		ret.append("\n\n<div class=\"recordview\" %s id=\"recordview_%s\">%s</div>"%(hidden,viewtype,q))





	# Fields for a particular record type
	ret.append("\n<div class=\"dicttable\" id=\"dicttable\">")

	ret.append("\n\n<table cellspacing=\"0\" cellpadding=\"0\">\n")
	skipped = 0
	for k,v in dict.items():
		try: item=db.getparamdef(str(k))
		except: continue

		js = """onmouseover="tooltip_show('tooltip_%s');" onmouseout="tooltip_hide('tooltip_%s');" """%(item.name,item.name)

		if missing and v == "":
			skipped = 1
		elif not special.count(k):
			ret.append("\t<tr>\n\t\t<td class=\"pitemname\" id=\"td_%s\" %s><a href=\"%s%s\">%s</a></td>\n\t\t<td>%s</td>\n\t</tr>\n"%(item.name,js,proto,k,item.desc_short,v))
		
	ret.append("</table>")

	# Unused record type fields
	if skipped:
		ret.append("\n\n<div class=\"emptyfields\">Emtpy fields: ")
		for k,v in dict.items():
			try:
				item=db.getparamdef(str(k))
				if v == "":
					ret.append("<a href=\"%s%s\">%s</a>, \n"%(proto,k,item.desc_short))
			except:
				pass
		ret.append("\n</div>")

	ret.append("\n</div>\n")

	return "".join(ret)
	

	

		
def html_home():
	ret=[html_header("EMEN2 Home Page")]
	
	ret.append(singleheader("Home"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("""<h2>EMEN2 Demo Page!!!</h2>
	Available tasks:<br />
	<ul>
		<li><a href="/db/record?name=0">Browse Records</a></li>
		<li><a href="/db/queryform">Query Database</a></li>
		<li><a href="/db/records">List of all Records</a></li>
		<li><a href="/db/paramdefs">List of Defined Experimental Parameters (ParamDef)</a></li>
		<li><a href="/db/recorddefs">List of Defined Experimental Protocols (RecordDef)</a></li>
		<li><a href="/db/users">List of Users</a></li>
	</ul>
	
	<br /><br />
	
	<ul>
		<li><a href="/db/newuser">Add New User</a></li>
		<li><a href="/db/newuserqueue">Approve New Users</a></li>
		<li><a href="/db/newparamdef">Define New Experimental Parameter</a></li>
		<li><a href="/db/newrecorddef">Describe new Experimental Protocol</a></li>
	</ul>""")
	
	
	ret.append("</div>")
	
	ret.append(html_footer())
	
	return "".join(ret)

def html_tileimage(path,args,ctxid,host):
	global db

	name,fpath=db.getbinary(path[1],ctxid,host)
	fpath=fpath+".tile"
	
	if not args.has_key("x") :
		dims=get_tile_dim(fpath)
		dimsx=[i[0] for i in dims]
		dimsy=[i[1] for i in dims]
		if not args.has_key("level") : lvl=len(dims)
		else: lvl=int(args["level"][0])
		
		ret=[]
		
		ret.append("""

		<html>

		<head>

		<title>
		Tile Viewer
		</title>

		<link rel="StyleSheet" href="/main.css" type="text/css" />
		
		<script type="text/JavaScript" src="/niftycube.js"></script>
		<script type="text/javascript" src="/switch.js"></script>
		<script type="text/javascript" src="/ajax.js"></script>

		<script type="text/javascript">
		var isdown=false;
		var nx=%s
		var ny=%s
		var level=nx.length-1

		function tileinit() {
			setsize(nx[level]*256,ny[level]*256);
			var outdiv=document.getElementById("outerdiv");
			outdiv.onmousedown = mdown;
			outdiv.onmousemove = mmove;
			outdiv.onmouseup = mup;
			outdiv.ondragstart = function() { return false; }
			recalc();
		}

		function tofloat(s) {
			if (s=="") return 0.0;
			return parseFloat(s.substring(0,s.length-2));
		}

		function zoom(lvl) {
			if (lvl==level || lvl<0 || lvl>=nx.length) return;
			indiv=document.getElementById("innerdiv");
			x=tofloat(indiv.style.left);
			y=tofloat(indiv.style.top);

			outdiv=document.getElementById("outerdiv");
			cx=outdiv.clientWidth/2.0;
			cy=outdiv.clientHeight/2.0;

			setsize(nx[lvl]*256,ny[lvl]*256);

			scl=Math.pow(2.0,level-lvl)
			indiv.style.left=cx-((cx-x)*scl);
			indiv.style.top=cy-((cy-y)*scl);

			for (i=indiv.childNodes.length-1; i>=0; i--) indiv.removeChild(indiv.childNodes[i]);
			level=lvl
			recalc();
		}

		function zoomout() {
			zoom(level+1);
		}

		function zoomin() {
			zoom(level-1);
		}

		function mdown(event) {
			if (!event) event=window.event;		// for IE
			indiv=document.getElementById("innerdiv");
			isdown=true;
			y0=tofloat(indiv.style.top);
			x0=tofloat(indiv.style.left);
			mx0=event.clientX;
			my0=event.clientY;
			return false;
		}

		function mmove(event) {
			if (!isdown) return;
			if (!event) event=window.event;		// for IE
			indiv=document.getElementById("innerdiv");
			indiv.style.left=x0+event.clientX-mx0;
			indiv.style.top=y0+event.clientY-my0;
			recalc();
		}

		function mup(event) {
			if (!event) event=window.event;		// for IE
			isdown=false;
			recalc();
		}

		function recalc() {
			indiv=document.getElementById("innerdiv");
			x=-Math.ceil(tofloat(indiv.style.left)/256);
			y=-Math.ceil(tofloat(indiv.style.top)/256);
			outdiv=document.getElementById("outerdiv");
			dx=outdiv.clientWidth/256+1;
			dy=outdiv.clientHeight/256+1;
			for (i=x; i<x+dx; i++) {
				for (j=y; j<y+dy; j++) {
					if (i<0 || j<0 || i>=nx[level] || j>=ny[level]) continue;
					nm="im"+i+"."+j
					var im=document.getElementById(nm);
					if (!im) {
						im=document.createElement("img");
						im.src="/db/tileimage/%s?level="+level+"&x="+i+"&y="+j;
						im.style.position="absolute";
						im.style.left=i*256+"px";
						im.style.top=j*256+"px";
						im.setAttribute("id",nm);
						indiv.appendChild(im);
					}
				}
			}
		}

		function setsize(w,h) {
			var indiv=document.getElementById("innerdiv");
			indiv.style.height=h;
			indiv.style.width=w;
		}
		</script>

		</head>

		<body onLoad="javascript:init();tileinit();">

		<div id="title">
			<img id="toplogo" src="/images/logo_trans.png" alt="NCMI" /> National Center for Macromolecular Imaging
		</div>


		<div class="nav_table"> 
			<div class="nav_tableli" id="nav_first"><a href="/db/record?name=0">Browse Database</a></div>
			<div class="nav_tableli" id="nav_middle1"><a href="/db/queryform">Query Database</a></div>
			<div class="nav_tableli" id="nav_middle2"><a href="/db/workflow">My Workflow</a></div>
			<div class="nav_tableli" id="nav_middle3"><a href="/db/paramdefs">Parameters</a></div>
			<div class="nav_tableli" id="nav_last"><a href="/db/recorddefs">Protocols</a></div>
		</div>


		<div id="content">"""%(str(dimsx),str(dimsy),path[1]))


		ret.append(singleheader("Tile Viewer"))
		ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

		ret.append("""
		<div id="outerdiv">
			<div id="innerdiv">LOADING</div>
		</div>

		<br><br><div id="dbug"></div>


		<button onclick=zoomout()>Zoom -</button><button onclick=zoomin()>Zoom +</button><br>
		""")

		ret.append("</div>")

		ret.append(html_footer())
		return " ".join(ret)
		
	try: ret=get_tile(fpath,int(args["level"][0]),int(args["x"][0]),int(args["y"][0]))
	except: return "Invalid tile"
	return ret

def html_getbinarynames(path,args,ctxid,host):
	global gb
	
	ret = []
	ret.append(html_header("Binary Ids"))
	ret.append(singleheader("Binary Ids"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	ret.append("<h2>Binary Identifiers</h2>")

	for i in db.getbinarynames():
		for j in range(0,i[1]):
			k = str(i[0])+"%05X"%j
			r = db.getbinary(k,ctxid)
			ret.append("%s : %s "%(k,str(r)))
			if os.path.exists("%s.tile"%r[1]):
				ret.append("<a href=\"/db/tileimage/%s\">View in browser</a>"%k)
			ret.append("<br />")

	ret.append("</div>")

	ret.append(html_footer())
	return " ".join(ret)

def html_paramdefs(path,args,ctxid,host):
	global db
	
	ftn=db.getparamdefnames()
	
	ret=[html_header("EMEN2 ParamDefs")]
		
	ret.append(singleheader("Parameter Definitions"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Registered Parameters</h2><br />%d defined:"%len(ftn))	
	
	ret.append(html_htable(ftn,3,"/db/paramdef?name="))

	ret.append("</div>")

	ret.append(html_footer())
	return "".join(ret) 

def html_paramdef(path,args,ctxid,host):
	global db
	
	item=db.getparamdef(args["name"][0])
	
	ret=[html_header("EMEN2 ParamDef Description")]
	
	ret.append(singleheader("Parameter Definition"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Experimental Parameter (ParamDef): <i>%s</i></h2>"%item.name)
	
	parents=db.getparents(item.name,keytype="paramdef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<h2>Parents:</h2> ")
		for p in parents:
			ret.append("<a href=\"/db/paramdef?name=%s\">%s</a> "%(p,p))
	
	children=db.getchildren(item.name,keytype="paramdef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<h2>Children:</h2>")
		for c in children:
			ret.append("<a href=\"/db/paramdef?name=%s\">%s</a> "%(c,c))
	
	ret.append("""\n\n<table><tr><td>Name</td><td>%s</td></tr>
	<tr><td>Variable Type</td><td>%s</td></tr>
	<tr><td>Short Description</td><td>%s</td></tr>
	<tr><td>Long Description</td><td>%s</td></tr>
	<tr><td>Property</td><td>%s</td></tr>
	<tr><td>Default Units</td><td>%s</td></tr>
	<tr><td>Creator</td><td>%s (%s)</td></table><a href="/db/newparamdef?parent=%s">Add a new child parameter</a>"""%(
	item.name,item.vartype,item.desc_short,item.desc_long,item.property,item.defaultunits,item.creator,item.creationtime,item.name))
	
	ret.append("</div>")
	
	ret.append(html_footer())
	
	return "".join(ret)

def html_newparamdef(path,args,ctxid,host):
	"""Add new ParamDef form. Also does the actual ParamDef insertion"""	

	ret=[html_header("EMEN2 Add Experimental Parameter")]
	
	ret.append(singleheader("Add Parameter"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h1>Add Experimental Parameter</h1><br>")


	if args.has_key("name") :
		try: 
			ft=DB.ParamDef(name=args["name"][0],vartype=args["vartype"][0],desc_short=args["desc_short"][0],desc_long=args["desc_long"][0],property=args["property"][0],defaultunits=args["defaultunits"][0])
			db.addparamdef(ft,ctxid,host)
		except Exception,e:
			ret.append("Error adding Parameter '%s' : <i>%s</i><br><br>"%(str(args["name"][0]),e))	# Failed for some reason, fall through so the user can update the form
			return "".join(ret)
		
		if args.has_key("parent") :
			db.pclink(args["parent"][0],args["name"][0],"paramdef")
			
		# ParamDef added sucessfully
		ret.append('<br><br>New Parameter <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["name"][0]))
		ret.append("</div>")
		ret.append(html_footer())
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		
		ret.append(html_form(method="GET",action="/db/newparamdef",items=(("","parent","hidden"),("Name:","name","text"),
		("Variable Type","vartype","select",("int","float","string","text","url","image","binary","datetime","link","child")),
		("Short Description","desc_short","text"),("Long Description","desc_long","textarea","",(60,3)),
		("Physical Property","property","select",DB.valid_properties),("Default Units","defaultunits","text")),args=args))

		ret.append("</div>")
		ret.append(html_footer())

		return "".join(ret)

def html_recorddefs(path,args,ctxid,host):
	global db
	
	ftn=db.getrecorddefnames()
	for i in range(len(ftn)):
		ftn[i]=(ftn[i],len(db.getindexbyrecorddef(ftn[i],ctxid)))
		
	ret=[html_header("EMEN2 Record Definitions")]
	
	ret.append(singleheader("Record Definitions"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Registered Record Definition</h2><br>%d defined:"%len(ftn))
	ret.append(html_htable2(ftn,3,"/db/recorddef?name="))

	ret.append("</div>")

	ret.append(html_footer())
	return "".join(ret)

def html_recorddef(path,args,ctxid,host):
	global db
	
	item=db.getrecorddef(args["name"][0],ctxid)
	
	ret=[html_header("EMEN2 Protocol Description")]
	
	ret.append(singleheader("Protocol Definition"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Experimental Protocol (RecordDef): <i>%s</i></h2><br>"%item.name)
	
	parents=db.getparents(item.name,keytype="recorddef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<h2>Parents:</h2>")
		for p in parents:
			ret.append('<a href="/db/recorddef?name=%s">%s</a> '%(p,p))
	
	children=db.getchildren(item.name,keytype="recorddef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<h2>Children:</h2> ")
		for c in Children:
			ret.append('<a href="/db/recorddef?name=%s">%s</a> '%(c,c))

	ret.append("<br><br>Parameters:<br>")
	ret.append(html_dicttable(item.params,"/db/paramdef?name="))
#	ret.append("<br>Default View:<br><form><textarea rows=10 cols=60>%s</textarea></form>"%item.mainview)
	
	re1= '<([^> ]*) ([^=]*)="([^"]*)" */>'
	rp1=r'<i>\3=None</i>'
	re2= '<([^> ]*) ([^=]*)="([^"]*)" *>([^<]*)</([^>]*)>'
	rp2=r'<i>\3=\4</i>'

	ret.append("<br><b>Experimental Protocol:</b><br>%s<br><br>"%re.sub(re2,rp2,re.sub(re1,rp1,item.mainview)))
	for i in item.views.keys():
		ret.append("<b>%s</b>:<br>%s<br><br>"%(i,re.sub(re2,rp2,re.sub(re1,rp1,item.views[i]))))
	ret.append('<br><br><a href="/db/newrecord?rdef=%s">Add a New Record</a><br><a href="/db/newrecorddef?parent=%s">Add a New Child Protocol</a><br>'%(
	item.name,item.name))
	ret.append('<br>Records (250 max shown):<br>')
	itm=list(db.getindexbyrecorddef(args["name"][0],ctxid))
	itm.sort()
	if (len(itm)>250) : itm=itm[:249]
	ret.append(html_htable(itm,6,"/db/record?name="))
	
	ret.append("</div>")
	
	ret.append(html_footer())
	
	return "".join(ret)

def html_newrecorddef(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 Add Protocol Definition")]
	
	ret.append(singleheader("New Protocol Definition"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Add Protocol Definition</h2><br>")
	if args.has_key("name") :
		try: 
			rd=DB.RecordDef()
			rd.name=args["name"][0]
			rd.mainview=args["mainview"][0]
			rd.views["oneline"]=args["oneline"][0]
			rd.views["summary"]=args["summary"][0]
			if args.has_key("private") : rd.private=1
			else: rd.private=0
			rd.findparams()
			db.addrecorddef(rd,ctxid,host)
		except Exception,e:
			traceback.print_exc()
			ret.append("Error adding RecordDef '%s' : <i>%s</i><br><br>"%(str(args["name"][0]),e))	# Failed for some reason, fall through so the user can update the form
			return "".join(ret)
			
		if args.has_key("parent") :
			db.pclink(args["parent"][0],args["name"][0],"recorddef")
		
		# RecordDef added sucessfully
		ret+=['<br /><br />New Protocol <i>%s</i> added.<br /><br />Press <a href="/db">here</a> for main menu.'%str(args["name"][0])]
		ret.append("</div>")
		ret.append(html_footer())
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		ret.append(html_form(method="GET",action="/db/newrecorddef",items=(("","parent","hidden"),("Name:","name","text"),
		("Experiment Description","mainview","textarea","",(80,16)),("Summary View","summary","textarea","",(80,8)),
		("One Line View","oneline","textarea","",(80,4)),("Private Access","private","checkbox")),args=args))
		ret.append("</div>")
		ret.append(html_footer())
	
		return "".join(ret)
	
	
def html_records(path,args,ctxid,host):
	
	ftn=db.getrecordnames(ctxid,host=host)
	ret=[html_header("EMEN2 Records")]
	
	ret.append(singleheader("All Records"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>All accessible records</h2>")
	ret.append(html_htable(ftn,3,"/db/record?name="))

	ret.append("</div>")
	ret.append(html_footer())
	return "".join(ret)


def html_queryform(path,args,ctxid,host):
	ret=[html_header("EMEN2 DB Query")]
	
	ret.append(singleheader("Database Query"))

	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append(	 html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea","find child of 71",(80,8))))	)

	ret.append("</div>")

	ret.append(html_footer())

	return "".join(ret)


def groupsettolist(groups):
	groupl = {}
	for i in groups.keys():
		glist = list(groups[i])
		groupl[i] = glist
	return groupl		

def html_debug(path,args,ctxid,host):
	ret = []

	global db

	ftn=db.getparamdefnames()

	ret=[html_header("EMEN2")]

	# stuff usually specified by singleheader
	ret.append("""<div class="navtree">
	<table cellpadding="0" cellspacing="0" class="navtable">
	</table>
	</div>""")
	
	
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("\t<div class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">Main View</a></div>\n")
	ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")
	ret.append("\t<div class=\"switchbutton\" id=\"button_scan\"><a href=\"javascript:switchid('scan')\">Scan</a></div>\n")
	ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")
	ret.append("\n</div>")

	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")



	ret.append("<h2>Page Title</h2><br />") 

	# stuff goes here


	ret.append("path: %s <br />"%path)
	ret.append("args: %s <br />"%args)
	
	url=[path[0]]
	for i in args.keys():
		url.append("&%s=%s"%(i,args[i][0],))
	ret.append("".join(url))
	
	ret.append("<br />")
	
	if args.has_key("yes"):
		ret.append("has key yes")
		
	if args.has_key("list"):
		z = args["list"][0].split(',')
		ret.append("<br>list: %s<br>"%args["list"][0])
		for i in z:
			ret.append("<br>z %s<br>"%i)

	ret.append("</div>")


#	ret.append("\n\n<div class=\"switchpage\" id=\"page_scan\">")
#	ret.append("\t<h1 class=\"switchheader\" id=\"header_scan\">scan</h1>\n")
		
#	ajaxargs = args
#	ajaxargs["zone"] = ["zone_scan"]
	ret.append(encapsulate_render_grouptable(path,args,ctxid,host))
		
#	ret.append("</div>")
		
#	ajaxargs["zone"] = ["zone2"]
#	ret.append("""
#	<div id="zone2">
#	%s
#	</div>
#	"""%html_rendergrouptable(path,ajaxargs,ctxid,host))

	ret.append("</div>")

	ret.append(html_footer())

	return "".join(ret)

def clearworkflowcache(ctxid):
	global db 
	
	wflist = db.getworkflow(ctxid)
	for wf in wflist:
		wfdict = wf.items_dict()
		if wfdict["wftype"] == "recordcache" or wfdict["wftype"] == "querycache":
			db.delworkflowitem(wf.wfid,ctxid)

def encapsulate_render_grouptable(path,args,ctxid,host):
	ret = []
	
	if args.has_key("groupname"):
		groupname = args["groupname"][0]
	
	
	ret.append("\n\n<div class=\"switchpage\" id=\"page_%s\">"%groupname)
	ret.append("\t<h1 class=\"switchheader\" id=\"header_%s\">%s</h1>\n"%(groupname,groupname))
	
	
	
	r = html_render_grouptable(path,args,ctxid,host)
	ret.append("".join(r))
	
	ret.append("</div>")
	return " ".join(ret)


def html_ajaxdebug(path,args,ctxid,host):
	ret = []
	
	prev = str(int(args["true"][0]) - 1)	
	next = str(int(args["true"][0]) + 1)
	
	zone = str(args["zone"][0])
	
	ret.append("""<span style="cursor: pointer; text-decoration: underline" onclick="makeRequest('/db/ajaxdebug?true=%s&false=0&zone=%s','%s')">Prev is %s</span> --- """%(prev,zone,zone,prev))
	
	ret.append("""<span style="cursor: pointer; text-decoration: underline" onclick="makeRequest('/db/ajaxdebug?true=%s&false=0&zone=%s','%s')">Next is %s</span>"""%(next,zone,zone,next))
	
	ret.append(str(args))
	
	return " ".join(ret)
	

def html_query(path,args,ctxid,host):
	global db
	
	query = str(args["query"][0])
	
	if args.has_key("wfid"):
		wf = db.getworkflowitem(int(args["wfid"][0]),ctxid)
#		wfdict = wf.items_dict()
		groupl = wf["appdata"]
		
	else:
		print "performing query... %s"%str(args["query"][0])
		raw = db.query(str(args["query"][0]),ctxid)
		result = raw['data']
		resultcount = len(result)
		groups = db.groupbyrecorddef(result,ctxid)
		groupl = groupsettolist(groups)

		if query.find("plot") != -1 or query.find("histogram") != -1:
#			print raw
			plotfile = render_plot(query,raw)
			isplot = True
		else:
			plotfile = ""
			isplot = False
	
		clearworkflowcache(ctxid)
	
		with = {'wftype':'querycache','desc':str(args["query"][0]),'longdesc':str(args["query"][0]),'resultcount':resultcount,'appdata':groupl,'plotfile':plotfile}
		newwf = db.newworkflow(with)
		wfid = db.addworkflowitem(newwf,ctxid)
		
#		print "wfid: %s	  wfid as list: %s\n"%(wfid,list(str(wfid)))
		
		args["wfid"]= [str(wfid)]


	ret = []

	if args.has_key("viewinit"):
		init="switchid('%s');"%str(args["viewinit"][0])
		ret=[html_header("EMEN2 Query Results",init=init)]
	elif isplot:
		init="switchid('allview');"
		ret=[html_header("EMEN2 Query Results",init=init)]
	else:
		ret.append(html_header("EMEN2 Query Results",init="showallids();"))
	
	
	# stuff usually specified by singleheader
	ret.append("""<div class="navtree">
	<table cellpadding="0" cellspacing="0" class="navtable">
	</table>
	</div>""")
	
	
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("\t<div class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">Edit Query</a></div>\n")
	ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")


	if isplot:
		
		ret.append("\t<div class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:switchid('allview')\">Graph</a></div>\n")
		ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")
		ret.append("\t<div class=\"switchbutton\" id=\"button_rawresult\"><a href=\"javascript:switchid('rawresult');\">Raw Result</a></div>\n")

	else:
		
		ret.append("\t<div class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:showallids()\">All Results</a></div>\n")
		ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")
		
		ret.append(render_groupedhead(groupl,ctxid=ctxid))

	ret.append("\n</div>")
	
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append(	 html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea",str(args["query"][0]),(80,8))))  )

	ret.append("</div>")
	
	args["wfid"] = [str(wfid)]

	if plotfile:
		ret.append("<div class=\"switchpage\" id=\"page_allview\">")
		ret.append("<img src=\"%s\" />"%plotfile)
		ret.append("</div>")

		ret.append("<div class=\"switchpage\" id=\"page_rawresult\">")
		ret.append("%s"%raw)
		ret.append("</div>")
		
	else:
		for i in groupl.keys():
			args["groupname"] = [str(i)]
			args["wfid"] = [str(wfid)]
			ret.append(encapsulate_render_grouptable(path,args,ctxid,host))

#	ret.append(render_groupedlist(path,args,ctxid,host,groupl=groupl))

#	ret.append("<script type=\"text/javascript\">showallids();</script>")


	ret.append(html_footer())

	return " ".join(ret)

def html_record(path,args,ctxid,host):
	global db
	
	name = int(args["name"][0])
		
	item=db.getrecord(name,ctxid)
	queryresult = db.getchildren(name,ctxid=ctxid)

	
#	if args.has_key("viewtype"):
#		viewtype = args["viewtype"]
#	else:
#		viewtype = "defaultview"
	
#	try:	
	view=db.getrecorddef(item["rectype"],ctxid)
	viewdef = view.views
	
	if not viewdef.has_key("defaultview"):
		viewdef["defaultview"] = view.mainview
	else:
		viewdef["protocol"] = view.mainview

# Let's remove onelineview, tabularview
	try:
		del viewdef["tabularview"]
	except:
		pass
	try:
		del viewdef["onelineview"]
	except:
		pass
#	except:
#		viewdef=db.getrecorddef(item["rectype"],ctxid).views["onelineview"]

	
#	result = db.query(str(args["query"][0]),ctxid)['data']
	resultcount = len(queryresult)
	groups = db.groupbyrecorddef(queryresult,ctxid)
	groupl = groupsettolist(groups)

	clearworkflowcache(ctxid)

	with = {'wftype':'recordcache','desc':"record cache",'longdesc':"record cache",'resultcount':resultcount,'appdata':groupl}
	newwf = db.newworkflow(with)
	wfid = db.addworkflowitem(newwf,ctxid)
	
	args["wfid"] = [str(wfid)]
	
		
#	groups = db.groupbyrecorddef(queryresult,ctxid)
#	groupl = groupsettolist(groups)

	if args.has_key("viewinit"):
		init="switchid('%s')"%str(args["viewinit"][0])
		ret=[html_header("EMEN2 Record",init=init)]
	else:
		ret=[html_header("EMEN2 Record")]
	
	ret.append(parent_tree(name,ctxid=ctxid))
	
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("\t<div class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">%s (%s)</a></div>\n"%(item["recname"],item["rectype"]))
	
	if queryresult:
		ret.append("\t<div class=\"switchshort\">&raquo;</div>")
		ret.append("\t<div class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:showallids()\">All Children</a></div>\n")
		ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")

#		print "\ngroups:%s\ngroupl:%s\n\n"%(groups,groupl)

		ret.append(render_groupedhead(groups,ctxid=ctxid))

	ret.append("\n\n</div>")

	ret.append("\n\n<div class=\"switchpage\" id=\"page_mainview\">")
	ret.append(html_record_dicttable(item,"/db/paramdef?name=",viewdef,missing=1))
	ret.append("\n</div>\n\n")

	ret.append(render_groupedlist(path,args,ctxid,host))

	ret.append(html_footer())
	
	return " ".join(ret)

def html_newrecord(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 Add Record")]
	
	ret.append(singleheader("Add Record"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h1>Add Record</h1><br>")
	
	if args.has_key("rdef") :
		rec=db.newrecord(args["rdef"][0],ctxid,host,init=1)
		parm=db.getparamdefs(rec)
		
#		print "Record(	",rec,"	 )"
		bld=[("","rectype","hidden"),("","parent","hidden")]
		for p in rec.keys():
			if p in ("owner","creator","creationtime","comments") or (p!="permissions" and parm[p].vartype in ("child","link")) : continue
			try: bld.append((parm[p].desc_short,p,"text"))
			except: bld.append((p,p,"text"))

		d=rec.items_dict()
		d["rectype"]=args["rdef"][0]
		if args.has_key("parent"):
#			print "adding parent key.. %s"%args["parent"][0]
			d["parent"]=args["parent"][0]
#

# FIXME: temp hack
		d2 = {}
		for i in d.keys():
			if type(d[i]) == str:
				try: d2[i] = d[i].split()[0]
				except: d2[i] = None
			else:
				d2[i] = d[i]

		print "submitting with args: %s"%d
		print "shortened args: %s"%d2
		print "items: %s"%bld
		print "host: %s"%host
		ret.append(html_form(method="POST",action="/db/newrecord",items=bld,args=d2))
		ret.append("</div>")
		ret.append(html_footer())
#		ret.append("</body></html")
		return "".join(ret)

	print "new record args: %s"%args

	if args.has_key("parent"):
		parent = int(args["parent"][0])
		del args["parent"]

	argmap(args)
	rec=db.newrecord(args["rectype"],ctxid,host,init=0)
#	del args["rdef2"]
	rec.update(args)

	rid=db.putrecord(rec,ctxid,host)


	if parent :
		db.pclink(parent,rid,"record",ctxid)

	ret.append('Record add successful.<br />New id: <a href="/db/record?name=%d">%d</a><br><br><a href="/db/index.html">Return to main menu</a>'%(rid,rid))
	
	ret.append("</div>")
	ret.append(html_footer())
		
	return ''.join(ret)
	
def html_users(path,args,ctxid,host):
	global db
	
	ftn=db.getusernames(ctxid,host)
	ret=[html_header("EMEN2 Users")]

	ret.append(singleheader("Users"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Users</h2><br />%d defined:"%len(ftn))
	ret.append(html_htable(ftn,3,"/db/user?uid="))

	ret.append("</div>")
	ret.append(html_footer())
	return "".join(ret)

def html_newuserqueue(path,args,ctxid,host):
	global db
	
	ftn=db.getuserqueue(ctxid,host)
	ret=[html_header("EMEN2 User Queue")]
	
	ret.append(singleheader("New User Queue"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>New Users Waiting Approval</h2><br>%d defined:"%len(ftn))
	ret.append(html_htable(ftn,3,"/db/approveuser?username="))

	ret.append("</div>")

	ret.append(html_footer())
	return "".join(ret)

def html_user(path,args,ctxid,host):
	global db
	
	if not args.has_key("uid") : args["uid"]=args["username"]
	ret=[html_header("EMEN2 User")]
	
	ret.append(singleheader("User"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>User: <i>%s</i></h2><br>"%args["uid"][0])
	
	if args.has_key("username") :
		for k in args.keys(): args[k]=args[k][0]
		item=db.getuser(args["username"],ctxid,host)
		item.__dict__.update(args)
		item.groups=[int(i) for i in args["groups"].split(',')]
		db.putuser(item,ctxid,host)
		ret.append("<br><b>Update successful!</b><br><br>")
	else :item=db.getuser(args["uid"][0],ctxid,host)
	
	item.groups=str(item.groups)[1:-1]
	item.name1=item.name[0]
	item.name2=item.name[1]
	item.name3=item.name[2]
	
	u=db.checkcontext(ctxid,host)
	if u[0]==item.username or -1 in u[1]: pwc='<br><a href="/db/chpasswd?username=%s">Change Password</a>'%args["uid"][0]+"</div>"+html_footer()
	else: pwc="</div>"+html_footer()
	
	return "".join(ret)+html_form(method="GET",action="/db/user",items=(("Username","username","text",14),
		("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
		("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea","",(40,3)),
		("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
		("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16),
		("Groups","groups","text",40)),args=item.__dict__)+pwc

def html_chpasswd(path,args,ctxid,host):
	argmap(args)
	ret=[html_header("EMEN2 Change Password")]
	
	ret.append(singleheader("Change Password"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>User: <i>%s</i></h2><br>"%args["username"])
	
	if args.has_key("password") :
		if args["password"]!=args["password2"] : raise SecurityError,"Passwords do not match"
		db.setpassword(args["username"],args["oldpassword"],args["password"],ctxid,host)
		ret.append('<br><b>Password Changed</b><br><br><a href="/db/index.html">Return Home</a>')
		ret.append("</div>")
		ret.append(html_footer())
		return "".join(ret)

	u=db.checkcontext(ctxid,host)
	
	# root users are permitted to change passwords without the original
	if not -1 in u[1]: 
		itm=(("Username","username","hidden"),
		("Old Password","oldpassword","password",16),("Password","password","password",16),
		("Confirm Password","password2","password",16))
	else :
		itm=(("Username","username","hidden"),("","oldpassword","hidden"),
		("Password","password","password",16),
		("Confirm Password","password2","password",16))
	
	return "".join(ret)+html_form(action="/db/chpasswd",items=itm,args=args)+"</div>"+html_footer()
	
def html_approveuser(path,args,ctxid,host):
	db.approveuser(args["username"][0],ctxid,host)
	return html_newuserqueue(path,args,ctxid,host)
	
def html_newuser(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 New User Form")]
	
	ret.append(singleheader("New User"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h1>New User Application</h1><br>")
	if args.has_key("username") :
		try: 
			for k in args.keys(): args[k]=args[k][0]
			rd=DB.User(args)
			db.adduser(rd)
		except Exception,e:
			traceback.print_exc()
			ret.append("Error adding User '%s' : <i>%s</i><br><br>"%(str(args["username"]),e))	# Failed for some reason, fall through so the user can update the form
			ret.append("</div>")
			return " ".join(ret)
			
		# User added sucessfully
		ret+=['<br><br>New User <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["username"]),"</div>"+html_footer()]
		return " ".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		return "".join(ret)+html_form(action="/db/newuser",items=(("Username","username","text",14),("Password","password","password",14),
			("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
			("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea","",(40,3)),
			("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
			("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16)),args=args)+html_footer()

def html_form(action="",items=(),args={},method="POST"):
	ret=['\n\n<table><form action="%s" method=%s>'%(action,method)]
	for i in items:
		if i[2]=="select" :
			ret.append('\t<tr>\n\t\t<td>%s:</td>\n\t\t<td><select name="%s">'%(i[0],i[1]))
			for j in i[3]:
				if j==args.get(i[1],[""])[0] : ret.append('<option selected>%s</option>'%j)
				else : ret.append('<option>%s</option>'%j)
			ret.append('</select></td>\n\t</tr>\n')
		elif i[2]=="textarea" :
			if len(i)<5 : i=i+(40,10)
			ret.append('\t<tr>\n\t\t<td>%s</td>\n\t\t<td><textarea name="%s" cols="%d" rows="%d">%s</textarea></td>\n\t</tr>\n'%(i[0],i[1],i[4][0],i[4][1],i[3]))
		elif i[2]=="password" :
			if (len(i)<4) : i=i+(20,)
			ret.append('\t<tr>\n\t\t<td>%s</td>\n\t\t<td><input type="%s" name="%s" value="%s" size="%d" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],str(args.get(i[1],"")),int(i[3])))
		elif i[2]=="text" :
			if (len(i)<4) : i=i+(20,)
			ret.append('\t<tr>\n\t\t<td>%s</td><td><input type="%s" name="%s" value="%s" size="%d" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],str(args.get(i[1],"")),int(i[3])))
		elif i[2]=="hidden" :
			ret.append('<input type="hidden" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[1],str(args.get(i[1],""))))
		else:
			ret.append('\t<tr>\n\t\t<td>%s</td><td><input type="%s" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],args.get(i[1],"")))

	ret.append('\t<tr>\n\t\t<td></td>\n\t\t<td><input type="submit" value="Submit" /></td>\n\t</tr>\n</form>\n</table>\n')
	
	return "".join(ret)

















############################################
### PLOT: From Haili's Cheetah interface
############################################

def render_plot(thequery,L,clickable=0, groupby=0):
	data = L['data']
	allx = []
	ally = []
	dataRid = []
	myloc = 1
	figsize=(10,8)
	
	if thequery.find("group"):
		groupby = 1
	
	if groupby == 0:
			allx = data['x']

			pylab.hold(False)
			if len(allx) == 0:
				page = "<h2>No Result Found! Please change your query and try again</h2>"
				return page

			if thequery.find('histogram') >= 0:
				ally = data[0]
				#ax = pylab.subplot(111)				   
				strX = 1

				N = len(allx)
				ind = range(N)
				width = 1
				sc = pylab.bar(ind, ally, width)
				thefigure = sc[0].get_figure()
#				thefigure.set_figsize_inches((6,4))
#				fig = sc.get_figure()
				thefigure.set_figsize_inches(figsize)				
				theaxes = thefigure.get_axes()
				theaxes[0].yaxis.set_major_formatter(FormatStrFormatter('%d'))					  
				pylab.xticks(ind, allx, rotation=45, fontsize=8)
				#pylab.xlim(-width, len(ind))
				if clickable == 1:
					dataRid = ind
			else:
				ally = data['y']
				if clickable == 1:
					   dataRid = data['i']
				else:
					dataRid = []
				sc = pylab.scatter(allx, ally)
	else:
		dotcolor = ['b', 'g', 'r', 'c', 'm', 'y','w', 'k', 'c']
		allcolor=['b', 'g', 'r', 'c', 'm', 'y', '#00ff00', '#800000', '#000080', '#808000', '#800080', '#c0c0c0', '#008080', '#7cfc00', '#cd5c5c', '#ff69b4', '#deb887', '#a52a2a', '#5f9ea0', '#6495ed', '#b8890b', '#8b008b', '#f08080', '#f0e68c', '#add8e6', '#ffe4c4', '#deb887', '#d08b8b', '#bdb76b', '#556b2f', '#ff8c00', '#8b0000', '#8fbc8f', '#ff1493', '#696969', '#b22222', '#daa520', '#9932cc', '#e9967a', '#00bfff', '#1e90ff', '#ffd700', '#adff2f', '#00ffff', '#ff00ff', '#808080', 'w', 'k', 0.3, 0.6, 0.9]

		#allcolor = colors.getColors()
		allshape= ['o', 's', '^', '>', 'v', '<', 'd', 'p', 'h', '8']
		pylab.hold(False)  


		if data == [] or len(data) == 0:
					page = "<h2>No Result Found! Please change your query and try again</h2>"
					return page
		i = 0
		labels = []
		thekeys = []

		if thequery.find('histogram') >= 0:
				   k = 0
				   allx = data['x']
				   ind = range(len(allx))
				   width = 1
				   #ax = pylab.subplot(111)					  

				   #yoff = pylab.arange([0.0] * len(allx))
				   yoff = []
				   for theone in allx:
					   yoff.append(0.0)
				   allsc = []
				   ykeys = []
				   for thekey in data.keys():
					   if type(thekey) == type(1):
						   ykeys.append(thekey)
				   ykeys.sort()
				   pylab.hold(False) 
				   for thekey in ykeys: 
					  if type(thekey) == type(1):
						   myY = data[thekey]
						   sc = pylab.bar(ind, myY, width, bottom=yoff, color=allcolor[k%len(allcolor)])
						   thefigure = sc[0].get_figure()
						   theaxes = thefigure.get_axes()
						   theaxes[0].yaxis.set_major_formatter(FormatStrFormatter('%d'))
						   i = 0
						   tmp = []
						   for theY in myY:
							   tmp.append(yoff[i])
							   yoff[i] += theY
							   i += 1
						   ally.append(tmp)
						   k += 1
						   if k>0:
								   pylab.hold(True)
						   allsc.append(sc[0])
				   pylab.hold(False) 
				   ally.append(yoff)
				   newkeys = []
				   for thekey in data['keys']:
					   newkeys.append(str(thekey))
				   pylab.legend(allsc, newkeys, loc=2, shadow=0, prop=font_manager.FontProperties(size='small', weight=500), handletextsep=0.005, axespad=0.01, pad=0.01, labelsep=0.001, handlelen=0.02)
				   #newind = range(len(allx)+1)
				   pylab.xticks(ind, allx, rotation=45, fontsize=8)
				   pylab.xlim(-width, len(ind)+1)

		else:
			pylab.hold(False)
			for thekey in data:
				if i>0:
					 pylab.hold(True) 
				datax = data[thekey]['x']
				datay = data[thekey]['y']
				allx.extend(datax)
				ally.extend(datay)
				if clickable == 1:
					dataRid.extend(data[thekey]['i'])
				label = str(dotcolor[i%8]) + '--' + allshape[i/8]
				lines = pylab.plot([datax[0]], [datay[0]], label, markersize=5)
				sc = pylab.scatter(datax, datay, c=dotcolor[i%len(dotcolor)], marker=allshape[i/8], s=20)

				fig = sc.get_figure()
				fig.set_figsize_inches(figsize)
				
				labels.append(lines)
				thekeys.append(str(thekey))

				i += 1
			pylab.hold(False) 
			try:
				pylab.legend(labels, thekeys, numpoints=2, shadow=0, prop=font_manager.FontProperties(size='small'), handletextsep=0.01, axespad=0.005, pad=0.005, labelsep=0.001, handlelen=0.01)
			except:
				pass

	pylab.xlabel(L['xlabel'])
	pylab.ylabel(L['ylabel'])

	t = str(time.time())
	rand = str(random.randint(0,100000))
	tempfile = "/graph/t" + t + ".r" + rand + ".png"

	
	pylab.savefig("tweb" + tempfile)				
	wspace = hspace = 0.8

	if clickable == 1:
		if thequery.find('histogram') >= 0:
			  trans = sc[0].get_transform()
			  if groupby == 0:
				  xlist = range(len(allx)+1)
				  ylist = ally
				  ylist.append(0)
				  xcoords, ycoords = trans.seq_x_y(xlist, ylist)
			  else:
				  xlist = range(len(allx))
				  ycoords = []
				  for i in range(len(ally)):
					xs, ys = trans.seq_x_y(xlist, ally[i])
					ycoords.append(ys)
				  xcoords, tmp = trans.seq_x_y(range(len(allx)+1), range(len(allx)+1))						
			  fig = sc[0].get_figure()
		else:
			  trans = sc.get_transform()
			  xcoords, ycoords = trans.seq_x_y(allx, ally)
			  fig = sc.get_figure()
			
		dpi = fig.get_dpi() 
		img_height = fig.get_figheight() * dpi
		img_width = fig.get_figwidth() * dpi
		if thequery.find('histogram') >= 0:
			if groupby == 0:
				  pass
#				  page = p.plot_view_bar(thequery, xcoords, ycoords, dataRid, img_height, wspace, hspace)
			else:
				  dataRid = ind
#				  page = p.plot_view_multibar(thequery, xcoords, ycoords, dataRid, img_height, wspace, hspace)

	return tempfile
		
	
