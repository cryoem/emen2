##############
# Database.py  Steve Ludtke  05/21/2004
##############

# TODO:
# read-only security index
# search interface
# XMLRPC interface
# XML parsing
# Database id's not supported yet


"""This module encapsulates an electronic notebook/oodb

Note that the database does have a security model, but it cannot be rigorously enforced at the python level.
That is, a programmer using this library will not be able to accidentally violate the security model, but
with sufficient intent and knowledge it is possible. To use this module securely it must be encapsulated
by another layer, say an xmlrpc server...
"""

from bsddb3 import db
from cPickle import dumps,loads
from sets import *
import os
import sha
import time
import re
import operator
from math import *

LOGSTRINGS = ["SECURITY", "CRITICAL","ERROR   ","WARNING ","INFO    ","DEBUG   "]

class SecurityError(Exception):
	"Exception for a security violation"

class FieldError(Exception):
	"Exception for problems with Field definitions"

def parseparmvalues(text):
	"""This will exctract XML 'emen_parm' tags from a block of text and return a dictionary
	containing the passed values"""
	# This nasty regex will extract <aaa bbb="ccc">ddd</eee> blocks as [(aaa,bbb,ccc,ddd,eee),...]
	srch=re.findall('<([^> ]*) ([^=]*)="([^"]*)" *>([^<]*)</([^>]*)>' ,text)
	ret={}
	
	for t in srch:
		if (t[0].lower()!="emen:param" or t[1].lower()!="name" or t[4]!="emen:param" or " " in t[2].strip()) :continue
		ret[t[2].strip().lower()]=t[3]

	return ret

def parseparmdef(text):
	"""This will exctract XML 'emen_parm' tags from a block of text and return a dictionary
	containing the tags as keys and default values (which may be None)"""
	
	# This nasty regex will extract <aaa bbb="ccc" /> blocks as [(aaa,bbb,ccc),...]
	srch=re.findall('<([^> ]*) ([^=]*)="([^"]*)" */>' ,text)
	ret={}

	for t in srch:
		if (t[0].lower()!="emen:param" or t[1].lower()!="name" or " " in t[2].strip()) :continue
		ret[t[2].strip().lower()]=None
	
	# This nasty regex will extract <aaa bbb="ccc">ddd</eee> blocks as [(aaa,bbb,ccc,ddd,eee),...]
	srch=re.findall('<([^> ]*) ([^=]*)="([^"]*)" *>([^<]*)</([^>]*)>' ,text)

	for t in srch:
		if (t[0].lower()!="emen:param" or t[1].lower()!="name" or t[4]!="emen:param" or " " in t[2].strip()) :continue
		ret[t[2].strip().lower()]=t[3]
	
	return ret	
		
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
	def __init__(self,name,file=None,dbenv=None,nelem=0,relate=0):
		"""This is a persistent dictionary implemented as a BerkeleyDB BTree
		name is required, and will also be used as a filename if none is
		specified. If relate is true, then parent/child and cousin relationships
		between records are also supported."""
		global globalenv
		if (not dbenv) : dbenv=globalenv
		self.bdb=db.DB(dbenv)
		if file==None : file=name+".bdb"
#		print "Open: ",file
#		if nelem : self.bdb.set_h_nelem(nelem)					# guess how many elements in a hash
		self.bdb.open(file,name,db.DB_BTREE,db.DB_CREATE)
#		self.bdb.open(file,name,db.DB_HASH,db.DB_CREATE)

		if relate :
			self.relate=1
		
			self.pcdb=db.DB(dbenv)
			self.pcdb.open(file+".pc",name,db.DB_BTREE,db.DB_CREATE)
			
			self.cpdb=db.DB(dbenv)
			self.cpdb.open(file+".cp",name,db.DB_BTREE,db.DB_CREATE)
			
			self.reldb=db.DB(dbenv)
			self.reldb.open(file+".rel",name,db.DB_BTREE,db.DB_CREATE)
		else : self.relate=0

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

	def pclink(self,parenttag,childtag,paramname=""):
		"""This establishes a parent-child relationship between two tags.
		The relationship may also be named. That is the parent may
		get a list of children only with a specific paramname."""
		if not self.relate : raise Exception,"relate option required"
		parenttag=str(parenttag)
		childtag=str(childtag)
		
		try:
			o=loads(self.pcdb.get(parenttag))
		except:
			o=[]
			
		if not (childtag,paramname) in o:
			o.append((childtag,paramname))
			self.pcdb.put(parenttag,dumps(o))
	
			try:
				o=loads(self.cpdb.get(childtag))
			except:
				o=[]
			
			o.append(parenttag)
			self.cpdb.put(childtag,dumps(o))
	
	def pcunlink(self,parenttag,childtag,paramname=""):
		"""Removes a parent-child relationship, returns quietly if relationship did not exist"""
		if not self.relate : raise Exception,"relate option required"
		parenttag=str(parenttag)
		childtag=str(childtag)
		
		try:
			o=loads(self.pcdb.get(parenttag))
		except:
			return
			
		if not (childtag,paramname) in o: return
		
		del o[childtag]
		self.pcdb.put(parenttag,dumps(o))
		
		o=loads(self.cpdb.get(childtag))
		del o[parenttag]
		self.cpdb.put(childtag,dumps(o))	
		
	def link(self,tag1,tag2):
		"""Establishes a lateral relationship (cousins) between two tags"""
		if not self.relate : raise Exception,"relate option required"
		tag1=str(tag1)
		tag2=str(tag2)
		
		try:
			o=loads(self.reldb.get(tag1))
		except:
			o=[]
			
		if not tag2 in o:
			o.append(tag2)
			self.reldb.put(tag1,dumps(o))
	
			try:
				o=loads(self.reldb.get(tag2))
			except:
				o=[]
			
			o.append(tag1)
			self.reldb.put(tag2,dumps(o))	
		
			
	def unlink(self,tag1,tag2):
		"""Removes a lateral relationship (cousins) between two tags"""
		if not self.relate : raise Exception,"relate option required"
		tag1=str(tag1)
		tag2=str(tag2)
		
		try:
			o=loads(self.rekdb.get(tag1))
		except:
			return
			
		if not tag2 in o: return
		
		del o[tag2]
		self.reldb.put(tag1,dumps(o))
		
		o=loads(self.reldb.get(tag2))
		del o[tag1]
		self.cpdb.put(tag2,dumps(o))	
	
	def parents(self,tag):
		"""Returns a list of the tag's parents"""
		if not self.relate : raise Exception,"relate option required"
		tag=str(tag)
		
		try:
			return loads(self.cpdb.get(tag))
		except:
			return []
		
		
	def children(self,tag,paramname=None):
		"""Returns a list of the tag's children. If paramname is
		omitted, all named and unnamed children will be returned"""
		if not self.relate : raise Exception,"relate option required"
		tag=str(tag)
		
		try:
			c=loads(self.pcdb.get(tag))
			if paramname :
				c=filter(lambda x:x[1]==paramname,c)
				return [x[0] for x in c]
			else: return c
		except:
			return []
	
	def cousins(self,tag):
		"""Returns a list of tags related to the given tag"""
		if not self.relate : raise Exception,"relate option required"
		tag=str(tag)
		
		try:
			return loads(self.reldb.get(tag))
		except:
			return []

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
	"choice":("s",lambda x:str(x)),			# string from a fixed enumerated list
	"string":("s",lambda x:str(x)),			# string from an extensible enumerated list
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
	"binary":(None,lambda x:str(x)),				# url points to an arbitrary binary
	"child":(None,lambda y:map(lambda x:int(x),y)),	# link to dbid/recid of a child record
	"link":(None,lambda y:map(lambda x:int(x),y))		# lateral link to related record dbid/recid
}

# Valid physical property names
# The first item in the value tuple is ostensibly a default, but this
# will generally be provided by the ParamDef. It may be that
# synonyms should be combined in a better way
valid_properties = { 
"count":(None,{}),
"unitless":(None,{}),
"length":("meter",{"m":1.,"meters":1,"km":1000.,"kilometer":1000.,"cm":0.01,"centimeter":0.01,"mm":0.001,
	"millimeter":0.001,"micron":1.0e-6,"nm":1.0e-9,"nanometer":1.0e-9,"angstrom":1.0e-10,
	"A":1.0e-10}),
"area":("m^2",{"m^2":1.,"cm^2":1.0e-4}),
"volume":("m^3",{"m^3":1,"cm^3":1.0e-6,"ml":1.0e-6,"milliliter":1.0e-6,"l":1.0e-3}),
"mass":("gram",{"g":1.,"gram":1.,"mg":.001,"milligram":.001,"Da":1.6605387e-24,"dalton":1.6605387e-24}),
"temperature":("K",{"K":1.,"kelvin":1.,"C":lambda x:x+273.15,"F":lambda x:(x+459.67)*5./9.,
	"degrees C":lambda x:x+273.15,"degrees F":lambda x:(x+459.67)*5./9.}),
"pH":("pH",{"pH":1.0}),
"voltage":("volt",{"V":1.0,"volt":1.0,"kv":1000.0,"kilovolt":1000.0,"mv":.001,"millivolt":.001}),
"current":("amp",{"A":1.0,"amp":1.0,"ampere":1.0}),
"resistance":("ohm",{"ohm":1.0}),
"inductance":("henry",{"H":1.0,"henry":1.0}),
"transmittance":("%T",{"%T":1.0}),
"relative_humidity":("%RH",{"%RH":1.0}),
"velocity":("m/s",{"m/s":1.0}),
"momentum":("kg m/s",{"kg m/s":1.0}),
"force":("N",{"N":1.0,"newton":1.0}),
"energy":("J",{"J":1.0,"joule":1.0}),
"angle":("degree",{"degree":1.0,"deg":1.0,"radian":180.0/pi})
}

class ParamDef:
	"""This class defines an individual data Field that may be stored in a Record.
	Field definitions are related in a tree, with arbitrary lateral linkages for
	conceptual relationships. The relationships are handled externally by the
	Database object. Fields may only be modified by the administrator once
	created, and then, they should only be modified for clarification""" 
	def __init__(self,name=None,vartype=None,desc_short=None,desc_long=None,property=None,defaultunits=None,choices=None):
		self.name=name					# This is the name used in XML files to refer to this field, lower case
		self.vartype=vartype			# Variable data type. List of valid types in the module global 'vartypes'
		self.desc_short=desc_short		# This is a very short description for use in forms
		self.desc_long=desc_long		# A complete description of the meaning of this variable
		self.property=property			# Physical property represented by this field, List in 'properties'
		self.defaultunits=defaultunits	# Default units (optional)
		self.choices=choices			# choices for choice and string vartypes, a tuple
		self.creator=None				# original creator of the record
		self.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
										# creation date
		self.creationdb=None		# dbid where paramdef originated

	def __str__(self):
		return format_string_obj(self.__dict__,["name","vartype","desc_short","desc_long","property","defaultunits","","creator","creationtime","creationdb"])
			
class RecordDef:
	"""This class defines a prototype for Database Records. Each Record is a member of
	a RecordClass. This class contains the information giving meaning to the data Fields
	contained by the Record"""
	def __init__(self,dict=None):
		self.name=None				# the name of the current RecordDef, somewhat redundant, since also stored as key for index in Database
		self.mainview=None			# an XML string defining the experiment with embedded params
									# this is the primary definition of the contents of the record
		self.views={}				# Dictionary of additional (named) views for the record
		self.params={}				# A dictionary keyed by the names of all params used in any of the views
									# values are the default value for the field.
									# this represents all params that must be defined to have a complete
									# representation of the record. Note, however, that such completeness
									# is NOT REQUIRED to have a valid Record 
		self.private=0				# if this is 1, this RecordDef may only be retrieved by its owner (which may be a group)
									# or by someone with read access to a record of this type
		self.owner=None				# The owner of this record
		self.creator=0				# original creator of the record
		self.creationtime=None		# creation date
		self.creationdb=None		# dbid where recorddef originated
		if (dict) : self.__dict__.update(dict)
		
	def __str__(self):
		return "{ name: %s\nmainview:\n%s\nviews: %s\nparams: %s\nprivate: %s\nowner: %s\ncreator: %s\ncreationtime: %s\ncreationdb: %s}\n"%(
			self.name,self.mainview,self.views,self.stringparams(),str(self.private),self.owner,self.creator,self.creationtime,self.creationdb)

	def stringparams(self):
		"""returns the params for this recorddef as an indented printable string"""
		r=["{"]
		for k,v in self.params.items():
			r.append("\n\t%s: %s"%(k,str(v)))
		return "".join(r)+" }\n"
	
	def findparams(self):
		"""This will update the list of params by parsing the views"""
		d=parseparmdef(self.mainview)
		for i in self.views.values():
			d.update(parseparmdef(i))
		self.params=d
			
class User:
	"""This defines a database user, note that group 0 membership is required to add new records.
Users are never deleted, only disabled, for historical logging purposes"""
	def __init__(self,dict=None):
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
		if (dict):
			self.__dict__.update(dict)
			if (dict.has_key("private")) : self.private=1
			else : self.private=0
			if (dict.has_key("name1")) :
				del self.__dict__["name1"]
				del self.__dict__["name2"]
				del self.__dict__["name3"]
				self.name=(dict["name1"],dict["name2"],dict["name3"])
			
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
	of a particular RecordDef, however, note that it is not required to have a value for
	every field described in the RecordDef, though this will usually be the case.
	
	To modify the params in a record use the normal obj[key]= or update() approaches. 
	Changes are not stored in the database until commit() is called. To examine params, 
	use obj[key]. There are a few special keys, handled differently:
	owner,creator,creationtime,permissions,comments

	Record instances must ONLY be created by the Database class through retrieval or
	creation operations. self.context will store information about security and
	storage for the record.
	
	Mechanisms for changing existing params are a bit complicated. In a sense, as in a 
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
	can override this behavior by changing 'params' directly rather than using
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
		self.rectype=""				# name of the RecordDef represented by this Record
		self.__params={}			# a Dictionary containing field names associated with their data
		self.__comments=[]			# a List of comments records
		self.__oparams={}			# when a field value is changed, the original value is stored here
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
		try: del odict['__context__']
		except: pass
		try: del odict['_Record__ptest']
		except: pass
		
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
			self.__permissions=((),(),(ctx.user,))
		
		# test for owner access in this context
		if (-1 in ctx.groups or ctx.user==self.__owner or self.__owner in ctx.groups) : self.__ptest=[1,1,1,1]
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
		ret=["%s (%s)\n"%(str(self.recid),self.rectype)]
		for i,j in self.__params.items():
			ret.append("%12s:  %s\n"%(str(i),str(j)))
		return "".join(ret)
		
	def __getitem__(self,key):
		"""Behavior is to return None for undefined params, None is also
		the default value for existant, but undefined params, which will be
		treated identically"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid
				
		key=key.lower()
		if key=="owner" : return self.__owner
		if key=="creator" : return self.__creator
		if key=="creationtime" : return self.__creationtime
		if key=="permissions" : return self.__permissions
		if key=="comments" : return self.__comments
		if self.__params.has_key(key) : return self.__params[key]
		return None
	
	def __setitem__(self,key,value):
		"""This and 'update' are the primary mechanisms for modifying the params in a record
		Changes are not written to the database until the commit() method is called!"""
		# comments may include embedded field values if the user has full write access
		key=key.strip()
		if (key=="comments") :
			if not isinstance(value,str): return		# if someone tries to update the comments tuple, we just ignore it
			if self.__ptest[1]:
				dict=parseparmvalues(value)	# find any embedded params
				if len(dict)>0 and not self.__ptest[2] : 
					raise SecurityError,"Insufficient permission to modify field in comment for record %d"%self.recid
				
				self.__comments.append((self.__context.user,time.strftime("%Y/%m/%d %H:%M:%S"),value))	# store the comment string itself
				
				# now update the values of any embedded params
				for i,j in dict.items():
					self.__realsetitem(i,j)
			else :
				raise SecurityError,"Insufficient permission to add comments to record %d"%self.recid
		elif (key=="rectype") :
			if self.__ptest[3]: self.rectype=value
			else: raise SecurityError,"Insufficient permission to change the record type"
		elif (key=="owner") :
			if self.__owner==value: return
			if self.__ptest[3]: self.__owner=value
			else : raise SecurityError,"Only the administrator or the record owner can change the owner"
		elif (key=="creator" or key=="creationtime") :
			# nobody is allowed to do this
			if self.__creator==value or self.__creationtime==value: return 
			raise SecurityError,"Creation params cannot be modified"
		elif (key=="permissions") :
			if self.__permissions==value: return
			if self.__ptest[2]:
				if isinstance(value,str) : value=eval(value)
				try:
					value=(tuple(value[0]),tuple(value[1]),tuple(value[2]))
					self.__permissions=value
				except:
					raise TypeError,"Permissions must be a 3-tuple of tuples"
			else: 
				raise SecurityError,"Write permission required to modify security %d"%self.recid
		else :
			if self.__params.has_key(key) and self.__params[key]==value : return
			if not self.__ptest[2] : raise SecurityError,"No write permission for record %s"%str(self.recid)
			if key in self.__params  and self.__params[key]!=None:
				self.__comments.append((self.__context.user,time.strftime("%Y/%m/%d %H:%M:%S"),"<field name=%s>%s</field>"%(str(key),str(value))))
			self.__realsetitem(key,value)
	
	def __realsetitem(self,key,value):
			"""This insures that copies of original values are made when appropriate
			security should be handled by the parent method"""
			if key in self.__params and self.__params[key]!=None and not key in self.__oparams : self.__oparams[key]=self.__params[key]
			self.__params[key]=value
									

	def update(self,dict):
		"""due to the processing required, it's best just to implement this as
		a sequence of calls to the existing setitem method"""
		for i,j in dict.items(): self[i]=j
	
	def keys(self):
		"""All retrievable keys for this record"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid		
		return tuple(self.__params.keys())+("comments","owner","creator","creationdate","permissions")
		
	def items(self):
		"""Key/value pairs"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid		
		ret=self.__params.items()
		try:
			ret+=[(i,self[i]) for i in ("comments","owner","creator","creationdate","permissions")]
		except:
			pass
		return ret
	
	def items_dict(self):
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information"""
		if not self.__ptest[0] : raise SecurityError,"No permission to access record %d"%self.recid		
		ret={}
		ret.update(self.__params)
		try:
			for i in ("comments","owner","creator","creationdate","permissions"): ret[i]=self[i]
		except:
			pass
		return ret
		
	
	def has_key(self,key):
		if key in self.keys() or key in ("comments","owner","creator","creationdate","permissions"): return True
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
		self.__dbenv=db.DBEnv()
		self.__dbenv.set_cachesize(0,cachesize,4)		# gbytes, bytes, ncache (splits into groups)
		self.__dbenv.set_data_dir(path)
		self.__dbenv.open(path+"/home",db.DB_CREATE+db.DB_INIT_MPOOL)
		
		if not os.access(path+"/security",os.F_OK) : os.makedirs(path+"/security")
		if not os.access(path+"/index",os.F_OK) : os.makedirs(path+"/index")
		
		# Users
		self.__users=BTree("users",path+"/security/users.bdb",dbenv=self.__dbenv)						# active database users
		self.__newuserqueue=BTree("newusers",path+"/security/newusers.bdb",dbenv=self.__dbenv)			# new users pending approval
	
		# Defined ParamDefs
		self.__paramdefs=BTree("ParamDefs",path+"/ParamDefs.bdb",dbenv=self.__dbenv,relate=1)						# ParamDef objects indexed by name

		# Defined RecordDefs
		self.__recorddefs=BTree("RecordDefs",path+"/RecordDefs.bdb",dbenv=self.__dbenv,relate=1)					# RecordDef objects indexed by name
					
		# The actual database, keyed by recid, a positive integer unique in this DB instance
		# 2 special keys exist, the record counter is stored with key -1
		# and database information is stored with key=0
		self.__records=BTree("database",path+"/database.bdb",dbenv=self.__dbenv,relate=1)						# The actual database, containing id referenced Records
		try:
			maxr=self.__records[-1]
		except:
			self.__records[-1]=0
			self.LOG(3,"New database created")
			
		# Indices
		self.__secrindex=FieldBTree("secrindex",path+"/security/roindex.bdb","s",dbenv=self.__dbenv)	# index of records each user can read
		self.__recorddefindex=FieldBTree("RecordDefindex",path+"/RecordDefindex.bdb","s",dbenv=self.__dbenv)		# index of records belonging to each RecordDef
		self.__fieldindex={}				# dictionary of FieldBTrees, 1 per ParamDef, not opened until needed

		# The mirror database for storing offsite records
		self.__mirrorrecords=BTree("mirrordatabase",path+"/mirrordatabase.bdb",dbenv=self.__dbenv)

		# Workflow database, user indexed btree of lists of things to do
		# again, key -1 is used to store the wfid counter
		self.__workflow=BTree("workflow",path+"/workflow.bdb",dbenv=self.__dbenv)
		try:
			max=self.__workflow[-1]
		except:
			self.__workflow[-1]=1
			self.LOG(3,"New workflow database created")
					
		self.LOG(4,"Database initialized")

		# Create an initial administrative user for the database
		self.LOG(0,"Warning, root user recreated")
		u=User()
		u.username="root"
		p=sha.new("foobar")
		u.password=p.hexdigest()
		u.groups=[-1]
		u.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		u.name=('Database','','Administrator')
		self.__users["root"]=u
		
		# This sets up a few standard ParamDefs common to all records
		if not self.__paramdefs.has_key("owner"):
			pd=ParamDef("owner","string","Record Owner","This is the user-id of the 'owner' of the record")
			self.__paramdefs["owner"]=pd
			pd=ParamDef("creator","string","Record Creator","The user-id that initially created the record")
			self.__paramdefs["creator"]=pd
			pd=ParamDef("creationdate","datetime","Creation timestamp","The date/time the record was originally created")
			self.__paramdefs["creationdate"]=pd
	
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
			print "%s: (%s)  %s\n"%(time.strftime("%Y/%m/%d %H:%M:%S"),LOGSTRINGS[level],message)
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
		
		# check password, hashed with sha-1 encryption
		else :
			s=sha.new(password)
			user=self.__users[username]
			if user.disabled : raise SecurityError,"User %s has been disabled. Please contact the administrator."
			if (s.hexdigest()==user.password) : ctx=Context(None,self,username,user.groups,host,maxidle)
			else:
				self.LOG(0,"Invalid password: %s (%s)"%(username,host))
				raise ValueError,"Invalid Password"
		
		# This shouldn't happen
		if ctx==None :
			self.LOG(1,"System ERROR, login(): %s (%s)"%(username,host))
			raise Exception,"System ERROR, login()"
		
		# we use sha to make a key for the context as well
		s=sha.new(username+str(host)+str(time.time()))
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
			
		if host and host!=ctx.host :
			self.LOG(0,"Hacker alert! Attempt to spoof context (%s != %s)"%(host,ctx.host))
			raise Exception,"Bad address match, login sessions cannot be shared"
		
		return ctx			

	def checkcontext(self,ctxid,host):
		"""This allows a client to test the validity of a context, and
		get basic information on the authorized user and his/her permissions"""
		a=self.__getcontext(ctxid,host)
		return(a.user,a.groups)
	
	def getchildren(self,key,keytype="record",paramname=None):
		"""This will get the keys of the children of the referenced object
		keytype is 'record', 'recorddef', or 'paramdef'"""
		if keytype=="record" : return self.__records.children(key,paramname)
		if keytype=="recorddef" : return self.__recorddefs.children(key,paramname)
		if keytype=="paramdef" : return self.__paramdefs.children(key,paramname)
		
		raise Exception,"getchildren keytype must be 'record', 'recorddef' or 'paramdef'"
	
	def getparents(self,key,keytype="record"):
		"""This will get the keys of the parents of the referenced object
		keytype is 'record', 'recorddef', or 'paramdef'"""
		
		if keytype=="record" : return self.__records.parents(key)
		if keytype=="recorddef" : return self.__recorddefs.parents(key)
		if keytype=="paramdef" : return self.__paramdefs.parents(key)
		
		raise Exception,"getparents keytype must be 'record', 'recorddef' or 'paramdef'"

	def getcousins(self,key,keytype="record"):
		"""This will get the keys of the cousins of the referenced object
		keytype is 'record', 'recorddef', or 'paramdef'"""
		
		if keytype=="record" : return self.__records.cousins(key)
		if keytype=="recorddef" : return self.__recorddefs.cousins(key)
		if keytype=="paramdef" : return self.__paramdefs.cousins(key)
		
		raise Exception,"getcousins keytype must be 'record', 'recorddef' or 'paramdef'"

	def pclink(self,pkey,ckey,keytype="record",paramname=""):
		"""Establish a parent-child relationship between two keys"""
		
		print "pclink '%s' '%s'"%(pkey,ckey)
		if keytype=="record" : return self.__records.pclink(pkey,ckey,paramname)
		if keytype=="recorddef" : return self.__recorddefs.pclink(pkey,ckey,paramname)
		if keytype=="paramdef" : return self.__paramdefs.pclink(pkey,ckey,paramname)
		
		raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
	
	def pcunlink(self,pkey,ckey,keytype="record",paramname=""):
		"""Remove a parent-child relationship between two keys. Simply returns if link doesn't exist."""
		
		if keytype=="record" : return self.__records.pcunlink(pkey,ckey,paramname)
		if keytype=="recorddef" : return self.__recorddefs.pcunlink(pkey,ckey,paramname)
		if keytype=="paramdef" : return self.__paramdefs.pcunlink(pkey,ckey,paramname)
		
		raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
	
	def link(self,key1,key2,keytype="record"):
		"""Establish a 'cousin' relationship between two keys."""
		
		if keytype=="record" : return self.__records.link(key1,key2)
		if keytype=="recorddef" : return self.__recorddefs.link(key1,key2)
		if keytype=="paramdef" : return self.__paramdefs.link(key1,key2)
		
		raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
	
	def unlink(self,key1,key2,keytype="record"):
		"""Remove a 'cousin' relationship between two keys."""
		
		if keytype=="record" : return self.__records.unlink(key1,key2)
		if keytype=="recorddef" : return self.__recorddefs.unlink(key1,key2)
		if keytype=="paramdef" : return self.__paramdefs.unlink(key1,key2)
		
		raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
		
	def disableuser(self,username,ctxid,host=None):
		"""This will disable a user so they cannot login. Note that users are NEVER deleted, so
		a complete historical record is maintained. Only an administrator can do this."""
		ctx=self.__getcontext(ctxid,host)
		if not -1 in ctx.groups :
			raise SecurityError,"Only administrators can disable users"

		if username==ctx.user : raise SecurityError,"Even administrators cannot disable themselves"
			
		user=self.__users[username]
		user.disabled=1
		self.__users[username]=user
		self.LOG(0,"User %s disabled by %s"%(username,ctx.user))

		        
	def approveuser(self,username,ctxid,host=None):
		"""Only an administrator can do this, and the user must be in the queue for approval"""
		ctx=self.__getcontext(ctxid,host)
		if not -1 in ctx.groups :
			raise SecurityError,"Only administrators can approve new users"
		
		if not username in self.__newuserqueue :
			raise KeyError,"User %s is not pending approval"%username
			
		if username in self.__users :
			self.__newuserqueue[username]=None
			raise KeyError,"User %s already exists, deleted pending record"%username

		self.__users[username]=self.__newuserqueue[username]
		self.__newuserqueue[username]=None
	
	def getuserqueue(self,ctxid,host=None):
		"""Returns a list of names of unapproved users"""
		return self.__newuserqueue.keys()

	def putuser(self,user,ctxid,host=None):

		try:
			ouser=self.__users[user.username]
		except:
			raise KeyError,"Putuser may only be used to update existing users"
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user!=ouser.username and not(-1 in ctx.groups) :
			raise SecurityError,"Only administrators and the actual user may update a user record"
		
		if not (-1 in ctx.groups) : user.groups=ouser.groups
		
		if user.password!=ouser.password:
			raise SecurityError,"Passwords may not be changed with this method"
		
		self.__users[user.username]=user
	
	def setpassword(self,username,oldpassword,newpassword,ctxid,host=None):
		ctx=self.__getcontext(ctxid,host)
		user=self.__users[username]
		
		s=sha.new(oldpassword)
		if not (-1 in ctx.groups) and s.hexdigest()!=user.password :
			time.sleep(2)
			raise SecurityError,"Original password incorrect"
		
		# we disallow bad passwords here, right now we just make sure that it 
		# is at least 6 characters long
		if (len(newpassword)<6) : raise SecurityError,"Passwords must be at least 6 characters long" 
		t=sha.new(newpassword)
		user.password=t.hexdigest()
		
		self.__users[user.username]=user
	
	def adduser(self,user):
		"""adds a new user record. However, note that this only adds the record to the
		new user queue, which must be processed by an administrator before the record
		becomes active. This system prevents problems with securely assigning passwords
		and errors with data entry. Anyone can create one of these"""
		if user.username==None or len(user.username)<3 : 
			raise KeyError,"Attempt to add user with invalid name"
		
		if user.username in self.__users :
			raise KeyError,"User with username %s already exists"%user.username
		
		if user.username in self.__newuserqueue :
			raise KeyError,"User with username %s already pending approval"%user.username
		
		if len(user.password)<5 :
			raise SecurityError,"Passwords must be at least 5 characters long"
		
		if len(user.password)!=40 :
			# we disallow bad passwords here, right now we just make sure that it 
			# is at least 6 characters long
			if len(user.password)<6 : raise SecurityError,"Passwords must be at least 6 characters long"
			s=sha.new(user.password)
			user.password=s.hexdigest()

		user.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		self.__newuserqueue[user.username]=user
		
	def getqueueduser(self,username,ctxid,host=None):
		"""retrieves a user's information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record"""
		
		ret=self.__newuserqueueu[username]
		
		ctx=self.__getcontext(ctxid,host)
		
		# The user him/herself or administrator can get all info
		if (-1 in ctx.groups) or (-2 in ctx.groups): return ret
		
		raise SecurityError,"Only administrators can access pending users"
				
	def getuser(self,username,ctxid,host=None):
		"""retrieves a user's information. Information may be limited to name and id if the user
		requested privacy. Administrators will get the full record"""
		
		ret=self.__users[username]
		
		ctx=self.__getcontext(ctxid,host)
		
		# The user him/herself or administrator can get all info
		if (-1 in ctx.groups) or (-2 in ctx.groups) or (ctx.user==username) : return ret
		
		# if the user has requested privacy, we return only basic info
		if (ret.privacy==1 and ctx.user==None) or ret.privacy>=2 :
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
		return self.__users.keys()

	def getworkflow(self,ctxid,host=None):
		"""This will return an (ordered) list of workflow objects for the given context (user).
		it is an exceptionally bad idea to change a WorkFlow object's wfid."""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
		
		try:
			return self.__workflow[ctx.user]
		except:
			return []

	def addworkflowitem(self,work,ctxid,host=None) :
		"""This appends a new workflow object to the user's list. wfid will be assigned by this function"""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"

		if not isinstance(work,WorkFlow) : raise TypeError,"Only WorkFlow objects can be added to a user's workflow"
		
		work.wfid=self.__workflow[-1]
		self.__workflow[-1]=work.wfid+1
		
		if self.__workflow.has_key(ctx.user) :
			wf=self.__workflow[ctx.user]
			wf.append(work)
			self.__workflow[ctx.user]=wf
	
	def delworkflowitem(self,wfid,ctxid,host=None) :
		"""This will remove a single workflow object"""
		
		ctx=self.__getcontext(ctxid,host)
		if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
		
		wf=self.__workflow[ctx.user]
		for i,w in enumerate(wf):
			if w.wfid==wfid :
				del wf[i]
				break
		else: raise KeyError,"Unknown workflow id"
		
		self.__workflow[ctx.user]=wf
		
		
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
				w.wfid=self.__workflow[-1]
				self.__workflow[-1]=w.wfid+1
		
		self.__workflow[ctx.user]=wflist
	
	def getvartypenames(self):
		"""This returns a list of all valid variable types in the database. This is currently a
		fixed list"""
		return valid_vartypes.keys()

	def getpropertynames(self):
		"""This returns a list of all valid property types in the database. This is currently a
		fixed list"""
		return valid_properties.keys()
	
	def getpropertyunits(self,propname):
		"""Returns a list of known units for a particular property"""
		return valid_properties[propname][1].keys()
			
	def addparamdef(self,paramdef,ctxid,host=None,parent=None):
		"""adds a new ParamDef object, group 0 permission is required
		a p->c relationship will be added if parent is specified"""
		if not isinstance(paramdef,ParamDef) : raise TypeError,"addparamdef requires a ParamDef object"
		ctx=self.__getcontext(ctxid,host)
		if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create new paramdefs (need record creation permission)"
		if self.__paramdefs.has_key(paramdef.name) : raise KeyError,"paramdef %s already exists"%paramdef.name
		
		# force these values
		paramdef.creator=ctx.user
		paramdef.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		
		# this actually stores in the database
		self.__paramdefs[paramdef.name]=paramdef
		if (parent): pclink(parent,paramdef.name,"paramdef")
	
	def addparamchoice(self,paramdefname,choice):
		"""This will add a new choice to records of vartype=string. This is
		the only modification permitted to a ParamDef record after creation"""
		d=self.__paramdefs[paramdefname]
		if d.vartype!="string" : raise SecurityError,"choices may only be modified for 'string' parameters"
		
		d.choices=d.choices+(choice,)
		self.__paramdefs[paramdefname]=d
		
	def getparamdef(self,paramdefname):
		"""gets an existing ParamDef object, anyone can get any field definition"""
		return self.__paramdefs[paramdefname]
		
	def getparamdefnames(self):
		"""Returns a list of all ParamDef names"""
		return self.__paramdefs.keys()
	
	def getparamdefs(self,recs):
		"""Returns a list of ParamDef records.
		recs may be a single record, a list of records, or a list
		of paramdef names. This routine will 
		retrieve the parameter definitions for all parameters with
		defined values in recs. The results are returned as a dictionary.
		It is much more efficient to use this on a list of records than to
		call it individually for each of a set of records."""
		ret={}
		if isinstance(recs,Record) : recs=(recs,)
		
		if isinstance(recs[0],str) :
			for p in recs:
				if ret.has_key(p) or p in ("comments","creationdate","permissions","creator","owner") : continue
				try: ret[p]=self.__paramdefs[p]
				except: self.LOG(2,"Request for unknown ParamDef %s in %s"%(p,r.rectype))
		else:	
			for r in recs:
				for p in r.keys():
					if ret.has_key(p) or p in ("comments","creationdate","permissions","creator","owner") : continue
					try: ret[p]=self.__paramdefs[p]
					except: self.LOG(2,"Request for unknown ParamDef %s in %s"%(p,r.rectype))

		return ret
		
	def addrecorddef(self,recdef,ctxid,host=None,parent=None):
		"""adds a new RecordDef object. The user must be an administrator or a member of group 0"""
		if not isinstance(recdef,RecordDef) : raise TypeError,"addRecordDef requires a RecordDef object"
		ctx=self.__getcontext(ctxid,host)
		if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create new RecordDefs"
		if self.__recorddefs.has_key(recdef.name) : raise KeyError,"RecordDef %s already exists"%recdef.name
		
		# force these values
		if (recdef.owner==None) : recdef.owner=ctx.user
		recdef.creator=ctx.user
		recdef.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
		recdef.findparams()
		
		# this actually stores in the database
		self.__recorddefs[recdef.name]=recdef
		if (parent): pclink(parent,recdef.name,"recorddef")

	def putrecorddef(self,recdef,ctxid,host=None):
		"""This modifies an existing RecordDef. Note that certain params, including the
		Main view cannot be modified by anyone."""
		ctx=self.__getcontext(ctxid,host)
		rd=self.__recorddefs[recdef.name]

		if (not -1 in ctx.groups) and (ctx.user!=rd.owner) : 
			raise SecurityError,"Only the owner or administrator can modify RecordDefs"

		recdef.creator=rd.creator
		recdef.creationtime=rd.creationtime
		recdef.mainview=rd.mainview
		recdef.update()
		
		self.__recorddefs[recdef.name]=recdef
				
	def getrecorddef(self,rectypename,ctxid,host=None,recid=None):
		"""Retrieves a RecordDef object. This will fail if the RecordDef is
		private, unless the user is an owner or  in the context of a recid the
		user has permission to access"""
		if not self.__recorddefs.has_key(rectypename) : raise KeyError,"No such RecordDef %s"%rectypename
		
		ret=self.__recorddefs[rectypename]	# get the record
		
		if not ret.private : return ret
		
		# if the RecordDef isn't private or if the owner is asking, just return it now
		ctx=self.__getcontext(ctxid,host)
		if (ret.private and (ret.owner==ctx.user or ret.owner in ctx.groups)) : return ret

		# ok, now we need to do a little more work. 
		if recid==None: raise SecurityError,"User doesn't have permission to access private RecordDef '%s'"%rectypename
		
		rec=self.getrecord(recid)		# try to get the record, may (and should sometimes) raise an exception

		if rec.rectype!=rectypename: raise SecurityError,"Record %d doesn't belong to RecordDef %s"%(recid,rectypename)

		# success, the user has permission
		return ret
	
	def getrecorddefnames(self):
		"""This will retrieve a list of all existing RecordDef names, 
		even those the user cannot access the contents of"""
		return self.__recorddefs.keys()
		
	def reindex(self,key,oldval,newval,recid):
		"""This function reindexes a single key/value pair
		This includes creating any missing indices if necessary"""

		if (key=="comments" or key=="permissions") : return		# comments & permissions are not currently indexed 
		if (oldval==newval) : return		# no change, no indexing required
		
		try:
			ind=self.__fieldindex[key]		# Try to get the index for this key
		except:
			# index not open yet, open/create it
			try:
				f=self.__paramdefs[key]		# Look up the definition of this field
			except:
				# Undefined field, we can't create it, since we don't know the type
				raise FieldError,"No such field %s defined"%key
			tp=valid_vartypes[f.vartype][0]
			if not tp : return			# if this is None, then this is an 'unindexable' field
			
			# create/open index
			self.__fieldindex[key]=FieldBTree(key,"%s/index/%s.bdb"%(self.path,key),tp,self.__dbenv)
			ind=self.__fieldindex[key]
		
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
		print o,n,uo,un

		# anything in both old and new should be ok,
		# So, we remove the index entries for all of the elements in 'old', but not 'new'
		for i in uo:
			self.__secrindex.removeref(i,recid)
		print "now un"
		# then we add the index entries for all of the elements in 'new', but not 'old'
		for i in un:
			self.__secrindex.addref(i,recid)

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
			orig=self.__records[record.recid]		# get the unmodified record
		except:
			# Record must not exist, lets create it
			#p=record.setContext(ctx)

			record.recid=self.__records[-1]+1				# Get a new record-id
			self.__records[-1]=record.recid				# Update the recid counter, TODO: do the update more safely/exclusive access
			
			# Group -1 is administrator, group 0 membership is global permission to create new records
			if (not 0 in ctx.groups) and (not -1 in ctx.groups) : raise SecurityError,"No permission to create records"

			record.setContext(ctx)
			
			# index params
			for k,v in record.items():
				self.reindex(k,None,v,record.recid)
			
			self.reindexsec(None,reduce(operator.concat,record["permissions"]),record.recid)		# index security
			self.__recorddefindex.addref(record.rectype,record.recid)			# index recorddef
			
#			print "putrec->\n",record.__dict__
			self.__records[record.recid]=record		# This actually stores the record in the database
			return record.recid
				
		p=orig.setContext(ctx)				# security check on the original record
		
		# Ok, to efficiently update the indices, we need to figure out what changed
		params=Set(orig.keys()).union_update(record.keys())		# list of all params (old and new)
		changedparams=[]
		for f in params:
			try:
				if (orig[f]!=record[f]) : changedparams.append(f)
			except:
				changedparams.append(f)
		
		# make sure the user has permission to modify the record
		if not p[2] :
			if not p[1] : raise SecurityError,"No permission to modify record %d"%record.recid
			if len(changedparams>1) or changedparams[0]!="comments" : raise SecurityError,"Insufficient permission to change field values on record %d"%record.recid
		
		# Now update the indices
		for f in changedparams:
			# reindex will accept None as oldval or newval
			try:    oldval=orig[f]
			except: oldval=None
			
			try:    newval=record[f]
			except: newval=None

			self.reindex(f,oldval,newval,record.recid)

		self.reindexsec(reduce(operator.concat,orig["permissions"]),
			reduce(operator.concat,record["permissions"]),record.recid)		# index security
		self.__records[record.recid]=record		# This actually stores the record in the database
		return record.recid
	
	def newrecord(self,rectype,ctxid,host=None,init=0):
		"""This will create an empty record and (optionally) initialize it for a given RecordDef (which must
		already exist)."""
		ctx=self.__getcontext(ctxid,host)
		ret=Record()
		ret.setContext(ctx)
		
		# try to get the RecordDef entry, this still may fail even if it exists, if the
		# RecordDef is private and the context doesn't permit access
		t=self.getrecorddef(rectype,ctxid,host)

		ret.recid=None
		ret.rectype=rectype						# if we found it, go ahead and set up
				
		if init:
			for k,v in t.params.items():
				ret[k]=v						# hmm, in the new scheme, perhaps this should just be a deep copy
		return ret

	def getrecordnames(self,ctxid,dbid=0,host=None) :
		"""This will return the ids of all records the user has permission to access""" 
		ctx=self.__getcontext(ctxid,host)
		
		return self.__secrindex[ctx.user]
		
	def getrecord(self,recid,ctxid,dbid=0,host=None) :
		"""Primary method for retrieving records. ctxid is mandatory. recid may be a list.
		if dbid is 0, the current database is used. host must match the host of the
		context"""
		
		ctx=self.__getcontext(ctxid,host)
		
		if (dbid!=0) : raise Exception,"External database support not yet available"
		
		# if a single id was requested, return it
		# setContext is required to make the record valid, and returns a binary security tuple
		if (isinstance(recid,int)):
			rec=self.__records[recid]
			p=rec.setContext(ctx)
			if not p[0] : raise Exception,"No permission to access record"
			return rec
		elif (isinstance(recid,list)):
			recl=map(lambda x:self.__records[x],recid)
			for rec in recl:
				p=rec.setContext(ctx)
				if not p[0] : raise Exception,"No permission to access one or more records"	
			return recl
		else : raise KeyError,"Invalid Key"
		
	def getrecordsafe(self,recid,ctxid,dbid=0,host=None) :
		"""Same as getRecord, but failure will produce None or a filtered list"""
		
		ctx=self.__getcontext(ctxid,host)
		
		if (dbid!=0) : return None
		
		if (isinstance(recid,int)):
			try:
				rec=self.__records[recid]
			except: 
				return None
			p=rec.setContext(ctx)
			if not p[0] : return None
			return rec
		elif (isinstance(recid,list)):
			try:
				recl=map(lambda x:self.__records[x],recid)
			except: 
				return None
			recl=filter(lambda x:x.setContext(ctx)[0],recl)
			return rec
		else : return None
	
	
