# $Id$

import functools
import time


import emen2.db.dataobject
import emen2.db.validators
import emen2.db.config
g = emen2.db.config.g()



class ParamDef(emen2.db.dataobject.BaseDBObject):
	"""A Parameter for a value in a Record. Each record is a key/value set, where each key must be a valid ParamDef. Each ParamDef has several attributes (below), including a data type that calls a validator to check value sanity. Most parameters are indexed for queries; this can be disabled with the index attr. Generally, only descriptions and choices may be edited after creation, although an admin may make other changes. Be aware that changing vartype may be very destructive if the validators or index types are incompatible (use this carefully, or not at all if you are unsure).

	Parameters may have parent/child relationships, similar to Records.

	Validators are defined in core_vartypes. Properties in core_properties.

	@attr name Parameter name. Can be unicode; spaces will be removed.
	@attr desc_short Short description. Shown in many places in the interface as the label for this ParamDef.
	@attr desc_long Long description. Contains details about proper use of ParamDef.
	@attr vartype Data type. This is used for validation, bounds checking, etc. Choice vartypes are limited to attr choices.
	@attr choices A list of default values. If vartype="choice", values are restricted to this list.
	@attr defaultunits Default units. If units are specified, property must also be specified.
	@attr property A physical property, e.g. length, mass. Defines acceptable units and conversions.
	@attr indexed If the vartype allows it, turn indexing on/off. Default is on.
	@attr creator Creator
	@attr creationtime Creation time
	@attr modifyuser Last change user
	@attr modifytime Last change time
	@attr uri Source URI

	"""

	attr_user = set(["immutable","desc_long","desc_short","choices","name","vartype","defaultunits","property","creator","creationtime","uri","indexed","parents","children"])


	@property
	def validators(self):
		return self._validators



	def init(self, d=None):

		# This is the name of the paramdef, also used as index
		self.name = d.get('name')

		# Variable data type. List of valid types in the module global 'vartypes'
		self.vartype = d.get('vartype')

		# This is a very short description for use in forms
		self.desc_short = d.get('desc_short')

		# A complete description of the meaning of this variable
		self.desc_long = d.get('desc_long')

		# Physical property represented by this field, List in 'properties'
		self.property = d.get('property')

		# Default units (optional)
		self.defaultunits = d.get('defaultunits')

		# choices for choice and string vartypes, a tuple
		self.choices = d.get('choices')

		# immutable
		self.immutable = d.get('immutable')

		# original creator of the record
		self.creator = None

		# creation date
		self.creationtime = emen2.db.database.gettime()
		
		# source of parameter
		self.uri = None

		# turn indexing on/off, if vartype allows for it
		self.indexed = True

		self.parents = set(d.pop('parents',[]))		
		self.children = set(d.pop('parents',[]))



@ParamDef.register_validator
@emen2.db.validators.Validator.make_validator
class ParamDefValidator(emen2.db.validators.DefinitionValidator):

	def validate_name(self):
		if not self._obj.name:
			raise ValueError, "No ParamDef name given"

		self._obj.name = unicode(self._obj.name).lower()

		test = self._obj.name.replace("_","")
		if not (test.isalnum() or self._obj.name[0].isalpha()):
			raise ValueError, "ParamDef name can only include a-z, A-Z, 0-9, underscore, and must start with a letter"


	def validate_vartype(self):
		vtm = emen2.db.datatypes.VartypeManager()
		self._obj.vartype = unicode(self._obj.vartype)

		if self._obj.vartype not in vtm.getvartypes():
			raise ValueError,"Invalid vartype %s; not in valid_vartypes"%self._obj.vartype

		if self._obj.property == "":
			self._obj.property=None

		if self._obj.property != None:
			self._obj.property = unicode(self._obj.property)

			if self._obj.property not in vtm.getproperties():
				g.log.msg("LOG_WARNING", "Invalid property %s"%self._obj.property)

		if self._obj.defaultunits == "" or self._obj.defaultunits == "unitless":
			self._obj.defaultunits = None

		if self._obj.defaultunits != None:
			self._obj.defaultunits=unicode(self._obj.defaultunits)

			if self._obj.property == None:
				g.log.msg("LOG_WARNING", "Units requires property")

			else:
				prop = vtm.getproperty(self._obj.property)

				if prop.equiv.get(self._obj.defaultunits):
					self._obj.defaultunits=prop.equiv.get(self._obj.defaultunits)

				if self._obj.defaultunits not in set(prop.units):
					g.log.msg("LOG_WARNING", "Invalid default units %s for property %s"%(self._obj.defaultunits,self._obj.property))


	def validate_indexed(self):
		self._obj.indexed = bool(self._obj.indexed)


	def validate_shortdesc(self):
		if not self._obj.desc_short:
			raise ValueError,"Short description (desc_short) required"
		self._obj.desc_short = unicode(self._obj.desc_short)


	def validate_choices(self):
		if self._obj.choices:
			try:
				self._obj.choices = filter(None, (unicode(x) for x in self._obj.choices))
			except Exception, inst:
				raise ValueError, "Invalid choices (%s)"%(inst)


	def validate_creator(self):
		if not self._obj.creator:
			self._obj.creator = u"root"

		self._obj.creationtime = unicode(self._obj.creationtime)
		self._obj.creator = unicode(self._obj.creator)

		if not self._obj.creationtime or not self._obj.creator:
			g.log.msg("LOG_WARNING", "Invalid creation info: %s %s"%(self._obj.creationtime, self._obj.creator))


__version__ = "$Revision$".split(":")[1][:-1].strip()
