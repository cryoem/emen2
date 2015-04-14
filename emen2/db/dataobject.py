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

    Parameters are stored in the self.data dict, and this is saved when
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
        # ugh..
        self.__dict__['history'] = [] 
        self.__dict__['comments'] = []
        self.__dict__['rels'] = []
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
        self.data['hidden'] = None
    
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

    def readable(self):
        """Check read permissions."""
        return True

    def commentable(self):
        """Does user have permission to comment (level 1)?"""
        return self.isowner()

    def writable(self, key=None):
        """Check write permissions."""
        return self.isowner()

    def isowner(self):
        """Check ownership permissions."""
        if self.isnew():
            return True
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
    
    ##### Magic #####
    
    def _setattr(self, key, value):
        object.__setattr__(self, key, value)
    
    def __setattr__(self, key, value):
        # If we have a setter method defined, use that.
        try:
            setter = object.__getattribute__(self, '_set_%s'%key)
        except AttributeError:
            setter = self._setattr
        setter(key, value)
            
    def __getattr__(self, key):
        # If we have a setter method, look in self.data.
        try:
            setter = object.__getattribute__(self, '_set_%s'%key)
        except AttributeError:
            raise
        return self.data.get(key)

    def _setitem(self, key, value):
        self.warn('Cannot set parameter "%s" in this way.'%(key))

    def __setitem__(self, key, value):
        # If a "_set_<key>" method exists, use this.
        # Otherwise, use _setitem as the setter. This will raise an error
        #    (default) or allow 'out of bounds' attrs (see Record class)
        if value == self.get(key):
            return
        getattr(self, '_set_%s'%key, self._setitem)(key, value)

    def __getitem__(self, key, default=None):
        return self.data[key]

    ##### Real updates #####

    def _set(self, key, value, check):
        """Actually set a value. 
        
        Check must be True; e.g.:
            self._set('key', 'value', self.isowner())
        This is to encourage the explicit permissions checking.
        """
        # No change
        if self.data.get(key) == value:
            return
        # If the permissions check is not true.
        if not check:
            msg = 'Insufficient permissions to change parameter: %s'%key
            raise self.error(msg, e=emen2.db.exceptions.PermissionsError)
        # Update the history log with the key and old value.
        # Only permissions/groups do not trigger a modifytime update.
        if not self.isnew() and key not in ['permissions', 'groups']:
            self.data['modifytime'] = emen2.db.database.utcnow()
            self.data['modifyuser'] = self.ctx.user
            self._addhistory(key, self.data.get(key))
        # Set the value.
        # print "set...", self.name, key, value, self.data.get(key)
        self.data[key] = value

    ##### Setters for core parameters. #####
    
    def _set_name(self, key, value):
        self._set(key, value, self.isnew())
        
    def _set_uri(self, key, value):
        self._set(key, value, self.isnew())

    def _set_hidden(self, key, value):
        self._set(key, value, self.isowner())

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

    # Reserved keys.
    def _set_comments(self, key, value):
        pass
    
    def _set_history(self, key, value):
        pass

    def _set_rels(self, key, value):
        pass

    def _set_children(self, key, value):
        pass

    def _set_parents(self, key, value):
        pass
        
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

    def warn(self, msg='', e=None):
        self.error(msg=msg, e=e, warning=True)

    def error(self, msg='', e=None, warning=False):
        """Raise a ValidationError exception.
        If warning=True, pass the exception, but make a note in the log.
        """
        if e == None:
            e = emen2.db.exceptions.ValidationError
        if not msg:
            msg = e.__doc__
        if warning:
            emen2.db.log.warn("Warning: %s: %s"%(self.name, e(msg)))
            pass
        return e(msg)

    ##### Comments and history #####

    def _addhistory(self, key, old):
        """Add an entry to the history log."""
        # Changes aren't logged on uncommitted records
        # if self.isnew():
        #     return
        c = {
            'name': self.name,
            'keytype': self.keytype,
            'user': unicode(self.ctx.user),
            'time': unicode(emen2.db.database.utcnow()),
            'key': unicode(key),
            'value': old
        }
        # print "HISTORY:", c
        self.history.append(c)

    def addcomment(self, value):
        """Add a comment."""
        if not self.commentable():
            raise self.error('Insufficient permissions to add comment.', e=emen2.db.exceptions.PermissionsError)
        if not value:
            return
        # Allow setting values inside comments.
        # d = {}
        # if not value.startswith("LOG"): # legacy fix..
        #     d = emen2.db.recorddef.parseparmvalues(value)[1]
        # if d.has_key("comments"):
        #     # Always abort
        #     raise self.error("Cannot set comments inside a comment.")
        # Now update the values of any embedded params
        # for i,j in d.items():
        #     self.__setitem__(i, j)
        # Store the comment string itself
        c = {
            'name': self.name,
            'keytype': self.keytype,
            'user': unicode(self.ctx.user),
            'time': unicode(emen2.db.database.utcnow()),
            'key': 'comments',
            'value': unicode(value)
        }
        # print "COMMENT:", c
        self.comments.append(c)

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

    Read: Permission to read the item
    Comment: Permission to add comments, if the item supports it
    Write: Permission to change record
    Owner: Permission to change the item's permissions and groups

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
        self.data['permissions'] = {}
        self.data['groups'] = {}

    ##### Permissions checking #####

    def initContext(self, ctx):
        self.ctx = ctx
        self.data['creator'] = self.ctx.user
        self.data['modifyuser'] = self.ctx.user
        self.data['permissions'] = {'owner':[self.ctx.user]}

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
        self.ptest = []
        for level in ['read', 'comment', 'write', 'owner']:
            access = self.ctx.user in self.permissions.get(level, [])
            access = access or set(self.groups.get(level, [])) & self.ctx.groups
            self.ptest.append(access)

        # If read admin, set read access.
        if self.ctx.checkreadadmin():
            self.ptest[0] = True
        
        # Now, check if we can read.
        if not self.readable():
            raise emen2.db.exceptions.PermissionsError("Permission denied: %s"%(self.name))

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
        return set(reduce(operator.concat, self.permissions.values(), []))

    ##### Permissions #####

    def _set_permissions(self, key, value):
        self.setpermissions(value)

    def setpermissions(self, value):
        """Set the permissions."""
        value = self._validate_permissions(value)
        self._set('permissions', value, self.isowner())

    def _validate_permissions(self, value):
        ci = emen2.utils.check_iterable
        p = {}
        for k,v in value.items():
            p[k] = [i.strip() for i in ci(v)]
        if p.has_key(None):
            del p[None]
        for k in p.keys():
            if not p[k]:
                del p[k]
            if k not in ['read', 'comment', 'write', 'owner']:
                raise ValueError("Invalid permissions format.")
        return p

    def _permissions_merge(self, base, add):
        print "MERGE: base:", base, "add:", add
        addmembers = set()
        for i in add.values():
            addmembers |= set(i)
        out = {}
        print "clear out--", addmembers
        for level in ['read', 'comment', 'write', 'owner', None]:
            s = set(base.get(level, [])) - addmembers
            s |= set(add.get(level, []))
            out[level] = list(s)
        print "merged --", out
        return out

    def adduser(self, users, level='read'):
        """Add a user to the record's permissions."""
        value = {level: set(emen2.utils.check_iterable(users))}
        value = self._permissions_merge(self.permissions, value)
        self.setpermissions(value)

    def addumask(self, value):
        """Set permissions for users in several different levels at once."""
        value = self._permissions_merge(self.permissions, value)
        self.setpermissions(value)

    def removeuser(self, users):
        """Remove users from permissions."""
        value = {None: set(emen2.utils.check_iterable(users))}
        value = self._permissions_merge(self.permissions, value)
        del value[None]
        self.setpermissions(value)

    ##### Groups #####

    def _set_groups(self, key, value):
        self.setgroups(value)

    def setgroups(self, value):
        value = self._validate_permissions(value)
        self._set('groups', value, self.isowner())

    def addgroup(self, groups, level='read'):
        value = {level: set(emen2.utils.check_iterable(groups))}
        value = self._permissions_merge(self.groups, value)
        self.setgroups(value)

    def removegroup(self, groups):
        value = {None: set(emen2.utils.check_iterable(groups))}
        value = self._permissions_merge(self.groups, value)
        del value[None]
        self.setgroups(value)

class PrivateDBO(BaseDBObject):
    pass
    # def setContext(self, ctx=None):
    #     raise emen2.db.exceptions.PermissionsError("Private item.")
            
            
# History
class History(object):
    """Manage previously used values."""
    def __init__(self, data=None):
        self.data = data or []
    
    def find(self, key=None, value=None, user=None, limit=None):
        h = sorted(self.data, key=lambda x:x.get('time'))
        if key:
            h = [i for i in h if i.get('key') == key]
        if value:
            h = [i for i in h if i.get('value') == value]
        if user:
            h = [i for i in h if i.get('user') == user]
        if limit is not None:
            h = h[:limit]
        return h
    
    # def checkhistory(self, timestamp=None, user=None, param=None, value=None, limit=None):
    def checkfind(self, key=None, value=None, user=None, limit=None):
        """Check if an key or value is in the past :limit: items."""
        if self.find(key=key, value=value, user=user, limit=limit):
            return True
        return False
            
