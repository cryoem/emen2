from twisted.web.resource import Resource
from emen2 import Database 

# we open the database as part of the module initialization
db=Database.Database("/home/stevel/emen2test")

def loginpage(redir):
	"""Why is this a function ?  Just because. Returns a simple login page."""
	return """%s<h3>Please Login:<br>
<form action="/db/login"><input type=hidden name=fw value=%s>
<br>Username: <input type=text name=username>
<br>Password: <input type=password name=pw>
<br><input type=submit value=submit></form></body></html>"""%(html_header("EMEN2 Login"),redir)


class DBResource(Resource):
	isLeaf = True
	def getChild(self,name,request):
		return self
	def render_GET(self,request):
		session=request.getSession()			# sets a cookie to use as a session id
		
#		return "request was '%s' %s"%(str(request.__dict__),request.getClientIP())
		global db,callbacks

		if (len(request.postpath)==0 or request.postpath[0]=="index.html") : return html_home()
				
		# This is the one request that doesn't require an existing session, since it sets up the session
		if (request.postpath[0]=='login'):
			session.ctxid=db.login(request.args["username"][0],request.args["pw"][0],request.getClientIP())
			return "Login Successful %s (%s)"%(str(request.__dict__),session.ctxid)
		
		# A valid session will have a valid ctxid set
		try:
			ctxid=session.ctxid
		except:
			return loginpage(request.uri)
		
		db.checkcontext(ctxid,request.getClientIP())

		# Ok, if we got here, we can actually start talking to the database
		
		method=request.postpath[0]
		host=request.getClientIP()
		
		return callbacks[method](request.postpath,request.args,ctxid,host)
								
		return "(%s)request was '%s' %s"%(ctxid,str(request.__dict__),request.getHost())

def html_header(name):
	"""Common header block, includes <body>"""
	return """<html><head><title>%s</title></head><body>"""

def html_htable(itmlist,cols,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=["<table>"]
	
	for i in range(len(itmlist)):
		if (i%cols==0): ret.append("<tr>")
		ret.append("<td><a href=%s%s>%s</a></td>"%(proto,itmlist[i],itmlist[i]))
		if (i%cols==cols-1) : ret.append("</tr>\n")
	
	if (itmlist%cols!=0) : ret.append("</tr></table>/n")
	else : ret.append("</table>/n")

	return "".join(ret)
		
def html_home():
	ret=[html_header("EMEN2 Home Page"),"""<h2>EMEN2 Demo Page</h2><br><br>Available tasks:<br><ul>
	<li><a href="/db/fieldtypes">List of Field Types</a></li>
	<li><a href="/db/recordtypes">List of Record Types</a></li>
	<li><a href="/db/users">List of Users</a></li>
	</ul>"""]
	
	return "".join(ret)

def html_fieldtypes(path,args,ctxid,host):
	global db
	
	ftn=db.getfieldtypenames()
	ret=[html_header("EMEN2 FieldTypes"),"<h2>Registered FieldTypes</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/fieldtype?name="))

	ret.append("</body></html>")
	return "".join(ret)	

def html_fieldtype(path,args,ctxid,host):
	global db
	
	item=db.getfieldtype(args["name"][0])
	
	ret=[html_header("EMEN2 FieldType Description"),"<h2>FieldType: <i>%s</i></h2><br>"%item.name]
	
	ret.append("""<table><tr><td>Name</td><td>%s</td></tr>
	<tr><td>Variable Type</td><td>%s</td></tr>
	<tr><td>Short Description</td><td>%s</td></tr>
	<tr><td>Long Description</td><td>%s</td></tr>
	<tr><td>Property</td><td>%s</td></tr>
	<tr><td>Default Units</td><td>%s</td></tr>
	<tr><td>Creator</td><td>%s (%s)</td></table></body></html>"""%(item.name,item.vartype,item.desc_short,
	item.desc_long,item.property,item.defaultunits,item.creator,item.creationtime))
	
	return "".join(ret)

def html_recordtypes(path,args,ctxid,host):
	global db
	
	ftn=db.getrecordtypenames()
	ret=[html_header("EMEN2 RecordTypes"),"<h2>Registered RecordTypes</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/recordtype?name="))

	ret.append("</body></html>")
	return "".join(ret)

def html_recordtype(path,args,ctxid,host):
	pass
	
def html_record(path,args,ctxid,host):
	pass

def html_users(path,args,ctxid,host):
	global db
	
	ftn=db.getusernames(ctxid,host)
	ret=[html_header("EMEN2 Users"),"<h2>Users</h2><br>%d defined:"%len(ftn)]
	ret.append(html_htable(ftn,3,"/db/user?name="))

	ret.append("</body></html>")
	return "".join(ret)

def html_user(path,args,ctxid,host):
	global db
	
	item=db.getuser(args["name"][0],ctxid,host)
	
	ret=[html_header("EMEN2 User"),"<h2>User: <i>%s</i></h2><br>"%item.username]
	
	ret.append("""<table><tr><td>Username</td><td>%s</td></tr>
	<tr><td>Name</td><td>%s</td></tr>
	<tr><td>Institution</td><td>%s</td></tr>
	<tr><td>Department</td><td>%s</td></tr>
	<tr><td>Address</td><td><pre>%s\n%s, %s  %s  %s</pre></td></tr>
	<tr><td>Webpage</td><td>%s</td></tr>
	<tr><td>Email</td><td>%s</td></tr>
	<tr><td>Phone</td><td>%s</td></tr>
	<tr><td>Fax</td><td>%s</td></tr>
	<tr><td>Cell Phone</td><td>%s</td></tr>
	<tr><td>Groups</td><td>%s</td></tr>
	<tr><td>Disabled</td><td>%d</td></tr>
	<tr><td>Privacy</td><td>%d</td></tr></table></body>"""%
	(item.username," ".join(item.name),item.institution,item.department,
	item.address,item.city,item.state,item.zipcode,item.country,
	item.webpage,item.email,item.phone,item.fax,item.cellphone,
	item.groups,item.disabled,item.privacy))
	
	return "".join(ret)

		
# We use a dictionary for callbacks rather than a series of if's
callbacks={'fieldtypes':html_fieldtypes,"fieldtype":html_fieldtype,"recordtypes":html_recordtypes,
"recordtype":html_recordtype,"record":html_record,"users":html_users,"user":html_user}
