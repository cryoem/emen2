import re
import cgi

import emen2.db.record
import emen2.db.config
g = emen2.db.config.g()



# def if_caching(f):
# 	def _inner(*args, **kwargs):
# 		if args[0].caching: return f(*args, **kwargs)
# 		else: pass
# 	return _inner


# ian: todo: this became somewhat unfocused; it might benefit from a rework.

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

	def macro_process(self, macro, params, rec, db=None):
		return self.__macros[macro]().process(self, macro, params, rec, db)


	def macro_render(self, macro, params, rec, mode="unicode", db=None):
		return self.__macros[macro]().render(self, macro, params, rec, mode, db)


	def name_render(self, pd, mode="unicode", db=None):
		if mode in ["html","htmledit"]:
			return u"""<a href="%s/db/paramdef/%s/">%s</a>"""%(g.EMEN2WEBROOT,pd.name, pd.desc_short)
		else:
			return unicode(pd.desc_short)


	def param_render(self, pd, value, mode="unicode", rec=None, db=None):
		#g.log.msg('LOG_DEBUG', "param_render: %s %s mode=%s"%(pd.vartype, value, mode))
		return self.__vartypes[pd.vartype]().render(self, pd, value, mode, rec, db)


	def param_render_sort(self, pd, value, mode="unicode", rec=None, db=None):
		"""Render for native sorting, e.g. lexicographical vs. numerical"""
		vt = self.__vartypes[pd.vartype]()
		if vt.getindextype() in ["d","f"]:
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









class Vartype(object):
	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls

	@classmethod
	def register(cls):
		name = cls.__name__
		if name.startswith('vt_'): name = name.split('_',1)[1]
		cls.__vartype__ = property(lambda *_: name)
		VartypeManager._register_vartype(name, cls)

	def __init__(self):
		# typical modes: html, unicode, edit
		self.modes={
			"html":self.render_html,
			"htmledit":self.render_htmledit,
			}


	def check_iterable(self, value):
		if not value:
			value=[]
		if not hasattr(value,"__iter__"):
			value=[value]	
		return value


	def getvartype(self):
		return self.__vartype__


	def getindextype(self):
		try:
			return self.__indextype__
		except:
			return None


	def render(self, engine, pd, value, mode, rec, db):
		return self.modes.get(mode, self.render_unicode)(engine, pd, value, rec, db)
		# except Exception, e:
		# 	g.log.msg('LOG_DEBUG', "render error: %s"%e)
		# 	try:
		# 		return unicode(value)
		# 	except:
		# 		return "(Error)"


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)


	def render_htmledit(self, engine, pd, value, rec, db):
		"""Mark field as editable, but do not show controls"""
		return self.render_html(engine, pd, value, rec, db=db, edit=1)


	def render_html(self, engine, pd, value, rec, db, edit=0):
		"""HTML output"""
		u = ""
		if pd.defaultunits and pd.defaultunits != "unitless":
			u = " %s"%pd.defaultunits

		if value in [None, "None", ""] and edit:
			value = '<img src="%s/images/blank.png" height="10" width="50" alt="(Editable)" />'%g.EMEN2WEBROOT
			u = ""
		else:
			value = cgi.escape(self.render_unicode(engine, pd, value, rec, db))
		
		if edit:
			return '<span class="editable" data-recid="%s" data-param="%s">%s%s <span class="label">Edit</span></span>'%(rec.recid, pd.name, value, u)
		else:	
			return '<span>%s%s</span>'%(value, u)



	def encode(self, value):
		return value


	def decode(self, pd, value):
		return value


	def validate(self, engine, pd, value, db):
		# return a validated value
		return value



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
		VartypeManager._register_property(name, cls)


	def validate(self, engine, pd, value, db):
		if hasattr(value,"__float__"):
			return float(value)

		#q=re.compile("([0-9+\-\.]+)(\s+)?(\D+)?")
		#ed: TODO: make sure this is correct, old one didn't work for e/A^2
		q=re.compile("([0-9+\-\.]+)(\s+)?(.+?)?\s*$")

		value=unicode(value).strip()
		try:
			r=q.match(value).groups()
		except:
			raise ValueError,"Unable to parse '%s' for units"%(value)

		v = float(r[0])
		u = None

		if r[2] != None:
			u = unicode(r[2]).strip()

		g.log.msg('LOG_DEBUG', "GOT VALUE AND UNITS: '%s', '%s' PARAM DU: %s, VT DU: %s"%(v,u, pd.defaultunits, self.defaultunits))

		if u == pd.defaultunits or u == None:
			#g.log.msg('LOG_DEBUG', "No units specified or defaultunits; no conversion necessary")
			return v

		du=pd.defaultunits
		if pd.defaultunits == None:
			#g.log.msg('LOG_DEBUG', "No paramdef defaultunits, using vartype defaultunits of %s"%self.defaultunits)
			du=self.defaultunits

		return self.convert(v, u, du, db)


	def convert(self, value, u, target, db):

		if self.conv.get((u,target)):
			return self.conv.get((u,target))(value,db)

		equiv = self.units.get(u) or self.units.get(self.equiv.get(u))
		du = self.units.get(target) or self.units.get(self.equiv.get(target))

		if equiv == None:
			raise ValueError, "Unknown units '%s' (value is '%s'). Valid units: %s"%(u, value, set([self.defaultunits]) | set(self.units.keys()) | set(self.equiv.keys()))

		#g.log.msg('LOG_DEBUG', "Using units %s, target is %s, conversion factor %s, %s"%(u, target, equiv, du))
		#value = value * ( valid_properties[pd.property][1][units] / valid_properties[pd.property][1][defaultunits] )
		newv = value * ( equiv / du )
		#if value != newv:
		#	g.log.msg('LOG_DEBUG', "Property: converted: %s -> %s"%(value,newv))
		return newv





class Macro(object):
	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls

	@classmethod
	def register(cls):
		name = cls.__name__
		if name.startswith('macro_'): name = name.split('_',1)[1]
		VartypeManager._register_macro(name, cls)

	def __init__(self):
		# typical modes: html, unicode, edit
		self.modes={}

	def process(self, engine, macro, params, rec, db):
		return "macro: %s"%macro

	def render(self, engine, macro, params, rec, mode, db):
		value=self.process(engine, macro, params, rec, db)
		return self.modes.get(mode, self.render_unicode)(engine, value, macro, params, rec, db)

	def render_unicode(self, engine, value, macro, params, rec, db):
		return unicode(value)

	def macroname_render(self, macro, params, rec, mode="unicode", db=None):
		return unicode("Maco: %s(%s)"%(macro,params))
