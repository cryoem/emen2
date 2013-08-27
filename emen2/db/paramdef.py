"""Parameter DBOs."""

import functools
import time

# EMEN2 imports
import emen2.utils
import emen2.db.dataobject
import emen2.db.magnitude

class ParamDef(emen2.db.dataobject.BaseDBObject):
    """Parameters.
    
    Each key in a DBO should have a matching Parameter.     
    
    Provides the following attributes:
        desc_short, desc_long, vartype, choices, defaultunits, property, 
        indexed, iter, immutable, property, indexed
    
    Please be aware that several attributes are effectively immutable, and
    cannot be easily changed after a ParamDef is created because it would
    change the meaning of existing recorded data or index formats.
    
    Each ParamDef has a 'vartype' (data type), which references a Vartype class
    for validation and rendering. Vartypes are defined as Vartype subclasses;
    see the vartypes module. Vartypes are usually able to handle loosely
    formatted data and clean it up (validate), or raise a ValidationError
    exception if it cannot be done, or if a value is invalid. The validation
    methods are usually called whenever an attribute/parameter is set on an
    item.
    
    The 'iter' attribute is used in conjunction with the vartype to specify
    whether the ParamDef stores a single value, or a list of values. Most
    vartypes allow iter, but some do not. Check the specific Vartype class.
    Vartypes are usually good at validating a single value into an iterable
    value, but not the reverse. The vartype cannot be easily changed after 
    creation; to do so requires running a migration script, which could require
    changing or discarding data, and likely rebuilding indexes.
    
    When ParamDefs are displayed in certain contexts, such as being rendered
    in a view or as a table header, the 'desc_short' and 'desc_long' attributes
    are used to provide short and long descriptions, respectively, of the
    ParamDef and its intended uses and requirements. The 'desc_short' attribute
    is required, 'desc_long' is optional. Because they do not change the actual
    values of recorded data, they can be edited (within reason) after creation.
    
    The 'choices' attribute can be used to provide a default list of choices
    when entering values. These are provided as suggestions for consistency
    among users, and are usually combined with query results to give additional
    common choices. However, for vartype 'choice', the list of choices is
    enforced as the only allowed values. Choices can be edited after creation.
    
    If a ParamDef represents a particular measurable physical property (length,
    volume, mass, pH, etc.) the 'property' attribute can be set to reference a
    Property class. Properties are defined as subclasses of Property; see the
    properties module for available classes. Properties provide additional
    methods for understanding units, converting between different units or
    combinations of units (e.g. meters to kilometers, degrees Celsius to
    Fahrenheit, etc.) and listing what units are valid for a particular
    physical property. If a property is set, you can usually set a parameter
    with units, such as:
    
        record['temperature_ambient'] = '72F'

    If the temperature_ambient ParamDef has the 'temperature' property and
    'degC' as the defaultunits, the 72F would be converted to 22.2 degrees C,
    and stored as float(22.2). The 'defaultunits' attribute selects which of the 
    acceptable units defined by the Property will be the default for this
    ParamDef. See the Property class for additioal details. The property and 
    defaultunits cannot be easily changed after creation; if the units change, 
    or the change will require a change in stored Record values or indexes, 
    it can only be changed by running a migration script.
        
    The 'indexed' attribute will determine if a ParamDef is indexed or not (if
    the DBO type supports indexing.) If it will not be important
    to run frequent queries on the parameter, or if the parameter changes very
    frequently, you might turn off indexing. This cannot be easily changed
    after creation; doing so requires rebuilding the index.
    
    Finally, the 'immutable' attribute is used to lock an parameter value. If 
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
    """
    
    public = emen2.db.dataobject.BaseDBObject.public | set(['immutable', 
        'iter', 'desc_long', 'desc_short', 'choices', 'vartype',
        'defaultunits', 'property', 'indexed'])

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

    def validate(self):
        if not self.vartype:
            raise self.error("Vartype required")
        if self.vartype not in emen2.db.vartypes.Vartype.registered:
            raise self.error("Vartype %s is not a valid vartype"%self.vartype)
    #     try:
    #         prop = emen2.db.properties.Property.get_property(self.property)
    #     except KeyError:
    #         raise self.error("Cannot set defaultunits without a property!")
    #    m = emen2.db.magnitude.mg(0, value)
    #    # raise self.error("Invalid units: %s"%value)
    #     if value not in prop.units:
    #         raise self.error("Invalid defaultunits %s for property %s. 
    #             Allowed: %s"%(value, self.property, ", ".join(prop.units)))

    ##### Setters #####
    # ParamDef does so much validation for other items, 
    # so everything is tightly checked....
    # Several values can only be changed by administrators.

    def _set_choices(self, key, value):
        value = map(self._strip, emen2.utils.check_iterable(value))
        value = filter(None, value) or None
        return self._set(key, value, self.isowner())

    def _set_desc_short(self, key, value):
        return self._set(key, self._strip(value or self.name), self.isowner())

    def _set_desc_long(self, key, value):
        return self._set(key, self._strip(value), self.isowner())

    # Only admin can change defaultunits/immutable/indexed/vartype.
    # This should still generate lots of warnings.
    def _set_immutable(self, key, value):
        value = bool(value)
        if value != self.immutable and not self.isnew():
            raise self.error("Cannot change immutable from %s to %s."%(self.immutable, value))
        return self._set(key, value, self.isowner())

    def _set_iter(self, key, value):
        value = bool(value)
        if value != self.iter and not self.isnew():
            raise self.error("Cannot change iter from %s to %s."%(self.iter, value))
        return self._set(key, value, self.isowner())

    def _set_indexed(self, key, value):
        value = bool(value)
        if value != self.indexed and not self.isnew():
            raise self.error("Cannot change indexed from %s to %s."%(self.indexed, value))
        return self._set(key, value, self.isowner())
            
    # These can't be changed, it would disrupt the meaning of existing Records.
    def _set_vartype(self, key, value):
        value = self._strip(value)
        if value != self.vartype and not self.isnew():
            raise self.error("Cannot change vartype from %s to %s."%(self.vartype, value))
        if value not in emen2.db.vartypes.Vartype.registered:
            raise self.error("Invalid vartype: %s"%value)
        return self._set(key, value, self.isowner())

    def _set_property(self, key, value):
        value = self._strip(value)
        if value != self.property and not self.isnew():
            raise self.error("Cannot change property from %s to %s."%(self.property, value))
        # Allow for unsetting
        if value != None and value not in emen2.db.properties.Property.registered:
            raise self.error("Invalid property: %s"%value)
        return self._set('property', value, self.isowner())

    def _set_defaultunits(self, key, value):
        value = self._strip(value)
        value = unicode(emen2.db.properties.equivs.get(value, value))
        if value != self.defaultunits and not self.isnew():
            raise self.error("Cannot change defaultunits from %s to %s."%(self.defaultunits, value))
        return self._set('defaultunits', value, self.isowner())
