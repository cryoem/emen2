################################################### 
## SUPPORT FUNCTIONS ##############################
###################################################

print "...loading %s"%__name__


from sets import Set
import re
import os
import pickle
from operator import itemgetter
import time

from emen2.emen2config import *
from emen2 import Database

def groupsettolist(groups):
	for i in groups.keys():
		groups[i] = list(groups[i])
	return groups		


	

regex_pattern =  "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"    \
				"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
				"|(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
regex = re.compile(regex_pattern)

# regex_pattern_var = "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"
# regex_pattern_macro = "(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)"
# regex_pattern_name = "(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
# regex_var = re.compile(regex_pattern_var)
# regex_macro = re.compile(regex_pattern_macro)
# regex_name = re.compile(regex_pattern_name)



recommentsregex = "\n"
pcomments = re.compile(recommentsregex)
# 	re1 =  "(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))[\s<]?"    \
# 				"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))[\s<]?" \
# 				"|(?P<name>(\$\#(?P<name1>\w*)[\s<]?))"



				

def argmap(dict):
	for i in dict: dict[i]=dict[i][0]
		


def render_groupedhead(groupl,ctxid=None,recid=None,wfid=None):
	"""Render tab switching buttons"""
	ret = []
	for i in groupl.keys():
#		ret.append("\t<div class=\"button_main\" id=\"button_main_%s\"><a href=\"javascript:switchin('main','%s')\">%s (%s)</a></div>\n"%(i,i,i,len(groupl[i])))
#db/render_grouptable?&name=135&groupname=project&reverse_project=1&zone=zone_project
#		if not wfid:
#			req = "/db/render_grouptable/%s?groupname=%s&zone=zone_%s"%(recid,i,i)
#		else:
#			req = "/db/render_grouptable/%s?groupname=%s&zone=zone_%s"%(wfid,i,i)
#			#makeRequest('%s','zone_%s');
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




	
def render_view(rec,viewdef,viewtype="",paramdefs={},markup=0,defaults=0,allowedit=0,showedit=0,runmacro=1,macrocache={},ctxid=None,db=None):
	"""render a record into view 'viewdef' (string). paramdefs = cached params. defaults = show default values. edit = allow editing.
		db needed if paramdefs not specified
		viewtype needed if edit or tabularview
		macrocache is pre-computed macro values"""
			
			
	###############################
	# VIEWS: new parser
	iterator = regex.finditer(viewdef)
		
	for match in iterator:
		prepend=""
		postpend=""
		######## $#names #######
		if match.group("name1"):

			if not paramdefs.has_key(match.group("name1")):
				paramdefs[match.group("name1")] = db.getparamdef(match.group("name1"))

			if markup:
				prepend = """<a title="%s" href="/db/paramdef/%s">"""%(match.group("name1"),match.group("name1"))
				postpend = """</a>""" + match.group("namesep")
			
			value = paramdefs[match.group("name1")].desc_short			
			matchstr = re.sub("\$","\$","$#" + match.group("name1")) + match.group("namesep")

			replace = """%s%s%s"""%(prepend,value,postpend)
			# do not break this :) !!
			viewdef = re.sub(matchstr,replace,viewdef)

		######## $$variables #######
		elif match.group("var1"):

			if markup and not paramdefs.has_key(match.group("var1")):
				paramdefs[match.group("var1")] = db.getparamdef(match.group("var1"))

			# empty keys just return empty now
			value = rec[match.group("var1")]
			if type(value) == type(None):
				value = ""
			value_raw=value
				
			if type(value) == list:
				value = ", ".join(value)

			value = pcomments.sub("<br />",str(value))

			if markup:				
				prepend	= """<span class="param_display">"""		
				if paramdefs[match.group("var1")].defaultunits and paramdefs[match.group("var1")].defaultunits != "unitless" and value != "":
					postpend += """ <span class="typehint">%s</span> """%(paramdefs[match.group("var1")].defaultunits)
				postpend += """</span>"""
				# are we allowing editing?
				if allowedit:
					postpend += editparamspan2(viewtype,paramdefs[match.group("var1")],value_raw,showedit=showedit)

			matchstr = re.sub("\$","\$",match.group("var")) + match.group("varsep") 
			postpend += match.group("varsep")

			replace = """%s%s%s"""%(prepend,value,postpend)
			# do not break this :) !!
			viewdef = re.sub(matchstr,replace,viewdef)

		######## $@macros #######
		#			currently disabled
		elif match.group("macro1"):
			if match.group("macro2") == None:
				m2 = ""
			else:
				m2 = match.group("macro2")
			
			value = ""
			if runmacro:
				try:
					value = macrocache[match.group("macro1")][m2][rec.recid]
				except:
					t2=time.time()
					value = macro_processor(rec, match.group("macro1"), m2, ctxid=ctxid, db=db)
					if DEBUG: print "in macro non-cached: %i"%((time.time()-t2)*1000000)


			repl = re.sub("\$","\$",match.group("macro"))
			repl2 = re.sub("\@","\@",repl)
			repl3 = re.sub("\(","\(",repl2)
			matchstr = re.sub("\)","\)",repl3)
			
			replace = """%s%s%s"""%(prepend,value,postpend)
			# do not break this :) !!
			viewdef = re.sub(matchstr,replace,viewdef)


	return viewdef



def macroprecache(recordids,macros,db=None,ctxid=None):
	# this allows getindexbyrecorddef to only be called once; can reduce a 1.5s render to 0.4s
	precache = {}
	
	for macro in macros:
		t0=time.time()
		
		if not precache.has_key(macro[0]):
			precache[macro[0]] = {}

		if macro[0] == "recid":
			precache[macro[0]][""] = {}
			for i in recordids:
				precache[macro[0]][""][i] = i

		if macro[0] == "childcount":
			precache[macro[0]][macro[1]] = {}
			c = {}
			q = Set()
			for i in recordids:
							c[i] = db.getchildren(i,ctxid=ctxid,recurse=4)
							q = q | c[i]
			macromgroup = q & db.getindexbyrecorddef(macro[1],ctxid)
			for i in recordids:
				precache[macro[0]][macro[1]][i] = len(c[i] & macromgroup)				

		if macro[0] == "parentvalue":
			precache[macro[0]][macro[1]] = {}
			for i in recordids:
				p=db.getparents(i,ctxid=ctxid)
				for j in p:
					if db.trygetrecord(j,ctxid):
						r=db.getrecord(j,ctxid)
						if r.has_key(macro[1]):
							precache[macro[0]][macro[1]][i] = r[macro[1]]
		
		if DEBUG: print "in macro %s: %i"%(macro,(time.time()-t0)*1000000)

	return precache


def macro_names(macro,macroparameters):
	if macro == "recid":
		return "Record ID"
	elif macro == "childcount":
		return "%s total:"%macroparameters
	elif macro == "parentvalue":
		return "Parent %s:"%macroparameters
		

def macro_processor(rec, macro, macroparameters, ctxid=None, db=None, macrocache={}):
	if macrocache.has_key(macro):
		return macrocache[macro][macroparameters][rec.recid]

	if macro == "recid":
		return rec.recid
		
 	if macro == "childcount":
 		queryresult = db.getchildren(rec.recid,recurse=5,ctxid=ctxid)
 
#		option 1: return queryresult & db.getindexbyrecorddef(macroparameters,ctxid)
#		option 2: mgroups = db.countchildren(int(recordid),recurse=0,ctxid=ctxid)
 
 		if len(queryresult) < 1000:
 			mgroups = db.groupbyrecorddeffast(queryresult,ctxid)
 		else:
 			mgroups = db.groupbyrecorddef(queryresult,ctxid)

 		if mgroups.has_key(macroparameters):
 			return len(mgroups[macroparameters])
 		else:
 			return

	if macro == "parentvalue":
		p=db.getparents(rec.recid,ctxid=ctxid)
		ret = []
		for j in p:
			if db.trygetrecord(j,ctxid):
				r=db.getrecord(j,ctxid)
				if r.has_key(macroparameters):
					ret.append(r[macroparameters])
		return ",".join(ret)
		
		
	if macro == "recname":
		if rec.has_key("recname"):
			return rec["recname"]
		else:
			recdef=db.getrecorddef(rec.rectype,ctxid)
			if recdef.views.has_key("recname"):
				return render_view(rec,recdef.views["recname"],ctxid=ctxid,db=db)
			else:
				return "(needs $@recname view)"

#			print "test..this is going to hurt"	
#		print ret


def getrecordrendered(recid, ctxid, db=None):
	pass
		


def editparamspan2(classname,paramdef,value,showedit=0):
	ret = []
#	if showedit:
#		ret.append("""<span class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,paramdef.name))
#	else:
#		ret.append("""<span style="display:none" class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,paramdef.name))	

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
# 	"dict":(None, lambda x:x)

	#	Set(['binary', 'string', 'int', 'text', 'float', 'choice', 'boolean', 'datetime', 'stringlist', 'binaryimage'])
	# choice = select one
	# boolean = radio buttons: true/false
	# list = select multiple + extend
	# text = textarea
	# date, datetime, time = calendar widget
	# int, longint, float, longfloat, string = 

# <span class="combobox">
# 	<input value="test" type="text" onfocus="javascript:return combobox_onfocus(this);" onkeypress="javascript:return combobox_onkeypress(this,event);" /><ul class="combobox_items">
# 			<li onclick="combobox_setv(this);">RemorasRemoras</li>
# 			<li onclick="combobox_setv(this);">Tigerfish</li>
# 			<li onclick="combobox_setv(this);">Pufferfish</li>
# 		</ul>
# </span>

	#	ekind = expanded[0] || "r";
	#	ename = expanded[1];
	#	etype = expanded[2] || "string";
	#	elist = parseInt(expanded[3]) || 0;
	#	epos = expanded[4] || null;		

	if showedit:
		style=""
#		ret.append("""<span class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,paramdef.name))
	else:
		style="""style="display:none" """
#		ret.append("""<span style="display:none" class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,paramdef.name))	


	hint=""
	units=""

	if paramdef.defaultunits and paramdef.defaultunits != "unitless":
		units = paramdef.defaultunits	

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
	elif paramdef.vartype == "boolean":
		hint = """ (bool)"""

	if paramdef.vartype == "choice":
		ret.append("""<span class="input_elem input_select" %s>"""%style)
		ret.append("""<select name="r___%s___%s>"""%(paramdef.name,paramdef.vartype))
		z=list(paramdef.choices)
		z.append("")
		for i in z:
			if value == i:
				ret.append("""<option value="%s" selected>%s</option>"""%(i,i))
			else:
				ret.append("""<option value="%s">%s</option>"""%(i,i))
		ret.append("""</select></span>""")
			
	elif paramdef.vartype == "boolean":
		ret.append("""<span class="input_elem input_select" %s>"""%style)
		ret.append("""<select name="r___%s___%s">"""%(paramdef.name,paramdef.vartype))
		ret.append("""<option value=""></option>""")		
		ret.append("""<option value="0">False</option><option value="1">True</option>""")
		ret.append("""</select></span>""")
		
	elif paramdef.vartype in ["datetime","time","date"]:
		if value=="" and paramdef.vartype == "datetime":
			value=time.strftime("%Y/%m/%d %H:%M:%S")
		elif value=="" and paramdef.vartype == "time":
			value=time.strftime("%H:%M:%S")
		elif value=="" and paramdef.vartype == "date":
			value=time.strftime("%Y/%m/%d")
		ret.append("""<span class="input_elem input_text" %s><input name="r___%s___%s" type="text" value="%s" /><span class="typehint">%s</span></span>"""%(style,paramdef.name,paramdef.vartype,value,hint))
	
	elif paramdef.vartype in ["intlist","stringlist","intlist"]:
		ret.append("""<span class="input_elem input_list" %s ><br />"""%style)
		for i in range(0,len(value)):
			ret.append("""<input name="r___%s___%s___1___%s" type="text" value="%s" /><br />"""%(paramdef.name,paramdef.vartype,i,value[i]))
		ret.append("""<input name="r___%s___%s___1___%s" type="text" value="" /> <span class="jslink" onclick="input_moreoptions(this)">[+]</span><span class="typehint">%s</span>"""%(paramdef.name,paramdef.vartype,len(value),hint))
		ret.append("""</span>""")
				
	elif paramdef.vartype == "text":
		ret.append("""<span class="input_elem input_textarea" %s><textarea rows="8" cols="80" name="r___%s___%s">%s</textarea><span class="typehint">%s</span></span>"""%(style,paramdef.name,paramdef.vartype,value,hint))
	
	elif paramdef.vartype in ["string","int","float","longint","longfloat","url"]:
		if paramdef.choices:
			ret.append("""<span class="input_elem input_combobox" %s >"""%style)
			ret.append("""<input name="r___%s___%s" value="%s" type="text" onfocus="javascript:return combobox_onfocus(this);" onkeypress="javascript:return combobox_onkeypress(this,event);" />"""%(paramdef.name,paramdef.vartype,value))
			ret.append("""<ul class="input_combobox_items">""")
			ret.append("""<li onclick="combobox_setv(this,'');">&nbsp;</li>""")
			for i in paramdef.choices:
				ret.append("""<li onclick="combobox_setv(this);">%s</li>"""%i)
			ret.append("""</ul><img class="input_combobox_image" onclick="javascript:return combobox_onfocus(this);" src="/images/dropdown.gif" valign="bottom" /><span class="typehint">%s</span></span>"""%hint)


		else:
			ret.append("""<span class="input_elem input_text" %s ><input name="r___%s___%s" type="text" value="%s"><span class="typehint">%s</span></span>"""%(style,paramdef.name,paramdef.vartype,value,hint))
			

	else:
		ret.append("""edit %s: %s"""%(paramdef,value))


#	ret.append("""</span>""")

	return "".join(ret)
	
	
	
	
	
	

def editparamspan_old(classname,paramdef,value,showedit=0):
	
	name = paramdef.name
	
	ret = []
	if showedit:
		ret.append("""<span class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,name))
	else:
		ret.append("""<span style="display:none" class="param_value_edit_%s" id="param_value_edit_%s_%s">"""%(classname,classname,name))

#	print "%s: %s"%(name,paramdef.choices)

	if paramdef.vartype == "time":
		hint = """ <span class="typehint">(HH:MM:SS)</span>"""
		hint2 = " (HH:MM:SS)"
	elif paramdef.vartype == "date":
		hint = """ <span class="typehint">(YYYY/MM/DD)</span>"""
		hint2 = " (YYYY/MM/DD)"
	elif paramdef.vartype == "datetime":
		hint = """ <span class="typehint">(YYYY/MM/DD HH:MM:SS)</span>"""
		hint2 = " (YYYY/MM/DD HH:MM:SS)"
	elif paramdef.vartype == "link":
		hint = """ <span class="typehint">(link to record id)</span> """
		hint2 = " (link)"
	elif paramdef.vartype == "int" or paramdef.vartype == "longint":
		hint = """ <span class="typehint">(integer)</span>"""
		hint2 = " (int)"
	elif paramdef.vartype == "float" or paramdef.vartype == "longfloat":
		hint = """ <span class="typehint">(float)</span>"""
		hint2 = " (float)"
	elif paramdef.vartype == "url":
		hint = """ <span class="typehint">(http://...)</span>"""
		hint2 = """ (url)"""
	elif paramdef.vartype == "binary" or paramdef.vartype == "binaryimage":
		hint = """ <span class="typehint">(bdo:...)</span>"""
		hint2 = """ (bdo:"""
	elif paramdef.vartype == "boolean":
		hint = """ <span class="typehint">(boolean)</span>"""
		hint2 = """ (bool)"""
	# string or text
	else:
		hint = ""
		hint2 = ""
		
	if paramdef.defaultunits and paramdef.defaultunits != "unitless":
		hint = hint + """ <span class="typehint">%s</span> """%(paramdef.defaultunits)
		hint2 = hint2 + " %s"%paramdef.defaultunits	

	# parameters with choices
	if paramdef.choices:

		# multiple selections possible
		if paramdef.vartype in ["stringlist","intlist","floatlist"]:
			for i in range(0,len(paramdef.choices)):
				if type(value) == type([]):
					if paramdef.choices[i] in value:
						ret.append("""<input type="checkbox" name="r___%s___%s___%s" value="%s" checked />%s%s<br />"""%(name,paramdef.vartype,i,paramdef.choices[i],paramdef.choices[i],hint))					
				else:
					ret.append("""<input type="checkbox" name="r___%s___%s___%s" value="%s"/>%s%s<br />"""%(name,paramdef.vartype,i,paramdef.choices[i],paramdef.choices[i],hint))					

		# only a single selection possible	
		else:			
			ret.append("""<select name="r___%s___%s">"""%(name,paramdef.vartype))
			ret.append("""<option value=""></option>""")

			for i in paramdef.choices:
#				if type(value) == type([]):
				if i == value:
					ret.append("""<option value="%s" selected>%s%s</option>"""%(i,i,hint2))
				else:
					ret.append("""<option value="%s">%s%s</option>"""%(i,i,hint2))
			ret.append("""</select>""")

		# choice type options are fixed at creation; others are extensible
		if paramdef.vartype != "choice":
			i = 0
			if type(value) == type([]):
				for j in value:
					if j not in paramdef.choices and j:
						i = i + 1
						ret.append("""<input type="checkbox" value="" name="r___%s___%s___e___%s" checked /><input name="r___%s___%s___etext___%s" type="text" value="%s" size="20" />%s<br />"""%(name,paramdef.vartype,i,name,paramdef.vartype,i,j,hint))
				i = 0
				ret.append("""<input type="checkbox" value="" name="r___%s___%s___e___%s" /><input name="r___%s___%s___etext___%s" type="text" value="Other" size="20" />%s<br />"""%(name,paramdef.vartype,i,name,paramdef.vartype,i,hint))

			else:
				if value not in paramdef.choices and value:
					i = 1
					ret.append("""<input type="checkbox" value="" name="r___%s___%s___e___%s" checked /><input name="r___%s___%s___etext___%s" type="text" value="%s" size="20" />%s<br />"""%(name,paramdef.vartype,i,name,paramdef.vartype,i,value,hint))
				else:
					i = 0
					ret.append("""<input type="checkbox" value="" name="r___%s___%s___e___%s" /><input name="r___%s___%s___etext___%s" type="text" value="Other" size="20" />%s<br />"""%(name,paramdef.vartype,i,name,paramdef.vartype,i,hint))


		ret.append("""</span>""")

	# parameters without choices
	else:
		
		try:
			newlinecount = value.count("\n")
		except:
			newlinecount = 3

		if type(value) != type(None):
			value = str(value)
		else:
			value = ""

		if len(value) > 55 or newlinecount or paramdef.vartype == "text":
			ret.append("""<textarea cols="80" name="%s___%s" rows="%s" type="text">%s</textarea>%s</span>"""%(name,paramdef.vartype,newlinecount + 4,value,hint))
#		elif len(value) > 0:
#			ret.append("""<input type="text" name="%s___%s" value="%s" size="%s" />%s</span>"""%(name,paramdef.vartype,value,len(value) + 5),hint)
		else:
			ret.append("""<input type="text" name="%s___%s" value="%s" size="20" />%s</span>"""%(name,paramdef.vartype,value,hint))

	return " ".join(ret)

