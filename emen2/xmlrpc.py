from twisted.web.resource import Resource
#from emen2 import Database
from twisted.web import xmlrpc
import xmlrpclib
import os
from sets import Set
from emen2.emen2config import *

from emen2 import ts

class DBXMLRPCResource(xmlrpc.XMLRPC):
	"""replaces the default version that doesn't allow None"""
	def _cbRender(self, result, request, ctxid=None):
#		print "cbRender ctxid: %s"%ctxid
		#hari:
		#allow_none = True
		if isinstance(result, xmlrpc.Handler):
			result = result.result
		if not isinstance(result, xmlrpc.Fault):
			result = (result,)
		try:
			s = xmlrpclib.dumps(result, methodresponse=1)
		except:
			f = xmlrpc.Fault(self.FAILURE, "can't serialize output")
			s = xmlrpclib.dumps(f, methodresponse=1)
			
		#	s = xmlrpclib.dumps(f, methodresponse=1,allow_none=1)
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
		
	def xmlrpc_login(self,username="anonymous",password="",host=None,maxidle=14400):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
#		return str(ts.db.login(str(username),str(password),host,maxidle))
		try:
			return str(ts.db.login(str(username),str(password),host,maxidle))
		except:
			return 0,"Login Failed"	

	def xmlrpc_checkcontext(self,ctxid=None,host=None):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
#		print ctxid
#		print ts.db.checkcontext(ctxid,host)
		return ts.db.checkcontext(ctxid,host)
		
	def xmlrpc_disableuser(self,username,ctxid=None,host=None):
		"""This will disable a user's account"""
		ts.db.disableuser(username,ctxid,host)
	
	def xmlrpc_approveuser(self,username,ctxid=None,host=None):
		"""Database administrators use this to approve users in the new user queue"""
		ts.db.approveuser(username,ctxid,host)
	
	def xmlrpc_getuserqueue(self,ctxid=None,host=None):
		"""Returns a list of users awaiting approval"""
		return ts.db.getuserqueue(ctxid,host)

	def xmlrpc_putuser(self,user,ctxid=None,host=None):
		"""Commit a modified User record into the database, passwords
		cannot be changed with this method, and only the user and root
		can make this change."""
		ts.db.putuser(user,ctxid,host)

	def xmlrpc_setpassword(self,username,oldpassword,newpassword,ctxid=None,host=None):
		"""This will modify a User's password. Only the user or a root
		user may do this. oldpassword is required for the user, but not
		for root users"""
		ts.db.setpassword(username,oldpassword,newpassword,ctxid,host)

	def xmlrpc_adduser(self,user,host=None):
		"""adds a user to the new user queue. Users must be approved by an
		administrator before they have access. 'user' is a dictionary
		representing a User object"""
		usero=Database.User()
		usero.__dict__.update(user)
		ts.db.adduser(self,usero)

	def xmlrpc_getuser(self,username,ctxid=None,host=None):
		"""Return a User record"""
		return ts.db.getuser(username,ctxid,host).__dict__
		
	def xmlrpc_getqueueduser(self,username,ctxid=None,host=None):
		"""Return a User record """
		return ts.db.getuser(username,ctxid,host).__dict__
		
	def xmlrpc_getusernames(self,ctxid=None,host=None):
		"""Return a list of all usernames in the database"""
		return ts.db.getusernames(ctxid,host)

	def xmlrpc_getworkflow(self,ctxid=None,host=None):
		"""This returns a list of workflow objects (dictionaries) for the given user
		based on the current context"""
		r=ts.db.getworkflow(ctxid,host)
		r=[x.__dict__ for x in r]
		return r
		
	def xmlrpc_setworkflow(self,wflist,ctxid=None,host=None) :
		"""This will set the user's entire workflow list. This should rarely be used."""
		w=[Database.WorkFlow(with=i) for i in wflist]
		ts.db.setworkflow(w,ctxid,host)
		
	def xmlrpc_addworkflowitem(self,work,ctxid=None,host=None) :
		"""Adds a Workflow object to the user's workflow"""
		worko=Database.WorkFlow()
		worko.__dict__.update(work)
		ts.db.addworkflowitem(worko,ctxid,host)
	
	def xmlrpc_delworkflowitem(self,wfid,ctxid=None,host=None) :
		"""Delete a single workflow entry"""
		ts.db.delworkflowitem(wfid,ctxid,host)
		
	def xmlrpc_getrecords(self,recids,ctxid=None,host=None,dbid=None):
		"""Retrieve records from the database as a list of dictionaries"""
		ret=[]
		try:
			for recid in recids:
				ret.append(ts.db.getrecord(recid,ctxid,dbid).items())
		except Exception,x:
			return 0,x
		
		return ret
	
	def xmlrpc_getrecord(self,recid,ctxid=None,dbid=None):
		"""Retrieve a record from the database as a dictionary"""
		try:
			r=ts.db.getrecord(recid,ctxid,dbid)
		except Exception,x:
			return 0,x
		
		return r.items()
	
	def xmlrpc_putrecord(self,recid,record,ctxid=None,host=None):
		"""Puts a modified record back into the database"""
		
		print "recid: %s \n record: %s \n ctxid: %s"%(recid,record,ctxid)
		
		rec = ts.db.getrecord(recid,ctxid)
		for i in record:
			rec[i[0]] = i[1]
		
		print "storing record..."
		print rec
		
#		try:
		r=ts.db.putrecord(rec,ctxid,host)
#		except: return -1
			
		return r
		
	def xmlrpc_getproto(self,classtype,ctxid=None,host=None):
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
	
	def xmlrpc_addparamchoice(self,paramdefname,choice,host=None):
		"""This will add a choice to ParamDefs of vartype 'string'"""
		ts.db.addparamchoice(paramdefname,choice)
			
	def xmlrpc_addparamdef(self,paramdef,ctxid=None,host=None,parent=None):
		"""Puts a new ParamDef in the database. User must have permission to add records."""
		r=ts.DB.ParamDef()
		r.__dict__.update(paramdef)
		ts.db.addparamdef(r,ctxid,host,parent)
	
	def xmlrpc_addparamdef2(self, name, ctxid=None, parent=None, vartype=None,desc_short=None,desc_long=None,property=None,defaultunits=None,choices=None):
		"""Puts a new ParamDef in the database. User must have permission to add records."""

		print locals()
		a = ts.DB.ParamDef(name, vartype, desc_short, desc_long, property, defaultunits, choices)
		#print ctxid 
		#ts.db.addparamdef(a,ctxid,host,parent)
		print "addparamdef2 ctxid: %s"%ctxid
		ts.db.addparamdef(a,ctxid=ctxid,parent=parent)	
		
	def xmlrpc_getparamdef(self,paramdefname,host=None):
		"""Anyone may retrieve any paramdef"""
		return tuple(ts.db.getparamdef(paramdefname).__dict__)
		
	def xmlrpc_getparamdef2(self,paramdefname,host=None):
		"""Anyone may retrieve any paramdef"""
		"""Maybe will change it so that it just returns the tuples and lets javascript do the rest, the current way seemed easier at the time (needed a new function because getparamdef wasn't working with the javascript)"""		
		b = ()
		a = ts.db.getparamdef(paramdefname).__dict__ 
		for i in a:
			if not b:
				b = ((i,a[i]),)
#				print b
			else:
				if a[i] == None: a[i] = ""
				b = b + ((i,a[i]),)
#				print b
#		print b
		return b
		
	""" 'get' functions are made into tuples because that's the expected format for xml-rpc"""
		
	def xmlrpc_getparamdefs(self,recs,host=None):
		"""Return a dictionary of Paramdef objects. recs
		may be a record id, or a list of record ids"""
		if isinstance(recs,str): recs=(recs,)
		
		# ok, since we don't have Record instances, but just
		# ids, we'll make a list of unique parameters to pass in
		l=Set()
		for n in recs:
			i=ts.db.getrecord(n)
			l.union_update(i.keys())
			
		return ts.db.getparamdefs(list(l))
		
	def xmlrpc_getparamdefnames(self,host=None):
		"""List of all paramdef names"""
		return tuple(ts.db.getparamdefnames())
	
	def xmlrpc_addrecorddef(self,recdef,ctxid=None,host=None,parent=None):
		"""New recorddefs may be added by users with record creation permission"""
		r=Database.RecordDef(rectype)
		ts.db.addrecorddef(r,ctxid,parent)
		
	def xmlrpc_addrecorddef2(self,name,ctxid=None,mainview=None, views=None, params=None, host=None,parent=None):
		"""New recorddefs may be added by users with record creation permission"""
		r=Database.RecordDef(rectype)
		ts.db.addrecorddef(r,ctxid,parent)
			
#	def xmlrpc_getrecorddef(self,rectypename,ctxid,recid=None):
	def xmlrpc_getrecorddef(self,rectypename,ctxid=None,host=None,recid=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		return ts.db.getrecorddef(recname,ctxid,host=host,recid=recid).__dict__ 
		
	def xmlrpc_getrecorddef2(self,rectypename,ctxid=None,host=None,recid=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		#return ts.db.getrecorddef(recname,ctxid,host=host,recid=recid).__dict__ no such name as recname defined, typo..?
		print "getting recorddef: %s"%rectypename
		b = ()
		print "getrecorddef2 ctxid: %s"%host
		a = ts.db.getrecorddef(rectypename,ctxid,host=host,recid=recid).__dict__ 	
		for x in a:
			t = x
			t += '='
			c= str(a[x]) 
			b+=(t,c, ";")
#		print "got recorddef: %s"%b
		return b
			
	def xmlrpc_getrecorddefnames(self,host=None):
		"""The names of all recorddefs are globally available to prevent duplication"""
		return ts.db.getrecorddefnames()
	
	def xmlrpc_getvartypenames(self,host=None):
		"""The names of all variable types, ie - int,float, etc."""
		return ts.db.getvartypenames()
	
	def xmlrpc_getpropertynames(self,host=None):
		"""The names of all valid properties: temperature, pressure, etc."""
		return ts.db.getpropertynames()

	def xmlrpc_getpropertyunits(self,propname,host=None):
		"""This returns a list of known units for a given physical property"""
		return ts.db.getpropertyunits(propname)
		

	def xmlrpc_getchildren(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		"""Gets the children of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """


#		print key
#		print keytype
#		print ts.db.getchildren(key,keytype,recurse=0,ctxid=None,host=None)
		children = list(ts.db.getchildren(key,keytype,recurse=0,ctxid=None,host=None))
		children.sort()
		return tuple(children)
	
	def xmlrpc_countchildren(self,key,recurse=0,ctxid=None,host=None):
		"""Unlike getchildren, this works only for 'records'. Returns a count of children
		of the specified record classified by recorddef as a dictionary. The special "all"
		key contains the sum of all different recorddefs"""
		return ts.db.countchildren(key,recurse=0,ctxid=None,host=None)

	def xmlrpc_getparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		"""Gets the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		#print tuple(ts.db.getparents(key,keytype,recurse=0,ctxid=None,host=None))
		return tuple(ts.db.getparents(key,keytype,recurse=0,ctxid=None,host=None))
		
	
	def xmlrpc_getchildrenofparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		"""Gets the children of all the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		a = list(ts.db.getparents(key,keytype,recurse=0,ctxid=None,host=None))
		a.sort()
		b = ()
		for i in a:
			children = list(ts.db.getchildren(i,keytype,recurse=0,ctxid=None,host=None))
			children.sort()
			if not b:
				b = (   (i,)   +   tuple( children ) , )
			else:
				b = ( b ,  ((i,)  +  tuple( children ) ) )
		return b
		
	
	def xmlrpc_getcousins(self,key,keytype="record",ctxid=None,host=None):
		"""Gets the cousins (related records with no defined parent/child relationship
		 of a record with the given key, keytype may be 'record', 'recorddef' or 'paramdef' """
		return tuple(ts.db.getcousins(key,keytype,ctxid=None,host=None))
		
	def xmlrpc_pclink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		"""Produce a parent <-> child link between two records"""
		return ts.db.pclink(pkey,ckey,keytype,ctxid=None,host=None)
		
	def xmlrpc_pcunlink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		"""Remove a parent <-> child link. No error raised if link doesn't exist."""
		return ts.db.pcunlink(pkey,ckey,keytype,ctxid=None,host=None)

	def xmlrpc_link(self,key1,key2,keytype="record",ctxid=None,host=None):
		"""Generate a 'cousin' relationship between two records"""
		return ts.db.link(key1,key2,keytype,ctxid=None,host=None)
		
	def xmlrpc_unlink(self,key1,key2,keytype="record",ctxid=None,host=None):
		"""Remove a 'cousin' relationship."""
		return ts.db.unlink(key1,key2,keytype,ctxid=None,host=None)
	
	def xmlrpc_isManager(self,ctxid=None,host=None):
		"""Returns true if context has manager permissions"""
		return ts.db.isManager(ctxid,host)
	
	def xmlrpc_newbinary(self,date,name,ctxid=None,host=None):
		"""make a new binary identifier"""
		return ts.db.newbinary(date,name,ctxid,host)
	
	def xmlrpc_getbinary(self,ident,ctxid=None,host=None):
		"""look up an existing binary identifier"""
		return ts.db.getbinary(ident,ctxid,host)
	
	def xmlrpc_query(self,query,ctxid=None,host=None,retindex=False):
		"""full database query"""
		return tuple(ts.db.query(query,ctxid,host,retindex))
	
	def xmlrpc_getindexbycontext(self,ctxid=None,host=None):
		return tuple(ts.db.getindexbycontext(ctxid,host))
		
	def xmlrpc_getindexbyuser(self,username,ctxid=None,host=None):
		return tuple(ts.db.getindexbyuser(username,ctxid,host))
	
	def xmlrpc_getindexbyrecorddef(self,recdefname,ctxid=None,host=None):
		return tuple(ts.db.getindexbyrecorddef(recdefname,ctxid,host))
	
	def xmlrpc_getindexkeys(self,paramname,valrange=None,ctxid=None,host=None):
		return tuple(ts.db.getindexkeys(paramname,valrange,ctxid,host))
	
	def xmlrpc_getindexbyvalue(self,paramname,valrange,ctxid=None,host=None):
		return tuple(ts.db.getindexbyvalue(paramname,valrange,ctxid,host))
	
	def xmlrpc_getindexdictbyvalue(self,paramname,valrange,ctxid=None,host=None,subset=None):
		return tuple(ts.db.getindexdictbyvalue(paramname,valrange,ctxid,host,subset))
	
	def xmlrpc_groupbyrecorddef(self,all,ctxid=None,host=None):
		return ts.db.groupbyrecorddef(all,ctxid,host)
	
	def xmlrpc_getworkflowitem(self,wfid,ctxid=None,host=None):
		return ts.db.getworkflowitem(wfid,ctxid,host)
	
	def xmlrpc_putrecorddef(self,recdef,ctxid=None,host=None):
		return ts.db.putrecorddef(recdef,ctxid,host)

	def xmlrpc_getrecordnames(self,ctxid,dbid=0,host=None):
		return ts.db.getrecordnames(ctxid,dbid,host)
	
	def xmlrpc_getrecordschangetime(self,recids,ctxid=None,host=None):
		return ts.db.getrecordschangetime(recids,ctxid,host)
	
	def xmlrpc_secrecordadduser(self,usertuple,recid,ctxid=None,recurse=0,host=None):
		print "recurse: %s"%recurse
		ts.db.secrecordadduser(usertuple,int(recid),ctxid,host,recurse)
		# db functions need proper returns
		return ""
	
	def xmlrpc_secrecorddeluser(self,users,recid,ctxid=None,recurse=0,host=None):
		print "users: %s"%users
		print "recid: %s"%recid
		ts.db.secrecorddeluser(users,recid,ctxid,host,recurse)
		return ""