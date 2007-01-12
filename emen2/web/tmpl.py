################################################### 
## TEMPALTE FUNCTIONS #############################
###################################################

from sets import Set
import re
import os
from emen2.TwistSupport_db import db
import html
#import tmpl
import supp
import plot



def html_header(name,init=None,short=0):
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


def html_footer(short=0):
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


def html_navbar():
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
		<tr><td>Parents:</td><td><input type="text"; id="parent_of_new_parameter"></td></tr>
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











def html_stub(path,args,ctxid,host):
	"""Example"""
	global db

	ret=[tmpl.html_header("EMEN2")]

	ret.append(tmpl.singleheader("Page"))
	ret.append("<div class=\"switchpage\" id=\"page_mainview\">")

	ret.append("<h2>Page Title</h2><br />") 

	# stuff goes here

	ret.append("</div>")

	ret.append(tmpl.html_footer())
	return "".join(ret)
	