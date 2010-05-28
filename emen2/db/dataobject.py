from abc import ABCMeta, abstractmethod, abstractproperty
from UserDict import DictMixin
import copy


import emen2.db.config
g = emen2.db.config.g()


class BaseDBInterface(object, DictMixin):
	__metaclass__ = ABCMeta

	attr_user = set()
	attr_vartypes = {
		"modifyuser":"user",
		"modifytime":"datetime",
		"creator":"user",
		"creationtime":"datetime",
		"name":"str"
	}

	
	# Interface definition

	# @abstractproperty
	# def attr_user(self): pass

	# @abstractproperty
	# def _ctx(self): pass


	@abstractmethod
	def init(self, d):
		"""Hook to init subclasses"""
		pass


	@abstractmethod
	def keys(self):
		pass


	@abstractmethod
	def validate(warning=False, ctx=None, txn=None):
		pass
		

	# End interface definition


	@classmethod
	def register_validator(cls, validatortype):
		cls.__validator = validatortype
		return validatortype

	def validate_auto(self, **kwargs):
		return self.__validator(self).validate(**kwargs)

	validate = validate_auto



	def __init__(self, _d=None, **_k):
		"""Accept either a dictionary named '_d' or keyword arguments. Remove the ctx and use it for setContext. See the Class docstring for what arguments are accepted."""
		
		if _d == None: _d = {}
		ctx = _k.pop("ctx",None)
		_d.update(_k)
		self.setContext(ctx)
		self.init(_d)


	def setContext(self, ctx=None):
		"""Set permissions and create reference to active database."""
		self._ctx = ctx

		

	#################################
	# Mapping methods. These may be changed if you want to implement special behavior,
	#	e.g. records["permissions"] = [...]
	#################################

	def __getitem__(self,key):
		try: return self.__dict__[key]
		except: pass


	def __setitem__(self,key,value):
		if key in self.attr_user:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key


	def __delitem__(self, key):
		raise AttributeError, 'Key deletion not allowed'


	def __unicode__(self):
		"A string representation of the record"
		ret = ["%s\n"%(self.__class__.__name__)]
		for i,j in self.items():
			ret.append(u"%12s:	%s\n"%(unicode(i),unicode(j)))
		return u"".join(ret)


	def __str__(self):
	 	return self.__unicode__().encode('utf-8')


	# def __repr__(self):
	# 	return "<Record id: %s recdef: %s at %x>" % (self.recid, self.rectype, id(self))


	##########################
	# Pickle methods
	##########################
	
	def __getstate__(self):
		"""Context and other session-specific information should not be pickled"""

		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_ctx'] = None
		return odict


	# ian: migration scripts can set this method, which is called during import.
	def upgrade(self):
		pass


	def validationwarning(self, msg, e=None, warning=False):
		if e == None:
			e = ValueError
		if warning:
			g.warn("Validation warning: %s"%(msg))
		elif e:
			raise e, msg



class BaseDBObject(BaseDBInterface):
	"""Most items in the DB will use this interface."""

	attr_user = set(["modifyuser","modifytime","creator","creationtime","name"])

	def init(self, d):
		self.update(d)

	def keys(self):
		return self.attr_user


