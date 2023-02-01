# $Id: paramdef.py,v 1.42 2012/07/28 06:31:18 irees Exp $
"""Parameter DBOs

Classes:
    ParamDef
    ParamDefDB

"""

import functools
import time

# EMEN2 imports
import emen2.util.listops
import emen2.db.btrees
import emen2.db.dataobject
import emen2.db.magnitude



class ParamDef(emen2.db.dataobject.BaseDBObject):
    """Parameters.
    
    Provides the following attributes:
        desc_short, desc_long, vartype, choices, defaultunits, property, 
        indexed, iter, immutable, property, indexed, controlhint
    
    This class repesents a particular piece of data, either an attribute on a
    DBO, or a parameter on a Record. Please be aware that several
    attributes are effectively immutable, and cannot be easily changed after
    a ParamDef is created because it would change the meaning of existing
    recorded data or index formats. This is a subclass of BaseDBObject; see 
    that class for additional documentation.
    
    Each ParamDef has a vartype (data type), which provides a class for 
    displaying and validating the attribute/parameter value. Vartypes are
    defined as Vartype subclasses; see the vartypes module. Vartypes are usually 
    able to handle loosely formatted data and clean it up (validate), or raise 
    a ValidationError exception if it cannot be done, or if a value is invalid.
    The validation methods are usually called whenever an attribute/parameter
    is set on an item.
    
    The iter attribute is used in conjunction with the vartype to specify
    whether the ParamDef stores a single value, or a list of values. Most
    vartypes allow iter, but some do not. Check the specific Vartype class.
    Vartypes are usually good at validating a single value into an iterable
    value, but not the reverse. The vartype cannot be easily changed after 
    creation; to do so requires running a migration script, which could require
    changing or discarding data, and likely rebuilding indexes.
    
    When ParamDefs are displayed in certain contexts, such as being rendered
    in a view or as a table header, the desc_short and desc_long attributes
    are used to provide short and long descriptions, respectively, of the
    ParamDef and its intended uses and requirements. The desc_short attribute
    is required, desc_long is optional. Because they do not change the actual
    values of recorded data, they can be edited (within reason) after creation.
    
    The choices attribute can be used to provide a default list of choices
    when entering values. These are provided as suggestions for consistency
    among users, and are usually combined with query results to give additional
    common choices. However, for vartype 'choice', this attribute is enforced
    as the only allowed values. Choices can be edited after creation.
    
    Editing widgets are usually determined by the vartype (this choice is
    always up to that particular user interface.) However, some vartypes might
    be edited in several different fashions, and a particular editing control
    might be more effective than the default. In these cases, the controlhint
    attribute can be used to describe a different editing widget. This is
    totally implementation specific; it is only provided here as a string with
    no additional validation. The controlhint can be changed after creation.
    
    If a ParamDef represents a particular measurable physical property (length,
    volume, mass, pH, etc.) the property attribute can be set. Properties are
    defined as subclasses of Property; see the properties module for available
    classes. Properties provide additional methods for understanding units,
    converting between different units or combinations of units (e.g. meters
    to kilometers, degrees Celsius to Fahrenheit, etc.) and listing what units
    are valid for a particular physical property. If a property is set, you can
    usually set a parameter with units, such as:
    
        record['temperature_ambient'] = '72F'

    If the temperature_ambient ParamDef has the 'temperature' property and
    'degC' as the defaultunits, the 72F would be converted to 22.2 degrees C,
    and stored as float(22.2). The defaultunits attribute selects which of the 
    acceptable units defined by the Property will be the default for this
    ParamDef. See the Property class for additioal details. The property and 
    defaultunits cannot be easily changed after creation; if the units change, 
    or the change will require a change in stored Record values or  indexes, 
    it can only be changed by running a migration script.
        
    The indexed attribute will determine if a ParamDef is indexed or not (if
    the DBO type supports indexing.) If it will not be important
    to run frequent queries on the parameter, or if the parameter changes very
    frequently, you might turn off indexing. This cannot be easily changed
    after creation; doing so requires rebuilding the index.
    
    Finally, the immutable attribute is used to lock an parameter value. If 
    set, no ParamDef of this type can be edited. This can be turned on/off after
    creation, within reason.
        
    The following methods are overridden:
        init        Initialize ParamDef attributes
        validate    Check the vartype and property are valid

    :attr desc_short: Short description of ParamDef
    :attr desc_long: Long description of ParamDef and indended uses
    :attr vartype: Data type
    :attr choices: A list of suggested (or restricted) choices
    :attr defaultunits: Default units for physical property
    :attr property: Physical property
    :attr indexed: Values are indexed
    :attr iter: Values can be iterable
    :attr immutable: ParamDef is locked
    :attr controlhint: Hint for user-interface widget

    """
    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(['immutable', 
        'iter', 'desc_long', 'desc_short', 'choices', 'vartype',
        'defaultunits', 'property', 'indexed', 'controlhint'])
    attr_required = set(['vartype'])


    def init(self, d):

        # Variable data type. List of valid types in the module global 'vartypes'
        self.__dict__['vartype'] = None

        # This is a very short description for use in forms
        self.__dict__['desc_short'] = None

        # A complete description of the meaning of this variable
        self.__dict__['desc_long'] = None

        # Physical property represented by this field, List in 'properties'
        self.__dict__['property'] = None

        # Default units (optional)
        self.__dict__['defaultunits'] = None

        # choices for choice and string vartypes, a tuple
        self.__dict__['choices'] = []

        # Immutable
        self.__dict__['immutable'] = False
        
        # Iterable. This can be False, True (list), list, set, dict.
        self.__dict__['iter'] = False

        # turn indexing on/off, if vartype allows for it
        self.__dict__['indexed'] = True
        
        # Widget hint
        self.__dict__['controlhint'] = None


    #################################
    # Setters
    #################################

    # ParamDef does so much validation for other items, 
    # so everything is checked....
    # Several values can only be changed by administrators.

    def _set_choices(self, key, value, vtm=None, t=None):
        value = emen2.util.listops.check_iterable(value)
        value = filter(None, [unicode(i) for i in value]) or None
        return self._set(key, value, self.isowner())


    def _set_desc_short(self, key, value, vtm=None, t=None):
        return self._set(key, unicode(value or self.name), self.isowner())


    def _set_desc_long(self, key, value, vtm=None, t=None):
        return self._set(key, unicode(value or ''), self.isowner())


    # Only admin can change defaultunits/immutable/indexed/vartype.
    # This should still generate lots of warnings.
    def _set_immutable(self, key, value, vtm=None, t=None):
        return self._set(key, bool(value), self._ctx.checkadmin())


    def _set_iter(self, key, value, vtm=None, t=None):
        return self._set(key, bool(value), self._ctx.checkadmin())


    def _set_indexed(self, key, value, vtm=None, t=None):
        return self._set(key, bool(value), self._ctx.checkadmin())


    def _set_controlhint(self, key, value, vtm=None, t=None):
        if value != None:
            value = unicode(value)
        value = value or None
        return self._set(key, value)
                
        
    # These can't be changed, it would disrupt the meaning of existing Records.
    def _set_vartype(self, key, value, vtm=None, t=None):
        if not self.isnew():
            self.error("Cannot change vartype from %s to %s."%(self.vartype, value))

        vtm, t = self._vtmtime(vtm, t)
        value = unicode(value or '') or None

        if value not in vtm.getvartypes():
            self.error("Invalid vartype: %s"%value)

        return self._set(key, value)


    def _set_property(self, key, value, vtm=None, t=None):
        if not self.isnew():
            self.error("Cannot change property from %s to %s."%(self.property, value))

        vtm, t = self._vtmtime(vtm, t)
        value = unicode(value or '')
        if value in ['None', None, '']:
            value = None

        # Allow for unsetting
        if value != None and value not in vtm.getproperties():
            self.error("Invalid property: %s"%value)

        return self._set('property', value)


    def _set_defaultunits(self, key, value, vtm=None, t=None):
        if not self.isnew():
            self.error("Cannot change defaultunits from %s to %s."%(self.defaultunits, value))

        vtm, t = self._vtmtime(vtm, t)
        value = unicode(value or '') or None
        value = emen2.db.properties.equivs.get(value, value)
        return self._set('defaultunits', value)


    def validate(self, vtm=None, t=None):
        if not self.vartype:
            self.error("Vartype required")
            
        vtm, _ = self._vtmtime(vtm, t)
        try:
            vtm.getvartype(self.vartype)
        except KeyError:
            self.error("Vartype %r is not a valid vartype" % self.vartype)

    #     try:
    #         prop = vtm.getproperty(self.property)
    #     except KeyError:
    #         self.error("Cannot set defaultunits without a property!")
    #    m = emen2.db.magnitude.mg(0, value)
    #    # self.error("Invalid units: %s"%value)
    #     if value not in prop.units:
    #         self.error("Invalid defaultunits %s for property %s. 
    #             Allowed: %s"%(value, self.property, ", ".join(prop.units)))






class ParamDefDB(emen2.db.btrees.RelateDB):
    dataclass = ParamDef



__version__ = "$Revision: 1.42 $".split(":")[1][:-1].strip()
