from twisted.web.resource import Resource
from twisted.web import resource, server
from twisted.internet import defer, reactor, threads
import traceback
#from emen2 import Database
from twisted.web import xmlrpc
import xmlrpclib
import os
from sets import Set
from emen2.emen2config import *
from emen2 import Database
import emen2.TwistSupport_html.supp

import time

#from emen2 import ts

Fault = xmlrpclib.Fault

class XMLRPCResource(xmlrpc.XMLRPC):
	"""replaces the default version that doesn't allow None"""
	def _cbRender(self, result, request, t0=None):
		allow_none = True

		if isinstance(result, xmlrpc.Handler):
			result = result.result

		if isinstance(result,dict):
			d2={}
			for k,v in result.items():
				d2[str(k)]=v
			result=d2

		if not isinstance(result, xmlrpc.Fault):
			result = (result,)

		try:
			s = xmlrpclib.dumps(result, methodresponse=1,allow_none=allow_none)
		except:
			f = xmlrpc.Fault(self.FAILURE, "can't serialize output")
			s = xmlrpclib.dumps(f, methodresponse=1)
			print "fault: "
			print s
		request.setHeader("content-length", str(len(s)))
		request.write(s)
		request.finish()

	def _ebRender(self,result,request):
		print "fault in xmlrpc function: "
		print result
		f = xmlrpc.Fault(self.FAILURE, result.getErrorMessage())
		s = xmlrpclib.dumps(f, methodresponse=1)
		request.setHeader("content-length", str(len(s)))
		request.write(s)
		request.finish()

	def render(self, request):
		request.content.seek(0, 0)
		content = request.content.read()
#		print "--"
#		print content
#		print "--"
		args, functionPath = xmlrpclib.loads(content)
		host = request.getClientIP()
		kwargs={"host":host}
		print "\n---- [%s] [%s] ---- xmlrpc request: %s ----"%(time.strftime("%Y/%m/%d %H:%M:%S"),host,functionPath)

		if functionPath != "login":
			print args

		try:
			function = self._getFunction(functionPath)
		except Fault, f:
			print "fault..."
			self._cbRender(f, request)
		else:
			request.setHeader("content-type", "text/xml")

		d = threads.deferToThread(function, *args, **kwargs)
		d.addCallback(self._cbRender, request, t0=time.time())
		d.addErrback(self._ebRender,request)

		return server.NOT_DONE_YET 



	
	###########################
	# xmlrpc functions		

	def xmlrpc_login(self,username="anonymous",password="",host=None,db=None,maxidle=14400):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
		return str(db.login(str(username),str(password),host,maxidle))

	def xmlrpc_checkcontext(self,ctxid=None,host=None,db=None):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
		return db.checkcontext(ctxid,host)
		
	def xmlrpc_disableuser(self,username,ctxid=None,host=None,db=None):
		"""This will disable a user's account"""
		db.disableuser(username,ctxid,host)
	
	def xmlrpc_approveuser(self,username,ctxid=None,host=None,db=None):
		"""Database administrators use this to approve users in the new user queue"""
		db.approveuser(username,ctxid,host)
	
	def xmlrpc_getuserqueue(self,ctxid=None,host=None,db=None):
		"""Returns a list of users awaiting approval"""
		return db.getuserqueue(ctxid,host)

	def xmlrpc_putuser(self,user,ctxid=None,host=None,db=None):
		"""Commit a modified User record into the database, passwords
		cannot be changed with this method, and only the user and root
		can make this change."""
		db.putuser(user,ctxid,host)

	def xmlrpc_setpassword(self,username,oldpassword,newpassword,ctxid=None,host=None,db=None):
		"""This will modify a User's password. Only the user or a root
		user may do this. oldpassword is required for the user, but not
		for root users"""
		db.setpassword(username,oldpassword,newpassword,ctxid,host)

	def xmlrpc_adduser(self,user,host=None,db=None):
		"""adds a user to the new user queue. Users must be approved by an
		administrator before they have access. 'user' is a dictionary
		representing a User object"""
		usero=Database.User()
		usero.__dict__.update(user)
		db.adduser(self,usero)

	def xmlrpc_getuser(self,username,ctxid=None,host=None,db=None):
		"""Return a User record"""
		return db.getuser(username,ctxid,host).__dict__
		
	def xmlrpc_getqueueduser(self,username,ctxid=None,host=None,db=None):
		"""Return a User record """
		return db.getuser(username,ctxid,host).__dict__
		
	def xmlrpc_getusernames(self,ctxid=None,host=None,db=None):
		"""Return a list of all usernames in the database"""
		return db.getusernames(ctxid,host)

	def xmlrpc_getworkflow(self,ctxid=None,host=None,db=None):
		"""This returns a list of workflow objects (dictionaries) for the given user
		based on the current context"""
		r=db.getworkflow(ctxid,host)
		r=[x.__dict__ for x in r]
		return r
		
	def xmlrpc_setworkflow(self,wflist,ctxid=None,host=None,db=None):
		"""This will set the user's entire workflow list. This should rarely be used."""
		w=[Database.WorkFlow(with=i) for i in wflist]
		db.setworkflow(w,ctxid,host)
		
	def xmlrpc_addworkflowitem(self,work,ctxid=None,host=None,db=None):
		"""Adds a Workflow object to the user's workflow"""
		worko=Database.WorkFlow()
		worko.__dict__.update(work)
		db.addworkflowitem(worko,ctxid,host)
	
	def xmlrpc_delworkflowitem(self,wfid,ctxid=None,host=None,db=None):
		"""Delete a single workflow entry"""
		db.delworkflowitem(wfid,ctxid,host)
		
	def xmlrpc_getrecords(self,recids,ctxid=None,host=None,dbid=None,db=None):
		"""Retrieve records from the database as a list of dictionaries"""
		ret=[]
		for recid in recids:
			ret.append(db.getrecord(recid,ctxid,dbid).items_dict())		
		return ret
	
	def xmlrpc_getrecord(self,recid,ctxid=None,dbid=None,host=None,db=None):
		"""Retrieve a record from the database as a dictionary"""
		r=db.getrecord(recid,ctxid,dbid)
		return r.items_dict()
	
#	def putrecord(self,record,ctxid,host=None,parents=[],children=[]):
#	def newrecord(self,rectype,ctxid=None,host=None,init=0,inheritperms=None):
	def xmlrpc_putrecord(self,record,ctxid=None,parents=[],children=[],inheritperms=None,host=None,db=None):
		"""Puts a modified record back into the database"""

		# get a record instance to put..
		if record.has_key("recid"):
			rec=db.getrecord(record["recid"],ctxid)
		else:
			rec=db.newrecord(record["rectype"],ctxid,host,1,inheritperms)
		
		rec.update(record)

		r=db.putrecord(rec, ctxid=ctxid, host=host, parents=parents, children=children)
		return r

	def xmlrpc_addparamchoice(self,paramdefname,choice,host=None,db=None):
		"""This will add a choice to ParamDefs of vartype 'string'"""
		db.addparamchoice(paramdefname,choice)
			
	def xmlrpc_addparamdef(self,paramdef,ctxid=None,parent=None,host=None,db=None):
		"""Puts a new ParamDef in the database. User must have permission to add records."""
		r=Database.ParamDef()
		r.__dict__.update(paramdef)
		db.addparamdef(r,ctxid,host,parent)
		return r.name
	
	def xmlrpc_getparamdef(self,paramdefname,host=None,db=None):
		"""Anyone may retrieve any paramdef"""
		return db.getparamdef(paramdefname).__dict__
		
	def xmlrpc_getparamdefs(self,recs,host=None,db=None):
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
		
	def xmlrpc_getparamdefnames(self,host=None,db=None):
		"""List of all paramdef names"""
		return db.getparamdefnames()
	
	def xmlrpc_addrecorddef(self,recdef,ctxid=None,parent=None,host=None,db=None):
		"""New recorddefs may be added by users with record creation permission"""
		r=Database.RecordDef(recdef)
		return db.addrecorddef(r,ctxid,parent)
			
	def xmlrpc_getrecorddef(self,rectypename,ctxid=None,recid=None,host=None,db=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		r = db.getrecorddef(rectypename,ctxid,host=host,recid=recid).__dict__
		return r
					
	def xmlrpc_getrecorddefnames(self,host=None,db=None):
		"""The names of all recorddefs are globally available to prevent duplication"""
		return db.getrecorddefnames()
	
	def xmlrpc_getvartypenames(self,host=None,db=None):
		"""The names of all variable types, ie - int,float, etc."""
		return db.getvartypenames()
	
	def xmlrpc_getpropertynames(self,host=None,db=None):
		"""The names of all valid properties: temperature, pressure, etc."""
		return db.getpropertynames()

	def xmlrpc_getpropertyunits(self,propname,host=None,db=None):
		"""This returns a list of known units for a given physical property"""
		return db.getpropertyunits(propname)
		
	def xmlrpc_getchildren(self,key,keytype="record",recurse=0,ctxid=None,host=None,db=None):
		print ctxid
		"""Gets the children of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		children = list(db.getchildren(key,keytype,recurse=recurse,ctxid=ctxid,host=host))
		children.sort()
		return tuple(children)
	
	def xmlrpc_countchildren(self,key,recurse=0,ctxid=None,host=None,db=None):
		"""Unlike getchildren, this works only for 'records'. Returns a count of children
		of the specified record classified by recorddef as a dictionary. The special "all"
		key contains the sum of all different recorddefs"""
		return db.countchildren(key,recurse=0,ctxid=ctxid,host=host)

	def xmlrpc_getparents(self,key,keytype="record",recurse=0,ctxid=None,host=None,db=None):
		"""Gets the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return tuple(db.getparents(key,keytype,recurse,ctxid,host))
	
	def xmlrpc_getcousins(self,key,keytype="record",ctxid=None,host=None,db=None):
		"""Gets the cousins (related records with no defined parent/child relationship
		 of a record with the given key, keytype may be 'record', 'recorddef' or 'paramdef' """
		return tuple(db.getcousins(key,keytype,ctxid,host))
		
	def xmlrpc_pclink(self,pkey,ckey,keytype="record",ctxid=None,host=None,db=None):
		"""Produce a parent <-> child link between two records"""
		r = db.pclink(pkey,ckey,keytype,ctxid,host)
		return r
		
	def xmlrpc_pcunlink(self,pkey,ckey,keytype="record",ctxid=None,host=None,db=None):
		"""Remove a parent <-> child link. No error raised if link doesn't exist."""
		return db.pcunlink(pkey,ckey,keytype,ctxid,host)

	def xmlrpc_link(self,key1,key2,keytype="record",ctxid=None,host=None,db=None):
		"""Generate a 'cousin' relationship between two records"""
		return db.link(key1,key2,keytype,ctxid,host)
		
	def xmlrpc_unlink(self,key1,key2,keytype="record",ctxid=None,host=None,db=None):
		"""Remove a 'cousin' relationship."""
		return db.unlink(key1,key2,keytype,ctxid,host)
	
	def xmlrpc_isManager(self,ctxid=None,host=None,db=None):
		"""Returns true if context has manager permissions"""
		return db.isManager(ctxid,host)
	
	def xmlrpc_newbinary(self,date,name,ctxid=None,host=None,db=None):
		"""make a new binary identifier"""
		return db.newbinary(date,name,ctxid,host)
	
	def xmlrpc_getbinary(self,ident,ctxid=None,host=None,db=None):
		"""look up an existing binary identifier"""
		return db.getbinary(ident,ctxid,host)
	
	def xmlrpc_query(self,query,ctxid=None,retindex=False,host=None,db=None):
		"""full database query"""
		return db.query(query,ctxid,host,retindex)
	
	def xmlrpc_getindexbycontext(self,ctxid=None,host=None,db=None):
		return tuple(db.getindexbycontext(ctxid,host))
		
	def xmlrpc_getindexbyuser(self,username,ctxid=None,host=None,db=None):
		return tuple(db.getindexbyuser(username,ctxid,host))
	
	def xmlrpc_getindexbyrecorddef(self,recdefname,ctxid=None,host=None,db=None):
		return tuple(db.getindexbyrecorddef(recdefname,ctxid,host))
	
	def xmlrpc_getindexkeys(self,paramname,valrange=None,ctxid=None,host=None,db=None):
		return tuple(db.getindexkeys(paramname,valrange,ctxid,host))
	
	def xmlrpc_getindexbyvalue(self,paramname,valrange,ctxid=None,host=None,db=None):
		return tuple(db.getindexbyvalue(paramname,valrange,ctxid,host))
	
	def xmlrpc_getindexdictbyvalue(self,paramname,valrange,ctxid=None,subset=None,host=None,db=None):
		ret=db.getindexdictbyvalue(paramname,valrange,ctxid,host,subset)
		return ret
	
	def xmlrpc_groupbyrecorddef(self,all,ctxid=None,host=None,db=None):
		r = db.groupbyrecorddef(all,ctxid,host)
		ret=[]
		for k,v in r:
			ret[k]=tuple(v)
		return ret
	
	def xmlrpc_getworkflowitem(self,wfid,ctxid=None,host=None,db=None):
		return db.getworkflowitem(wfid,ctxid,host)
	
	def xmlrpc_putrecorddef(self,recdict,ctxid=None,host=None,db=None):
		recdef = Database.RecordDef(recdict)
		return db.putrecorddef(recdef,ctxid,host)

	def xmlrpc_getrecordnames(self,ctxid,dbid=0,host=None,db=None):
		return db.getrecordnames(ctxid,dbid,host)
	
	def xmlrpc_getrecordschangetime(self,recids,ctxid=None,host=None,db=None):
		return db.getrecordschangetime(recids,ctxid,host)
	
	def xmlrpc_secrecordadduser(self,usertuple,recid,ctxid=None,recurse=0,host=None,db=None):
		db.secrecordadduser(usertuple,int(recid),ctxid,host,recurse)
	
	def xmlrpc_secrecorddeluser(self,users,recid,ctxid=None,recurse=0,host=None,db=None):
		db.secrecorddeluser(users,recid,ctxid,host,recurse)
		
		
				
###################################################################
# Convenience functions (not direct map to db methods)

	def xmlrpc_putrecords(self,records,ctxid=None,parents=[],children=[],inheritperms=None,host=None,db=None):
		ret=[]
		for record in records:
			recid=self.xmlrpc_putrecord(record,ctxid,parents,children,inheritperms,host,db)
			ret.append(recid)
		return ret
	
	def xmlrpc_echo(self,args,host=None,db=None):
		for i in args:
			print i
		return str(args)
	
	def xmlrpc_error(self,host=None,db=None):
		raise KeyError
		return ""
	
	def xmlrpc_sleep(self,args,host=None,db=None):
		time.sleep(100)
		return ""
	
	def xmlrpc_ping(self,host=None,db=None):
		return "pong"

	def xmlrpc_test(self,host=None,db=None):
		a=Database.WorkFlow()
		b=Database.WorkFlow()
		c=(a,b)
		d=[dict(x.__dict__) for x in c]
		
		return {"a":None,"b":None}		
		
		
	def xmlrpc_checktile(self,bid,ctxid=None,host=None,db=None):
		from emen2.TwistSupport_html.html.tileimage import get_tile, get_tile_dim

		bname,ipath,bdocounter=db.getbinary(bid,ctxid)
		fpath=E2TILEPATH+bid+".tile"

		if not os.access(fpath,os.R_OK):
			return (-1,-1,bid)
		else:
			dims=get_tile_dim(fpath)
			dimsx=[i[0] for i in dims]
			dimsy=[i[1] for i in dims]
			return (dimsx,dimsy,bid) 

		
	def xmlrpc_createtile(self,bid,ctxid=None,host=None,db=None):
		from emen2.TwistSupport_html.html.tileimage import get_tile, get_tile_dim

		bname,ipath,bdocounter=db.getbinary(bid,ctxid)
		fpath=E2TILEPATH+bid+".tile"
		print "Generating tile... %s"%(ipath) 
		os.system("%s %s --build=%s --decompress=%s"%(E2TILEFILE,fpath,ipath,bname))

		if not os.access(fpath,os.R_OK):
			print "Error with tile."
			return (-1,-1,bid)
		else:
			dims=get_tile_dim(fpath)
			dimsx=[i[0] for i in dims]
			dimsy=[i[1] for i in dims]
			print (dimsx,dimsy,bid) 
			return (dimsx,dimsy,bid) 

			
		
	def xmlrpc_addcomment(self,recid,comment,ctxid=None,host=None,db=None):
		"""Append comment to record."""
		rec = db.getrecord(recid,ctxid=ctxid)
		rec["comments"] = comment
		return db.putrecord(rec,ctxid)
				
		
		
	def xmlrpc_getproto(self,classtype,ctxid=None,host=None,db=None):
		"""This will generate a 'dummy' record to fill in for a particular classtype.
		classtype may be: user,paramdef,recorddef,workflow or the name of a valid recorddef"""
		if	 (classtype.lower()=="user") :
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
			r=db.newrecord(classtype,ctxid,init=1)
			return r.items()		
		
		
		
	def xmlrpc_getchildrenofparents(self,key,keytype="record",recurse=0,ctxid=None,host=None,db=None):
		"""Gets the children of all the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		a = list(db.getparents(key,keytype,recurse=0,ctxid=ctxid,host=host))
		a.sort()
		b = []
		for i in a:
			children = list(db.getchildren(i,keytype,recurse=0,ctxid=ctxid,host=host))
			children.sort()
			b.append([i,children])
		return b		
	
	def xmlrpc_getrecnames(self,recids,ctxid,host=None,db=None):
		r=[]
		for recid in recids:
			r.append((recid,db.getrecordrecname(recid,ctxid)))
		return r
	
	def xmlrpc_getrelatedrecswithnames(self,key,type,ctxid,host=None,db=None):
		if type == "children": 
			a = db.getchildren(key,"record",0,ctxid)
		else: 
			a = db.getparents(key,"record",0,ctxid)
		r = []
		for i in a:
			z = db.getrecord(i,ctxid)
			r.append((i,z["recname"]))
		return r
		
		
	def xmlrpc_findparamname(self,q,ctxid=None,host=None,db=None):
		if len(q) < 3: return []
		
		q = q.lower()
		ret = []
		for i in db.getparamdefnames():
			z = db.getparamdef(i)
			
			try:
				if q in z.name.lower():
					ret.append((z.name,""))
					continue

				if q in z.desc_short.lower():
					ret.append((z.name,z.desc_short))
					continue

				if q in z.desc_long.lower():
					ret.append((z.name,z.desc_long))
			except:
				pass
			
		return ret
