# $Id$
import time
import operator
import hashlib
import random
import re
import weakref

import emen2.db.btrees
import emen2.db.dataobject
import emen2.db.exceptions

import emen2.db.config
g = emen2.db.config.g()


class Group(emen2.db.dataobject.PermissionsDBObject):
	"""Groups of users. These can be set in individual Records to provide access to members of a group.
	@attr name
	@attr disabled
	@attr privacy
	"""

	param_user = emen2.db.dataobject.PermissionsDBObject.param_user | set(['privacy', 'disabled', 'displayname'])
	param_all = emen2.db.dataobject.PermissionsDBObject.param_all | param_user

	def init(self, d):
		super(Group, self).init(d)

		# These follow the regular param_user rules for setting; writer=owner=creator
		self.__dict__['disabled'] = False
		self.__dict__['displayname'] = self.name
		self.__dict__['privacy'] = False
		

	# Validate	
	def validate_create(self):
		if not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only admins may create groups"


	def __setstate__(self, d):
		# Backwards compatibility..
		# This became a regular attribute, instead of self.__permissions
		if d.has_key('_Group__permissions'):
			d['permissions'] = d.pop('_Group__permissions', None)

		# I added some additional attributes..
		if not 'groups' in d:
			d['groups'] = set(['anonymous'])
		if not 'disabled' in d:
			d['disabled'] = False
		if not 'privacy' in d:
			d['privacy'] = 0

		return self.__dict__.update(d)







class GroupBTree(emen2.db.btrees.DBOBTree):
	def init(self):
		self.setdatatype('p', emen2.db.group.Group)	
		super(GroupBTree, self).init()

	def openindex(self, param, create=False):
		if param == 'permissions':
			return emen2.db.btrees.IndexBTree(filename="index/security/groupsbyuser", keytype='s', datatype="s", dbenv=self.dbenv)




			
__version__ = "$Revision$".split(":")[1][:-1].strip()

