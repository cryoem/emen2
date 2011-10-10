# $Id$
'''Group Database Objects

Classes:
	Group: Represents a group of users, each with certain permissions
	GroupDB: BTree for storing Groups

'''

import time
import operator
import hashlib
import random
import re
import weakref

# EMEN2 imports
import emen2.db.btrees
import emen2.db.dataobject
import emen2.db.exceptions


class Group(emen2.db.dataobject.PermissionsDBObject):
	"""Groups of users. These can be set in individual Records to provide access to members of a group.
	
	@attr name
	@attr permissions
	@attr groups
	@attr disabled
	@attr privacy
	"""

	param_all = emen2.db.dataobject.PermissionsDBObject.param_all | set(['privacy', 'disabled', 'displayname'])

	def init(self, d):
		super(Group, self).init(d)
		self.__dict__['disabled'] = False
		self.__dict__['displayname'] = self.name
		self.__dict__['privacy'] = False
	
	
	# Special groups are readable by anyone.
	def readable(self):
		if any(self._ptest) or self.name in ['authenticated', 'anon']:
			return True	


	# Setters
	def _set_privacy(self, key, value, vtm=None, t=None):
		value = int(value)
		if value not in [0,1,2]:
			self.error("User privacy setting may be 0, 1, or 2.")
		return self._set(key, value, self.isowner())


	def _set_disabled(self, key, value, vtm=None, t=None):
		return self._set(key, bool(value), self.isowner())


	def _set_displayname(self, key, value, vtm=None, t=None):
		return self._set(key, str(value or self.name), self.isowner())


	# Validate	
	def validate_create(self):
		if not self._ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only admins may create groups"






class GroupDB(emen2.db.btrees.DBODB):
	dataclass = Group

	def openindex(self, param, txn=None):
		if param == 'permissions':
			ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
		else:
			ind = super(GroupDB, self).openindex(param, txn=txn)
		return ind


			
__version__ = "$Revision$".split(":")[1][:-1].strip()

