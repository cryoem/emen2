################################################### 
## TEMPALTE FUNCTIONS #############################
###################################################


from sets import Set
import re
from emen2.emen2config import *


def form(action="",items=(),args={},method="POST"):
	ret=["""\n\n<table><form action="%s" method=%s>"""%(action,method)]
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
			ret.append('<input style="display:none" type="hidden" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[1],str(args.get(i[1],""))))
		else:
			ret.append('\t<tr>\n\t\t<td>%s</td><td><input type="%s" name="%s" value="%s" /></td>\n\t</tr>\n'%(i[0],i[2],i[1],args.get(i[1],"")))

	ret.append('\t<tr>\n\t\t<td></td>\n\t\t<td><input type="submit" value="Submit" /></td>\n\t</tr>\n</form>\n</table>\n')
	
	return "".join(ret)


# def form_new(action="",items=(),method="POST"):
# 	ret = []
# 	
# 	for i in items:
# 		if not i.has_key("cols"): i["cols"] = 20
# 		if not i.has_key("rows"): i["rows"] = 5
# 		if not i.has_key("default"): i["default"] = ""
# 		if not i.has_key("postfix"): i["postfix"] = ""
# 		if not i.has_key("default"): i["default"] = ""
# 		if not i.has_key("form"): i["form"] = "text"
# 
# 		if i["form"] == "select":
# 			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><select name="%s">'%(i["desc"],i["name"]))
# 			defaultchoice = ""
# 			if i["default"]: ret.append('<option selected>%s</option>'%default)
# 			for j in i["choices"]:
# 				if j != i["default"]:
# 					ret.append('<option>%s</option>'%j)
# 			ret.append('</select></div>')
# 				
# 		elif i["form"] == "textarea":
# 			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><textarea name="%s" cols="%d" rows="%d" id="form_%s">%s</textarea />%s </div>'%(i["desc"],i["name"],i["cols"],i["rows"],i["name"],i["default"],i["postfix"]))
# 		elif i["form"] == "password":
# 			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><input type="password" name="%s" value="%s" size="%s" />%s</div>'%(i["desc"],i["name"],i["default"],i["cols"],i["postfix"]))
# 		elif i["form"] == "text":
# 			ret.append('<div class="formcol1">%s:</div><div class="formcol2"><input type="text" name="%s" value="%s" size="%s" id="form_%s" />%s</div>'%(i["desc"],i["name"],i["default"],i["cols"],i["name"],i["postfix"]))
# 		elif i["form"] == "hidden":
# 			ret.append('<input type="hidden" name="%s" value="%s" />'%(i["name"],i["default"]))
# 		elif i["form"] == "space":
# 			ret.append('<br /><br />')
# 		else:
# 			ret.append('<div class="formcol1">Unknown field type: %s</div>'%i)
# 
# 	return '<div class="formdiv"><form action="%s" method=%s>%s<div class="formcol1"></div><div class="formcol2"><input type="submit" value="Submit" /></div></form></div>'%(action,method," ".join(ret))
#
	





def header(name,notify=None,init=None,short=0,tabs=1,ctxid=None,db=None):
	"""Common header block, includes <body>"""

	ret = []
	# <!--quirks mode for ie--> 
	ret.append("""<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">	

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>

	<title>
	NCMIDB: %s
	</title>

	<link rel="StyleSheet" href="/main.css" type="text/css" />
	<!--[if IE]>
	<link rel="StyleSheet" href="/iehx.css" type="text/css"  />
	<![endif]-->

	<script type="text/javascript" src="/jquery.js"></script>
	<script type="text/javascript" src="/switch.js"></script>
	<script type="text/javascript" src="/forms.js"></script>
	<script type="text/javascript" src="/formcontrols.js"></script>
	<script type="text/javascript" src="/xmlrpc.js"></script>
	<script type="text/JavaScript" src="/parambrowser.js"></script>
	<script type="text/javascript" src="/tile.js"></script>

</head>

<body onload="javascript:init();"""%name)

	if init:
		ret.append(str(init))

	ret.append("\">")

	if not short:
		ret.append("""

<div id="container">

<div id="precontent">

<div id="title">
	<a href="/db/home"><img src="/images/logo_trans.gif" alt="NCMI" />National Center for Macromolecular Imaging</a>
</div>

<ul id="nav">
		<li><a href="/db/home">Home</a></li>
		<li><a href="/db/record/%s/group">Browse</a></li>
		<li><a href="/db/query">Query</a></li>
		<li><a href="/db/workflow">Workflow</a></li>
		<li><a href="/db/users">Users</a></li>
		<li><a href="/db/record/%s/group">Groups</a></li>
		<li><a href="/db/record/%s">Equipment</a></li>
		<li><a href="/db/paramdefs">Parameters</a></li>
		<li><a href="/db/recorddefs">Protocols</a></li>
		<li><a href="/help/">Help</a></li>
</ul>


<ul id="alert"><li style="display:none"></li></ul>

		"""%(KEYRECORDS["GROUPHOME"],KEYRECORDS["GROUPROOT"],KEYRECORDS["MICROSCOPEROOT"]))	

#	ret.append(notifymsg(args))

	if tabs:
		ret.append("""
<div class="buttons">
	<ul><li class="button button_active button_main button_main_active" id="button_main_mainview">%s</li></ul>
</div>

</div><!-- end #precontent -->



<div class="pages">
<div class="page page_main" id="page_main_mainview">"""%name)

	return " ".join(ret)



# moved into header
def singleheader(title,short=0):
	return ""




def footer(short=0,tabs=1,ctxid=None,db=None):
	"""Common header block, includes </body>"""
	ret = []
	# end page main, end page
	if tabs:
		ret.append("""\n\n</div><!-- end #page_main_mainview -->""")

	if not short:
		ret.append("""
		
<div id="bottom">

<img src="/images/logo_alt_sm.gif" alt="Baylor College of Medicine" />	""")

		try:
			user = db.checkcontext(ctxid)[0]
			ret.append("""Loggged in as: <a href="/db/user/%s">%s</a> | <a href="/db/logout">Logout</a> <br />"""%(user,user))
			ret.append("""<script type="text/javascript">var global_user="%s";var ctxid="%s"</script>"""%(user,ctxid))
		except:
			ret.append("""Not logged in. <a href="/db/login">Login?</a><br /><script type="text/javascript">var global_user=null;</script>""")

		ret.append("""
Hosted by <a href="http://ncmi.bcm.tmc.edu">NCMI</a> | Phone: 713-798-6989 | Fax: 713-798-1625<br />
Room N421 Alkek Building, One Baylor Plaza, Houston, TX, 77030<br />
Please mail comments/suggestions to: <a href="mailto:ian.rees@bcm.edu">WEBMASTER</a>

</div><!-- end #bottom -->
	
</div><!-- end #container -->


</body></html>""")

	return " ".join(ret)

	
	
def notifymsg(args):
	"""Alert messages to show in the top of the page."""
	if args and args.has_key("notify"):
		notify = args["notify"][0].split("*")
	else:
		return ""

	ret = []

	msgs = [\
	"Added comment successfully", \
	"Permission change successful", \
	"Record operation successful", \
	"Attached file successfully",\
	"Logged out",\
	"Changes saved",\
	"NOTE: Database in development mode. Changes will be erased each morning.",\
	"Added Protocol Successfully",\
	"Added Parameter Successfully"
	]
	
	ret.append("""<script type="text/javascript">var alerts=new Array();""")
	
	for i in notify:
		if i:
			try:
				ret.append("""alerts.push("%s");"""%msgs[int(i)])
			except:
				ret.append("""alerts.push("%s");"""%i)				
	
	ret.append("""topalert(alerts);</script>""")

	return " ".join(ret)


	
	
# def parambrowser(all=None,viewfull=None,addchild=None,edit=None,select=None,hidden=None):
# 	form = []
# 	addchildhtml = ""
# 	hiddenhtml = ""
# 	if hidden:
# 		hiddenhtml = "style=\"display:none\""
# 	if all:
# 		select,viewfull,addchild,edit = 1,1,1,1
# 	if select:
# 		form.append('<div class="l" onclick="selecttarget()">Select</div>')
# 	if viewfull:
# 		form.append('<div class="l"><a id="viewfull" href="">View Full</a></div>')
# #	if addchild:
# 	if 1:
# 		form.append('<div class="l"><a href="javascript:toggle(\'addchild\')">Add Child</a></div>')
# 
# 		addchildhtml = """
# 		<form name="form_addparamdef" ">
# 
# 		<table>
# 		<tr><td>Name:</td>
# 				<td><input type="text" name="r___name" /></td><tr>
# 
# 		<tr><td>Parents:</td>
# 				<td><input type="text" name="p___parent" /></td></tr>
# 
# 		<tr><td colspan="2">Short description:</td></tr>
# 		<tr><td colspan="2"><input type="text" name="r___desc_short" /></td></tr>
# 
# 		<tr><td colspan="2">Long description:</td></tr>
# 		<tr><td colspan="2"><textarea rows="5" cols="30" name="r___desc_long"></textarea></td></tr>
# 		
# 		<tr><td colspan="2">Default units:</td></tr>
# 		<tr><td colspan="2"><select name="p___defaultunits">	
# 			<option value="None">None</option>
# 			<option value="%">Percent (%)</option>
# 			<option value="%RH">Relative Humidity (%RH)</option>
# 			<option value="A">Anstroms (A)</option>
# 			<option value="A/pix">Anstroms/Pixel (A/pix)</option>
# 			<option value="A^2">Anstroms Squared (A^2)</option>
# 			<option value="C">Degrees Celsius (C)</option>
# 			<option value="K">Degrees Kelvin (K)</option>
# 			<option value="KDa">Kilodaltons (KDa)</option>
# 			<option value="Pi">Radians (Pi)</option>
# 			<option value="Amp/cm2">Amperes per cm^2 (Amp/cm2)</option>
# 			<option value="V">Volts (V)</option>
# 			<option value="cm">Centimeters (cm)</option>
# 			<option value="degree">Degrees (degree)</option>
# 			<option value="e/A2/sec">e/A2/sec</option>
# 			<option value="kv">Kilovolts (kv)</option>
# 			<option value="mg/ml">mg/ml concentration (mg/ml)</option>
# 			<option value="min">Minutes (min)</option>
# 			<option value="mm">Millimeters (mm)</option>
# 			<option value="mrad">Milliradians (mrad)</option>
# 			<option value="ms">Milliseconds (ms)</option>
# 			<option value="nm">Nanometers (nm)</option>
# 			<option value="p/ml">? (p/ml)</option>
# 			<option value="pixels">Pixels</option>
# 			<option value="s">Seconds (s)</option>
# 			<option value="ul">Microliters (ul)</option>
# 			<option value="um">Micrometers (um)</option>
# 			<option value="unitless">Unitless</option>
# 		</select></td></tr>
# 
# 		<tr><td>Vartype:</td>
# 		<td><select name="r___vartype">
# 			<option value="string">String</option>
# 			<option value="int">Integer</option>
# 			<option value="float">Floating point</option>
# 			<option value="stringlist">String List</option>
# 			<option value="intlist">Integer List</option>	
# 			<option value="boolean">Boolean</option>
# 			<option value="datetime">Date</option>
# 			<option value="text">Text</option>
# 			<option value="link">Link</option>		
# 			<option value="choice">Choice</option>
# 			<option value="binary">Binary</option>
# 		</select></td></tr>
# 		
# 		<tr><td>Property:</td>
# 		<td><select name="r___property">
# 			<option value="None">None</option>
# 			<option value="count">Count</option>
# 			<option value="length">Length</option>
# 			<option value="angle">Angle</option>
# 			<option value="bfactor">B-factor</option>
# 			<option value="area">Area</option>
# 			<option value="concentration">Concentration</option>
# 			<option value="mass">Mass</option>
# 			<option value="time">Time</option>
# 			<option value="volume">Volume</option>
# 			<option value="density">Density</option>
# 		</select></td></tr>
# 
# 		<tr><td>Choices:</td>
# 		<td>"""
# 		
# 		addchildhtml += """<span class="input_elem input_list" ><br />"""
# #		for i in range(0,len(value)):
# #			ret.append("""<input name="r___%s___%s___1___%s" type="text" value="%s" /><br />"""%(paramdef.name,paramdef.vartype,i,value[i]))
# 		addchildhtml += """<input name="r___choices___stringlist___1___0" type="text" value="" /> <span class="jslink" onclick="input_moreoptions(this)">[+]</span></span>"""
# 		addchildhtml += """			
# 		</td></tr>
# 
# 		</table>
# 		<input type="button" onclick="action_addparamdef(this.form)" value="Submit" />
# 		</form>"""
# 		
# #	if edit:
# #		form.append('<div class="l">Edit</div>')
# 
# 	return("""	
# 	<div id="browserid">Parameter Browser</div>
# 	<div id="parambrowser" %s>
# 
# 		<div class="floatleft" id="left">
# 			<div id="getchildrenofparents"></div>
# 		</div>
# 
# 		<div class="floatleft" id="center">
# 			<div id="focus"><div id="paramdef_name"></div></div>
# 			<div id="getparamdef"></div>
# 			<div id="parambuttons">%s<div id="addchild">%s</div></div>
# 		</div>
# 		
# 		<div class="floatleft" id="right">
# 			<div id="getchildren"></div>
# 			<div id="getcousins"></div>
# 		</div>
# 	</div>
# 	"""%(hiddenhtml," ".join(form),addchildhtml))	


# def protobrowser(all=None,viewfull=1,addchild=None,edit=0,select=None,hidden=None):
# 	form = []
# 	addchildhtml = ""
# 	hiddenhtml = ""
# 	if hidden:
# 		hiddenhtml = "style=\"display:none\""
# 	if all:
# 		select,viewfull,addchild,edit = 1,1,1,1
# 	if select:
# 		form.append('<div class="l" onclick="selecttarget()">Select</div>')
# 	if viewfull:
# 		form.append('<div class="l"><a id="viewfull" href="">View Full</a></div>')
# 
# #	if addchild:
# #		form.append('<div class="l"><a href="javascript:toggle(\'addchild\')">Add Child</a></div>')
# #
# #		addchildhtml = """
# #		<table>
# #		<tr><td>Name:</td><td><input type="text"; id = "name"></td><tr>
# #		<tr><td>Parents:</td><td><input type="text"; id="parent_new"></td></tr>
# #		<tr><td>Exp. Desc.:</td><td><input type="text"; id="mainview"></td></tr>
# #		<tr><td>Summary:</td><td><input type="text"; id = "summary"></td></tr>
# #		<tr><td>One line view:</td><td><input type="text"; id = "oneline"></td></tr>
# #		<tr><td>Private:</td><td><input type="checkbox"; id = "private"></td></tr>
# #		</table>
# #		<input type="submit">
# #		</form>"""		
# 	form.append("""
# 			<div class="l" id="form_protobrowser_edit" style="display:none" onClick="form_protobrowser_edit(this.form)">Edit</div>
# 			<div class="l" id="form_protobrowser_commit" style="display:none" ><input type="button" onClick="xmlrpc_putrecorddef(this.form)" value="Commit" /></div> 
# 			<div class="l" id="form_protobrowser_cancel" style="display:none" ><input type="button" onClick="form_protobrowser_cancel(this.form)" value="Cancel"></div>
# 			<div class="l" id="form_protobrowser_addrecorddef"><a id="form_protobrowser_newrecorddeftarget" href="/db/newrecorddef/">Add Child</a></div>
# 		""")
# 
# 	return("""	
# 	<div id="browserid">Protocol Browser</div>
# 	<div id="protobrowser" %s>
# 
# 	<form action="javascript:void(0)" name="form_protobrowser">
# 
# 		<div class="floatleft" id="left">
# 			<div id="getchildrenofparents"></div>
# 		</div>
# 
# 		<div class="floatleft" id="center">
# 			<div id="focus"><div id="recdef_name"></div></div>
# 			<div id="getrecorddef"></div>
# 			<div id="parambuttons">%s
# 				<div id="addchild">%s</div>
# 			</div>
# 		</div>
# 		
# 		<div class="floatleft" id="right">
# 			<div id="getchildren"></div>
# 			<div id="getcousins"></div>
# 		</div>
# 		
# 		<div id="recorddefviews"></div>
# 		
# 		
# 		<div id="recorddefsimple" style="display:none"></div>
# 
# 	</form>
# 		
# 	</div>
# 	
# 
# 	"""%(hiddenhtml," ".join(form),addchildhtml))	
