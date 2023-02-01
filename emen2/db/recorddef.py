# $Id: recorddef.py,v 1.39 2012/07/28 06:31:18 irees Exp $
"""RecordDef (Protocol) classes

Classes:
    RecordDef
    RecordDefDB

"""

import re
import textwrap

# EMEN2 imports
import emen2.db.btrees
import emen2.db.dataobject


def parseparmvalues(text):
    regex = emen2.db.database.VIEW_REGEX

    params = set()
    required = set()
    defaults = {}

    for match in regex.finditer(text):
        n = match.group('name')
        t = match.group('type')

        if not n:
            continue
        if t == '$' or t == '*':
            params.add(match.group('name'))
            if match.group('def'):
                defaults[n] = match.group('def')
        if t == '*':
            required.add(n)

    return params, defaults, required



class RecordDef(emen2.db.dataobject.BaseDBObject):
    """RecordDefs, aka Protocols.

    RecordDefs, aka Protocols, function as templates for Records. Each Record must be an instance of a defined RecordDef.
    The RecordDef defines the default parameters that make up a record, and a set of presentation formats ('views'). The 'mainview'
    is parsed for parameters and becomes the default view. Other important views that are used by the web interface are:

        recname            A simple title for each record built from record values
        tabularview        Columns to use in table views

    RecordDefs may have parent/child relationships, similar to Records.

    @attr desc_short Short description. Shown in many places in the interface as the label for this RecordDef.
    @attr desc_long Long description. Shown as help in new record page.
    @attr mainview Default protocol view. This should be an expanded form, similar to a lab notebook or experimental protocol. This should be IMMUTABLE, as it may describe a particular experiment. However, admins are allowed to edit the mainview if it is absolutely necessary.
    @attr views Dictionary of additional views. Usually recname/tabularview will be defined, as well as defaultview
    @attr private Mark this RecordDef as private. False for public access, True for private. If private, you must be admin or able to read a record of this type to access the RecordDef
    @attr typicalchld A list of RecordDefs that are generally seen as children of this RecordDef. This refers to Records, not the RecordDef ontology, which describes relationships between RecordDefs themselves. e.g., "grid_imaging" Records are often children of "subprojects."
    @attr params Dictionary of all params found in all views (keys), with any default values specified (as value) (read-only attribute).
    @attr paramsK List of all params found in all views (read-only attribute).
    @attr paramsR Parameters that are required for a Record of this RecordDef to validate (read-only attribute).
    @attr owner Current owner of RecordDef. May be different than creator. Gives permission to edit views.
    """

    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(["mainview", "views", "private", "typicalchld", "desc_long", "desc_short"])
    attr_required = set(['mainview'])

    # Add custom validators
    _handlers = {}

    def init(self, d):
        super(RecordDef, self).init(d)

        # A string defining the experiment with embedded params
        # this is the primary definition of the contents of the record
        # Required parameter..
        self.__dict__['mainview'] = ''

        # Dictionary of additional (named) views for the record
        self.__dict__['views'] = {}

        # If this is True, this RecordDef may only be retrieved by its owner
        # or by someone with read access to a record of this type
        self.__dict__['private'] = False

        # A list of RecordDef names of typical child records for this RecordDef
        self.__dict__['typicalchld'] = []

        # Short description
        self.__dict__['desc_short'] = None

        # Long description
        self.__dict__['desc_long'] = None

        # The following are automatically generated
        # A dictionary keyed by the names of all params used in any of the views
        # values are the default value for the field.
        # this represents all params that must be defined to have a complete
        # representation of the record. Note, however, that such completeness
        # is NOT REQUIRED to have a valid Record
        self.__dict__['params'] = {}

        # keys from params()
        self.__dict__['paramsK'] = set()

        # required parameters (will throw exception on record commit if empty)
        self.__dict__['paramsR'] = set()


    ##### Setters #####

    def _set_mainview(self, key, value, vtm=None, t=None):
        """Only an admin may change the mainview"""
        if not self.isnew() and not self._ctx.checkadmin():
            self.error("Cannot change mainview")

        value = unicode(textwrap.dedent(value))
        ret = self._set('mainview', value, self.isowner())
        self.findparams()
        return ret

    # These require normal record ownership
    def _set_views(self, key, value, vtm=None, t=None):
        views = {}
        value = value or {}
        for k,v in value.items():
            views[k] = unicode(textwrap.dedent(v))

        ret = self._set('views', views, self.isowner())
        self.findparams()
        return ret

    def _set_private(self, key, value, vtm=None, t=None):
        return self._set('private', int(value), self.isowner())

    # ian: todo: Validate that these are actually valid RecordDefs
    def _set_typicalchld(self, key, value, vtm=None, t=None):
        value = emen2.util.listops.check_iterable(value)
        value = filter(None, [unicode(i) for i in value]) or None
        return self._set('typicalchld', value, self.isowner())

    def _set_desc_short(self, key, value, vtm=None, t=None):
        return self._set('desc_short', unicode(value or self.name), self.isowner())

    def _set_desc_long(self, key, value, vtm=None, t=None):
        return self._set('desc_long', unicode(value or ''), self.isowner())


    ##### RecordDef Methods #####

    # ian: todo: important!! setContext for RecordDef
    # def setContext(self, ctx):
        # def accessible(self):
        #     """Does current Context allow access to this RecordDef?"""
        #     result = False
        #     if not self.private:
        #         result = True
        #     elif self._ctx.username == self.owner:
        #         result = True
        #     elif self._ctx.checkreadadmin():
        #         result = True
        #     return result

    def findparams(self):
        """This will update the list of params by parsing the views"""
        t, d, r = parseparmvalues(self.mainview)

        for i in self.views.values():
            t2, d2, r2 = parseparmvalues(i)
            t |= t2
            r |= r2
            for j in t2:
                # ian: fix for: empty default value in a view unsets default value specified in mainview
                d.setdefault(j, d2.get(j))

        p = {}
        p['params'] = d
        p['paramsK'] = t
        p['paramsR'] = r
        self.__dict__.update(p)

    def validate(self, vtm=None, t=None):
        # Run findparams one last time before we commit...
        if not self.mainview:
            self.error("Main protocol (mainview) required")
        self.findparams()

    # This handler implementation is not finalized.
    @classmethod
    def register(cls, names):
        def f(o):
            # print "Registering RecordDef handler:", o
            for name in names:
                if name in cls._handlers:
                    raise ValueError("""RecordDef handler %s already registered""" % name)
                cls._handlers[name] = o
            return o
        return f

    @classmethod
    def get_handler(cls, rec=None):
        handler = None
        if rec:
            handler = rec.get('rectype')
        handler = cls._handlers.get(handler, RecordDefHandler)
        return handler(rec)


# This is not finalized. Subject to change. 
class RecordDefHandler(object):
    def __init__(self, rec):
        self.rec = rec

    def validate(self):
        # print "Base validator...", self.rec
        return


class RecordDefDB(emen2.db.btrees.RelateDB):
    dataclass = RecordDef



__version__ = "$Revision: 1.39 $".split(":")[1][:-1].strip()
