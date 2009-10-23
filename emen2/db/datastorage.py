import time
import re
import traceback
import math
import UserDict


import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

# validation
import emen2.Database.subsystems
import emen2.Database.subsystems.dataobject
import emen2.Database.database
from emen2.Database.dataobjects.paramdef import ParamDef
from emen2.Database.dataobjects.recorddef import RecordDef, parseparmvalues

class Binary(emen2.Database.subsystems.dataobject.BaseDBObject):
	validators = []

	@property
	def attr_user(self): return set(["filename","filepath", "uri","recid","modifyuser","modifytime"])

	@property
	def attr_admin(self): return set(["creator","creationtime","name"])

	attr_vartypes = {
		"recid":"int",
		"filename":"string",
		"uri":"string",
		"modifyuser":"user",
		"modifytime":"datetime",
		"creator":"user",
		"creationtime":"datetime",
		"name":"str"
		}


	# name is BDO
	def init(self, d): pass

	def validate(self): pass





class Record(object, UserDict.DictMixin):
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

	param_special = set(["recid","rectype","comments","creator","creationtime","permissions"])
	cleared_fields = set(["viewcache"])
		#"groups",
		#"dbid",#"uri"
	 	# dbid # "modifyuser","modifytime",


	def __init__(self, d=None, ctx=None, **kwargs):
		"""Normally the record is created with no parameters, then setContext is called by the
		Database object. However, for initializing from a dictionary (ie - XMLRPC call, this
		may be done at initiailization time."""

		if not d: d = {}
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

		self.viewcache = {}
		self.__comments = d.get('comments',[])
		self.__creator = d.get('creator')
		self.__creationtime = d.get('creationtime')


		self.__permissions = d.get('permissions',((),(),(),()))
		#self.__groups = d.get('groups',set())


		self.__params = {}

		self.__ptest = [0,0,0,0]

		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext

		self.__ctx = None # Validated access context

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
		for field in self.cleared_fields:
			setattr(self, field, None)

		if not self.__ctx.db:
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

		if not self.rectype:
			raise ValueError, "rectype must not be empty"

		self.rectype = unicode(self.rectype)

		if self.rectype not in self.__ctx.db.getrecorddefnames():
			raise ValueError, "invalid rectype %s"%(self.rectype)

		if self.rectype != orec.get("rectype") and orec.get("rectype") != None:
			raise ValueError, "rectype cannot be changed (%s != %s)"%(self.rectype,orec.get("rectype"))



	def validate_comments(self, orec={}):
		# validate comments
		users=[]
		dates=[]
		newcomments=[]

		for i in self.__comments:
			#try:
			users.append(i[0])
			dates.append(i[1])
			newcomments.append((unicode(i[0]),unicode(i[1]),unicode(i[2])))
			#except:
			#	raise ValueError, "invalid comment format: %s; skipping"%(i)

		usernames = set(self.__ctx.db.getusernames())

		if set(users) - usernames:
			raise ValueError, "invalid users in comments: %s"%(set(users) - usernames)

		# validate date formats
		#for i in dates:
		#	pass

		self.__comments = newcomments


	def validate_creator(self, orec={}):
		self.__creator = unicode(self.__creator)
		return

		try:
			self.__ctx.db.getuser(self.__creator, filt=0)
		except:
			raise ValueError, "invalid creator: %s"%(self.__creator)



	def validate_creationtime(self, orec={}):
		# validate creation time format
		self.__creationtime = unicode(self.__creationtime)



	def validate_permissions(self, orec={}):
		self.__permissions = self.__checkpermissionsformat(self.__permissions)


	def validate_permissions_users(self,orec={}):
		users = set(self.__ctx.db.getusernames())
		u = set(reduce(operator.concat, self.__permissions))
		if u - users:
			raise ValueError, "undefined users: %s"%",".join(map(unicode, u-users))


	def validate_params(self, orec={}, warning=0, params=[]):

		# restrict by params if given
		p2 = set(self.__params.keys()) & set(params or self.__params.keys())
		if not p2:
			return

		vtm = emen2.Database.subsystems.datatypes.VartypeManager()

		pds = self.__ctx.db.getparamdefs(p2)
		newpd = {}
		exceptions = []

		for param,pd in pds.items():
			#print "\tValidate param: %s: %s (vartype: %s, property: %s)"%(pd.name, self[param], pd.vartype, pd.property)
			try:
				newpd[param] = self.validate_param(self.__params.get(param), pd, vtm)
			except (ValueError,KeyError), inst:
				newpd[param] = self.__params.get(param)
				#print traceback.print_exc()
				exceptions.append("parameter: %s (%s): %s"%(param,pd.vartype,unicode(inst)))

		for i in exceptions:
			self.validationwarning(i)

		if exceptions and not warning:
			raise ValueError, "Validation exceptions:\n\t%s\n\n"%"\n\t".join(exceptions)

		self.__params = newpd
		#self.__params.update(newpd)



	def validate_param(self, value, pd, vtm):

		v = vtm.validate(pd, value, db=self.__ctx.db)

		if v != value and v != None:
			self.validationwarning("parameter: %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v))

		return v


	def changedparams(self,orec=None):
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

		try: del odict['_Record__ctx']
		except:	pass

		# filter out values that are None
		odict["_Record__params"] = dict(filter(lambda x:x[1]!=None,odict["_Record__params"].items()))

		return odict


	def __setstate__(self, dict):
		"""restore unpickled values to defaults after unpickling"""

		self.__dict__.update(dict)
		self.__ptest = [0,0,0,0]
		self.__ctx = None



	#################################
	# repr methods
	#################################

	def __unicode__(self):
		"A string representation of the record"
		ret=["%s (%s)\n"%(unicode(self.recid),self.rectype)]
		for i,j in self.items():
			ret.append(u"%12s:	%s\n"%(unicode(i),unicode(j)))
		return u"".join(ret)

	def __str__(self):
		return self.__unicode__().encode('utf-8')

	def __repr__(self):
		return "<Record id: %s recdef: %s at %x>" % (self.recid, self.rectype, id(self))


	def json_equivalent(self):
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information"""
		ret={}
		ret.update(self.__params)
		for i in self.param_special:
			try:
				ret[i]=self[i]
			except:
				pass
		return ret



	#################################
	# mapping methods;
	#		UserDict.DictMixin provides the remainder
	#################################

	def __getitem__(self, key):
		"""Behavior is to return None for undefined params, None is also
		the default value for existant, but undefined params, which will be
		treated identically"""

		key = unicode(key)

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
		#elif key == "groups":
		#	return self.__groups
		#elif key == "uri":
		#	return self.uri

		return self.__params.get(key)


	def __setitem__(self, key, value):
		"""This and 'update' are the primary mechanisms for modifying the params in a record
		Changes are not written to the database until the commit() method is called!"""
		# comments may include embedded field values if the user has full write access
		# replaced by validation...
		# if value == "None":
		# 			value = None
		# 		try:
		# 			if len(value) == 0:
		# 				value = None
		# 		except:
		# 			pass

		key = unicode(key)

		# special params have get/set handlers
		if key not in self.param_special:
			#if not self.writable():
			#	raise SecurityError, "Insufficient permissions to change param %s"%key
			self.__params[key] = value

		elif key == 'comments':
			self.addcomment(value)

		elif key == 'permissions':
			self.setpermissions(value)

		#elif key == 'groups':
		#	self.setgroups(value)

		else:
			#raise Exception # ValueError or KeyError?
			self.validationwarning("cannot set item %s in this way"%key)


	def __delitem__(self,key):

		key = unicode(key)

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
		if unicode(key) in self.keys(): return True
		return False


	def get(self, key, default=None):
		return UserDict.DictMixin.get(self, key, default) # or default




	#################################
	# record methods
	#################################

	# these can only be used on new records before commit for now...
	def adduser(self, level, users, reassign=1):

		level=int(level)

		p = [set(x) for x in self.__permissions]
		if not -1 < level < 4:
			raise Exception, "Invalid permissions level; 0 = read, 1 = comment, 2 = write, 3 = owner"

		if not hasattr(users,"__iter__"):
			users=[users]

		# Strip out "None"
		users = set(filter(lambda x:x != None, users))

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

		p = [set(x) for x in self.__permissions]
		if not hasattr(users,"__iter__"):
			users = [users]
		users = set(users)
		p = [i-users for i in p]

		self.setpermissions(p)
		#self.__permissions = tuple([tuple(i) for i in p])


	def __partitionints(self, i):
		ints = []
		strs = []
		for j in i:
			try:
				ints.append(int(j))
			except:
				strs.append(unicode(j))
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

		value = [self.__partitionints(i) for i in value]
		return tuple(tuple(x) for x in value)


	def setpermissions(self, value):

		if not self.isowner():
			raise SecurityError, "Insufficient permissions to change permissions"

		self.__permissions = self.__checkpermissionsformat(value)



	def setgroups(self, value):
		if not self.isowner():
			raise SecurityError, "Insufficient permissions to change permissions"
		self.__groups = set(value)


	def addgroup(self, value):
		self.__groups.add(value)


	def removegroup(self, value):
		try:
			self.__groups.remove(value)
		except:
			pass


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

		value = unicode(value)
		self.__comments.append((unicode(self.__ctx.username),unicode(emen2.Database.database.gettime()),value))
		# store the comment string itself



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self.__params.keys()



	def setContext(self, ctx=None):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work to see if a ctx(a user context) has the permission to access/write to this record
		"""

		self.__ctx = ctx

		if self.__ctx == None:
			raise SecurityError, "No ctx!"

		if not self.__creator:
			self.__creator = unicode(self.__ctx.username)
			self.__creationtime = self.__ctx.db.gettime()
			self.__permissions = ((),(),(),(unicode(self.__ctx.username),))

		# print "setContext: ctx.groups is %s"%ctx.groups

		# test for owner access in this context.
		if self.__ctx.checkreadadmin():
			self.__ptest = [1,1,1,1]
			return

		# we use the sets module to do intersections in group membership
		# note that an empty set tests false, so u1&p1 will be false if
		# there is no intersection between the 2 sets
		p1 = set(self.__permissions[0]+self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		p2 = set(self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		p3 = set(self.__permissions[2]+self.__permissions[3])
		p4 = set(self.__permissions[3])
		u1 = set(self.__ctx.groups)

		# ian: fixed ctx.groups to include these implicit groups
		#+[-4] all users are permitted group -4 access
		#if ctx._user!=None : u1.add(-3)		# all logged in users are permitted group -3 access

		# test for read permission in this context
		#if (-2 in u1 or ctx._user in p1 or u1 & p1):
		if (-2 in u1 or self.__ctx.username in p1 or u1 & p1):
			self.__ptest[0] = 1
		else:
			raise SecurityError,"Permission Denied: %s"%self.recid

		# test for comment write permission in this context
		if (self.__ctx.username in p2 or u1 & p2): self.__ptest[1] = 1

		# test for general write permission in this context
		if (self.__ctx.username in p3 or u1 & p3): self.__ptest[2] = 1

		# test for administrative permission in this context
		if (self.__ctx.username in p4 or u1 & p4): self.__ptest[3] = 1



	def commit(self):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putrecord will fail"""
		return self.__ctx.db.putrecord(self)


	def isowner(self):
		return self.__ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the given context"""
		return self.__ptest[2]


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return self.__ptest[1]

