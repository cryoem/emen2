"""RecordDef (Protocol) classes."""

import re
import textwrap

# EMEN2 imports
import emen2.db.dataobject

def parseparmvalues(text):
    regex = re.compile(emen2.db.database.VIEW_REGEX_M)
    params = set()
    required = set()
    defaults = {}

    for match in regex.finditer(text):
        n = match.group('name')
        if not n:
            continue
        if n.endswith('?'):
            pass
        elif n.endswith(')'):
            pass
        elif n.endswith('*'):
            required.add(n[:-1])
        else:
            params.add(n)
        # if match.group('def'):
        #   defaults[n] = match.group('def')

    return params, defaults, required

class RecordDef(emen2.db.dataobject.BaseDBObject):
    """RecordDefs, aka Experimental Protocols.

    RecordDefs, aka Experimental Protocols, function as templates for Records.
    Each Record has an associated RecordDef. The RecordDef defines the default
    parameters that make up a record, and a set of presentation formats (views).
    
    The 'mainview' is parsed for parameters and becomes the default view. This
    should be an expanded form, similar to a lab notebook or experimental
    protocol. This should be immutable, as it may describe a particular
    experiment. However, admins are allowed to edit the mainview if it is
    absolutely necessary.
    
    Additional views are in the 'views' dictionary:

        recname            A simple title for each record built from record values
        tabularview        Columns to use in table views

    Some details from the mainview are cached in 'params' (default values) and
    'paramsR' (required params).

    RecordDefs may have parent/child relationships, similar to Records.

    RecordDefs can be marked as private by setting the 'private' attribute. If
    private, you must be admin or able to read a record of this type to access
    the RecordDef
    
    RecordDefs can suggest values for child records using the 'typicalchld'
    attribute, e.g., "grid_imaging" Records are often children of "project"
    Records.

    These BaseDBObject methods are overridden:

        init            Set attributes
        setContext      Check read permissions and bind Context
        validate        Check required attributes

    :attr desc_short: Short description.
    :attr desc_long: Long description. Shown as help in new record page.
    :attr mainview: Default protocol view.
    :attr views: Dictionary of additional views.
    :attr private: Mark this RecordDef as private.
    :attr typicalchld: A list of RecordDefs that are generally seen as children.
    :attr params: Dictionary of all params found in all views (keys), with any default values specified (as value) (read-only attribute).
    :attr paramsR: Parameters that are required for a Record of this RecordDef to validate (read-only attribute).
    :attr owner: Current owner of RecordDef. May be different than creator. Gives permission to edit views.
    """

    public = emen2.db.dataobject.BaseDBObject.public | set(["mainview", "views", "private", "typicalchld", "desc_long", "desc_short"])

    def init(self, d):
        super(RecordDef, self).init(d)

        # A string defining the experiment with embedded params
        # this is the primary definition of the contents of the record
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

        # Required parameters (will throw exception on record commit if empty)
        self.__dict__['paramsR'] = set()

    # ian: todo: Important!! If we can access a record with the recorddef...
    def setContext(self, ctx):
        super(RecordDef, self).setContext(ctx=ctx)
        if not self.private:
            return True
        # Private RecordDef...
        if self._ctx.username == self.owner:
            return True
        elif self._ctx.checkreadadmin():
            return True
        raise PermissionsError, "Private RecordDef"

    def validate(self):
        # Run findparams one last time before we commit...
        if not self.mainview:
            raise self.error("Main protocol (mainview) required")
        self._findparams()

    ##### Setters #####

    def _set_mainview(self, key, value):
        """Only an admin may change the mainview"""
        if not self.isnew() and not self._ctx.checkadmin():
            raise self.error("Cannot change mainview")
        value = self._strip(textwrap.dedent(value))
        ret = self._set('mainview', value, self.isowner())
        self._findparams()
        return ret

    # These require normal record ownership
    def _set_views(self, key, value):
        views = {}
        value = value or {}
        for k,v in value.items():
            views[unicode(k)] = unicode(textwrap.dedent(v))
        ret = self._set('views', views, self.isowner())
        self._findparams()
        return ret

    def _set_private(self, key, value):
        return self._set('private', int(value), self.isowner())

    # ian: todo: Validate that these are actually valid RecordDefs
    def _set_typicalchld(self, key, value):
        value = map(self._strip, emen2.utils.check_iterable(value))
        value = filter(None, value) or None
        return self._set('typicalchld', value, self.isowner())

    def _set_desc_short(self, key, value):
        return self._set('desc_short', self._strip(value or self.name), self.isowner())

    def _set_desc_long(self, key, value):
        return self._set('desc_long', self._strip(value), self.isowner())

    ##### RecordDef Methods #####

    def _findparams(self):
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
        p['paramsR'] = r
        self.__dict__.update(p)

