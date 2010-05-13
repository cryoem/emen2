import operator
import weakref

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import emen2.Database.datatypes
import emen2.Database.dataobject
import emen2.Database.exceptions
import emen2.Database.validators



class Record(emen2.Database.dataobject.BaseDBObject):
	"""
	This class encapsulates a single database record. In a sense this is an instance
	of a particular RecordDef, however, note that it is not required to have a value for
	every field described in the RecordDef, though this will usually be the case.

	To modify the params in a record use the normal obj[key]= or update() approaches.
	Changes are not stored in the database until commit() is called. To examine params,
	use obj[key]. There are a few special keys, handled differently:
	creator,creationtime,permissions,comments,history,parents,children,groups

	Record instances must ONLY be created by the Database class through retrieval or
	creation operations. self._ctx will store information about security and
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
	
	Some of these attributes are actually stored as hidden, but can be accessed with dictionary methods.
	
	@attr recid Integer ID for Record
	@attr rectype Associated RecordDef
	@attr comments List of comments; format is [[user, time, text], ...]
	@attr history History log; similar to comments: [[user, time, param, old value], ...]

	@attr permissions 4-Tuple of permissions. [[read users], [comment users], [write users], [owners]]
	@attr groups Set of groups

	@attr creationtime
	@attr creator
	
	"""


	attr_user = set([])
	param_special = set(["recid", "rectype", "comments", "creator", "creationtime", "permissions", "history", "groups"])
	cleared_fields = set(["viewcache"])


	def init(self, d=None):
		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext
		self.__ptest = [True,True,True,True]

		self.recid = d.pop('recid', None)
		self.rectype = d.pop('rectype', None)

		self.__creator = d.pop('creator', None)
		self.__creationtime = d.pop('creationtime', None)

		self.__comments = d.pop('comments',[])
		self.__history = d.pop('history',[])

		self.__params = {}

		self.__permissions = d.pop("permissions", ((),(),(),()))
		self.__groups = set(d.pop('groups',[]))

		for key in set(d.keys()) - self.param_special:
			self[key] = d[key]

		# ian: are we initializing a new record?
		if self._ctx and self.recid < 0:
			self.__creator = unicode(self._ctx.username)
			self.__creationtime = emen2.Database.database.gettime()
			if self._ctx.username != "root":
				self.adduser(self._ctx.username, 3)



	#################################
	# validation methods
	#################################


	def changedparams(self, orec=None):
		"""Difference between two records"""
		
		if not orec: orec = {}
		allkeys = set(self.keys() + orec.keys())
		return set(filter(lambda k:self.get(k) != orec.get(k), allkeys))




	#################################
	# pickle methods
	#################################

	def __getstate__(self):
		"""Context and other session-specific information should not be pickled"""

		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_ctx'] = None
		odict['_Record__ptest'] = None
		# filter out values that are None
		odict["_Record__params"] = dict(filter(lambda x:x[1]!=None, odict["_Record__params"].items()))
		return odict


	#################################
	# repr methods
	#################################


	def json_equivalent(self):
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information. For use with demjson"""

		ret={}
		ret.update(self.__params)
		for i in self.param_special:
			ret[i]=self[i]
		return ret



	#################################
	# mapping methods
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
		Changes are not written to the database until the record is committed!"""

		key = unicode(key)

		# special params have get/set handlers
		if key not in self.param_special:
			if not self.writable():
				raise emen2.Database.exceptions.SecurityError, "Insufficient permissions to change param %s"%key
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
		return self.__params.keys() + list(self.param_special)


	def has_key(self,key):
		if unicode(key) in self.keys():
			return True
		return False


	def get(self, key, default=None):
		ret = self.__getitem__(key)
		if ret == None:
			return default
		return ret


	def __unicode__(self):
		"A string representation of the record"
		ret = ["%s: %s (%s)\n"%(self.__class__.__name__, self.rectype, self.recid)]
		for key in self.keys():
			ret.append(u"%12s:	%s\n"%(key, self[key]))
		return u"".join(ret)


	#################################
	# record methods
	#################################

	# these can only be used on new records before commit for now...
	def adduser(self, users, level=0, reassign=False):
		"""Add a user with a specified permissions level.
		
		@attr users Single or iterable of users to give permissions

		@keyparam level Permissions level for this assignment. 0 (read) is default.
		@keyparam reassign If a user already has a higher set of permissions, reassign to this lower level

		"""

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
		"""Apply a mask of permissions
		
		@param umask 4-tuple of permissions to overlay
		
		@keyparam reassign If a user already has a higher set of permissions, reassign to this lower level
		
		"""

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
		"""Remove users from permissions
		
		@param users Single or iterable of users to remove from permissions
		
		"""
		
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
		"""Set permissions to a 4-tuple. Discards existing permissions.
		
		@param value New permissions, in standard 4-tuple format.
		
		"""
		
		if not self.isowner():
			raise emen2.Database.exceptions.SecurityError, "Insufficient permissions to change permissions"

		self.__permissions = self.__checkpermissionsformat(value)


	def setgroups(self, groups):
		"""Set groups. Discards existing groups.

		@param groups Iterable of groups
		
		"""
		
		if not self.isowner():
			raise emen2.Database.exceptions.SecurityError, "Insufficient permissions to change permissions"
		self.__groups = set(groups)


	def addgroup(self, groups):
		"""Add groups
		
		@param groups Single or iterable groups
		
		"""
		
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.__groups |= set(groups)


	def removegroup(self, groups):
		"""Remove groups
		
		@param groups Single or iterable groups

		"""
		
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.__groups -= set(groups)


	def addcomment(self, value):
		"""Add a comment to Record. This can be used to explain changes, make notes, or continue a dialog. Parameter values can be embedded with $$param=value format.
		
		@param value Comment
		
		"""
		
		
		if not self.commentable():
			raise emen2.Database.exceptions.SecurityError, "Insufficient permissions to add comment"

		if not isinstance(value,basestring):
			self.validationwarning("addcomment: invalid comment: %s"%value)
			return

		d = emen2.Database.recorddef.parseparmvalues(value, noempty=1)[1]

		if d.has_key("comments") or d.has_key("permissions"):
			self.validationwarning("addcomment: cannot set comments/permissions inside a comment")
			return

		# now update the values of any embedded params
		# if setting value fails, comment won't be added; record can still be committed, perhaps with partial changes,
		# 	but validation would catch anything the user could not normally set otherwise
		for i,j in d.items():
			self[i] = j

		value = unicode(value)

		self.__comments.append((unicode(self._ctx.username), unicode(emen2.Database.database.gettime()), value))
		# store the comment string itself


	def _addhistory(self, param, value):
		"""Append to history log. This can only be used internally by the database; other attempts will be discarded when committed."""
		
		if not param:
			raise Exception, "Unable to add item to history log"
		self.__history.append((unicode(self._ctx.username), unicode(emen2.Database.database.gettime()), param, value))



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		
		return self.__params.keys()



	def setContext(self, ctx=None):
		"""See base class"""
		
		self._ctx = ctx

		if self._ctx.checkreadadmin():
			self.__ptest = [True, True, True, True]
			return

		self.__ptest = [self._ctx.username in level for level in self.__permissions]

		for group in self.__groups & self._ctx.groups:
			self.__ptest[self._ctx.grouplevels[group]] = True

		if not any(self.__ptest):
			raise emen2.Database.exceptions.SecurityError,"Permission Denied: %s"%self.recid

		# raise Database.exceptions.SecurityError, "No ctx!"

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
		"""We intend to expand this functionality; for now this just calls db.putrecord in the current Context."""
		return self._ctx.db.putrecord(self)


	def isowner(self):
		"""Returns whether user has ownership level permissions in the current context"""
		return self.__ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the current context"""
		return any(self.__ptest[2:])


	def commentable(self):
		"""Returns whether the user has commenting privileges in the current context"""
		return any(self.__ptest[1:])


	def validationwarning(self, msg, e=None, warning=False):
		"""Raise a warning or exception during validation
		
		@param msg Text
		
		@keyparam e Exception
		@keyparam warning Raise the exception if False, otherwise just inform
		
		"""

		if e == None:
			e = ValueError
		if warning:
			g.log.msg("LOG_WARNING", "Validation warning: %s: %s"%(self.recid, msg))
		elif e:
			raise e, msg


# ian: not ready yet..
# @Record.register_validator
# @emen2.Database.dataobject.Validator.make_validator
# class RecordValidator(emen2.Database.dataobject.Validator):
	
	def validate(self, orec=None, warning=False, params=[]):
		"""Validate a record before committing"""

		if not orec:
			orec = {}

		for field in self.cleared_fields:
			setattr(self, field, None)

		if not self._ctx:
			self.validationwarning("No context; cannot validate", warning=True)
			return
			
		elif not self._ctx.db:
			self.validationwarning("No context; cannot validate", warning=True)
			return

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

		if self.rectype not in self._ctx.db.getrecorddefnames():
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
			self.__comments = [(unicode(self._ctx.username), unicode(emen2.Database.database.gettime()), self.__comments)]

		# ian: filter comments for empties..
		for i in filter(None, self.__comments or []):
			try:
				users.append(i[0])
				dates.append(i[1])
				newcomments.append((unicode(i[0]),unicode(i[1]),unicode(i[2])))
			except Exception, inst:
				self.validationwarning("invalid comment format: %s"%(i), e=inst, warning=warning)
				newcomments.append((unicode(self._ctx.username), unicode(emen2.Database.database.gettime()), "Error with comment: %s"%i))


		if users:
			usernames = set(self._ctx.db.getusernames())
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
			if users - set(self._ctx.db.getusernames()):
				self.validationwarning("invalid users in history: %s"%(set(users) - usernames), warning=warning)


	def validate_creator(self, orec=None, warning=False):
		if not orec: orec = {}

		self.__creator = unicode(self.__creator)
		return

		# ian: todo: activate
		if self.__creator != orec.get("creator"):
			self.validationwarning("cannot change creator", warning=warning)
		try:
			self._ctx.db.getuser(self.__creator, filt=0)
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

		users = set(self._ctx.db.getusernames())
		u = set(reduce(operator.concat, self.__permissions))
		if u - users:
			self.validationwarning("undefined users in permissions: %s"%",".join(map(unicode, u-users)))


	def validate_params(self, orec=None, warning=False, params=None):
		if not orec: orec = {}

		# restrict by params if given
		p2 = self.__params.keys()
		if params:
			p2 = set(self.__params.keys()) & set(params)

		if not p2:
			return

		vtm = emen2.Database.datatypes.VartypeManager()

		pds = self._ctx.db.getparamdefs(p2)
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

		v = vtm.validate(pd, value, db=self._ctx.db)

		if v != value and v != None:
			self.validationwarning("parameter: %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v), warning=True)

		return v

