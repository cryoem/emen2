"""Base classes for EMEN2 DatabaseObjects."""

import re
import collections
import operator
import hashlib
import UserDict

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
    specially when an item is committed: both the parent and the child will 
    be updated.

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
    :property parents: Parents set
    :property children: Children set
    :property keytype:
    :classattr public: Public (exported) keys
    """
    
    public = set(['children', 'parents', 'keytype', 'creator', 'creationtime', 'modifytime', 'modifyuser', 'uri', 'name'])

    def __init__(self, **kwargs):
        """Initialize a new DBO."""
        self.data = {}
        self.new = True
        self.ctx = kwargs.pop('ctx', None)
        if kwargs:
            self.init(kwargs)
            self.setContext(self.ctx)
            self.update(kwargs)

    def init(self, d, ctx=None):
        """Subclass init."""
        # Base data
        data = {}
        data['name'] = None
        data['uri'] = None
        data['keytype'] = unicode(self.__class__.__name__.lower())
        data['creator'] = self.ctx.username
        data['creationtime'] = self.ctx.utcnow
        data['modifyuser'] = self.ctx.username
        data['modifytime'] = self.ctx.utcnow
        data['children'] = set()
        data['parents'] = set()
        self.data = data
        
    def load(self, d, ctx=None):
        """Load directly from JSON / dict."""
        self.new = False
        self.data = d
        self.setContext(ctx)

    def validate(self):
        """Validate."""
        pass

    def setContext(self, ctx):
        """Set permissions and bind the context."""
        self.ctx = ctx
        if not self.readable():
            raise emen2.db.exceptions.PermissionsError("Permission denied: %s"%(self.name))

    def changed(self, item=None):
        """Differences between two DBOs."""
        allkeys = set(self.keys() + item.keys())
        return set(filter(lambda k:self.get(k) != item.get(k), allkeys))

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
        if self.ctx.username == getattr(self, 'creator', None):
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
        """Returns a set of keys that were updated."""
        for k,v in update.items():
            self.__setitem__(k, v)
        
    def __setattr__(self, key, value):
        # Treat keys in self.public as properties.
        if key in self.public:
            self.__setitem__(key, value)
        object.__setattr__(self, key, value)

    def __getattr__(self, key):
        # Treat keys in self.public as properties.
        if key in self.public:
            return self.data.get(key)
        return object.__getattribute__(self, key)

    def __getitem__(self, key, default=None):
        # Behave like dict.get(key) instead of dict[key]
        return self.data.get(key, default)

    def __delitem__(self, key):
        raise AttributeError, 'Key deletion not allowed.'

    def __setitem__(self, key, value):
        # If a "_set_<key>" method exists, that will always be used for setting.
        # Otherwise, use _setoob as the setter. This will raise an error
        #    (default) or allow 'out of bounds' attrs (see Record class)
        if self.data.get(key) == value:
            return

        # Find a setter method (self._set_<key>)
        setter = getattr(self, '_set_%s'%key, None)
        if setter:
            pass
        elif key in self.public:
            # These can't be modified without a setter method defined.
            # (Return quietly instead of PermissionsError or KeyError)
            return
        else:
            # Setter for parameters that are not explicitly in self.public
            # Default is to raise KeyError or ValidationError
            setter = self._setoob            

        # The setter might return multiple items that were updated
        # For instance, comments can update other params
        setter(key, value)

    ##### Real updates #####

    def _set(self, key, value, check):
        """Actually set a value. 
        
        Check must be True; e.g.:
            self._set('key', 'value', self.isowner())
        This is to encourage the developer to think and explicitly check permissions.
        """
        if not check:
            msg = 'Insufficient permissions to change parameter: %s'%key
            raise self.error(msg, e=emen2.db.exceptions.PermissionsError)

        self.data[key] = value

        # Only permissions, groups, and links do not trigger a modifytime update
        if key not in ['permissions', 'groups', 'parents', 'children'] and not self.isnew():
            self.data['modifytime'] = self.ctx.utcnow
            self.data['modifyuser'] = self.ctx.username

    def _setoob(self, key, value):
        """Out-of-bounds."""
        self.error('Cannot set parameter %s in this way'%key, warning=True)

    ##### Core parameters. #####
    
    def _set_name(self, key, value):
        self._set(key, value, self.isnew())
        
    def _set_uri(self, key, value):
        self._set(key, value, self.isnew())

    ##### Update parents / children #####

    def _set_children(self, key, value):
        self._setrel(key, value)

    def _set_parents(self, key, value):
        self._setrel(key, value)

    def _setrel(self, key, value):
        """Set a relationship."""
        value = set(map(self._strip, emen2.utils.check_iterable(value)))
        value = filter(None, value) or []
        self._set(key, value, self.writable())

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

        # Is it an immutable param?
        if pd.get('immutable') and not self.isnew():
            raise self.error('Cannot change immutable parameter: %s'%pd.name)

        # Validate
        vartype = emen2.db.vartypes.Vartype.get_vartype(pd.vartype, pd=pd, db=self.ctx.db, cache=self.ctx.cache)
        try:
            value = vartype.validate(value)
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
            emen2.db.log.warn("Warning: %s"%e(msg))
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
    
    # These methods are overridden from BaseDBObject:
    #    init, setContext, isowner, writable,
    # The following methods are added to BaseDBObject:
    #    addumask, addgroup, removegroup, removeuser, 
    #     adduser, getlevel, ptest, readable, commentable, 
    #     members, owners, setgroups, setpermissions

    # Changes to permissions and groups, along with parents/children,
    # are not logged.
    public = BaseDBObject.public | set(['permissions', 'groups'])

    def init(self, d):
        """Initialize the permissions and groups."""
        super(PermissionsDBObject, self).init(d)

        # Results of security test performed when the context is set
        # correspond to: read, comment, write, and owner permissions,
        self.ptest = [True, True, True, True]

        # Setup the base permissions
        self.data['permissions'] = [[],[],[],[self.ctx.username]]
        self.data['groups'] = set()

    ##### Permissions checking #####

    def setContext(self, ctx):
        """Check read permissions and bind Context.

        :param ctx: Context.
        """
        # Check if we can access this item..
        self.ctx = ctx

        # test for owner access in this context.
        if self.isnew() or self.ctx.checkadmin() or self.creator == self.ctx.username:
            self.ptest = [True, True, True, True]
            return

        # Check if we're listed in each level.
        self.ptest = [self.ctx.username in level for level in self.permissions]

        # If read admin, set read access.
        if self.ctx.checkreadadmin():
            self.ptest[0] = True
        
        # Apply any group permissions.
        for group in set(self.groups) & self.ctx.groups:
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
        return set(reduce(operator.concat, self.permissions))

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
            raise ValueError, "Invalid permissions format"
        return permissions

    def setpermissions(self, value):
        """Set the permissions."""
        value = self._validate_permissions(value)
        self._set('permissions', value, self.isowner())

    def adduser(self, users, level=0, reassign=False):
        """Add a user to the record's permissions.

        :param users: A list of users to be added to the permissions
        :param level: The permission level to give to the users
        :param reassign: Whether or not the users added should be reassigned. (default False)
        """
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
        groups = set(map(self._strip, emen2.utils.check_iterable(groups)))
        self._set('groups', groups, self.isowner())

    def addgroup(self, groups):
        """Add a group to the record."""
        if not hasattr(groups, "__iter__"):
            groups = [groups]
        g = self.groups | set(groups)
        self.setgroups(g)

    def removegroup(self, groups):
        """Remove a group from the record."""
        if not hasattr(groups, "__iter__"):
            groups = [groups]
        g = self.groups - set(groups)
        self.setgroups(g)

class PrivateDBO(object):
    def setContext(self, ctx=None):
        raise emen2.db.exceptions.PermissionsError("Private item.")

# History
class History(PrivateDBO):
    """Manage previously used values."""
    def __init__(self, name=None, *args, **kwargs):
        self.name = name
        self.history = []

    def addhistory(self, timestamp, user, param, value):
        """Add a value to the history."""
        v = (timestamp, user, param, value)
        if v in self.history:
            raise ValueError, "This event is already present."
        self.history.append(v)
    
    def gethistory(self, timestamp=None, user=None, param=None, value=None, limit=None):
        """Get :limit: previously used values."""
        h = sorted(self.history, reverse=True)
        if timestamp:
            h = filter(lambda x:x[0] == timestamp, h)
        if user:
            h = filter(lambda x:x[1] == user, h)
        if param:
            h = filter(lambda x:x[2] == param, h)
        if value:
            h = filter(lambda x:x[3] == value, h)
        if limit is not None:
            h = h[:limit]
        return h

    def checkhistory(self, timestamp=None, user=None, param=None, value=None, limit=None):
        """Check if an param or value is in the past :limit: items."""
        if self.gethistory(timestamp=timestamp, user=user, param=param, value=value, limit=limit):
            return True
        return False

    def prunehistory(self, user=None, param=None, value=None, limit=None):
        """Prune the history to :limit: items."""
        other = []
        match = []
        for t, u, p, v in self.history:
            if u == user or p == param or v == value:
                match.append((t,u,p,v))
            else:
                other.append((t,u,p,v))

        if limit:
            match = sorted(match, reverse=True)[:limit]
        else:
            match = []
        self.history = sorted(match+other, reverse=True)
        
