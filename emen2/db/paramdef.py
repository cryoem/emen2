# $Id$

import functools
import time

import emen2.util.listops

import emen2.db.btrees
import emen2.db.dataobject
import emen2.db.magnitude

import emen2.db.config
g = emen2.db.config.g()



class ParamDef(emen2.db.dataobject.BaseDBObject):
	"""A Parameter for a value in a Record. Each record is a key/value set, where each key must be a valid ParamDef. Each ParamDef has several attributes (below), including a data type that calls a validator to check value sanity. Most parameters are indexed for queries; this can be disabled with the indexed attr. Generally, only descriptions and choices may be edited after creation, although an admin may make other changes. Be aware that changing vartype may be very destructive if the validators or index types are incompatible (use this carefully, or not at all if you are unsure).

	@attr desc_short Short description. Shown in many places in the interface as the label for this ParamDef.
	@attr desc_long Long description. Contains details about proper use of ParamDef.
	@attr vartype Data type. This is used for validation, bounds checking, etc. Choice vartypes are limited to attr choices.
	@attr choices A list of default values. If vartype="choice", values are restricted to this list.
	@attr defaultunits Default units. If units are specified, property must also be specified.
	@attr property A physical property, e.g. length, mass. Defines acceptable units and conversions.
	@attr indexed If the vartype allows it, turn indexing on/off. Default is on.
	"""

	param_all = emen2.db.dataobject.BaseDBObject.param_all | set(['immutable', 'desc_long', 'desc_short', 'choices', 'vartype', 'defaultunits', 'property', 'indexed'])
	param_required = set(['vartype'])


	def init(self, d):

		# Variable data type. List of valid types in the module global 'vartypes'
		self.__dict__['vartype'] = d.pop('vartype')

		# This is a very short description for use in forms
		self.__dict__['desc_short'] = self.name

		# A complete description of the meaning of this variable
		self.__dict__['desc_long'] = ''

		# Physical property represented by this field, List in 'properties'
		self.__dict__['property'] = None

		# Default units (optional)
		self.__dict__['defaultunits'] = None

		# choices for choice and string vartypes, a tuple
		self.__dict__['choices'] = []

		# Immutable
		self.__dict__['immutable'] = False

		# turn indexing on/off, if vartype allows for it
		self.__dict__['indexed'] = True


	#################################
	# Setters
	#################################

	# ParamDef does so much validation for other items, so everything is checked.... 
	# Several values can only be changed by administrators.

	def _set_choices(self, key, value, vtm=None, t=None):
		value = emen2.util.listops.check_iterable(value)
		value = filter(None, [unicode(i) for i in value]) or None
		return self._set(key, value, self.isowner())


	# These 3 methods are borrowed from RecordDef
	def _set_desc_short(self, key, value, vtm=None, t=None):
		return self._set(key, unicode(value or self.name), self.isowner())
		

	def _set_desc_long(self, key, value, vtm=None, t=None):
		return self._set(key, unicode(value or ''), self.isowner())
		

	def _set_typicalchld(self, key, value, vtm=None, t=None):
		value = emen2.util.listops.check_iterable(value)
		value = filter(None, [unicode(i) for i in value]) or None
		return self._set(key, value, self.isowner())
		
		
	# Only admin can change defaultunits/immutable/indexed/vartype.
	# This should still generate lots of warnings.
	def _set_immutable(self, key, value, vtm=None, t=None):
		return self._set(key, bool(value), self._ctx.checkadmin())


	def _set_indexed(self, key, value, vtm=None, t=None):
		return self._set(key, bool(value), self._ctx.checkadmin())


	# These can't be changed, it would disrupt the meaning of existing Records.	
	def _set_vartype(self, key, value, vtm=None, t=None):
		vtm, t = self._vtmtime(vtm, t)
		value = unicode(value or '') or None

		if value not in vtm.getvartypes():
			self.error("Invalid vartype: %s"%value)

		if self.vartype and self.vartype != value:
			self.error("Cannot change vartype from %s to %s."%(self.vartype, value))

		return self._set(key, value)


	def _set_property(self, key, value, vtm=None, t=None):
		vtm, t = self._vtmtime(vtm, t)
		value = unicode(value or '')
		if value in ['None', None, '']:
			value = None
			
		# Allow for unsetting
		if value != None and value not in vtm.getproperties():
			self.error("Invalid property: %s"%value)

		if self.property and self.property != value:
			self.error("Cannot change property from %s to %s."%(self.property, value))	

		return self._set('property', value)

		
	def _set_defaultunits(self, key, value, vtm=None, t=None):
		vtm, t = self._vtmtime(vtm, t)		
		value = unicode(value or '') or None			
		value = emen2.db.properties.equivs.get(value, value)

		if self.defaultunits and self.defaultunits != value:
			self.error("Cannot change defaultunits from %s to %s."%(self.defaultunits, value))

		return self._set('defaultunits', value)

	
	# def validate(self):
	# 	try:
	# 		prop = vtm.getproperty(self.property)	
	# 	except:
	# 		self.error("Cannot set defaultunits without a property!")
	#	try:
	#		m = emen2.db.magnitude.mg(0, value)
	# 	except:
	#		self.error("Invalid units: %s"%value)
	# 	if value not in prop.units:
	# 		self.error("Invalid defaultunits %s for property %s. Allowed: %s"%(value, self.property, ", ".join(prop.units)))

				




class ParamDefBTree(emen2.db.btrees.RelateBTree):
	def init(self):
		self.setdatatype('p', emen2.db.paramdef.ParamDef)
		super(ParamDefBTree, self).init()






__version__ = "$Revision$".split(":")[1][:-1].strip()
