from UserDict import DictMixin
from math import *
import time
import re
from emen2.Database.exceptions import SecurityError
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

import traceback

# validation
import emen2.Database.subsystems
import emen2.Database.database



class ParamDef(DictMixin) :
	"""This class defines an individual data Field that may be stored in a Record.
	Field definitions are related in a tree, with arbitrary lateral linkages for
	conceptual relationships. The relationships are handled externally by the
	Database object. Fields may only be modified by the administrator once
	created, and then, they should only be modified for clarification"""

	# non-admin users may only update descs and choices
	attr_user = set(["desc_long","desc_short","choices"])
	attr_admin = set(["name","vartype","defaultunits","property","creator","creationtime","uri","creationdb"]) #
	attr_all = attr_user | attr_admin

	# name may be a dict; this allows backwards compat dictionary initialization
	def __init__(self,name=None,vartype=None,desc_short=None,desc_long=None,
						property=None,defaultunits=None,choices=None,uri=None):
		self.name=name					# This is the name of the paramdef, also used as index
		self.vartype=vartype			# Variable data type. List of valid types in the module global 'vartypes'
		self.desc_short=desc_short		# This is a very short description for use in forms
		self.desc_long=desc_long		# A complete description of the meaning of this variable
		self.property=property			# Physical property represented by this field, List in 'properties'
		self.defaultunits=defaultunits	# Default units (optional)
		self.choices=choices			# choices for choice and string vartypes, a tuple
		self.creator=None				# original creator of the record
		self.creationtime=time.strftime(emen2.Database.database.TIMESTR)	# creation date
		self.creationdb=None			# dbid where paramdef originated # deprecated; use URI
		self.uri = None

		if isinstance(name,dict):
			self.update(name)


	#################################
	# repr methods
	#################################

	def __str__(self):
		return str(dict(self))
		#return format_string_obj(self.__dict__,["name","vartype","desc_short","desc_long","property","defaultunits","","creator","creationtime","creationdb"])


	#################################
	# mapping methods
	#################################

	def __getitem__(self,key):
		try:
			return self.__dict__[key]
		except:
			pass

	def __setitem__(self,key,value):
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key

	def __delitem__(self,key):
		raise KeyError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)


	#################################
	# ParamDef methods
	#################################

	def items_dict(self):
		ret = {}
		for k in self.attr_all:
			ret[k]=self.__dict__[k]
		return ret


	#################################
	# validation methods
	#################################

	def validate(self):

		vtm=emen2.Database.subsystems.datatypes.VartypeManager()


		if set(self.__dict__.keys())-self.attr_all:
			raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)

		try:
			self.name=str(self.name)
			if len(self.desc_short)==0: raise Exception
		except:
			raise ValueError,"name required"


		try:
			self.vartype=str(self.vartype)
			if self.vartype not in vtm.getvartypes(): raise Exception
		except:
			raise ValueError,"Invalid vartype %s; not in valid_vartypes"%self.vartype


		try:
			self.desc_short=unicode(self.desc_short)
			if len(self.desc_short)==0: raise Exception
		except:
			raise ValueError,"Short description (desc_short) required"


		try:
			self.desc_long=unicode(self.desc_long)
			if len(self.desc_long)==0: raise Exception
		except:
			raise ValueError,"Long description (desc_long) required"


		if self.property == "": self.property=None
		if self.property != None:
			try:
				self.property = str(self.property)
				if self.property not in vtm.getproperties(): raise Exception
			except:
				g.debug("WARNING: Invalid property %s"%self.property)


		if self.defaultunits == "" or self.defaultunits == "unitless": self.defaultunits = None
		if self.defaultunits != None:
			self.defaultunits=str(self.defaultunits)
			if self.property == None:
				#raise ValueError,"Units requires property"
				g.debug("WARNING: Units requires property")
			else:
				prop=vtm.getproperty(self.property)
				if prop.equiv.get(self.defaultunits):
					self.defaultunits=prop.equiv.get(self.defaultunits)
				if self.defaultunits not in set(prop.units):
					#raise Exception,"Invalid default units %s for property %s"%(self.defaultunits,self.property)
					g.debug("WARNING: Invalid default units %s for property %s"%(self.defaultunits,self.property))

		if self.choices:
			try:
				self.choices = map(unicode, filter(bool, self.choices))
			except:
				raise ValueError, "Invalid choices"

		return



def parseparmvalues(text,noempty=0):
	"""This will extract parameter names $param or $param=value """
	# Ed 05/17/2008 -- cleaned up
	#srch=re.findall('<([^> ]*) ([^=]*)="([^"]*)" *>([^<]*)</([^>]*)>' ,text)
	#srch=re.findall('\$\$([^\$\d\s<>=,;-]*)(?:(?:=)(?:(?:"([^"]*)")|([^ <>"]*)))?',text)
	srch=re.finditer('\$\$([a-zA-Z0-9_\-]*)(?:(?:=)(?:(?:"([^"]*)")|([^ <>"]*)))?',text)
	params, vals = ret=[[],{}]

	for name, a, b in (x.groups() for x in srch):
		if name is '': continue
		else:
			params.append(name)
			if a is None: val=b
			else: val=a
			vals[name] = val
	return ret




class RecordDef(DictMixin) :
	"""This class defines a prototype for Database Records. Each Record is a member of
	a RecordClass. This class contains the information giving meaning to the data Fields
	contained by the Record"""

	attr_user = set(["mainview","views","private","typicalchld","desc_long","desc_short"])
	attr_admin = set(["name","params","paramsK","owner","creator","creationtime","uri","creationdb"])#
	attr_all = attr_user | attr_admin


	def __init__(self,d=None):
		self.name=None				# the name of the current RecordDef, somewhat redundant, since also stored as key for index in Database
		self.views={"recname":"$$rectype $$creator $$creationtime"}				# Dictionary of additional (named) views for the record
		self.mainview="$$rectype $$creator $$creationtime"			# a string defining the experiment with embedded params
									# this is the primary definition of the contents of the record
		self.private=0				# if this is 1, this RecordDef may only be retrieved by its owner (which may be a group)
									# or by someone with read access to a record of this type
		self.typicalchld=[]			# A list of RecordDef names of typical child records for this RecordDef
									# implicitly includes subclasses of the referenced types

		self.params={}				# A dictionary keyed by the names of all params used in any of the views
									# values are the default value for the field.
									# this represents all params that must be defined to have a complete
									# representation of the record. Note, however, that such completeness
									# is NOT REQUIRED to have a valid Record
		self.paramsK = []			# ordered keys from params()
		self.owner=None				# The owner of this record
		self.creator=0				# original creator of the record
		self.creationtime=None		# creation date
		self.creationdb=None		# dbid where recorddef originated
		self.uri=None
		self.desc_short=None
		self.desc_long=None

		if (d):
			self.update(d)


		self.findparams()


	def __setattr__(self,key,value):
		self.__dict__[key] = value
		if key == "mainview": self.findparams()


	#################################
	# pickle methods
	#################################

	def __setstate__(self,dict):
		"""restore unpickled values to defaults after unpickling"""
		self.__dict__.update(dict)
		if not dict.has_key("typicalchld") : self.typicalchld=[]


	#################################
	# repr methods
	#################################

	def __str__(self):
		return "{ name: %s\nmainview:\n%s\nviews: %s\nparams: %s\nprivate: %s\ntypicalchld: %s\nowner: %s\ncreator: %s\ncreationtime: %s\ncreationdb: %s}\n"%(
			self.name,self.mainview,self.views,self.stringparams(),str(self.private),str(self.typicalchld),self.owner,self.creator,self.creationtime,self.creationdb)

	def stringparams(self):
		"""returns the params for this recorddef as an indented printable string"""
		r=["{"]
		for k,v in self.params.items():
			r.append("\n\t%s: %s"%(k,str(v)))
		return "".join(r)+" }\n"


	#################################
	# mapping methods
	#################################

	def __getitem__(self,key):
		return self.__dict__.get(key)

	def __setitem__(self,key,value):
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise AttributeError,"Invalid key: %s"%key

	def __delitem__(self,key):
		raise AttributeError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)


	#################################
	# RecordDef methods
	#################################

	def findparams(self):
		"""This will update the list of params by parsing the views"""
		t,d=parseparmvalues(self.mainview)
		for i in self.views.values():
			t2,d2=parseparmvalues(i)
			for j in t2:
				# ian: fix for: empty default value in a view unsets default value specified in mainview
				if not d.has_key(j):
					t.append(j)
					d[j] = d2[j]
#			d.update(d2)

		self.params=d
		self.paramsK=tuple(t)


	def items_dict(self):
		ret = {}
		for k in self.attr_all:
			ret[k]=self.__dict__[k]
		return ret


	def fromdict(self,d):
		for k,v in d.items():
			self.__setattr__(k,v)
		self.validate()


	#################################
	# validate methods
	#################################

	def validate(self):

		if set(self.__dict__.keys())-self.attr_all:
			raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)

		try:
			if str(self.name) == "" or self.name==None:
				raise Exception
		except:
			raise ValueError,"name required; must be str or unicode"

		try:
			self.name=str(self.name)
		except:
			self.name=unicode(self.name)

		try:
			dict(self.views)
		except:
			raise ValueError,"views must be dict"

		try:
			list(self.typicalchld)
		except:
			raise ValueError,"Invalid value for typicalchld; list of recorddefs required."

		try:
			if unicode(self.mainview) == "": raise Exception
		except:
			raise ValueError,"mainview required; must be str or unicode"


		if not dict(self.views).has_key("recname"):
			g.debug("WARNING:: recname view strongly suggested")


		newviews={}
		for k,v in self.views.items():
			try:
				newviews[str(k)]=unicode(v)
			except:
				raise Exception,"View names must be str, views must be str/unicode"
		self.views=newviews


		#if self.private not in [0,1]:
		try:
			self.private=int(bool(self.private))
		except:
			raise ValueError,"Invalid value for private; must be 0 or 1"





class Record(DictMixin):
	"""This class encapsulates a single database record. In a sense this is an instance
	of a particular RecordDef, however, note that it is not required to have a value for
	every field described in the RecordDef, though this will usually be the case.

	To modify the params in a record use the normal obj[key]= or update() approaches.
	Changes are not stored in the database until commit() is called. To examine params,
	use obj[key]. There are a few special keys, handled differently:
	creator,creationtime,permissions,comments

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

	param_special = set(["recid","rectype","comments","creator","creationtime","permissions"])#"dbid",#"uri"
	 	# dbid # "modifyuser","modifytime",


	def __init__(self, d=None, ctx=None, **kwargs):
		"""Normally the record is created with no parameters, then setContext is called by the
		Database object. However, for initializing from a dictionary (ie - XMLRPC call, this
		may be done at initiailization time."""

		if not d:
			d = {}
		#kwargs.update(d or {})
		## recognized keys
		# recid -- 32 bit integer recordid (within the current database)
		# rectype -- name of the RecordDef represented by this Record
		# comments -- a List of comments records
		# creator -- original creator of the record
		# creationtime -- creation date
		# dbid -- dbid where this record resides (any other dbs have clones)
		# params -- a Dictionary containing field names associated with their data
		# permissions -- permissions for
			# read access, comment write access, full write access,
			# and administrative access. Each element is a tuple of
			# user names or group id's,
			# Group -3 includes any logged in user,
			# Group -4 includes any user (anonymous)

		self.recid = d.get('recid')
		self.rectype = d.get('rectype')
		#self.dbid = d.get('dbid',None)
		#self.uri = d.get('uri',None)
		
		self.__comments = d.get('comments',[])
		self.__creator = d.get('creator')
		self.__creationtime = d.get('creationtime')
		self.__permissions = d.get('permissions',((),(),(),()))
		self.__params = {}

		self.__ptest = [0,0,0,0]

		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext

		self.__context = None # Validated access context
		#ctx = ctx or kwargs.get('context', ctx)
		if ctx:
			self.setContext(ctx)

		for key in set(d.keys()) - self.param_special:
			self[key] = d[key]
			
			

	#################################
	# validation methods
	#################################


	def validationwarning(self, msg):
		print "Validation warning: %s: %s"%(self.recid, msg)
			
			
	def validate(self, orec={}, warning=0, params=[]):
		if not self.__context.db:
			self.validationwarning("No context; cannot validate")
			return
			
		validators = [
			self.validate_recid,
			self.validate_rectype,
			self.validate_comments,
			self.validate_creator,
			self.validate_creationtime,
			self.validate_permissions
			#self.validate_permissions_users
			]

		for i in validators:
			try:
				i(orec)
			except (TypeError, ValueError), inst:
				if warning:
					self.validationwarning("%s: %s"%(i.func_name, inst))
				else:
					raise ValueError, "%s: %s"%(i.func_name, inst)

		self.validate_params(orec, warning=warning, params=params)
				
				
				
	def validate_recid(self, orec={}):
		try:
			if self.recid != None:
				self.recid = int(self.recid)
				# negative recids are used as temp ids for new records
				# ian todo: make a NewrecordRecid int class or something similar..
				#if self.recid < 0:
				#	raise ValueError

		except (TypeError, ValueError):
			raise ValueError, "recid must be positive integer"

		if self.recid != orec.get("recid") and orec.get("recid") != None:
			raise ValueError, "recid cannot be changed (%s != %s)"%(self.recid,orec.get("recid"))



	def validate_rectype(self, orec={}):

		self.rectype = str(self.rectype)
		
		if self.rectype in ["",None]:
			raise ValueError, "rectype must not be empty"

		if self.rectype not in self.__context.db.getrecorddefnames(self.__context.ctxid,self.__context.host):
			raise ValueError, "invalid rectype %s"%(self.rectype)

		if self.rectype != orec.get("rectype") and orec.get("rectype") != None:
			raise ValueError, "rectype cannot be changed (%s != %s)"%(self.rectype,orec.get("rectype"))



	def validate_comments(self, orec={}):
		# validate comments
		users=[]
		dates=[]
		newcomments=[]
		for i in self.__comments:
			try:
				users.append(i[0])
				dates.append(i[1])
				newcomments.append((str(i[0]),str(i[1]),unicode(i[2])))
			except:
				raise ValueError, "invalid comment format: %s; skipping"%(i)
				
		usernames = set(self.__context.db.getusernames(ctxid=self.__context.ctxid,host=self.__context.host))		
		if set(users) - usernames:
			raise ValueError, "invalid users in comments: %s"%(set(users) - usernames)		
			
		# validate date formats
		#for i in dates:
		#	pass

		self.__comments = newcomments


	def validate_creator(self, orec={}):
		return
		self.__creator=str(self.__creator)
		try:
			self.__context.db.getuser(self.__creator, filt=0, ctxid=self.__context.ctxid, host=self.__context.host)
		except:
			raise ValueError, "invalid creator: %s"%(self.__creator)
		
		
	def validate_creationtime(self, orec={}):
		# validate creation time format
		return


	def validate_permissions(self, orec={}):
		self.__permissions = self.__checkpermissionsformat(self.__permissions)


	def validate_permissions_users(self,orec={}):
		u = set()
		users = set(self.__context.db.getusernames(ctxid=self.__context.ctxid,host=self.__context.host))
		for j in self.__permissions: u |= set(j)
		# todo: get group names...
		u -= set([0,-1,-2,-3,-4])
		if u-users:
			raise ValueError, "undefined users: %s"%",".join(map(str, u-users))
			

	def validate_uri(self, orec={}, warning=0):
		pass
		
		
			
	def validate_params(self, orec={}, warning=0, params=[]):

		# restrict by params if given
		p2 = set(self.__params.keys()) & set(params or self.__params.keys())
		if not p2:
			return
		
		vtm = emen2.Database.subsystems.datatypes.VartypeManager()	

		pds = self.__context.db.getparamdefs(p2)
		newpd = {}
		exceptions = []
		
		for param,pd in pds.items():
			#print "\tValidate param: %s: %s (vartype: %s, property: %s)"%(pd.name, self[param], pd.vartype, pd.property)
			try:
				newpd[param] = self.validate_param(self[param], pd, vtm)
			except (ValueError,KeyError), inst:
				#print traceback.print_exc()
				exceptions.append("parameter: %s (%s): %s"%(param,pd.vartype,str(inst)))
								
		for i in exceptions:
			self.validationwarning(i)
		
		if exceptions and not warning:
			raise ValueError, "Validation exceptions:\n\t%s\n\n"%"\n\t".join(exceptions)
							
				
		self.__params.update(newpd)



	def validate_param(self, value, pd, vtm):

		v = vtm.validate(pd, value, db=self.__context.db, ctxid=self.__context.ctxid, host=self.__context.host)

		if v != value and v != None:
			self.validationwarning("parameter: %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v))

		return v


	def changedparams(self,orec={}):
		"""difference between two records"""
		
		allkeys = set(self.keys() + orec.keys())
		return set(filter(lambda k:self.get(k) != orec.get(k), allkeys))




	#################################
	# pickle methods
	#################################

	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it

		#odict["_Record__oparams"]={}
		try: del odict['_Record__ptest']
		except:	pass

		try: del odict['_Record__context']
		except:	pass

		# filter out values that are None
		odict["_Record__params"] = dict(filter(lambda x:x[1]!=None,odict["_Record__params"].items()))

		return odict


	def __setstate__(self,dict):
		"""restore unpickled values to defaults after unpickling"""
		#g.debug("unpickle: _Record__oparams")
		#if dict["_Record__oparams"]	!= {}:
		#	g.debug(dict["recid"],dict["_Record__oparams"])

		# this is properly handled by putrecord
		# try:
		# 	p=dict["_Record__params"]
		#		dict["_Record__params"]={}
		#		for i,j in p.items():
		#			if j!=None and j!="None" : dict["_Record__params"][i.lower()]=j
		#except:
		#	traceback.g.debug(=sys.stdout))
		#dict["rectype"]=dict["rectype"].lower()

		#if dict.has_key("localcpy") :
		#	del dict["localcpy"]
		#	self.__ptest=[1,1,1,1]
		#else:
		#	self.__dict__.update(dict)
		#	self.__ptest=[0,0,0,0]
		
		self.__dict__.update(dict)
		self.__ptest=[0,0,0,0]
		self.__context=None



	#################################
	# repr methods
	#################################

	def __unicode__(self):
		"A string representation of the record"
		ret=["%s (%s)\n"%(str(self.recid),self.rectype)]
		for i,j in self.items():
			ret.append(u"%12s:	%s\n"%(str(i),unicode(j)))
		return u"".join(ret)

	def __str__(self):
		return self.__unicode__().encode('utf-8')

	def __repr__(self):
		return "<Record id: %s recdef: %s at %x>" % (self.recid, self.rectype, id(self))

	def json_equivalent(self):
		return self.items_dict()



	#################################
	# mapping methods;
	#		DictMixin provides the remainder
	#################################

	def __getitem__(self, key):
		"""Behavior is to return None for undefined params, None is also
		the default value for existant, but undefined params, which will be
		treated identically"""
		
		key = str(key).strip().lower()

		if key == "comments":
			return self.__comments
		elif key == "recid":
			return self.recid
		elif key == "rectype":
			return self.rectype
		elif key == "creator":
			return self.__creator
		elif key == "creationtime":
			return self.__creationtime
		elif key == "permissions":
			return self.__permissions
		#elif key == "uri":
		#	return self.uri

		return self.__params.get(key)


	def __setitem__(self, key, value):
		"""This and 'update' are the primary mechanisms for modifying the params in a record
		Changes are not written to the database until the commit() method is called!"""
		# comments may include embedded field values if the user has full write access

		key = str(key).strip().lower()

		# replaced by validation...
		# if value == "None":
		# 			value = None
		# 		try:
		# 			if len(value) == 0:
		# 				value = None
		# 		except:
		# 			pass
		
		# special params have get/set handlers
		if key not in self.param_special:
			if not self.writable():
				raise SecurityError, "Insufficient permissions to change param %s"%key
			self.__params[key] = value

		elif key == 'comments':
			self.addcomment(value)

		elif key == 'permissions':
			self.setpermissions(value)
			
		else:
			#raise Exception # ValueError or KeyError?
			self.validationwarning("cannot set item %s in this way"%key)


	def __delitem__(self,key):
		key = str(key).strip().lower()

		if key not in self.param_special and self.__params.has_key(key):
			del self.__params[key]
			#self.__setitem__(key,None)
		else:
			raise KeyError,"Cannot delete key %s"%key


	def keys(self):
		"""All retrievable keys for this record"""
		#return tuple(self.__params.keys())+tuple(self.param_special)
		return self.__params.keys() + list(self.param_special)


	def has_key(self,key):
		if str(key).strip().lower() in self.keys(): return True
		return False


	def get(self, key, default=None):
		return DictMixin.get(self, key) # or default




	#################################
	# record methods
	#################################

	# these can only be used on new records before commit for now...
	def adduser(self, level, users, reassign=1):
			
		p = [set(x) for x in self.__permissions]
		level=int(level)
		if -1 < level < 3:
			raise Exception, "Invalid permissions level; 0 = read, 1 = comment, 2 = write, 3 = owner"

		if not hasattr(users,"__iter__"):
			users=[users]

		# Strip out "None"
		users=set(filter(lambda x:x != None, users))

		if not users:
			return

		if reassign:
			p = [i-users for i in p ]

		p[level] |= users
		
		p[0] -= p[1] | p[2] | p[3]
		p[1] -= p[2] | p[3]
		p[2] -= p[3]
		
		self.setpermissions(p)
		#self.__permissions = tuple([tuple(i) for i in p])


	def removeuser(self, users):
				
		p=[set(x) for x in self.__permissions]
		if not hasattr(users,"__iter__"):
			users=[users]
		users=set(users)
		p=[i-users for i in p]
		
		self.setpermissions(p)
		#self.__permissions = tuple([tuple(i) for i in p])


	def __partitionints(self, i):
		ints=[]
		strs=[]
		for j in i:
			try:
				ints.append(int(j))
			except:
				strs.append(j)
		return ints + strs


	def __checkpermissionsformat(self, value):
		if value == None:
			value = ((),(),(),())

		try:
			if len(value) != 4:
				raise ValueError
			for j in value:
				if not hasattr(value,"__iter__"):
					raise ValueError
		except ValueError:
			self.validationwarning("invalid permissions format: %s"%value)
			raise

		r = [self.__partitionints(i) for i in value]

		return tuple(tuple(x) for x in r)
		

	def setpermissions(self, value):
		
		if not self.isowner():
			raise SecurityError, "Insufficient permissions to change permissions"
		
		self.__permissions = self.__checkpermissionsformat(value)
		
	

	def addcomment(self, value):
		
		if not self.commentable():
			raise SecurityError, "Insufficient permissions to add comment"
		
		if not isinstance(value,basestring):
			self.validationwarning("addcomment: invalid comment: %s"%value)
			return

		d = parseparmvalues(value,noempty=1)[1]

		if d.has_key("comments") or d.has_key("permissions"):
			self.validationwarning("addcomment: cannot set comments/permissions inside a comment")				
			return

		# now update the values of any embedded params
		# if setting value fails, comment won't be added; record can still be committed, perhaps with partial changes,
		# 	but validation would catch anything the user could not normally set otherwise
		for i,j in d.items():
			self[i] = j

		self.__comments.append((self.__context.user,time.strftime(emen2.Database.database.TIMESTR),value))	# store the comment string itself



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self.__params.keys()
		


	def setContext(self, ctx):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work to see if a ctx(a user context) has the permission to access/write to this record
		"""

		self.__context = ctx

		if not self.__creator:
			self.__creator = ctx.user
			self.__creationtime = time.strftime(emen2.Database.database.TIMESTR)
			self.__permissions = ((),(),(),(ctx.user,))

		# test for owner access in this context.
		if (-1 in ctx.groups):
			self.__ptest = [1,1,1,1]
			return

		# we use the sets module to do intersections in group membership
		# note that an empty set tests false, so u1&p1 will be false if
		# there is no intersection between the 2 sets
		p1 = set(self.__permissions[0]+self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		p2 = set(self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		p3 = set(self.__permissions[2]+self.__permissions[3])
		p4 = set(self.__permissions[3])
		u1 = set(ctx.groups)

		# ian: fixed ctx.groups to include these implicit groups
		#+[-4] all users are permitted group -4 access
		#if ctx.user!=None : u1.add(-3)		# all logged in users are permitted group -3 access

		# test for read permission in this context
		if (-2 in u1 or ctx.user in p1 or u1 & p1):
			self.__ptest[0] = 1
		else:
			raise SecurityError,"Permission Denied: %s"%self.recid

		# test for comment write permission in this context
		if (ctx.user in p2 or u1 & p2): self.__ptest[1] = 1

		# test for general write permission in this context
		if (ctx.user in p3 or u1 & p3): self.__ptest[2] = 1

		# test for administrative permission in this context
		if (ctx.user in p4 or u1 & p4): self.__ptest[3] = 1


	def items_dict(self):
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information"""
		ret={}
		ret.update(self.__params)
		for i in self.param_special:
			try:
				ret[i]=self[i]
			except:
				pass
		return ret


	def commit(self):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putrecord will fail"""
		return self.__context.db.putrecord(self, ctxid=self.__context.ctxid, host=self.__context.host)


	def isowner(self):
		return self.__ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the given context"""
		return self.__ptest[2]


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return self.__ptest[1]

