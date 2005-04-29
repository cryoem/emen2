#!/usr/bin/env python
# DBIsolator.py  04/28/2005   Steve Ludtke
#
# This program is used to isolate a server (like Apache) from
# direct interface with the database code. This program is run
# as a separate process and pipes data back and forth vi stdio

import Database
import os
import sys
import cPickle

db=None

def main():
	global db
	
	# we can't have any spurious output going to stdout
	out=sys.stdout
	sys.stdout=sys.stderr
	
	# open the database
	DB=Database
	if len(sys.argv)>1 : dbpath=sys.argv[1]
	else :
		try: dbpath=os.getenv("EMEN2DB")
		except: dbpath="/home/emen2/db"
	if dbpath==None : dbpath="/home/emen2/db"
	db=DB.Database(dbpath)

	# here is the main loop, respond to requests indefinitely
	while (1):
		request=cPickle.load(sys.stdin)
		if request=="EXIT": break
		
#		try:
		ret=dbisolator.__dict__["meth_"+request[0]](*request)
#		except Exception,msg:
#			ret=(0,msg)
		cPickle.dump(ret,out)
		out.flush()
		
	db=None

class dbisolator:	
	def meth_login(self,userid,password):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
		try:
			return str(db.login(str(userid),str(password),None))
		except:
			return 0,"Login Failed"	

	def meth_checkcontext(self,ctxid):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
		return db.checkcontext(ctxid)
		
	def meth_disableuser(self,username,ctxid):
		"""This will disable a user's account"""
		db.disableuser(username,ctxid)
	
	def meth_approveuser(self,username,ctxid):
		"""Database administrators use this to approve users in the new user queue"""
		db.approveuser(username,ctxid)
	
	def meth_getuserqueue(self,ctxid):
		"""Returns a list of users awaiting approval"""
		return db.getuserqueue(ctxid)

	def meth_putuser(self,user,ctxid):
		"""Commit a modified User record into the database, passwords
		cannot be changed with this method, and only the user and root
		can make this change."""
		db.putuser(user,ctxid)

	def meth_setpassword(self,username,oldpassword,newpassword,ctxid):
		"""This will modify a User's password. Only the user or a root
		user may do this. oldpassword is required for the user, but not
		for root users"""
		db.setpassword(username,oldpassword,newpassword,ctxid)

	def meth_adduser(self,user):
		"""adds a user to the new user queue. Users must be approved by an
		administrator before they have access. 'user' is a dictionary
		representing a User object"""
		usero=Database.User()
		usero.__dict__.update(user)
		db.adduser(self,usero)
				
	def meth_getuser(self,username,ctxid):
		"""Return a User record"""
		return db.getuser(username,ctxid,None).__dict__
		
	def meth_getqueueduser(self,username,ctxid):
		"""Return a User record """
		return db.getuser(username,ctxid,None).__dict__
		
	def meth_getusernames(self,ctxid):
		"""Return a list of all usernames in the database"""
		return db.getusernames(ctxid)

	def meth_getworkflow(self,ctxid):
		"""This returns a list of workflow objects (dictionaries) for the given user
		based on the current context"""
		r=db.getworkflow(ctxid)
		r=[x.__dict__ for x in r]
		return r
		
	def meth_setworkflow(self,wflist,ctxid):
		"""This will set the user's entire workflow list. This should rarely be used."""
		w=[Database.WorkFlow(with=i) for i in wflist]
		db.setworkflow(w,ctxid)
		
	def meth_addworkflowitem(self,work,ctxid):
		"""Adds a Workflow object to the user's workflow"""
		worko=Database.WorkFlow()
		worko.__dict__.update(work)
		db.addworkflowitem(worko,ctxid)
	
	def meth_delworkflowitem(self,wfid,ctxid):
		"""Delete a single workflow entry"""
		db.delworkflowitem(wfid,ctxid)
		
	def meth_getrecords(self,recids,ctxid,dbid=0):
		"""Retrieve records from the database as a list of dictionaries"""
		ret=[]
		try:
			for recid in recids:
				ret.append(db.getrecord(recid,ctxid,dbid).items_dict())
		except Exception,x:
			return 0,x
		
		return ret
	
	def meth_getrecord(self,recid,ctxid,dbid=0):
		"""Retrieve a record from the database as a dictionary"""
		try:
			r=db.getrecord(recid,ctxid,dbid)
		except Exception,x:
			return 0,x
		
		return r.items_dict()
	
	def meth_getrecordnames(self,ctxid,dbid=0):
		"""Retrieve a record from the database as a dictionary"""
		try:
			r=db.getrecordnames(ctxid,dbid)
		except Exception,x:
			return 0,x
		
		return r
	
	def meth_putrecord(self,record,ctxid):
		"""Puts a modified record back into the database"""
		try:
			r=db.putrecord(recid,record,ctxid)
		except: return -1
			
		return r
		
	def meth_getproto(self,classtype,ctxid):
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
	
	def meth_addparamchoice(self,paramdefname,choice):
		"""This will add a choice to ParamDefs of vartype 'string'"""
		db.addparamchoice(paramdefname,choice)
			
	def meth_addparamdef(self,paramdef,ctxid,parent=None):
		"""Puts a new ParamDef in the database. User must have permission to add records."""
		r=Database.ParamDef()
		r.__dict__.update(paramdef)
		db.addparamdef(r,ctxid,parent)
		
	def meth_getparamdef(self,paramdefname):
		"""Anyone may retrieve any paramdef"""
		return db.getparamdef(paramdefname).__dict__
	
	def meth_getparamdefs(self,recs):
		"""Return a dictionary of Paramdef objects. recs
		may be a record id, or a list of record ids"""
		if isinstance(recs,str): recs=(recs,)
		
		# ok, since we don't have Record instances, but just
		# ids, we'll make a list of unique parameters to pass in
		l=Set()
		for n in recs:
			i=db.getrecord(n)
			l.union_update(i.keys())
			
		return db.getparamdefs(list(l))
		
	def meth_getparamdefnames(self):
		"""List of all paramdef names"""
		return db.getparamdefnames()
	
	def meth_addrecorddef(self,rectype,ctxid,parent=None):
		"""New recorddefs may be added by users with record creation permission"""
		r=Database.RecordDef(rectype)
		db.addrecorddef(r,ctxid,parent)
			
	def meth_getrecorddef(self,rectypename,ctxid,recid=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		return db.getrecorddef(rectypename,ctxid,recid=recid).__dict__
			
	def meth_getrecorddefnames(self):
		"""The names of all recorddefs are globally available to prevent duplication"""
		return db.getrecorddefnames()
	
	def meth_getvartypenames(self):
		"""The names of all variable types, ie - int,float, etc."""
		return db.getvartypenames()
	
	def meth_getpropertynames(self):
		"""The names of all valid properties: temperature, pressure, etc."""
		return db.getpropertynames()

	def meth_getpropertyunits(self,propname):
		"""This returns a list of known units for a given physical property"""
		return db.getpropertyunits(propname)
		
	def meth_getchildren(self,key,keytype="record",paramname=None,recurse=0,ctxid=None,host=0):
		"""Gets the children of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return db.getchildren(key,keytype,paramname,recurse,ctxid,host)
	
	def meth_getparents(self,key,keytype="record",recurse=0,ctxid=None,host=0):
		"""Gets the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return db.getparents(key,keytype,recurse,ctxid,host)
	
	def meth_getcousins(self,key,keytype="record"):
		"""Gets the cousins (related records with no defined parent/child relationship
		 of a record with the given key, keytype may be 'record', 'recorddef' or 'paramdef' """
		return db.getcousins(key,keytype)
		
	def meth_pclink(self,pkey,ckey,keytype="record"):
		"""Produce a parent <-> child link between two records"""
		return db.pclink(pkey,ckey,keytype)
		
	def meth_pcunlink(self,pkey,ckey,keytype="record"):
		"""Remove a parent <-> child link. No error raised if link doesn't exist."""
		return db.pcunlink(pkey,ckey,keytype)
		
	def meth_link(self,key1,key2,keytype="record"):
		"""Generate a 'cousin' relationship between two records"""
		return db.link(key1,key2,keytype)
		
	def meth_unlink(self,key1,key2,keytype="record"):
		"""Remove a 'cousin' relationship."""
		return db.unlink(key1,key2,keytype)
		
if __name__ == "__main__":
	main()

