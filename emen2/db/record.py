import UserDict
import collections
import operator
import weakref
import copy

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
#	creation operations. self._ctx will store information about security and
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


def make_orec():
	return {}

def make_cache():
	return {'usernames':None, 'recdefs':{}, 'paramdefs':{}}



class Record(emen2.db.dataobject.BaseDBInterface):
	attr_user = set([])
	param_special = set(["recid", "rectype", "comments", "creator", "creationtime", "permissions", "history", "groups"])
	cleared_fields = set(["viewcache"])


	def __init__(self, *args, **kwargs):
		# these need to be defined for setContext to work..
		self.__permissions = ((),(),(),())
		self.__groups = set()
		super(Record, self).__init__(*args, **kwargs)
		
		
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
		if self._ctx and self.recid < 0:
			self.__creator = unicode(self._ctx.username)
			self.__creationtime = emen2.db.database.gettime()
			if self._ctx.username != "root":
				self.adduser(self._ctx.username, 3)







	#################################
	# pickle methods
	#################################

	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_Record__ptest'] = None
		# filter out values that are None
		odict["_Record__params"] = dict(filter(lambda x:x[1]!=None, odict["_Record__params"].items()))

		return odict


	# def __setstate__(self, dict):
	# 	"""restore unpickled values to defaults after unpickling"""
	# 	self.__dict__.update(dict)
	# 	self.__ptest = [False, False, False, False]
	# 	# ian: todo: temp patch, remove...
	# 	try: self.__history
	# 	except: self.__history = []



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
		"""Returns a dictionary of current values, __dict__ wouldn't return the correct information. For use with JSON"""
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

			# Log changes
			if self.recid >= 0:
				self._addhistory(key)

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

		if value == None:
			return

		if not isinstance(value, basestring):
			self.validationwarning("addcomment: invalid comment: %s"%value)
			return

		d = emen2.db.recorddef.parseparmvalues(value)[1]
		if d.has_key("comments"):
			self.validationwarning("addcomment: cannot set comments inside a comment")
			return

		# now update the values of any embedded params
		# if setting value fails, comment won't be added; record can still be committed, perhaps with partial changes,
		# 	but validation would catch anything the user could not normally set otherwise
		if self.recid > -1:
			for i,j in d.items():
				self[i] = j

		value = unicode(value)

		self.__comments.append((unicode(self._ctx.username), unicode(emen2.db.database.gettime()), value))
		# store the comment string itself


	def _addhistory(self, param):
		if not param:
			raise Exception, "Unable to add item to history log"
		self.__history.append((unicode(self._ctx.username), unicode(emen2.db.database.gettime()), param, self.__params.get(param)))



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self.__params.keys()



	def setContext(self, ctx=None):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work to see if a ctx(a user context) has the permission to access/write to this record
		"""


		self._ctx = ctx #weakref.proxy(ctx)
		if self._ctx == None:
			return

		# test for owner access in this context.
		if self._ctx.checkreadadmin():
			self.__ptest = [True, True, True, True]
			return


		self.__ptest = [self._ctx.username in level for level in self.__permissions]

		for group in self.__groups & self._ctx.groups:
			self.__ptest[self._ctx.grouplevels[group]] = True


		if not any(self.__ptest):
			raise emen2.db.exceptions.SecurityError,"Permission Denied: %s"%self['recid']



	def commit(self):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putrecord will fail"""
		nrec = self._ctx.db.putrecord(self)
		self.recid = nrec
		return nrec


	def isowner(self):
		return self.__ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the given context"""
		return any(self.__ptest[2:])


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return any(self.__ptest[1:])

	
	def ptest(self):
		return self.__ptest


	def revision(self, revision=None):
		"""This will return information about the record's revision history"""


		history = copy.copy(self.__history)
		comments = copy.copy(self.__comments)
		comments.append((self.get('creator'), self.get('creationtime'), 'Created'))
		paramcopy = {}

		bydate = collections.defaultdict(list)
		
		for i in filter(lambda x:x[1]>=revision, history):
			bydate[i[1]].append([i[0], i[2], i[3]])

		for i in filter(lambda x:x[1]>=revision, comments):
			bydate[i[1]].append([i[0], None, i[2]])
			
		revs = sorted(bydate.keys(), reverse=True)

		for rev in revs:				
			for item in bydate.get(rev, []):
				# user, param, oldval
				if item[1] == None:
					continue
				if item[1] in paramcopy.keys():
					newval = paramcopy.get(item[1])
				else:
					newval = self.get(item[1])
	
				paramcopy[item[1]] = copy.copy(item[2])				
				# item[2] = newval

		return bydate, paramcopy
		


	# ian: not ready yet..
	# @Record.register_validator
	# @emen2.db.validators.Validator.make_validator
	# class RecordValidator(emen2.db.dataobject.Validator):

	#################################
	# validation methods
	#################################


	def validate(self, orec=None, warning=False, params=[], cache=None):

		# Setup the two caching dicts
		orec = orec or make_orec()
		cache = cache or make_cache()

		for field in self.cleared_fields:
			setattr(self, field, None)

		if not self._ctx:
			self.validationwarning("No context; cannot validate", warning=True)
			return

		elif not self._ctx.db:
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
			i(orec=orec, warning=warning, cache=cache)
			# self.validationwarning("%s: %s"%(i.func_name, inst), e=inst, warning=warning)

		self.validate_params(orec, warning=warning, params=params)



	def changedparams(self, orec=None, cache=None):
		"""difference between two records"""
		allkeys = set(self.keys() + orec.keys())
		return set(filter(lambda k:self.get(k) != orec.get(k), allkeys))



	def validate_recid(self, orec=None, warning=False, cache=None):
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


	def validate_rectype(self, orec=None, warning=False, cache=None):
		orec = orec or make_orec()
		cache = cache or make_cache()

		if not self.rectype:
			self.validationwarning("rectype must not be empty")

		self.rectype = unicode(self.rectype)
		
		rd = cache['recdefs'].get(self.rectype)
		if not rd:
			rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
			cache['recdefs'][self.rectype] = rd

		if self.rectype != orec.get("rectype") and orec.get("rectype") != None:
			self.validationwarning("rectype cannot be changed (%s != %s)"%(self.rectype,orec.get("rectype")))


	def validate_comments(self, orec=None, warning=False, cache=None):
		orec = orec or make_orec()
		cache = cache or make_cache()

		# validate comments
		users=[]
		dates=[]
		newcomments=[]

		if isinstance(self.__comments, basestring):
			self.__comments = [(unicode(self._ctx.username), unicode(emen2.db.database.gettime()), self.__comments)]

		# ian: filter comments for empties..
		for i in filter(None, self.__comments or []):
			try:
				users.append(i[0])
				dates.append(i[1])
				newcomments.append((unicode(i[0]),unicode(i[1]),unicode(i[2])))
			except Exception, inst:
				self.validationwarning("invalid comment format: %s"%(i), e=inst, warning=warning)
				newcomments.append((unicode(self._ctx.username), unicode(emen2.db.database.gettime()), "Error with comment: %s"%i))


		# ian: comment users are never set manually, so probably safe to skip this
		# if users:
		# 	usernames = set(self._ctx.db.getusernames())
		# 	if set(users) - usernames:
		# 		self.validationwarning("invalid users in comments: %s"%(set(users) - usernames), warning=warning)

		# validate date formats
		#for i in dates:
		#	pass

		self.__comments = newcomments


	def validate_history(self, orec=None, warning=False, cache=None):
		return

		# orec = orec or make_orec()
		# cache = cache or make_cache()
		# ian: skipping; see comments for validate_comments
		# users=set([i[0] for i in self.__history])
		# dates=set([i[1] for i in self.__history])
		# if users:
		# 	if users - set(self._ctx.db.getusernames()):
		# 		self.validationwarning("invalid users in history: %s"%(set(users) - usernames), warning=warning)


	def validate_creator(self, orec=None, warning=False, cache=None):
		self.__creator = unicode(self.__creator)
		return

		# orec = orec or make_orec()
		# cache = cache or make_cache()
		# ian: skipping; see comments for validate_comments
		# if self.__creator != orec.get("creator"):
		# 	self.validationwarning("cannot change creator", warning=warning)
		# try:
		# 	self._ctx.db.getuser(self.__creator, filt=0)
		# except:
		# 	self.validationwarning("invalid creator: %s"%(self.__creator))


	def validate_creationtime(self, orec=None, warning=False, cache=None):
		# validate creation time format
		self.__creationtime = unicode(self.__creationtime)
		
		# orec = orec or make_orec()
		# cache = cache or make_cache()		
		#if self.__creationtime != orec.get("creationtime"):
		#	self.validationwarning("cannot change creationtime", warning=warning)


	def validate_permissions(self, orec=None, warning=False, cache=None):
		try:
			self.__permissions = self.__checkpermissionsformat(self.__permissions)
		except Exception, inst:
			self.validationwarning("invalid permissions: %s"%self.__permissions, warning=warning)


	def validate_permissions_users(self, orec=None, warning=False, cache=None):
		orec = orec or make_orec()
		cache = cache or make_cache()

		usernames = cache.get('usernames')
		if usernames == None:
			usernames = self._ctx.db.getusernames()
			cache['usernames'] = usernames
		
		u = set(reduce(operator.concat, self.__permissions))
		if u - usernames:
			self.validationwarning("undefined users in permissions: %s"%",".join(map(unicode, u-usernames)))


	def validate_params(self, orec=None, warning=False, params=None, cache=None):
		orec = orec or make_orec()
		cache = cache or make_cache()

		# restrict by params if given
		p2 = self.__params.keys()
		if params:
			p2 = set(self.__params.keys()) & set(params)

		if not p2:
			return

		vtm = emen2.db.datatypes.VartypeManager()

		# ian: todo: find a way to cache these
		# pds = self._ctx.db.getparamdef(p2)		
		
		newpd = {}
		exceptions = []
		for param in p2:

			pd = cache['paramdefs'].get(param)
			if not pd:
				pd = self._ctx.db.getparamdef(param, filt=False)
				cache['paramdefs'][param] = pd

			try:
				value = self.__params.get(param)
				v = vtm.validate(pd, value, db=self._ctx.db)
				if v != value and v != None:
					self.validationwarning("parameter %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v), warning=True)
				newpd[pd.name] = v

			except Exception, inst: #(ValueError,KeyError,IndexError)
				self.addcomment("Validation error: param %s, value '%s' %s"%(param, self.__params.get(param),type(self.__params.get(param))))
				exceptions.append("parameter: %s (%s): %s"%(param,pd.vartype,unicode(inst)))
				

		for e in exceptions:
			self.validationwarning(e, warning=warning)

		rd = cache['recdefs'].get(self.rectype)
		if not rd:
			rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
			cache['recdefs'][self.rectype] = rd
		
		for param in rd.paramsR:
			if newpd.get(param) == None:
				self.validationwarning("%s is a required parameter"%(param), warning=warning)

		self.__params = newpd

