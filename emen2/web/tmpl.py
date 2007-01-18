################################################### 
## TEMPALTE FUNCTIONS #############################
###################################################

print "...loading %s"%__name__


from sets import Set
import re
#import os
from emen2.ts import db
#import html
#import tmpl
import supp
#import plot


def form(action="",items=(),args={},method="POST"):
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


def form_new(action="",items=(),method="POST"):
	ret = []
	
	for i in items:
		if not i.has_key("cols"): i["cols"] = 20
		if not i.has_key("rows"): i["rows"] = 5
		if not i.has_key("default"): i["default"] = ""

		if i["form"] == "select":
			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><select name="%s">'%(i["desc"],i["name"]))
			defaultchoice = ""
			if i["default"]: ret.append('<option selected>%s</option>'%default)
			for j in i["choices"]:
				if j != i["default"]:
					ret.append('<option>%s</option>'%j)
			ret.append('</select></div>')
				
		elif i["form"] == "textarea":
			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><textarea name="%s" cols="%d" rows="%d" id="form_%s">%s</textarea /> </div>'%(i["desc"],i["name"],i["cols"],i["rows"],i["name"],i["default"]))
		elif i["form"] == "password":
			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><input type="password" name="%s" value="%s" size="%s" /></div>'%(i["desc"],i["name"],i["default"],i["cols"]))
		elif i["form"] == "text":
			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><input type="text" name="%s" value="%s" size="%s" id="form_%s" /></div>'%(i["desc"],i["name"],i["default"],i["cols"],i["name"]))
		elif i["form"] == "hidden":
			ret.append('<input type="hidden" name="%s" value="%s" />'%(i["name"],i["default"]))
		else:
			ret.append('<div class="formcol1">Unknown field type: %s</div>'%i)

	return '<div class="formdiv"><form action="%s" method=%s>%s<div class="formcol1"></div><div class="formcol2"><input type="submit" value="Submit" /></div></form></div>'%(action,method," ".join(ret))
	

def record_dicttable(dict,proto,viewdef,missing=0,ctxid=None):
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
	ret.append("<tr><td colspan=\"2\"><a href=\"javascript:toggle('comments_history')\">+ History:</a><br /><div id=\"comments_history\">")
	comments = dict["comments"]
#	p = re.compile("LOG")
	for i in comments: 
		ret.append("<span class=\"sidebar_smallheader\"><a href=\"/db/user?uid=%s\">%s</a>@%s:</span><br />%s<br />"%(i[0],i[0],i[1],i[2]))

	ret.append("</div></td></tr>")

	# Permissions
	ret.append("<tr><td colspan=\"2\"><a href=\"javascript:toggle('comments_permissions')\">+ Permissions:</a><br /><span id=\"comments_permissions\">")

	ret.append(supp.permissions(dict,edit=1))

	ret.append("</span></td></tr>")

	# Views
	ret.append("<tr><td colspan=\"2\">+ Views: ")
	ret.append("<a href=\"javascript:hideclass('page_recordview');qshow('page_recordview_dicttable');\">params</a> ")

	k = viewdef.keys()
	k.reverse()
	for i in k:
		j = re.sub("view","",i)
		ret.append("<a href=\"javascript:hideclass('page_recordview');qshow('page_recordview_%s');\">%s</a> "%(i,j))
	ret.append("</td></tr>")

	# Attach comment
	js = "javascript:window.open('/db/addcommentform?name=%s','Add comment','width=1024,height=750,location=no,status=no,menubar=no,resizable=yes,scrollbars=yes')"%dict.recid
	ret.append("<tr><td colspan=\"2\"><span class=\"jslink\" onclick=\"%s\">+ Add comment</span></td></tr>"%js)
	
	# Attach file
	js = "javascript:window.open('/db/addfileform?name=%s','Attach file','width=1024,height=750,location=no,status=no,menubar=no,resizable=yes,scrollbars=yes')"%dict.recid
	ret.append("<tr><td colspan=\"2\"><span class=\"jslink\" onclick=\"%s\">+ Attach file</span></td></tr>"%js)
	
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
				try:
					q = re.sub(repl,"<span class=\"viewparam\" %s>%s</span>"%(popup,value),q)
				except:
					pass
#				q = re.sub(repl + r"\b","<span class=\"viewparam\" %s>%s</span>"%(popup,value),q)

			elif match.group("macro1"):
				value = supp.macro_processor(match.group("macro1"),match.group("macro2"),dict.recid,ctxid=ctxid)
				repl = re.sub("\$","\$",match.group("macro"))
				repl2 = re.sub("\@","\@",repl)
				repl3 = re.sub("\(","\(",repl2)
				repl4 = re.sub("\)","\)",repl3)
				q = re.sub(repl4,str(value),q)


		# now put the rendered view into the document
		ret.append("\n\n<div class=\"page_recordview\" style=\"display:none\" id=\"page_recordview_%s\">%s</div>"%(viewtype,q))
		
	# End of defined views.
	
	# Automatically generated parameter view is called "dicttable"
	ret.append("\n<div class=\"page_recordview\" id=\"page_recordview_dicttable\">")

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

def header(name,init=None,short=0):
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

<script type="text/javascript" src="/switch.js"></script>
<script type="text/javascript" src="/ajax.js"></script>
<script type="text/JavaScript" src="/parambrowser.js"></script>
<script type="text/javascript" src="/tile.js"></script>


</head>

<body onLoad="javascript:init();"""%name)

	if init:
		ret.append(str(init))

	ret.append("\">")
#	ret.append("""">
	if not short:
		ret.append("""

<div id="container">

<div id="title">
	<a href="/db/">
	<img id="toplogo" src="/images/logo_trans.png" alt="NCMI" /> National Center for Macromolecular Imaging
	</a>
</div>


<div id="nav_table"> 
	<div class="nav_tableli"><a href="/db/record?name=0">Browse Database</a></div>
	<div class="nav_tableli"><a href="/db/queryform">Query Database</a></div>
	<div class="nav_tableli"><a href="/db/workflow">My Workflow</a></div>
	<div class="nav_tableli"><a href="/db/paramdefs">Parameters</a></div>
	<div class="nav_tableli"><a href="/db/recorddefs">Protocols</a></div>
</div>
		""")
		
	ret.append("""
<div id="content">
	""")

	return " ".join(ret)


def footer(short=0):
	"""Common header block, includes </body>"""
	ret = []
	ret.append("</div>")
	
	if not short:
		ret.append("""
<div id="bottom">

<img id="bottomlogo" src="/images/logo_alt_sm.gif" alt="Baylor College of Medicine" />	

<!-- -->

Loggged in as: <br />

Hosted by <a href="http://ncmi.bcm.tmc.edu">NCMI</a>&nbsp;&nbsp;Phone: 713-798-6989 &nbsp;&nbsp;Fax: 713-798-1625<br />
Room N421 Alkek Building, One Baylor Plaza, Houston, TX, 77030<br />
Please mail comments/suggestions to: <a href="mailto:htu@bcm.tmc.edu">WEBMASTER</a><br /><br />

</div></div>
		""")
	ret.append("</div></body></html>")
	return " ".join(ret)
	
def singleheader(title,short=0):
	"""For pages without option tabs, make the single tab"""
	ret = []
	if not short:
		ret.append("""
	<div class="navtreeouter">	
	<div class="navtree">
	<table cellpadding="0" cellspacing="0" class="navtable">
	</table></div>
	</div>""")

	ret.append("""
	<div id="button_main_container">
	<div class="floatcontainer">
		<div class="button_main" id="button_main_mainview"><a href="">%s</a></div>
	</div>
	</div>
	
	<div class=\"pagecontainer\" id="pagecontainer_main">
	
	"""%title)
	
	return " ".join(ret)


def navbar():
	"""Top navigation bar"""
	return """
	"""
	
	
def parambrowser(all=None,viewfull=None,addchild=None,edit=None,select=None,hidden=None):
	form = []
	addchildhtml = ""
	hiddenhtml = ""
	if hidden:
		hiddenhtml = "style=\"display:none\""
	if all:
		select,viewfull,addchild,edit = 1,1,1,1
	if select:
		form.append('<div class="l" onclick="selecttarget()">Select</div>')
	if viewfull:
		form.append('<div class="l"><a id="viewfull" href="">View Full</a></div>')
	if addchild:
		form.append('<div class="l"><a href="javascript:toggle(\'addchild\')">Add Child</a></div>')

		addchildhtml = """
		<form name="full_form" method="POST" action="javascript:make_param()">
		<table>
		<tr><td>Name:</td><td><input type="text"; id = "name_of_new_parameter"></td><tr>
		<tr><td>Parents:</td><td><input type="text"; id="parent_new"></td></tr>
		<tr><td colspan="2">Short description:</td></tr><tr><td colspan="2"><input type="text"; id = "short_description_of_new_parameter"></td></tr>
		<tr><td colspan="2">Long description:</td></tr><tr><td colspan="2"><textarea rows="5" cols="30" id = "long_description_of_new_parameter"></textarea></td></tr>
		
		<tr><td colspan="2">Default units:</td></tr><tr><td colspan="2"><select id = "default_units_of_new_parameter">	
			<option value="None">None</option>
			<option value="%">Percent (%)</option>
			<option value="%RH">Relative Humidity (%RH)</option>
			<option value="A">Anstroms (A)</option>
			<option value="A/pix">Anstroms/Pixel (A/pix)</option>
			<option value="A^2">Anstroms Squared (A^2)</option>
			<option value="C">Degrees Celsius (C)</option>
			<option value="K">Degrees Kelvin (K)</option>
			<option value="KDa">Kilodaltons (KDa)</option>
			<option value="Pi">Radians (Pi)</option>
			<option value="Amp/cm2">Amperes per cm^2 (Amp/cm2)</option>
			<option value="V">Volts (V)</option>
			<option value="cm">Centimeters (cm)</option>
			<option value="degree">Degrees (degree)</option>
			<option value="e/A2/sec">e/A2/sec</option>
			<option value="kv">Kilovolts (kv)</option>
			<option value="mg/ml">mg/ml concentration (mg/ml)</option>
			<option value="min">Minutes (min)</option>
			<option value="mm">Millimeters (mm)</option>
			<option value="mrad">Milliradians (mrad)</option>
			<option value="ms">Milliseconds (ms)</option>
			<option value="nm">Nanometers (nm)</option>
			<option value="p/ml">? (p/ml)</option>
			<option value="pixels">Pixels</option>
			<option value="s">Seconds (s)</option>
			<option value="ul">Microliters (ul)</option>
			<option value="um">Micrometers (um)</option>
			<option value="unitless">Unitless</option>
		</select></td></tr>

		<tr><td>Vartype:</td><td><select id = "vartype_of_new_parameter">
			<option value="string">String</option>
			<option value="int">Integer</option>
			<option value="float">Floating point</option>
			<option value="stringlist">String List</option>
			<option value="intlist">Integer List</option>	
			<option value="boolean">Boolean</option>
			<option value="datetime">Date</option>
			<option value="text">Text</option>
			<option value="link">Link</option>		
			<option value="choice">Choice</option>
			<option value="binary">Binary</option>
		</select></td></tr>
		
		<tr><td>Property:</td><td><select id = "property_of_new_parameter">
			<option value="None">None</option>
			<option value="count">Count</option>
			<option value="length">Length</option>
			<option value="angle">Angle</option>
			<option value="bfactor">B-factor</option>
			<option value="area">Area</option>
			<option value="concentration">Concentration</option>
			<option value="mass">Mass</option>
			<option value="time">Time</option>
			<option value="volume">Volume</option>
			<option value="density">Density</option>
		</select></td></tr>

		<tr><td>Choices:</td><td><input type="text"; id = "choices_of_new_parameter"></td></tr>


		</table>
		<input type="submit">
		</form>"""
		
#	if edit:
#		form.append('<div class="l">Edit</div>')

	return("""	
	<div id="browserid">Parameter Browser</div>
	<div id="parambrowser" %s>
		<div class="floatleft" id="left">
			<div id="getchildrenofparents"></div>
		</div>

		<div class="floatleft" id="center">
			<div id="focus"></div>
			<div id="getparamdef2"></div>
			<div id="parambuttons">%s<div id="addchild">%s</div></div>
		</div>
		
		<div class="floatleft" id="right">
			<div id="getchildren"></div>
			<div id="getcousins"></div>
		</div>
	</div>
	"""%(hiddenhtml," ".join(form),addchildhtml))	








def protobrowser(all=None,viewfull=None,addchild=None,edit=None,select=None,hidden=None):
	form = []
	addchildhtml = ""
	hiddenhtml = ""
	if hidden:
		hiddenhtml = "style=\"display:none\""
	if all:
		select,viewfull,addchild,edit = 1,1,1,1
	if select:
		form.append('<div class="l" onclick="selecttarget()">Select</div>')
	if viewfull:
		form.append('<div class="l"><a id="viewfull" href="">View Full</a></div>')
	if addchild:
		form.append('<div class="l"><a href="javascript:toggle(\'addchild\')">Add Child</a></div>')

		addchildhtml = """
		<form name="full_form" method="POST" action="javascript:make_proto()">
		<table>
		<tr><td>Name:</td><td><input type="text"; id = "name"></td><tr>
		<tr><td>Parents:</td><td><input type="text"; id="parent_new"></td></tr>
		<tr><td>Exp. Desc.:</td><td><input type="text"; id="mainview"></td></tr>
		<tr><td>Summary:</td><td><input type="text"; id = "summary"></td></tr>
		<tr><td>One line view:</td><td><input type="text"; id = "oneline"></td></tr>
		<tr><td>Private:</td><td><input type="checkbox"; id = "private"></td></tr>
		</table>
		<input type="submit">
		</form>"""
		
#	if edit:
#		form.append('<div class="l">Edit</div>')

	return("""	
	<div id="browserid">Record Definition Browser</div>
	<div id="protobrowser" %s>
		<div class="floatleft" id="left">
			<div id="getchildrenofparents"></div>
		</div>

		<div class="floatleft" id="center">
			<div id="focus"></div>
			<div id="getrecorddef2"></div>
			<div id="parambuttons">%s<div id="addchild">%s</div></div>
		</div>
		
		<div class="floatleft" id="right">
			<div id="getchildren"></div>
			<div id="getcousins"></div>
		</div>
		
		<div id="recorddefsimple"></div>

		
	</div>
	

	"""%(hiddenhtml," ".join(form),addchildhtml))	











def stub(path,args,ctxid,host):
	"""Example"""
	global db

	ret=[tmpl.header("EMEN2")]

	ret.append(tmpl.singleheader("Page"))
	ret.append("<div class=\"pagecontainer\" id=\"page_main_mainview\">")

	ret.append("<h2>Page Title</h2><br />") 

	# stuff goes here

	ret.append("</div>")

	ret.append(tmpl.footer())
	return "".join(ret)
	