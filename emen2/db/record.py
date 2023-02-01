# $Id: record.py,v 1.82 2012/10/01 23:46:45 irees Exp $
"""Record DBOs

Classes:
    Record
    RecordDB

"""

import collections
import copy

# EMEN2 imports
import emen2.db.btrees
import emen2.db.datatypes
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.recorddef
import emen2.util.listops as listops



class Record(emen2.db.dataobject.PermissionsDBObject):
    """Database Record.

    Provides the following additional attributes:
        rectype, history, comments

    This class represents a single database record. In a sense this is an
    instance of a particular RecordDef, however, note that it is not required
    to have a value for every field described in the RecordDef, although this
    will usually be the case. This class is a subclass of PermissionsDBObject
    (and BaseDBObject); see these classes for additinal documentation.

    The RecordDef name is stored in the rectype attribute. Currently, this
    cannot be changed after a Record is created, even by admins. However, this
    functionality may be provided at some point in the future.

    Unlike most other DBOs, Records allow arbitrary attributes
    as long as they are valid EMEN2 Parameters. These are stored in the params
    attribute, which is a dictionary with parameter names as keys.  The params
    attribute is effectively private and not exported. Instead, it is part of
    the mapping interface. Items can be set with __setitem__
    (record['parameter'] = Value) or through an update(). When an item is
    exported (e.g. JSON), the contents of param are in the regular dictionary
    of attributes. Changes to these parameters are always logged in the history
    log, described below, and will always trigger an update to the
    modification time.

    Records contain an integrated log of all changes over the entire history
    of the record. In a sense, as in a physical lab notebook, an original value
    can never be changed, only superceded. This log is stored in the history
    attribute, which is a list containing a tuple entry for every change made,
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
    is committed. From a database standpoint, this is rather odd behavior. Such
    tasks would generally be handled with an audit log of some sort. However,
    in this case, as an electronic representation of a Scientific lab notebook,
    it is absolutely necessary that all historical values are permanently
    preserved for any field, and there is no particular reason to store this
    information in a separate file. Generally speaking, such changes should be
    infrequent. When a value is edited, the user interface should generally
    prompt the user for a comment describing the reason for the change. If
    provided, the comment and the history log item will have the same timestamp.

    Users also can store free-form textual comments in the comments attribute,
    either by setting the comments key (item['comments'] = 'Test') or through
    the  addcomment() method. Comments will stored as plain text, and usually
    displayed with Markdown-type formatting applied. Like the history log,
    comments are immutable once set, even to admins. Additionally, parameters
    can be updated inside of a comment using the RecordDef view syntax:
        $$parameter="value"

    Each new comment is added to the comments list as a tuple with the format:

    0
        User
    1
        Time of comment
    2
        Comment text


    The following methods are overridden:

    init
                Init the rectype, comments, and history
    keys
                Add parameter keys

    :attr history: History log
    :attr comments: Comments log
    :attr rectype: Associated RecordDef

    """

    #: Attributes readable by the user
    attr_public = emen2.db.dataobject.PermissionsDBObject.attr_public | set(['comments', 'history', 'rectype'])

    #: Attributes that cannot be edited directly by the user
    attr_protected = emen2.db.dataobject.PermissionsDBObject.attr_protected | set(['comments', 'history'])

    #: Attributes required for validation
    attr_required = set(['rectype'])

    #: The id of the record, for backwards compatibility only
    recid = property(lambda s:s.name)

    def init(self, d):
        # Call PermissionsDBObject init
        super(Record, self).init(d)

        # rectype is required
        # Access to RecordDef is checked during validation
        self.__dict__['rectype'] = None

        # comments, history, and other param values
        self.__dict__['comments'] = []
        self.__dict__['history'] = []
        self.__dict__['params'] = {}
        
        # Records are initialized with these two parameters....
        # There is no reason they couldn't be regular attributes -- just historical.
        self.__dict__['params']['date_occurred'] = self.__dict__['creationtime']
        self.__dict__['params']['performed_by'] = self.__dict__['creator']


    def __repr__(self):
        return "<%s %s, %s at %x>" % (self.__class__.__name__, self.name, self.rectype, id(self))


    ##### Setters #####

    def _set_rectype(self, key, value, vtm=None, t=None):
        if not self.isnew():
            self.error("Cannot change rectype")
        self.__dict__['rectype'] = unicode(value)
        return set(['rectype'])
        

    def _set_comments(self, key, value, vtm=None, t=None):
        """Bind record['comments'] setter"""
        return self.addcomment(value, t=t)

    # in Record, params not in self.attr_public are put in self.params{}.
    def _setoob(self, key, value, vtm=None, t=None):
        """Set a parameter value."""
        # Check write permission
        if not self.writable():
            msg = "Insufficient permissions to change param %s"%key
            self.error(msg, e=emen2.db.exceptions.SecurityError)

        # No change
        if self.params.get(key) == value:
            return set()

        self._addhistory(key, t=t)
        # Really set the value
        self.params[key] = value
        return set([key])


    ##### Tweaks to mapping methods #####

    def __getitem__(self, key, default=None):
        """Default behavior is similar to .get: return None as default"""
        if key in self.attr_public:
            return getattr(self, key, default)
        else:
            return self.params.get(key, default)

    def keys(self):
        """All retrievable keys for this record"""
        return self.params.keys() + list(self.attr_public)

    def paramkeys(self):
        return self.params.keys()

    ##### Comments and history #####

    def _addhistory(self, param, t=None):
        """Add an entry to the history log."""
        # Changes aren't logged on uncommitted records
        if self.isnew():
            return

        if not param:
            raise Exception, "Unable to add item to history log"

        vtm, t = self._vtmtime(t=t)
        self.history.append((unicode(self._ctx.username), unicode(t), unicode(param), self.params.get(param)))

    def addcomment(self, value, vtm=False, t=None):
        """Add a comment. Any $$param="value" comments will be parsed and set as values.

        :param value: The comment to be added
        """
        if not self.commentable():
            self.error('Insufficient permissions to add comment', e=emen2.db.exceptions.SecurityError)

        if not value:
            return set()

        vtm, t = self._vtmtime(vtm, t)
        cp = set()
        if value == None:
            return set()

        # Grumble...
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
                self.error("Cannot set comments inside a comment", warning=False)

            # Now update the values of any embedded params
            for i,j in d.items():
                cp |= self.__setitem__(i, j, vtm=vtm, t=t)

            # Store the comment string itself
            self.comments.append((unicode(self._ctx.username), unicode(t), unicode(value)))
            cp.add('comments')

        return cp

    def revision(self, revision=None):
        """Calculate the record's values to a point in the past

        :param revision: the revision of the record to start
        """

        history = copy.copy(self.history)
        comments = copy.copy(self.comments)
        comments.append((self.get('creator'), self.get('creationtime'), 'Created'))
        paramcopy = {}

        bydate = collections.defaultdict(list)

        for i in filter(lambda x:x[1]>=revision, history):
            bydate[i[1]].append([i[0], i[2], i[3]])

        for i in filter(lambda x:x[1]>=revision, comments):
            bydate[i[1]].append([i[0], None, i[2]])

        revs = sorted(bydate.keys(), reverse=True)

        for rev in revs:
            for item in bydate.get(rev, []):
                # user, param, oldval
                if item[1] == None:
                    continue
                if item[1] in paramcopy.keys():
                    newval = paramcopy.get(item[1])
                else:
                    newval = self.get(item[1])

                paramcopy[item[1]] = copy.copy(item[2])
                # item[2] = newval

        return bydate, paramcopy


    ##### Validation #####

    def validate(self, vtm=None, t=None):
        """Validate the record before committing.

        :param vtm: the :py:class:`~.datatypes.VartypeManager` used to validate param values
        :type vtm: :py:class:`.datatypes.VartypeManager`
        :param t: the time of validation

        """
        # Cut out any None's
        # The rest of the parameters are validated 
        # when they are set or updated.
        pitems = self.params.items()
        for k,v in pitems:
            if not v and v != 0 and v != False:
                del self.params[k]

        # Check the rectype and any required parameters
        # (Check the cache for the recorddef)
        vtm, t = self._vtmtime(vtm=vtm, t=t)
        cachekey = vtm.get_cache_key('recorddef', self.rectype)
        hit, rd = vtm.check_cache(cachekey)

        if not self.rectype:
            self.error('Protocol required')

        if not hit:
            try:
                rd = self._ctx.db.recorddef.get(self.rectype, filt=False)
            except KeyError:
                self.error('No such protocol: %s' % self.rectype)
            vtm.store(cachekey, rd)

        # This does rely somewhat on validators returning None if empty..
        for param in rd.paramsR:
            if self.get(param) == None:
                self.error("Required parameter: %s"%(param))

        self.__dict__['rectype'] = unicode(rd.name)

        # Look up any additional validators..
        validator = emen2.db.recorddef.RecordDef.get_handler(self)
        if validator:
            validator.validate()



class RecordDB(emen2.db.btrees.RelateDB):
    cfunc = False     # Do not sort the BTree keys as integers
    dataclass = Record
    

    def _name_generator(self, item, txn=None):
        # Set name policy in this method.
        return unicode(self._incr_sequence(txn=txn))


    def openindex(self, param, txn=None):
        # Parents / children
        ind = super(RecordDB, self).openindex(param, txn=txn)
        if ind:
            return ind

        # Check the paramdef to see if it's indexed
        pd = self.dbenv["paramdef"].get(param, filt=False, txn=txn)
        if not pd or pd.vartype not in self.dbenv.indexablevartypes or not pd.indexed:
            return None

        # Open the index
        vtm = emen2.db.datatypes.VartypeManager()
        tp = vtm.getvartype(pd.vartype).keyformat
        ind = emen2.db.btrees.IndexDB(filename=self._indname(param), keyformat=tp, dataformat=self.keyformat, dbenv=self.dbenv)
        return ind


    def hide(self, names, ctx=None, txn=None):
        recs = self.cgets(names, ctx=ctx, txn=txn)
        crecs = []
        for rec in recs:
            rec.setpermissions([[],[],[],[]])
            rec.setgroups([])
            if rec.parents and rec.children:
                rec["comments"] = "Record hidden by unlinking from parents %s and children %s"%(", ".join([unicode(x) for x in rec.parents]), ", ".join([unicode(x) for x in rec.children]))
            elif rec.parents:
                rec["comments"] = "Record hidden by unlinking from parents %s"%", ".join([unicode(x) for x in rec.parents])
            elif rec.children:
                rec["comments"] = "Record hidden by unlinking from children %s"%", ".join([unicode(x) for x in rec.children])
            else:
                rec["comments"] = "Record hidden"

            rec['deleted'] = True
            rec.children = set()
            rec.parents = set()
            crecs.append(rec)

        return self.cputs(crecs, ctx=ctx, txn=txn)

    def groupbyrectype(self, names, ctx=None, txn=None):
        """Group Records by Rectype. Filters for permissions.

        :param names: Record(s) or Record name(s)
        :returns: {rectype:set(record names)}
        """
        if not names:
            return {}

        # Allow either Record(s) or Record name(s) as input
        ret = collections.defaultdict(set)
        recnames, recs, other = listops.typepartition(names, basestring, emen2.db.dataobject.BaseDBObject)

        if len(recnames) < 1000:
            # Just get the rest of the records directly
            recs.extend(self.cgets(recnames, ctx=ctx, txn=txn))
        else:
            # Use the index for large numbers of records
            ind = self.getindex("rectype", txn=txn)
            # Filter permissions
            names = self.filter(recnames, ctx=ctx, txn=txn)
            while names:
                # get a random record's rectype
                rid = names.pop()
                rec = self.get(rid, txn=txn)
                # get the set of all records with this recorddef
                ret[rec.rectype] = ind.get(rec.rectype, txn=txn) & names
                # remove the results from our list since we have now classified them
                names -= ret[rec.rectype]
                # add back the initial record to the set
                ret[rec.rectype].add(rid)

        for i in recs:
            ret[i.rectype].add(i.name)

        return ret

    def names(self, names=None, ctx=None, txn=None, **kwargs):
        if names is not None:
            return self.filter(names, rectype=kwargs.get('rectype'), ctx=ctx, txn=txn)

        if ctx.checkreadadmin():
            m = self.get_max(txn=txn)
            return set(map(unicode, range(0, m)))
            # return set(self.keys(txn=txn))

        ind = self.getindex("permissions", txn=txn)
        indc = self.getindex('creator', txn=txn)
        indg = self.getindex("groups", txn=txn)
        ret = ind.get(ctx.username, set(), txn=txn)
        ret |= indc.get(ctx.username, set(), txn=txn)
        for group in sorted(ctx.groups, reverse=True):
            ret |= indg.get(group, set(), txn=txn)

        return ret

    def filter(self, names, rectype=None, ctx=None, txn=None):
        """Filter for permissions.

        :param names: Record name(s).
        :returns: Readable Record names.
        """

        names = self.expand(names, ctx=ctx, txn=txn)

        if rectype:
            ind = self.getindex('rectype', txn=txn)
            # ian: use the context.
            rd = set()
            for i in ctx.db.recorddef.get(listops.check_iterable(rectype)):
                rd |= ind.get(i.name, txn=txn)
            names &= rd

        if ctx.checkreadadmin():
            return names

        # ian: indexes are now faster, generally...
        if len(names) <= 1000:
            crecs = self.cgets(names, ctx=ctx, txn=txn)
            return set([i.name for i in crecs])

        # Make a copy
        find = copy.copy(names)

        # Use the permissions/groups index
        ind = self.getindex('permissions', txn=txn)
        indc = self.getindex('creator', txn=txn)
        indg = self.getindex('groups', txn=txn)

        find -= ind.get(ctx.username, set(), txn=txn)
        find -= indc.get(ctx.username, set(), txn=txn)
        for group in sorted(ctx.groups):
            if find:
                find -= indg.get(group, set(), txn=txn)

        return names - find



__version__ = "$Revision: 1.82 $".split(":")[1][:-1].strip()
