from twisted.web.resource import Resource
from emen2 import Database 
from twisted.web import xmlrpc
import xmlrpclib
import os

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
	"""This resource serves HTML requests. Look in TwistServer for the actual server code."""
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
	
	if (len(itmlist)%cols!=0) : ret.append("</tr></table>/n")
	else : ret.append("</table><br>")

	return "".join(ret)

def html_dicttable(dict,proto):
	"""Produce a table of values in 'cols' columns"""
	ret=["<table>"]
	
	for k,v in dict:
		ret.append("<tr><td><a href=%s/%s>%s</a></td><td>%s</td></tr>\n"%(proto,k,k,v))
		
	ret.append("</table><br>")

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
	global db
	
	item=db.getrecordtype(args["name"][0])
	
	ret=[html_header("EMEN2 RecordType Description"),"<h2>RecordType: <i>%s</i></h2><br>fields:<br>"%item.name]
	
	ret.append(html_dicttable(item.fields,"/db/fieldtype?name="))
	ret.append("<br>Default View:<br><form><textarea rows=10 cols=60>%s</textarea></form>"%item.mainview)
	ret.append("""</body></html>""")
	
	return "".join(ret)
	
def html_record(path,args,ctxid,host):
	global db
	
	item=db.getrecord(int(args["name"][0]),ctxid)

	ret=[html_header("EMEN2 Record"),"<h2>Recor: <i>%d</i></h2><br>fields:<br>"%int(item.recid)]
	
	ret.append(html_dicttable(item.items(),"/db/fieldtype?name="))
	ret.append("""</body></html>""")
	
	return "".join(ret)

	
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

class DBXMLRPCResource(xmlrpc.XMLRPC):
	"""replaces the default version that doesn't allow None"""
	def _cbRender(self, result, request):
		if isinstance(result, xmlrpc.Handler):
			result = result.result
		if not isinstance(result, xmlrpc.Fault):
			result = (result,)
		try:
			s = xmlrpclib.dumps(result, methodresponse=1,allow_none=1)
		except:
			f = xmlrpc.Fault(self.FAILURE, "can't serialize output")
			s = xmlrpclib.dumps(f, methodresponse=1,allow_none=1)
		request.setHeader("content-length", str(len(s)))
		request.write(s)
		request.finish()

	
	def xmlrpc_ping(self):
		return "pong"

	def xmlrpc_test(self):
		a=Database.WorkFlow()
		b=Database.WorkFlow()
		c=(a,b)
		d=[dict(x.__dict__) for x in c]
		
		return {"a":None,"b":None}

		
	def xmlrpc_login(self,userid,password):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
		try:
			return str(db.login(str(userid),str(password),None))
		except:
			return 0,"Login Failed"	

	def xmlrpc_getproto(self,classtype):
		"""This will generate a 'dummy' record to fill in for a particular classtype.
		classtype may be: user,fieldtype,recordtype,workflow or the name of a valid recordtype"""
					
	def xmlrpc_getuser(self,username,ctxid):
		"""Return a User record"""
		return db.getuser(username,ctxid,None).__dict__
		
	def xmlrpc_getusernames(self,ctxid):
		"""Return a list of all usernames in the database"""
		return db.getusernames(ctxid)

	def xmlrpc_disableuser(self,username,ctxid,host=None):
	def xmlrpc_approveuser(self,username,ctxid,host=None):
	def xmlrpc_adduser(self,user):

				
	def xmlrpc_getworkflow(self,ctxid):
		"""This returns a list of workflow objects (dictionaries) for the given user
		based on the current context"""
		return db.getworkflow(ctxid)

	def xmlrpc_addworkflow(self,work,ctxid,host=None):
	def xmlrpc_setworkflow(self,wflist,ctxid,host=None):

				
	def xmlrpc_getrecord(self,recid,ctxid,dbid=None):
		"""Retrieve a record from the database"""
		try:
			r=db.getrecord(recid,ctxid,dbid)
		except Exception,x:
			return 0,x
		
		return r.items()
	def xmlrpc_putrecord(self,record,ctxid,host=None):
	
	def xmlrpc_addfieldtype(self,fieldtype,ctxid,host=None):
	def xmlrpc_getfieldtype(self,fieldtypename):
	def xmlrpc_getfieldtypenames(self):
	
	def xmlrpc_addrecordtype(self,rectype,ctxid,host=None):
	def xmlrpc_getrecordtype(self,rectypename,ctxid,host=None,recid=None):
	def xmlrpc_getrecordtypenames(self):
	
