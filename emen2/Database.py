##############
# Database.py  Steve Ludtke  05/21/2004
##############

### TODO
# Database id's not supported yet


"""This module encapsulates an electronic notebook/oodb

Note that the database does have a security model, but it cannot be rigorously enforced at the python level.
That is, a programmer using this library will not be able to accidentally violate the security model, but
with sufficient intent and knowledge it is possible. To use the module securely it must be encapsulated
by another layer, say an xmlrpc server...
"""

from bsddb3 import db
from cPickle import dumps,loads
from sets import *
import os
import md5
import time

LOGSTRINGS = ["SECURITY", "CRITICAL","ERROR   ","WARNING ","INFO    ","DEBUG   "]

class SecurityError(Exception):
	"Exception for a security violation"

class FieldError(Exception):
	"Exception for problems with Field definitions"

def parsefieldstring(self,text):
	"""This will exctract XML 'field' tags from a block of text"""
	# This nasty regex will extract <aaa bbb=ccc>ddd</eee> blocks as [(aaa,bbb,ccc,ddd,eee),...]
	srch=re.findall("<([^> ]*) ([^=]*)=([^>]*)>([^<]*)</([^>]*)>" ,text)
	ret={}
	if not srch : return ret
	for t in srch:
		if (t[0].lower!="field" or t[1].lower!="name" or t[4]!="field" or " " in t[2].strip()) :continue
		ret[t[2].strip()]=t[3]
								

def format_string_obj(dict,keylist):
	"""prints a formatted version of an object's dictionary"""
	r=["{"]
	for k in keylist:
		if (k==None or len(k)==0) : r.append("\n")
		else:
			try:
				r.append("\n%s: %s"%(k,str(dict[k])))
			except:
				r.append("\n%s: None"%k)
	r.append(" }\n")
	return "".join(r)
						
class BTree:
	"""This class uses BerkeleyDB to create an object much like a persistent Python Dictionary,
	keys and data may be arbitrary pickleable types"""
	def __init__(self,name,file=None,dbenv=None,nelem=0):
		"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		name is required, and will also be used as a filename if none is
		specified"""
		global globalenv
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.open(file,name,db.DB_BTREE,db.DB_CREATE)
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)

	def rmvlist(self,key,item):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		a=self[key]
		a.remove(item)
		self[key]=a

	def addvlist(self,key,item):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		if (self.has_key(key)):
			self[key]=(self[key]+[item])
		else: self[key]=[item]

	def __del__(self):
		self.close()

	def close(self):
		self.bdb.close()

	def __len__(self):
		return len(self.bdb)

	def __setitem__(self,key,val):
		if (val==None) :
			self.__delitem__(key)
		else : self.bdb.put(dumps(key),dumps(val))

	def __getitem__(self,key):
		return loads(self.bdb.get(dumps(key)))

	def __delitem__(self,key):
		self.bdb.delete(dumps(key))

	def __contains__(self,key):
		return self.bdb.has_key(dumps(key))

	def keys(self):
		return map(lambda x:loads(x),self.bdb.keys())

	def values(self):
		return map(lambda x:loads(x),self.bdb.values())

	def items(self):
		return map(lambda x:(loads(x[0]),loads(x[1])),self.bdb.items())

	def has_key(self,key):
		return self.bdb.has_key(dumps(key))

	def get(self,key):
		return self[key]

	def update(self,dict):
		for i,j in dict.items(): self[i]=j

class FieldBTree:
	"""This is a specialized version of the BTree class. This version uses type-specific 
	keys, and supports efficient key range extraction. The referenced data is a python list
	of 32-bit integers with no repeats allowed. The purpose of this class is to act as an
	efficient index for records. Each FieldBTree will represent the global index for
	one Field within the database. Valid dey types are:
	"d" - integer keys
	"f" - float keys (64 bit)
	"s" - string keys
	"""
	def __init__(self,name,file=None,keytype="s",dbenv=None,nelem=0):
		global globalenv
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.index_open(file,keytype,name,db.DB_BTREE,db.DB_CREATE)
		self.keytype=keytype
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)

	def typekey(self,key) :
		if key==None : return None
		if self.keytype=="f" : return float(key)
		if self.keytype=="d" : return int(key)
		return str(key)
			
	def removeref(self,key,item):
		"""The keyed value must be a list of objects. 'item' will be removed from this list"""
		key=self.typekey(key)
		self.bdb.index_remove(key,item)
		
	def addref(self,key,item):
		"""The keyed value must be a list, and is created if nonexistant. 'item' is added to the list. """
		key=self.typekey(key)
		self.bdb.index_append(key,item)

	def __del__(self):
		self.close()

	def close(self):
		self.bdb.close()

	def __len__(self):
		return len(self.bdb)
#		if (self.len<0) : self.keyinit()
#		return self.len

	def __setitem__(self,key,val):
		key=self.typekey(key)
		if (val==None) :
			self.__delitem__(key)
		else : self.bdb.index_put(key,val)

	def __getitem__(self,key):
		key=self.typekey(key)
		return self.bdb.index_get(key)

	def __delitem__(self,key):
		key=self.typekey(key)
		self.bdb.delete(key)

	def __contains__(self,key):
		key=self.typekey(key)
		return self.bdb.index_has_key(key)

	def keys(self,mink=None,maxk=None):
		"""Returns a list of valid keys, mink and maxk allow specification of
		minimum and maximum key values to retrieve"""
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_keys(mink,maxk)

	def values(self,mink=None,maxk=None):
		"""Returns a single list containing the concatenation of the lists of,
		all of the individual keys in the mink to maxk range"""
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_values(mink,maxk)

	def items(self,mink=None,maxk=None):
		mink=self.typekey(mink)
		maxk=self.typekey(maxk)
		return self.bdb.index_items(mink,maxk)

	def has_key(self,key):
		key=self.typekey(key)
		return self.bdb.index_has_key(key)

	def get(self,key):
		key=self.typekey(key)
		return self[key]

	def update(self,dict):
		self.bdb.index_update(dict)

# vartypes is a dictionary of valid data type names keying a tuple
# with an indexing type and a validation/normalization
# function for each. Currently the validation functions are fairly stupid.
# some types aren't currently indexed, but should be eventually
valid_vartypes={
	"int":("d",lambda x:int(x)),			# 32-bit integer
	"longint":("d",lambda x:int(x)),		# not indexed properly this way
	"float":("f",lambda x:float(x)),		# double precision
	"longfloat":("f",lambda x:float(x)),	# arbitrary precision, limited index precision
	"string":("s",lambda x:str(x)),			# string from an enumerated list
	"text":(None,lambda x:str(x)),			# freeform text, not indexed yet
	"time":("s",lambda x:str(x)),			# HH:MM:SS
	"date":("s",lambda x:str(x)),			# yyyy/mm/dd
	"datetime":("s",lambda x:str(x)),		# yyyy/mm/dd HH:MM:SS
	"intlist":(None,lambda y:map(lambda x:int(x),y)),		# list of integers
	"floatlist":(None,lambda y:map(lambda x:float(x),y)),	# list of floats
	"stringlist":(None,lambda y:map(lambda x:str(x),y)),	# list of enumerated strings
	"url":(None,lambda x:str(x)),			# link to a generic url
	"hdf":(None,lambda x:str(x)),			# url points to an HDF file
	"image":(None,lambda x:str(x)),			# url points to a browser-compatible image
	"binary":lambda x:str(x),				# url points to an arbitrary binary
	"child":lambda y:map(lambda x:int(x),y),	# link to dbid/recid of a child record
	"link":lambda y:map(lambda x:int(x),y)		# lateral link to related record dbid/recid
}

# Valid physical property names
# this really ought to have a list of valid units for each property, and perhaps a conversion
# function of some sort
valid_properties = ["count","length","area","volume","mass","temperature","pH","voltage","current","resistance","inductance",
	"transmittance","absorbance","relative_humidity","velocity","momentum","force","energy","angular_momentum"]

				
class FieldType:
	"""This class defines an individual data Field that may be stored in a Record.
	Field definitions are related in a tree, with arbitrary lateral linkages for
	conceptual relationships. The relationships are handled externally by the
	Database object. Fields may only be modified by the administrator once
	created, and then, they should only be modified for clarification""" 
	def __init__(self,name=None,vartype=None,desc_short=None,desc_long=None,property=None,defaultunits=None):
		self.name=name					# This is the name used in XML files to refer to this field, lower case
		self.vartype=vartype			# Variable data type. List of valid types in the module global 'vartypes'
		self.desc_short=desc_short		# This is a very short description for use in forms
		self.desc_long=desc_long		# A complete description of the meaning of this variable
		self.property=property			# Physical property represented by this field, List in 'properties'
		self.defaultunits=defaultunits	# Default units (optional)
		self.creator=None				# original creator of the record
		self.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
										# creation date
		self.creationdb=None		# dbid where fieldtype originated

	def __str__(self):
		return format_string_obj(self.__dict__,["name","vartype","desc_short","desc_long","property","defaultunits","","creator","creationtime","creationdb"])
			
class RecordType:
	"""This class defines a prototype for Database Records. Each Record is a member of
	a RecordClass. This class contains the information giving meaning to the data Fields
	contained by the Record"""
	def __init__(self,dict=None):
		self.name=None				# the name of the current RecordType, somewhat redundant, since also stored as key for index in Database
		self.mainview=None			# an XML string defining the experiment with embedded fields
									# this is the primary definition of the contents of the record
		self.views={}				# Dictionary of additional (named) views for the record
		self.fields={comments:[]}				# A dictionary keyed by the names of all fields used in any of the views
									# values are the default value for the field.
									# this represents all fields that must be defined to have a complete
									# representation of the record. Note, however, that such completeness
									# is NOT REQUIRED to have a valid Record 
		self.private=0				# if this is 1, this RecordType may only be retrieved by its owner (which may be a group)
									# or by someone with read access to a record of this type
		self.owner=None				# The owner of this record
		self.creator=0				# original creator of the record
		self.creationtime=None		# creation date
		self.creationdb=None		# dbid where recordtype originated
		if (dict) : self.__dict__.update(dict)
		
	def __str__(self):
		return "{ name: %s\nmainview:\n%s\nviews: %s\nfields: %s\nprivate: %s\nowner: %s\ncreator: %s\ncreationtime: %s\ncreationdb: %s}\n"%(
			self.name,self.mainview,self.views,self.stringfields(),str(self.private),self.owner,self.creator,self.creationtime,self.creationdb)

	def stringfields(self):
		"""returns the fields for this recordtype as an indented printable string"""
		r=["{"]
		for k,v in self.fields.items():
			r.append("\n\t%s: %s"%(k,str(v)))
		return "".join(r)+" }\n"
		
class User:
	"""This defines a database user, note that group 0 membership is required to add new records.
Users are never deleted, only disabled, for historical logging purposes"""
	def __init__(self):
		self.username=None			# username for logging in, First character must be a letter.
		self.password=None			# sha hashed password
		self.groups=[]				# user group membership
									# magic groups are 0 = add new records, -1 = administrator, -2 = read-only administrator

		self.disabled=0             # if this is set, the user will be unable to login
		self.privacy=0				# 1 conceals personal information from anonymous users, 2 conceals personal information from all users
		self.creator=0				# administrator who approved record
		self.creationtime=None		# creation date
		
		self.name=(None,None,None)  # tuple first, middle, last
		self.institution=None
		self.department=None
		self.address=None			# May be a multi-line string
		self.city=None
		self.state=None
		self.zipcode=None
		self.country=None
		self.webpage=None			# URL
		self.email=None				# email address
		self.altemail=None			# alternate email
		self.phone=None				# non-validated string
		self.fax=None				#
		self.cellphone=None			#
			
	def __str__(self):
		return format_string_obj(self.__dict__,["username","groups","name","email","phone","fax","cellphone","webpage","",
			"institution","department","address","city","state","zipcode","country","","disabled","privacy","creator","creationtime"])

class Context:
	"""Defines a database context (like a session). After a user is authenticated
	a Context is created, and used for subsequent access."""
	def __init__(self,ctxid=None,db=None,user=None,groups=None,host=None,maxidle=1800):
		self.ctxid=ctxid			# unique context id
		self.db=db					# Points to Database object for this context
		self.user=user				# validated username
		self.groups=groups			# groups for this user
		self.host=host				# ip of validated host for this context
		self.time=time.time()		# last access time for this context
		self.maxidle=maxidle
	
	def __str__(self):
		return format_string_obj(self.__dict__,["ctxid","user","groups","time","maxidle"])
		
class WorkFlow:
	"""Defines a workflow object, ie - a task that the user must complete at
	some point in time. These are intended to be transitory objects, so they
	aren't implemented using the Record class. 
	Implementation of workflow behavior is largely up to the
	external application. This simply acts as a repository for tasks"""
	def __init__(self,with=None):
		if isinstance(with,dict) :
			self.__dict__.update(with)
		else:
			self.wftype=None			# a short string defining the task to complete. Applications
										# should select strings that are likely to be unique for
										# their own tasks
			self.desc=None				# A 1-line description of the task to complete
			self.longdesc=None			# an optional longer description of the task
			self.appdata=None			# application specific data used to implement the actual activity
			self.wfid=None				# unique workflow id number assigned by the database
			self.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		
	def __str__(self):
		return str(__dict__)
			
class Record:
	"""This class encapsulates a single database record. In a sense this is an instance
	of a particular RecordType, however, note that it is not required to have a value for
	every field described in the RecordType, though this will usually be the case.
	
	To modify the fields in a record use the normal obj[key]= or update() approaches. 
	Changes are not stored in the database until commit() is called. To examine fields, 
	use obj[key]. There are a few special keys, handled differently:
	owner,creator,creationtime,permissions,comments

	Record instances must ONLY be created by the Database class through retrieval or
	creation operations. self.context will store information about security and
	storage for the record.
	
	Mechanisms for changing existing fields are a bit complicated. In a sense, as in a 
	physical lab notebook, an original value can never be changed, only superceded. 
	All records have a 'magic' field called 'comments', which is an extensible array
	of text blocks with immutable entries. 'comments' entries can contain new field
	definitions, which will supercede the original definition as well as any previous
	comments. Changing a field will result in a new comment being automatically generated
	describing and logging the value change.
	
	From a database standpoint, this is rather odd behavior. Such tasks would generally be
	handled with an audit log of some sort. However, in this case, as an electronic
	representation of a Scientific lab notebook, it is absolutely necessary
	that all historical values are permanently preserved for any field, and there is no
	particular reason to store this information in a separate file. Generally speaking,
	such changes should be infrequent.
	
	Naturally, as with anything in Python, anyone with code-level access to the database
	can override this behavior by changing 'fields' directly rather than using
	the supplied access methods. There may be appropriate uses for this when constructing
	a new Record before committing changes back to the database.
	"""
	def __init__(self,dict=None,ctxid=None):
		"""Normally the record is created with no parameters, then setContext is called by the
		Database object. However, for initializing from a dictionary (ie - XMLRPC call, this
		may be done at initiailization time."""
		if (dict!=None and ctxid!=None):
			self.__dict__.update(dict)
			self.setContext(ctxid)
			return
		self.recid=None				# 32 bit integer recordid (within the current database)
		self.dbid=None				# dbid where this record resides (any other dbs have clones)
		self.rectype=""				# name of the RecordType represented by this Record
		self.__fields={comments:[]}	# a Dictionary containing field names associated with their data
		self.__ofields={}			# when a field value is changed, the original value is stored here
		self.__owner=None			# The owner of this record, may be a username or a group id
		self.__creator=0			# original creator of the record
		self.__creationtime=None	# creation date
		self.__permissions=((),(),())
									# permissions for read access, comment write access, and full write access
									# each element is a tuple of user names or group id's, if a -3 is present
									# this denotes access by any logged in user, if a -4 is present this
									# denotes anonymous record access
		self.__context=None			# Validated access context
		self.__ptest=[0,0,0,0]		# Results of security test performed when the context is set
									# correspond to, read,comment,write and owner permissions
										
	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		del odict['__context']
		del odict['__ptest']
		return odict
	
	def __setstate__(self,dict):
		"""restore unpickled values to defaults after unpickling"""
		self.__dict__.update(dict)	
		self.__context=None
		self.__ptest=[0,0,0,0]

	def setContext(self,ctx):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work"""
		self.__context__=ctx
		if self.__creator==0 :
			self.__owner=ctx.user
			self.__creator=ctx.user
			self.__creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
			self.__permissions=((),(),(ctx.user))
		
		# test for owner access in this context
		if (-1 in ctx.groups or ctx.user==self.owner or self.owner in ctx.groups) : self._ptest=[1,1,1,1]	
		else:
			# we use the sets module to do intersections in group membership
			# note that an empty Set tests false, so u1&p1 will be false if
			# there is no intersection between the 2 sets
			p1=Set(self.__permissions[0]+self.__permissions[1]+self.__permissions[2])
			p2=Set(self.__permissions[1]+self.__permissions[2])
			p3=Set(self.__permissions[2])
			u1=Set(ctx.groups+(-4))				# all users are permitted group -4 access
			
			if ctx.user!=None : u1.add(-3)		# all logged in users are permitted group -3 access
			
			# test for read permission in this context
			if (-2 in u1 or ctx.user in p1 or u1&p1) : self.__ptest[0]=1
	
			# test for comment write permission in this context
			if (ctx.user in p2 or u1&p2): self.__ptest[1]=1
						
			# test for general write permission in this context
			if (ctx.user in p3 or u1&p3) : self.__ptest[2]=1
		return self.__ptest
	
	def __str__(self):
		"A string representation of the record"
		ret=["%d (%s)\n"%(self.recid,self.rectype)]
		for i,j in self.__fields.items:
			ret.append("%12s:  %s\n"%(str(i),str(j)))
		return ret.join()
		
	def __getitem__(self,key):
		"""Behavior is to return None for undefined fields, None is also
		the default value for existant, but undefined fields, which will be
		treated identically"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid
				
		key=key.lower()
		if key=="owner" : return self.__owner
		if key=="creator" : return self.__creator
		if key=="creationtime" : return self.__creationtime
		if key=="permissions" : return self.__permissions
		if self.__fields.has_key(key) : return self.__fields[key]
		return None
	
	def __setitem__(self,key,value):
		"""This and 'update' are the primary mechanisms for modifying the fields in a record
		Changes are not written to the database until the commit() method is called!"""
		# comments may include embedded field values if the user has full write access
		key=key.strip()
		if (key=="comments") :
			if not isinstance(value,str): return		# if someone tries to update the comments tuple, we just ignore it
			if self.__ptest[1]:
				dict=parsefieldstring(value)	# find any embedded fields
				if len(dict)>0 and not self.__ptest[2] : 
					raise SecurityError,"Insufficient permission to modify field in comment for record %d"%self.recid
				
				self.__fields["comments"].append((self.__context.user,time.strftime("%Y/%m/%d %H:%M:%S"),value))	# store the comment string itself
				
				# now update the values of any embedded fields
				for i,j in dict.items():
					self.__realsetitem(i,j)
			else :
				raise SecurityError,"Insufficient permission to add comments to record %d"%self.recid
		elif (key=="owner") :
			if self.__owner==value: return
			if self.__ptest[3]: self.__owner=value
			else : raise SecurityError,"Only the administrator or the record owner can change the owner"
		elif (key=="creator" or key=="creationtime") :
			# nobody is allowed to do this
			if self.__creator==value or self.__creationtime==value: return 
			raise SecurityError,"Creation fields cannot be modified"
		elif (key=="permissions") :
			if self.__permissions==value: return
			if self.__ptest[2]:
				try:
					value=(tuple(value[0]),tuple(value[1]),tuple(value[2]))
					self.__permissions=value
				except:
					raise TypeError,"Permissions must be a 3-tuple of tuples"
			else: 
				raise SecurityError,"Write permission required to modify security %d"%self.recid
		else :
			if self.__fields[key]==value : return
			if not self.__ptest[2] : raise SecurityError,"No write permission for record %d"%self.recid
			if key in self.__fields  and self.__fields[key]!=None:
				self.__fields.comments.append((self.__context.user,time.strftime("%Y/%m/%d %H:%M:%S"),"<field name=%s>%s</field>"%(str(key),str(value))))
			__realsetitem(key,value)
	
	def __realsetitem(self,key,value):
			"""This insures that copies of original values are made when appropriate
			security should be handled by the parent method"""
			if key in self.__fields and self.__fields[key]!=None and not key in self.__ofields : self.__ofields[key]=self.__fields[key]
			self.__fields[key]=value
									

	def update(self,dict):
		"""due to the processing required, it's best just to implement this as
		a sequence of calls to the existing setitem method"""
		for i,j in dict.items(): self[i]=j
	
	def keys(self):
		"""All retrievable keys for this record"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid		
		return tuple(self.__fields.keys())+("owner","creator","creationdate","permissions")
		
	def items(self):
		"""Key/value pairs"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid		
		ret=self.__fields.items()
		try:
			ret+=[(i,self[i]) for i in ("owner","creator","creationdate","permissions")]
		except:
			pass
		return ret
			
	def has_key(self,key):
		if key in self.keys() or key in ("owner","creator","creationdate","permissions"): return True
		return False

	def commit(self,host=None):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putRecord will fail"""
		self.__context.db.putRecord(self,self.__context.ctxid,host)
	
#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()	
class Database:
	"""This class represents the database as a whole. There are 3 primary identifiers used in the database:
	dbid - Database id, a unique identifier for this database server
	recid - Record id, a unique (32 bit int) identifier for a particular record
	ctxid - A key for a database 'context' (also called a session), allows access for pre-authenticated user
	
	TODO : Probably should make more of the member variables private for slightly better security"""
	def __init__(self,path=".",cachesize=256000000,logfile="db.log"):
		self.path=path
		self.logfile=path+"/"+logfile
		self.lastctxclean=time.time()
	
			
		self.__contexts={}			# dictionary of current db contexts, may need to put this on disk for mulithreaded server ?
					
		# This sets up a DB environment, which allows multithreaded access, transactions, etc.
		if not os.access(path+"/home",os.F_OK) : os.makedirs(path+"/home")
		self.LOG(4,"Database initialization started")
		self.dbenv=db.DBEnv()
		self.dbenv.set_cachesize(0,cachesize,4)		# gbytes, bytes, ncache (splits into groups)
		self.dbenv.set_data_dir(path)
		self.dbenv.open(path+"/home",db.DB_CREATE+db.DB_INIT_MPOOL)
		
		if not os.access(path+"/security",os.F_OK) : os.makedirs(path+"/security")
		if not os.access(path+"/index",os.F_OK) : os.makedirs(path+"/index")
		
		# Users
		self.users=BTree("users",path+"/security/users.bdb",dbenv=self.dbenv)						# active database users
		self.newuserqueue=BTree("newusers",path+"/security/newusers.bdb",dbenv=self.dbenv)			# new users pending approval
	
		# Defined FieldTypes
		self.fieldtypes=BTree("FieldTypes",path+"/FieldTypes.bdb",dbenv=self.dbenv)						# FieldType objects indexed by name

		# Defined RecordTypes
		self.recordtypes=BTree("RecordTypes",path+"/RecordTypes.bdb",dbenv=self.dbenv)					# RecordType objects indexed by name
					
		# The actual database, keyed by recid, a positive integer unique in this DB instance
		# 2 special keys exist, the record counter is stored with key -1
		# and database information is stored with key=0
		self.records=BTree("database",path+"/database.bdb",dbenv=self.dbenv)						# The actual database, containing id referenced Records
		try:
			max=self.records[-1]
		except:
			self.records[-1]=0
			self.LOG(3,"New database created")
		
		# Indices
		self.secrindex=FieldBTree("secrindex",path+"/security/roindex.bdb","s",dbenv=self.dbenv)	# index of records each user can read
		self.recordtypeindex=FieldBTree("RecordTypeindex",path+"/RecordTypeindex.bdb","s",dbenv=self.dbenv)		# index of records belonging to each RecordType
		self.fieldindex={}				# dictionary of FieldBTrees, 1 per FieldType, not opened until needed

		# The mirror database for storing offsite records
		self.records=BTree("mirrordatabase",path+"/mirrordatabase.bdb",dbenv=self.dbenv)			# The actual database, containing (dbid,recid) referenced Records

		# Workflow database, user indexed btree of lists of things to do
		# again, key -1 is used to store the wfid counter
		self.workflow=BTree("workflow",path+"/workflow.bdb",dbenv=self.dbenv)
		try:
			max=self.workflow[-1]
		except:
			self.workflow[-1]=1
			self.LOG(3,"New workflow database created")
					
		self.LOG(4,"Database initialized")

		# Create an initial administrative user for the database
		self.LOG(0,"Warning, root user recreated")
		u=User()
		u.username="root"
		p=md5.new("foobar")
		u.password=p.hexdigest()
		u.groups=[-1]
		u.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		u.name=('Database','','Administrator')
		self.users["root"]=u
	
	def LOG(self,level,message):
		"""level is an integer describing the seriousness of the error:
		0 - security, security-related messages
		1 - critical, likely to cause a crash
		2 - serious, user will experience problem
		3 - minor, likely to cause minor annoyances
		4 - info, informational only
		5 - verbose, verbose logging """
		global LOGSTRINGS
		if (level<0 or level>5) : level=0
		try:
			o=file(self.logfile,"a")
			o.write("%s: (%s)  %s\n"%(time.strftime("%Y/%m/%d %H:%M:%S"),LOGSTRINGS[level],message))
			o.close()
		except:
			print("Critical error!!! Cannot write log message to '%s'\n"%self.logfile)

	def __str__(self):
		"""try to print something useful"""
		return "Database ( %s )"%format_string_obj(self.__dict__,["path","logfile","lastctxclean"])

	def login(self,username="anonymous",password="",host=None,maxidle=1800):
		"""Logs a given user in to the database and returns a ctxid, which can then be used for
		subsequent access"""
		ctx=None
		
		# anonymous user
		if (username=="anonymous" or username=="") :
			ctx=Context(None,self,None,(),host,maxidle)
		
		# check password, hashed with md5 encryption
		else :
			s=md5.new(password)
			user=self.users[username]
			if user.disabled : raise SecurityError,"User %s has been disabled. Please contact the administrator."
			if (s.hexdigest()==user.password) : ctx=Context(None,self,username,user.groups,host,maxidle)
			else:
				self.LOG(0,"Invalid password: %s (%s)"%(username,host))
				raise ValueError,"Invalid Password"
		
		# This shouldn't happen
		if ctx==None :
			self.LOG(1,"System ERROR, login(): %s (%s)"%(username,host))
			raise Exception,"System ERROR, login()"
		
		# we use md5 to make a key for the context as well
		s=md5.new(username+str(host)+str(time.time()))
		ctx.ctxid=s.hexdigest()
		self.__contexts[ctx.ctxid]=ctx
		self.LOG(4,"Login succeeded %s (%s)"%(username,ctx.ctxid))
		
		return ctx.ctxid

	def cleanupcontexts(self):
		"""This should be run periodically to clean up sessions that have been idle too long"""
		self.lastctxclean=time.time()
		for k in self.__contexts.items():
			if k[1].time+k[1].maxidle<time.time() : 
				self.LOG(4,"Expire context (%s) %d"%(k[1].ctxid,time.time()-k[1].time))
				del self.__contexts[k[0]]
		
	def __getcontext(self,key,host):
		"""Takes a key and returns a context (for internal use only)
		Note that both key and host must match."""
		if (time.time()>self.lastctxclean+30):
			self.cleanupcontexts()		# maybe not the perfect place to do this, but it will have to do
		
		try:
			ctx=self.__contexts[key]
		except:
			self.LOG(4,"Session expired")
			raise KeyError,"Session expired"
			
		if host!=ctx.host :
			self.LOG(0,"Hacker alert! Attempt to spoof context (%s != %s)"%(host,ctx.host))
			raise Exception,"Bad address match, login sessions cannot be shared"
		
		return ctx			

	def checkcontext(self,ctxid,host):
		a=self.__getcontext(ctxid,host)
		
	def disableuser(self,username,ctxid,host=None):
		"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
		a complete historical record is maintained. Only an administrator can do this."""
		ctx=self.__getcontext(ctxid,host)
		if not -1 in ctx.groups :
			raise SecurityError,"Only administrators can disable users"

		if username==ctx.user : raise SecurityError,"Even administrators cannot disable themselves"
			
		user=self.users[username]
		user.disabled=1
		self.users[username]=user
		self.LOG(0,"User %s disabled by %s"%(username,ctx.user))

		        
	def approveuser(self,username,ctxid,host=None):
		"""Only an administrator can do this, and the user must be in the queue for approval"""
		ctx=self.__getcontext(ctxid,host)
		if not -1 in ctx.groups :
			raise SecurityError,"Only administrators can approve new users"
		
		if not username in self.newuserqueue :
			raise KeyError,"User %s is not pending approval"%username
			
		if username in self.users :
			self.newuserqueue[username]=None
			raise KeyError,"User %s already exists, deleted pending record"%username

		self.users[username]=self.newuserqueue[username]
		self.newuserqueue[username]=None
	
	def adduser(self,user):
		"""adds a new user record. However, note that this only adds the record to the
		new user queue, which must be processed by an administrator before the record
		becomes active. This system prevents problems with securely assigning passwords
		and errors with data entry. Anyone can create one of these"""
		if user.username==None or len(user.username)<3 : 
			raise KeyError,"Attempt to add user with invalid name"
		
		if user.username in self.users :
			raise KeyError,"User with username %s already exists"%user.username
		
		if user.username in self.newuserqueue :
			raise KeyError,"User with username %s already pending approval"%user.username
		
		if len(user.password)<5 :
			raise SecurityError,"Passwords must be at least 5 characters long"
		
		if len(user.password)!=32 :
			s=md5.new(user.password)
			user.password=s.hexdigest()

		user.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		self.newuserqueue[user.username]=user
		
		
	def getuser(self,username,ctxid,host=None):
		"""retrieves a user's information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record"""
		
		ret=self.users[username]
		
		ctx=self.__getcontext(ctxid,host)
		
		# The user him/herself or administrator can get all info
		if (-1 in ctx.groups) or (-2 in ctx.groups) or (ctx.user==username) : return ret
		
		# if the user has requested privacy, we return only basic info
		if (user.privacy==1 and ctx.user==None) or user.privacy>=2 :
			ret2=User()
			ret2.username=ret.username
			ret2.privacy=ret.privacy
			ret2.name=ret.name
			return ret2

		ret.password=None		# the hashed password has limited access
		
		# Anonymous users cannot use this to extract email addresses
		if ctx.user==None : 
			ret.groups=None
			ret.email=None
			ret.altemail=None
		
		return ret
		
	def getusernames(self,ctxid,host=None):
		"""Not clear if this is a security risk, but anyone can get a list of usernames
			This is likely needed for inter-database communications"""
		return self.users.keys()

	def getworkflow(self,ctxid,host=None):
		"""This will return an (ordered) list of workflow objects for the given context (user).
		it is an exceptionally bad idea to change a WorkFlow object's wfid."""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
		
		try:
			return self.workflow[ctx.user]
		except:
			return []

	def addworkflowitem(self,work,ctxid,host=None) :
		"""This appends a new workflow object to the user's list. wfid will be assigned by this function"""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"

		if not isinstance(work,WorkFlow) : raise TypeError,"Only WorkFlow objects can be added to a user's workflow"
		
		work.wfid=self.workflow[-1]
		self.workflow[-1]=work.wfid+1
		
		if self.workflow.has_key(ctx.user) :
			wf=self.workflow[ctx.user]
			wf.append(work)
			self.workflow[ctx.user]=wf
	
	def delworkflowitem(self,wfid,ctxid,host=None) :
		"""This will remove a single workflow object"""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
		
		wf=self.workflow[ctx.user]
		for i,w in enumerate(wf):
			if w.wfid==wfid :
				del wf[i]
				break
		else: raise KeyError,"Unknown workflow id"
		
		self.workflow[ctx.user]=wf
		
		
	def setworkflow(self,wflist,ctxid,host=None) :
		"""This allows an authorized user to directly modify or clear his/her workflow. Note that
		the external application should NEVER modify the wfid of the individual WorkFlow records.
		Any wfid's that are None will be assigned new values in this call."""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
		
		if wflist==None : wflist=[]
		wflist=list(wflist)				# this will (properly) raise an exception if wflist cannot be converted to a list
		
		for w in wflist:
			if not isinstance(w,WorkFlow): raise TypeError,"Only WorkFlow objects may be in the user's workflow"
			if w.wfid==None: 
				w.wfid=self.workflow[-1]
				self.workflow[-1]=w.wfid+1
		
		self.workflow[ctx.user]=wflist
	
	def getvartypenames(self):
		"""This returns a list of all valid variable types in the database. This is currently a
		fixed list"""
		return valid_vartypes.keys()

	def getpropertynames(self):
		"""This returns a list of all valid property types in the database. This is currently a
		fixed list"""
		return valid_properties
		
	def addfieldtype(self,fieldtype,ctxid,host=None):
		"""adds a new FieldType object, group 0 permission is required"""
		if not isinstance(fieldtype,FieldType) : raise TypeError,"addfieldtype requires a FieldType object"
		ctx=self.__getcontext(ctxid,host)
		if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create new fieldtypes (need record creation permission)"
		if self.fieldtypes.has_key(fieldtype.name) : raise KeyError,"fieldtype %s already exists"%fieldtype.name
		
		# force these values
		fieldtype.creator=ctx.user
		fieldtype.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		
		# this actually stores in the database
		self.fieldtypes[fieldtype.name]=fieldtype
		
		
	def getfieldtype(self,fieldtypename):
		"""gets an existing FieldType object, anyone can get any field definition"""
		return self.fieldtypes[fieldtypename]
		
	def getfieldtypenames(self):
		"""Returns a list of all FieldType names"""
		return self.fieldtypes.keys()
		
	def addrecordtype(self,rectype,ctxid,host=None):
		"""adds a new RecordType object. The user must be an administrator or a member of group 0"""
		if not isinstance(rectype,RecordType) : raise TypeError,"addRecordType requires a RecordType object"
		ctx=self.__getcontext(ctxid,host)
		if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create new RecordTypes"
		if self.recordtypes.has_key(rectype.name) : raise KeyError,"RecordType %s already exists"%rectype.name
		
		# force these values
		if (rectype.owner==None) : rectype.owner=ctx.user
		rectype.creator=ctx.user
		rectype.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		
		# this actually stores in the database
		self.recordtypes[rectype.name]=rectype
		
		
	def getrecordtype(self,rectypename,ctxid,host=None,recid=None):
		"""Retrieves a RecordType object. This will fail if the RecordType is
		private, unless the user is an owner or  in the context of a recid the
		user has permission to access"""
		ctx=self.__getcontext(ctxid,host)
		if not self.recordtypes.has_key(rectypename) : raise KeyError,"No such RecordType %s"%rectypename
		
		ret=self.recordtypes[rectypename]	# get the record
		
		# if the RecordType isn't private or if the owner is asking, just return it now
		if not ret.private or (ret.private and (ret.owner==ctx.user or ret.owner in ctx.groups)) : return ret

		# ok, now we need to do a little more work. 
		if recid==None: raise SecurityError,"User doesn't have permission to access private RecordType '%s'"%rectypename
		
		rec=self.getrecord(recid)		# try to get the record, may (and should sometimes) raise an exception

		if rec.rectype!=rectypename: raise SecurityError,"Record %d doesn't belong to RecordType %s"%(recid,rectypename)

		# success, the user has permission
		return ret
	
	def getrecordtypenames(self):
		"""This will retrieve a list of all existing FieldType names, even
		those the user cannot access the contents of"""
		return self.recordtypes.keys()
		
	def reindex(self,key,oldval,newval,recid):
		"""This function reindexes a single key/value pair
		This includes creating any missing indices if necessary"""

		if (oldval==newval) : return
		try:
			ind=self.fieldindex[key]		# Try to get the index for this key
		except:
			# index not open yet, open/create it
			try:
				f=self.FieldType[key]		# Look up the definition of this field
			except:
				# Undefined field, we can't create it, since we don't know the type
				raise FieldError,"No such field %s defined"%key
			tp=valid_vartypes[f.vartype][0]
			if not tp : return			# if this is None, then this is an 'unindexable' field
			
			# create/open index
			self.fieldindex[key]=FieldBTree(key,"%s/index/%s.bdb"%(self.path,key),tp,self.dbenv)
			ind=self.fieldindex[key]
		
		# remove the old ref and add the new one
		if oldval!=None : ind.removeref(oldval,recid)
		if newval!=None : ind.addref(newval,recid)

	def reindexsec(self,oldlist,newlist,recid):
		"""This updates the security (read-only) index
		takes two lists of userid/groups (may be None)"""
		o=Set(oldlist)
		n=Set(newlist)
		
		uo=o-n	# unique elements in the 'old' list
		un=n-o	# unique elements in the 'new' list

		# anying in both old and new should be ok,
		# So, we remove the index entries for all of the elements in 'old', but not 'new'
		for i in uo:
			self.secrindex.removeref(i,recid)

		# then we add the index entries for all of the elements in 'new', but not 'old'
		for i in un:
			self.secrindex.addred(i,recid)
												
	def putrecord(self,record,ctxid,host=None):
		"""The record has everything we need to commit the data. However, to 
		update the indices, we need the original record as well. This also provides
		an opportunity for double-checking security vs. the original. If the 
		record is new, recid should be set to None. recid is returned upon success"""
		ctx=self.__getcontext(ctxid,host)
		
		if isinstance(record,dict) :
			r=record
			record=Record(r,ctxid)
				
		if (record.recid<0) : record.recid=None
		
		try:
			orig=self.records[record.recid]		# get the unmodified record
		except:
			# Record must not exist, lets create it
			#p=record.setContext(ctx)

			record.recid=self.records[-1]+1				# Get a new record-id
			self.records[-1]=record.recid				# Update the recid counter, TODO: do the update more safely/exclusive access
			
			# Group -1 is administrator, group 0 membership is global permission to create new records
			if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create records"
			
			# index fields
			for k,v in record.items():
				self.reindex(k,None,v,record.recid)
			
			self.reindexsec(None,record["security"],record.recid)		# index security
			self.recordtypeindex.addref(record.rectype,record.recid)	# index recordtype
			
			self.records[record.recid]=record		# This actually stores the record in the database
			return record.recid
				
		p=orig.setContext(ctx)				# security check on the original record
		
		# Ok, to efficiently update the indices, we need to figure out what changed
		fields=Set(orig.keys()).union_update(record.keys())		# list of all fields (old and new)
		changedfields=[]
		for f in fields:
			try:
				if (orig[f]!=record[f]) : changedfields.append(f)
			except:
				changedfields.append(f)
		
		# make sure the user has permission to modify the record
		if not p[2] :
			if not p[1] : raise SecurityError,"No permission to modify record %d"%record.recid
			if len(changedfields>1) or changedfields[0]!="comments" : raise SecurityError,"Insufficient permission to change field values on record %d"%record.recid
		
		# Now update the indices
		for f in changedfields:
			# reindex will accept None as oldval or newval
			try:    oldval=orig[f]
			except: oldval=None
			
			try:    newval=record[f]
			except: newval=None

			self.reindex(f,oldval,newval,record.recid)

		self.records[record.recid]=record		# This actually stores the record in the database
		return record.recid
		
	def newrecord(self,rectype,ctxid,host=None,init=0):
		"""This will create an empty record and (optionally) initialize it for a given RecordType (which must
		already exist)."""
		ret=Record()
		
		# try to get the RecordType entry, this still may fail even if it exists, if the
		# RecordType is private and the context doesn't permit access
		t=self.getrecordtype(rectype,ctxid,host)	

		ret.recid=None
		ret.rectype=rectype						# if we found it, go ahead and set up
				
		if init:
			for k,v in t.fields.items():
				ret[k]=v						# hmm, in the new scheme, perhaps this should just be a deep copy
		
		return ret
		
	def getrecord(self,recid,ctxid,dbid=0,host=None) :
		"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
		if dbid is 0, the current database is used. host must match the host of the
		context"""
		
		ctx=self.__getcontext(ctxid,host)
		
		if (dbid!=0) : raise Exception,"External database support not yet available"
		
		# if a single id was requested, return it
		# setContext is required to make the record valid, and returns a binary security tuple
		if (isinstance(recid,int)):
			rec=self.records[recid]
			p=rec.setContext(ctx)
			if p[0] : return rec
			raise Exception,"No permission to access record"
		elif (isinstance(recid,list)):
			rec=map(lambda x:self.records[x],recid)
			for r in rec:
				p=rec.setContext(ctx)
				if not p[0] : raise Exception,"No permission to access one or more records"	
			return rec
		else : raise KeyError,"Invalid Key"
		
	def getrecordsafe(self,recid,ctxid,dbid=0,host=None) :
		"""Same as getRecord, but failure will produce None or a filtered list"""
		
		ctx=self.__getcontext(ctxid,host)
		
		if (dbid!=0) : return None
		
		if (isinstance(recid,int)):
			try:
				rec=self.records[recid]
			except: 
				return None
			p=rec.setContext(ctx)
			if p[0] : return rec
			return None
		elif (isinstance(recid,list)):
			try:
				rec=map(lambda x:self.records[x],recid)
			except: 
				return None
			rec=filter(lambda x:x.setContext(ctx)[0],rec)
			return rec
		else : return None
	
	
