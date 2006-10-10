################################################### 
## PAGE FUNCTIONS #################################
###################################################

import traceback


from sets import Set
import re
import os
from emen2.TwistSupport_db import db, DB
#import html
import tmpl
import supp
import plot

import timing
import time


# ok

def html_home():
	ret=[tmpl.html_header("EMEN2 Home Page")]

	ret.append(tmpl.singleheader("Home"))
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

	ret.append(tmpl.html_footer())

	return "".join(ret)



# ok
def html_workflow(path,args,ctxid,host):
	global db

	ftn=db.getparamdefnames()

	ret=[tmpl.html_header("EMEN2 Workflow")]

	ret.append(tmpl.singleheader("Workflow"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Workflow</h2><br />")	

	ret.append("<a href=\"/db/cwf\">Clear Workflow Cache</a><br /><br />")

	all = []
	wf = db.getworkflow(ctxid)
	
	for i in wf:
		wfdict = i.items_dict()
		ret.append("workflow: %s <br />query: %s<br />results: %s<br />\n\n"%(wfdict["wfid"],wfdict["longdesc"],wfdict["resultcount"]))

		ret.append("<a href=\"javascript:toggle('workflowdict_%s');\">+ contents:</a><br /><div id=\"workflowdict_%s\" style=\"display:none\">"%(wfdict["wfid"],wfdict["wfid"]))
		ret.append(str(i.items_dict()))
		ret.append("</div><br />")
		

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret)



# ajax goodness
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

#	timing.start()


	wf = db.getworkflowitem(int(args["wfid"][0]),ctxid)
#	print wf
	recordids = wf["appdata"][groupname]
	print "\nRecord ids for type %s count: %s"%(groupname,len(recordids))

	if not args.has_key("sort_%s"%groupname): 
		if not args.has_key("sorted"):
			print "Default sorting by modifytime..."
			sortby = "modifytime"
			args["sort_%s"%groupname] = [sortby]
			args["reverse_%s"%groupname] = [1]
		else:
			print "Already sorted..."
			reverse = 0

	if args.has_key("sort_%s"%groupname):
		sortby = args["sort_%s"%groupname][0]
		print "Sorting by %s now.."%sortby
		args["sorted"] = [1]
		reverse = int(args["reverse_%s"%groupname][0])
		recordids = supp.sortlistbyparamname(sortby,recordids,reverse,ctxid)
		reverse = int(not reverse)




#	timing.finish()
#	print "microseconds getting workflow: %s"%timing.micro()

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


		print "Args: %s"%args
		for j in args.keys():
			# exclude sort to keep from constantly resorting
			if j != key and j != "viewinit" and j != "sort_%s"%groupname:
				baseurl.append("&%s=%s"%(j,args[j][0]))
		baseurlstr = "".join(baseurl)

		nav.append("<div class=\"table_arrows\">")
		if (ipos - perpage) >= 0:
			nav.append("""<span class="table_span" onclick="makeRequest('%s&%s=%s&zone=%s','%s')">&laquo;</span>"""%(baseurlstr,key,ipos - perpage,"zone_%s"%groupname,"zone_%s"%groupname))

		end = pos+perpage
		count = len(recordids)
		if end > count:
			end = count
		nav.append("""<span class="table_span"> (%s-%s of %s) </span>"""%(pos,end,count))

		if (ipos + perpage) <= len(recordids):
			nav.append("""<span class="table_span" onclick="makeRequest('%s&%s=%s&zone=%s','%s')">&raquo;</span>"""%(baseurlstr,key,ipos + perpage,"zone_%s"%groupname,"zone_%s"%groupname))

		nav.append("</div>")

	ret.append(" ".join(nav))


	# Now let's draw a table.

	
#	timing.start()
	
	# regex to parse view definition
	re1 = supp.regexparser()
	p = re.compile(re1)
	
	viewtype = "tabularview"
	# cut off for long text fields
	maxtextlength=500
	
	vt = {}
	vd = {}
	firstrow = []
	secondrows = []
#	ret = []

	# get view def
	viewdef=db.getrecorddef(groupname,ctxid).views[viewtype]

	ret.append("\n\n<table class=\"groupview\" cellspacing=\"0\" cellpadding=\"0\" >\n")
	ret.append("\t<tr>\n")

	# look at all the fields, get their data types, make table header
	iterator = p.finditer(viewdef)
	
	for match in iterator:
		if match.group("var1"): 
			item = db.getparamdef(match.group("var1"))
			vt[match.group("var1")] = item.vartype
			vd[match.group("var1")] = item.desc_short
			if item.vartype == "text":
				secondrows.append(["var",match.group("var1"),match.group("var2")])
			else:

				# url
				baseurl=["/db/render_grouptable","?"]							
				baseurl.append("&groupname=%s"%groupname)
				baseurl.append("&pos_%s=0"%groupname)
				baseurl.append("&wfid=%s"%args["wfid"][0])
				baseurl.append("&%s=%s"%("sort_%s"%groupname,match.group("var1")))
				baseurl.append("&%s=%s"%("reverse_%s"%groupname,reverse))
				baseurlstr = "".join(baseurl)
				r = "javascript:makeRequest('%s&%s=%s&zone=%s','%s')"%(baseurlstr,key,ipos - perpage,"zone_%s"%groupname,"zone_%s"%groupname)

				ret.append("\t\t<th><span class=\"table_span\" onclick=\"%s\">%s</span></th>\n"%(r,vd[match.group("var1")]))

				firstrow.append(["var",match.group("var1"),match.group("var2")])
#				print "Added to frontrow: %s"%match.group("var")
		if match.group("macro1"): 
			firstrow.append(["macro",match.group("macro1"),match.group("macro2")])
			# macros don't have a sorting method yet
			ret.append("\t\t<th><span class=\"table_span\" onclick=\"%s\">m: %s</span></th>\n"%("",match.group("macro1")))
		if match.group("name1"):
			pass
			#  I don't think tabularviews will use $#name	
			#firstrow.append(["name",match.group("name1"),None])

	ret.append("\t</tr>\n")

#	timing.finish()
#	print "parsed view in %s us"%timing.micro()

#	print "Table rows..."

	# for alternating colors
	modulo = 0
	# for each record, draw the rows
	for id in recordids[pos:pos+perpage]:

#		print "Row %s"%id
		ret.append("\t<tr>\n")

		modulo = modulo + 1
		if modulo % 2:
			tdclass = ""
		else:
			tdclass = "shaded"

		timing.start()

		# get the record and restart the iterator
		record=db.getrecord(id,ctxid)
		record_dict = record.items_dict()

#		timing.finish()
#		print "microseconds getting record %s: %s"%(id,timing.micro())


#		timing.start()

#		print "Ok, now parsing."
		for i in firstrow:
			if i[0] == "var":
				# put in the value, or say "i tried, no answer"
				try:
					ret.append("\t\t<td class=\"%s\"><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,id,record_dict[i[1]]))
				except:
					ret.append("\t\t<td class=\"%s\"><a href=\"/db/record?name=%s\"><!-- %s --></a></td>\n"%(tdclass,id,i[1]))

			# macro processing
			if i[0] == "macro":
				value = supp.macro_processor(i[1],i[2],id,ctxid=ctxid)
				ret.append("\t\t<td class=\"%s\"><a href=\"/db/record?name=%s\">%s</a></td>\n"%(tdclass,id,value))

#		print "Second rows.."
		# text fields
		for i in secondrows:
			if i[0] == "var":
#				item=db.getparamdef(i[1])
				try:
					string = record_dict[i[1]]
				except:
					string = ""
					
				if len(string) >= maxtextlength:
					string = string[0:maxtextlength] + " <a href=\"/db/record?name=%s\">(view more)</a>..."%id

				ret.append("\t</tr>\n\t<tr>\n\t\t<td class=\"%s\"></td><td class=\"%s\" colspan=\"%s\">%s: %s</td>\n"%(tdclass,tdclass,len(firstrow)-1,vd[i[1]],string))

		ret.append("\t</tr>\n")

		timing.finish()
		print "microseconds parsing record %s: %s"%(id,timing.micro())

	ret.append("</table>")
	# close the table
	
	ret.append("</div>\n\n")
#	ret.append("</div>")
	# close the pages

	return " ".join(ret)



	

# ok	
def html_record_dicttable(dict,proto,viewdef,missing=0,ctxid=None):
	global db
	
	"""Main record function: sidebar, views, etc"""

	# we'll need this a few times
	recommentsregex = "\n"
	pcomments = re.compile(recommentsregex)

	ret = []
	
	# special fields to remove from record: held in sidebar
	special = ["rectype","creator","creationtime","permissions","title","identifier","modifytime","modifyuser","parent","comments_text","comments","file_image_binary"]
	
	# start SIDEBAR
	# Standard fields for all records
	ret.append("\n\n<div class=\"standardfields\">\n")
	ret.append("<a href=\"javascript:toggle('standardtable')\">&raquo;</a><br />")

	ret.append("<table class=\"standardtable\" id=\"standardtable\" cellspacing=\"0\" cellpadding=\"5\">")

	ret.append("<tr><td colspan=\"2\" class=\"standardtable_roundedtop\"></td></tr>");

	# Timestamps
	ret.append("<tr><td class=\"standardtable_shaded\">Created:</td><td class=\"standardtable_shaded\">Modified:</td></tr>")
	ret.append("<tr><td class=\"standardtable_shaded\">%s<br />%s</td><td class=\"standardtable_shaded\">%s<br />%s</td></tr>"%(dict["creationtime"],dict["creator"],dict["modifytime"],dict["modifyuser"]))

	# Creation time
#	ret.append("<tr><td class=\"standardtable_shaded\" id=\"standardtable_rightborder\">Created: %s <!-- %s --></td></tr>"%(dict["creationtime"],dict["creator"]))

	# Modified time
#	ret.append("<tr><td class=\"standardtable_shaded\">Modified: %s <!-- %s --></td></tr>"%(dict["modifytime"],dict["modifyuser"]))

	# Any comments attached to file
	if dict["comments_text"]: 
		recomments = pcomments.sub("<br />",dict["comments_text"])
		ret.append("<tr><td colspan=\"2\"><span id=\"comments_main\">Comments:<br />%s</span></td></tr>"%recomments)

	# Comment history
	ret.append("<tr><td colspan=\"2\"><a href=\"javascript:toggle('comments_history')\">+ History:</a><br /><span id=\"comments_history\">")
	comments = dict["comments"]
	for i in comments: 
		ret.append("%s<br />"%str(i))
	ret.append("</span></td></tr>")

	# Permissions
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

	# Views
	ret.append("<tr><td colspan=\"2\">+ Views: ")
	ret.append("<a href=\"javascript:hideclass('recordview');qshow('dicttable');\">params</a> ")

	k = viewdef.keys()
	k.reverse()
	for i in k:
		j = re.sub("view","",i)
		ret.append("<a href=\"javascript:qhide('dicttable');hideclass('recordview');qshow('recordview_%s');\">%s</a> "%(i,j))
	ret.append("</td></tr>")

	# Attach comment
	js = "javascript:window.open('/db/addcommentform?name=%s','Add comment','width=1024,height=750,location=no,status=no,menubar=no,resizable=yes,scrollbars=yes')"%dict.recid
	ret.append("<tr><td colspan=\"2\"><span onclick=\"%s\">+ Append comment</span></td></tr>"%js)
	
	
	# Add child record
	ret.append("<tr><td colspan=\"2\"><a href=\"\"><a href=\"javascript:toggle('addchild')\">+ Add child</a>")
	ret.append("<span style=\"display:none\" id=\"addchild\"><ul>")
	ftn=db.getrecorddefnames()
	for i in ftn:
		ret.append("<li><a href=\"/db/newrecord?rdef=%s&parent=%s\">%s</a></li>"%(i,dict.recid,i))
		
	ret.append("</span></td></tr>")
	ret.append("</table>")

	# If there is a data file, show it
	bdo = dict["file_image_binary"]
	if bdo:
		# If it's a tile, link to viewer, else just download it
		if bdo[0:3] == "bdo":
			ret.append("<div class=\"viewbinary\"><a href=\"\" onclick=\"javascript:window.open('/db/tileimage/%s','tilebrowser','status=0,location=0,toolbar=0,width=550,height=650');return false\">View Binary Data</a></div>"%bdo[4:])
		else:
			ret.append("<div class=\"viewbinary\"><a href=\"%s\">Download Binary Data</a></div>"%bdo)

	# Draw tooltips (inside sidebar area: hidden)
	# make item name dictionary to reuse later
	itemdescshort = {}
	for k,v in dict.items():
		try: item=db.getparamdef(str(k))
		except: continue
		itemdescshort[item.name] = item.desc_short
		ret.append("""\n\n
		<div id="tooltip_%s" class="tooltip">
		Parameter Name: %s<br />Variable type: %s<br />Description: %s<br />Property: %s
		</div>\n\n"""%(item.name,item.name,item.vartype,item.desc_short,item.property))

	ret.append("</div>")
	# End sidebar	
	

	# VIEWS: new parser
	# re1 grabs all vars and their default values
	# re2 grabs placeholders for data type names
	# re3 grabs macros
#	re1 = "(\$\$(\w*)(?:=\"([\w\s]+)\")?)[\s<]?"
#	re2 = "(\$\#(\w*))\s?"
#	re3 = "(\$\@(\w*)(?:\((\w*)\))?)[\s<]?"
#	p = re.compile(re1)
#	p2 = re.compile(re2)
#	p3 = re.compile(re3)

	re1 = supp.regexparser()
	p = re.compile(re1)




	for viewtype in viewdef.keys():
		# run view parser
		q = viewdef[viewtype]
		iterator = p.finditer(q)
		
		for match in iterator:
			if match.group("name1"):
				try: item=db.getparamdef(match.group("name1"))
				except: continue
				q = re.sub(re.sub("\$","\$",match.group("name")),item.desc_short,q)

			elif match.group("var1"):
				try: value1 = dict[match.group("var1")]
				except:	value1 = "<span style=\"color:grey\">%s</span>"%match.group("var2")
				if value1:
					value = pcomments.sub("<br />",str(value1))
				# include popup
#				print "%s: %s"%(match.group("var1"),value)
				popup = "onmouseover=\"tooltip_show('tooltip_%s');\" onmouseout=\"tooltip_hide('tooltip_%s');\""%(match.group("var1"),match.group("var1"))
				repl = re.sub("\$","\$",match.group("var"))
#				print "repl: %s"%repl
				q = re.sub(repl,"<span class=\"viewparam\" %s>%s</span>"%(popup,value),q)
#				q = re.sub(repl + r"\b","<span class=\"viewparam\" %s>%s</span>"%(popup,value),q)

			elif match.group("macro1"):
				value = supp.macro_processor(match.group("macro1"),match.group("macro2"),dict.recid,ctxid=ctxid)
				repl = re.sub("\$","\$",match.group("macro"))
				repl2 = re.sub("\@","\@",repl)
				repl3 = re.sub("\(","\(",repl2)
				repl4 = re.sub("\)","\)",repl3)
				q = re.sub(repl4,str(value),q)


		# now put the rendered view into the document
		ret.append("\n\n<div class=\"recordview\" style=\"display:none\" id=\"recordview_%s\">%s</div>"%(viewtype,q))
		
	# End of defined views.
	
	# Automatically generated parameter view is called "dicttable"
	ret.append("\n<div class=\"dicttable\" id=\"dicttable\">")

	ret.append("\n\n<table cellspacing=\"0\" cellpadding=\"0\">\n")
	skipped = 0
	
	# for each key value pair in the record dict; sort first
	items = itemdescshort.items()
	items.sort(lambda x,y: cmp(x[1],y[1]))
	for k in items:

		js = """onmouseover="tooltip_show('tooltip_%s');" onmouseout="tooltip_hide('tooltip_%s');" """%(k[0], k[0])

		# missing is a passed variable: if field is empty, move it to the bottom box with other emtpy vars
		if missing and dict[k[0]] == "":
			skipped = 1
		# if it's not empty and not held in the sidebar, make a table entry
		elif not special.count(k[0]):
			recomments = pcomments.sub("<br />",str(dict[k[0]]))
			ret.append("\t<tr>\n\t\t<td class=\"pitemname\" id=\"td_%s\" %s><a href=\"%s%s\">%s</a></td>\n\t\t<td %s><span class=\"viewparam\">%s</span></td>\n\t</tr>\n"%(k[0],js,proto,k[0],k[1],js,recomments))
		
	ret.append("</table>")
	# end of the dict table

	# Unused record type fields
	if skipped:
		ret.append("\n\n<div class=\"emptyfields\">Emtpy fields: ")
		for k in dict.items():
			if dict[k[0]] == "":
				ret.append("<a href=\"%s%s\">%s</a>, \n"%(proto,k,itemdescshort[k[0]]))
		ret.append("\n</div>")

	ret.append("\n</div>\n")
	# end of the parameter view

	return "".join(ret)




def html_tileimagepopup(path,args,ctxid,host):
	global db

	name,fpath=db.getbinary(path[1],ctxid,host)
	fpath=fpath+".tile"
	
	if not args.has_key("x") :
		dims=supp.get_tile_dim(fpath)
		dimsx=[i[0] for i in dims]
		dimsy=[i[1] for i in dims]
		if not args.has_key("level") : lvl=len(dims)
		else: lvl=int(args["level"][0])
		
		ret=[tmpl.html_header("Micrograph Viewer",init="tileinit(%s,%s,%s)"%(str(dimsx),str(dimsy),path[1]),short=1)]

		ret.append(tmpl.singleheader("Micrograph Viewer",short=1))
		ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
		
		


		ret.append("""
		<div id="outerdiv">
			<div id="innerdiv">LOADING</div>
		</div>

		<br><br><div id="dbug"></div>


		<button onclick=zoomout()>Zoom -</button><button onclick=zoomin()>Zoom +</button><a href=%s?level=-1&x=0&y=0><button>pspec</button></a><a href=%s?level=-2&x=0&y=0><button>plot</button></a><br>
		"""%(path[1],path[1]))
		
		
		ret.append("</div><div style=\"clear:both\"></div>")
		ret.append(tmpl.html_footer(short=1))
		return "".join(ret)		

		
	try: ret=supp.get_tile(fpath,int(args["level"][0]),int(args["x"][0]),int(args["y"][0]))
	except: return "Invalid tile"
	return ret


def html_tileimage(path,args,ctxid,host):
	global db

	name,fpath=db.getbinary(path[1],ctxid,host)
	fpath=fpath+".tile"
	
	if not args.has_key("x") :
		dims=supp.get_tile_dim(fpath)
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


		<div id="content">"""%(str(dimsx),str(dimsy),path[1]))

		ret.append(tmpl.singleheader("Tile Viewer",short=1))
		ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

		ret.append("""
		<div id="outerdiv">
			<div id="innerdiv">LOADING</div>
		</div>

		<br><br><div id="dbug"></div>


		<button onclick=zoomout()>Zoom -</button><button onclick=zoomin()>Zoom +</button><a href=%s?level=-1&x=0&y=0><button>pspec</button></a><a href=%s?level=-2&x=0&y=0><button>plot</button></a><br>
		"""%(path[1],path[1]))

		ret.append("</div>")

		ret.append(tmpl.html_footer(short=1))
		return " ".join(ret)
		
	try: ret=supp.get_tile(fpath,int(args["level"][0]),int(args["x"][0]),int(args["y"][0]))
	except: return "Invalid tile"
	return ret


# a debugging fxn
def html_getbinarynames(path,args,ctxid,host):
	global gb
	
	ret = []
	ret.append(tmpl.html_header("Binary Ids"))
	ret.append(tmpl.singleheader("Binary Ids"))
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

	ret.append(tmpl.html_footer())
	return " ".join(ret)




def html_paramdefs(path,args,ctxid,host):
	global db
	
	ftn=db.getparamdefnames()
	
#	ret=[tmpl.html_header("EMEN2 Query Results",init=init)]
	init="parambrowserinit()"
	ret=[tmpl.html_header("EMEN2 ParamDefs",init=init)]
		
	ret.append(tmpl.singleheader("Parameter Definitions"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Parameter Browser</h2><br />")
	
	ret.append(tmpl.parambrowser(viewfull=1,edit=1,addchild=1))
	
#	ret.append("</div>")
#	ret.append("<div class=\"switchpage\" id=\"page_params\">")
	ret.append("<div style=\"clear:both\"><h2>Registered Parameters</h2><br />%d defined:"%len(ftn))	
	
	ret.append(supp.html_htable(ftn,3,"/db/paramdef?name="))

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret) 





def html_paramdef(path,args,ctxid,host):
	global db
	
	item=db.getparamdef(args["name"][0])
	
	ret=[tmpl.html_header("EMEN2 ParamDef Description",init="parambrowserinit('%s')"%item.name)]
	
	ret.append(tmpl.singleheader("Parameter Definition"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append(tmpl.parambrowser(viewfull=1,edit=1,addchild=1))
	
#	ret.append("<div style=\"clear:both\"><h2>Experimental Parameter (ParamDef): <i>%s</i></h2>"%item.name)
	
#	ret.append("""\n\n<table><tr><td>Name</td><td>%s</td></tr>
#	<tr><td>Variable Type</td><td>%s</td></tr>
#	<tr><td>Short Description</td><td>%s</td></tr>
#	<tr><td>Long Description</td><td>%s</td></tr>
#	<tr><td>Property</td><td>%s</td></tr>
#	<tr><td>Default Units</td><td>%s</td></tr>
#	<tr><td>Creator</td><td>%s <!-- %s --></td></table><a href="/db/newparamdef?parent=%s">Add a new child parameter</a>"""%(
#	item.name,item.vartype,item.desc_short,item.desc_long,item.property,item.defaultunits,item.creator,item.creationtime,item.name))
	
	
#	parents=db.getparents(item.name,keytype="paramdef",ctxid=ctxid)
#	if len(parents)>0 :
#		ret.append("<h2>Parents:</h2><ul>")
#		for p in parents:
#			ret.append("<li><a href=\"/db/paramdef?name=%s\">%s</a></li>"%(p,p))
#		ret.append("</ul>")
	
#	children=db.getchildren(item.name,keytype="paramdef",ctxid=ctxid)
#	if len(children)>0 :
#		ret.append("<h2>Children:</h2><ul>")
#		for c in children:
#			ret.append("<li><a href=\"/db/paramdef?name=%s\">%s</a></li>"%(c,c))
#	ret.append("</ul>")
# ret.append("</div>")	
	
	ret.append("</div>")
	
	ret.append(tmpl.html_footer())
	
	return "".join(ret)





def html_newparamdef(path,args,ctxid,host):
	"""Add new ParamDef form. Also does the actual ParamDef insertion"""	
	global db,DB

	ret=[tmpl.html_header("EMEN2 Add Experimental Parameter")]
	
	ret.append(tmpl.singleheader("Add Parameter"))
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
		ret.append(tmpl.html_footer())
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		supp.argmap(args)
		
		ret.append(html_form(method="GET",action="/db/newparamdef",items=(("","parent","hidden"),("Name:","name","text"),
		("Variable Type","vartype","select",("int","float","string","text","url","image","binary","datetime","link","child")),
		("Short Description","desc_short","text"),("Long Description","desc_long","textarea","",(60,3)),
		("Physical Property","property","select",DB.valid_properties),("Default Units","defaultunits","text")),args=args))

		ret.append("</div>")
		ret.append(tmpl.html_footer())

		return "".join(ret)





def html_recorddefs(path,args,ctxid,host):
	global db
	
	ftn=db.getrecorddefnames()
	for i in range(len(ftn)):
		ftn[i]=(ftn[i],len(db.getindexbyrecorddef(ftn[i],ctxid)))
		
	init="protobrowserinit()"
	ret=[tmpl.html_header("EMEN2 RecordDefs",init=init)]
		
	ret.append(tmpl.singleheader("Record Definitions"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>Record Definition Browser</h2><br />")
	
	ret.append(tmpl.protobrowser(viewfull=1,edit=1,addchild=1))
	
	ret.append("<h2>Registered Record Definition</h2><br>%d defined:"%len(ftn))
	ret.append(supp.html_htable2(ftn,3,"/db/recorddef?name="))

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret)





def html_recorddef(path,args,ctxid,host):
	global db
	
	
	item=db.getrecorddef(args["name"][0],ctxid)
	
	ret=[tmpl.html_header("EMEN2 RecordDef Description",init="protobrowserinit('%s')"%item.name)]
	
	ret.append(tmpl.singleheader("RecordDef Definition"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append(tmpl.protobrowser(viewfull=1,edit=1,addchild=1))
		
#	ret.append("<h2>Experimental Protocol (RecordDef): <i>%s</i></h2><br>"%item.name)
#	ret.append("<div style=\"clear:both\">")
	
	parents=db.getparents(item.name,keytype="recorddef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<h2>Parents:</h2>")
		for p in parents:
			ret.append('<a href="/db/recorddef?name=%s">%s</a> '%(p,p))
	
	children=db.getchildren(item.name,keytype="recorddef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<h2>Children:</h2> ")
		for c in children:
			ret.append('<a href="/db/recorddef?name=%s">%s</a> '%(c,c))

	ret.append("<h2>Parameters:</h2>")
	ret.append(supp.html_dicttable(item.params,"/db/paramdef?name="))
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
	ret.append(supp.html_htable(itm,6,"/db/record?name="))
	
	ret.append("</div>")
	
	ret.append(tmpl.html_footer())
	
	return "".join(ret)





def html_newrecorddef(path,args,ctxid,host):
	global db, DB
	ret=[tmpl.html_header("EMEN2 Add Protocol Definition")]
	
	ret.append(tmpl.singleheader("New Protocol Definition"))
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
		ret.append(tmpl.html_footer())
		return "".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		supp.argmap(args)
		ret.append(html_form(method="GET",action="/db/newrecorddef",items=(("","parent","hidden"),("Name:","name","text"),
		("Experiment Description","mainview","textarea","",(80,16)),("Summary View","summary","textarea","",(80,8)),
		("One Line View","oneline","textarea","",(80,4)),("Private Access","private","checkbox")),args=args))
		ret.append("</div>")
		ret.append(tmpl.html_footer())
	
		return "".join(ret)
	



def html_records(path,args,ctxid,host):
	ftn=db.getrecordnames(ctxid,host=host)
	ret=[tmpl.html_header("EMEN2 Records")]
	
	ret.append(tmpl.singleheader("All Records"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>All accessible records</h2>")
	ret.append(supp.html_htable(ftn,3,"/db/record?name="))

	ret.append("</div>")
	ret.append(tmpl.html_footer())
	return "".join(ret)





def html_queryform(path,args,ctxid,host):
	ret=[tmpl.html_header("EMEN2 DB Query",init="parambrowserinit('root','form_query')")]
	ret.append(tmpl.singleheader("Database Query"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append(	 html_form(method="GET",action="/db/query",items=(("","parent","hidden"),("Query:","query","textarea","",(80,8))))	)

	ret.append(tmpl.parambrowser(select=1,viewfull=1,hidden=0))

	ret.append("</div>")

	ret.append(tmpl.html_footer())

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

	ret=[tmpl.html_header("EMEN2")]

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
	ret.append(supp.encapsulate_render_grouptable(path,args,ctxid,host))
		
#	ret.append("</div>")
		
#	ajaxargs["zone"] = ["zone2"]
#	ret.append("""
#	<div id="zone2">
#	%s
#	</div>
#	"""%html_rendergrouptable(path,ajaxargs,ctxid,host))

	ret.append("</div>")
	ret.append(tmpl.html_footer())

	return "".join(ret)




	

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
			plotfile = plot.render_plot(query,raw)
			isplot = True
		else:
			plotfile = ""
			isplot = False

#		clear work flow cache	
#		clearworkflowcache(ctxid)
	
		with = {'wftype':'querycache','desc':str(args["query"][0]),'longdesc':str(args["query"][0]),'resultcount':resultcount,'appdata':groupl,'plotfile':plotfile}
		newwf = db.newworkflow(with)
		wfid = db.addworkflowitem(newwf,ctxid)
		
#		print "wfid: %s	  wfid as list: %s\n"%(wfid,list(str(wfid)))
		
		args["wfid"]= [str(wfid)]


	ret = []

	if args.has_key("viewinit"):
		init="switchid('%s');"%str(args["viewinit"][0])
		ret=[tmpl.html_header("EMEN2 Query Results",init=init)]
	elif isplot:
		init="switchid('allview');"
		ret=[tmpl.html_header("EMEN2 Query Results",init=init)]
	else:
		ret.append(tmpl.html_header("EMEN2 Query Results",init="showallids();"))
	
	
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
		ret.append(supp.render_groupedhead(groupl,ctxid=ctxid))


	ret.append("\n</div>")
	
	ret.append("<div id=\"pagecontainer\">")
	
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
			ret.append(supp.encapsulate_render_grouptable(path,args,ctxid,host))

	ret.append(tmpl.html_footer())

	return " ".join(ret)


def html_cwf(path,args,ctxid,host):
	"""Example"""
	global db

	ret=[tmpl.html_header("EMEN2")]

	ret.append(tmpl.singleheader("CWF"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Cleared</h2><br />") 

	# stuff goes here
	supp.clearworkflowcache(ctxid)
	ret.append("Cleared work flow cache.")

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret)



def html_record(path,args,ctxid,host):
	global db
	
	name = int(args["name"][0])

#	print "html_record dir: %s"%dir()
		
	item=db.getrecord(name,ctxid)

	view=db.getrecorddef(item["rectype"],ctxid)
	viewdef = view.views
	
#	if not viewdef.has_key("defaultview"):
#		viewdef["defaultview"] = view.mainview
#	else:
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

	# get the kids, and group them
	queryresult = db.getchildren(name,ctxid=ctxid)
	resultcount = len(queryresult)
	groups = db.groupbyrecorddef(queryresult,ctxid)
	groupl = groupsettolist(groups)

	# fix this with a better mechanism. clear the workflow to keep things moving fast.
	# clear work flow cache
#	clearworkflowcache(ctxid)

	# store the result count and grouped list in a workflow item
	with = {'wftype':'recordcache','desc':"record cache",'longdesc':"record cache",'resultcount':resultcount,'appdata':groupl}
	newwf = db.newworkflow(with)
	wfid = db.addworkflowitem(newwf,ctxid)
	
	args["wfid"] = [str(wfid)]
	

	# is there a view type in the args?
	if args.has_key("viewinit"):
		init="switchid('%s')"%str(args["viewinit"][0])
		ret=[tmpl.html_header("EMEN2 Record",init=init)]
	else:
		ret=[tmpl.html_header("EMEN2 Record")]
	
	# parents tree
	ret.append(supp.parent_tree(name,ctxid=ctxid))
	
	# switching buttons
	ret.append("\n\n<div class=\"switchcontainer\">\n")
	ret.append("\t<div class=\"switchbutton\" id=\"button_mainview\"><a href=\"javascript:switchid('mainview');\">%s <!-- %s --></a></div>\n"%(item["recname"],item["rectype"]))
	if queryresult:
		ret.append("\t<div class=\"switchshort\">&raquo;</div>")
		ret.append("\t<div class=\"switchbutton\" id=\"button_allview\"><a href=\"javascript:showallids()\">All Children</a></div>\n")
		ret.append("\t<div class=\"switchshort\">&raquo;</div>\n")
		# one for each group of children...
		ret.append(supp.render_groupedhead(groups,ctxid=ctxid))
	ret.append("\n\n</div>")

	ret.append("<div id=\"pagecontainer\">")

	# render the 'record page': sidebar, views
	ret.append("\n\n<div class=\"switchpage\" id=\"page_mainview\">")
	ret.append(html_record_dicttable(item,"/db/paramdef?name=",viewdef,missing=1,ctxid=ctxid))
	ret.append("\n</div>\n\n")

	# render all the children grouped together
	ret.append(supp.render_groupedlist(path,args,ctxid,host))


	ret.append(tmpl.html_footer())
	
	return " ".join(ret)





def html_newrecord(path,args,ctxid,host):
	global db
	ret=[tmpl.html_header("EMEN2 Add Record")]
	
	ret.append(tmpl.singleheader("Add Record"))
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

#		print "submitting with args: %s"%d
#		print "shortened args: %s"%d2
#		print "items: %s"%bld
#		print "host: %s"%host
		ret.append(html_form(method="POST",action="/db/newrecord",items=bld,args=d2))
		ret.append("</div>")
		ret.append(tmpl.html_footer())
		return "".join(ret)

#	print "new record args: %s"%args

	if args.has_key("parent"):
		parent = int(args["parent"][0])
		del args["parent"]

	supp.argmap(args)
	rec=db.newrecord(args["rectype"],ctxid,host,init=0)
#	del args["rdef2"]
	rec.update(args)

	rid=db.putrecord(rec,ctxid,host)


	if parent :
		db.pclink(parent,rid,"record",ctxid)

	ret.append('Record add successful.<br />New id: <a href="/db/record?name=%d">%d</a><br><br><a href="/db/index.html">Return to main menu</a>'%(rid,rid))
	
	ret.append("</div>")
	ret.append(tmpl.html_footer())
		
	return ''.join(ret)
	
	
	
	
	
def html_users(path,args,ctxid,host):
	global db
	
	ftn=db.getusernames(ctxid,host)
	ret=[tmpl.html_header("EMEN2 Users")]

	ret.append(tmpl.singleheader("Users"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Users</h2><br />%d defined:"%len(ftn))
	ret.append(supp.html_htable(ftn,3,"/db/user?uid="))

	ret.append("</div>")
	ret.append(tmpl.html_footer())
	return "".join(ret)





def html_newuserqueue(path,args,ctxid,host):
	global db
	
	ftn=db.getuserqueue(ctxid,host)
	ret=[tmpl.html_header("EMEN2 User Queue")]
	
	ret.append(tmpl.singleheader("New User Queue"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>New Users Waiting Approval</h2><br>%d defined:"%len(ftn))
	ret.append(supp.html_htable(ftn,3,"/db/approveuser?username="))

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret)





def html_user(path,args,ctxid,host):
	global db
	
	if not args.has_key("uid") : args["uid"]=args["username"]
	ret=[tmpl.html_header("EMEN2 User")]
	
	ret.append(tmpl.singleheader("User"))
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
	if u[0]==item.username or -1 in u[1]: pwc='<br><a href="/db/chpasswd?username=%s">Change Password</a>'%args["uid"][0]+"</div>"+tmpl.html_footer()
	else: pwc="</div>"+tmpl.html_footer()
	
	return "".join(ret)+html_form(method="GET",action="/db/user",items=(("Username","username","text",14),
		("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
		("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea","",(40,3)),
		("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
		("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16),
		("Groups","groups","text",40)),args=item.__dict__)+pwc





def html_chpasswd(path,args,ctxid,host):
	supp.argmap(args)
	ret=[tmpl.html_header("EMEN2 Change Password")]
	
	ret.append(tmpl.singleheader("Change Password"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h2>User: <i>%s</i></h2><br>"%args["username"])
	
	if args.has_key("password") :
		if args["password"]!=args["password2"] : raise SecurityError,"Passwords do not match"
		db.setpassword(args["username"],args["oldpassword"],args["password"],ctxid,host)
		ret.append('<br><b>Password Changed</b><br><br><a href="/db/index.html">Return Home</a>')
		ret.append("</div>")
		ret.append(tmpl.html_footer())
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
	
	return "".join(ret)+html_form(action="/db/chpasswd",items=itm,args=args)+"</div>"+tmpl.html_footer()




	
def html_approveuser(path,args,ctxid,host):
	db.approveuser(args["username"][0],ctxid,host)
	return html_newuserqueue(path,args,ctxid,host)

def html_addcommentform(path,args,ctxid,host):
	ret=[tmpl.html_header("Append Comment: %s"%args["name"][0],init="parambrowserinit('root','form_comment')",short=1)]
	
	ret.append(tmpl.singleheader("Append Comment: %s"%args["name"][0],short=1))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	if args.has_key("added"):
		ret.append("<div class=\"alertsuccess\">Added comment</div>")


	ret.append("""
		
	<form action="/db/addcomment" target="_parent" method="GET">
	
	<input type="hidden" name="parent" value="" />
	
<input type="hidden" name="name" value="%s" />
		Comment: <br />
		<textarea name="comment" cols="80" rows="8" id="form_comment"></textarea> <br />
		<input type="submit" value="Submit" />
</form>
	
	
	"""%args["name"][0])

#	ret.append(html_form(method="GET",action="/db/addcomment",items=(("","parent","hidden"),("","name","hidden"),("Comment:","comment","textarea","",(80,8))),args={"name":args["name"][0]})	)

	r = db.getrecord(int(args["name"][0]),ctxid=ctxid)
	ret.append("<div class=\"parent\">Update Existing Value</div><div class=\"parents\">")
	for i in r.items_dict().keys():
		ret.append("<span class=\"child\" onclick=\"display('%s','paramdef')\">%s</span> "%(i,i))
	ret.append("</div>")

	ret.append(tmpl.parambrowser(all=1))

	ret.append("</div><div style=\"clear:both\"></div>")

	ret.append(tmpl.html_footer(short=1))
	return "".join(ret)		


def html_addcomment(path,args,ctxid,host):
	r = db.getrecord(int(args["name"][0]),ctxid=ctxid)
	r["comments"] = args["comment"][0]
	r.commit()
	print "Committed comment to record %s: %s"%(args["name"][0],args["comment"][0])
	args["added"] = ["1"]
	return html_addcommentform(path,args,ctxid,host)

	
def html_newuser(path,args,ctxid,host):
	global db, DB
	ret=[tmpl.html_header("EMEN2 New User Form")]
	
	ret.append(tmpl.singleheader("New User"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")
	
	ret.append("<h1>New User Application</h1><br>")
	if args.has_key("username") :
		print "New user args: %s"%args

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
		ret+=['<br><br>New User <i>%s</i> added.<br><br>Press <a href="index.html">here</a> for main menu.'%str(args["username"]),"</div>"+tmpl.html_footer()]
		return " ".join(ret)

	# Ok, if we got here, either we need to display a blank form, or a filled in form with an error
	else:
		supp.argmap(args)
		return "".join(ret)+html_form(action="/db/newuser",items=(("Username","username","text",14),("Password","password","password",14),
			("First Name","name1","text",16),("Middle Name","name2","text",6),("Family Name","name3","text",20),("Privacy","privacy","checkbox"),
			("Institution","institution","text",30),("Department","department","text",30),("Address","address","textarea","",(40,3)),
			("City","city","text",30),("State","state","text",3),("Zip Code","zipcode","text",10),("Country","country","text",30),
			("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16)),args=args)+tmpl.html_footer()





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
			ret.append('\t<tr>\n\t\t<td>%s</td>\n\t\t<td><textarea name="%s" cols="%d" rows="%d" id="form_%s">%s</textarea></td>\n\t</tr>\n'%(i[0],i[1],i[4][0],i[4][1],i[1],i[3]))
		elif i[2]=="password" :
			if (len(i)<4) : i=i+(20,)
			ret.append('\t<tr>\n\t\t<td>%s</td>\n\t\t<td><input type="%s" name="%s" value="%s" size="%d" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],str(args.get(i[1],"")),int(i[3])))
		elif i[2]=="text" :
			if (len(i)<4) : i=i+(20,)
			ret.append('\t<tr>\n\t\t<td>%s</td><td><input type="text" name="%s" value="%s" size="20" id="form_%s" /></td>\n\t</tr>\n'%(i[0],i[1],i[1],i[1]))
		elif i[2]=="hidden" :
			ret.append('<input type="hidden" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[1],str(args.get(i[1],""))))
		else:
			ret.append('\t<tr>\n\t\t<td>%s</td><td><input type="%s" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],args.get(i[1],"")))

	ret.append('\t<tr>\n\t\t<td></td>\n\t\t<td><input type="submit" value="Submit" /></td>\n\t</tr>\n</form>\n</table>\n')
	
	return "".join(ret)






def html_reloadparent(path,args,ctxid,host):
	return("""
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">

<head>
	<meta http-equiv="Content-type" content="text/html; charset=utf-8">
	<title>Action Successful</title>
	
	<script type="text/javascript" charset="utf-8">
 			if (window.opener && !window.opener.closed) {
    			window.opener.document.reload();
  				window.close();
			}
	</script>

</head>

<body id="" onload="">
	Action Successful
</body>

</html>
	""")
