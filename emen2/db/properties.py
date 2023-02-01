# $Id: properties.py,v 1.27 2012/07/28 06:31:18 irees Exp $
# This Python file is encoding:UTF-8 Encoded
"""Properties -- types of physical properties (units)

Classes:
    Property
    prop_*: A number of included Properties

"""

import sys
import math
import re

# EMEN2 imports
import emen2.db.datatypes
import emen2.db.magnitude as mg

# Convenience
ci = emen2.util.listops.check_iterable
ValidationError = emen2.db.exceptions.ValidationError
vtm = emen2.db.datatypes.VartypeManager

# Unit synonyms
equivs = {
    'mm^2': 'mm mm',
    'cm^2': 'cm cm',
    'm^2': 'm m',
    'km^2': 'km km',
    'square feet': 'ft ft',
    'square meters': 'm m',
    'square kilometers': 'km km',
    'square miles': 'mile mile',

    'gallons': 'gallon',

    'kg/m^3': 'kg/m m m',
    'mol/m^3': 'mol/m m m',    
    'm^3': 'm m m',

    'Torr': 'torr',

    u'Ångstrom': u'Å',
    u'Ångstroms': u'Å',
    'Angstrom': u'Å',
    'Angstroms': u'Å',

    'nL': 'nl',
    'uL': 'ul',
    'mL': 'ml',
    'L': 'l',
    'kL': 'kl',
    'ML': 'Ml',    

    'degrees K': 'K',
    'degrees Kelvin': 'K',
    'Kelvin': 'K',
    
    'degrees C': 'degC',
    'Celcius': 'degC',
    'centigrade': 'degC',
    'degrees Celcius': 'degC',
    
    'degrees': 'degree',
    
    'moles': 'mol',
    
    'dollar': '$',
    'dollars': '$',

    'feet': 'ft',
    'foot': 'ft',
    
    'inches': 'inch',
    
    'lightspeed': 'c',

    'dots per inch': 'dpi',
    'lines per inch': 'lpi',
    
    'Henry': 'H',
    'Henrys': 'H',
    
    'katal': 'kat',
    'katals': 'kat',
    
    'lumen': 'lm',
    'lumens': 'lm',
        
    'minute': 'min',
    'minutes': 'min',
    
    'mins': 'min',
    'days': 'day',
    'years': 'year'
}


# SI prefix synonyms
si_equivs = {
    'meter': 'm',
    'meters': 'm',
    'metre': 'm',
    'metres': 'm',

    'Liter': 'l',
    'Liters': 'l',
    'Litre': 'l',
    'Litres': 'l',

    'gram': 'g',
    'grams': 'g',

    'amp': 'ampere',
    'amps': 'ampere',
    'amperes': 'ampere',
    
    'second': 's',
    'seconds': 's',

    'Newton': 'N',
    'Newtons': 'N',
    
    'Gray': 'Gy',
    'Grays': 'Gy',
    
    'Watt': 'W',
    'Watts': 'W',
    
    'Joule': 'J',
    'Joules': 'J',
    
    'Volt': 'V',
    'Volts': 'V',
    
    'rads': 'rad',
    'radians': 'rad',
        
    'Hertz': 'Hz',
    
    'Ohm': 'ohm',
    'Ohms': 'ohm',
    
    'Tesla': 'T',
    'Teslas': 'T',
    
    'Sievert': 'Sv',
    'Sieverts': 'Sv',
    
    'Becquerel': 'Bq',
    'Becquerels': 'Bq',

    'Coulomb': 'C',
    'Coulombs': 'C',
    
    'farad': 'F',
    'farads': 'F'    
}

# SI Prefixes
si_prefix = {
    'yocto': 'y',
    'zepto': 'z',
    'atto': 'a',
    'femto': 'f',
    'pico': 'p',
    'nano': 'n',
    'micro': 'u',
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


# Non-SI Units
mg.new_mag('degF', mg.Magnitude(1.0))
mg.new_mag('mile', mg.mg(160934.4, 'cm'))
mg.new_mag('gallon', mg.Magnitude(3.78541178e-3, m=3))
mg.new_mag('torr', mg.Magnitude(1/760.0, m=-1, kg=1, s=-2))
mg.new_mag('degree', mg.Magnitude(1))







class Property(object):
    
    restricted = False
    defaultunits = None
    units = []

    def validate(self, engine, pd, value, db):
        if hasattr(value, "__iter__"):
            return [self.validate(engine, pd, i, db) for i in value]

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
            raise ValueError, "Unable to parse '%s' for units"%(value)

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
        return
        # allowed = [equivs.get(i,i) for i in allowed]
        # if units not in allowed:
        #     raise ValueError, "Units %s not allowed for this property. Allowed units: %s"%(units, ", ".join(allowed))
            

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
            self.error(units, target, msg='dimensionless property')        
        return v.toval()


    def error(self, units, target, msg=None):
        raise ValueError, "Couldn't convert %s to %s: %s"%(units, target, msg or '')
        

    def unknown(self, units, target):
        raise ValueError, "Don't know how to convert %s to %s"%(units, target)



@vtm.register_property('transmittance')
class prop_transmittance(Property):
    defaultunits = '%T'
    units = ['%T']



@vtm.register_property('force')
class prop_force(Property):
    defaultunits = 'N'
    units = ['N']

    
        
@vtm.register_property('energy')
class prop_energy(Property):
    defaultunits = 'J'
    units = ['J']



@vtm.register_property('resistance')
class prop_resistance(Property):
    defaultunits = 'ohm'
    units = ['microohm', 'milliohm', 'ohm']



@vtm.register_property('dose')
class prop_dose(Property):
    defaultunits = "e/A2/sec"
    units = ["e/A2/sec"]



@vtm.register_property('exposure')
class prop_exposure(Property):
    defaultunits = 'e/A^2'
    units = ['e/A^2']



@vtm.register_property('currency')
class prop_currency(Property):
    defaultunits = 'dollar'
    units = ['dollar']



@vtm.register_property('voltage')
class prop_voltage(Property):
    defaultunits = 'V'
    units = ['uV', 'mV', 'V', 'kV', 'MV']



@vtm.register_property('pH')
class prop_pH(Property):
    defaultunits = 'pH'
    units = ['pH']

    def check_bounds(self, value, target):
        if (target == 'pH' and not 0 <- value <- 14):
            raise ValueError, "pH must be between 0 and 14"



@vtm.register_property('concentration')
class prop_concentration(Property):
    defaultunits = 'mg/ml'
    units = ['mg/ml', 'pfu', 'kg/kg', 'kg/m^3', 'mol/m^3', 'mol/mol']

        

@vtm.register_property('angle')
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



@vtm.register_property('temperature')
class prop_temperature(Property):
    defaultunits = 'K'
    units = ['degC', 'K', 'degF']
    
    def check_bounds(self, value, target):
        # Check absolute zero
        if (target == 'degC' and value < -273.15) or (target == 'K' and value < 0) or (target == 'degF' and value < -459.67):
            raise ValueError, "Cannot set a temperature below absolute zero"

    
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
            raise ValueError, "Don't know how to convert %s to %s"%(units, target)

        return value
    
        

@vtm.register_property('area')
class prop_area(Property):
    defaultunits = 'm^2'
    units = ['mm^2', 'cm^2', 'm^2', 'km^2', 'square feet']



@vtm.register_property('current')        
class prop_current(Property):
    defaultunits = 'A'
    units = ['uA', 'mA', 'A', 'kA', 'MA']



@vtm.register_property('bytes')
class prop_bytes(Property):
    defaultunits = 'B'
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'KiB', 'MiB', 'GiB', 'TiB']



@vtm.register_property('percentage')
class prop_percentage(Property):
    defaultunits = '%'
    units = ['%']
    

        
@vtm.register_property('property')
class prop_momentum(Property):
    defaultunits = 'kg m/s'
    units = ['kg m/s']



@vtm.register_property('volume')
class prop_volume(Property):
    defaultunits = 'L'
    units = ['nL', 'uL', 'mL', 'L', 'gallon', 'm^3']



@vtm.register_property('pressure')
class prop_pressure(Property):
    defaultunits = 'Pa'
    units = ['Pa', 'bar', 'atm', 'torr', 'psi']


        
@vtm.register_property('unitless')
class prop_unitless(Property):
    defaultunits = 'unitless'
    units = ['unitless']

        

@vtm.register_property('inductance')
class prop_inductance(Property):
    defaultunits = 'H'
    units = ['H']
        


@vtm.register_property('currentdensity')
class prop_currentdensity(Property):
    defaultunits = 'Pi Amp/cm^2'
    units = ['Pi Amp/cm^2']


        
@vtm.register_property('count')
class prop_count(Property):
    defaultunits = 'count'
    units = ['count', 'pixel']



@vtm.register_property('bfactor')
class prop_bfactor(Property):
    defaultunits = 'A^2'
    units = ['A^2']



@vtm.register_property('relative_humidity')
class prop_relative_humidity(Property):
    defaultunits = '%RH'
    units = ['%RH']

        

@vtm.register_property('length')
class prop_length(Property):
    defaultunits = 'm'
    units = [u'Å', 'nm', 'um', 'mm', 'm', 'km']



@vtm.register_property('mass')
class prop_mass(Property):
    defaultunits = 'g'
    units = ['Da', 'kDa', 'MDa', 'ng', 'ug', 'mg', 'g', 'kg']



@vtm.register_property('time')
class prop_time(Property):
    defaultunits = 's'
    units = ['fs', 'ps', 'ns', 'us', 'ms', 's', 'min', 'hour', 'day', 'year']



@vtm.register_property('velocity')
class prop_velocity(Property):
    defaultunits = 'm/s'
    units = ['m/s']



@vtm.register_property('acceleration')
class prop_acceleration(Property):
    defaultunits = 'm/s**2'
    units = ['m/s**2']

        

@vtm.register_property('resolution')
class prop_resolution(Property):
    defaultunits = u'Å/pixel'
    units = [u'Å/pixel', 'dpi', 'lpi']
        

        
        
if __name__ == '__main__':
    # print convert(-460, 'degF', 'K')
    # a = prop_temperature()
    # print a.convert(100, 'K', 'degC')
    
    # a = prop_angle()
    # print a.convert(360, 'degree', 'rad')    
        
    # a = prop_mass()
    # print a.convert(1, 'kDa', 'MDa')    
        
    a = prop_angle()
    print a.convert(1, 'degree', 'rads')    
        
        
        
__version__ = "$Revision: 1.27 $".split(":")[1][:-1].strip()
