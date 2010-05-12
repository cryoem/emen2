import time
import operator
import hashlib
import random
import UserDict
import re
import weakref

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

#import emen2.Database
import emen2.Database.exceptions



# ian: todo: upgrade to BaseDBObject
class Group(object, UserDict.DictMixin):

	attr_user = set(["privacy", "modifytime","modifyuser","permissions","_ctx"])
	attr_admin = set(["name","disabled","creator","creationtime"])
	attr_all = attr_user | attr_admin


	def __init__(self, _d=None, **_k):
		_k.update(_d or {})
		ctx = _k.pop('ctx',None)

		self.name = _k.pop('name', None)
		self.disabled = _k.pop('disabled',False)
		self.privacy = _k.pop('privacy',False)
		self.creator = _k.pop('creator',None)
		self.creationtime = _k.pop('creationtime',None)
		self.modifytime = _k.pop('modifytime',None)
		self.modifyuser = _k.pop('modifyuser',None)

		self.setpermissions(_k.pop('permissions', None))
		self.setContext(ctx)

		if ctx:
			self.creator = self._ctx.username
			self.adduser(self.creator, level=3)
			self.creationtime = emen2.Database.database.gettime()
			#self.validate()

		#self.__permissions = kwargs.get('permissions')


	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		try: del odict['_ctx']
		except:	pass
		return odict


	def upgrade(self):
		pass


	def setContext(self, ctx=None):
		self._ctx = ctx


	def getlevel(self, user):
		for level in range(3, -1, -1):
			if user in self.__permissions[level]:
				return level



	def members(self):
		return set(reduce(operator.concat, self.__permissions))


	def owners(self):
		return self.__permissions[3]


	def adduser(self, users, level=0, reassign=1):

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


	##########################################
	# taken from Record
	##########################################

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
			#self.validationwarning("invalid permissions format: %s"%value)
			raise

		r = [self.__partitionints(i) for i in value]

		return tuple(tuple(x) for x in r)


	def setpermissions(self, value):
		#if not self.isowner():
		#	raise SecurityError, "Insufficient permissions to change permissions"
		self.__permissions = self.__checkpermissionsformat(value)


	def getpermissions(self):
		return self.__permissions


	def isowner(self):
		return self._ctx.checkadmin() or self._ctx.username in self.__permissions[3]



	################################
	# mapping methods
	################################


	def __getitem__(self, key, default=None):
		if key == "permissions":
			return self.getpermissions()
		return self.__dict__.get(key,default)

	get = __getitem__

	def __setitem__(self,key,value):
		if key == "permissions":
			return self.setpermissions(value)
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key

	def __delitem__(self,key):
		raise AttributeError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)


	################################
	# validation methods
	################################


	def validate(self, orec=None, warning=False, txn=None):
		if not self.isowner():
			raise emen2.Database.exceptions.SecurityError, "Not authorized to change group: %s"%self.name

		allusernames = self._ctx.db.getusernames(ctx=self._ctx, txn=txn)
		if self.members() - allusernames:
			raise Exception, "Invalid user names: %s"%(self.members() - allusernames)
