from twisted.web.resource import Resource
from twisted.web import resource, server
from twisted.internet import defer

#from emen2 import Database
from twisted.web import xmlrpc
import xmlrpclib
import os
from sets import Set
from emen2.emen2config import *

import time

from emen2 import ts

Fault = xmlrpclib.Fault


class DBXMLRPCResource(xmlrpc.XMLRPC):
	"""replaces the default version that doesn't allow None"""
	def _cbRender(self, result, request, ctxid=None):
	#		#hari:
		allow_none = True
		if isinstance(result, xmlrpc.Handler):
			result = result.result
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
	
	
	
	def render(self, request):
		 request.content.seek(0, 0)

		 content = request.content.read()
		 args, functionPath = xmlrpclib.loads(content)

		 print "--------- xmlrpc request: %s ----------------"%functionPath
		 print args

		 try:
				 function = self._getFunction(functionPath)
		 except Fault, f:
				 print "fault..."
				 self._cbRender(f, request)
		 else:
				 request.setHeader("content-type", "text/xml")
				 defer.maybeDeferred(function, *args).addErrback(
						 self._ebRender
				 ).addCallback(
						 self._cbRender, request
				 )
		 return server.NOT_DONE_YET 



	
	###########################
	# xmlrpc functions		

	def xmlrpc_login(self,username="anonymous",password="",host=None,maxidle=14400):
		"""login method, should probably be called with https, TODO: note no support for host validation yet
		This returns a ctxid to the caller. The ctxid must be used in subsequent requests"""
		try:
			return str(ts.db.login(str(username),str(password),host,maxidle))
		except:
			return 0,"Login Failed" 

	def xmlrpc_checkcontext(self,ctxid=None,host=None):
		"""This routine will verify that a context id is valid, and return the
		authorized username for a context as well as a list of authorized groups"""
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
		usero=ts.DB.User()
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
		
	def xmlrpc_setworkflow(self,wflist,ctxid=None,host=None):
		"""This will set the user's entire workflow list. This should rarely be used."""
		w=[ts.DB.WorkFlow(with=i) for i in wflist]
		ts.db.setworkflow(w,ctxid,host)
		
	def xmlrpc_addworkflowitem(self,work,ctxid=None,host=None):
		"""Adds a Workflow object to the user's workflow"""
		worko=ts.DB.WorkFlow()
		worko.__dict__.update(work)
		ts.db.addworkflowitem(worko,ctxid,host)
	
	def xmlrpc_delworkflowitem(self,wfid,ctxid=None,host=None):
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
	
	def xmlrpc_putrecord(self,record,ctxid=None,host=None):
		"""Puts a modified record back into the database"""

		print "ctxid: %s"%ctxid
		recdict = {}
		recdict.update(record)
		
		try:
			rec = ts.db.getrecord(int(recdict["recid"]),ctxid)
			del(recdict["recid"])
		except:
			rec = ts.db.newrecord(recdict["rectype"],ctxid)

		for i in recdict.keys():
			rec[i] = recdict[i]
												
		r=ts.db.putrecord(rec,ctxid)
		return r

	def xmlrpc_addparamchoice(self,paramdefname,choice,host=None):
		"""This will add a choice to ParamDefs of vartype 'string'"""
		ts.db.addparamchoice(paramdefname,choice)
			
	def xmlrpc_addparamdef(self,paramdef,ctxid=None,host=None,parent=None):
		"""Puts a new ParamDef in the database. User must have permission to add records."""
		r=ts.DB.ParamDef()
		r.__dict__.update(paramdef)
		ts.db.addparamdef(r,ctxid,host,parent)
	
	def xmlrpc_getparamdef(self,paramdefname,host=None):
		"""Anyone may retrieve any paramdef"""
		return tuple(ts.db.getparamdef(paramdefname).__dict__.items())
		
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
		r=ts.DB.RecordDef(rectype)
		return tuple(ts.db.addrecorddef(r,ctxid,parent))
			
	def xmlrpc_getrecorddef(self,rectypename,ctxid=None,host=None,recid=None):
		"""Most RecordDefs are generally accessible. Some may be declared private in
		which case they may only be accessed by the user or by someone with permission
		to access a record of that type"""
		r = ts.db.getrecorddef(rectypename,ctxid,host=host,recid=recid).__dict__.items()
		return r
					
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
		children = list(ts.db.getchildren(key,keytype,recurse=0,ctxid=ctxid,host=host))
		children.sort()
		return tuple(children)
	
	def xmlrpc_countchildren(self,key,recurse=0,ctxid=None,host=None):
		"""Unlike getchildren, this works only for 'records'. Returns a count of children
		of the specified record classified by recorddef as a dictionary. The special "all"
		key contains the sum of all different recorddefs"""
		return ts.db.countchildren(key,recurse=0,ctxid=ctxid,host=host)

	def xmlrpc_getparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		"""Gets the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		return tuple(ts.db.getparents(key,keytype,recurse,ctxid,host))
	
	def xmlrpc_getcousins(self,key,keytype="record",ctxid=None,host=None):
		"""Gets the cousins (related records with no defined parent/child relationship
		 of a record with the given key, keytype may be 'record', 'recorddef' or 'paramdef' """
		return tuple(ts.db.getcousins(key,keytype,ctxid,host))
		
	def xmlrpc_pclink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		"""Produce a parent <-> child link between two records"""
		print "linking parent %s to child %s"%(pkey,ckey)
		return ts.db.pclink(pkey,ckey,keytype,ctxid,host)
		
	def xmlrpc_pcunlink(self,pkey,ckey,keytype="record",ctxid=None,host=None):
		"""Remove a parent <-> child link. No error raised if link doesn't exist."""
		print "UNlinking parent %s to child %s"%(pkey,ckey)
		return ts.db.pcunlink(pkey,ckey,keytype,ctxid,host)

	def xmlrpc_link(self,key1,key2,keytype="record",ctxid=None,host=None):
		"""Generate a 'cousin' relationship between two records"""
		return ts.db.link(key1,key2,keytype,ctxid,host)
		
	def xmlrpc_unlink(self,key1,key2,keytype="record",ctxid=None,host=None):
		"""Remove a 'cousin' relationship."""
		return ts.db.unlink(key1,key2,keytype,ctxid,host)
	
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
	
	def xmlrpc_putrecorddef(self,recdict,ctxid=None,host=None):
		recdef = ts.DB.RecordDef(recdict)
		return ts.db.putrecorddef(recdef,ctxid,host)

	def xmlrpc_getrecordnames(self,ctxid,dbid=0,host=None):
		return ts.db.getrecordnames(ctxid,dbid,host)
	
	def xmlrpc_getrecordschangetime(self,recids,ctxid=None,host=None):
		return ts.db.getrecordschangetime(recids,ctxid,host)
	
	def xmlrpc_secrecordadduser(self,usertuple,recid,ctxid=None,recurse=0,host=None):
		print "recurse: %s"%recurse
		ts.db.secrecordadduser(usertuple,int(recid),ctxid,host,recurse)
		return ""
	
	def xmlrpc_secrecorddeluser(self,users,recid,ctxid=None,recurse=0,host=None):
		print "users: %s"%users
		print "recid: %s"%recid
		ts.db.secrecorddeluser(users,recid,ctxid,host,recurse)
		return ""
		
		
		
###################################################################
# Convenience functions (not direct map to db methods)
		
	
	def xmlrpc_echo(self,args):
		for i in args:
			print i
		return args
	
	def xmlrpc_error(self):
		raise KeyError
		return ""
	
	def xmlrpc_sleep(self):
		time.sleep(100)
		return ""
	
	def xmlrpc_ping(self):
		return "pong"

	def xmlrpc_test(self):
		a=ts.DB.WorkFlow()
		b=ts.DB.WorkFlow()
		c=(a,b)
		d=[dict(x.__dict__) for x in c]
		
		return {"a":None,"b":None}		
		
		
	def xmlrpc_checktile(self,bid,ctxid=None,host=None):
		from emen2.TwistSupport_html.html.tileimage import get_tile, get_tile_dim

		bname,ipath,bdocounter=ts.db.getbinary(bid,ctxid)
		fpath=ipath+".tile"

		if not os.access(fpath,os.R_OK):
			return (-1,-1,bid)
		else:
			dims=get_tile_dim(fpath)
			dimsx=[i[0] for i in dims]
			dimsy=[i[1] for i in dims]
			return (dimsx,dimsy,bid) 
#			init="tileinit(%s,%s,'%s');"%(str(dimsx),str(dimsy),bid)
#		except Exception, inst:
#			args["notify"][0] = "%s*Error getting binary data for %s: %s"%(args["notify"][0],rec["file_binary_image"], inst)	
		
		
	def xmlrpc_createtile(self,bid,ctxid=None,host=None):
		bname,ipath,bdocounter=ts.db.getbinary(bid,ctxid)
		fpath=ipath+".tile"
		print "Generating tile... %s"%(ipath) 
		result = os.system("export PYTHONPATH=/home/EMAN2/lib;export LD_LIBRARY_PATH=/home/EMAN2/lib;cd /tmp;/home/emen2/copydata/e2tilefile.py %s --build=%s --buildpspec --decompress=%s"%(fpath,ipath,bname))
		return (1,)
			
		
	def xmlrpc_addcomment(self,recid,comment,ctxid=None,host=None):
		"""Append comment to record."""
		rec = ts.db.getrecord(recid,ctxid=ctxid)
		rec["comments"] = comment
		return ts.db.putrecord(rec,ctxid)
				
		
		
	def xmlrpc_getproto(self,classtype,ctxid=None,host=None):
		"""This will generate a 'dummy' record to fill in for a particular classtype.
		classtype may be: user,paramdef,recorddef,workflow or the name of a valid recorddef"""
		if	 (classtype.lower()=="user") :
			r=ts.DB.User()
			return r.__dict__
		elif (classtype.lower()=="paramdef") :
			r=ts.DB.ParamDef()
			return r.__dict__
		elif (classtype.lower()=="recorddef") :
			r=ts.DB.RecordDef()
			return r.__dict__
		elif (classtype.lower()=="workflow") :
			r=ts.DB.Workflow()
			return r.__dict__
		else :
			r=ts.db.newrecord(classtype,ctxid,init=1)
			return r.items()		
		
		
		
	def xmlrpc_getchildrenofparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
		"""Gets the children of all the parents of a record with the given key, keytype may be 
		'record', 'recorddef' or 'paramdef' """
		a = list(ts.db.getparents(key,keytype,recurse=0,ctxid=ctxid,host=host))
		a.sort()
		b = []
		for i in a:
			children = list(ts.db.getchildren(i,keytype,recurse=0,ctxid=ctxid,host=host))
			children.sort()
			b.append([i,children])
		return b		
	
		
		
	def xmlrpc_findparamname(self,q,ctxid=None,host=None):
		if len(q) < 3: return []
		
		q = q.lower()
		ret = []
		for i in ts.db.getparamdefnames():
			z = ts.db.getparamdef(i)
			
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
