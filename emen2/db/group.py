# $Id$
import time
import operator
import hashlib
import random
import re
import weakref

#import emen2.db
import emen2.db.exceptions
import emen2.db.config
g = emen2.db.config.g()



# ian: todo: upgrade to BaseDBObject
class Group(emen2.db.dataobject.BaseDBObject):
	"""Groups of users. These can be set in individual Records to provide access to members of a group.

	@attr name
	@attr disabled
	@attr privacy
	@attr permissions Group membership, similar to Record permissions

	@attr creator
	@attr creationtime
	@attr modifytime
	@attr modifyuser

	"""

	attr_user = set(["privacy", "modifytime", "modifyuser", "permissions", "name", "disabled", "creator", "creationtime", "displayname"])

	def init(self, d=None):
		self.name = d.pop('name', None)
		self.disabled = d.pop('disabled',False)
		self.displayname = d.pop('displayname', None)
		self.privacy = d.pop('privacy',False)
		self.creator = d.pop('creator',None)
		self.creationtime = d.pop('creationtime',None)
		self.modifytime = d.pop('modifytime',None)
		self.modifyuser = d.pop('modifyuser',None)

		self.setpermissions(d.pop('permissions', None))

		if self._ctx:
			self.creator = self._ctx.username
			self.adduser(self.creator, level=3)
			self.creationtime = emen2.db.database.gettime()


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
		return self.__dict__.get(key, default)

	get = __getitem__


	def __setitem__(self,key,value):
		if key == "permissions":
			return self.setpermissions(value)
		if key in self.attr_user:
			self.__dict__[key] = value
		else:
			raise KeyError,"Invalid key: %s"%key


	################################
	# validation methods
	################################


	def validate(self, orec=None, warning=False, txn=None):
		
		if not self.name :
			raise ValueError, "No name given"

		self.name = re.sub("\W", "", self.name).lower()
		
		if not self.isowner():
			raise emen2.db.exceptions.SecurityError, "Not authorized to change group: %s"%self.name

		allusernames = self._ctx.db.getusernames(ctx=self._ctx, txn=txn)
		if self.members() - allusernames:
			raise Exception, "Invalid user names: %s"%(self.members() - allusernames)
__version__ = "$Revision$".split(":")[1][:-1].strip()
