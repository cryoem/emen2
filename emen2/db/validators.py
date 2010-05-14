import functools

import emen2.globalns
g = emen2.globalns.GlobalNamespace()
import copy


class Validator(object):
	"""This class handles validation for a DBObject class."""
	
	_validators = []

	@classmethod
	def make_validator(cls, othercls):
		"""Create and register a Validator class"""
		othercls._validators = copy.deepcopy(othercls._validators)
		othercls._validators.extend(v for k, v in othercls.__dict__.iteritems() if k.startswith('validate'))
		return othercls


	def __init__(self, obj):
		"""Create a reference to the instance being validated"""
		self._obj = obj


	def __get_validators(self):
		"""Return the validation functions"""
		return [item for item in self._validators]


	def validate(self, warning=False):
		"""Perform validation
		
		@keyparam warning Ignore failures; currently this parameter is not used and all failures raise Exceptions
		
		"""
		
		failures = []
		# ian: todo: fix this so that it raises all relevant exceptions, not just the first
		# (this appears to have been working at one point...)
		for validator in self.__get_validators():
			#try:
			#print validator
			validator(self)
			#except Exception, e:
			#	failures.append((e,validator))
		return failures or True






@Validator.make_validator
class DefinitionValidator(Validator):
	def validate_attributes(self):
		badattrs = set(k for k in self._obj.__dict__.keys() if not k.startswith('_'))-self._obj.attr_user
		if badattrs:
			raise AttributeError,"Invalid attributes: %s"%", ".join(badattrs)
		return True

	def validate_name(self):
		if not self._obj.name: raise ValueError,"name required"
		self._obj.name = unicode(self._obj.name)
		#if not self._obj.name.replace('_','').isalnum():
		#	raise ValueError, "name must only contain alphanumeric characters or underscores"
		return True

	def validate_longdesc(self):
		self._obj.desc_long = unicode(self._obj.desc_long)

	def validate_uri(self):
		if hasattr(self._obj, 'uri') and self._obj.uri:
			self._obj.uri = unicode(self._obj.uri)
		elif not hasattr(self._obj, 'uri'):
			self._obj.uri = None
