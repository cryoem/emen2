import re

import emen2
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


regex_pattern2 = u"(\$\$(?P<var>(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"		\
								"|(\$\@(?P<macro>(?P<macro1>\w*)(?:\((?P<macro2>[\w\s,]+)\))?))(?P<macrosep>[\s<]?)" \
								"|(\$\#(?P<name>(?P<name1>\w*)))(?P<namesep>[\s<:]?)"
regex2 = re.compile(regex_pattern2, re.UNICODE) # re.UNICODE


def if_caching(f):
	def _inner(*args, **kwargs):
		if args[0].caching: return f(*args, **kwargs)
		else: pass
	return _inner


# Why is this called vartype manager when it manages other things as well?
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

	#@if_caching
	def get_cache_key(self, *args, **kwargs):
		return (args, tuple(kwargs.items()))

	#@if_caching
	def store(self, key, result):
		self.cache[key] = result

	#@if_caching
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
		if mode in ["html","htmleditable", "htmledit"]:
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
		return vt.render(self, pd, value, mode, rec, db=db)


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



	def __dicttable_view(self, params, paramdefs={}, mode="unicode", db=None):
		"""generate html table of params"""

		if mode=="html":
			dt = ["<table><tr><td><h6>Key</h6></td><td><h6>Value</h6></td></tr>"]
			for i in params:
				dt.append("<tr><td>$#%s</td><td>$$%s</td></tr>"%(i,i))
			dt.append("</table>")
		else:
			dt = []
			for i in params:
				dt.append("$#%s:\t$$%s\n"%(i,i))
		return "".join(dt)



	def renderview(self, recs, viewdef=None, viewtype="dicttable", paramdefs=None, showmacro=True, mode="unicode", outband=0, db=None):
		"""Render views"""

		if paramdefs:
			self.paramdefcache.update(paramdefs)

		# viewtype "dicttable" is builtin now.
		# ian: todo: remove.
		if recs != 0 and not recs:
			return


		ol = 0
		if not hasattr(recs,"__iter__") or isinstance(recs, emen2.Database.dataobjects.record.Record):
			ol = 1
			recs = [recs]


		if not isinstance(list(recs)[0],emen2.Database.dataobjects.record.Record):
			recs = db.getrecord(recs,filt=1)


		builtinparams=["recid","rectype","comments","creator","creationtime","permissions"]
		builtinparamsshow=["recid","rectype","comments","creator","creationtime"]

		groupviews={}
		groups = set([rec.rectype for rec in recs])
		recdefs = db.getrecorddef(groups)
		#g.debug('recdefs:', recdefs)

		if not viewdef:

			for rd in recdefs:
				i = rd.name


				if viewtype == "mainview":
					groupviews[i] = rd.mainview

				elif viewtype=="dicttable":
					# move built in params to end of table
					par = [p for p in rd.paramsK if p not in builtinparams]
					par += builtinparamsshow
					groupviews[i] = self.__dicttable_view(par, mode=mode, db=db)

				else:
					groupviews[i] = rd.views.get(viewtype, rd.name)

		else:
			groupviews[None] = viewdef


		if outband:
			for rec in recs:
				obparams = [i for i in rec.keys() if i not in recdefs[rec.rectype].paramsK and i not in builtinparams and rec.get(i) != None]
				if obparams:
					groupviews[rec.recid] = groupviews[rec.rectype] + self.__dicttable_view(obparams, mode=mode, db=db)
				# switching to record-specific views; no need to parse group views
				#del groupviews[rec.rectype]


		names = {}
		values = {}
		macros = {}
		pd = set()

		for g1,vd in groupviews.items():
			n = []
			v = []
			m = []

			vd = vd.encode('utf-8', "ignore")
			iterator = regex2.finditer(vd)

			for match in iterator:
				if match.group("name"):
						pd.add(match.group("name1"))
						n.append((match.group("name"),match.group("namesep"),match.group("name1")))
				elif match.group("var"):
						pd.add(match.group("var1"))
						v.append((match.group("var"),match.group("varsep"),match.group("var1")))
				elif match.group("macro"):
						m.append((match.group("macro"),match.group("macrosep"),match.group("macro1"), match.group("macro2")))

			names[g1] = n
			values[g1] = v
			macros[g1] = m


		if pd - set(self.paramdefcache.keys()):
			self.paramdefcache.update(db.getparamdefs(pd))


		for g1, vd in groupviews.items():
			for i in names.get(g1,[]):
				vrend = self.name_render(self.paramdefcache.get(i[2]), mode=mode, db=db)
				vd = vd.replace(u"$#" + i[0] + i[1], vrend + i[1])
			groupviews[g1] = vd
				

		ret={}


		for rec in recs:
			if groupviews.get(rec.recid):
				key = rec.recid
			else:
				key = rec.rectype
			if viewdef: key = None
			a = groupviews.get(key)

			for i in values[key]:
				v = self.param_render(self.paramdefcache[i[2]], rec.get(i[2]), mode=mode, rec=rec, db=db)
				a = a.replace(u"$$" + i[0] + i[1], v + i[1])

			if showmacro:
				for i in macros[key]:
					v=self.macro_render(i[2], i[3], rec, mode=mode, db=db)
					a=a.replace(u"$@" + i[0], v + i[1])

			ret[rec.recid]=a

		if ol:
			return ret.values()[0]
		return ret







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
			"htmleditable":self.render_htmleditable
			}


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
		"""Show editing controls"""
		if value==None:
			value=""
		else:
			value=self.render_unicode(engine, pd, value, rec.recid, db)
		return '<span class="editable" data-param="%s">%s</span>'%(pd.name,value)


	def render_htmleditable(self, engine, pd, value, rec, db):
		"""Mark field as editable, but do not show controls"""
		return self.render_html(engine, pd, value, rec, db=db, edit=1)


	def render_html(self, engine, pd, value, rec, db, edit=0):
		"""HTML output"""
		u=""
		if pd.defaultunits and pd.defaultunits != "unitless":
			u=" %s"%pd.defaultunits

		if value in [None, "None", ""] and edit:
			value='<img src="%s/images/blank.png" height="10" width="50" alt="(editable field)" />'%g.EMEN2WEBROOT
			u=""
		else:
			value=self.render_unicode(engine, pd, value, rec, db)

		return '<span class="%s" data-recid="%s" data-param="%s">%s%s</span>'%(["","editable"][edit],rec.recid, pd.name, value, u)


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

		q=re.compile("([0-9+\-\.]+)(\s+)?(\D+)?")

		value=unicode(value).strip()
		try:
			r=q.match(value).groups()
		except:
			raise ValueError,"Unable to parse '%s' for units"%(value)

		v = float(r[0])
		u = None

		if r[2] != None:
			u = unicode(r[2]).strip()

		#g.log.msg('LOG_DEBUG', "GOT VALUE AND UNITS: '%s', '%s' PARAM DU: %s, VT DU: %s"%(v,u, pd.defaultunits, self.defaultunits))

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
