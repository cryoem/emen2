##############
# Database.py  Steve Ludtke  05/21/2004
##############

"""This module encapsulates an electronic notebook/oodb

Note that the database does have a security model, but it cannot be rigorously enforced at the python level.
That is, a programmer using this library will not be able to accidentally violate the security model, but
with sufficient intent and knowledge it is possible. To use the module securely it must be encapsulated
by another layer, say an xmlrpc server...
"""

from bsddb3 import db
from cPickle import dumps,loads
import md5

LOGSTRINGS = ["SECURITY", "CRITICAL","ERROR   ","WARNING ","INFO    ","DEBUG   "]

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
		return self.bdb.has_key(key)

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
		for i in dict.items():
			self[i[0]]=i[1]

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
	Database object.""" 
	def __init__(self):
		self.name=None				# This is the name used in XML files to refer to this field, lower case
		self.vartype=None			# Variable data type. List of valid types in the module global 'vartypes'
		self.desc_short=None		# This is a very short description for use in forms
		self.desc_long=None			# A complete description of the meaning of this variable
		self.property=None			# Physical property represented by this field, List in 'properties'
		self.defaultunits=None		# Default units (optional)
#		self.needsupdate=0			# flag indicating a field that has an incomplete definition
	
class RecordType:
	"""This class defines a prototype for Database Records. Each Record is a member of
	a RecordClass. This class contains the information giving meaning to the data Fields
	contained by the Record"""
	def __init__(self):
		self.name=None				# the name of the current RecordDef, somewhat redundant, since also stored as key for index in Database
		self.mainview=None			# an XML string defining the experiment with embedded fields
									# this is the primary definition of the contents of the record
		self.views={}				# Dictionary of additional (named) views for the record
		self.fields=[]				# A list containing the names of all fields used in any of the views
									# this represents all fields that must be defined to have a complete
									# representation of the record. Note, however, that such completeness
									# is NOT REQUIRED to have a valid Record 

class User:
	"""This defines a database user"""
	def __init__(self):
		self.username=None			# username for logging in, First character must be a letter.
		self.password=None			# sha hashed password
		self.groups=[]				# user group membership
									# magic groups are -1 = administrator, -2 = read-only administrator
		self.name=None				# tuple first, last, middle
		self.email=None				# email address
		self.altemail=None			# alternate email
		self.phone=None				# non-validated string
		self.fax=None				#
		self.cellphone=None			#
			

									
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
		
class Record:
	"""This class encapsulates a single database record. In a sense this is an instance
	of a particular RecordType, however, note that it is not required to have a value for
	every field described in the RecordType, though this will usually be the case.

	Record instances must ONLY be created by the Database class through retrieval or
	creation operations. self.context will store information about security and
	storage for the record.
	
	fields are accessed/modified as if this were a dictionary, ie rec["temperature"]=23.5
		
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
	can easily override this behavior by changing 'fields' directly rather than using
	the supplied access methods. There may be appropriate uses for this when constructing
	a new Record before committing changes back to the database.
	"""
	def __init__(self):
		"""Record must be created with a context. This should only be done directly
		by a Database object, to insure security and protocols are handled correctly"""
		self.recid=None				# 32 bit integer recordid (within the current database)
		self.rectype=""				# string of the RecordType represented by this Record
		self.fields={comments:[]}				# a Dictionary containing field names associated with their data
		self.ofields={}				# when a field value is changed, the original value is stored here
		self.__owner=0				# The owner of this record
		self.__creator=0			# original creator of the record
		self.__creationtime=None	# creation date
		self.__permissions=[(),(),()]
									# permissions for read access, comment write access, and full write access
		self.__context=None			# Record objects are only 
	
	def setContext(self,ctx):
		"""This method may ONLY be used by the Database class. Constructing your
		own context will not work"""
		self.__context__=ctx
		if self.__creator==0 :
			self.__creator=ctx.user
			self.__creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
						
	def __str__(self):
		ret=["%d (%s)\n"%(self.recid,self.rectype)]
		for i in fields
		
	def __getitem__(self,key):
		"""Behavior is to return None for undefined fields, None is also
		the default value for existant, but undefined fields, which will be
		treated identically"""
		if not (self.__context.user in self.__permissions[0]+self.__permissions[1]+self.__permissions[2]) : raise Exception,"No Permission"
				
		key=key.lower()
		if key=="owner" : return self.__owner
		if key=="creator" : return self.__creator
		if key=="creationtime" : return self.__creationtime
		if key=="permissions" : return self.__permissions
		if self.fields.has_key(key) : return self.fields[key]
		return None
	
	def __setitem__(self,key,value):
		if (key=="comments") :
			if self.__context.user in self.__permissions[1]+self.__permissions[2]:
				dict=self.parsestring(value)
				self.fields["comments"].append(value)
			else :
				raise Exception,"No Permission"
		if (key=="owner") :
			if -1 in __context.groups or __context.user==self.__owner:
				self.__owner=value
		if (key=="creator" or key=="creationtime") :
			raise Exception,"Creation info cannot be modified"
		if (key=="permissions") :
		if (self.fields.has_key(key) and self.fields[key]!=None) :
			self.fields["comments"].append("Field changed <...")
			
			self.fields[key]=value

		self.fields[key]=value		# if we got here, there was no previously assigned value for this field	
									# and it wasn't a special value

	def update(self,dict):
		
	
	def keys(self):
		return self.fields.keys()+["owner","creator","creationdate","permissions"]
	
	def has_key(self,key):
		if key in self.keys() : return True
		return False
	
	
	
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
		
			self.LOG(4,"Database initialization started")
				
			self.__contexts={}			# dictionary of current db contexts, may need to put this on disk for mulithreaded server ?
						
			# This sets up a DB environment, which allows multithreaded access, transactions, etc.
			self.dbenv=db.DBEnv()
			self.dbenv.set_cachesize(0,cachesize,4)		# gbytes, bytes, ncache (splits into groups)
			self.dbenv.set_data_dir(path)
			self.dbenv.open(path+"/home",db.DB_CREATE+db.DB_INIT_MPOOL)
			
			# security related items
			self.users=BTree("users",path+"/security/users.bdb",dbenv=self.dbenv)						# active database users
			self.newuserqueue=BTree("newusers",path+"/security/newusers.bdb",dbenv=self.dbenv)			# new users pending approval
			self.secrindex=FieldBTree("secrindex",path+"/security/roindex.bdb","s",dbenv=self.dbenv)	# index of records each user can read
			
			# Defined FieldTypes
			self.fieldtype=BTree("fieldtypes",path+"/fieldtypes.bdb",dbenv=self.dbenv)						# FieldType objects indexed by name

			# Defined RecordTypes
			self.recordtype=BTree("recordtypes",path+"/recordtypes.bdb",dbenv=self.dbenv)						# FieldType objects indexed by name
						
			# The actual database
			self.records=BTree("database",path+"/database.bdb",dbenv=self.dbenv)						# The actual database, containing id referenced Records
			self.recordtypes=FieldBTree("recordtypeindex",path+"/recordtypeindex.bdb","s",dbenv=self.dbenv)		# index of records belonging to each RecordType
			self.fieldindex={}				# dictionary of FieldBTrees, 1 per FieldType, not opened until needed

			# The mirror database for storing offsite records
			self.records=BTree("mirrordatabase",path+"/mirrordatabase.bdb",dbenv=self.dbenv)			# The actual database, containing (dbid,recid) referenced Records
			
			self.LOG(4,"Database initialized")
					
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
				o.write("%s: (%s)  %s\n"%(time.ctime(),LOGSTRINGS[level],message))
				o.close()
			except:
				print("Critical error!!! Cannot write log message\n")
										
		def login(self,username="anonymous",password="",host=None,maxidle=1800):
			"""Logs a given user in to the database and returns a ctxid, which can then be used for
			subsequent access"""
			ctx=None
			
			# anonymous user
			if (username=="anonymous" or username=="") :
				ctx=Context(self,"",[],host,maxidle)
			
			# check password, hashed with md5 encryption
			else :
				s=md5.new(password)
				user=self.users[username]
				if (s.hexdigest()==user.password) : ctx=Context(self,username,user.groups,host,maxidle)
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
			self.__contexts[s.hexdigest()]=ctx
			
			return s.hexdigest()

		def cleanupcontexts(self):
			"""This should be run periodically to clean up sessions that have been idle too long"""
			self.lastctxclean=time.time()
			for k in __contexts.items():
				if k[1].time+k[1].maxidle<time.time() : del __contexts[k[0]]
			
		def __getcontext(self,key,host):
			"""Takes a key and returns a context (for internal use only)
			Note that both key and host must match."""
			if (time.time()>self.lastctxclean+30):
				self.cleanupcontexts()		# maybe not the perfect place to do this, but it will have to do
			
			try:
				ctx=__contexts(key)
			except:
				self.LOG(4,"Session expired")
				raise KeyError,"Session expired"
				
			if host!=ctx.host :
				self.LOG(0,"Hacker alert! Attempt to spoof context (%s != %s)"%(host,ctx.host))
				raise Exception,"Bad address match, login sessions cannot be shared"
			
			return ctx			
			
		def getRecord(self,ctxid,recid,dbid=0) :
			"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
			if dbid is 0, the current database is used."""
			
			ctx=__getcontext(ctxid)
			
			if (dbid!=0) : raise Exception,"External database support not yet available"
			
			if (isinstance(recid,int)):
				rec=self.records[recid]
				if ctx.user in rec.permissions[0] : return rec
				raise Exception,"No permission to access record"
			elif (isinstance(recid,list)):
				rec=map(lambda x:self.records[x],recid)
				for r in rec:
					if not (ctx.user in r.permissions[0]) : raise Exception,"No permission to access one or more records"	
				return rec
			else : raise KeyError,"Invalid Key"
			
		def getRecordSafe(self,ctxid,recid,dbid=0) :
			"""Same as getRecord, but failure will produce None or a filtered list"""
			
			ctx=__getcontext(ctxid)
			
			if (dbid!=0) : return None
			
			if (isinstance(recid,int)):
				try:
					rec=self.records[recid]
				except: 
					return None
				if ctx.user in rec.permissions[0] : return rec
				return None
			elif (isinstance(recid,list)):
				try:
					rec=map(lambda x:self.records[x],recid)
				except: 
					return None
				rec=filter(lambda x:ctx.user in x.permissions[0],rec)
				return rec
			else : return None
			