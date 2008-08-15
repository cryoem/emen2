################################################### 
## SUPPORT FUNCTIONS ##############################
###################################################


from sets import Set
import re
import os
import pickle
from operator import itemgetter
import time

from emen2.emen2config import *
from emen2 import Database
		

# Parameters to keep in the sidebar
sidebarparams = Set(["rectype","creator","creationtime","permissions","modifytime","modifyuser","comments_text","comments","file_binary_image","file_binary"])


# Main record def view parser
regex_pattern =  "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"    \
				"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
				"|(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
regex = re.compile(regex_pattern)


# Convert newlines to html breaks
recommentsregex = "\n"
pcomments = re.compile(recommentsregex)



# rename
def groupsettolist(groups):
	"""Convert a dictionary of Sets to a dict of lists."""
	for i in groups.keys():
		groups[i] = list(groups[i])
	return groups



def getuserrealnames(ctxid,reverse=0,db=None):
	"""Return a dictionary of users and full names from their record."""
	ret = {}
	for i in db.getusernames(ctxid):
		try:
			user=db.getuser(i,ctxid)
			urec=db.getrecord(user.record,ctxid)
			if reverse:
				ret[i] = "%s, %s %s"%(urec["name_last"],urec["name_first"],urec["name_middle"])
			else:
				ret[i] = "%s %s %s"%(urec["name_first"],urec["name_middle"],urec["name_last"])
		except:
			ret[i] = "(%s)"%i
	return ret


def getuserrealname(user,ctxid,db=None):
	"""Return the full name of a user from the user record."""
	try:
		urec=db.getrecord(db.getuser(user,ctxid).record,ctxid)
		uname="%s %s %s"%(urec["name_first"],urec["name_middle"],urec["name_last"])
	except:
		uname=user
	return uname
	
				
				
# remove
def argmap(dict):
	"""un-list the request args"""
	for i in dict: dict[i]=dict[i][0]
		
		
	
# remove eventually		
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



# remove eventually
def htable2(itmlist,cols,proto):
	"""Produce a table of values and counts in 'cols' columns"""
	
	ret=['\n\n<table>']

	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("\t<tr>")
		ret.append("\t\t<td><a href=\"%s%s\">%s (%d)</a></td>"%(proto,j[0],j[0],j[1]))
		if (i%cols==cols-1) : ret.append("\t</tr>\n")

	if (len(itmlist)%cols!=0) : ret.append("\t</tr>\n</table>\n")
	else : ret.append("</table><br />")

	return "".join(ret)



def dicttableview(rec,params=[]):
	"""Quickly build a table for viewing key/values for a record."""

	if not params:
		params = rec.keys()

	dicttable = ["<table><tr><td><h6>Key</h6></td><td><h6>Value</h6></td></tr>"]	
	for i in params:
		if i not in sidebarparams:
			dicttable.append("<tr><td>$#" + i + "</td><td>$$" + i + "</td></tr>")
	dicttable.append("</table>")
	return "".join(dicttable)



###################################################
# Preparse views for web display (important)

def renderpreparse(rec,viewdef,paramdefs={},edit=0,paramlinks=1,db=None,ctxid=None):
	"""Add HTML markup to a record def view, including editing markup if requested."""

	editclass=""
	if edit:
		editclass="editable"
	
	iterator = Database.database.regex2.finditer(viewdef)
		
	for match in iterator:
		prepend=""
		postpend=""
		
		######## $#names #######
		if match.group("name1"):
			if paramlinks:
				prepend = """<a title="%s" href="/db/paramdef/%s">"""%(match.group("name1"),match.group("name1"))
				postpend = """</a>"""
			matchstr = "\$\\#"+match.group("name")+match.group("namesep")
			viewdef = re.sub(matchstr,prepend+"$#"+match.group("name")+postpend+match.group("namesep"),viewdef)

			
		######## $$variables #######
		elif match.group("var1"):
			if not paramdefs.has_key(match.group("var1")):
				paramdefs[match.group("var1")] = db.getparamdef(match.group("var1"))
			
			pd=paramdefs[match.group("var1")]
			v=rec[match.group("var1")]
										
# 			prepend	= """<strong class="editable paramdef___%s">$$"""%(match.group("var")) + match.group("var")	
# 			postpend = """</strong>"""
# 			if pd.defaultunits and pd.defaultunits != "unitless" and v != None:
# 				postpend += """ <em>%s</em> """%(pd.defaultunits)
# 
 			matchstr = "\$\$"+match.group("var")+match.group("varsep")
			units=""
			if pd.defaultunits and pd.defaultunits != "unitless" and v != None:
				units=pd.defaultunits
			replstr = """<strong class="%s paramdef___%s">$$%s %s </strong>%s"""%(editclass,match.group("var"), match.group("var"), units, match.group("varsep"))

			viewdef = re.sub(matchstr,replstr,viewdef)

	return viewdef


# FIXME: write macro definitions in a more flexible way. (does python have closures/blocks?)
def macro_names(macro,macroparameters):
	"""Return the name of a macro, equivalent to paramdef.desc_short"""
		
	if macro == "recid":
		return "Record ID"
	elif macro == "childcount":
		return "%s total:"%macroparameters
	elif macro == "parentvalue":
		return "Parent %s:"%macroparameters


# deprecated
def editparamspan2(paramdef,value,db=None,ctxid=None):
	"""Create an editable field."""
	
	# 	"int":("d",lambda x:int(x)),			# 32-bit integer
	# 	"longint":("d",lambda x:int(x)),		# not indexed properly this way
	# 	"float":("f",lambda x:float(x)),		# double precision
	# 	"longfloat":("f",lambda x:float(x)),	# arbitrary precision, limited index precision
	# 	"choice":("s",lambda x:str(x)),			# string from a fixed enumerated list, eg "yes","no","maybe"
	# 	"string":("s",lambda x:str(x)),			# a string indexed as a whole, may have an extensible enumerated list or be arbitrary
	# 	"text":("s",lambda x:str(x)),			# freeform text, fulltext (word) indexing
	# 	"time":("s",lambda x:str(x)),			# HH:MM:SS
	# 	"date":("s",lambda x:str(x)),			# yyyy/mm/dd
	# 	"datetime":("s",lambda x:str(x)),		# yyyy/mm/dd HH:MM:SS
	# 	"intlist":(None,lambda y:map(lambda x:int(x),y)),		# list of integers
	# 	"floatlist":(None,lambda y:map(lambda x:float(x),y)),	# list of floats
	# 	"stringlist":(None,lambda y:map(lambda x:str(x),y)),	# list of enumerated strings
	# 	"url":("s",lambda x:str(x)),			# link to a generic url
	# 	"hdf":("s",lambda x:str(x)),			# url points to an HDF file
	# 	"image":("s",lambda x:str(x)),			# url points to a browser-compatible image
	# 	"binary":("s",lambda y:map(lambda x:str(x),y)),				# url points to an arbitrary binary... ['bdo:....','bdo:....','bdo:....']
	# 	"binaryimage":("s",lambda x:str(x)),		# non browser-compatible image requiring extra 'help' to display... 'bdo:....'
	# 	"child":("child",lambda y:map(lambda x:int(x),y)),	# link to dbid/recid of a child record
	# 	"link":("link",lambda y:map(lambda x:int(x),y)),		# lateral link to related record dbid/recid
	# 	"boolean":("d",lambda x:int(x)),
	# 	"dict":(None, lambda x:x),
	#		"user":("s",lambda x:str(x))
	#
	#	Set(['binary', 'string', 'int', 'text', 'float', 'choice', 'boolean', 'datetime', 'stringlist', 'binaryimage'])
	# choice = select one
	# boolean = radio buttons: true/false
	# list = select multiple + extend
	# text = textarea
	# date, datetime, time = calendar widget
	# int, longint, float, longfloat, string = 

	#	ekind = expanded[0] || "r";
	#	ename = expanded[1];
	#	etype = expanded[2] || "string";
	#	elist = parseInt(expanded[3]) || 0;
	#	epos = expanded[4] || null;		
	ret = []

	if value==None:
		value=""

	hint=""

	if paramdef.vartype == "time":
		hint = " (HH:MM:SS)"
	elif paramdef.vartype == "date":
		hint = " (YYYY/MM/DD)"
	elif paramdef.vartype == "datetime":
		hint = " (YYYY/MM/DD HH:MM:SS)"
	elif paramdef.vartype == "link":
		hint = " (link)"
	elif paramdef.vartype == "int" or paramdef.vartype == "longint":
		hint = " (int)"
	elif paramdef.vartype == "float" or paramdef.vartype == "longfloat":
		hint = " (float)"
	elif paramdef.vartype == "url":
		hint = """ (url)"""
	elif paramdef.vartype == "binary" or paramdef.vartype == "binaryimage":
		hint = """ (bdo:)"""

	if paramdef.defaultunits and paramdef.defaultunits != "unitless":
		hint = paramdef.defaultunits + hint



	if paramdef.vartype == "choice":
		ret.append("""<span class="input_elem input_select">""")
		ret.append("""<select name="r___%s___%s" >"""%(paramdef.name,paramdef.vartype))
		z=list(paramdef.choices)
		z.append("")
		for i in z:
			if value == i:
				ret.append("""<option value="%s" selected>%s</option>"""%(i,i))
			else:
				ret.append("""<option value="%s">%s</option>"""%(i,i))
		ret.append("""</select></span><em>%s</em>"""%hint)
			


	elif paramdef.vartype == "boolean":
		ret.append("""<span class="input_elem input_select">""")
		ret.append("""<select name="r___%s___%s">"""%(paramdef.name,paramdef.vartype))
		ret.append("""<option value=""></option>""")		
		for i in [[0,"False"],[1,"True"]]:
			if value == i[0]:
				ret.append("""<option value="%s" selected>%s</option>"""%(i[0],i[1]))
			else:
				ret.append("""<option value="%s">%s</option>"""%(i[0],i[1]))
		ret.append("""</select></span><em>%s</em>"""%hint)



	elif paramdef.vartype in ["user","userlist"]:

		# sanity checks
		if value == None:
			value = ""
		if paramdef.vartype == "userlist" and type(value) != list:
			value=[value]
		if paramdef.vartype == "userlist" and len(value) == 0:
			value=[""]

		usernames=getuserrealnames(ctxid,reverse=1,db=db)	
		
		# fixme: replace with a more general python->js method (JSON?)
		js=[[k,re.sub("'","",v)+" (%s)"%k] for k,v in [i for i in sorted(usernames.items(), key=itemgetter(1))]]
								
		ret.append("""<span class="input_elem input_combobox"><br />""")

		if paramdef.vartype == "userlist":
			for i in range(0,len(value)):
				ret.append("""<span><input name="r___%s___%s___1___%s" type="text" onfocus="new combobox(this, %s, true)" value="%s" /></span><br />"""%(paramdef.name,paramdef.vartype,i,js,value[i]))
			ret.append("""<span><input name="r___%s___%s___1___%s" type="text" onfocus="new combobox(this, %s, true)" value="" /></span>"""%(paramdef.name,paramdef.vartype,i+1,js))				
			ret.append("""<span class="jslink" onclick="javascript:input_moreoptions_combobox(this)">[+]</span>""")

		else:
			ret.append("""<span><input name="r___%s___%s" type="text" onfocus="new combobox(this, %s, true)" value="%s" /></span>"""%(paramdef.name,paramdef.vartype,js,value))
		
		ret.append("""</span>""")
		
		
		
	elif paramdef.vartype in ["datetime","time","date"]:
		if value=="" and paramdef.vartype == "datetime":
			value=time.strftime("%Y/%m/%d %H:%M:%S")
		elif value=="" and paramdef.vartype == "time":
			value=time.strftime("%H:%M:%S")
		elif value=="" and paramdef.vartype == "date":
			value=time.strftime("%Y/%m/%d")
		ret.append("""<span class="input_elem input_text"><input name="r___%s___%s" type="text" value="%s" size="19" maxlength="19" /></span><em>%s</em>"""%(paramdef.name,paramdef.vartype,value,hint))


	
	elif paramdef.vartype in ["intlist","stringlist","intlist"]:
		ret.append("""<span class="input_elem input_list">""")
		for i in range(0,len(value)):
			ret.append("""<input name="r___%s___%s___1___%s" type="text" value="%s" /><br />"""%(paramdef.name,paramdef.vartype,i,value[i]))
		ret.append("""<input name="r___%s___%s___1___%s" type="text" value="" /> <span class="jslink" onclick="javascript:input_moreoptions_text(this)">[+]</span>"""%(paramdef.name,paramdef.vartype,len(value)))
		ret.append("""</span><em>%s</em>"""%hint)


				
	elif paramdef.vartype == "text":
		# find a good size for textarea
		rows=4
		cols=40
		if len(value) > cols: cols = len(value)
		if cols > 80: cols = 80
		if value.count("\n") > rows: rows = value.count("\n")
		if len(value) > rows * 80: rows = int(len(value) / 80.0) + rows
		if rows > 40: rows = 40

		ret.append("""<span class="input_elem input_textarea"><textarea cols="%s" rows="%s" name="r___%s___%s">%s</textarea></span><em>%s</em>"""%(cols, rows, paramdef.name,paramdef.vartype,value,hint))

	

	elif paramdef.vartype in ["string","int","float","longint","longfloat","url"]:
		if paramdef.choices:
			print paramdef.choices
			# escape for js
			js = [[re.sub("'",r"\'",str(i)),re.sub("'",r"\'",str(i))] for i in paramdef.choices]
			ret.append("""<span class="input_elem input_combobox"><br /><input name="r___%s___%s" type="text" onfocus="new combobox(this, %s, false)" value="%s" /></span>"""%(paramdef.name,paramdef.vartype,js,value))

		else:
			size = 20
			if len(unicode(value)) > size: size = len(unicode(value))
			if size > 40: size = 40
			
			ret.append("""<span class="input_elem input_text" ><input name="r___%s___%s" type="text" value="%s" size="%s"></span><em>%s</em>"""%(paramdef.name,paramdef.vartype,value,size,hint))
			


	else:
		ret.append("""<br />%s: %s<br />"""%(paramdef,value))



	return "".join(ret)
	

