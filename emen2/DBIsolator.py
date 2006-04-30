#!/usr/bin/env python
# DBIsolator.py  04/28/2005   Steve Ludtke
#
# This program is used to isolate a server (like Apache) from
# direct interface with the database code. This program is run
# as a separate process and pipes data back and forth via stdio

from emen2 import Database
from emen2.emen2config import *
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
		except: dbpath=EMEN2DBPATH
	if dbpath==None : dbpath=EMEN2DBPATH
	db=DB.Database(dbpath)

	# here is the main loop, respond to requests indefinitely
	while (1):
		request=cPickle.load(sys.stdin)
		if request=="EXIT": break
		
		sys.stderr.write(str(request)+"\n")	# logging for debugging
# 		try:
		ret=dbisolator.__dict__["meth_"+request[0]](*request)
#		except Exception,msg:
#			ret=(0,request,msg)
		cPickle.dump(ret,out)
		out.flush()
		
	db=None

class dbisolator:	
	def meth_login(self,username="anonymous",password="",host=None,maxidle=1800):
		return db.login(username,password,None)
	def meth_isManager(self, ctxid, host=None):
	        return db.isManager(ctxid, host)
	def meth_isMe(self, ctxid, host=None):
	        return db.isMe(ctxid, host)
	
	def meth_loginuser(self, ctxid, host=None):
		return db.loginuser(ctxid, host)

	def meth_checkcontext(self,ctxid,host=None):
		return db.checkcontext(ctxid,host)
	
	def meth_query(self, query, ctxid, host=None, retindex=False):
       		return db.query(query, ctxid, host, retindex)
	
	def meth_getindexbyuser(self,username,ctxid,host=None):
		return db.getindexbyuser(self,username,ctxid,host)
	
	def meth_getindexbyrecorddef(self,recdefname,ctxid,host=None):
		return db.getindexbyrecorddef(recdefname,ctxid,host)
		
	def meth_getindexkeys(self,paramname,valrange=None,ctxid=None,host=None):
		return db.getindexkeys(paramname,valrange,ctxid,host)

	def meth_getindexbyvalue(self,paramname,valrange,ctxid,host=None):
		return db.getindexbyvalue(paramname,valrange,ctxid,host)
	
	def meth_getindexdictbyvalue(self,paramname,valrange,ctxid,host=None,subset=None):
		return db.getindexdictbyvalue(paramname,valrange,ctxid,host,subset)
	
	def meth_groupbyrecorddef(self,all,ctxid=None,host=None):
		return db.groupbyrecorddef(all,ctxid,host)
	
	def meth_getchildren(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		return db.getchildren(key,keytype,recurse,ctxid,host)
		
	def meth_getparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		return db.getparents(key,keytype,recurse,ctxid,host)
	
	def meth_getcousins(self,key,keytype="record",ctxid=None,host=None):
		return db.getcousins(key,keytype,ctxid,host)
	
	def meth_pclink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		return db.pclink(pkey,ckey,keytype,ctxid,host)

	def meth_pcunlink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		return db.pcunlink(pkey,ckey,keytype,ctxid,host)
	
	def meth_link(self,key1,key2,keytype="record",ctxid=None,host=None):
		return db.link(key1,key2,keytype,ctxid,host)
		
	def meth_unlink(self,key1,key2,keytype="record",ctxid=None,host=None):
		return db.unlink(key1,key2,keytype,ctxid,host)
	
	def meth_disableuser(self,username,ctxid,host=None):
		return db.disableuser(username,ctxid,host)
		
	def meth_approveuser(self,username,ctxid,host=None):
		return db.approveuser(username,ctxid,host)
		
	
	def meth_getuserqueue(self,ctxid,host=None):
		return db.getuserqueue(ctxid,host)
		
	def meth_putuser(self,user,ctxid,host=None):
		return db.putuser(user,ctxid,host)
	
	def meth_putuserdict(self,username,userdict,ctxid,host=None):
		return db.putuserdict(username, userdict, ctxid, host)
			
	def meth_setpassword(self,username,oldpassword,newpassword,ctxid,host=None):
		return db.setpassword(username,oldpassword,newpassword,ctxid,host)

	def meth_adduserdict(self,userdict):
		theuser = Database.User(userdict)
		db.adduser(theuser)
		return theuser
	
	def meth_adduser(self,user):
		return db.adduser(user)

	def meth_getqueueduser(self,username,ctxid,host=None):
		return db.getqueueduser(username,ctxid,host)
		
	def meth_getuser(self,username,ctxid,host=None):
		return db.getuser(username,ctxid,host)
	
	def meth_getusernames(self,ctxid,host=None):
		return db.getusernames(ctxid,host)
	
	def meth_getworkflow(self,ctxid,host=None):
		return db.getworkflow(ctxid,host)

	def meth_newworkflow(self, with):
		theobj = db.newworkflow(with)
		return theobj
	
	def meth_getworkflowitem(self,wfid,ctxid,host=None):
		return db.getworkflowitem(wfid, ctxid, host)
	
	def meth_addworkflowitem(self,work,ctxid,host=None) :
		return db.addworkflowitem(work,ctxid,host)
		
	def meth_delworkflowitem(self,wfid,ctxid,host=None) :
		return db.delworkflowitem(wfid,ctxid,host)
	
	def meth_setworkflow(self,wflist,ctxid,host=None) :
		return db.setworkflow(wflist,ctxid,host)
		
	def meth_getvartypenames(self):
		return db.getvartypenames()
	
	def meth_getvartype(self, thekey, thevalue):
		return db.getvartype(thekey)(thevalue)
	
	def meth_getpropertynames(self):
		return db.getpropertynames()
		
	def meth_getpropertyunits(self,propname):
		return getpropertyunits(propname)
		
	def meth_addparamdef(self,paramdef,ctxid,host=None,parent=None):
		return db.addparamdef(paramdef,ctxid,host,parent)
		
	def meth_addparamchoice(self,paramdefname,choice):
		return db.addparamchoice(paramdefname,choice)
	
	def meth_getparamdef(self,paramdefname):
		return db.getparamdef(paramdefname)
	
	def meth_getparamdefnames(self):
		return db.getparamdefnames()
		
	def meth_getparamdefs(self,recs):
		return db.getparamdefs(recs)
	
	def meth_addrecorddef(self,recdef,ctxid,host=None,parent=None):
		return db.addrecorddef(recdef,ctxid,host,parent)
	
	def meth_putrecorddef(self,recdef,ctxid,host=None):
		db.putrecorddef(recdef,ctxid,host)
	
	def meth_getrecorddef(self,rectypename,ctxid,host=None,recid=None):
		return db.getrecorddef(rectypename,ctxid,host,recid)
		
	def meth_getrecorddefnames(self):
		return db.getrecorddefnames()
	
	def meth_putrecord(self,record,ctxid,host=None):
#		db.LOG(2,str(record.__dict__))
		return db.putrecord(record,ctxid,host)
	
	def meth_newrecord(self,rectype,ctxid,host=None,init=0):
		rec=db.newrecord(rectype,ctxid,host,init)
		rec.localcpy=1
		return rec
	
	def meth_getrecordnames(self,ctxid,dbid=0,host=None) :
		return db.getrecordnames(ctxid,dbid,host)
	
	def meth_getrecordschangetime(self,recids,ctxid,host=None):
		return db.getrecordschangetime(recids,ctxid,host)
	
	def meth_getrecord(self,recid,ctxid,host=None,dbid=0) :
		rec=db.getrecord(recid,ctxid,host,dbid)
		rec.localcpy=1
		return rec
		
	def meth_secrecordadduser(self,usertuple,recid,ctxid,host=None,recurse=0):
		return db.secrecordadduser(usertuple,recid,ctxid,host,recurse)
		
	def meth_secrecorddeluser(self,users,recid,ctxid,host=None,recurse=0):
		return db.secrecorddeluser(users,recid,ctxid,host,recurse)


		
if __name__ == "__main__":
	main()

