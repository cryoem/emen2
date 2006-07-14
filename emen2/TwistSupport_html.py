# TwistSupport_html.py  Steven Ludtke  06/2004
# This module provides the resources needed for a HTML server using Twisted

from twisted.web.resource import Resource
from emen2 import TwistSupport 
import pickle
#from twebutil import *
import os
import traceback
import re

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
			return """<html> <head> <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
				<meta http-equiv="REFRESH" content="2; URL=%s"><title>HTML REDIRECT</title></head>
				<body><h3>Login Successful</h3></body></html>"""%request.received_headers["referer"]

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
					text = record_dict['title']
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




def parse_view(recordid, record_dict, group=1, header=0, modulo=0, ctxid=None):
	"""Get view, parse it, return constructed view"""

	recorddef=db.getrecorddef(record_dict['rectype'],ctxid)

	viewtype = "tabularview"

	parse = recorddef.views[viewtype]
	preparse = []

	#
	# Pre-parsing
	#
	parse_split = parse.split(' ')
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
	#	print "i: %s     v: %s"%(i,isplit)

	preparse2 = []
	for i in preparse:
		if i[0] != "":
			preparse2.append(i)
	preparse = preparse2

	#
	# Main parsing
	#
	out = []
	vartypes = []
	vardescs = []
	for i in preparse:
		if i[0].count("$") == 2:
			j = i[0].replace("$$","")
			try: 
				text = record_dict[j.lower()]
				item = db.getparamdef(j.lower())
				vt = item.vartype
				vd = item.desc_short
			except:
				text = ''
				vt = ''
				vd = ''
			out.append(str(text))
			vartypes.append(vt)
			vardescs.append(vd)
		elif i == "":
			pass
		else:
			out.append(str(i[0]))
			vartypes.append('')
			vardescs.append('')

	ret = []
	#
	# View parsing
	#
	if viewtype == "onelineview":
		onelineview = render_onelineview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=ctxid)
		ret.append(" ".join(onelineview))


	if viewtype == "tabularview":
		tabularview = render_tabularview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=ctxid)
		ret.append(" ".join(tabularview))

	return ret



def render_onelineview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=None):
	ret = []
	ret.append("\t\t<td><a href=\"/db/record?name=%s\">%s</a> -- %s -- \n"%(recordid,recordid,record_dict['rectype']))
	ret.append(" ".join(out))
	ret.append("</td>")
	return ret

def render_tabularview(recordid,record_dict,vartypes,vardescs,preparse,out,header,modulo,ctxid=None):
	maxtextlength=500
	ret = []
	if header:
		ret.append("\t<tr>\n")
		for i in range(0,len(out)):
			if vartypes[i] != "text":
				if vartypes[i] != "":
					ret.append("\t\t<th>%s</th>\n"%vardescs[i])
				else:
					ret.append("\t\t<th>(%s)</th>\n"%preparse[i][0].replace("$$",""))
		ret.append("\t</tr>\n")

	# tdclass is for shaded/non-shaded row
	# tdclass2 is for first-item on row
	else:
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
				ret.append("\t\t<td class=\"%s %s\"><!-- %s --><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,tdclass2,preparse[i][0].replace("$$",""),recordid,out[i]))
				tdclass2 = ""

		tdclass2 = "firstitem"
		for i in skipped:
			string = out[i]
			if len(string) >= maxtextlength:
				string = string[0:maxtextlength] + " <a href=\"/db/record?name=%s\">(view more)</a>..."%recordid
			ret.append("\t</tr>\n\t<tr>\n\t\t<td class=\"%s %s\"></td><td class=\"%s\" colspan=\"%s\"><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,tdclass2,tdclass,len(out)-1,recordid,string))
			tdclass2 = ""

		ret.append("\t</tr>\n")

	return ret
	

def render_groupedhead(queryresult,ctxid=None):
#	queryresult = db.getchildren(recordid,ctxid=ctxid)
	record_dicts = get_recorddicts(queryresult,ctxid=ctxid)
	groups = group_by_key(record_dicts,'rectype',ctxid=ctxid)
	ret = []
	for i in groups.keys():
		ret.append("\t<li class=\"switchbutton\" id=\"button_%s\"><a href=\"javascript:switchid('%s')\">%s (%s)</a></li>\n"%(i,i,i,len(groups[i])))
	return " ".join(ret)
	

def render_groupedlist(queryresult, viewonly=None, groupby="rectype", sortgroup=None, ctxid=None):
	"""Draw headers and tables for parents/children of a record"""
#	if render == "parents":
#		queryresult = db.getparents(recordid,ctxid=ctxid)
#	elif render == "children":
#		queryresult = db.getchildren(recordid,ctxid=ctxid)

	ret = []
	record_dicts = get_recorddicts(queryresult,ctxid=ctxid)
	groups = group_by_key(record_dicts,'rectype',ctxid=ctxid)

	if groupby:
		for i in groups.keys():
			# do we want to render this record type?
			if viewonly and viewonly != i:
				pass
			else:
				table = render_grouptable(groups[i],record_dicts,ctxid=ctxid)
				ret.append(" ".join(table))

	else:
		for id in queryresult:
			parse = parse_view(id,record_dicts[str(id)],group=0,ctxid=ctxid)
			ret.append(" ".join(parse))

	return " ".join(ret)


def get_recorddicts(queryresult,ctxid=None):
	"""Take a query result, turn it into record_dicts"""
	record_dicts = {}
	for id in queryresult:
		record = db.getrecord(id, ctxid)
		record_dicts[str(id)] = record.items_dict()
	return record_dicts



def group_by_key(record_dicts,groupby,ctxid=None):
	"""Group record_dicts by key"""
	groups = {}
	for id in record_dicts.keys():
		key = str(record_dicts[str(id)][groupby])

		try:
			groups[key]
		except KeyError:
			groups[key] = []		

		groups[str(record_dicts[str(id)][groupby])].append(id)
	return groups		


# Include recordids in definition because record_dicts may contain extra definitions..
def render_grouptable(recordids,record_dicts,ctxid=None):
	"""Make a table for items with a common view definition"""
	ret = []
	ret.append("\n\n<div class=\"switchpage\" id=\"page_%s\">"%record_dicts[str(recordids[0])]['rectype'])
	ret.append("\t<h1 class=\"switchheader\" id=\"header_%s\">%s</h1>\n"%(record_dicts[str(recordids[0])]['rectype'],record_dicts[str(recordids[0])]['rectype']))
	ret.append("\n\n<table class=\"groupview\" cellspacing=\"0\" cellpadding=\"0\">\n")
					
	tableheader = parse_view(recordids[0],record_dicts[str(recordids[0])],header=1,ctxid=ctxid)
	ret.append(" ".join(tableheader))
	
	modulo=0
	for id in recordids:
		parse = parse_view(id,record_dicts[str(id)],modulo=modulo,ctxid=ctxid)
		modulo=modulo+1
		ret.append(" ".join(parse))

	ret.append("</table>\n</div>\n\n")
	return ret
	
	
	
def get_tile(tilefile,level,x,y):
	"""get_tile(tilefile,level,x,y)
	retrieve a tile from the file"""

	print "get_tile: %s %s %s %s"%(tilefile,level,x,y)

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

	 <ul class="table">
	 	<li class="switchbutton" id="button_mainview"><a href="">%s</a></li>
	</ul>
	</div>"""%title
	return ret
	
###################################################	
## HTML FUNCTIONS #################################
###################################################

def loginpage(redir):
	"""Why is this a function ?  Just because. Returns a simple login page."""
	ret = []
	ret.append(html_header("EMEN2 Login"))
	ret.append(singleheader("EMEN2 Login"))
	page = """
<div class="switchpage" id="page_mainview">
	<h3>Please Login:</h3>
		<form action="/db/login" method="POST">
			<input type="hidden" name="fw" value="%s" />
			<span class="inputlabel">Username:</span> 
			<span class="inputfield"><input type="text" name="username" /></span><br />
			<span class="inputlabel">Password:</span>
			<span class="inputfield"><input type="password" name="pw" /></span><br />
			<span class="inputcommit"><input type="submit" value="submit" /></span>
		</form>
</div>
"""%(redir)

	ret.append(page)
	ret.append(html_footer())

	return " ".join(ret)


def html_header(name,init=None):
	"""Common header block, includes <body>"""

	extra = """
	<div class="nav" id="leftnav">
	<ul id="nav">
		<li id="first"><div><a href="">Query Children</a></div>
			<ul>
			<li><a href="">Recent query 1..</a></li>
			<li><a href="">Recent query 2..</a></li>
			<li><a href="">Recent query 3..</a></li>
			</ul>
		</li>
		<li><div><a href="">Add Child</a></div>
			<ul>
			<li><a href="">Child type 1</a></li>
			<li><a href="">Child type 2</a></li>
			<li><a href="">Child type 3</a></li>
			</ul>
		</li>
		<li><div><a href="">Parent View</a></div>
			<ul>
			<li><a href="">View 1</a></li>
			<li><a href="">View 2</a></li>
			<li><a href="">View 3</a></li>
			</ul>
		</li>
		<li><div><a href="">Child View</a></div>
			<ul>
			<li><a href="">View 1</a></li>
			<li><a href="">View 2</a></li>
			<li><a href="">View 3</a></li>
			</ul>
		</li>
	</ul>
	</div>"""
	
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

<script type="text/javascript" src="/niftycube.js"></script>
<script type="text/javascript" src="/switch.js"></script>
<script type="text/javascript" src="/tile.js"></script>


</head>

<body onLoad="javascript:init();"""%name)

	if init:
		ret.append(str(init))
		
	ret.append("""">

<div id="title">
	<img id="toplogo" src="/images/logo_trans.png" alt="NCMI" /> National Center for Macromolecular Imaging
</div>

<div class="nav_buttons">

<ul class="nav_table">	
	<li class="nav_tableli" id="nav_first"><a href="/db/record?name=0">Browse Database</a></li>
	<li class="nav_tableli"><a href="/db/queryform">Query Database</a></li>
	<li class="nav_tableli"><a href="/emen2/logic/workflow.py/getWorkflow">My Workflow</a></li>
	<li class="nav_tableli"><a href="/db/paramdefs">Parameters</a></li>
	<li class="nav_tableli" id="nav_last"><a href="/db/recorddefs">Protocols</a></li>
</ul>

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
	
def html_record_dicttable(dict,proto,missing=0):
	"""Produce a table of values in 'cols' columns"""

	ret = []
	special = ["rectype","comments","creator","creationtime","permissions","title","identifier","modifytime","modifyuser","parent","comments_text"]
	
	# Standard fields for all records
	ret.append("\n\n<div class=\"standardfields\">\n")
	ret.append("<a href=\"javascript:toggle('standardtable')\">&raquo;</a><br />")

	ret.append("<table class=\"standardtable\" id=\"standardtable\" cellspacing=\"0\" cellpadding=\"5\">")

	ret.append("<tr><td class=\"standardtable_shaded\" id=\"standardtable_rightborder\">Created: %s (%s)</td></tr>"%(dict["creationtime"],dict["creator"]))

	ret.append("<tr><td class=\"standardtable_shaded\">Modified: %s (%s)</td></tr>"%(dict["modifytime"],dict["modifyuser"]))

	if dict["comments_text"]: ret.append("<tr><td colspan=\"2\"><span id=\"comments_main\">%s</span></td></tr>"%dict["comments_text"])

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
	ret.append("</table>")

	ret.append("</div>")

	# Fields for a particular record type
	ret.append("\n\n<table class=\"dicttable\" cellspacing=\"0\" cellpadding=\"0\">\n")
	skipped = 0
	for k,v in dict.items():
		try: item=db.getparamdef(str(k))
		except: continue
#		ret.append("<!-- %s -->"%item)
#		item=db.getparamdef(str(k))
		if missing and v == "":
			skipped = 1
		elif not special.count(k):
			ret.append("\t<tr>\n\t\t<td class=\"pitemname\"><a href=\"%s%s\">%s</a></td>\n\t\t<td>%s</td>\n\t</tr>\n"%(proto,k,item.desc_short,v))
		
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
		<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
		    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">	

		<html>

		<head>

		<title>
		Image Browser
		</title>

		<link rel="StyleSheet" href="/main.css" type="text/css" />

		<script type="text/javascript" src="/niftycube.js"></script>
		<script type="text/javascript" src="/switch.js"></script>

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

		<div class="nav_buttons">

		<ul class="nav_table">	
			<li class="nav_tableli" id="nav_first"><a href="/db/record?name=0">Browse Database</a></li>
			<li class="nav_tableli"><a href="/db/queryform">Query Database</a></li>
			<li class="nav_tableli"><a href="/emen2/logic/workflow.py/getWorkflow">My Workflow</a></li>
			<li class="nav_tableli"><a href="/db/paramdefs">Parameters</a></li>
			<li class="nav_tableli" id="nav_last"><a href="/db/recorddefs">Protocols</a></li>
		</ul>

		</div>

		<div id="content">"""%(str(dimsx),str(dimsy),path[1])


		ret.append(singleheader("Parameter Definitions"))
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
			r = db.getbinary(str(i[0])+"%05X"%j,ctxid)
			ret.append("%s <br />"%str(r))

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
	
	ret.append(  html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea","find child of 71",(80,8))))  )

	ret.append("</div>")

	ret.append(html_footer())

	return "".join(ret)
		

def html_query(path,args,ctxid,host):
	global db

	result = db.query(str(args["query"][0]),ctxid)
	
	with = {'wftype':'query','desc':str(args["query"][0]),'longdesc':str(args["query"][0]),'appdata':result['data']}
	newwf = db.newworkflow(with)
	wfid = db.addworkflowitem(newwf,ctxid)

	ret = []

	ret.append(html_header("EMEN2 Record",init="showallids();"))
	
	ret.append("""<div class="navtree">
	<table cellpadding="0" cellspacing="0" class="navtable">
	</table>
	</div>""")
	
	
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("<ul class=\"table\">\n")
	ret.append("\t<li class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">Edit Query</a></li>\n")
	ret.append("\t<li>&raquo;</li>\n")
	ret.append("\t<li class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:showallids()\">All Results</a></li>\n")
	ret.append("\t<li>&raquo;</li>\n")


	ret.append(render_groupedhead(result['data'],ctxid=ctxid))
	ret.append("\n</ul>\n</div>")
	
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append(  html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea",str(args["query"][0]),(80,8))))  )

	ret.append("</div>")
	
	ret.append(render_groupedlist(result['data'],ctxid=ctxid))

#	ret.append("<script type=\"text/javascript\">showallids();</script>")


	ret.append(html_footer())

	return " ".join(ret)

def html_record(path,args,ctxid,host):
	global db
	
	item=db.getrecord(int(args["name"][0]),ctxid)
	queryresult = db.getchildren(int(args["name"][0]),ctxid=ctxid)

	ret=[html_header("EMEN2 Record")]
	
	ret.append(parent_tree(int(args["name"][0]),ctxid=ctxid))
	
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("<ul class=\"table\">\n")
	ret.append("\t<li class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">Record %d (%s)</a></li>\n"%(int(item.recid),item["rectype"]))
	
	if queryresult:
		ret.append("\t<li class=\"switchshort\">&raquo;</li>")
		ret.append("\t<li class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:showallids()\">All Children</a></li>\n")
		ret.append("\t<li class=\"switchshort\">&raquo;</li>\n")
		ret.append(render_groupedhead(queryresult,ctxid=ctxid))

	ret.append("\n</ul>\n</div>")

	ret.append("\n\n<div class=\"switchpage\" id=\"page_mainview\">")
	ret.append(html_record_dicttable(item,"/db/paramdef?name=",missing=1))
	ret.append("\n</div>\n\n")

	ret.append(render_groupedlist(queryresult,ctxid=ctxid))

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
		
#		print "Record(  ",rec,"  )"
		bld=[("","rectype","hidden")]
		for p in rec.keys():
			if p in ("owner","creator","creationdate","comments") or (p!="permissions" and parm[p].vartype in ("child","link")) : continue
			try: bld.append((parm[p].desc_short,p,"text"))
			except: bld.append((p,p,"text"))

		d=rec.items_dict()
		d["rectype"]=args["rdef"][0]
		ret.append(html_form(method="POST",action="/db/newrecord",items=bld,args=d))
		ret.append("</div>")
		ret.append(html_footer())
#		ret.append("</body></html")
		return "".join(ret)

	argmap(args)
	rec=db.newrecord(args["rectype"],ctxid,host,init=0)
#	del args["rdef2"]
	rec.update(args)

	rid=db.putrecord(rec,ctxid,host)
	ret.append('Record add successful.<br />New id=%d<br><br><a href="/db/index.html">Return to main menu</a>'%rid)
	
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
