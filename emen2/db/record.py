import UserDict
import operator
import weakref
import emen2.db.datatypes
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.config
g = emen2.db.config.g()

from . import validators


#	This class encapsulates a single database record. In a sense this is an instance
#	of a particular RecordDef, however, note that it is not required to have a value for
#	every field described in the RecordDef, though this will usually be the case.
#
#	To modify the params in a record use the normal obj[key]= or update() approaches.
#	Changes are not stored in the database until commit() is called. To examine params,
#	use obj[key]. There are a few special keys, handled differently:
#	creator,creationtime,permissions,comments,history,parents,children,groups
#
#	Record instances must ONLY be created by the Database class through retrieval or
#	creation operations. self.__ctx will store information about security and
#	storage for the record.
#
#	Mechanisms for changing existing params are a bit complicated. In a sense, as in a
#	physical lab notebook, an original value can never be changed, only superceded.
#	All records have a 'magic' field called 'comments', which is an extensible array
#	of text blocks with immutable entries. 'comments' entries can contain new field
#	definitions, which will supercede the original definition as well as any previous
#	comments. Changing a field will result in a new comment being automatically generated
#	describing and logging the value change.
#
#	From a database standpoint, this is rather odd behavior. Such tasks would generally be
#	handled with an audit log of some sort. However, in this case, as an electronic
#	representation of a Scientific lab notebook, it is absolutely necessary
#	that all historical values are permanently preserved for any field, and there is no
#	particular reason to store this information in a separate file. Generally speaking,
#	such changes should be infrequent.
#
#	Naturally, as with anything in Python, anyone with code-level access to the database
#	can override this behavior by changing 'params' directly rather than using
#	the supplied access methods. There may be appropriate uses for this when constructing
#	a new Record before committing changes back to the database.

#class Record(object, UserDict.DictMixin):

def strip(cls):
	dct = {}
	for x,y in cls.__dict__.iteritems():
		if '__' in x:
			dct[x.split('__',1)[1]] = y
		else:
			dct[x] = y
	return type(cls.__name__, cls.__bases__, dct)



class Record(emen2.db.dataobject.BaseDBInterface):
	attr_user = set([])
	attr_admin = set([])

	param_special = set(["recid", "rectype", "comments", "creator", "creationtime", "permissions", "history", "groups"])
	cleared_fields = set(["viewcache"])


	def init(self, _d=None, **_k):
		"""Normally the record is created with no parameters, then setContext is called by the
		Database object. However, for initializing from a dictionary (ie - XMLRPC call, this
		may be done at initiailization time.

		recognized keys:
		  recid -- 32 bit integer recordid (within the current database)
		  rectype -- name of the RecordDef represented by this Record
		  comments -- a List of comments records
		  creator -- original creator of the record
		  creationtime -- creation date
		  dbid -- dbid where this record resides (any other dbs have clones)
		  params -- a Dictionary containing field names associated with their data
		  permissions -- permissions for
			  read access, comment write access, full write access,
			  and administrative access. Each element is a tuple of
			  user names or group id's,
		"""

		_k.update(_d or {})


		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext
		self.__ptest = [True,True,True,True]

		self.recid = _k.pop('recid', None)
		self.rectype = _k.pop('rectype', None)

		self.__creator = _k.pop('creator', None)
		self.__creationtime = _k.pop('creationtime', None)

		self.__comments = _k.pop('comments',[])
		self.__history = _k.pop('history',[])

		self.__params = {}

		self.__permissions = _k.pop("permissions", ((),(),(),()))
		self.__groups = set(_k.pop('groups',[]))

		for key in set(_k.keys()) - self.param_special:
			self[key] = _k[key]

		# ian: are we initializing a new record?
		ctx = self.__ctx
		if self.__ctx and self.recid < 0:
			self.__creator = unicode(ctx.username)
			self.__creationtime = emen2.db.database.gettime()
			if ctx.username != "root":
				self.adduser(ctx.username, 3)




	#################################
	# validation methods
	#################################


	def validate(self, orec=None, warning=False, params=[]):

		if not orec:
			orec = {}

		for field in self.cleared_fields:
			setattr(self, field, None)

		if not self.__ctx:
			self.validationwarning("No context; cannot validate", warning=True)
			return
			
		elif not self.__ctx.db:
			self.validationwarning("No context; cannot validate", warning=True)
			return

		#self.validate_auto()
		validators = [
			self.validate_recid,
			self.validate_rectype,
			self.validate_comments,
			self.validate_history,
			self.validate_creator,
			self.validate_creationtime,
			self.validate_permissions,
			self.validate_permissions_users
		]

		for i in validators:
			i(orec, warning=warning)
			# self.validationwarning("%s: %s"%(i.func_name, inst), e=inst, warning=warning)

		self.validate_params(orec, warning=warning, params=params)


	def changedparams(self, orec=None):
		"""difference between two records"""
		if not orec: orec = {}
		allkeys = set(self.keys() + orec.keys())
		return set(filter(lambda k:self.get(k) != orec.get(k), allkeys))




	#################################
	# pickle methods
	#################################

	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_Record__ptest'] = None
		odict['_Record__ctx'] = None
		# filter out values that are None
		odict["_Record__params"] = dict(filter(lambda x:x[1]!=None, odict["_Record__params"].items()))

		return odict


	def __setstate__(self, dict):
		"""restore unpickled values to defaults after unpickling"""
		self.__dict__.update(dict)
		self.__ptest = [False, False, False, False]
		self.__ctx = None
		# ian: todo: temp patch, remove...
		try: self.__history
		except: self.__history = []



	def upgrade(self):
		pass


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
		try:
			return "<Record id: %s recdef: %s at %x>" % (self.recid, self.rectype, id(self))
		except:
			return object.__repr__(self)


	def json_equivalent(self):
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information. For use with demjson"""
		ret={}
		ret.update(self.__params)
		for i in self.param_special:
			try: ret[i]=self[i]
			except: pass
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

		result = self.__params.get(key)
		if   key == "comments":
			result = self.__comments
		elif key == "recid":
			result = self.recid
		elif key == "rectype":
			result = self.rectype
		elif key == "creator":
			result = self.__creator
		elif key == "creationtime":
			result = self.__creationtime
		elif key == "permissions":
			result = self.__permissions
		elif key == "groups":
			result = self.__groups
		elif key == "history":
			result = self.__history

		return result


	def __setitem__(self, key, value):
		"""This and 'update' are the primary mechanisms for modifying the params in a record
		Changes are not written to the database until the commit() method is called!"""

		key = unicode(key)

		# special params have get/set handlers
		if key not in self.param_special:
			if not self.writable():
				raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change param %s"%key
			self.__params[key] = value

		elif key == 'comments':
			self.addcomment(value)

		elif key == 'permissions':
			self.setpermissions(value)

		elif key == 'groups':
			self.setgroups(value)

		else:
			self.validationwarning("Cannot set item %s in this way"%key, warning=True)


	def __delitem__(self,key):

		key = unicode(key)

		if key not in self.param_special:
			self.__params[key] = None
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
		ret = UserDict.DictMixin.get(self, key)
		if ret == None:
			return default
		return ret
		#return UserDict.DictMixin.get(self, key, default=default)




	#################################
	# record methods
	#################################

	# these can only be used on new records before commit for now...
	def adduser(self, users, level=0, reassign=False):

		if not users: return

		if not hasattr(users,"__iter__"):
			users=[users]

		level=int(level)

		p = [set(x) for x in self.__permissions]
		#if not -1 < level < 4:
		#	raise Exception, "Invalid permissions level; 0 = read, 1 = comment, 2 = write, 3 = owner"

		users = set(users) - set(['root'])

		if reassign:
			p = [i-users for i in p ]

		p[level] |= users

		p[0] -= p[1] | p[2] | p[3]
		p[1] -= p[2] | p[3]
		p[2] -= p[3]

		self.setpermissions(p)


	def addumask(self, umask, reassign=False):
		if not umask:
			return

		p = [set(x) for x in self.__permissions]
		umask = [set(x) for x in umask]
		users = reduce(set.union, umask)

		if reassign:
			p = [i-users for i in p ]

		p = [j|k for j,k in zip(p,umask)]
		p[0] -= p[1] | p[2] | p[3]
		p[1] -= p[2] | p[3]
		p[2] -= p[3]

		self.setpermissions(p)


	def removeuser(self, users):
		p = [set(x) for x in self.__permissions]
		if not hasattr(users,"__iter__"):
			users = [users]
		users = set(users)
		p = [i-users for i in p]

		self.setpermissions(p)


	def __checkpermissionsformat(self, value):
		if value == None:
			value = ((),(),(),())

		try:
			if len(value) != 4:
				raise ValueError
			r = tuple(tuple([unicode(j) for j in x.__iter__()]) for x in value)

		except (ValueError, AttributeError), e:
			self.validationwarning("Invalid permissions format")
			return

		return r


	def setpermissions(self, value):
		if not self.isowner():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change permissions"

		self.__permissions = self.__checkpermissionsformat(value)


	def setgroups(self, groups):
		if not self.isowner():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change permissions"
		self.__groups = set(groups)


	def addgroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.__groups |= set(groups)


	def removegroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.__groups -= set(groups)


	def addcomment(self, value):
		if not self.commentable():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to add comment"

		if not isinstance(value,basestring):
			self.validationwarning("addcomment: invalid comment: %s"%value)
			return

		d = emen2.db.dataobjects.recorddef.parseparmvalues(value, noempty=1)[1]

		if d.has_key("comments") or d.has_key("permissions"):
			self.validationwarning("addcomment: cannot set comments/permissions inside a comment")
			return

		# now update the values of any embedded params
		# if setting value fails, comment won't be added; record can still be committed, perhaps with partial changes,
		# 	but validation would catch anything the user could not normally set otherwise
		for i,j in d.items():
			self[i] = j

		value = unicode(value)

		self.__comments.append((unicode(self.__ctx.username), unicode(emen2.db.database.gettime()), value))
		# store the comment string itself


	def _addhistory(self, param, value):
		if not param:
			raise Exception, "Unable to add item to history log"
		self.__history.append((unicode(self.__ctx.username), unicode(emen2.db.database.gettime()), param, value))



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self.__params.keys()



	def setContext(self, ctx=None):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work to see if a ctx(a user context) has the permission to access/write to this record
		"""

		#if self.__ctx == None:
		#	return

		self.__ctx = ctx #weakref.proxy(ctx)

		# g.debug('setContext:: context.db type == %r' % self._ctx.db)
		# test for owner access in this context.
		if self.__ctx.checkreadadmin():
			self.__ptest = [True, True, True, True]
			return

		self.__ptest = [self.__ctx.username in level for level in self.__permissions]


		for group in self.__groups & self.__ctx.groups:
			self.__ptest[self.__ctx.grouplevels[group]] = True


		if not any(self.__ptest):
			raise emen2.db.exceptions.SecurityError,"Permission Denied: %s"%self.recid


		# raise emen2.db.exceptions.SecurityError, "No ctx!"

		# g.log.msg('LOG_DEBUG', "setContext: ctx.groups is %s"%ctx.groups)

		# # we use the sets module to do intersections in group membership
		# # note that an empty set tests false, so u1&p1 will be false if
		# # there is no intersection between the 2 sets
		# p1 = set(self.__permissions[0]+self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		# p2 = set(self.__permissions[1]+self.__permissions[2]+self.__permissions[3])
		# p3 = set(self.__permissions[2]+self.__permissions[3])
		# p4 = set(self.__permissions[3])
		#
		# # test for read permission in this context
		# if (self.__ctx.username in p1): self.__ptest[0] = 1
		# else:
		#
		# # test for comment write permission in this context
		# if (self.__ctx.username in p2): self.__ptest[1] = 1
		#
		# # test for general write permission in this context
		# if (self.__ctx.username in p3): self.__ptest[2] = 1
		#
		# # test for administrative permission in this context
		# if (self.__ctx.username in p4): self.__ptest[3] = 1




	def commit(self):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putrecord will fail"""
		return self.__ctx.db.putrecord(self)


	def isowner(self):
		return self.__ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the given context"""
		return any(self.__ptest[2:])


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return any(self.__ptest[1:])


	# def validationwarning(self, msg, e=None, warning=False):
	# 	"""Raise a warning or exception during validation
	# 	
	# 	@param msg Text
	# 	
	# 	@keyparam e Exception
	# 	@keyparam warning Raise the exception if False, otherwise just inform
	# 	
	# 	"""
	# 
	# 	if e == None:
	# 		e = ValueError
	# 	if warning:
	# 		g.log.msg("LOG_WARNING", "Validation warning: %s: %s"%(self.recid, msg))
	# 	elif e:
	# 		raise e, msg
	# 

# ian: not ready yet..
# @Record.register_validator
# @emen2.db.validators.Validator.make_validator
# class RecordValidator(emen2.db.dataobject.Validator):
	


	def validate_recid(self, orec=None, warning=False):
		if not orec: orec = {}

		try:
			if self.recid != None:
				self.recid = int(self.recid)
				# negative recids are used as temp ids for new records
				# ian todo: make a NewrecordRecid int class or something similar..
				#if self.recid < 0:
				#	raise ValueError

		except (TypeError, ValueError), inst:
			self.validationwarning("recid must be positive integer")


		if self.recid != orec.get("recid") and orec.get("recid") != None:
			self.validationwarning("recid cannot be changed (%s != %s)"%(self.recid,orec.get("recid")))


	def validate_rectype(self, orec=None, warning=False):
		if not orec: orec = {}

		if not self.rectype:
			self.validationwarning("rectype must not be empty")

		self.rectype = unicode(self.rectype)

		if self.rectype not in self.__ctx.db.getrecorddefnames():
			self.validationwarning("invalid rectype %s"%(self.rectype))

		if self.rectype != orec.get("rectype") and orec.get("rectype") != None:
			self.validationwarning("rectype cannot be changed (%s != %s)"%(self.rectype,orec.get("rectype")))


	def validate_comments(self, orec=None, warning=False):
		if not orec: orec = {}

		# validate comments
		users=[]
		dates=[]
		newcomments=[]

		if isinstance(self.__comments, basestring):
			self.__comments = [(unicode(self.__ctx.username), unicode(emen2.db.database.gettime()), self.__comments)]

		# ian: filter comments for empties..
		for i in filter(None, self.__comments or []):
			try:
				users.append(i[0])
				dates.append(i[1])
				newcomments.append((unicode(i[0]),unicode(i[1]),unicode(i[2])))
			except Exception, inst:
				self.validationwarning("invalid comment format: %s"%(i), e=inst, warning=warning)
				newcomments.append((unicode(self.__ctx.username), unicode(emen2.db.database.gettime()), "Error with comment: %s"%i))


		if users:
			usernames = set(self.__ctx.db.getusernames())
			if set(users) - usernames:
				self.validationwarning("invalid users in comments: %s"%(set(users) - usernames), warning=warning)

		# validate date formats
		#for i in dates:
		#	pass

		self.__comments = newcomments


	def validate_history(self, orec=None, warning=False):
		if not orec: orec = {}
		return

		# ian: todo: activate
		users=set([i[0] for i in self.__history])
		dates=set([i[1] for i in self.__history])
		if users:
			if users - set(self.__ctx.db.getusernames()):
				self.validationwarning("invalid users in history: %s"%(set(users) - usernames), warning=warning)


	def validate_creator(self, orec=None, warning=False):
		if not orec: orec = {}

		self.__creator = unicode(self.__creator)
		return

		# ian: todo: activate
		if self.__creator != orec.get("creator"):
			self.validationwarning("cannot change creator", warning=warning)
		try:
			self.__ctx.db.getuser(self.__creator, filt=0)
		except:
			self.validationwarning("invalid creator: %s"%(self.__creator))


	def validate_creationtime(self, orec=None, warning=False):
		if not orec: orec = {}

		# validate creation time format
		self.__creationtime = unicode(self.__creationtime)
		#if self.__creationtime != orec.get("creationtime"):
		#	self.validationwarning("cannot change creationtime", warning=warning)


	def validate_permissions(self, orec=None, warning=False):
		if not orec: orec = {}

		try:
			self.__permissions = self.__checkpermissionsformat(self.__permissions)
		except Exception, inst:
			self.validationwarning("invalid permissions: %s"%self.__permissions, warning=warning)


	def validate_permissions_users(self, orec=None, warning=False):
		if not orec: orec = {}

		users = set(self.__ctx.db.getusernames())
		u = set(reduce(operator.concat, self.__permissions))
		if u - users:
			self.validationwarning("undefined users in permissions: %s"%",".join(map(unicode, u-users)))


	def validate_params(self, orec=None, warning=False, params=None):
		if not orec:
			orec = {}

		# restrict by params if given
		p2 = self.__params.keys()
		if params:
			p2 = set(self.__params.keys()) & set(params)

		if not p2:
			return

		vtm = emen2.db.datatypes.VartypeManager()

		pds = self.__ctx.db.getparamdefs(p2)
		newpd = {}
		exceptions = []

		for param,pd in pds.items():
			try:
				newpd[param] = self.validate_param(self.__params.get(param), pd, vtm, warning=warning)

			except Exception, inst: #(ValueError,KeyError,IndexError)
				self.addcomment("Validation error: param %s, value '%s' %s"%(param, self.__params.get(param),type(self.__params.get(param))))
				exceptions.append("parameter: %s (%s): %s"%(param,pd.vartype,unicode(inst)))

		for e in exceptions:
			self.validationwarning(e, warning=warning)

		self.__params = newpd



	def validate_param(self, value, pd, vtm, warning=False):

		v = vtm.validate(pd, value, db=self.__ctx.db)

		if v != value and v != None:
			self.validationwarning("parameter: %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v), warning=True)

		return v

