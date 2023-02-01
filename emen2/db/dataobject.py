# $Id: dataobject.py,v 1.75 2012/07/28 06:31:17 irees Exp $
"""Base classes for EMEN2 DBOs

Classes:
    BaseDBObject: Base EMEN2 DBO
    PermissionsDBObject: DBO with additional access controls

"""

import re
import collections
import operator
import hashlib
import UserDict

# EMEN2 datatypes.
# This is just used to get the current database time.
# This may be changed in the future.
import emen2.db.datatypes

# TODO: Remove UserDict, just do all the methods myself?
# TODO: implement collections.MutableMapping instead of subclassing DictMixin
class BaseDBObject(object, UserDict.DictMixin):
    """Base class for EMEN2 DBOs.

    This class implements the mapping interface, and all the required base
    attributes for DBOs:

        name, keytype, creator, creationtime, modifytime, modifyuser, uri

    The name attribute is usually specified by the user when a new item is created,
     but the rest are set by the database when an item is committed. The creator
    and creationtime attributes are set on initial commit, and modifyuser and
    modifytime attributes are usually updated on subsequent commits. The uri
    attribute can be set to indicate an item was imported from an external
    source; presence of the uri attribute will generally mark an item as
    read-only, even to admin users.

    The keytype attribute is set by the BTree storage container.

    The parents and children attributes are valid for classes that allow
    relationships (RelateDB). These are treated specially when an item is
    committed: both the parent and the child will be updated.

    All attributes should also be valid EMEN2 parameters. The default behavior
    for BaseDBObject and subclasses is to validate the attributes as parameters
    when they are set or updated. When a DBO is exported (JSON, XML,
    network proxy, etc.) only the attributes listed in cls.attr_public are
    exported. Private attributes may be used by using an underscore
    prefix -- but these WILL NOT BE SAVED, and discarded before committing. An
    example of this behavior is the User._displayname attribute, which
    is recalculated whenever the user is retreived from the database. However,
    the dynamic _displayname attribute is still exported by creating a
    displayname class property, and listing that in cls.attr_public. In this way
    it is part of the public interface, even though it is a generated, read-only
    attribute. Another example is the params attribute of Record. This is a
    normal attribute, and read/set from within the class's methods, but is not
    exported (it is instead copied into the regular export dictionary.)

    Required attributes can be specified using cls.attr_required. If any of
    these are None, a ValidationError will be raised during commit.

    In addition to implementing the mapping interface, the following methods
    are required as part of the database interface:

        validate        Validate the item before committing
        setContext        Check read permission and bind to a Context
        isowner            Check ownership permission
        isnew            Check if the item has been committed
        writable        Check write permission
        delete            Prepare item for deletion
        rename            Prepare item for renaming

    BaseDBObject also provides the following methods for extending/overriding:

        init            Subclass init
        validate_param    Validate a parameter
        changedparams     Check parameters to re-index
        commit            Commit and return the updated item
        error            Raise an Exception (default is ValidationError)

    All public methods are safe to override or extend, but be aware of any
    important default behaviors, particularly those related to security and
    validation.

    Naturally, as with anything in Python, anyone with file or code-level
    access to the database can override security by accessing or committing
    to the database with low-level database methods. Therefore, it is generally
    necessary to restrict access using a proxy (e.g. DBProxy) over a network
    connection.

    :attr name: Item name
    :attr creator: Item creator
    :attr creationtime: Creation time, ISO 8601 format
    :attr modifyuser: Last user to modify item
    :attr modifytime: Time of last modification, ISO 8601 format
    :attr uri: Reference to original item if imported

    :classattr attr_public: Public (exported) attributes
    :classattr attr_required: Required attributes
    :property keytype: Key type (default is lower case class name)

    """
    attr_public = set(['children', 'parents', 'keytype', 'creator',
        'creationtime', 'modifytime', 'modifyuser', 'uri', 'name'])
    attr_protected = set(['creator', 'creationtime', 'modifytime', 'modifyuser', 'uri'])

    attr_required = set()

    def __init__(self, _d=None, **_k):
        """Initialize a new DBO.

        You may provide either a dictionary named (first argument or _d keyword,
        or any extra keyword arguments.)

        Remove the ctx and use it for setContext. Finally, update with any left
        over items from _d.
        """

        # Set the uncommitted flag. This will be stripped out when committed.
        # Check with self.isnew()
        self.__dict__['_new'] = True

        # Copy input and kwargs into one dict
        _d = dict(_d or {})
        _d.update(_k)

        # Temporary setContext
        ctx = _d.pop('ctx', None)
        t = _d.pop('t', None)
        self.__dict__['_ctx'] = ctx
                
        vtm, t = self._vtmtime(t=t) # get current time.

        # Assign a name; 
        # Names are now assigned and validated by the BTree.
        p = {}
        p['name'] = _d.pop('name', None)

        # Base owner/time parameters
        p['creator'] = self._ctx.username
        p['creationtime'] = t
        p['modifyuser'] = self._ctx.username
        p['modifytime'] = t

        # Other attributes.
        p['uri'] = None
        p['children'] = set()
        p['parents'] = set()

        # Directly update the base attributes.
        self.__dict__.update(p)

        # Subclass init
        self.init(_d)

        # Set the context
        self.setContext(ctx)

        # Update with the remaining params
        self.update(_d)


    def init(self, d):
        """Subclass init."""
        pass

    def validate(self, vtm=None, t=None):
        """Validate."""
        pass

    def setContext(self, ctx):
        """Set permissions and bind the context."""
        self.__dict__['_ctx'] = ctx

    def changedparams(self, item=None):
        """Differences between two instances."""
        allkeys = set(self.keys() + item.keys())
        return set(filter(lambda k:self.get(k) != item.get(k), allkeys))


    ##### Permissions
    # Two basic permissions are defined: owner and writable
    # PermissiionsDBObject has a more complete permissions model
    # Lack of read access is handled in setContext (raise SecurityError)

    def isowner(self):
        """Check ownership privileges on item."""
        if self._ctx.checkadmin():
            return True
        if self._ctx.username == getattr(self, 'creator', None):
            return True

    def writable(self, key=None):
        """Check write permissions."""
        return self.isowner()

    def isnew(self):
        return getattr(self, '_new', False) == True

    ##### Delete and rename. #####

    def delete(self):
        self.error("No permission to delete.")

    def rename(self):
        self.error("No permission to rename.")


    ##### String representation #####

    def __unicode__(self):
        ret = ["%s\n"%(self.__class__.__name__)]
        for i,j in self.items():
            ret.append(u"%12s:    %s\n"%(unicode(i),unicode(j)))
        return u"".join(ret)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return "<%s %s at %x>" % (self.__class__.__name__, self.name, id(self))


    ##### Required mapping interface #####
    # High level mapping methods

    def get(self, key, default=None):
        return self.__getitem__(key, default)

    def has_key(self,key):
        return key in self.attr_public

    def keys(self):
        return list(self.attr_public)

    def update(self, update, vtm=None, t=None):
        """Dict-like update. Returns a set of keys that were updated."""
        vtm, t = self._vtmtime(vtm, t)
        cp = set()

        # Make sure to pass in t=t to keep all the times in sync
        for k,v in update.items():
            cp |= self.__setitem__(k, v, vtm=vtm, t=t)

        return cp

    def _load(self, update, vtm=None, t=None):
        """Load from a JSON file; this skips validation on a few keys."""
        if not self.isnew():
            self.error('Cannot update previously committed items this way.')

        # Validate
        vtm, t = self._vtmtime(vtm, t)
        
        # Skip validation for protected keys.
        keys = self.attr_protected & set(update.keys())
        keys.add('name')
        for key in keys:
            value = update.pop(key, None)
            # value = self.validate_param(key, value, vtm=vtm) # skip
            self.__dict__[unicode(key)] = value
        
        # Skip validation for relationships.
        # This will assume they are the correct data format.
        for key in ['parents', 'children']:
            self.__dict__[unicode(key)] = set(update.pop(key, None) or [])
        
        self.update(update, vtm=vtm, t=t)

    # Low level mapping methods
    # Behave like dict.get(key) instead of dict[key]
    def __getitem__(self, key, default=None):
        if key in self.attr_public:
            return getattr(self, key, default)
        elif default:
            return default

    def __delitem__(self, key):
        raise AttributeError, 'Key deletion not allowed'

    def __getattr__(self, name):
        return object.__getattribute__(self, name)
        
    # Put everything through setitem for validation/logging/etc..
    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    # Check if there is a method for setting this key,
    # validate the value, set the value, and update the time stamp.
    def __setitem__(self, key, value, vtm=None, t=None):
        """Validate and set an attribute or key."""

        # This will validate the parameter, look for a setter, and then call the setter.
        # If a "_set_<key>" method exists, that will always be used for setting.
        # To allow editing of a public attr, there MUST be a _set_<key> method.
        # Then if no setter, and the method is part of the public attrs, then silently return.
        # Finally, use _setoob as the setter. This can allow OOB attrs, or raise error (default).

        cp = set()
        if self.get(key) == value:
            return cp

        # Find a setter method (self._set_<key>)
        setter = getattr(self, '_set_%s'%key, None)
        if setter:
            pass
        elif key in self.attr_public:
            # These cannot be directly modified (not even by admin)
            # (Return quietly instead of SecurityError or KeyError)
            return cp
        else:
            # Setter for parameters that are not explicitly listed as attributes
            # in (attr_public)
            # Default is to raise KeyError or ValidationError
            # Record class will use this to set non-attribute parameters
            setter = self._setoob

        # Validate.
        # *ALL VALUES* must pass through a validator.
        vtm, t = self._vtmtime(vtm, t)
        value = self.validate_param(key, value, vtm=vtm)

        # The setter might return multiple items that were updated
        # For instance, comments can update other params
        cp |= setter(key, value, vtm=vtm, t=t)

        # Only permissions, groups, and links do not trigger a modifytime update
        if cp - set(['permissions', 'groups', 'parents', 'children']) and not self.isnew():
            self.__dict__['modifytime'] = t
            self.__dict__['modifyuser'] = self._ctx.username
            cp.add('modifytime')
            cp.add('modifyuser')

        # Return all the params that changed
        return cp

    ##### Real updates #####

    def _set(self, key, value, check=None, vtm=None, t=None):
        """Actually set a value."""
        # The default permission required to set a key
        # is write permissions. Additionally, the default
        # for write permissions is owners only.
        if check == None:
            check = self.writable()
        if not check:
            msg = "Insufficient permissions to change param %s"%key
            self.error(msg, e=emen2.db.exceptions.SecurityError)

        self.__dict__[key] = value
        return set([key])

    def _setoob(self, key, value, vtm=None, t=None):
        """Handle params not found in self.attr_public"""
        self.error("Cannot set param %s in this way"%key, warning=True)
        return set()


    ##### Update parents / children #####

    def _setrel(self, key, value):
        """Set a relationship. Make sure we have permissions to edit the relationship."""
        # Filter out changes to permissions on records
        # that we can't access...
        value = emen2.util.listops.check_iterable(value)
        value = set(value)
        orig = self.get(key)

        # ian: todo: temporary fix.. force record keys to be ints.
        # if self.keytype == 'record':
        #    value = set(map(int, value))
        #    orig = set(map(int, orig))

        changed = orig ^ value
        # Get all of the changed items that we can access
        # (KeyErrors will be checked later, during commit..)
        access = self._ctx.db.get(changed, keytype=self.keytype)

        # Check write permissions
        for item in access:
            if not (self.writable() or item.writable()):
                msg = 'Insufficient permissions to add or remove relationship: %s -> %s'%(self.name, item.name)
                self.error(msg, e=emen2.db.exceptions.SecurityError)

        # Keep items that we can't access..
        #     they might be new items, or items we won't
        #    have permission to read/edit.
        value |= changed - set(i.name for i in access)
        return self._set(key, value, True)

    def _set_children(self, key, value, vtm=None, t=None):
        return self._setrel(key, value)

    def _set_parents(self, key, value, vtm=None, t=None):
        return self._setrel(key, value)



    ##### Pickle methods #####

    def __getstate__(self):
        """Context and other session-specific information should not be pickled.
        All private keys (starts with underscore) will be removed."""
        odict = self.__dict__.copy() # shallow copy since we are removing keys
        for key in odict.keys():
            if key.startswith('_'):
                odict.pop(key, None)
        return odict


    ##### Validation and error control #####

    # This is the main mechanism for validation.
    def validate_param(self, key, value, vtm=None):
        """Validate a single parameter value."""
        # Check the cache for the param
        vtm, t = self._vtmtime(vtm=vtm)
        cachekey = vtm.get_cache_key('paramdef', key)
        hit, pd = vtm.check_cache(cachekey)

        # ... otherwise, raise an Exception if the param isn't found.
        if not hit:
            try:
                pd = self._ctx.db.paramdef.get(key, filt=False)
                vtm.store(cachekey, pd)
            except KeyError:
                # This helps to bootstrap when ParamDefs are first being imported.
                if key in self.attr_public:
                    return value
                else:
                    self.error('paramdef %s does not exist' % key)

        # Is it an immutable param?
        if pd.get('immutable') and not self.isnew():
            self.error('Cannot change immutable param %s'%pd.name)

        # Validate
        v = vtm.validate(pd, value)

        # Issue a warning if param changed during validation
        # if v != value:
        #    self.error(
        #        "Parameter %s (%s) changed during validation: %s '%s' -> %s '%s' "%
        #        (pd.name, pd.vartype, type(value), value, type(v), v), warning=True)
        return v


    ##### Convenience methods #####

    def _vtmtime(self, vtm=None, t=None):
        """Utility method to check/get a vartype manager and the current time."""
        # Time stamps are now in ISO 8601 format.
        vtm = vtm or emen2.db.datatypes.VartypeManager(db=self._ctx.db, keytype=self.keytype)
        t = t or emen2.db.database.gettime()
        return vtm, t

    def error(self, msg='', e=None, warning=False):
        """Raise a ValidationError exception.
        If warning=True, pass the exception, but make a note in the log.
        """
        if e == None:
            e = emen2.db.exceptions.ValidationError
        if not msg:
            msg = e.__doc__
            
        if warning:
            # emen2.db.log.warn("Warning: %s"%e(msg))
            pass
        else:
            raise e(msg)

    def commit(self):
        """Commit the item and return the updated copy."""
        return self._ctx.db.put([self], keytype=self.keytype)



# A class for dbo's that have detailed ACL permissions.
class PermissionsDBObject(BaseDBObject):
    """DBO with additional access control.

    This class is used for DBOs that require finer grained control
    over reading and writing. For instance, :py:class:`emen2.db.record.Record` and :py:class:`emen2.db.group.Group`. It is a subclass
    of :py:class:`BaseDBObject`; see that class for additional documentation.

    Two additional attributes are provided:
    -    permissions
    -    groups

    The permissions attribute is of the "acl" vartype. It is a list comprised of four
    lists or user names, denoting the following levels of permissions:

    Level 0 - Read
        Permission to read the item

    Level 1 - Comment
        Permission to add comments, if the item supports it

    Level 2 - Write
        Permission to change record attributes/parameters

    Level 3 - Owner
        Permission to change the item's permissions and groups

    The groups attribute is a set of group names. The permissions attribute of
    each group will be overlaid on top of the item's permissions. For instance,
    a user who has comment permissions in a listed group will have comment
    permissions on this item. There are a few built-in groups: administrators,
    read-only administrators, authenticated users, anonymous users, etc. See the
    Group class documentation for additional details.

    Changes to permissions and groups do not trigger an update to the
    modification time and user.


    :attr permissions: Access control list
    :attr groups: Groups

    """
    #These methods are overridden from BaseDBObject:
    #    init, setContext, isowner, writable,
    #The following methods are added to BaseDBObject:
    #    addumask, addgroup, removegroup, removeuser, 
    #     adduser, getlevel, ptest, readable, commentable, 
    #     members, owners, setgroups, setpermissions

    # Changes to permissions and groups, along with parents/children,
    # are not logged.
    attr_public = BaseDBObject.attr_public | set(['permissions', 'groups'])

    def init(self, d):
        """Initialize the permissions and groups

        This method overrides :py:meth:`BaseDBObject.init`
        """
        super(PermissionsDBObject, self).init(d)

        p = {}
        # Results of security test performed when the context is set
        # correspond to, read,comment,write and owner permissions,
        # return from setContext
        p['_ptest'] = [True,True,True,True]

        # Setup the base permissions
        p['permissions'] = [[],[],[],[]]
        p['groups'] = set()

        if self._ctx.username != 'root':
            p['permissions'][3].append(self._ctx.username)

        self.__dict__.update(p)


    ##### Setters #####

    def _set_permissions(self, key, value, vtm=None, t=None):
        self.setpermissions(value)
        return set(['permissions'])

    def _set_groups(self, key, value, vtm=None, t=None):
        self.setgroups(value)
        return set(['groups'])


    ##### Permissions checking #####

    def setContext(self, ctx):
        """Check read permissions and bind Context.

        This method overrides :py:meth:`BaseDBObject.setContext`

        :param ctx: the context to check access against.
        :type: :py:class:`emen2.db.context.Context`
        """

        # Check if we can access this item..
        self.__dict__['_ctx'] = ctx

        # test for owner access in this context.
        if self.isnew() or self._ctx.checkadmin() or self.creator == self._ctx.username:
            self.__dict__['_ptest'] = [True, True, True, True]
            return True

        self.__dict__['_ptest'] = [self._ctx.username in level for level in self.permissions]

        if self._ctx.checkreadadmin():
            self._ptest[0] = True

        for group in self.groups & self._ctx.groups:
            self._ptest[self._ctx.grouplevels[group]] = True

        # Allow us to override readable; previously just checks "any(self._ptest)"
        if not self.readable():
            raise emen2.db.exceptions.SecurityError, "Permission denied: %s %s"%(self.keytype, self.name)

        return self._ptest[0]

    def getlevel(self, user):
        """Get the user's permissions for this object

        :rtype: int
        """
        for level in range(3, -1, -1):
            if user in self.permissions[level]:
                return level

    def isowner(self):
        """Is the current user the owner?

        This method overrides :py:meth:`BaseDBObject.isowner`

        :rtype: bool
        """
        return self._ptest[3]

    def readable(self):
        """Does the user have permission to read the stored data (level 0)?

        :rtype: bool
        """
        # First check if we have any defined permission, then run
        # checkreadadmin() as a last minute rescue
        return any(self._ptest)

    def commentable(self):
        """Does user have permission to comment (level 1)?

        :rtype: bool
        """
        return any(self._ptest[1:])

    def writable(self, key=None):
        """Does the user have permission to change the stored data (level 2)?

        This method overrides :py:meth:`BaseDBObject.writable`

        :rtype: bool
        """
        return any(self._ptest[2:])

    def members(self):
        """Get all users with read permissions.

        :rtype: [str]
        """
        ###TODO:documentation: what does this do?
        return set(reduce(operator.concat, self.permissions))

    def owners(self):
        """Get all users with ownership permissions.

        :rtype: [str]
        """
        return self.permissions[3]

    def ptest(self):
        """Get a tuple with permission checks for each level"""
        ###FIXME: should _ptest be publicly accessible?
        return self._ptest


    ##### Users #####

    def _check_permformat(self, value):
        if hasattr(value, 'items'):
            v = [[],[],[],[]]
            ci = emen2.util.listops.check_iterable
            v[0] = ci(value.get('read'))
            v[1] = ci(value.get('comment'))
            v[2] = ci(value.get('write'))
            v[3] = ci(value.get('admin'))
            value = v
        return [[unicode(y) for y in x] for x in value]

    def adduser(self, users, level=0, reassign=False):
        """Add a user to the record's permissions

        :param users: A list of users to be added to the permissions
        :type users: [str]
        :param level: The permission level to give to the users
        :type level: int
        :param reassign: Whether or not the users added should be reassigned. (default False)
        :type reassign: bool
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
        :type value: [ [str], [str], [str] ]
        :param reassign: Whether or not the users added should be reassigned. (default False)
        :type reassign: bool

        """
        umask = self._check_permformat(value)

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
        """Remove a user from permissions"""
        if not users:
            return

        p = [set(x) for x in self.permissions]
        if not hasattr(users, "__iter__"):
            users = [users]
        users = set(users)
        p = [i-users for i in p]

        self.setpermissions(p)

    def setpermissions(self, value):
        """Set the permissions"""
        value = self._check_permformat(value)

        if len(value) != 4:
            raise ValueError, "Invalid permissions format: %s"%value

        return self._set('permissions', value, self.isowner())


    ##### Groups #####

    def addgroup(self, groups):
        """Add a group to the record"""
        if not hasattr(groups, "__iter__"):
            groups = [groups]
        g = self.groups | set(groups)
        self.setgroups(g)

    def removegroup(self, groups):
        """Remove a group from the record"""
        if not hasattr(groups, "__iter__"):
            groups = [groups]
        g = self.groups - set(groups)
        self.setgroups(g)

    def setgroups(self, groups):
        """Set the object's groups"""
        groups = emen2.util.listops.check_iterable(groups)
        return self._set('groups', set(groups), self.isowner())



__version__ = "$Revision: 1.75 $".split(":")[1][:-1].strip()
