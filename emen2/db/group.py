"""Group: Represents a group of users, each with certain permissions."""

# EMEN2 imports
import emen2.db.dataobject
import emen2.db.exceptions

class Group(emen2.db.dataobject.PermissionsDBObject):
    """Groups of users.

    Provides the following parameters:
        disabled, displayname, privacy

    Groups are used in conjunction with permissions access control lists to
    share a set of permissions between many records. Some groups are also used
    to provide role-based access, such as administrative rights, the right to
    read published (public) records, the right to create records, etc. Groups
    are only slightly modified from the parent PermissionsDBOBject class; you
    will find additional documentation there.

    When referenced in a Record's groups parameter, the Group's permissions
    will be overlaid on top of the Record permissions. As such, if a user has
    comment level permissions in a group, that user will have comment level
    permissions in any Record that lists that group. All four permissions levels
    will be checked in this way.

    Like a Record, you must have administrative rights in a group to edit that
    group's permissions list.

    The 'displayname' parameter serves a similar purpose to the User displayname
    parameter; it provides a human-formatted description of the group.

    The 'disabled' parameter will disable the Group: it will not be active, and
    Records will not inherit its permissions.

    The following methods are overridden:

        init            Init disabled, displayname, and privacy
        readable        Some special groups are readable by all

    :property displayname: Human readable display name
    :property disabled: Group is disabled
    :property privacy: 

    """
    public = emen2.db.dataobject.PermissionsDBObject.public | set(['privacy', 'disabled', 'displayname'])

    def init(self, d):
        super(Group, self).init(d)
        self.data['disabled'] = False
        self.data['displayname'] = None
        self.data['privacy'] = True

    # Groups are readable by anyone.
    def readable(self):
        return True

    # Setters
    def _set_privacy(self, key, value):
        value = int(value)
        if value not in [0,1,2]:
            raise self.error("Group privacy setting may be 0, 1, or 2.")
        self._set(key, value, self.isowner())

    def _set_disabled(self, key, value):
        self._set(key, bool(value), self.isowner())

    def _set_displayname(self, key, value):
        self._set(key, str(value or self.name), self.isowner())
