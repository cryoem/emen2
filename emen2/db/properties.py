# $Id$
# This Python file is encoding:UTF-8 Encoded

import sys
import math
import re

import emen2.db.datatypes
import emen2.db.config
g = emen2.db.config.g()

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
		if hasattr(value,"__float__"):
			return float(value)

		q = re.compile("([0-9+\-\.]+)(.*)")
		value = unicode(value).strip()

		try:
			r = q.match(value).groups()
		except Exception, e:
			raise ValueError,"Unable to parse '%s' for units"%(value)

		value = float(r[0])
		
		target = pd.defaultunits
		if not target:
			target = self.defaultunits

		units = None
		if r[1] != None:
			units = unicode(r[1]).strip()
		if not units:
			units = target

		return self.convert(value, units, target)


	def check_bounds(self, value, target):
		return value


	def check_restrict(self, units, allowed):
		return
		# allowed = [equivs.get(i,i) for i in allowed]
		# if units not in allowed:
		# 	raise ValueError, "Units %s not allowed for this property. Allowed units: %s"%(units, ", ".join(allowed))
			

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





class prop_transmittance(Property):
	__metaclass__ = Property.register_view
	defaultunits = '%T'
	units = ['%T']


		


class prop_force(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'N'
	units = ['N']
	
		


class prop_energy(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'J'
	units = ['J']


		


class prop_resistance(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'ohm'
	units = ['microohm', 'milliohm', 'ohm']

		


class prop_dose(Property):
	__metaclass__ = Property.register_view
	defaultunits = "e/A2/sec"
	units = ["e/A2/sec"]


		


class prop_currency(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'dollar'
	units = ['dollar']


		


class prop_voltage(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'V'
	units = ['uV', 'mV', 'V', 'kV', 'MV']


		


class prop_pH(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'pH'
	units = ['pH']

	def check_bounds(self, value, target):
		if (target == 'pH' and not 0 <- value <- 14):
			raise ValueError, "pH must be between 0 and 14"


		


class prop_concentration(Property):
	__metaclass__ = Property.register_view	
	defaultunits = 'mg/ml'
	units = ['mg/ml', 'pfu', 'kg/kg', 'kg/m^3', 'mol/m^3', 'mol/mol']

		


class prop_angle(Property):
	__metaclass__ = Property.register_view
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





class prop_temperature(Property):
	__metaclass__ = Property.register_view
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
	
		

		


class prop_area(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'm^2'
	units = ['mm^2', 'cm^2', 'm^2', 'km^2', 'square feet']


		


class prop_current(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'A'
	units = ['uA', 'mA', 'A', 'kA', 'MA']


		


class prop_filesize(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'B'
	units = ['B', 'KB', 'MB', 'GB', 'TB', 'KiB', 'MiB', 'GiB', 'TiB']


		


class prop_percentage(Property):
	__metaclass__ = Property.register_view
	defaultunits = '%'
	units = ['%']
	

		

class prop_momentum(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'kg m/s'
	units = ['kg m/s']

		


class prop_volume(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'L'
	units = ['nL', 'uL', 'mL', 'L', 'gallon', 'm^3']


		

class prop_pressure(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'Pa'
	units = ['Pa', 'bar', 'atm', 'torr', 'psi']


		

class prop_unitless(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'unitless'
	units = ['unitless']

		


class prop_inductance(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'H'
	units = ['H']
		


class prop_currentdensity(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'Pi Amp/cm^2'
	units = ['Pi Amp/cm^2']


		

class prop_exposure(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'e/A^2'
	units = ['e/A^2']

		


class prop_count(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'count'
	units = ['count', 'pixel']




class prop_bfactor(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'A^2'
	units = ['A^2']


		


class prop_relative_humidity(Property):
	__metaclass__ = Property.register_view
	defaultunits = '%RH'
	units = ['%RH']

		


class prop_length(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'm'
	units = [u'Å', 'nm', 'um', 'mm', 'm', 'km']


		


class prop_mass(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'g'
	units = ['Da', 'kDa', 'MDa', 'ng', 'ug', 'mg', 'g', 'kg']


		


class prop_time(Property):
	__metaclass__ = Property.register_view
	defaultunits = 's'
	units = ['fs', 'ps', 'ns', 'us', 'ms', 's', 'min', 'hour', 'day', 'year']




class prop_velocity(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'm/s'
	units = ['m/s']



class prop_acceleration(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'm/s**2'
	units = ['m/s**2']

		

class prop_resolution(Property):
	__metaclass__ = Property.register_view
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
		
		
		
__version__ = "$Revision$".split(":")[1][:-1].strip()











