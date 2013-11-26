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

    :attr history: History log
    :attr comments: Comments log
    :attr rectype: Associated RecordDef
    """

    #: Attributes readable by the user
    public = emen2.db.dataobject.PermissionsDBObject.public | set(['comments', 'history', 'rectype', 'hidden'])

    def __repr__(self):
        return "<%s %s, %s at %x>" % (self.__class__.__name__, self.name, self.rectype, id(self))

    def init(self, d):
        # Call PermissionsDBObject init
        super(Record, self).init(d)

        # rectype is required
        # Access to RecordDef is checked during validation
        self.data['rectype'] = None

        # comments, history, and other param values
        self.data['comments'] = []
        self.data['history'] = []

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

        # for param in rd.paramsR:
        #     if self.get(param) is None:
        #         raise self.error("Required parameter: %s"%(param))
        self.data['rectype'] = self._strip(rd.name)

    ##### Setters #####
    
    def _set_hidden(self, key, value):
        self._set(key, value, self.isowner())
    
    def _set_rectype(self, key, value):
        if not self.isnew():
            raise self.error("Cannot change rectype from %s to %s."%(self.rectype, value))
        self._set(key, self._strip(value), self.isowner())
        
    def _set_comments(self, key, value):
        """Bind record['comments'] setter"""
        self.addcomment(value)

    def _setoob(self, key, value):
        """Set a parameter value."""
        # Check write permission
        if not self.writable():
            msg = "Insufficient permissions to change param %s"%key
            raise self.error(msg, e=emen2.db.exceptions.PermissionsError)

        value = self._validate(key, value)

        # No change
        if self.data.get(key) == value:
            return

        # Really set the value
        self._addhistory(key)
        self.data[key] = value

    ##### Comments and history #####

    def _addhistory(self, param):
        """Add an entry to the history log."""
        # Changes aren't logged on uncommitted records
        if self.isnew():
            return
        if not param:
            raise Exception("Unable to add item to history log.")
        if self.data.get('history') is None:
            self.data['history'] = []            
        self.data['history'].append((unicode(self.ctx.username), unicode(self.ctx.utcnow), unicode(param), self.data.get(param)))

    def addcomment(self, value):
        """Add a comment. Any $$param="value" comments will be parsed and set as values.

        :param value: The comment to be added
        """
        if not self.commentable():
            raise self.error('Insufficient permissions to add comment.', e=emen2.db.exceptions.PermissionsError)

        if not value:
            return
        
        # Grumble...
        if self.data.get('comments') is None:
            self.data['comments'] = []
        newcomments = []
        existing = [i[2] for i in self.comments]
        if not hasattr(value, "__iter__"):
            value = [value]
        for c in value:
            if hasattr(c, "__iter__"):
                c = c[-1]
            if c and c not in existing:
                newcomments.append(unicode(c))

        # newcomments2 = []
        # updvalues = {}
        for value in newcomments:
            d = {}
            if not value.startswith("LOG"): # legacy fix..
                d = emen2.db.recorddef.parseparmvalues(value)[1]

            if d.has_key("comments"):
                # Always abort
                raise self.error("Cannot set comments inside a comment.", warning=False)

            # Now update the values of any embedded params
            for i,j in d.items():
                self.__setitem__(i, j)

            # Store the comment string itself
            self.data['comments'].append((unicode(self.ctx.username), unicode(self.ctx.utcnow), unicode(value)))
