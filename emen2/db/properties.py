# $Id$

import sys
import math
import re


import emen2.db.datatypes
import emen2.db.config
g = emen2.db.config.g()

import emen2.db.magnitude as mg


equivs = {
	'mm^2': 'mm mm',
	'cm^2': 'cm cm',
	'm^2': 'm m',
	'km^2': 'km km',
	'square feet': 'ft ft',
	'square meters': 'm m',
	'square kilometers': 'km km',	

	'gallons': 'gallon',

	'kg/m^3': 'kg/m m m',
	'mol/m^3': 'mol/m m m',	
	'm^3': 'm m m',

	'Torr': 'torr',

	# It's just a PITA to use the Unicode Angstrom symbol... :(
	'Angstrom': 'Angstrom',
	'Angstroms': 'Angstroms',

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
	
	'rad': 'rad',
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

bytes_equivs = {
	'bit': 'b',
	'bits': 'b',
	'byte': 'B',
	'bytes': 'B',
}

bytes_prefix = {
	'Kibi': 'Ki',
	'Mebi': 'Mi',
	'Gibi': 'Gi',
	'Tebi': 'Ti',
	'Pebi': 'Pi',
	'Exbi': 'Ei'
}


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




#for k,v in sorted(equivs.items()):
#	print k,v


# Some additional units
mg.new_mag('Angstrom', mg.Magnitude(1e-10, m=1))
mg.new_mag('pixel', mg.Magnitude(1.0))
mg.new_mag('count', mg.Magnitude(1.0))
mg.new_mag('degF', mg.Magnitude(1.0))

mg.new_mag('gallon', mg.Magnitude(3.78541178e-3, m=3))

mg.new_mag('torr', mg.Magnitude(1/760.0, m=-1, kg=1, s=-2))

mg.new_mag('Da', mg.Magnitude(1.6605402e-27, kg=1))

mg.new_mag('unitless', mg.Magnitude(1))
mg.new_mag('%RH', mg.Magnitude(1))
mg.new_mag('%RH', mg.Magnitude(1))
mg.new_mag('%T', mg.Magnitude(1))
mg.new_mag('%', mg.Magnitude(1))

mg.new_mag('degree', mg.Magnitude(1))
mg.new_mag('pfu', mg.Magnitude(1))



def convert(value, units, target):
	print "CONVERTING: ", value, units, target

	units = equivs.get(units, units)
	target = equivs.get(target, target)	
	special = ['degC', 'K', 'degF', 'degree']
	
	if not units or units == target or units == 'unitless':
		return value

	if units not in special and target not in special:
		return mg.mg(value, units, ounit=target)
						
	# Degrees / Radians
	if units == 'degree' and target == 'rad':
		return value * (math.pi / 180.0)
	elif units == 'rad' and target == 'degree':
		return value * (180.0 / math.pi)
		
	# C / K
	if units == 'degC' and target == 'K':
		return value + 273.15
	elif units == 'K' and target == 'degC':
		return value - 273.15

	# F / K
	if units == 'degF' and target == 'K':
		return (value + 459.67) * (5.0 / 9.0)
	elif units == 'K' and target == 'degF':
		return (value * (9.0 / 5.0)) - 459.67

	# C / F
	if units == 'degC' and target == 'degF':
		return value * (9.0 / 5.0) + 32
	elif units == 'degF' and target == 'degC':
		return (value - 32) * (5.0 / 9.0)


	raise ValueError, "Cannot convert from %s to %s"%(units, target)





class Property(object):

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls

	@classmethod
	def register(cls):
		name = cls.__name__
		if name.startswith('prop_'): name = name.split('_',1)[1]
		emen2.db.datatypes.VartypeManager._register_property(name, cls)


	def validate(self, engine, pd, value, db):
		if hasattr(value,"__float__"):
			return float(value)

		#q=re.compile("([0-9+\-\.]+)(\s+)?(\D+)?")
		#ed: TODO: make sure this is correct, old one didn't work for e/A^2
		q=re.compile("([0-9+\-\.]+)(\s+)?(.+?)?\s*$")

		value=unicode(value).strip()
		try:
			r = q.match(value).groups()
		except:
			raise ValueError,"Unable to parse '%s' for units"%(value)

		value = float(r[0])
		units = None
		if r[2] != None:
			units = unicode(r[2]).strip()

		target = pd.defaultunits
		if not target:
			target = self.defaultunits

		return convert(value, units, target)


	# def convert(self, value, u, target, db):
	# 	# value is value to convert
	# 	# u = parameter's default units
	# 	# target = target units
	# 	# db = database handle
	# 	if self.conv.get((u,target)):
	# 		return self.conv.get((u,target))(value,db)
	# 
	# 	equiv = self.units.get(u) or self.units.get(self.equiv.get(u)) or self.units.get(self.equiv.get(u.lower()))
	# 	du = self.units.get(target) or self.units.get(self.equiv.get(target))
	# 
	# 	if equiv == None:
	# 		raise ValueError, "Unknown units '%s' (value is '%s'). Valid units: %s"%(u, value, set(self.units.keys()))
	# 
	# 	#g.log.msg('LOG_DEBUG', "Using units %s, target is %s, conversion factor %s, %s"%(u, target, equiv, du))
	# 	#value = value * ( valid_properties[pd.property][1][units] / valid_properties[pd.property][1][defaultunits] )
	# 	newv = value * ( equiv / du )
	# 	#if value != newv:
	# 	#	g.log.msg('LOG_DEBUG', "Property: converted: %s -> %s"%(value,newv))
	# 	return newv





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

		


class prop_concentration(Property):
	__metaclass__ = Property.register_view	
	defaultunits = 'mg/ml'
	units = ['mg/ml', 'pfu', 'kg/kg', 'kg/m^3', 'mol/m^3', 'mol/mol']

		


class prop_angle(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'rad'
	units = ['mrad', 'rad', 'degree']


		


class prop_temperature(Property):
	__metaclass__ = Property.register_view
	defaultunits = 'K'
	units = ['degC', 'K', 'degF']
	
		

		


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
	units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'KiB', 'MiB', 'GiB', 'TiB']


		


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
	units = ['Angstrom', 'nm', 'um', 'mm', 'm', 'km']


		


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
	defaultunits = 'Angstrom/pixel'
	units = ['Angstrom/pixel', 'dpi', 'lpi']
		
		
		
__version__ = "$Revision$".split(":")[1][:-1].strip()











