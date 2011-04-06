# $Id$

import UserDict
import collections
import operator
import weakref
import copy
import re


import emen2.db.datatypes
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.config


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



# These are built-ins that we treat specially, and changes aren't logged.
param_special = set(["recid", "rectype", "comments", "creator", "creationtime", "modifyuser", "modifytime", "permissions", "history", "groups", "children", "parents"])

# These cannot be changed after they are set, or are set by the system
param_immutable = set(["recid", "rectype", "creator", "creationtime", "modifytime", "modifyuser", "history"])

# These are params to index for new records
param_new = set(["rectype", "creator", "creationtime", "permissions", "groups"])



def make_orec():
	return {}


def make_cache():
	return {'usernames':None, 'recdefs':{}, 'paramdefs':{}}



class Record(emen2.db.dataobject.BaseDBInterface):
	attr_user = set([])
	name = property(lambda s:s.recid)

	def __init__(self, *args, **kwargs):
		# these need to be defined for setContext to work..
		self.permissions = [[],[],[],[]]
		self.groups = set()
		super(Record, self).__init__(*args, **kwargs)
		
		
	def init(self, _d=None, **_k):
		_k.update(_d or {})

		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext
		self._ptest = [True,True,True,True]

		self.recid = _k.pop('recid', None)
		self.rectype = _k.pop('rectype', None)

		self.creator = _k.pop('creator', None)
		self.creationtime = _k.pop('creationtime', None)
		self.modifyuser = _k.pop('modifyuser', None)
		self.modifytime = _k.pop('modifytime', None)

		self.comments = _k.pop('comments',[])
		self.history = _k.pop('history',[])

		self.permissions = _k.pop("permissions",[[],[],[],[]])
		self.groups = set(_k.pop('groups',[]))		

		# (slowly) moving to new style..
		self.parents = set(_k.pop('parents',[]))		
		self.children = set(_k.pop('children',[]))

		self.uri = set(_k.pop('uri',[]))

		self._params = {}

		for key in set(_k.keys()) - param_special:
			self[key] = _k[key]

		if self._ctx and self.recid < 0:
			self.creator = unicode(self._ctx.username)
			self.creationtime = emen2.db.database.gettime()
			if self._ctx.username != "root":
				self.adduser(self._ctx.username, 3)




	#################################
	# pickle methods
	#################################

	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_ptest'] = None
		odict['_ctx'] = None
		# filter out values that are None
		# odict["_params"] = dict(filter(lambda x:x[1]!=None, odict["_params"].items()))

		return odict


	def __setstate__(self, d):
		# Backwards compatibility..
		if not d.has_key('_params'):			
			d["modifyuser"] = d["_Record__params"].pop("modifyuser", None)
			d["modifytime"] = d["_Record__params"].pop("modifytime", None)
			d["uri"] = d["_Record__params"].pop("uri", None)

			d["_params"] = d["_Record__params"]
			d["history"] = d["_Record__history"]
			d["comments"] = d["_Record__comments"]
			d["permissions"] = d["_Record__permissions"]
			d["groups"] = d["_Record__groups"]

			d["creator"] = d["_Record__creator"]
			d["creationtime"] = d["_Record__creationtime"]
			d["parents"] = set()
			d["children"] = set()

			for i in ["_Record__ptest", 
				"_Record__ptest", 
				"_Record__params", 
				"_Record__history", 
				"_Record__comments", 
				"_Record__permissions", 
				"_Record__groups", 
				"_Record__creator", 
				"_Record__creationtime"]:
				try:
					del d[i]
				except:
					pass		

		return self.__dict__.update(d)




	def upgrade(self):
		pass


	#################################
	# repr methods
	#################################

	def __unicode__(self):
		"A string representation of the record"
		ret = ["%s (%s)\n"%(unicode(self.recid),self.rectype)]
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
		ret = {}
		ret.update(self._params)
		for i in param_special:
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

		if key in param_special:
			return getattr(self, key, None)
		else:		
			return self._params.get(key)


	def __setitem__(self, key, value):
		"""This and 'update' are the primary mechanisms for modifying the params in a record
		Changes are not written to the database until the commit() method is called!"""

		if key == "comments":
			print "setitem comments"
			return self._addcomment(value)

		if not self.writable():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change param %s"%key

		# Special params have get/set handlers
		if key not in param_special:
			self._params[key] = value

		elif key == 'permissions':
			self.setpermissions(value)

		elif key == 'groups':
			self.setgroups(value)
			
		elif key == 'parents':
			self.parents = value
		
		elif key == 'children':
			self.children = value

		else:
			self.validationwarning("Cannot set item %s in this way"%key, warning=True)


	def __delitem__(self,key):

		if key not in param_special:
			self.params[key] = None
		else:
			raise KeyError,"Cannot delete key %s"%key


	def keys(self):
		"""All retrievable keys for this record"""
		#return tuple(self._params.keys())+tuple(param_special)
		return self._params.keys() + list(param_special)


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

		if not users:
			return

		if not hasattr(users,"__iter__"):
			users=[users]

		level=int(level)

		p = [set(x) for x in self.permissions]
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

		p = [set(x) for x in self.permissions]
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
		p = [set(x) for x in self.permissions]
		if not hasattr(users,"__iter__"):
			users = [users]
		users = set(users)
		p = [i-users for i in p]

		self.setpermissions(p)


	def setpermissions(self, value):
		if not self.isowner():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change permissions"

		value = [[unicode(y) for y in x] for x in value]
		if len(value) != 4:
			raise ValueError, "Invalid permissions format: %s"%value
			
		self.permissions = value


	def setgroups(self, groups):
		if not self.isowner():
			raise emen2.db.exceptions.SecurityError, "Insufficient permissions to change permissions"
		self.groups = set(groups)


	def addgroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.groups |= set(groups)


	def removegroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		self.groups -= set(groups)


	def _addcomment(self, value, t=None):
		t = t or emen2.db.database.gettime()
	
		if value == None:
			return
		
		newcomments = []	
		if hasattr(value, "__iter__"):
			check = [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in value]
			existing = [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in self.comments]
			for c in check:
				if c not in existing:
					newcomments.append(c[2])
		else:
			newcomments.append(unicode(value))

		for value in newcomments:
			d = {}
			if not value.startswith("LOG"): # legacy fix..
				d = emen2.db.recorddef.parseparmvalues(value)[1]

			if d.has_key("comments"):
				self.validationwarning("Cannot set comments inside a comment")
				return
						
			if not self.commentable():
				raise emen2.db.exceptions.SecurityError, "Insufficient permissions to add comment"

			# now update the values of any embedded params
			# if setting value fails, comment won't be added; record can still be committed, perhaps with partial changes,
			# 	but validation would catch anything the user could not normally set otherwise
			for i,j in d.items():
				self[i] = j

			# store the comment string itself
			self.comments.append((unicode(self._ctx.username), unicode(t), unicode(value)))


	def _addhistory(self, param, t=None):
		t = t or emen2.db.database.gettime()
		if not param:
			raise Exception, "Unable to add item to history log"
		self.history.append((unicode(self._ctx.username), unicode(t), unicode(param), self._params.get(param)))



	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self._params.keys()



	def setContext(self, ctx=None, filt=False):
		"""This method may ONLY be used directly by the Database class. Constructing your
		own context will not work to see if a ctx(a user context) has the permission to access/write to this record
		"""
		
		self._ctx = ctx #weakref.proxy(ctx)
		if self._ctx == None:
			return

		# test for owner access in this context.
		if self._ctx.checkreadadmin():
			self._ptest = [True, True, True, True]
			return True

		self._ptest = [self._ctx.username in level for level in self.permissions]

		for group in self.groups & self._ctx.groups:
			self._ptest[self._ctx.grouplevels[group]] = True

		if not filt and not any(self._ptest):
			raise emen2.db.exceptions.SecurityError,"Permission Denied: %s"%self['recid']

		return self._ptest[0]


	def commit(self):
		"""This will commit any changes back to permanent storage in the database, until
		this is called, all changes are temporary. host must match the context host or the
		putrecord will fail"""
		nrec = self._ctx.db.putrecord(self)
		self.recid = nrec
		return nrec


	def isowner(self):
		return self._ptest[3]


	def writable(self):
		"""Returns whether this record can be written using the given context"""
		return any(self._ptest[2:])


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return any(self._ptest[1:])

	
	def ptest(self):
		return self._ptest


	def revision(self, revision=None):
		"""This will return information about the record's revision history"""

		history = copy.copy(self.history)
		comments = copy.copy(self.comments)
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
		


	#################################
	# validation methods
	#################################

	def validate(self, d, warning=False, clone=False, vtm=False, t=None):
		vtm = vtm or emen2.db.datatypes.VartypeManager(db=self._ctx.db)
		t = t or emen2.db.database.gettime()
		cp = set()		

		for param, value in d.items():
			if self.get(param) == d.get(param):
				# print "Unchanged param %s, skipping"%param
				continue

			cachekey = vtm.get_cache_key('paramdef', param)
			hit, pd = vtm.check_cache(cachekey)
			if not hit:
				pd = self._ctx.db.getparamdef(param, filt=False)
				vtm.store(cachekey, pd)

			if pd.get('immutable') or pd.name in param_immutable:
				# print "Skipping immutable param: ", pd.name
				continue

			# Validate
			try:
				v = vtm.validate(pd, value)
			except Exception, inst:
				if warning or clone:
					v = value
					print "Warning: ignored validation error: %s"%inst	
				else:
					raise
					
				
			if self.get(param) == v:
				continue

			if v != value:
				self.validationwarning("Parameter %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v), warning=True)
			
			# Log
			if pd.name not in param_special:
				self._addhistory(pd.name, t=t)

			# print "Setting %s, %s %s -> %s %s"%(pd.name, self.get(param), type(self.get(param)), v, type(v))
			
			# check to keep times in sync..
			if pd.name == "comments":
				self._addcomment(v, t=t)
			else:
				self[pd.name] = v

			# print "new value -> ", self[pd.name]
			cp.add(pd.name)
			
			
		# param_immutable is checked above, so don't need to add it back.
		if self.recid < 0:
			cp |= param_new	
			
		# Update to anything but groups/permissions triggers modify time
		if cp - set(["permissions","groups"]):
			self.__dict__["modifytime"] = unicode(t)
			self.__dict__["modifyuser"] = unicode(self._ctx.username)
			cp.add("modifytime")
			cp.add("modifyuser")


		# If a record is being cloned, it forces history/comments/create/modify
		if clone:
			cp |= param_new
			self.__dict__["comments"] = d.comments
			self.__dict__["history"] = d.history
			self.__dict__["creator"] = d.creator
			self.__dict__["creationtime"] = d.creationtime
			self.__dict__["modifyuser"] = d.modifyuser
			self.__dict__["modifytime"] = d.modifytime				


		# Check for required parameters
		cachekey = vtm.get_cache_key('recorddef', self.rectype)
		hit, rd = vtm.check_cache(cachekey)
		if not hit:
			rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
			vtm.store(cachekey, rd)

		for param in rd.paramsR:
			if self.get(param) == None:
				self.validationwarning("%s is a required parameter"%(param), warning=warning)
												
		return cp
			
	

			
	def changedparams(self, orec=None, cache=None):
		"""difference between two records"""
		allkeys = set(self.keys() + orec.keys())
		return set(filter(lambda k:self.get(k) != orec.get(k), allkeys))

			
		

	# def validate_params(self, orec=None, warning=False, params=None, cache=None):
	# 	orec = orec or make_orec()
	# 	cache = cache or make_cache()
	# 
	# 	# restrict by params if given
	# 	p2 = self._params.keys()
	# 	if params:
	# 		p2 = set(self._params.keys()) & set(params)
	# 
	# 	if not p2:
	# 		return
	# 
	# 	vtm = emen2.db.datatypes.VartypeManager(db=self._ctx.db)		
	# 	newpd = {}
	# 	exceptions = []
	# 	for param in p2:
	# 
	# 		pd = cache['paramdefs'].get(param)
	# 		if not pd:
	# 			pd = self._ctx.db.getparamdef(param, filt=False)
	# 			cache['paramdefs'][param] = pd
	# 
	# 		try:
	# 			value = self._params.get(param)
	# 			v = vtm.validate(pd, value)
	# 			if v != value and v != None:
	# 				self.validationwarning("Parameter %s (%s) changed during validation: %s '%s' -> %s '%s' "%(pd.name,pd.vartype,type(value),value,type(v),v), warning=True)
	# 			newpd[pd.name] = v
	# 
	# 		except Exception, inst: #(ValueError,KeyError,IndexError)
	# 			self.addcomment("Validation error: param %s, value '%s' %s"%(param, self._params.get(param),type(self._params.get(param))))
	# 			exceptions.append("Parameter: %s (%s): %s"%(param,pd.vartype,unicode(inst)))
	# 			
	# 
	# 	for e in exceptions:
	# 		self.validationwarning(e, warning=warning)
	# 
	# 	rd = cache['recdefs'].get(self.rectype)
	# 	if not rd:
	# 		rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
	# 		cache['recdefs'][self.rectype] = rd
	# 
	# 	# for param in rd.paramsA:
	# 	#	if self.recid >= 0 and not ctx.checkadmin():
	# 	# 		only admins can set this..
	# 	
	# 	for param in rd.paramsR:
	# 		if newpd.get(param) == None:
	# 			self.validationwarning("%s is a required parameter"%(param), warning=warning)
	# 
	# 	self._params = newpd



__version__ = "$Revision$".split(":")[1][:-1].strip()
