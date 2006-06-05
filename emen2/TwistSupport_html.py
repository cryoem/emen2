# TwistSupport_html.py  Steven Ludtke  06/2004
# This module provides the resources needed for a HTML server using Twisted

from twisted.web.resource import Resource
from emen2 import TwistSupport 
import os
import traceback
import re

# we open the database as part of the module initialization
db=None
DB=TwistSupport.DB

def loginpage(redir):
	"""Why is this a function ?  Just because. Returns a simple login page."""
	return """%s<h3>Please Login:<br>
<form action="/db/login" method="POST"><input type=hidden name=fw value=%s>
<br>Username: <input type=text name=username>
<br>Password: <input type=password name=pw>
<br><input type=submit value=submit></form>%s"""%(html_header("EMEN2 Login"),redir,html_footer())

def argmap(dict):
	for i in dict: dict[i]=dict[i][0]


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
		
		return eval("html_"+method)(request.postpath,request.args,ctxid,host)
#		return callbacks[method](request.postpath,request.args,ctxid,host)

#		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())



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
			print "Parents for %s: %s"%(m[y][x],queryresult)

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

		print m
		
	# fix stupid bug -- pad rows before reversing -- FIX: find longer one	
	for i in range(0,len(m)):
		if len(m[0]) > len(m[i]):
			for j in range(len(m[i]),len(m[0])):
				m[i].append("")
		elif len(m[i]) > len(m[0]):
			for j in range(len(m[0]),len(m[i])):
				m[0].append("")
	# requires two passes
	for i in range(0,len(m)):			
		m[i].reverse()



	ret = ["<table class=\"navtree\" cellpadding=0 cellspacing=0>"]
	
	ret.append("<!-- %s -->"%m)

	for posy in range(0,len(m)):
		ret.append("<tr>\n")
		for posx in range(0,len(m[posy])):
			if m[posy][posx] != "":
				record = db.getrecord(m[posy][posx], ctxid)
				record_dict = record.items_dict()

				pclass="ptree"
				ret.append("\t<td class=%s>"%pclass)

				
				if os.path.exists("tweb/images/icons/%s.gif"%record_dict['rectype']):
					ret.append("<img src=/images/icons/%s.gif>"%record_dict['rectype'])
				
				ret.append("<a href=/db/record?name=%s>%s</a></td>\n"%(m[posy][posx],record_dict['rectype']))

				ok = ["","","","",""]
				img = ""

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

				if ok[0] and not ok[2]:
					img = "branch_next"
				if ok[4] and not ok[1] and not img:
					img = "branch_up"
				if ok[1] and not img:
					img = "next"
				if not img:
					img = "blank"

				ret.append("\t   <td class=\"ptreeempty\"><img src=\"/images/%s.png\"></td>\n"%img)

			else:
				ret.append("\t<td></td>\t<td></td>\n")

		ret.append("<tr>\n")
	ret.append("</table>")

	return " ".join(ret)


def render_special_view(recordid,record_dict,out):
	type = record_dict['rectype']

	format = ""

	if type == "project":
#		print out
		format = "(Special View) Project: <a href=\"/db/record?name=%s\">%s</a> %s   --   PI: %s <br>"%(recordid,recordid,out[0],out[1])

	return format

def parse_view(recordid, record_dict, group=1, header=0, modulo=0, maxtextlength=500, ctxid=None):
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
	varnames = []
	vardescs = []
	for i in preparse:
		if i[0].count("$") == 2:
			j = i[0].replace("$$","")
			try: 
				text = record_dict[j.lower()]
				item = db.getparamdef(j.lower())
				vt = item.vartype
				vn = item.name
				vd = item.desc_short
			except:
				text = ''
				vt = ''
				vn = ''
				vd = ''
			out.append(str(text))
			vartypes.append(vt)
			varnames.append(vn)
			vardescs.append(vd)

		elif i == "":
			pass
		else:
			out.append(str(i[0]))
			vartypes.append('')
			varnames.append('')
			vardescs.append('')

	ret = []
	#
	# View parsing
	#
	if viewtype == "onelineview":

		if group:
			ret.append("<tr><a href=/db/record?name=%s>%s</a> -- \n"%(recordid,recordid))
		else: 
			ret.append("<tr><a href=/db/record?name=%s>%s</a> -- %s -- \n"%(recordid,recordid,record_dict['rectype']))

		ret.append(" ".join(out))
		ret.append("</tr>")

	elif viewtype == "tabularview":

		if header:
			print "Header: %s"%record_dict['rectype']
			ret.append("<tr>")
			for i in range(0,len(out)):
				if vartypes[i] != "text":
					if vartypes[i] != "":
						ret.append("<th>%s</th>\n"%vardescs[i])
					else:
						ret.append("<th>(%s)</th>\n"%preparse[i][0].replace("$$",""))
			ret.append("</tr>\n")

		else:
			skipped = []
			ret.append("<tr>")

			if modulo % 2:
				tdclass = ""
			else:
				tdclass = "shaded"

			for i in range(0,len(out)):
				if vartypes[i] == "text":
					skipped.append(i)
				else:
					ret.append("<td class=\"%s\"><!-- %s --><a href=/db/record?name=%s>%s</a></td>\n"%(tdclass,preparse[i][0].replace("$$",""),recordid,out[i]))

			for i in skipped:
				string = out[i]
				if len(string) >= maxtextlength:
					string = string[0:maxtextlength] + " <a href=/db/record?name=%s>(view more)</a>..."%recordid
				ret.append("</tr><tr><td class=\"%s\"></td><td class=\"%s\" colspan=%s>%s</td>\n"%(tdclass,tdclass,len(out)-1,string))

			ret.append("</tr>\n")


	return ret

def render_parentschildren(recordid, render, viewonly=None, groupby="rectype", sortgroup=None, ctxid=None):
	if render == "parents":
		queryresult = db.getparents(recordid,ctxid=ctxid)
	elif render == "children":
		queryresult = db.getchildren(recordid,ctxid=ctxid)
	else:
		# fix: throw an exception
		print "Render types: parents, children"	
		return

	ret = []
	record_dicts = {}
	groups = {}

	for id in queryresult:

		record = db.getrecord(id, ctxid)
		record_dicts[str(id)] = record.items_dict() 
		recorddef=db.getrecorddef(record_dicts[str(id)]['rectype'],ctxid=ctxid)

		groupby="rectype"

		if groupby:
			key = str(record_dicts[str(id)][groupby])

			try:
				groups[key]
			except KeyError:
				groups[key] = []		

			groups[str(record_dicts[str(id)][groupby])].append(id)

			#print "Groups: " + str(groups)

		# by default, no sorting
		# sortgroup is a dictionary with group: [parameter, sortby]
		# will sort each group 
		# will need switch for int/float/date/etc.
		if sortgroup:
			pass

	if groupby:
		for i in groups.keys():
			# do we want to render this record type?
			if viewonly and viewonly != i:
				pass
			else:
				ret.append("\n<h4>%s</h4>\n"%i)
				ret.append("<table class=\"groupview\" cellspacing=0 cellpadding=0>\n")
								
				tableheader = parse_view(id,record_dicts[str(groups[i][0])],header=1,ctxid=ctxid)
				ret.append(" ".join(tableheader))
				
				modulo=0
				for id in groups[i]:
					parse = parse_view(id,record_dicts[str(id)],modulo=modulo,ctxid=ctxid)
					modulo=modulo+1
					ret.append(" ".join(parse))

				ret.append("</table>")

	else:
		for id in queryresult:
			parse = parse_view(id,record_dicts[str(id)],group=0,ctxid=ctxid)
			ret.append(" ".join(parse))

	return " ".join(ret)


def html_header(name):
	"""Common header block, includes <body>"""
	return """
	<html>
	<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

	  <link rel=StyleSheet href="/main.css" type="text/css">
	
	<head>
	<title>
	%s
	</title>
	</head>

	<body bgcolor="#FFFFFF">

	<div id="title">
		<img id="toplogo" src="/images/logo_trans.png"> National Center for Macromolecular Imaging
	</div>
	
	<div class="nav" id="nav">

	<ul id="nav">	
		<li id="first"><div><a href="/db/record?name=0">Browse Database</a></div></li>
		<li><div><a href="/db/queryform">Query Database</a></div></li>
		<li><div><a href="/emen2/logic/workflow.py/getWorkflow">My Workflow</a></div></li>
		<li><div><a href="/db/paramdefs">Parameters</a></div></li>
		<li><div><a href="/db/recorddefs">Protocols</a></div></li>
	</ul>

	</div>
	
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
	</div>
	
	<div id="content">
	"""%name

def html_navbar():
	"""Top navigation bar"""
	return """
	"""

def html_footer():
	"""Common header block, includes <body>"""
	return """
	
	</div>
	
	<div id="bottom">

	<img id="bottomlogo" src="/images/logo_alt_sm.gif">	

	<!-- -->

	Loggged in as: <br>

		       <SCRIPT LANGUAGE="JavaScript">
		       mydate = new Date()
		       document.writeln(mydate.toLocalString())
		       document.writeln(document.cookie)
		       </SCRIPT>

	Hosted by <a href="http://ncmi.bcm.tmc.edu">NCMI</a>&nbsp;&nbsp;Phone: 713-798-6989 &nbsp;&nbsp;Fax: 713-798-1625<br>
	Room N421 Alkek Building, One Baylor Plaza, Houston, TX, 77030<br>
	Please mail comments/suggestions to: <a href="mailto:htu@bcm.tmc.edu">WEBMASTER</a><br><br>

	</div>

	</body>
	</html>
	"""


def html_htable(itmlist,cols,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=['<table>']
	
	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("<tr>")
		ret.append("<td><a href=%s%s>%s</a></td>"%(proto,j,j))
		if (i%cols==cols-1) : ret.append("</tr>\n")
	
	if (len(itmlist)%cols!=0) : ret.append("</tr></table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)

def html_htable2(itmlist,cols,proto):
	"""Produce a table of values and counts in 'cols' columns"""
	ret=['<table>']
	
	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("<tr>")
		ret.append("<td><a href=%s%s>%s (%d)</a></td>"%(proto,j[0],j[0],j[1]))
		if (i%cols==cols-1) : ret.append("</tr>\n")
	
	if (len(itmlist)%cols!=0) : ret.append("</tr></table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)

def html_dicttable(dict,proto,missing=0):
	"""Produce a table of values in 'cols' columns"""
	ret=["<table class=\"dicttable\" cellspacing=0 cellpadding=0>"]

	skipped = 0
	for k,v in dict.items():
		item=db.getparamdef(str(k))
#		ret.append("<!-- %s -->"%item)
		if missing and v == "":
			skipped = 1
		else:
			ret.append("<tr><td class=\"pitemname\"><a href=%s%s>%s</a></td><td>%s</td></tr>\n"%(proto,k,item.desc_short,v))
		
	ret.append("</table><br>")

	if skipped:
		ret.append("<div class=\"emptyfields\">Emtpy fields: ")
		for k,v in dict.items():
			item=db.getparamdef(str(k))
			if v == "":
				ret.append("<a href=%s%s>%s</a>, \n"%(proto,k,item.desc_short))
		ret.append("</div>")

	return "".join(ret)
		
def html_home():
	ret=[html_header("EMEN2 Home Page")]
	ret.append("""<h2>EMEN2 Demo Page!!!</h2><br><br>Available tasks:<br><ul>
	<li><a href="/db/record?name=0">Browse Records</a></li>
	<li><a href="/db/queryform">Query Database</a></li>
	<li><a href="/db/records">List of all Records</a></li>
	<li><a href="/db/paramdefs">List of Defined Experimental Parameters (ParamDef)</a></li>
	<li><a href="/db/recorddefs">List of Defined Experimental Protocols (RecordDef)</a></li>
	<li><a href="/db/users">List of Users</a></li>
	</ul><br><br><ul>
	<li><a href="/db/newuser">Add New User</a></li>
	<li><a href="/db/newuserqueue">Approve New Users</a></li>
	<li><a href="/db/newparamdef">Define New Experimental Parameter</a></li>
	<li><a href="/db/newrecorddef">Describe new Experimental Protocol</a></li>
	</ul>""")
	ret.append(html_footer())
	
	return "".join(ret)

def html_tileimage(path,args,ctxid,host):
	global db

	name,fpath=db.getbinary(path[1],ctxid,host)
	fpath=fpath+".tile"
	
	if not args.has_key("x") :
		lvl=int(args["level"][0])
		dims=get_tile_dim(fpath)
		dimsx=[i[0] for i in dims]
		dimsy=[i[1] for i in dims]
		
		ret="""<HTML><HEAD><TITLE>IMAGE</TITLE><style type="text/css">
		#outerdiv { height: 512; width:512; border: 1px solid black; position:relative; overflow:hidden; }
		#innerdiv { position:relative; left: 0px; right: 0px; }</style>
		</style>
		<script type="text/javascript">
		var isdown=false;
		var nx=%s
		var ny=%s
		var level=nx.length-1
		
		function init() {
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
		</script></HEAD><BODY onload=init()>
		<div id="outerdiv"><div id="innerdiv">LOADING</div></div><br><br><div id="dbug"></div>
		<button onclick=zoomout()>Zoom -</button><button onclick=zoomin()>Zoom +</button><br></BODY></HTML>"""%(str(dimsx),str(dimsy),path[1])
		
		
		return ret
		
	try: ret=get_tile(fpath,int(args["level"][0]),int(args["x"][0]),int(args["y"][0]))
	except: return "Invalid tile"
	return ret

def get_tile(tilefile,level,x,y):
	"""get_tile(tilefile,level,x,y)
	retrieve a tile from the file"""

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

def html_paramdefs(path,args,ctxid,host):
	global db
	
	ftn=db.getparamdefnames()
	ret=[html_header("EMEN2 ParamDefs"),"<h2>Registered ParamDefs</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/paramdef?name="))

	ret.append(html_footer())
	return "".join(ret)	

def html_paramdef(path,args,ctxid,host):
	global db
	
	item=db.getparamdef(args["name"][0])
	
	ret=[html_header("EMEN2 ParamDef Description"),"<h2>Experimental Parameter (ParamDef): <i>%s</i></h2><br>"%item.name]
	
	parents=db.getparents(item.name,keytype="paramdef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<h2>Parents:</h2> ")
		for p in parents:
			ret.append('<a href="/db/paramdef?name=%s">%s</a> '%(p,p))
	
	children=db.getchildren(item.name,keytype="paramdef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<h2>Children:</h2>")
		for c in children:
			ret.append('<a href="/db/paramdef?name=%s">%s</a> '%(c,c))
	
	ret.append("""<table><tr><td>Name</td><td>%s</td></tr>
	<tr><td>Variable Type</td><td>%s</td></tr>
	<tr><td>Short Description</td><td>%s</td></tr>
	<tr><td>Long Description</td><td>%s</td></tr>
	<tr><td>Property</td><td>%s</td></tr>
	<tr><td>Default Units</td><td>%s</td></tr>
	<tr><td>Creator</td><td>%s (%s)</td></table><br><br><a href="/db/newparamdef?parent=%s">Add a new child parameter</a>"""%(
	item.name,item.vartype,item.desc_short,item.desc_long,item.property,item.defaultunits,item.creator,item.creationtime,item.name))
	
	ret.append(html_footer())
	
	return "".join(ret)

def html_newparamdef(path,args,ctxid,host):
	"""Add new ParamDef form. Also does the actual ParamDef insertion"""	
	ret=[html_header("EMEN2 Add Experimental Parameter"),"<h1>Add Experimental Parameter</h1><br>"]
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
		ret+=['<br><br>New Parameter <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["name"][0]),html_footer()]
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		return "".join(ret)+html_form(method="GET",action="/db/newparamdef",items=(("","parent","hidden"),("Name:","name","text"),
		("Variable Type","vartype","select",("int","float","string","text","url","image","binary","datetime","link","child")),
		("Short Description","desc_short","text"),("Long Description","desc_long","textarea",(60,3)),
		("Physical Property","property","select",DB.valid_properties),("Default Units","defaultunits","text")),args=args)+html_footer()

def html_recorddefs(path,args,ctxid,host):
	global db
	
	ftn=db.getrecorddefnames()
	for i in range(len(ftn)):
		ftn[i]=(ftn[i],len(db.getindexbyrecorddef(ftn[i],ctxid)))
	ret=[html_header("EMEN2 RecordDefs"),"<h2>Registered RecordDefs</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable2(ftn,3,"/db/recorddef?name="))

	ret.append(html_footer())
	return "".join(ret)

def html_recorddef(path,args,ctxid,host):
	global db
	
	item=db.getrecorddef(args["name"][0],ctxid)
	
	ret=[html_header("EMEN2 RecordDef Description"),"<h2>Experimental Protocol (RecordDef): <i>%s</i></h2><br>"%item.name,
	]
	
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
	ret.append(html_footer())
	
	return "".join(ret)

def html_newrecorddef(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 Add Record Definition"),"<h1>Add Record Definition</h1><br>"]
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
		ret+=['<br><br>New Protocol <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["name"][0]),html_footer()]
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		return "".join(ret)+html_form(method="GET",action="/db/newrecorddef",items=(("","parent","hidden"),("Name:","name","text"),
		("Experiment Description","mainview","textarea",(80,16)),("Summary View","summary","textarea",(80,8)),
		("One Line View","oneline","textarea",(80,4)),("Private Access","private","checkbox")),args=args)+html_footer()
	
def html_records(path,args,ctxid,host):
	
	ftn=db.getrecordnames(ctxid,host=host)
	ret=[html_header("EMEN2 Records"),"<h2>All accessible records</h2>"]
	ret.append(html_htable(ftn,3,"/db/record?name="))

	ret.append(html_footer())
	return "".join(ret)


def html_queryform(path,args,ctxid,host):
	ret=[html_header("EMEN2 DB Query")]
	
	ret.append(  html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea","find 0")))  )
	
	ret.append(html_footer())

	return "".join(ret)
		


def html_record(path,args,ctxid,host):
	global db
	
	item=db.getrecord(int(args["name"][0]),ctxid)

	ret=[html_header("EMEN2 Record")]
	
	ret.append(parent_tree(int(args["name"][0]),ctxid=ctxid))
	
	ret.append("<h2>Record: <i>%d (%s)</i></h2>"%(int(item.recid),item["rectype"]))
	
	ret.append(html_dicttable(item,"/db/paramdef?name=",missing=1))

	ret.append("<h2>Parents:</h2>")
	ret.append(render_parentschildren(int(args["name"][0]),"parents",ctxid=ctxid))

	ret.append("<h2>Children:</h2>")
	ret.append(render_parentschildren(int(args["name"][0]),"children",ctxid=ctxid))

	ret.append(html_footer())
	
	return " ".join(ret)

def html_newrecord(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 Add Record"),"<h1>Add Record</h1><br>"]
	
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
		ret.append("</body></html")
		return "".join(ret)

	argmap(args)
	rec=db.newrecord(args["rectype"],ctxid,host,init=0)
#	del args["rdef2"]
	rec.update(args)

	rid=db.putrecord(rec,ctxid,host)
	ret.append('Record add successful.<br>New id=%d<br><br><a href="/db/index.html">Return to main menu</a>'%rid)
	
	ret.append(html_footer())
	
	return ''.join(ret)
	
def html_users(path,args,ctxid,host):
	global db
	
	ftn=db.getusernames(ctxid,host)
	ret=[html_header("EMEN2 Users"),"<h2>Users</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/user?uid="))

	ret.append(html_footer())
	return "".join(ret)

def html_newuserqueue(path,args,ctxid,host):
	global db
	
	ftn=db.getuserqueue(ctxid,host)
	ret=[html_header("EMEN2 User Queue"),"<h2>New Users Waiting Approval</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/approveuser?username="))

	ret.append(html_footer())
	return "".join(ret)

def html_user(path,args,ctxid,host):
	global db
	
	if not args.has_key("uid") : args["uid"]=args["username"]
	ret=[html_header("EMEN2 User"),"<h2>User: <i>%s</i></h2><br>"%args["uid"][0]]
	
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
	if u[0]==item.username or -1 in u[1]: pwc='<br><a href="/db/chpasswd?username=%s">Change Password</a>'%args["uid"][0]+html_footer()
	else: pwc=html_footer()
	
	return "".join(ret)+html_form(method="GET",action="/db/user",items=(("Username","username","text",14),
		("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
		("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea",(40,3)),
		("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
		("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16),
		("Groups","groups","text",40)),args=item.__dict__)+pwc

def html_chpasswd(path,args,ctxid,host):
	argmap(args)
	ret=[html_header("EMEN2 Change Password"),"<h2>User: <i>%s</i></h2><br>"%args["username"]]
	
	if args.has_key("password") :
		if args["password"]!=args["password2"] : raise SecurityError,"Passwords do not match"
		db.setpassword(args["username"],args["oldpassword"],args["password"],ctxid,host)
		ret.append('<br><b>Password Changed</b><br><br><a href="/db/index.html">Return Home</a>')
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
	
	return "".join(ret)+html_form(action="/db/chpasswd",items=itm,args=args)+html_footer()
	
def html_approveuser(path,args,ctxid,host):
	db.approveuser(args["username"][0],ctxid,host)
	return html_newuserqueue(path,args,ctxid,host)
	
def html_newuser(path,args,ctxid,host):
	global db
	ret=[html_header("EMEN2 New User Form"),"<h1>New User Application</h1><br>"]
	if args.has_key("username") :
		try: 
			for k in args.keys(): args[k]=args[k][0]
			rd=DB.User(args)
			db.adduser(rd)
		except Exception,e:
			traceback.print_exc()
			ret.append("Error adding User '%s' : <i>%s</i><br><br>"%(str(args["username"]),e))	# Failed for some reason, fall through so the user can update the form
			return "".join(ret)
			
		# User added sucessfully
		ret+=['<br><br>New User <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["username"]),html_footer()]
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		argmap(args)
		return "".join(ret)+html_form(action="/db/newuser",items=(("Username","username","text",14),("Password","password","password",14),
			("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
			("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea",(40,3)),
			("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
			("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16)),args=args)+html_footer()

def html_form(action="",items=(),args={},method="POST"):
	ret=['<table><form action="%s" method=%s>'%(action,method)]
	for i in items:
		if i[2]=="select" :
			ret.append('<tr><td>%s:</td><td><select name="%s">'%(i[0],i[1]))
			for j in i[3]:
				if j==args.get(i[1],[""])[0] : ret.append('<option selected>%s</option>'%j)
				else : ret.append('<option>%s</option>'%j)
			ret.append('</select></td></tr>\n')
		elif i[2]=="textarea" :
			if len(i)<5 : i=i+(40,10)
			ret.append('<tr><td>%s</td><td><textarea name="%s" cols="%d" rows="%d">%s</textarea></td></tr>\n'%(i[0],i[1],i[4],i[5],i[3]))
		elif i[2]=="password" :
			if (len(i)<4) : i=i+(20,)
			ret.append('<tr><td>%s</td><td><input type="%s" name="%s" value="%s" size="%d" /></td></tr>\n'%(i[0],i[2],i[1],str(args.get(i[1],"")),int(i[3])))
		elif i[2]=="text" :
			if (len(i)<4) : i=i+(20,)
			ret.append('<tr><td>%s</td><td><input type="%s" name="%s" value="%s" size="%d" /></td></tr>\n'%(i[0],i[2],i[1],str(args.get(i[1],"")),int(i[3])))
		elif i[2]=="hidden" :
			ret.append('<input type="hidden" name="%s" value="%s" /></td></tr>\n'%(i[1],str(args.get(i[1],""))))
		else:
			ret.append('<tr><td>%s</td><td><input type="%s" name="%s" value="%s" /></td></tr>\n'%(i[0],i[2],i[1],args.get(i[1],"")))

	ret.append('<tr><td></td><td><input type="submit" value="Submit" /></td></tr></form></table>\n')
	
	return "".join(ret)
