from abc import ABCMeta, abstractmethod, abstractproperty
from UserDict import DictMixin
import copy



class Validator(object):
	_validators = []

	@classmethod
	def make_validator(cls, othercls):
		othercls._validators = copy.deepcopy(othercls._validators)
		othercls._validators.extend(v for k, v in othercls.__dict__.iteritems() if k.startswith('validate'))
		return othercls

	def __init__(self, obj): self._obj = obj

	def __get_validators(self):
		return [item for item in self._validators]

	def validate(self, warning=False):
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




class BaseDBInterface(object, DictMixin):
	__metaclass__ = ABCMeta
	# Interface definition
	#   properties
	@abstractproperty
	def attr_user(self): pass

	@abstractproperty
	def attr_admin(self): pass

	#@abstractproperty
	#def _ctx(self): pass

	#  methods
	@abstractmethod
	def init(self, d): pass

	@abstractmethod
	def keys(self): pass
	# End interface definition

	@abstractmethod
	def validate(warning=False, ctx=None, txn=None): pass

	@property
	def attr_all(self): return self.attr_user | self.attr_admin

	@classmethod
	def register_validator(cls, validatortype):
		cls.__validator = validatortype
		return validatortype

	def validate_auto(self, **kwargs):
		return self.__validator(self).validate(**kwargs)
	validate = validate_auto

	attr_vartypes = {
		"modifyuser":"user", "modifytime":"datetime", "creator":"user", "creationtime":"datetime", "name":"str"
	}


	def __init__(self, _d=None, **_k):
		if _d == None: _d = {}
		ctx = _k.pop("ctx",None)
		_d.update(_k)
		self.setContext(ctx)
		self.init(_d)


	def setContext(self, ctx=None):
		self._ctx = ctx

	def __str__(self): return unicode(repr(self)) + unicode(dict(self))


	#################################
	# mapping methods
	#################################

	def __getitem__(self,key):
		try: return self.__dict__[key]
		except: pass


	def __setitem__(self,key,value):
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key

	def __delitem__(self, key):
		raise AttributeError, 'Key deletion not allowed'

	# ian: migration scripts can set this method, which is called during import.
	def upgrade(self):
		pass



class BaseDBObject(BaseDBInterface):
	"""Most items in the DB will use this interface."""

	@property
	def attr_user(self): return set(["modifyuser","modifytime"])

	@property
	def attr_admin(self): return set(["creator","creationtime","name"])

	def init(self, d):
		self.update(d)

	def keys(self):
		return self.attr_all


