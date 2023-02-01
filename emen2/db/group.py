# $Id: group.py,v 1.30 2012/07/28 06:31:17 irees Exp $
"""Group DBOs

Classes:
    Group: Represents a group of users, each with certain permissions
    GroupDB: BTree for storing Groups

"""

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
    """Groups of users.

    Provides the following attributes:
        disabled, displayname, privacy

    Groups are used in conjunction with permissions access control lists to
    share a set of permissions between many records. Some groups are also used
    to provide role-based access, such as administrative rights, the right to
    read published (public) records, the right to create records, etc. Groups
    are only slightly modified from the parent PermissionsDBOBject class; you
    will find additional documentation there.

    When referenced in a Record's groups attribute, the Group's permissions
    will be overlaid on top of the Record permissions. As such, if a user has
    comment level permissions in a group, that user will have comment level
    permissions in any Record that lists that group. All four permissions levels
    will be checked in this way.

    Like a Record, you must have administrative rights in a group to edit that
    groups permissions list.

    The displayname attribute serves a similar purpose to the User displayname
    attribute; it provides a human-formatted description of the group (in some
    cases, groups may have random, arbitrary, or cryptic names.)

    The disabled attribute will disable the Group: it will not be active, and
    Records will not inherit its permissions.

    The privacy attribute will hide the members of the Group from non-members.
    Groups are private by default.

    The following methods are overridden:

        init            Init disabled, displayname, and privacy
        readable        Some special groups are readable by all


    :attr privacy: Hide members from non-members
    :attr displayname: Human readable display name
    :attr disabled: Group is disabled

    """
    attr_public = emen2.db.dataobject.PermissionsDBObject.attr_public | set(['privacy', 'disabled', 'displayname'])

    def init(self, d):
        super(Group, self).init(d)
        self.__dict__['disabled'] = False
        self.__dict__['displayname'] = None
        self.__dict__['privacy'] = True


    # Groups are readable by anyone.
    def readable(self):
        # return any(self._ptest)
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
        






class GroupDB(emen2.db.btrees.DBODB):
    dataclass = Group

    def openindex(self, param, txn=None):
        if param == 'permissions':
            ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
        else:
            ind = super(GroupDB, self).openindex(param, txn=txn)
        return ind



__version__ = "$Revision: 1.30 $".split(":")[1][:-1].strip()

