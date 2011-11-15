# $Id$
"""Vartype, Property, and Macro managers

Classes:
	VartypeManager:
		= Registers available Vartypes, Properties, and Macros
		- Helper methods for access, validating, and rendering parameters
		- This class may be replaced in the future, by moving it to the 
			appropriate Vartype/Property/Macro classes.
"""

import re
import cgi

class VartypeManager(object):

	_vartypes = {}
	_properties = {}
	_macros = {}
	nonevalues = [None,"","N/A","n/a","None"]

	@classmethod
	def register_vartype(cls, name):
		def f(o):
			if name in cls._vartypes.keys():
				raise ValueError("""vartype %s already registered""" % name)
			#emen2.db.log.info("REGISTERING VARTYPE (%s)"% name)
			o.vartype = property(lambda *_: name)
			cls._vartypes[name] = o
			return o
		return f


	@classmethod
	def register_property(cls, name):
		def f(o):
			if name in cls._properties.keys():
				raise ValueError("""property %s already registered""" % name)
			#emen2.db.log.info("REGISTERING PROPERTY (%s)"% name)
			cls._properties[name] = o
			return o
		return f


	@classmethod
	def register_macro(cls, name):
		def f(o):
			if name in cls._macros.keys():
				raise ValueError("""macro %s already registered""" % name)
			#emen2.db.log.info("REGISTERING MACRO (%s)"% name)
			cls._macros[name] = o
			return o
		return f


	def __init__(self, db=None):
		object.__init__(self)
		self.db = db
		self.caching = False
		self.reset_cache()


	###################################
	# Caching
	###################################

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


	###################################
	# Macro Rendering
	###################################

	def macro_preprocess(self, macro, params, recs):
		return self._macros[macro](engine=self).preprocess(macro, params, recs)


	def macro_process(self, macro, params, rec):
		return self._macros[macro](engine=self).process(macro, params, rec)


	def macro_render(self, macro, params, rec, **kwargs):
		return self._macros[macro](engine=self).render(macro, params, rec, **kwargs)


	def macro_name(self, macro, params):
		return self._macros[macro](engine=self).macro_name(macro, params, rec)


	###################################
	# ParamDef Rendering
	###################################

	def name_render(self, pd, markup=False):
		return u"""<span class="paramdef" title="%s -- %s">%s</span>"""%(pd.name, pd.desc_long, pd.desc_short)

		# if mode in ["html","htmledit"]:
		# else:
		# return unicode(pd.desc_short)


	###################################
	# Param Rendering
	###################################

	def param_render(self, pd, value, **kwargs):
		return self._vartypes[pd.vartype](engine=self, pd=pd).render(value, **kwargs)


	def param_render_sort(self, pd, value, **kwargs):
		"""Render for native sorting, e.g. lexicographical vs. numerical"""

		vt = self._vartypes[pd.vartype](engine=self, pd=pd)

		if vt.getkeytype() in ["d","f"]:
			return rec.get(pd.name)

		value = vt.render(value=value)

		if value == None:
			return value

		return value.lower()


	###################################
	# Validation
	###################################

	def encode(self, pd, value):
		return self._vartypes[pd.vartype](engine=self, pd=pd).encode(value)


	def decode(self, pd, value):
		return self._vartypes[pd.vartype](engine=self, pd=pd).decode(value)


	def validate(self, pd, value):
		if value in self.nonevalues:
			return None

		if pd.property:
			value = self._properties[pd.property]().validate(self, pd, value, self.db)

		return self._vartypes[pd.vartype](engine=self, pd=pd).validate(value)


	###################################
	# Misc
	###################################

	def getkeytype(self, name):
		pass


	def getvartype(self, name):
		return self._vartypes[name]()


	def getproperty(self, name):
		return self._properties[name]()


	def getmacro(self, name):
		return self._macros[name]()


	def getvartypes(self):
		return self._vartypes.keys()


	def getproperties(self):
		return self._properties.keys()


	def getmacros(self):
		return self._macros.keys()



__version__ = "$Revision$".split(":")[1][:-1].strip()
