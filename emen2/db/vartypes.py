# $Id$

import cgi
import operator
import collections
import urllib
import time, datetime
import htmlentitydefs
import re

try:
	import markdown2 as markdown
except ImportError:
	try:
		import markdown
	except ImportError:
		markdown = None


import emen2.db.datatypes
import emen2.db.config
import emen2.util.listops
g = emen2.db.config.g()


class Vartype(object):

	keytype = None
	iterable = False
	elem_class = 'editable'
	elem = 'span'

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls


	@classmethod
	def register(cls):
		name = cls.__name__
		if name.startswith('vt_'): name = name.split('_',1)[1]
		cls.vartype = property(lambda *_: name)
		emen2.db.datatypes.VartypeManager._register_vartype(name, cls)


	def __init__(self, engine=None, pd=None):
		self.pd = pd
		self.engine = engine


	def getvartype(self):
		return self.vartype


	def getkeytype(self):
		return self.keytype


	# This is the default HTML renderer for single-value items. It is important to cgi.escape the values!!
	def render(self, value, name=0, edit=False, showlabel=False, markup=False, table=False):
		# Store these for convenience
		self.name = name
		self.edit = edit
		self.showlabel = showlabel
		self.markup = markup
		self.table = table
		if self.pd.get('immutable'):
			self.edit = False

		# Process the value
		value = self.process(value)

		# Use the iterable renderer
		if self.iterable:
			return self._render_list(value)

		return self._render(value)


	def process(self, value, *args, **kwargs):
		if value == None:
			return ''
		return cgi.escape(unicode(value))


	# After pre-processing values into markup
	# The lt flag is used for table format, to link to the row's name
	def _render_list(self, value):
		# Note: value should already be escaped!

		label = ''

		# Plain text rendering
		if not self.markup:
			return ", ".join(value)

		# Empty
		if not value:
			if self.edit and self.showlabel:
				label = '<img src="%s/static/images/blank.png" class="label underline" alt="No value" />'%g.EMEN2WEBROOT
			if self.edit:
				return '<span class="%s" data-name="%s" data-param="%s">%s</span>'%(self.elem_class, self.name, self.pd.name, label)
			return '<span></span>'


		# Basic
		if self.table:
			lis = ['<li><a href="%s/record/%s">%s</a></li>'%(g.EMEN2WEBROOT, self.name, i) for i in value]
		else:
			lis = ['<li>%s</li>'%(i) for i in value]

		if not self.edit:
			return '<ul>%s</ul>'%("\n".join(lis))

		# Editable..
		# Are we showing the edit label?
		if self.showlabel:
			lis.append('<li class="nonlist"><span class="edit label"><img src="%s/static/images/edit.png" alt="Edit" /></span></li>'%g.EMEN2WEBROOT)

		# Put the editing widget together
		return '<ul class="%s" data-name="%s" data-param="%s" data-vartype="%s">%s</ul>'%(self.elem_class, self.name, self.pd.name, self.pd.vartype, "\n".join(lis))


	def _render(self, value):
		# Note: value should already be escaped!

		label = ''
		if value == None:
			value = ''

		# Plain text
		if not self.markup:
			if value and self.pd.defaultunits:
				return '%s %s'%(value, self.pd.defaultunits)
			return unicode(value)

		# Empty
		if not value:
			if self.edit and self.showlabel:
				label = '<img src="%s/static/images/blank.png" class="label underline" alt="No value" />'%g.EMEN2WEBROOT
			if self.edit:
				return '<%s class="%s" data-name="%s" data-param="%s">%s</%s>'%(self.elem, self.elem_class, self.name, self.pd.name, label, self.elem)
			return '<%s></%s>'%(self.elem, self.elem)


		if self.pd.defaultunits:
			value = '%s %s'%(value, self.pd.defaultunits)

		if self.table:
			value = '<a href="%s/record/%s/">%s</a>'%(g.EMEN2WEBROOT, self.name, value)

		if not self.edit:
			return value

		# Editable..
		# Are we showing the edit label?
		if self.showlabel:
			label = '<span class="edit label"><img src="%s/static/images/edit.png" alt="Edit" /></span>'%g.EMEN2WEBROOT

		# Put the editing widget together
		return '<%s class="%s" data-name="%s" data-param="%s" data-vartype="%s">%s%s</%s>'%(self.elem, self.elem_class, self.name, self.pd.name, self.pd.vartype, value, label, self.elem)



	def encode(self, value):
		return value


	def decode(self, pd, value):
		return value


	def validate(self, value):
		"""Validate a value"""
		return value


	def reindex(self, items):
		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)
		for name, new, old in items:
			if new == old:
				continue
			delrefs[old].add(name)
			addrefs[new].add(name)

		if None in addrefs: del addrefs[None]
		if None in delrefs: del delrefs[None]

		return addrefs, delrefs






class vt_iter(object):

	iterable = True

	def reindex(self, items):
		# items format: [name, newval, oldval]
		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)
		for name, new, old in items:
			if new == old:
				continue

			new = set(new or [])
			old = set(old or [])
			for n in new-old:
				addrefs[n].add(name)

			for o in old-new:
				delrefs[o].add(name)

		if None in addrefs: del addrefs[None]
		if None in delrefs: del delrefs[None]

		return addrefs, delrefs






###################################
# None
###################################

class vt_none(Vartype):
	"""Organizational vartype that cannot be used"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		raise ValueError, "This is an organizational parameter not designed for use."


	def process(self, value):
		if value == None:
			return ''
		return "%g"%value



###################################
# Float vartypes
###################################

class vt_float(Vartype):
	"""single-precision floating-point"""
	__metaclass__ = Vartype.register_view
	keytype = "f"

	def validate(self, value):
		return float(value)


	def process(self, value):
		if value == None:
			return ''
		return "%g"%value



# class vt_longfloat(vt_float):
# 	"""double-precision floating-point"""
# 	__metaclass__ = Vartype.register_view

class vt_percent(Vartype):
	"""Percentage; floating point 0 <= x <= 1"""
	__metaclass__ = Vartype.register_view
	keytype = "f"
	def validate(self, value):
		value = float(value)
		if not 0 <= value <= 1.0:
			raise ValueError, "Percentage stored as 0 <= value <= 1.0"
		return value

	def process(self, value):
		if value == None:
			return ''
		return "%0.0f"%(value*100.0)



class vt_floatlist(vt_iter, vt_float):
	"""list of floats"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		return [float(x) for x in value] or None

	def process(self, value):
		if value == None:
			return ''
		return ["%g"%i for i in value]



###################################
# Integer vartypes
###################################

class vt_int(Vartype):
	"""32-bit integer"""
	__metaclass__ = Vartype.register_view
	keytype = "d"

	def validate(self, value):
		return int(value)



# class vt_longint(vt_int):
# 	"""64-bit integer"""
# 	__metaclass__ = Vartype.register_view



class vt_intlist(vt_iter, vt_int):
	"""list of ints"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		return [int(x) for x in value] or None



class vt_intlistlist(Vartype):
	"""list of int tuples: e.g. [[1,2],[3,4], ..]"""
	__metaclass__ = Vartype.register_view

	iterable = True
	keytype = None

	def validate(self, value):
		return [[int(x) for x in i] for i in value] or None



class vt_boolean(vt_int):
	"""boolean"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		try:
			return bool(int(value))
		except ValueError:
			if unicode(value).lower() in ("t","y","true"):
				return True
			if unicode(value).lower() in ("f","n","false"):
				return False
			raise ValueError, "Invalid boolean: %s"%unicode(value)



# ian: todo: rename to vt_name
class vt_recid(Vartype):
	__metaclass__ = Vartype.register_view
	keytype = None
	def validate(self, value):
		try:
			value = int(value)
			if value < 0:
				raise ValueError
		except ValueError:
			raise ValueError, "Invalid name: %s"%value
		return value


class vt_name(Vartype):
	__metaclass__ = Vartype.register_view
	keytype = None
	def validate(self, value):
		try:
			value = int(value)
		except ValueError:
			value = unicode(value or '')
		return value



###################################
# String vartypes
###################################

class vt_string(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		return unicode(value).strip() or None


# ian: todo: validate choices!
class vt_choice(vt_string):
	"""string from a fixed enumerated list, eg "yes","no","maybe"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = unicode(value).strip()
		if value not in self.pd.choices:
			raise ValueError, "Choice not in defined options: %s"%value
		return value or None



# ian: todo: validate rectype
class vt_rectype(vt_string):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = unicode(value).strip()
		check_rectypes(self.engine, [value])
		return value or None



class vt_stringlist(vt_iter, vt_string):
	"""list of strings"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		return [unicode(x).strip() for x in value] or None


	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		if self.markup:
			value = [cgi.escape(i) for i in value]
		return value



class vt_choicelist(vt_iter, vt_string):
	"""list of choice strings"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		value = [unicode(i).strip() for i in value]
		for v in value:
			if v not in self.pd.choices:
				raise ValueError, "Choice not in defined options: %s"%v
		return value or None


	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		if self.markup:
			value = [cgi.escape(i) for i in value]
		return value



class vt_text(vt_string):
	"""freeform text, fulltext (word) indexing, str or unicode"""

	__metaclass__ = Vartype.register_view
	elem = 'div'

	def reindex(self, items):
		"""(Internal) calculate param index updates for vartype == text"""

		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)
		for item in items:
			if item[1]==item[2]:
				continue

			for i in self._reindex_getindexwords(item[1]):
				addrefs[i].append(item[0])

			for i in self._reindex_getindexwords(item[2]):
				delrefs[i].append(item[0])

		allwords = set(addrefs.keys() + delrefs.keys()) - set(g.UNINDEXED_WORDS)
		addrefs2 = {}
		delrefs2 = {}

		for i in allwords:
			# make set, remove unchanged items
			addrefs2[i] = set(addrefs.get(i,[]))
			delrefs2[i] = set(delrefs.get(i,[]))
			u = addrefs2[i] & delrefs2[i]
			addrefs2[i] -= u
			delrefs2[i] -= u

		return addrefs2, delrefs2


	_reindex_getindexwords_m = re.compile('([a-zA-Z]+)|([0-9][.0-9]+)')
	def _reindex_getindexwords(self, value, ctx=None, txn=None):
		"""(Internal) Split up a text param into components"""
		if value == None: return []
		value = unicode(value).lower()
		return set((x[0] or x[1]) for x in self._reindex_getindexwords_m.findall(value))


	def process(self, value):
		if value == None:
			return ''
		if self.markup:
			value = cgi.escape(value)
			if markdown:
				value = markdown.markdown(value)
		return value




###################################
# Time vartypes (keytype is string)
###################################

# ian: todo: high priority: see fixes in parse_datetime, extend to other date validators
class vt_datetime(vt_string):
	"""date/time, yyyy/mm/dd HH:MM:SS"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		return unicode(parse_datetime(value)[1]).strip() or None



class vt_time(vt_datetime):
	"""time, HH:MM:SS"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		parse_time(value)
		return unicode(value).strip() or None



class vt_date(vt_datetime):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		parse_date(value)
		return unicode(value).strip() or None


### Extended date vartypes

class vt_duration(vt_datetime):
	"""TimeStart, OR, TimeStart-TimeStop"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		parse_date(value)
		return unicode(value).strip() or None


class vt_recurring(vt_datetime):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		d = {}
		# Manually specified times
		d['datetimes']
		d['dates']
		
		# These times of day
		d['times']
		# ... or these intervals
		d['durations']

		# Repeat days
		# Default: every day
		# Repeat These days of the week....
		# Sun 0
		# Mon 1
		# Tue 2
		# Wed 3
		# Thu 4
		# Fri 5
		# Sat 6
		d['days_week']
		# ... or 'first monday', 'last friday'. List of days, -7 to 35.
		# e.g. 	second tuesday = 9, divmod(9,7) = (1,2)
		# 		third sunday = 21, divmod(21,7) = (3,0)
		#		last friday = -2, divmod(-2,7) = (-1,5)
		d['days_week_month']
		# ... or list of days each month, -31 to 31
		d['days_month']

		# ... repeat these months of the year, 0-11
		# 	Default: all months
		d['months']

		# datetime stamps to start/end
		d['start']
		d['end']

		return d




###################################
# Reference vartypes (uri, binary, hdf, etc.).
###################################

class vt_ref(Vartype):
	keytype = "s"



class vt_uri(vt_ref):
	"""link to a generic uri"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = unicode(value).strip()
		if not value.startswith("http://"):
			raise ValueError, "Invalid URI: %s"%value
		return value


	def process(self, value):
		if value == None:
			return ''
		if self.markup:
			value = cgi.escape(unicode(value))
			if not self.table:
				value = '<a href="%s">%s</a>'%(value,value)
		return value



class vt_urilist(vt_iter, vt_ref):
	"""list of uris"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		value = [unicode(i).strip() for i in value]
		for v in value:
			if not v.startswith("http://"):
				raise ValueError, "Invalid URI: %s"%value
		return value
		# return [unicode(x) for x in value if x.startswith('http://')] or None


	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		if self.markup:
			value = [cgi.escape(i) for i in value]
			if not self.table:
				value = ['<a href="%s">%s</a>'%(i,i) for i in value]
		return value




###################################
# Mapping types
###################################


# all = set(['displayname', 'groups', 'views', 'mainview', 'creationtime', 'typicalchld', 'compress', 'private', 'disabled', 'rectype', 'signupinfo', 'vartype', 'userrec', 'modifytime', 'filename', 'children', 'desc_short', 'name', 'modifyuser', 'desc_long', 'privacy', 'filepath', 'uri', 'comments', 'choices', 'defaultunits', 'record', 'name', 'filesize', 'indexed', 'parents', 'permissions', 'property', 'creator', 'immutable', 'md5', 'history'])

# displayname: string
# groups: groups
# views: dict
# mainview: string
# creationtime: datetime
# typicalchld: rectypelist
# compress: bool
# private: bool
# disabled: int
# rectype: rectype
# signupinfo: paramdict
# vartype: vartype
# userrec: None
# modifytime: datetime
# filename: filename
# children: links
# desc_short: string
# name: None, but immutable..
# modifyuser: user
# desc_long: text
# privacy: int
# filepath: None, immutable
# uri: uri
# comments: comments
# choices: stringlist
# defaultunits: string... check property for choices?
# record: name
# filesize: int
# indexed: bool
# parents: links
# property: string... check properties?
# creator: user
# immutable: bool
# md5: md5
# history: history

# So, new vartypes: dict, rectypelist, paramdict, unvalidated, filename, units (check Magnitude and property), md5 (length == 40, or maybe unvalidated)

class vt_paramdict(vt_iter, Vartype):
	"""Dictionary with valid param keys"""
	__metaclass__ = Vartype.register_view
	def validate(self, value):
		ret = {}
		for k,v in value.items():
			pd = check_rectype(self.engine, k)
			# will this work?
			v = self.engine.validate(pd, v)
			ret[pd.name] = v
		return ret



class vt_dict(vt_iter, Vartype):
	"""Dictionary with valid param keys"""
	__metaclass__ = Vartype.register_view
	def validate(self, value):
		ret = {}
		for k,v in value.items():
			ret[unicode(k)] = v
		return ret






###################################
# Binary vartypes
###################################

# ian: todo: strict validation; these can actually take any arbitrary string

class vt_binary(vt_iter, Vartype):
	"""BDO reference"""
	__metaclass__ = Vartype.register_view
	keytype = None
	elem_class = "editable_files"

	def validate(self, value):
		return value
		value = emen2.util.listops.check_iterable(value)
		value = [i.name for i in self.engine.db.getbinary(value, filt=False)]
		return value or None


	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		if not self.markup:
			return value

		try:
			v = self.engine.db.getbinary(value)
			if self.table:
				value = ['%s'%(cgi.escape(i.filename)) for i in v]
			else:
				value = ['<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename)) for i in v]

		except (ValueError, TypeError):
			value = ['Error getting binary %s'%i for i in value]

		return value



class vt_binaryimage(Vartype):
	"""non browser-compatible image requiring extra 'help' to display... 'bdo:....'"""
	__metaclass__ = Vartype.register_view
	keytype = None
	elem_class = "editable_files"

	def validate(self, value):
		return value
		value = self.engine.db.getbinary(value, filt=False)
		if value:
			return value.name
		return None


	def process(self, value):
		if not self.markup:
			return value

		if not value:
			return ''

		try:
			i = self.engine.db.getbinary(value)
			if self.table:
				value = '%s'%cgi.escape(i.filename)
			else:
				value = '<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename))

		except (ValueError, TypeError):
			value = "Error getting binary %s"%value

		return value




class vt_hdf(vt_binary):
	"""BDO or URI points to an HDF file"""
	__metaclass__ = Vartype.register_view
	keytype = None



class vt_image(vt_binary):
	"""BDO or URI points to a browser-compatible image"""
	__metaclass__ = Vartype.register_view
	keytype = None






###################################
# Internal record-record linkes
###################################

class vt_links(vt_iter, Vartype):
	"""references to other records; can be parent/child/cousin/etc."""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		return [int(x) for x in value] or None





# dict -- I don't think this is used anywhere.

# class vt_dict(Vartype):
# 	"""dict"""
# 	__metaclass__ = Vartype.register_view
# 	keytype = None
#
# 	def validate(self, engine, pd, value, db):
# 		return dict(value) or None




###################################
# User vartypes
###################################

class vt_user(Vartype):
	"""user, by username"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		value = unicode(value).strip()
		check_usernames(self.engine, [value])
		return value or None


	# ian: todo: make these nice .userboxes ?
	def process(self, value):
		if value == None:
			return ''

		update_username_cache(self.engine, [value])
		hit, dn = self.engine.check_cache(self.engine.get_cache_key('displayname', value))
		if not hit:
			return ''

		dn = cgi.escape(dn)
		if self.table or not self.markup:
			value = dn
		else:
			value = '<a href="%s/user/%s/">%s</a>'%(g.EMEN2WEBROOT, value, dn)

		return value



class vt_userlist(vt_iter, Vartype):
	"""list of usernames"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		check_usernames(self.engine, value)
		return [unicode(x).strip() for x in value] or None



	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		update_username_cache(self.engine, value)

		lis = []
		for i in value:
			key = self.engine.get_cache_key('displayname', i)
			hit, dn = self.engine.check_cache(key)
			dn = cgi.escape(dn)
			if self.table or not self.markup:
				lis.append(dn)
			else:
				lis.append('<a href="%s/user/%s">%s</a>'%(g.EMEN2WEBROOT, i, dn))

		return lis




# ian: todo: change to be more like vt_userlist
class vt_acl(Vartype):
	"""Permissions access control list; nested lists of users"""
	__metaclass__ = Vartype.register_view
	keytype = "s"
	iterable = True

	def validate(self, value):
		if not hasattr(value, '__iter__'):
			value = [[value],[],[],[]]

		for i in value:
			if not hasattr(i, '__iter__'):
				raise ValueError, "Invalid permissions format: ", value

		value = [[unicode(y) for y in x] for x in value]
		if len(value) != 4:
			raise ValueError, "Invalid permissions format: ", value

		users = reduce(lambda x,y:x+y, value)
		check_usernames(self.engine, users)
		return value


	def process(self, value):
		if not value:
			return []

		value = reduce(lambda x,y:x+y, value)
		unames = {}

		for user in self.engine.db.getuser(value):
			user.getdisplayname(lnf=True)
			unames[user.name] = user.displayname

		levels=["Read","Comment","Write","Admin"]
		ret=[]

		for level,names in enumerate(value):
			namesr = [unames.get(i,"(%s)"%i) for i in names]
			ret.append("%s: %s"%(levels[level],", ".join(namesr)))

		return ret



	def reindex(self, items):
		"""(Internal) Calculate secrindex updates"""

		# Calculating security updates...
		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)
		for name, new, old in items:

			#nperms = set(reduce(operator.concat, new or [], []))
			#operms = set(reduce(operator.concat, old or [], []))
			nperms = set()
			for i in new or []:
				nperms |= set(i)
			operms = set()
			for i in old or []:
				operms |= set(i)

			for user in nperms - operms:
				addrefs[user].append(name)

			for user in operms - nperms:
				delrefs[user].append(name)

		return addrefs, delrefs



class vt_comments(Vartype):
	"""Comments"""
	__metaclass__ = Vartype.register_view
	keytype = None
	iterable = True

	# ian: todo... sort this out.
	def validate(self, value):
		return value
		# print "validating comments"
		# print value
		# if value:
		# 	users = [i[0] for i in value]
		# 	times = [i[1] for i in value]
		# 	values = [i[2] for i in value]
		# 	check_usernames(self.engine, users)
		# 	return [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in value]



	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		users = [i[0] for i in value]
		update_username_cache(self.engine, users)

		lis = []
		for user, time, comment in value:
			key = self.engine.get_cache_key('displayname', user)
			hit, dn = self.engine.check_cache(key)
			dn = cgi.escape(dn)
			comment = cgi.escape(comment)
			if self.table or not self.markup:
				t = '%s @ %s: %s'%(user, time, comment)
			else:
				t = '<h4><a href="%s/user/%s">%s</a> @ %s</h4>%s'%(g.EMEN2WEBROOT, user, dn, time, comment)

			lis.append(t)

		return lis




class vt_history(Vartype):
	"""history"""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, value):
		users = [i[0] for i in value]
		times = [i[1] for i in value]
		check_usernames(self.engine, users)
		return [(unicode(i[0]), unicode(i[1]), unicode(i[2]), i[3]) for i in value]


	def process(self, value):
		value = emen2.util.listops.check_iterable(value)
		return [unicode(i) for i in value]




class vt_groups(vt_iter, Vartype):
	"""groups"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		value = emen2.util.listops.check_iterable(value)
		check_groupnames(self.engine, value)
		return set([unicode(i).strip() for i in value]) or None


	def process(self, engine, pd, value, rec, db):
		value = emen2.util.listops.check_iterable(value)
		return [unicode(i) for i in value]







###########################
# Helper methods

def check_rectype(engine, value):
	key = engine.get_cache_key('paramdef', value)
	hit, paramdef = engine.check_cache(key)
	if not hit:
		paramdef = engine.db.getparamdef(value, filt=False)
		engine.store(key, paramdef)

	return paramdef



def check_rectypes(engine, values):
	key = engine.get_cache_key('paramdefnames')
	hit, paramdefs = engine.check_cache(key)
	if not hit:
		paramdefs = engine.db.getparamdefnames()
		engine.store(key, paramdefs)

	if set(values) - paramdefs:
		raise ValueError, "Unknown ParamDefs: %s"%(", ".join(set(values)-paramdefs))



def check_rectypes(engine, values):
	key = engine.get_cache_key('recorddefnames')
	hit, rectypes = engine.check_cache(key)
	if not hit:
		rectypes = engine.db.getrecorddefnames()
		engine.store(key, rectypes)

	if set(values) - rectypes:
		raise ValueError, "Unknown RecordDefs: %s"%(", ".join(set(values)-rectypes))



def check_usernames(engine, values):
	key = engine.get_cache_key('usernames')
	hit, usernames = engine.check_cache(key)
	if not hit:
		usernames = engine.db.getusernames()
		engine.store(key, usernames)

	if set(values) - usernames:
		raise ValueError, "Unknown users: %s"%(", ".join(set(values)-usernames))



def check_groupnames(engine, values):
	key = engine.get_cache_key('groupnames')
	hit, groupnames = engine.check_cache(key)
	if not hit:
		groupnames = engine.db.getgroupnames()
		engine.store(key, groupnames)

	if set(values) - groupnames:
		raise ValueError, "Unknown groups: %s"%(", ".join(set(values)-groupnames))



def update_username_cache(engine, values):
	# Check cache
	to_cache = []
	for v in values:
		key = engine.get_cache_key('displayname', v)
		hit, dn = engine.check_cache(key)
		if not hit:
			to_cache.append(v)

	if to_cache:
		users = engine.db.getuser(to_cache, filt=True)
		for user in users:
			user.getdisplayname(lnf=True)
			key = engine.get_cache_key('displayname', user.name)
			engine.store(key, user.displayname)





"""Following based on public domain code by Paul Harrison, 2006; modified by Ian"""

time_formats = [
	'%H:%M:%S',
	'%H:%M',
	'%H'
	]

date_formats = [
	'%Y %m %d',
	'%Y %m',
	'%Y'
	]

# Foramts to check [0] and return [1] in order of priority
# (the return value will be used for the internal database value for consistency)
# The DB will return the first format that validates.

datetime_formats = [
	['%Y %m %d %H:%M:%S','%Y/%m/%d %H:%M:%S'],
	['%Y %m %d %H:%M','%Y/%m/%d %H:%M'],
	['%Y %m %d %H', '%Y/%m/%d %H'],
	['%Y %m %d', '%Y/%m/%d'],
	['%Y %m','%Y/%m'],
	['%Y','%Y'],
	['%m %Y','%Y/%m'],
	['%d %m %Y','%Y/%m/%d'],
	['%d %m %Y %H:%M:%S','%Y/%m/%d %H:%M:%S'],
	['%m %d %Y','%Y/%m/%d'],
	['%m %d %Y %H:%M:%S','%Y/%m/%d %H:%M:%S']
	]



def parse_datetime(string):
	"""Return a tuple: datetime instance, and validated output"""
	string = string.strip()
	if not string:
		return None, None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ').split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format, output in datetime_formats:
		try:
			string = datetime.datetime.strptime(string, format)
			return string, datetime.datetime.strftime(string, output)
		except ValueError, inst:
			pass

	raise ValueError()



def parse_time(string):
	string = string.strip()

	string = string.split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format in time_formats:
		try:
			return string, datetime.datetime.strptime(string, format).time()
		except ValueError, inst:
			pass

	raise ValueError()



def parse_date(string):
	string = string.strip()
	if not string: return None, None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ')

	for format in date_formats:
		try:
			return string, datetime.datetime.strptime(string, format).date()
		except ValueError:
			pass

	raise ValueError()



__version__ = "$Revision$".split(":")[1][:-1].strip()
