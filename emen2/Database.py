##############
# Database.py  Steve Ludtke  05/21/2004
##############

"""This module encapsulates an electronic notebook/oodb

"""

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

# vartypes is a dictionary of valid data types and a validation/normalization
# function for each. Currently the validation functions are fairly stupid.
valid_vartypes={
	"int":lambda x:int(x),
	"longint":lambda x:int(x),
	"float":lambda x:float(x),
	"longfloat":lambda x:float(x),
	"string":lambda x:str(x),
	"text":lambda x:str(x),
	"time":lambda x:str(x),
	"date":lambda x:str(x),
	"datetime":lambda x:str(x),
	"intlist":lambda y:map(lambda x:int(x),y),
	"floatlist":lambda y:map(lambda x:float(x),y),
	"stringlist":lambda y:map(lambda x:str(x),y),
	"url":lambda x:str(x),
	"hdf":lambda x:str(x),
	"image":lambda x:str(x),
	"binary":lambda x:str(x),
	"child":lambda y:map(lambda x:int(x),y),
	"link":lambda y:map(lambda x:int(x),y)
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
		self.password=None			# hashed password (need to think this through)
		self.groups=[]				# user group membership
									# magic groups are -1 = administrator, -2 = read-only administrator
		self.name=None				# tuple first, last, middle
		self.email=None				# email address
		self.altemail=None			# alternate email
		self.phone=None				# non-validated string
		self.fax=None				#
		self.cellphone=None			#
			

									
class dbContext:
	"""This class """
	def __init__(self):
		self.db=None				# Points to Database object for this context
		self.user=None				# validated username
		self.groups=None			# groups for this user
		
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
	def __init__(self,context):
		"""Record must be created with a context. This should only be done directly
		by a Database object, to insure security and protocols are handled correctly"""
		self.recid=None				# 32 bit integer recordid (within the current database)
		self.rectype=""				# string of the RecordType represented by this Record
		self.fields={comments:[]}				# a Dictionary containing field names associated with their data
		self.ofields={}				# when a field value is changed, the original value is stored here
		self.__owner=0				# The owner of this record
		self.__creator=0			# original creator of the record
		self.__creationdate=None	# creation date
		self.__permissions=			# permissions for read access, comment write access
		self.__context=None			# Record objects are only 
				
	def __str__(self):
		ret=["%d (%s)\n"%(self.recid,self.rectype)]
		for i in fields
	
	def __getitem__(self,key):
		"""Behavior is to return None for undefined fields, None is also
		the default value for existant, but undefined fields, which will be
		treated identically"""
		key=key.lower()
		if key=="owner" : return self.__owner
		if key=="creator" : return self.__creator
		if key=="creationdate" : return self.__creationdate
		if key=="permissions" : return self.__permissions
		if self.fields.has_key(key) : return self.fields[key]
		return None
	
	def __setitem__(self,key,value):
		if (key=="comments") :
		if (key=="owner") :
		if (key=="creator") :
		if (key=="creationdate") :
		if (key=="permissions") :
		if (self.fields.has_key(key) and self.fields[key]!=None) :
			self.fields["comments"].append("Field changed <...")
			
			self.fields[key]=value

		self.fields[key]=value		# if we got here, there was no previously assigned value for this field	
									# and it wasn't a special value
	
class Database:
	"""This class represents the database as a whole. Records can be accessed"""
		def __init__(self,path=".",cachesize=256000000):
			self.path=path
			
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
	

