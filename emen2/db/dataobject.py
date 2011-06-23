# $Id$
import re
from abc import ABCMeta, abstractmethod, abstractproperty
from UserDict import DictMixin
import collections
import copy
import re
import traceback
import operator

import emen2.db.config
g = emen2.db.config.g()


class BaseDBObject(object, DictMixin):
	__metaclass__ = ABCMeta

	# Protected params are keytype, creator, creationtime, modifytime, modifyuser, uri, and name
	# name is required during init; uri can also be provided during init, but can't be changed afterwards
	param_all = set(['children', 'parents', 'keytype', 'creator', 'creationtime', 'modifytime', 'modifyuser', 'uri', 'name'])
	param_required = set()
	keytype = property(lambda s:s.getkeytype())

	#######################################
	# Interface definition

	def init(self, d):
		"""Hook for subclass init"""
		pass


	def validate(self, vtm=None, t=None):
		pass


	# End interface definition
	########################################

	def __init__(self, _d=None, **_k):
		"""Accept either a dictionary named '_d' or keyword arguments.
		Remove the ctx and use it for setContext.
		See the Class docstring for what arguments are accepted.
		"""

		# Copy input and kwargs into one dict
		_d = dict(_d or {})
		_d.update(_k)
		p = {}

		# Temporary setContext
		ctx = _d.pop('ctx', None)
		t = _d.pop('t', None)
		self.__dict__['_ctx'] = ctx
		vtm, t = self._vtmtime(t=t) # get time/user

		# Validate the name -- the only always required parameter for all DBOs
		p['name'] = self.validate_name(_d.pop('name', None))

		# Base parameters
		p['creator'] = self._ctx.username
		p['creationtime'] = t
		p['modifyuser'] = self._ctx.username
		p['modifytime'] = t

		# Other parameters
		p['uri'] = unicode(_d.pop('uri', '')) or None
		p['children'] = set()
		p['parents'] = set()

		# Directly update these base params
		self.__dict__.update(p)

		# Check that we can create this type of record
		self.validate_create()

		# Subclass init
		self.init(_d)

		# Set the context
		self.setContext(ctx)

		# Update with the remaining params
		self.update(_d)


	def getkeytype(self):
		return self.__class__.__name__.lower()


	def setContext(self, ctx):
		"""Set permissions and create reference to active database."""
		self.__dict__['_ctx'] = ctx


	def __unicode__(self):
		"""A string representation of the record"""
		ret = ["%s\n"%(self.__class__.__name__)]
		for i,j in self.items():
			ret.append(u"%12s:	%s\n"%(unicode(i),unicode(j)))
		return u"".join(ret)


	def __str__(self):
		return self.__unicode__().encode('utf-8')


	def __repr__(self):
		return "<%s %s at %x>" % (self.__class__.__name__, self.name, id(self))


	def clone(self, update, vtm=None, t=None):
		self.vw(msg='Warning! Only an admin may clone items!', check=self._ctx.checkadmin())
		vtm, t = self._vtmtime(vtm, t)
		cp = set()

		# Make a copy of the protected items
		# Usually: creator, creationtime, modifyuser, modifytime, uri, name, keytype
		protected = {}
		skip = self.param_required | set(['name', 'keytype', 'uri'])

		for k,v in update.items():
			if k not in self.param_all or k in skip:
				continue
			elif k == 'comments':
				# Comments has a _set_comments, but it works differently
				pass
			elif getattr(self, '_set_%s'%k, None):
				continue
			if v:
				protected[k] = v

		# Set items in the normal way
		for k,v in update.items():
			cp |= self.__setitem__(k, v, vtm=vtm, t=t)

		# print "Updating %s with protected:"%self.name, protected.keys()
		self.__dict__.update(protected)
		cp |= set(protected.keys())

		return cp


	def update(self, update, vtm=None, t=None):
		vtm, t = self._vtmtime(vtm, t)
		cp = set()

		# Make sure to pass in t=t to keep all the times in sync
		for k,v in update.items():
			cp |= self.__setitem__(k, v, vtm=vtm, t=t)

		# ed, changed return type from cp to self
		#     I checked grep, this shouldn't effect anything
		return self



	#################################
	# Mapping methods. These may be changed if you want to implement special behavior,
	#	e.g. records["permissions"] = [...]
	#		-> self._set_permissions(key, value)
	#################################
	def __getattr__(self, name):
		return object.__getattribute__(self, name)

	# Behave like dict.get(key) instead of db[key]
	def __getitem__(self, key, default=None):
		if key in self.param_all:
			return getattr(self, key, default)
		elif default:
			return default


	def get(self, key, default=None):
		return self.__getitem__(key, default)


	def __delitem__(self, key):
		raise AttributeError, 'Key deletion not allowed'


	def has_key(self,key):
		return key in self.param_all


	def keys(self):
		return list(self.param_all)


	def changedparams(self, item=None):
		"""Differences between two items"""
		allkeys = set(self.keys() + item.keys())
		return set(filter(lambda k:self.get(k) != item.get(k), allkeys))



	##########################
	# Setters
	##########################

	# Put everything through setitem for validation/logging/etc..
	def __setattr__(self, key, value):
		return self.__setitem__(key, value)


	def __setitem__(self, key, value, vtm=None, t=None):
		"""Validate and set an attribute or key."""
		cp = set()
		if self.get(key) == value:
			return cp

		# Find a setter method
		setter = getattr(self, '_set_%s'%key, None)
		if setter:
			pass
		elif key in self.param_all:
			# These cannot be directly modified (not even by admin, unless cloning)
			return cp
		else:
			# Setter for unknown params
			setter = self._setoob

		# Validate
		vtm, t = self._vtmtime(vtm, t)
		value = self.validate_param(key, value, vtm=vtm)

		# The setter might return multiple items that were updated
		# For instance, comments can update other params
		cp |= setter(key, value, vtm=vtm, t=t)

		# Only permissions, groups, and links do not trigger a modifytime update
		if cp - set(['permissions', 'groups', 'parents', 'children']):
			self.__dict__['modifytime'] = t
			self.__dict__['modifyuser'] = self._ctx.username
			cp.add('modifytime')
			cp.add('modifyuser')

		# Return all the params that changed
		return cp


	def _seterror(self, key, *args, **kwargs):
		"""Immutable params"""
		self.error("Cannot set param %s in this way"%key, warning=True)
		return set()


	# Record will override this
	def _setoob(self, key, value, vtm=None, t=None):
		"""Handle params not found in self.param_all"""
		return self._seterror(key, value)


	def _set(self, key, value, check=None, vtm=None, t=None):
		"""Actually set a value. See self.vw() for check argument"""
		self.vw(key, check)
		self.__dict__[key] = value
		return set([key])


	##########################
	# Set parents / children
	##########################

	def _set_children(self, key, value, vtm=None, t=None):
		return self._set(key, set(value or []))


	def _set_parents(self, key, value, vtm=None, t=None):
		return self._set(key, set(value or []))


	def _set_uri(self, key, value, vtm=None, t=None):
		return self._set(key, value)


	##########################
	# Permissions
	#	Two basic permissions are defined: owner and writable
	#	PermissiionsDBObject has a more complete permissions model
	##########################

	def isowner(self):
		if self._ctx.checkadmin():
			return True

		if self._ctx.username == getattr(self, 'creator', None):
			return True

		return self._ctx.username == getattr(self, 'owner', None)


	def writable(self, key=None):
		"""Returns whether this record can be written using the given context"""
		return self.isowner()


	##########################
	# Other methods
	##########################

	def delete(self):
		self.error("No permission to delete.")


	def rename(self):
		self.error("No permission to rename.")


	##########################
	# Pickle methods
	##########################

	def __getstate__(self):
		"""Context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		for i in ['_ctx', '_ptest', '_userrec', '_groups', '_displayname', '_vtm', '_t']:
			odict.pop(i, None)
		return odict



	##########################
	# Utility methods
	##########################

	def _vtmtime(self, vtm=None, t=None):
		"""Utility method to check/get a vartype manager and the current time."""
		vtm = vtm or emen2.db.datatypes.VartypeManager(db=self._ctx.db)
		t = t or emen2.db.database.gettime()
		return vtm, t


	# Verify write
	def vw(self, key=None, check=None, msg=None):
		"""Convenience method for checking permissions and printing
		error messages.

		Typical use:
		self.vw('permissions', check=self.isowner())
		self.vw('vartype', check=self._ctx.checkadmin())

		@keyword key Param to use error message
		@keyword check None: Perform a basic .writable() check. False: Raise SecurityError. True: OK
		@keyword msg Alternative error message
		"""
		if check == None:
			check = self.writable()
		if not check:
			msg = msg or "Insufficient permissions to change param %s"%key
			self.error(msg, e=emen2.db.exceptions.SecurityError)



	##########################
	# Validation and error control
	##########################

	# Check that we have permissions to create this type of item
	def validate_create(self):
		"""Can we create this type of item?"""
		if not self._ctx.checkcreate():
			raise emen2.db.exceptions.SecurityError, "No creation privileges"


	# This is the main mechanism for validation.
	def validate_param(self, key, value, vtm=None):
		"""Validate a single param value"""

		# Check the cache for the param
		vtm, t = self._vtmtime(vtm=vtm)
		cachekey = vtm.get_cache_key('paramdef', key)
		hit, pd = vtm.check_cache(cachekey)

		# ian: todo: critical: no validation for params that do not have
		#	a ParamDef if they are listed in self.param_all
		if not hit and key in self.param_all:
			return value

		# ... otherwise, raise an Exception if the param isn't found.
		if not hit:
			pd = self._ctx.db.getparamdef(key, filt=False)
			vtm.store(cachekey, pd)

		# Is it an immutable param?
		if self.name and pd.get('immutable'):
			self.error('Cannot change immutable param %s'%pd.name)

		# Validate
		v = vtm.validate(pd, value)

		# Issue a warning if param changed during validation
		if v != value:
			self.error(
				"Parameter %s (%s) changed during validation: %s '%s' -> %s '%s' "%
				(pd.name, pd.vartype, type(value), value, type(v), v), warning=True)

		return v


	def validate_name(self, name):
		"""Validate the name of this object"""
		if not name:
			self.error("No name specified")

		# have to compile since flags= is a Python 2.7+ keyword
		r = re.compile('[\w-]', re.UNICODE)

		newname = "".join(r.findall(name)).lower()
		if name != newname or not name[0].isalpha():
			self.error("Name '%s' can only include a-z, A-Z, 0-9, underscore, must be lowercase, and must start with a letter"%name)

		return name


	def error(self, msg='', e=None, warning=False):
		"""Raise a ValidationError exception. If warning=True, it will pass the exception, but make a note in the log."""
		if e == None:
			e = emen2.db.exceptions.ValidationError

		if not msg:
			msg = e.__doc__

		if warning:
			g.warn(msg)
		elif e:
			raise e(msg)





# A class for dbo's that have permissions associated.. Eventually I would like this to be everything.
# This will help us do things like protect group memberships.

class PermissionsDBObject(BaseDBObject):

	# Changes to permissions and groups, along with parents/children, aren't logged.
	param_all = BaseDBObject.param_all | set(['permissions', 'groups'])

	def init(self, d):
		super(PermissionsDBObject, self).init(d)

		p = {}
		# Results of security test performed when the context is set
		# correspond to, read,comment,write and owner permissions, return from setContext
		p['_ptest'] = [True,True,True,True]

		# Setup the base permissions
		p['permissions'] = [[],[],[],[]]
		p['groups'] = set()

		if self._ctx.username != 'root':
			p['permissions'][3].append(self._ctx.username)

		self.__dict__.update(p)


	##########################
	# Setters
	##########################

	def _set_permissions(self, key, value, vtm=None, t=None):
		self.setpermissions(value)
		return set(['permissions'])


	def _set_groups(self, key, value, vtm=None, t=None):
		self.setgroups(value)
		return set(['groups'])


	#################################
	# Permissions checking
	#################################

	def setContext(self, ctx):
		# Check if we can access this item..
		self.__dict__['_ctx'] = ctx

		# test for owner access in this context.
		if self._ctx.checkreadadmin():
			self.__dict__['_ptest'] = [True, True, True, True]
			return True

		self.__dict__['_ptest'] = [self._ctx.username in level for level in self.permissions]

		for group in self.groups & self._ctx.groups:
			self._ptest[self._ctx.grouplevels[group]] = True

		# Allow us to override readable; normally just checks "any(self._ptest)"
		if not self.readable():
			raise emen2.db.exceptions.SecurityError, "Permission Denied: %s"%self.name

		return self._ptest[0]


	def getlevel(self, user):
		for level in range(3, -1, -1):
			if user in self.permissions[level]:
				return level


	def isowner(self):
		return self._ptest[3]


	def writable(self, key=None):
		"""Returns whether this record can be written using the given context"""
		return any(self._ptest[2:])


	def commentable(self):
		"""Does user have level 1 permissions? Required to comment or link."""
		return any(self._ptest[1:])


	def readable(self):
		return any(self._ptest)


	def members(self):
		return set(reduce(operator.concat, self.permissions))


	def owners(self):
		return self.permissions[3]


	def ptest(self):
		return self._ptest


	#################################
	# Permissions methods
	#################################

	def adduser(self, users, level=0, reassign=False):
		"""Add a user to the record's permissions"""
		if not users:
			return

		if not hasattr(users,"__iter__"):
			users = [users]

		level = int(level)
		if not 0 <= level <= 3:
			raise Exception, "Invalid permissions level. 0 = Read, 1 = Comment, 2 = Write, 3 = Owner"

		p = [set(x) for x in self.permissions]

		# Root is implicit
		users = set(users) - set(['root'])

		if reassign:
			p = [i-users for i in p]

		p[level] |= users

		p[0] -= p[1] | p[2] | p[3]
		p[1] -= p[2] | p[3]
		p[2] -= p[3]

		self.setpermissions(p)


	def addumask(self, umask, reassign=False):
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
		if not users:
			return

		p = [set(x) for x in self.permissions]
		if not hasattr(users, "__iter__"):
			users = [users]
		users = set(users)
		p = [i-users for i in p]

		self.setpermissions(p)


	def setpermissions(self, value):
		# You could skip validation here, but commits go through update(), and get validated that way.
		value = [[unicode(y) for y in x] for x in value]
		if len(value) != 4:
			raise ValueError, "Invalid permissions format: %s"%value

		return self._set('permissions', value, self.isowner())



	#################################
	# ...groups
	#################################

	def addgroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		g = self.groups | set(groups)
		self.setgroups(g)


	def removegroup(self, groups):
		if not hasattr(groups, "__iter__"):
			groups = [groups]
		g = self.groups - set(groups)
		self.setgroups(g)


	def setgroups(self, groups):
		return self._set('groups', set(groups), self.isowner())



__version__ = "$Revision$".split(":")[1][:-1].strip()
