# $Id$

import operator


import emen2.db.datatypes
import emen2.db.config
g = emen2.db.config.g()



class Macro(object):

	keytype = 's'

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls


	@classmethod
	def register(cls):
		name = cls.__name__
		if name.startswith('macro_'): name = name.split('_',1)[1]
		emen2.db.datatypes.VartypeManager._register_macro(name, cls)


	def __init__(self, engine=None):
		self.engine = engine


	def getkeytype(self):
		return self.keytype
		
		
	# Pre-cache if we're going to be doing alot of records.. This can be a substantial improvement.
	def preprocess(self, macro, params, recs):
		pass
		

	# Run the macro
	def process(self, macro, params, rec):
		return "Macro: %s"%macro


	# Render the macro
	def render(self, macro, params, rec, markup=False, table=False):
		self.rec = rec
		self.table = table
		self.markup = markup
		value = self.process(macro, params, rec)
		return self._render(value)


	# Post-rendering
	def _render(self, value):
		if hasattr(value, '__iter__'):
			value = ", ".join(map(unicode, value))
		if not self.markup:
			return unicode(value)		
		if self.table:
			value = '<a href="%s/record/%s/">%s</a>'%(g.EMEN2WEBROOT, self.rec.name, value)
		return unicode(value)


	# Get some info about the macro
	def macro_name(self, macro, params):
		return unicode("Maco: %s(%s)"%(macro,params))





# ian: todo: Macros can specify a return vartype, which will go through normal rendering... 

class macro_name(Macro):
	"""name macro"""
	keytype = 'd'
	__metaclass__ = Macro.register_view

	def process(self, macro, params, rec):
		return rec.name
		

	def macro_name(self, macro, params):
		return "Record Name"


# legacy..
class macro_recid(Macro):
	"""name macro"""
	keytype = 'd'
	__metaclass__ = Macro.register_view

	def process(self, macro, params, rec):
		return rec.name


	def macro_name(self, macro, params):
		return "Record Name"





class macro_parents(Macro):
	__metaclass__ = Macro.register_view
			
	def process(self, macro, params, rec):
		rectype, _, recurse = params.partition(",")
		recurse = int(recurse or 1)
		return self.engine.db.getparents(rec.name, rectype=rectype, recurse=recurse)
		

	def macro_name(self, macro, params):
		return "Parents: %s"%params				
				



class macro_recname(Macro):
	"""recname macro"""
	__metaclass__ = Macro.register_view
			
	def process(self, macro, params, rec):
		return self.engine.db.renderview(rec) #vtm=self.engine


	def macro_name(self, macro, params):
		return "Record ID"				
				


class macro_childcount(Macro):
	"""childcount macro"""
	keytype = 'd'
	__metaclass__ = Macro.register_view
	
	def preprocess(self, macro, params, recs):
		rectypes = params.split(",")
		# ian: todo: recurse = -1..
		children = self.engine.db.getchildren([rec.name for rec in recs], rectype=rectypes, recurse=3)
		for rec in recs:
			key = self.engine.get_cache_key('getchildren', rec.name, *rectypes)
			self.engine.store(key, len(children.get(rec.name,[])))

		
	def process(self, macro, params, rec):
		"""Now even more optimized!"""
		rectypes = params.split(",")
		key = self.engine.get_cache_key('getchildren', rec.name, *rectypes)
		hit, children = self.engine.check_cache(key)
		if not hit:
			children = len(self.engine.db.getchildren(rec.name, rectype=rectypes, recurse=3))
			self.engine.store(key, children)

		return children


	def macro_name(self, macro, params):
		return "Childcount: %s"%(params)




class macro_img(Macro):
	"""image macro"""
	__metaclass__ = Macro.register_view

	def process(self, macro, params, rec):
		default = ["file_binary_image","640","640"]
		ps = params.split(",")
		for i,v in list(enumerate(ps))[:3]:
			default[i] = v
			
		param, width, height = default

		pd = self.engine.db.getparamdef(param)

		if pd.vartype=="binary":
			bdos = rec[param]
		elif pd.vartype=="binaryimage":
			bdos = [rec[param]]
		else:
			return "(Invalid parameter)"

		#print bdos
		if bdos == None:
			return "(No Image)"

		ret = []
		for i in bdos:
			try:
				bdoo = self.engine.db.getbinary(i, filt=False)
				fname = bdoo.get("filename")
				bname = bdoo.get("filepath")
				ret.append('<img src="%s/download/%s/%s" style="max-height:%spx;max-width:%spx;" alt="" />'%(g.EMEN2WEBROOT,i[4:], fname, height, width))
			except (KeyError, AttributeError, emen2.db.exceptions.SecurityError):
				ret.append("(Error: %s)"%i)

		return "".join(ret)


	def macro_name(self, macro, params):
		return "Image Macro"



class macro_childvalue(Macro):
	"""childvalue macro"""
	__metaclass__ = Macro.register_view

	def process(self, macro, params, rec):
		name = rec.name
		children = self.engine.db.getrecord(self.engine.db.getchildren(name))
		return [i.get(params) for i in children]


	def macro_name(self, macro, params):
		return "Child Value: %s"%params



class macro_parentvalue(Macro):
	"""parentvalue macro"""
	__metaclass__ = Macro.register_view
		
	def process(self, macro, params, rec):
		p = params.split(",")
		param, recurse, rectype = p[0], 1, None

		if len(p) == 3:
			param, recurse, rectype = p
		elif len(p) == 2:
			param, recurse = p
			
		recurse = int(recurse or 1)
		name = rec.name
		parents = self.engine.db.getrecord(self.engine.db.getparents(name, recurse=recurse, rectype=rectype))
		return filter(None, [i.get(param) for i in parents])


	def macro_name(self, macro, params):
		return "Parent Value: %s"%params




class macro_first(Macro):
	"""Return the first value found from a list of params"""
	__metaclass__ = Macro.register_view
			
	def process(self, macro, params, rec):
		ret = None
		for param in params.split(","):
			ret = rec.get(params.strip())
			if ret != None:
				return ret

	def macro_name(self, macro, params):
		return " or ".join(params.split(","))


class macro_or(Macro):
	"""parentvalue macro"""
	__metaclass__ = Macro.register_view
			
	def process(self, macro, params, rec):
		ret = None
		for param in params.split(","):
			ret = rec.get(params.strip())
			if ret != None:
				return ret

	def macro_name(self, macro, params):
		return " or ".join(params.split(","))





# class macro_or(Macro):
# 	"""parentvalue macro"""
# 	__metaclass__ = Macro.register_view
# 			
# 	def process(self, macro, params, rec):
# 		params = params.split(",")
# 		return filter(None, [rec.get(i.strip()) for i in params])
# 
# 
# 	def macro_name(self, macro, params):
# 		return " or ".join(params.split(","))





import cgi
class macro_escape_paramdef_val(Macro):
	"""escape_paramdef_val macro"""
	__metaclass__ = Macro.register_view
		
	def process(self, macro, params, rec):
		return cgi.escape(rec.get(params, ''))


	def macro_name(self, macro, params):
		return "Escaped Value: %s"%params



class macro_renderchildren(Macro):
	"""renderchildren macro"""
	__metaclass__ = Macro.register_view
		
	def process(self, macro, params, rec):
		r = self.engine.db.renderview(self.engine.db.getchildren(rec.name), viewtype=params or "recname") #ian:mustfix

		hrefs = []
		for k,v in sorted(r.items(), key=operator.itemgetter(1)):
			l = """<li><a href="%s/record/%s">%s</a></li>"""%(g.EMEN2WEBROOT, k, v or k)
			hrefs.append(l)

		return "<ul>%s</ul>"%("\n".join(hrefs))


	def macro_name(self, macro, params):
		return "renderchildren"			



class macro_renderchild(Macro):
	"""renderchild macro"""
	__metaclass__ = Macro.register_view
	
		
	def process(self, macro, params, rec):
		#rinfo = dict(,host=host)
		#view, key, value = args.split(' ')
		#def get_records(name):
		#	return db.getindexbyvalue(key.encode('utf-8'), value, **rinfo).intersection(db.getchildren(name, **rinfo))
		#return render_records(db, rec, view, get_records,rinfo, html_join_func)
		return ""

		
	def macro_name(self, macro, params):
		return "renderchild"		



class macro_renderchildrenoftype(Macro):
	"""renderchildrenoftype macro"""
	__metaclass__ = Macro.register_view

		
	def process(self, macro, params, rec):
		# print macro, params
		r = self.engine.db.renderview(self.engine.db.getchildren(rec.name, rectype=params))

		hrefs = []
		for k,v in sorted(r.items(), key=operator.itemgetter(1)):
			l = """<li><a href="%s/record/%s">%s</a></li>"""%(g.EMEN2WEBROOT, k, v or k)
			hrefs.append(l)

		return "<ul>%s</ul>"%("\n".join(hrefs))

		
	def macro_name(self, macro, params):
		return "renderchildrenoftype"	




class macro_getfilenames(Macro):
	"""getfilenames macro"""
	__metaclass__ = Macro.register_view

		
	def process(self, macro, params, rec):
		# files = {}
		# if rec["file_binary"] or rec["file_binary_image"]:
		# 	bids = []
		# 	if rec["file_binary"]:
		# 		bids += rec["file_binary"]
		# 	if rec["file_binary_image"]:
		# 		bids += [rec["file_binary_image"]]
		#
		# 	for bid in bids:
		# 		bid = bid[4:]
		# 		try:
		# 			bname,ipath,bdocounter=db.getbinary(bid,,host=host)
		# 		except Exception, inst:
		# 			bname="Attachment error: %s"%bid
		# 		files[bid]=bname
		#
		# return files
		return ""

		
	def macro_name(self, macro, params):
		return "getfilenames"	




class macro_getrectypesiblings(Macro):
	"""getrectypesiblings macro"""
	__metaclass__ = Macro.register_view
		
	def process(self, macro, params, rec):
		pass
		# """returns siblings and cousins of same rectype"""
		# ret = {}
		# parents = db.getparents(rec.name,,host=host)
		# siblings = set()
		#
		# for i in parents:
		# 	siblings = siblings.union(db.getchildren(i))
		#
		# groups = db.groupbyrectype(siblings)
		#
		# if groups.has_key(rec.rectype):
		# 	q = db.getindexdictbyvaluefast(groups[rec.rectype],"modifytime")
		# 	ret = [i[0] for i in sorted(q.items(), key=itemgetter(1), reverse=True)] #BUG: What is supposed to happen here?
		#
		
	def macro_name(self, macro, params):
		return "getrectypesiblings"	
		
		
		
		



class macro_thumbnail(Macro):
	"""tile thumb macro"""
	__metaclass__ = Macro.register_view
	
		
	def process(self, macro, params, rec):

		format = "jpg"
		defaults = ["file_binary_image", "thumb", "jpg"]
		params = (params or '').split(",")

		for i,v in enumerate(params):
			if v:
				defaults[i]=v

		#print defaults
	
		bdos = rec.get(defaults[0])
		if not hasattr(bdos,"__iter__"):
			bdos = [bdos]

		return "".join(['<img src="%s/download/%s/%s.%s.%s?size=%s&amp;format=%s" alt="" />'%(
				g.EMEN2WEBROOT, bid, bid, defaults[1], defaults[2], defaults[1], defaults[2]) for bid in filter(lambda x:isinstance(x,basestring), bdos
				)])


	def macro_name(self, macro, params):
		return "Thumbnail Image"














__version__ = "$Revision$".split(":")[1][:-1].strip()
