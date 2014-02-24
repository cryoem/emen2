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
    
    Provides the following parameters:
        desc_short, desc_long, vartype, choices, defaultunits, property, 
        indexed, iter, property, indexed
    
    Please be aware that several parameters are effectively immutable, and
    cannot be easily changed after a ParamDef is created because it would
    change the meaning of existing recorded data or index formats.
    
    Each ParamDef has a 'vartype' (data type), which references a Vartype class
    for validation and rendering. Vartypes are defined as Vartype subclasses;
    see the vartypes module. Vartypes are usually able to handle loosely
    formatted data and clean it up (validate), or raise a ValidationError
    exception if it cannot be done, or if a value is invalid. The validation
    methods are usually called whenever an parameter is set on an
    item.
    
    The 'iter' parameter is used in conjunction with the vartype to specify
    whether the ParamDef stores a single value, or a list of values. Most
    vartypes allow iter, but some do not. Check the specific Vartype class.
    Vartypes are usually good at validating a single value into an iterable
    value, but not the reverse. The vartype cannot be easily changed after 
    creation; to do so requires running a migration script, which could require
    changing or discarding data, and likely rebuilding indexes.
    
    When ParamDefs are displayed in certain contexts, such as being rendered
    in a view or as a table header, the 'desc_short' and 'desc_long' parameters
    are used to provide short and long descriptions, respectively, of the
    ParamDef and its intended uses and requirements. The 'desc_short' parameter
    is required, 'desc_long' is optional. Because they do not change the actual
    values of recorded data, they can be edited (within reason) after creation.
    
    The 'choices' parameter can be used to provide a default list of choices
    when entering values. These are provided as suggestions for consistency
    among users, and are usually combined with query results to give additional
    common choices. However, for vartype 'choice', the list of choices is
    enforced as the only allowed values. Choices can be edited after creation.
    
    If a ParamDef represents a particular measurable physical property (length,
    volume, mass, pH, etc.) the 'property' parameter can be set to reference a
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
    and stored as float(22.2). The 'defaultunits' parameter selects which of the 
    acceptable units defined by the Property will be the default for this
    ParamDef. See the Property class for additioal details. The property and 
    defaultunits cannot be easily changed after creation; if the units change, 
    or the change will require a change in stored Record values or indexes, 
    it can only be changed by running a migration script.
        
    The 'indexed' parameter will determine if a ParamDef is indexed or not (if
    the DBO type supports indexing.) If it will not be important
    to run frequent queries on the parameter, or if the parameter changes very
    frequently, you might turn off indexing. This cannot be easily changed
    after creation; doing so requires rebuilding the index.
    
    The following methods are overridden:
        init        Initialize ParamDef
        validate    Check the vartype and property are valid

    :property desc_short: Short description of ParamDef
    :property desc_long: Long description of ParamDef and indended uses
    :property vartype: Data type
    :property choices: A list of suggested (or restricted) choices
    :property defaultunits: Default units for physical property
    :property property: Physical property
    :property indexed: Values are indexed
    :property iter: Values can be iterable
    """
    
    def init(self):
        super(ParamDef, self).init()
        # Data type. 
        self.data['vartype'] = None
        # This is a very short description for use in forms
        self.data['desc_short'] = None
        # A complete description of the meaning of this variable
        self.data['desc_long'] = None
        # Physical property represented by this field, List in 'properties'
        self.data['property'] = None
        # Default units (optional)
        self.data['defaultunits'] = None
        # choices for choice and string vartypes, a tuple
        self.data['choices'] = []
        # Iterable. Boolean.
        self.data['iter'] = False
        # turn indexing on/off, if vartype allows for it
        self.data['indexed'] = True

    def validate(self):
        if not self.vartype:
            raise self.error("Vartype required.")
        if self.vartype not in emen2.db.vartypes.Vartype.registered:
            raise self.error("Vartype %s is not a valid vartype."%self.vartype)
        # try:
        #     prop = emen2.db.properties.Property.get_property(self.property)
        # except KeyError:
        #     raise self.error("Cannot set defaultunits without a property!")
        # m = emen2.db.magnitude.mg(0, value)
        # # raise self.error("Invalid units: %s"%value)
        # if value not in prop.units:
        #     raise self.error("Invalid defaultunits %s for property %s. 
        #         Allowed: %s"%(value, self.property, ", ".join(prop.units)))

    def get_vartype(self, *args, **kwargs):
        # print "get_vartype:", args, kwargs, self.data, self.data['vartype']
        vtc = emen2.db.vartypes.Vartype.get_vartype(
            name=self.data['name'],
            vartype=self.data['vartype'],
            iter=self.data['iter'],
            choices=self.data['choices'],
            defaultunits=self.data['defaultunits'],
            db=self.ctx.db,
            cache=self.ctx.cache,
            options=kwargs.get('options')
        )
        return vtc

    ##### Setters #####

    def _set_choices(self, key, value):
        value = map(self._strip, emen2.utils.check_iterable(value))
        value = filter(None, value) or None
        self._set(key, value, self.isowner())

    def _set_desc_short(self, key, value):
        self._set(key, self._strip(value or self.name), self.isowner())

    def _set_desc_long(self, key, value):
        self._set(key, self._strip(value), self.isowner())

    def _set_iter(self, key, value):
        value = bool(value)
        if value != self.iter and not self.isnew():
            raise self.error("Cannot change iter from %s to %s."%(self.iter, value))
        self._set(key, value, self.isowner())

    def _set_indexed(self, key, value):
        value = bool(value)
        if value != self.indexed and not self.isnew():
            raise self.error("Cannot change indexed from %s to %s."%(self.indexed, value))
        self._set(key, value, self.isowner())
            
    def _set_vartype(self, key, value):
        # These can't be changed, 
        #   it would disrupt the meaning of existing Records.
        value = self._strip(value)
        if value != self.vartype and not self.isnew():
            raise self.error("Cannot change vartype from %s to %s."%(self.vartype, value))
        if value not in emen2.db.vartypes.Vartype.registered:
            raise self.error("Invalid vartype: %s"%value)
        self._set(key, value, self.isowner())

    def _set_property(self, key, value):
        value = self._strip(value)
        if value != self.property and not self.isnew():
            raise self.error("Cannot change property from %s to %s."%(self.property, value))
        # Allow for unsetting
        if value != None and value not in emen2.db.properties.Property.registered:
            raise self.error("Invalid property: %s"%value)
        self._set('property', value, self.isowner())

    def _set_defaultunits(self, key, value):
        value = self._strip(value)
        value = unicode(emen2.db.properties.equivs.get(value, value))
        if value != self.defaultunits and not self.isnew():
            raise self.error("Cannot change defaultunits from %s to %s."%(self.defaultunits, value))
        self._set('defaultunits', value, self.isowner())
