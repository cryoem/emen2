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
from sets import Set

# we open the database as part of the module initialization
db=None
DB=Database 

def startup(path):
	global db
	db=Database.Database(path)
	
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

	def xmlrpc_checkcontext(self,ctxid):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
			
		
	def xmlrpc_disableuser(self,username,ctxid):
		"""This will disable a user's account"""
		db.disableuser(username,ctxid)
	
	def xmlrpc_approveuser(self,username,ctxid):
		"""Database administrators use this to approve users in the new user queue"""
		db.approveuser(username,ctxid)
	
	def xmlrpc_getuserqueue(self,ctxid):
		"""Returns a list of users awaiting approval"""
		return db.getuserqueue(ctxid)

	def xmlrpc_putuser(self,user,ctxid):
		"""Commit a modified User record into the database, passwords
		cannot be changed with this method, and only the user and root
		can make this change."""
		db.putuser(user,ctxid)

	def xmlrpc_setpassword(self,username,oldpassword,newpassword,ctxid):
		"""This will modify a User's password. Only the user or a root
		user may do this. oldpassword is required for the user, but not
		for root users"""
		db.setpassword(username,oldpassword,newpassword,ctxid)

	def xmlrpc_adduser(self,user):
		"""adds a user to the new user queue. Users must be approved by an
		administrator before they have access. 'user' is a dictionary
		representing a User object"""
		usero=Database.User()
		usero.__dict__.update(user)
		db.adduser(self,usero)
				
	def xmlrpc_getuser(self,username,ctxid):
		"""Return a User record"""
		return db.getuser(username,ctxid,None).__dict__
		
	def xmlrpc_getqueueduser(self,username,ctxid):
		"""Return a User record """
		return db.getuser(username,ctxid,None).__dict__
		
	def xmlrpc_getusernames(self,ctxid):
		"""Return a list of all usernames in the database"""
		return db.getusernames(ctxid)

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
		
	def xmlrpc_getproto(self,classtype,ctxid):
		"""This will generate a 'dummy' record to fill in for a particular classtype.
		classtype may be: user,paramdef,recorddef,workflow or the name of a valid recorddef"""
		if   (classtype.lower()=="user") :
			r=Database.User()
			return r.__dict__
		elif (classtype.lower()=="paramdef") :
			r=Database.ParamDef()
			return r.__dict__
		elif (classtype.lower()=="recorddef") :
			r=Database.RecordDef()
			return r.__dict__
		elif (classtype.lower()=="workflow") :
			r=Database.Workflow()
			return r.__dict__
		else :
			r=Database.newrecord(classtype,ctxid,init=1)
			return r.items()
		
	def xmlrpc_addparamdef(self,paramdef,ctxid):
		"""Puts a new ParamDef in the database. User must have permission to add records."""
		r=Database.ParamDef()
		r.__dict__.update(paramdef)
		db.addparamdef(r,ctxid)
		
	def xmlrpc_getparamdef(self,paramdefname):
		"""Anyone may retrieve any paramdef"""
		return db.getparamdef(paramdefname).__dict__
	
	def xmlrpc_getparamdefs(self,recs):
		"""Return a dictionary of Paramdef objects. recs
		may be a record, a list of records, or a list of strings (parameter names)"""
		if isinstance(recs,dict): recs=(recs,)
		
		if isinstance(recs[0],str): return db.getparamdefs(recs)
		
		# ok, since we don't really have Record instances, but just
		# dictionaries, we'll make a list of unique parameters to pass in
		l=Set()
		for i in recs:
			l.union_update(i.keys())
			
		return db.getparamdefs(list(l))
		
	def xmlrpc_getparamdefnames(self):
		"""List of all paramdef names"""
		return db.getparamdefnames()
	
	def xmlrpc_addrecorddef(self,rectype,ctxid):
		"""New recorddefs may be added by users with record creation permission"""
		r=Database.RecordDef(rectype)
		db.addrecorddef(r,ctxid)
			
	def xmlrpc_getrecorddef(self,rectypename,ctxid,recid=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		return db.getrecorddef(recname,ctxid,recid=recid).__dict__
			
	def xmlrpc_getrecorddefnames(self):
		"""The names of all recorddefs are globally available to prevent duplication"""
		return db.getrecorddefnames()
	
	def xmlrpc_getvartypenames(self):
		"""The names of all variable types, ie - int,float, etc."""
		return db.getvartypenames()
	
	def xmlrpc_getpropertynames(self):
		"""The names of all valid properties: temperature, pressure, etc."""
		return db.getpropertynames()

	def xmlrpc_getchildren(self,key,keytype="record"):
		"""Gets the children of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return db.getchildren(key,keytype)
	
	def xmlrpc_getparents(self,key,keytype="record"):
		"""Gets the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return db.getparents(key,keytype)
	
	def xmlrpc_getcousins(self,key,keytype="record"):
		"""Gets the cousins (related records with no defined parent/child relationship
		 of a record with the given key, keytype may be 'record', 'recorddef' or 'paramdef' """
		return db.getcousins(key,keytype)
		
	def xmlrpc_pclink(self,pkey,ckey,keytype="record"):
		"""Produce a parent <-> child link between two records"""
		return db.pclink(pkey,ckey,keytype)
		
	def xmlrpc_pcunlink(self,pkey,ckey,keytype="record"):
		"""Remove a parent <-> child link. No error raised if link doesn't exist."""
		return db.pcunlink(pkey,ckey,keytype)
		
	def xmlrpc_link(self,key1,key2,keytype="record"):
		"""Generate a 'cousin' relationship between two records"""
		return db.link(key1,key2,keytype)
		
	def xmlrpc_unlink(self,key1,key2,keytype="record"):
		"""Remove a 'cousin' relationship."""
		return db.unlink(key1,key2,keytype)
