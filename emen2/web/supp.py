
# move these two functions elsewhere...



from sets import Set
import re
import os
import pickle
from operator import itemgetter
import time

from emen2.emen2config import *
from emen2 import Database
		

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

def renderpreparse(rec,viewdef,paramdefs={},edit=0,paramlinks=1,db=None,ctxid=None,host=None):
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
				paramdefs[match.group("var1")] = db.getparamdef(match.group("var1"), ctxid=ctxid, host=host)
			
			pd=paramdefs[match.group("var1")]
			v=rec[match.group("var1")]

 			matchstr = "\$\$"+match.group("var")+match.group("varsep")
			units=""
			if pd.defaultunits and pd.defaultunits != "unitless" and v != None:
				units=pd.defaultunits
			replstr = """<strong class="%s paramdef___%s">$$%s %s </strong>%s"""%(editclass,match.group("var"), match.group("var"), units, match.group("varsep"))

			viewdef = re.sub(matchstr,replstr,viewdef)

	return viewdef