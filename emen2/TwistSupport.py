# TwistSupport.py  Steven Ludtke  06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

from twisted.web.resource import Resource
from emen2 import Database 
from twisted.web import xmlrpc
import xmlrpclib
import os

# we open the database as part of the module initialization
db=Database.Database("/home/stevel/emen2test")

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

	def xmlrpc_getproto(self,classtype,ctxid):
		"""This will generate a 'dummy' record to fill in for a particular classtype.
		classtype may be: user,fieldtype,recordtype,workflow or the name of a valid recordtype"""
		if   (classtype.lower()=="user") :
			r=Database.User()
			return r.__dict__
		elif (classtype.lower()=="fieldtype") :
			r=Database.FieldType()
			return r.__dict__
		elif (classtype.lower()=="recordtype") :
			r=Database.RecordType()
			return r.__dict__
		elif (classtype.lower()=="workflow") :
			r=Database.Workflow()
			return r.__dict__
		else :
			r=Database.newrecord(classtype,ctxid,init=1)
			return r.items()
		
		
	def xmlrpc_getuser(self,username,ctxid):
		"""Return a User record"""
		return db.getuser(username,ctxid,None).__dict__
		
	def xmlrpc_getusernames(self,ctxid):
		"""Return a list of all usernames in the database"""
		return db.getusernames(ctxid)

	def xmlrpc_disableuser(self,username,ctxid):
		"""This will disable a user's account"""
		db.disableuser(username,ctxid)
	
	def xmlrpc_approveuser(self,username,ctxid):
		"""Database administrators use this to approve users in the new user queue"""
		db.approveuser(username,ctxid)
	
	def xmlrpc_adduser(self,user):
		"""adds a user to the new user queue. Users must be approved by an
		administrator before they have access. 'user' is a dictionary
		representing a User object"""
		usero=Database.User()
		usero.__dict__.update(user)
		db.adduser(self,usero)
				
	def xmlrpc_getworkflow(self,ctxid):
		"""This returns a list of workflow objects (dictionaries) for the given user
		based on the current context"""
		r=db.getworkflow(ctxid)
		r=[x.__dict__ for x in r]
		return r
		
	def xmlrpc_setworkflow(self,wflist,ctxid):
		"""This will set the user's entire workflow list. This should rarely be used."""
		w=[Database.WorkFlow(with=i) for i in wflist]
		db.setworkflow(w,ctxid)
		
	def xmlrpc_addworkflowitem(self,work,ctxid):
		"""Adds a Workflow object to the user's workflow"""
		worko=Database.WorkFlow()
		worko.__dict__.update(work)
		db.addworkflowitem(worko,ctxid)
	
	def xmlrpc_delworkflowitem(self,wfid,ctxid):
		"""Delete a single workflow entry"""
		db.delworkflowitem(wfid,ctxid)
		
	def xmlrpc_getrecord(self,recid,ctxid,dbid=None):
		"""Retrieve a record from the database as a dictionary"""
		try:
			r=db.getrecord(recid,ctxid,dbid)
		except Exception,x:
			return 0,x
		
		return r.items()
	
	def xmlrpc_putrecord(self,record,ctxid):
		"""Puts a modified record back into the database"""
		try:
			r=db.putrecord(recid,record,ctxid)
		except: return -1
			
		return r
		
	def xmlrpc_addfieldtype(self,fieldtype,ctxid):
		"""Puts a new FieldType in the database. User must have permission to add records."""
		r=Database.FieldType()
		r.__dict__.update(fieldtype)
		db.addfieldtype(r,ctxid)
		
	def xmlrpc_getfieldtype(self,fieldtypename):
		"""Anyone may retrieve any fieldtype"""
		return db.getfieldtype(fieldtypename).__dict__
	
	def xmlrpc_getfieldtypenames(self):
		"""List of all fieldtype names"""
		return db.getfieldtypenames()
	
	def xmlrpc_addrecordtype(self,rectype,ctxid):
		"""New recordtypes may be added by users with record creation permission"""
		r=Database.RecordType(rectype)
		db.addrecordtype(r,ctxid)
			
	def xmlrpc_getrecordtype(self,rectypename,ctxid,recid=None):
		"""Most RecordTypes are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		return db.getrecordtype(recname,ctxid,recid=recid).__dict__
			
	def xmlrpc_getrecordtypenames(self):
		"""The names of all recordtypes are globally available to prevent duplication"""
		return db.getrecordtypenames()
	def xmlrpc_getvartypenames(self):
		"""The names of all variable types, ie - int,float, etc."""
		return db.getvartypenames()
	
	def xmlrpc_getpropertynames(self):
		"""The names of all valid properties: temperature, pressure, etc."""
		return db.getpropertynames()
