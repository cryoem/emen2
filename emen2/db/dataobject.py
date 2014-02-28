"""Base classes for EMEN2 DatabaseObjects."""

import re
import collections
import operator
import hashlib
import UserDict
import json

import emen2.utils
import emen2.db.exceptions
import emen2.db.vartypes

class BaseDBObject(object):
    """Base class for EMEN2 DBOs.

    This class implements the mapping interface, and all the required base
    parameters for DBOs:

        name, keytype, creator, creationtime, modifytime, modifyuser, uri

    The 'name' parameter is usually specified by the user when a new item is
    created, but the rest are set by the database when an item is committed.
    The 'creator' and 'creationtime' parameters are set on initial commit, and
    'modifyuser' and 'modifytime' parameters are usually updated on subsequent
    commits. The 'uri' parameter can be set to indicate an item was imported
    from an external source; presence of the uri parameter will generally mark
    an item as read-only. The 'parents' and 'children' parameters are treated 
    specially when an item is committed.

    Parameters are stored in the self.data dictionary, and this is saved when
    the DBO is committed.

    In addition to implementing the mapping interface, the following methods
    are required as part of the database object interface:

        setContext       Check read permission and bind to a Context
        validate         Validate the item before committing
        isowner          Check ownership permission
        isnew            Check if the item has been committed
        writable         Check write permission
        delete           Prepare item for deletion
        rename           Prepare item for renaming

    BaseDBObject also provides the following methods for extending/overriding:

        init             Subclass init
        changed          Check parameters to re-index
        error            Raise an Exception (default is ValidationError)

    All public methods are safe to override or extend, but be aware of any
    important default behaviors, particularly those related to security and
    validation.

    Naturally, as with anything in Python, anyone with direct
    access to the database can override security by accessing or committing
    to the database with low-level database methods. Therefore, it is generally
    necessary to restrict access using a proxy (e.g. DBProxy) over a network
    connection.

    :property name: Item name
    :property creator: Item creator
    :property creationtime: Creation time, ISO 8601 format
    :property modifyuser: Last user to modify item
    :property modifytime: Time of last modification, ISO 8601 format
    :property uri: Reference to original item if imported
    :property keytype:
    :classattr public: Public (exported) keys
    """

    def __init__(self):
        self.data = {}
        self.ctx = None
        self.new = True
        self.init()
        
    @classmethod
    def new(cls, ctx=None, **data):        
        d = cls()
        if ctx:
            d.initContext(ctx)
            d.setContext(ctx)
        d.update(data)
        return d
    
    @classmethod
    def load(cls, data):
        d = cls()
        d.data = data
        d.new = False
        return d

    def init(self):
        """Subclass init."""
        t = emen2.db.database.utcnow()
        self.data = {}
        self.data['name'] = None
        self.data['uri'] = None
        self.data['keytype'] = unicode(self.__class__.__name__.lower())
        self.data['creator'] = None 
        self.data['modifyuser'] = None
        self.data['creationtime'] = t
        self.data['modifytime'] = t
    
    def validate(self):
        """Validate."""
        pass

    def initContext(self, ctx):
        self.ctx = ctx
        self.data['creator'] = self.ctx.user
        self.data['modifyuser'] = self.ctx.user

    def setContext(self, ctx):
        """Set permissions and bind the context."""
        self.ctx = ctx
        if not self.readable():
            raise emen2.db.exceptions.PermissionsError("Permission denied: %s"%(self.name))

    def changed(self, item=None):
        """Differences between two DBOs."""
        allkeys = set(self.keys() + item.keys())
        return set(filter(lambda k:self.get(k) != item.get(k), allkeys))

    def __repr__(self):
        return """<%s at %0x: %s>"""%(self.__class__.__name__, id(self), self.name)

    ##### Permissions
    # Two basic permissions are defined: owner and writable
    # By default, everyone can read an object.
    # PermissionsDBObject has a more complete permissions model
    # Lack of read access is handled in setContext (raise PermissionsError)

    def readable(self):
        """Check read permissions."""
        return True

    def writable(self, key=None):
        """Check write permissions."""
        return self.isowner()

    def isowner(self):
        """Check ownership permissions."""
        if not getattr(self, 'ctx', None):
            return False
        if self.ctx.checkadmin():
            return True
        if self.ctx.user == getattr(self, 'creator', None):
            return True

    def isnew(self):
        return getattr(self, 'new', False) == True

    ##### Delete and rename. #####

    def delete(self):
        raise self.error("No permission to delete.")

    def rename(self):
        raise self.error("No permission to rename.")

    ##### Mapping interface #####

    def set(self, key, value):
        self.__setitem__(key, value)
        
    def get(self, key, default=None):
        return self.data.get(key, default)

    def has_key(self,key):
        return key in self.data

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def update(self, update):
        for k,v in update.items():
            self.__setitem__(k, v)
    
    def _setattr(self, key, value):
        object.__setattr__(self, key, value)
    
    def __setattr__(self, key, value):
        getattr(self, '_set_%s'%key, self._setattr)(key, value)
            
    def __getattr__(self, key):
        # If key is not already an existing attribute, look in self.data.
        # Otherwise raise AttributeError so getattr() returns default.
        # print "__getattr__ self.__dict__", key, self.__dict__
        try:
            return object.__getattribute__(self, 'data')[key]
        except KeyError, e:
            raise AttributeError("No attribute: %s"%key)

    def _setitem(self, key, value):
        self.error('Cannot set parameter "%s" in this way.'%(key), warning=True)
        print value

    def __setitem__(self, key, value):
        # If a "_set_<key>" method exists, use this.
        # Otherwise, use _setitem as the setter. This will raise an error
        #    (default) or allow 'out of bounds' attrs (see Record class)
        if value == self.get(key):
            return
        getattr(self, '_set_%s'%key, self._setitem)(key, value)

    def __getitem__(self, key, default=None):
        # Behave like dict.get(key) instead of dict[key]
        return self.data.get(key, default)

    ##### Real updates #####

    def _set(self, key, value, check):
        """Actually set a value. 
        
        Check must be True; e.g.:
            self._set('key', 'value', self.isowner())
        This is to encourage the developer to explicitly check permissions.
        """
        if not check:
            msg = 'Insufficient permissions to change parameter: %s'%key
            raise self.error(msg, e=emen2.db.exceptions.PermissionsError)
        self.data[key] = value
        # Only permissions/groups do not trigger a modifytime update
        if key not in ['permissions', 'groups'] and not self.isnew():
            self.data['modifytime'] = emen2.db.database.utcnow()
            self.data['modifyuser'] = self.ctx.user

    ##### Core parameters. #####
    
    def _set_name(self, key, value):
        self._set(key, value, self.isnew())
        
    def _set_uri(self, key, value):
        self._set(key, value, self.isnew())

    def _set_keytype(self, key, value):
        pass

    def _set_keywords(self, key, value):
        pass
        
    def _set_creator(self, key, value):
        pass
    
    def _set_creationtime(self, key, value):
        pass
        
    def _set_modifyuser(self, key, value):
        pass
        
    def _set_modifytime(self, key, value):
        pass

    # Backwards compat...
    def _set_children(self, key, value):
        self.data['children'] = sorted(map(self._strip, emen2.utils.check_iterable(value)))
    
    def _set_parents(self, key, value):
        self.data['parents'] = sorted(map(self._strip, emen2.utils.check_iterable(value)))
        
    ##### Pickle / serialize methods #####

    def __setstate__(self, data):
        if 'data' not in data:
            data['keytype'] = unicode(self.__class__.__name__.lower())
            params = data.pop('params', {})
            params.update(data)
            data = {'data':params}
        self.__dict__.update(data)
        
    def __getstate__(self):
        """Pickle just the data; ignore context and other temporary information."""
        return {'data':self.data}

    ##### Validation and error control #####

    def _validate(self, key, value):
        """Validate a single parameter value."""
        # This is the main mechanism for validation.
        # Check the cache for the param
        # ... raise an Exception if the param isn't found.
        hit, pd = self.ctx.cache.check(('paramdef', key))
        if not hit:
            try:
                pd = self.ctx.db.paramdef.get(key, filt=False)
                self.ctx.cache.store(('paramdef', key), pd)
            except KeyError:
                raise self.error('Parameter %s does not exist.'%key)

        # Validate
        vtc = pd.get_vartype()
        try:
            value = vtc.validate(value)
        except emen2.db.exceptions.EMEN2Exception, e:
            raise self.error(msg=e.message)
        except Exception, e:
            raise self.error(msg=e.message)
        return value

    ##### Convenience methods #####

    def _strip(self, value):
        return unicode(value or '').strip() or None

    def error(self, msg='', e=None, warning=False):
        """Raise a ValidationError exception.
        If warning=True, pass the exception, but make a note in the log.
        """
        if e == None:
            e = emen2.db.exceptions.ValidationError
        if not msg:
            msg = e.__doc__
        if warning:
            emen2.db.log.warn("Warning: %s %s: %s"%(self.keytype, self.name, e(msg)))
            pass
        return e(msg)

# A class for dbo's that have detailed ACL permissions.
class PermissionsDBObject(BaseDBObject):
    """DBO with additional access control.

    This class is used for DBOs that require finer grained control
    over reading and writing. For instance, :py:class:`emen2.db.record.Record` 
    and :py:class:`emen2.db.group.Group`. It is a subclass
    of :py:class:`BaseDBObject`; see that class for additional documentation.

    Two additional parameters are provided:
        permissions, groups

    The 'permissions' parameter is of the "acl" vartype. It is a list comprised of four
    lists or user names, denoting the following levels of permissions:

    Level 0 - Read
        Permission to read the item

    Level 1 - Comment
        Permission to add comments, if the item supports it

    Level 2 - Write
        Permission to change record

    Level 3 - Owner
        Permission to change the item's permissions and groups

    The 'groups' parameter is a set of group names. The permissions of
    each group will be overlaid on top of the item's permissions. For instance,
    a user who has comment permissions in a listed group will have comment
    permissions on this item. There are a few built-in groups: administrators,
    read-only administrators, authenticated users, anonymous users, etc. See the
    Group class documentation for additional details.

    Changes to permissions and groups do not trigger an update to the
    modification time and user.

    :property permissions: Access control list
    :property groups: Groups
    """
    
    def init(self):
        """Initialize the permissions and groups."""
        super(PermissionsDBObject, self).init()
        # Results of security test performed when the context is set
        # correspond to: read, comment, write, and owner permissions,
        self.ptest = [True, True, True, True]
        # Setup the base permissions
        self.data['permissions'] = [[],[],[],[]]
        self.data['groups'] = []

    ##### Permissions checking #####

    def initContext(self, ctx):
        self.ctx = ctx
        self.data['creator'] = self.ctx.user
        self.data['modifyuser'] = self.ctx.user
        self.data['permissions'] = [[], [], [], [self.ctx.user]]

    def setContext(self, ctx):
        """Check read permissions and bind Context.

        :param ctx: Context.
        """
        # Check if we can access this item..
        self.ctx = ctx

        # test for owner access in this context.
        if self.isnew() or self.ctx.checkadmin() or self.creator == self.ctx.user:
            self.ptest = [True, True, True, True]
            return

        # Check if we're listed in each level.
        self.ptest = [self.ctx.user in level for level in self.permissions]

        # If read admin, set read access.
        if self.ctx.checkreadadmin():
            self.ptest[0] = True
        
        # Apply any group permissions.
        for group in set(self.groups) & set(self.ctx.groups):
            self.ptest[self.ctx.grouplevels[group]] = True

        # Now, check if we can read.
        if not self.readable():
            raise emen2.db.exceptions.PermissionsError("Permission denied: %s"%(self.name))

    def getlevel(self, user):
        """Get the user's permission level (0-3) for this object."""
        for level in range(3, -1, -1):
            if user in self.permissions[level]:
                return level

    def isowner(self):
        """Is the current user the owner?"""
        return self.ptest[3]

    def readable(self):
        """Does the user have permission to read the record(level 0)?"""
        return any(self.ptest)

    def commentable(self):
        """Does user have permission to comment (level 1)?"""
        return any(self.ptest[1:])

    def writable(self):
        """Does the user have permission to change the record (level 2)?"""
        return any(self.ptest[2:])

    def members(self):
        """Get all users with read permissions."""
        return reduce(operator.concat, self.permissions)

    def owners(self):
        """Get all users with ownership permissions."""
        return self.data['permissions'][3]

    ##### Permissions #####

    def _set_permissions(self, key, value):
        self.setpermissions(value)

    def _validate_permissions(self, value):
        if hasattr(value, 'items'):
            v = [[],[],[],[]]
            ci = emen2.utils.check_iterable
            v[0] = ci(value.get('read'))
            v[1] = ci(value.get('comment'))
            v[2] = ci(value.get('write'))
            v[3] = ci(value.get('admin'))
            value = v
        permissions = [[self._strip(y) for y in x] for x in value]
        if len(permissions) != 4:
            raise ValueError("Invalid permissions format.")
        return permissions

    def setpermissions(self, value):
        """Set the permissions."""
        value = self._validate_permissions(value)
        self._set('permissions', value, self.isowner())

    def adduser(self, users, level=0, reassign=True):
        """Add a user to the record's permissions.

        :param users: A list of users to be added to the permissions
        :param level: The permission level to give to the users
        :param reassign: Allow for lowering of permission level.
        """
        if not users:
            return
        if not hasattr(users,"__iter__"):
            users = [users]

        level = int(level)
        if not 0 <= level <= 3:
            raise Exception("Invalid permissions level. 0 = Read, 1 = Comment, 2 = Write, 3 = Owner.")

        p = [set(x) for x in self.permissions]
        users = set(users) 
        if reassign:
            p = [i-users for i in p]

        p[level] |= users
        p[0] -= p[1] | p[2] | p[3]
        p[1] -= p[2] | p[3]
        p[2] -= p[3]
        self.setpermissions(p)

    def addumask(self, value, reassign=False):
        """Set permissions for users in several different levels at once.

        :param value: The list of users
        :param reassign: Whether or not the users added should be reassigned. (default False)
        """
        umask = self._validate_permissions(value)
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
        """Remove users from permissions."""
        if not users:
            return
        p = [set(x) for x in self.permissions]
        if not hasattr(users, "__iter__"):
            users = [users]
        users = set(users)
        p = [i-users for i in p]
        self.setpermissions(p)

    ##### Groups #####

    def _set_groups(self, key, value):
        self.setgroups(value)

    def setgroups(self, groups):
        """Set the object's groups."""
        groups = sorted(map(self._strip, emen2.utils.check_iterable(groups)))
        self._set('groups', groups, self.isowner())

    def addgroup(self, groups):
        """Add a group to the record."""
        if not hasattr(groups, "__iter__"):
            groups = [groups]        
        g = set(self.groups) | set(groups)
        self.setgroups(g)

    def removegroup(self, groups):
        """Remove a group from the record."""
        if not hasattr(groups, "__iter__"):
            groups = [groups]
        g = set(self.groups) - set(groups)
        self.setgroups(g)

class PrivateDBO(BaseDBObject):
    pass
    # def setContext(self, ctx=None):
    #     raise emen2.db.exceptions.PermissionsError("Private item.")


