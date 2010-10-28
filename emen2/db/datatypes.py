# $Id$

import re
import cgi


import emen2.db.record
import emen2.db.config
g = emen2.db.config.g()


class VartypeManager(object):

	__vartypes = {}
	__properties = {}
	__macros = {}
	nonevalues = [None,"","N/A","n/a","None"] #set([None,"","N/A","n/a","None"])


	@classmethod
	def _register_vartype(cls, name, refcl):
		if name in cls.__vartypes.keys():
			raise ValueError('''vartype %s already registered''' % name)
		# g.log.msg('LOG_INIT', "REGISTERING VARTYPE (%s)"% name)
		cls.__vartypes[name]=refcl


	@classmethod
	def _register_property(cls, name, refcl):
		if name in cls.__properties.keys():
			raise ValueError('''property %s already registered''' % name)
		# g.log.msg('LOG_INIT', "REGISTERING PROPERTY (%s)"% name)
		cls.__properties[name]=refcl


	@classmethod
	def _register_macro(cls, name, refcl):
		if name in cls.__macros.keys():
			raise ValueError('''macro %s already registered''' % name)
		# g.log.msg('LOG_INIT', "REGISTERING MACRO (%s)"% name)
		cls.__macros[name]=refcl


	# rolled in MacroEngine
	def __init__(self):
		object.__init__(self)
		self.caching = False
		self.reset_cache()

	def reset_cache(self):
		self.paramdefcache = {}
		self.cache = {}

	def start_caching(self):
		self.caching = True
		self.reset_cache()

	def stop_caching(self):
		self.caching = False
		self.reset_cache()

	def toggle_caching(self):
		self.caching = not self.caching

	def get_cache_key(self, *args, **kwargs):
		return (args, tuple(kwargs.items()))

	def store(self, key, result):
		self.cache[key] = result

	def check_cache(self, key):
		if self.cache.has_key(key):
			return True, self.cache[key]
		return False, None


	# rendering methods
	def macro_preprocess(self, macro, params, recs, db=None):
		return self.__macros[macro]().preprocess(self, macro, params, recs, db)


	def macro_process(self, macro, params, rec, db=None):
		return self.__macros[macro]().process(self, macro, params, rec, db)


	def macro_render(self, macro, params, rec, mode="unicode", db=None):
		return self.__macros[macro]().render(self, macro, params, rec, mode, db)


	def name_render(self, pd, mode="unicode", db=None):
		if mode in ["html","htmledit"]:
			return u"""<a href="%s/paramdef/%s/">%s</a>"""%(g.EMEN2WEBROOT,pd.name, pd.desc_short)
		else:
			return unicode(pd.desc_short)


	def param_render(self, pd, value, mode="unicode", rec=None, db=None):
		#g.log.msg('LOG_DEBUG', "param_render: %s %s mode=%s"%(pd.vartype, value, mode))
		if pd.name in ["creator", "creationtime", "modifyuser", "modifytime", "recid", "rectype", "groups", "permissions", "history", "username"] and mode == "htmledit":
			mode = "html"
		return self.__vartypes[pd.vartype]().render(self, pd, value, mode, rec, db)


	def param_render_sort(self, pd, value, mode="unicode", rec=None, db=None):
		"""Render for native sorting, e.g. lexicographical vs. numerical"""
		vt = self.__vartypes[pd.vartype]()
		if vt.getkeytype() in ["d","f"]:
			return value
		value = vt.render(self, pd, value, mode, rec, db=db)
		if value == None:
			return value
		return value.lower()


	def macroname_render(self, macro, params, rec, mode="unicode", db=None):
		return self.__macros[macro]().macroname_render(macro, params, rec, mode, db)

	# validate, etc.

	def encode(self, pd, value):
		return self.__vartypes[pd.vartype]().encode(value)

	def decode(self, pd, value):
		return self.__vartypes[pd.vartype]().decode(pd, value)

	def validate(self, pd, value, db=None):
		if value in self.nonevalues:
			return None

		if pd.property:
			value = self.__properties[pd.property]().validate(self, pd, value, db)

		if value == None:
			return None

		ret = self.__vartypes[pd.vartype]().validate(self, pd, value, db)
		return ret


	def getvartype(self,name):
		return self.__vartypes[name]()

	def getproperty(self,name):
		return self.__properties[name]()

	def getmacro(self,name):
		return self.__macros[name]()


	def getvartypes(self):
		return self.__vartypes.keys()


	def getproperties(self):
		return self.__properties.keys()


	def getmacros(self):
		return self.__macros.keys()
		
		
		
__version__ = "$Revision$".split(":")[1][:-1].strip()
