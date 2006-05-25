# TwistSupport_html.py  Steven Ludtke  06/2004
# This module provides the resources needed for a HTML server using Twisted

from twisted.web.resource import Resource
from emen2 import TwistSupport 
import os
import traceback
import pickle
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
<br><input type=submit value=submit></form></body></html>"""%(html_header("EMEN2 Login"),redir)

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


def html_header(name):
	"""Common header block, includes <body>"""
	return """<html><head><title>%s</title></head><body>"""%name

def html_footer():
	"""Common header block, includes <body>"""
	return """<hr /></body></html>"""


def html_htable(itmlist,cols,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=['<table border="1">']
	
	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("<tr>")
		ret.append("<td><a href=%s%s>%s</a></td>"%(proto,j,j))
		if (i%cols==cols-1) : ret.append("</tr>\n")
	
	if (len(itmlist)%cols!=0) : ret.append("</tr></table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)

def html_htable2(itmlist,cols,proto):
	"""Produce a table of values and counts in 'cols' columns"""
	ret=['<table border="1">']
	
	for i,j in enumerate(itmlist):
		if (i%cols==0): ret.append("<tr>")
		ret.append("<td><a href=%s%s>%s (%d)</a></td>"%(proto,j[0],j[0],j[1]))
		if (i%cols==cols-1) : ret.append("</tr>\n")
	
	if (len(itmlist)%cols!=0) : ret.append("</tr></table>\n")
	else : ret.append("</table><br>")

	return "".join(ret)

def html_dicttable(dict,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=["<table border=2>"]
	
	for k,v in dict.items():
		ret.append("<tr><td><a href=%s%s>%s</a></td><td>%s</td></tr>\n"%(proto,k,k,v))
		
	ret.append("</table><br>")

	return "".join(ret)
		
def html_home():
	ret=[html_header("EMEN2 Home Page"),"""<h2>EMEN2 Demo Page</h2><br><br>Available tasks:<br><ul>
	<li><a href="/db/record?name=1">Browse Records</a></li>
	<li><a href="/db/records">List of all Records</a></li>
	<li><a href="/db/paramdefs">List of Defined Experimental Parameters (ParamDef)</a></li>
	<li><a href="/db/recorddefs">List of Defined Experimental Protocols (RecordDef)</a></li>
	<li><a href="/db/users">List of Users</a></li>
	</ul><br><br><ul>
	<li><a href="/db/newuser">Add New User</a></li>
	<li><a href="/db/newuserqueue">Approve New Users</a></li>
	<li><a href="/db/newparamdef">Define New Experimental Parameter</a></li>
	<li><a href="/db/newrecorddef">Describe new Experimental Protocol</a></li>
	</ul>"""]
	
	return "".join(ret)

def html_tileimage(path,args,ctxid,host):
	global db

	name,fpath=db.getbinary(path[1],ctxid,host)
	fpath=fpath+".tile"
	

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


def html_paramdefs(path,args,ctxid,host):
	global db
	
	ftn=db.getparamdefnames()
	ret=[html_header("EMEN2 ParamDefs"),"<h2>Registered ParamDefs</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/paramdef?name="))

	ret.append("</body></html>")
	return "".join(ret)	

def html_paramdef(path,args,ctxid,host):
	global db
	
	item=db.getparamdef(args["name"][0])
	
	ret=[html_header("EMEN2 ParamDef Description"),"<h2>Experimental Parameter (ParamDef): <i>%s</i></h2><br>"%item.name]
	
	parents=db.getparents(item.name,keytype="paramdef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<br>Parents: ")
		for p in parents:
			ret.append('<a href="/db/paramdef?name=%s">%s</a> '%(p,p))
	
	children=db.getchildren(item.name,keytype="paramdef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<br>Children: ")
		for c in children:
			ret.append('<a href="/db/paramdef?name=%s">%s</a> '%(c,c))
	
	ret.append("""<table><tr><td>Name</td><td>%s</td></tr>
	<tr><td>Variable Type</td><td>%s</td></tr>
	<tr><td>Short Description</td><td>%s</td></tr>
	<tr><td>Long Description</td><td>%s</td></tr>
	<tr><td>Property</td><td>%s</td></tr>
	<tr><td>Default Units</td><td>%s</td></tr>
	<tr><td>Creator</td><td>%s (%s)</td></table><br><br><a href="/db/newparamdef?parent=%s">Add a new child parameter</a></body></html>"""%(
	item.name,item.vartype,item.desc_short,item.desc_long,item.property,item.defaultunits,item.creator,item.creationtime,item.name))
	
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
		("Physical Property","property","select",DB.valid_properties),("Default Units","defaultunits","text")),args=args)+"</body></html>"

def html_recorddefs(path,args,ctxid,host):
	global db
	
	ftn=db.getrecorddefnames()
	for i in range(len(ftn)):
		ftn[i]=(ftn[i],len(db.getindexbyrecorddef(ftn[i],ctxid)))
	ret=[html_header("EMEN2 RecordDefs"),"<h2>Registered RecordDefs</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable2(ftn,3,"/db/recorddef?name="))

	ret.append("</body></html>")
	return "".join(ret)

def html_recorddef(path,args,ctxid,host):
	global db
	
	item=db.getrecorddef(args["name"][0],ctxid)
	
	ret=[html_header("EMEN2 RecordDef Description"),"<h2>Experimental Protocol (RecordDef): <i>%s</i></h2><br>"%item.name,
	]
	
	parents=db.getparents(item.name,keytype="recorddef",ctxid=ctxid)
	if len(parents)>0 :
		ret.append("<br>Parents: ")
		for p in parents:
			ret.append('<a href="/db/recorddef?name=%s">%s</a> '%(p,p))
	
	children=db.getchildren(item.name,keytype="recorddef",ctxid=ctxid)
	if len(children)>0 :
		ret.append("<br>Children: ")
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
	ret.append("""</body></html>""")
	
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
		("One Line View","oneline","textarea",(80,4)),("Private Access","private","checkbox")),args=args)+"</body></html>"
	
def html_records(path,args,ctxid,host):
	
	ftn=db.getrecordnames(ctxid,host=host)
	ret=[html_header("EMEN2 Records"),"<h2>All accessible records</h2>"]
	ret.append(html_htable(ftn,3,"/db/record?name="))

	ret.append("</body></html>")
	return "".join(ret)

		
def html_record(path,args,ctxid,host):
	global db
	
	item=db.getrecord(int(args["name"][0]),ctxid)

	ret=[html_header("EMEN2 Record"),"<h2>Record: <i>%d  (%s)</i></h2><br>params:<br>"%(int(item.recid),item["recdef"])]
	
	ret.append(html_dicttable(item,"/db/paramdef?name="))
	ret.append("<br>Parents:<br>")
	ret.append(html_htable(db.getparents(int(args["name"][0]),ctxid=ctxid),6,"/db/record?name="))
	ret.append("<br>Children:<br>")
	
	# c is a list of this record's children
	c=[i[0] for i in db.getchildren(int(args["name"][0]),ctxid=ctxid)]
	
	# split up the record ids recordtype
	cat={}
	for i in c:
		r=db.getrecord(i,ctxid)
		try: a=(i,r.inputdate)
		except: a=(i,"Unknown")
		try: cat[r.rectype].append(a)
		except: cat[r.rectype]=[a]
		
	# generate a 1-line link for each record sorted by recorddef
	for i,j in cat.items():
		for k in j:
			ret.append('<a href=/db/record?name=%s>%s %s</a><br>'%(k[0],i,k[1]))
	
	ret.append("""</body></html>""")
	
	return "".join(ret)

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
	ret.append('Record add successful.<br>New id=%d<br><br><a href="/db/index.html">Return to main menu</a></body></html>'%rid)
	
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
	if u[0]==item.username or -1 in u[1]: pwc='<br><a href="/db/chpasswd?username=%s">Change Password</a></BODY></HTML>'%args["uid"][0]
	else: pwc="</body></html>"
	
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
		ret.append('<br><b>Password Changed</b><br><br><a href="/db/index.html">Return Home</a></body></html>')
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
	
	return "".join(ret)+html_form(action="/db/chpasswd",items=itm,args=args)+"</body></html>"
	
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
			("Home Page","webpage","text",40),("email","email","text",40),("Phone #","phone","text",16),("Fax #","fax","text",16)),args=args)+"</BODY></HTML>"

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
			if len(i)<4 : i=i+(40,10)
			ret.append('<tr><td>%s</td><td><textarea name="%s" cols="%d" rows="%d">%s</textarea></td></tr>\n'%(i[0],i[1],i[3][0],i[3][1],args.get(i[1],"")))
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
