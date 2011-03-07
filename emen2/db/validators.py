# $Id$

import copy
import functools
import re


import emen2.db.config
#g = emen2.db.config.g()


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


	def _get_validators(self):
		"""Return the validation functions"""
		return [item for item in self._validators]


	def validate(self, warning=False):
		"""Perform validation

		@keyparam warning Ignore failures; currently this parameter is not used and all failures raise Exceptions

		"""

		failures = []
		# ian: todo: fix this so that it raises all relevant exceptions, not just the first
		# (this appears to have been working at one point...)
		for validator in self._get_validators():
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




# ian: moved this here from emen2.web.text_validators
# ed: this is completely irrelevant to what comes before
class InputValidator(object):
	'''Base class to validate input'''
	def __init__(self):
		self._predicates = {}

	def add_predicate(self, name, predicate='is_alnum'):
		'''Add a condition to the validator'''
		if isinstance(predicate, str):
			predicate = getattr(InputValidator, predicate)
		self._predicates[name] = predicate

	def check_field(self, name, value):
		'''Match a specific name/value pair'''
		result = True
		if self._predicates.has_key(name):
			# print name, self._predicates[name]
			result = self._predicates[name](value)
		return result

	def check_dictionary(self, fields):
		'''Match a dictionary against the stored conditions'''
		result = []
		if not fields: result = self._predicates.keys()
		for field in fields:
			if not self.check_field(field, fields[field]):
				result.append(field)
		return result

	@staticmethod
	def is_string(inp): return isinstance(inp, str)

	@staticmethod
	def _is_of_pred(self, pred, inp):
		'''utility function for composing new predicates'''
		return len([ch for ch in inp if not pred(ch)]) == 0


	# @staticmethod
	# def is_alnum(self, inp):
	# 	inp = ''.join(inp.split())
	# 	if not inp: return False
	# 	return inp.isalnum()

	is_alnum = staticmethod(lambda inp: ''.join(inp.split()).isalnum())
	is_alpha = staticmethod(lambda inp: ''.join(inp.split()).isalpha())
	is_numeric = str.isdigit

	@staticmethod
	def is_of_pattern(re):
		'''match input against a regex'''
		def _validate(inp):
			return bool(re.match(inp))
		return _validate


__version__ = "$Revision$".split(":")[1][:-1].strip()
