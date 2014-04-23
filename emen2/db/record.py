"""Record DBOs."""

import collections
import copy

# EMEN2 imports
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.recorddef

class Record(emen2.db.dataobject.PermissionsDBObject):
    """Database Record.

    Provides the following additional parameters:
        rectype, history, comments

    This class represents a single database record. In a sense this is an
    instance of a particular RecordDef, however, note that it is not required
    to have a value for every field described in the RecordDef, although this
    will often be the case. This class is a subclass of PermissionsDBObject
    (and BaseDBObject); see these classes for additinal documentation.

    The RecordDef name is stored in the 'rectype' parameter. Currently, this
    cannot be changed after a Record is created, even by admins. However, this
    functionality may be provided at some point in the future.

    Unlike most other DBOs, Records allow arbitrary parameters
    as long as they are valid EMEN2 Parameters. 
    
    Changes to these parameters are always logged in the history
    log, described below, and will always trigger an update to the
    modification time.

    Records contain an integrated log of all changes over the entire history
    of the record. In a sense, as in a physical lab notebook, an original value
    can never be changed, only superceded. This log is stored in the 'history'
    parameter, which is a list containing a tuple entry for every change made,
    in the following format:

    0
        User
    1
        Time of change
    2
        Parameter changed
    3
        Previous parameter value

    The history log is immutable, even to admins, and is updated when the item
    is committed. 
    
    Users also can store free-form textual comments in the comments parameter,
    either by setting the comments key (item['comments'] = 'Test') or through
    the addcomment() method. Comments will stored as plain text, and usually
    displayed with Markdown-type formatting applied. Like the history log,
    comments are immutable once set, even to admins. Each new comment is added
    to the 'comments' list as a tuple with the format:

    0
        User
    1
        Time of comment
    2
        Comment text

    The following methods are overridden:
    
        init        Init the rectype, comments, and history
        keys        Add parameter keys

    :attr rectype: Associated RecordDef
    """

    def __repr__(self):
        return "<%s %s, %s at %x>" % (self.__class__.__name__, self.name, self.rectype, id(self))

    def init(self):
        super(Record, self).init()
        self.data['rectype'] = None

    def validate(self):
        """Validate the record before committing."""
        # Check the rectype and any required parameters
        # (Check the cache for the recorddef)
        if not self.rectype:
            raise self.error('Protocol required')
        cachekey = ('recorddef', self.rectype)
        hit, rd = self.ctx.cache.check(cachekey)
        if not hit:
            try:
                rd = self.ctx.db.recorddef.get(self.rectype, filt=False)
            except KeyError:
                raise self.error('No such protocol: %s'%self.rectype)
            self.ctx.cache.store(cachekey, rd)

    ##### Setters #####
    
    def _set_rectype(self, key, value):
        if not self.isnew():
            raise self.error("Cannot change protocol from %s to %s."%(self.rectype, value))
        self._set(key, self._strip(value), self.isowner())
        
    def _setitem(self, key, value):
        """Set a parameter value."""
        value = self._validate(key, value)
        self._set(key, value, self.writable())
