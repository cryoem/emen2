# This Python file is encoding:UTF-8 Encoded
"""Properties -- types of physical properties (units)."""

import sys
import math
import re

# EMEN2 imports
import emen2.utils
import emen2.db.exceptions
import emen2.db.magnitude as mg

# Convenience
ci = emen2.utils.check_iterable
ValidationError = emen2.db.exceptions.ValidationError

# Unit synonyms
equivs = {}

# SI Synonyms
# http://physics.nist.gov/cuu/Units/units.html
si_equivs = {
    # meter / m
    'meter': 'm',
    'meters': 'm',
    'metre': 'm',
    'metres': 'm',

    # liter / l
    'Liter': 'l',
    'Liters': 'l',
    'Litre': 'l',
    'Litres': 'l',

    # kilogram / kg
    'gram': 'g',
    'grams': 'g',

    # ampere
    'Amp': 'ampere',
    'Amps': 'ampere',
    'Ampere': 'ampere',
    'Amperes': 'ampere',
    'amp': 'ampere',
    'amps': 'ampere',
    'amperes': 'ampere',
    
    # second / s
    'second': 's',
    'seconds': 's',
    
    # Derived Units
    # Force: Newton / N
    'Newton': 'N',
    'Newtons': 'N',
    'newton': 'N',
    'newtons': 'N',
    
    # Absorbed dose: Gray / Gy
    'Gray': 'Gy',
    'Grays': 'Gy',
    'gray': 'Gy',
    'grays': 'Gy',
    
    # Power: Watt / W
    'Watt': 'W',
    'Watts': 'W',
    'watt': 'W',
    'watts': 'W',
    
    # Energy: Joule / J
    'Joule': 'J',
    'Joules': 'J',
    'joule': 'J',
    'joules': 'J',
    
    # Electric potential difference: Volt / V
    'Volt': 'V',
    'Volts': 'V',
    'volt': 'V',
    'volts': 'V',
    
    # Plane angle: radian / rad
    'rads': 'rad',
    'radians': 'rad',
    
    # Frequency: Hertz / Hz
    'Hertz': 'Hz',
    'hertz': 'Hz',
    
    # Electric resistence: Ohm / Ω
    'Ohm': 'ohm',
    'Ohms': 'ohm',
    'ohms': 'ohm',
    
    # Magnetic flux density: Tesla / T
    'Tesla': 'T',
    'Teslas': 'T',
    'tesla': 'T',
    'teslas': 'T',
    
    # Dose equivalent: Sievert / Sv
    'Sievert': 'Sv',
    'Sieverts': 'Sv',
    'sievert': 'Sv',
    'sieverts': 'Sv',
    
    # Radionuclide activity: Becquerel / Bq
    'Becquerel': 'Bq',
    'Becquerels': 'Bq',
    'becquerel': 'Bq',
    'becquerels': 'Bq',

    # Eletric charge: Coulomb / C
    'Coulomb': 'C',
    'Coulombs': 'C',
    'coulomb': 'C',
    'coulombs': 'C',
    
    # Capacitance: Farad / F
    'Farad': 'F',
    'Farads': 'F',
    'farad': 'F',
    'farads': 'F',
    
    # Solid angle: steradian / sr
    
    # Pressure: Pascal / Pa
    'Pascal': 'Pa',
    'pascal': 'Pa',

    # Electric conductance
    'Siemens': 'S',
    'siemens': 'S',
    
    # Magnetic flux: Weber / Wb
    'Weber': 'Wb',
    'weber': 'Wb',
    
    # Inductance: Henry / H
    'Henry': 'H',
    'henry': 'H',
    
    # Luminous flux: lumen / lm
    'Lumen': 'lm',
    'lumen': 'lm',
    
    # Catalytic activity: katal / kat
    'katal': 'kat',

    # Illuminance: lux / lx
    # Not defined in magnitude.py
    # 'lux':, 'lx',
}

# SI Prefixes
# These are placed before each synonym above, e.g.
# nanometers -> nm
si_prefix = {
    'yocto': 'y',
    'zepto': 'z',
    'atto': 'a',
    'femto': 'f',
    'pico': 'p',
    'nano': 'n',
    'micro': 'u', # u'µ',
    'milli': 'm',
    'centi': 'c',
    'deci': 'd',
    'kilo': 'k',
    'mega': 'M',
    'giga': 'G',
    'tera': 'T',
    'peta': 'P',
    'exa': 'E',
    'zetta': 'Z',
    'yotta': 'Y',
}

# These are handled a little differently.
# bit/byte synonyms
bytes_equivs = {
    'bit': 'b',
    'bits': 'b',
    'byte': 'B',
    'bytes': 'B',
}

# SI bit/byte prefixes
bytes_prefix = {
    'Kibi': 'Ki',
    'Mebi': 'Mi',
    'Gibi': 'Gi',
    'Tebi': 'Ti',
    'Pebi': 'Pi',
    'Exbi': 'Ei'
}

# Other unit synonyms
other_equivs = {
    # 'KB': 'KiB',

    # Pressure
    'Torr': 'torr',

    # (Liquid volume)
    'gallons': 'gallon',
    # lowercase l for liter
    'nL': 'nl',
    'uL': 'ul',
    # 'ul': u'µl',
    # u'µL': u'µl',
    # u'uL': u'µl',
    'mL': 'ml',
    'L': 'l',
    'kL': 'kl',
    'ML': 'Ml',    

    # Temperature
    'degrees K': 'K',
    'degrees Kelvin': 'K',
    'Kelvin': 'K',
    'degrees C': 'degC',
    'Celcius': 'degC',
    'centigrade': 'degC',
    'degrees Celcius': 'degC',
    
    # Amount of substance
    'moles': 'mol',
    
    # Currency
    'dollar': '$',
    'dollars': '$',

    # Length
    u'Ångstrom': u'Å',
    u'Ångstroms': u'Å',
    'Angstrom': u'Å',
    'Angstroms': u'Å',
    'feet': 'ft',
    'foot': 'ft',
    'inches': 'inch',
    'lightspeed': 'c',

    # Spatial frequency
    'dots per inch': 'dpi',
    'lines per inch': 'lpi',
    
    # Time
    'minute': 'min',
    'minutes': 'min',
    'mins': 'min',
    'days': 'day',
    'years': 'year',
    
    # Derived units
    'mm^2': 'mm mm',
    'cm^2': 'cm cm',
    'm^2': 'm m',
    'km^2': 'km km',
    'square feet': 'ft ft',
    'square meters': 'm m',
    'square kilometers': 'km km',
    'square miles': 'mile mile',
    'kg/m^3': 'kg/m m m',
    'mol/m^3': 'mol/m m m',    
    'm^3': 'm m m',    
}

equivs.update(other_equivs)

# Massage my equivalents into the units system.
for name,abbr in si_equivs.items():
    equivs[name] = abbr
    for prefix, p in si_prefix.items():
        equivs[prefix + name] = p + abbr

for name,abbr in bytes_equivs.items():
    equivs[name] = abbr
    for prefix, p in si_prefix.items():
        equivs[prefix + name] = p + abbr
    for prefix, p in bytes_prefix.items():
        equivs[prefix + name] = p + abbr
    
for name, abbr in equivs.items():
    equivs[name.lower()] = abbr

# print "EQUIVS:"
# for k,v in equivs.items(): print k,v

# Structural biology units: Angstrom and Dalton
mg.new_mag(u'Å', mg.Magnitude(1e-10, m=1))
mg.new_mag('Da', mg.Magnitude(1.6605402e-27, kg=1))

# Unitless
mg.new_mag('pixel', mg.Magnitude(1.0))
mg.new_mag('count', mg.Magnitude(1.0))
mg.new_mag('unitless', mg.Magnitude(1))
mg.new_mag('%RH', mg.Magnitude(1))
mg.new_mag('%RH', mg.Magnitude(1))
mg.new_mag('%T', mg.Magnitude(1))
mg.new_mag('%', mg.Magnitude(1))
mg.new_mag('pfu', mg.Magnitude(1))

# Other units
mg.new_mag('degF', mg.Magnitude(1.0))
mg.new_mag('mile', mg.mg(160934.4, 'cm'))
mg.new_mag('gallon', mg.Magnitude(3.78541178e-3, m=3))
mg.new_mag('torr', mg.mg(133.3224, 'Pa'))
mg.new_mag('psi', mg.mg(6.8948e3, 'Pa'))
mg.new_mag('bar', mg.mg(1e5, 'Pa'))
mg.new_mag('atm', mg.mg(1.01325e5, 'Pa'))
mg.new_mag('degree', mg.Magnitude(1))
mg.new_mag('hour', mg.Magnitude(3600.0, s=1))
mg.new_mag('hectare', mg.Magnitude(1e4, m=2))
mg.new_mag('acre', mg.Magnitude(4046.8564224, m=2))

class Property(object):    
    restricted = False
    defaultunits = None
    units = []
    
    ##### Extensions #####

    registered = {}
    @classmethod
    def register(cls, name):
        def f(o):
            if name in cls.registered:
                raise ValueError("""%s is already registered"""%name)
            cls.registered[name] = o
            return o
        return f

    @classmethod
    def get_property(cls, name, *args, **kwargs):
        return cls.registered[name](*args, **kwargs)

    ##### Validation #####

    def validate(self, pd, value, db):
        if hasattr(value, "__iter__"):
            return [self.validate(pd, i, db) for i in value]

        if hasattr(value, "__float__"):
            return float(value)

        # print "Parsing for units: '%s'"%value            
        value = unicode(value).strip()
        if not value:
            return None

        # Match floating point numbers
        q = re.compile("^([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(.*)")

        try:
            r = q.match(value).groups()
        except Exception, e:
            raise ValueError("Unable to parse '%s' for units."%(value))

        value = float(r[0])
        
        target = pd.defaultunits
        if not target:
            target = self.defaultunits

        units = None
        if r[2] != None:
            units = unicode(r[2]).strip()
        if not units:
            units = target

        return self.convert(value, units, target)

    def check_bounds(self, value, target):
        return value

    def check_restrict(self, units, allowed):
        equivs = equivs.get(units, units)
        allowed = [equivs.get(i,i) for i in allowed]
        if units not in allowed:
            raise ValueError("Units %s not allowed for this property. Allowed units: %s."%(units, ", ".join(allowed)))
            
    def convert(self, value, units, target):
        units = equivs.get(units, units)
        target = equivs.get(target, target)    
        if not units or units == target:
            self.check_bounds(value, target)
            return value

        # self.check_restrict(units, self.units)
        value = self._convert(value, units, target)
        self.check_bounds(value, target)
        return value

    def _convert(self, value, units, target):
        # print "value/units/target", value, units, target
        try:
            v = mg.mg(value, units, ounit=target)
        except emen2.db.magnitude.MagnitudeError:
            raise
            
        # Check for dimensionless conversions...
        if v.dimensionless():
            raise self.error(units, target, msg='dimensionless property')        
        return v.toval()

    def error(self, units, target, msg=None):
        return ValueError("Couldn't convert %s to %s: %s"%(units, target, msg or ''))

    def unknown(self, units, target):
        raise ValueError("Don't know how to convert %s to %s."%(units, target))

@Property.register('transmittance')
class prop_transmittance(Property):
    defaultunits = '%T'
    units = ['%T']

@Property.register('force')
class prop_force(Property):
    defaultunits = 'N'
    units = ['N', 'kN']

@Property.register('energy')
class prop_energy(Property):
    defaultunits = 'J'
    units = ['J', 'kJ']

@Property.register('resistance')
class prop_resistance(Property):
    defaultunits = 'ohm'
    units = ['microohm', 'milliohm', 'ohm']

@Property.register('dose')
class prop_dose(Property):
    defaultunits = "e/A2/sec"
    units = ["e/A2/sec"]

@Property.register('exposure')
class prop_exposure(Property):
    defaultunits = 'e/A^2'
    units = ['e/A^2']

@Property.register('currency')
class prop_currency(Property):
    defaultunits = 'dollar'
    units = ['dollar']

@Property.register('voltage')
class prop_voltage(Property):
    defaultunits = 'V'
    units = ['uV', 'mV', 'V', 'kV', 'MV']

@Property.register('pH')
class prop_pH(Property):
    defaultunits = 'pH'
    units = ['pH']
    def check_bounds(self, value, target):
        if (target == 'pH' and (value < 0 or value > 14)):
            raise ValueError("pH must be between 0 and 14.")

@Property.register('concentration')
class prop_concentration(Property):
    defaultunits = 'mg/ml'
    units = ['mg/ml', 'pfu', 'kg/kg', 'kg/m^3', 'mol/m^3', 'mol/mol']

@Property.register('angle')
class prop_angle(Property):
    defaultunits = 'rad'
    units = ['mrad', 'rad', 'degree']

    def _convert(self, value, units, target):
        # if we get one of the rad variants, convert to rads
        if units != 'degree' and target == 'degree':
            value = mg.mg(value, units, ounit='rad')
            value = float(value) * (180.0 / math.pi)
            
        elif units == 'degree' and target != 'degree':
            value = value * (math.pi / 180.0)
            value = mg.mg(value, 'rad', target)
    
        elif units != 'degree' and target != 'degree':
            value = mg.mg(value, units, ounit=target)

        else:
            self.unknown(units, target)

        return value

@Property.register('temperature')
class prop_temperature(Property):
    defaultunits = 'K'
    units = ['degC', 'K', 'degF']
    
    def check_bounds(self, value, target):
        # Check absolute zero
        if (target == 'degC' and value < -273.15) or (target == 'K' and value < 0) or (target == 'degF' and value < -459.67):
            raise ValueError("Cannot set a temperature below absolute zero.")

    def _convert(self, value, units, target):
        # C / K
        if units == 'degC' and target == 'K':
            value = value + 273.15
        elif units == 'K' and target == 'degC':
            value = value - 273.15
        # F / K
        elif units == 'degF' and target == 'K':
            value = (value + 459.67) * (5.0 / 9.0)
        elif units == 'K' and target == 'degF':
            value = (value * (9.0 / 5.0)) - 459.67
        # C / F
        elif units == 'degC' and target == 'degF':
            value = value * (9.0 / 5.0) + 32
        elif units == 'degF' and target == 'degC':
            value = (value - 32) * (5.0 / 9.0)
        else:
            raise ValueError("Don't know how to convert %s to %s."%(units, target))
        return value
    
@Property.register('area')
class prop_area(Property):
    defaultunits = 'm^2'
    units = ['mm^2', 'cm^2', 'm^2', 'km^2', 'square feet', 'hectare', 'acre']

@Property.register('current')        
class prop_current(Property):
    defaultunits = 'A'
    units = ['uA', 'mA', 'A', 'kA', 'MA']

@Property.register('bytes')
class prop_bytes(Property):
    defaultunits = 'B'
    units = ['B', 'kB', 'MB', 'GB', 'TB', 'KiB', 'MiB', 'GiB', 'TiB']

@Property.register('percentage')
class prop_percentage(Property):
    defaultunits = '%'
    units = ['%']
    
@Property.register('property')
class prop_momentum(Property):
    defaultunits = 'kg m/s'
    units = ['kg m/s']

@Property.register('volume')
class prop_volume(Property):
    defaultunits = 'L'
    units = ['nL', 'uL', 'mL', 'L', 'gallon', 'm^3']

@Property.register('pressure')
class prop_pressure(Property):
    defaultunits = 'Pa'
    units = ['Pa', 'bar', 'atm', 'torr', 'psi']
    
@Property.register('unitless')
class prop_unitless(Property):
    defaultunits = 'unitless'
    units = ['unitless']
    
@Property.register('inductance')
class prop_inductance(Property):
    defaultunits = 'H'
    units = ['H']
        
@Property.register('currentdensity')
class prop_currentdensity(Property):
    defaultunits = 'Pi Amp/cm^2'
    units = ['Pi Amp/cm^2']
    
@Property.register('count')
class prop_count(Property):
    defaultunits = 'count'
    units = ['count', 'pixel']

@Property.register('bfactor')
class prop_bfactor(Property):
    defaultunits = 'A^2'
    units = ['A^2']

@Property.register('relative_humidity')
class prop_relative_humidity(Property):
    defaultunits = '%RH'
    units = ['%RH']

@Property.register('length')
class prop_length(Property):
    defaultunits = 'm'
    units = [u'Å', 'nm', 'um', 'mm', 'm', 'km']

@Property.register('mass')
class prop_mass(Property):
    defaultunits = 'g'
    units = ['Da', 'kDa', 'MDa', 'ng', 'ug', 'mg', 'g', 'kg']

@Property.register('time')
class prop_time(Property):
    defaultunits = 's'
    units = ['fs', 'ps', 'ns', 'us', 'ms', 's', 'min', 'hour', 'day', 'year']

@Property.register('velocity')
class prop_velocity(Property):
    defaultunits = 'm/s'
    units = ['m/s']

@Property.register('acceleration')
class prop_acceleration(Property):
    defaultunits = 'm/s**2'
    units = ['m/s**2']

@Property.register('resolution')
class prop_resolution(Property):
    defaultunits = u'Å/pixel'
    units = [u'Å/pixel', 'dpi', 'lpi']
