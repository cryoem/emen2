# $Id$

import operator
import cgi

import emen2.db.datatypes
import emen2.db.config
g = emen2.db.config.g()

# Convenience
ci = emen2.util.listops.check_iterable
ValidationError = emen2.db.exceptions.ValidationError
vtm = emen2.db.datatypes.VartypeManager


class Macro(object):

	keytype = 's'

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




@vtm.register_macro('name')
class macro_name(Macro):
	"""name macro"""
	keytype = 'd'

	def process(self, macro, params, rec):
		return rec.name
		

	def macro_name(self, macro, params):
		return "Record Name"


# legacy..
@vtm.register_macro('recid')
class macro_recid(Macro):
	"""name macro"""
	keytype = 'd'

	def process(self, macro, params, rec):
		return rec.name


	def macro_name(self, macro, params):
		return "Record Name"



@vtm.register_macro('parents')
class macro_parents(Macro):
			
	def process(self, macro, params, rec):
		rectype, _, recurse = params.partition(",")
		recurse = int(recurse or 1)
		return self.engine.db.getparents(rec.name, rectype=rectype, recurse=recurse)
		

	def macro_name(self, macro, params):
		return "Parents: %s"%params				
				


@vtm.register_macro('recname')
class macro_recname(Macro):
	"""recname macro"""
			
	def process(self, macro, params, rec):
		return self.engine.db.renderview(rec) #vtm=self.engine


	def macro_name(self, macro, params):
		return "Record ID"				
				

@vtm.register_macro('childcount')
class macro_childcount(Macro):
	"""childcount macro"""
	keytype = 'd'
	
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



@vtm.register_macro('img')
class macro_img(Macro):
	"""image macro"""

	def process(self, macro, params, rec):
		default = ["file_binary_image","640","640"]
		ps = params.split(",")
		for i,v in list(enumerate(ps))[:3]:
			default[i] = v
			
		param, width, height = default

		pd = self.engine.db.getparamdef(param)

		if pd.vartype=="binary":
			if pd.iter:
				bdos = rec[param]
			else:
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



@vtm.register_macro('childvalue')
class macro_childvalue(Macro):
	"""childvalue macro"""

	def process(self, macro, params, rec):
		name = rec.name
		children = self.engine.db.getrecord(self.engine.db.getchildren(name))
		return [i.get(params) for i in children]


	def macro_name(self, macro, params):
		return "Child Value: %s"%params



@vtm.register_macro('parentvalue')
class macro_parentvalue(Macro):
	"""parentvalue macro"""
		
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



@vtm.register_macro('first')
class macro_first(Macro):
	"""Return the first value found from a list of params"""
			
	def process(self, macro, params, rec):
		ret = None
		for param in params.split(","):
			ret = rec.get(params.strip())
			if ret != None:
				return ret

	def macro_name(self, macro, params):
		return " or ".join(params.split(","))


@vtm.register_macro('or')
class macro_or(Macro):
	"""parentvalue macro"""
			
	def process(self, macro, params, rec):
		ret = None
		for param in params.split(","):
			ret = rec.get(params.strip())
			if ret != None:
				return ret

	def macro_name(self, macro, params):
		return " or ".join(params.split(","))



@vtm.register_macro('escape_paramdef_val')
class macro_escape_paramdef_val(Macro):
	"""escape_paramdef_val macro"""
		
	def process(self, macro, params, rec):
		return cgi.escape(rec.get(params, ''))


	def macro_name(self, macro, params):
		return "Escaped Value: %s"%params


@vtm.register_macro('renderchildren')
class macro_renderchildren(Macro):
	"""renderchildren macro"""
		
	def process(self, macro, params, rec):
		r = self.engine.db.renderview(self.engine.db.getchildren(rec.name), viewtype=params or "recname") #ian:mustfix

		hrefs = []
		for k,v in sorted(r.items(), key=operator.itemgetter(1)):
			l = """<li><a href="%s/record/%s">%s</a></li>"""%(g.EMEN2WEBROOT, k, v or k)
			hrefs.append(l)

		return "<ul>%s</ul>"%("\n".join(hrefs))


	def macro_name(self, macro, params):
		return "renderchildren"			



@vtm.register_macro('renderchild')
class macro_renderchild(Macro):
	"""renderchild macro"""
		
	def process(self, macro, params, rec):
		#rinfo = dict(,host=host)
		#view, key, value = args.split(' ')
		#def get_records(name):
		#	return db.getindexbyvalue(key.encode('utf-8'), value, **rinfo).intersection(db.getchildren(name, **rinfo))
		#return render_records(db, rec, view, get_records,rinfo, html_join_func)
		return ""

		
	def macro_name(self, macro, params):
		return "renderchild"		



@vtm.register_macro('renderchildrenoftype')
class macro_renderchildrenoftype(Macro):
	"""renderchildrenoftype macro"""

		
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



@vtm.register_macro('getfilenames')
class macro_getfilenames(Macro):
	"""getfilenames macro"""
		
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



@vtm.register_macro('getrectypesiblings')
class macro_getrectypesiblings(Macro):
	"""getrectypesiblings macro"""
		
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
		
	def macro_name(self, macro, params):
		return "getrectypesiblings"	
		
		

@vtm.register_macro('thumbnail')
class macro_thumbnail(Macro):
	"""tile thumb macro"""
	
	def process(self, macro, params, rec):

		format = "jpg"
		defaults = ["file_binary_image", "thumb", "jpg"]
		params = (params or '').split(",")

		for i,v in enumerate(params):
			if v:
				defaults[i]=v
	
		bdos = rec.get(defaults[0])
		if not hasattr(bdos,"__iter__"):
			bdos = [bdos]

		return "".join(['<img src="%s/download/%s/%s.%s.%s?size=%s&amp;format=%s" alt="" />'%(
				g.EMEN2WEBROOT, bid, bid, defaults[1], defaults[2], defaults[1], defaults[2]) for bid in filter(lambda x:isinstance(x,basestring), bdos
				)])


	def macro_name(self, macro, params):
		return "Thumbnail Image"






# Editing macros
@vtm.register_macro('checkbox')
class macro_checkbox(Macro):
	"""draw a checkbox for editing values"""
		
	def process(self, macro, params, rec):
		print "Checkbox params:", macro, params
		return "Checkbox!"

	def macro_name(self, macro, params):
		return "Checkbox:", params			




__version__ = "$Revision$".split(":")[1][:-1].strip()
