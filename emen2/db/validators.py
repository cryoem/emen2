import functools

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import emen2.Database.dataobject

@emen2.Database.dataobject.Validator.make_validator
class DefinitionValidator(emen2.Database.dataobject.Validator):
	def validate_attributes(self):
		badattrs = set(k for k in self._obj.__dict__.keys() if not k.startswith('_'))-self._obj.attr_all
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
