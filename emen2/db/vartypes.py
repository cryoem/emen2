# $Id$

import cgi
import operator
import collections
import urllib
import time
import datetime
import dateutil
import dateutil.rrule
import calendar
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
import emen2.db.exceptions
g = emen2.db.config.g()

# Convenience
ci = emen2.util.listops.check_iterable
ValidationError = emen2.db.exceptions.ValidationError


class Vartype(object):

	keytype = None
	iterable = True
	elem_class = 'editable'
	elem = 'span'

	@staticmethod
	def register_view(name, bases, dict):
		cls = type(name, bases, dict)
		cls.register()
		return cls

	@classmethod
	def register_new(cls):
		print "Registering vartype:", cls
		pass
	
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


	def process(self, value, *args, **kwargs):
		return [cgi.escape(unicode(i)) for i in value]


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

		value = self.process(ci(value))
		return self._render(value)


	# After pre-processing values into markup
	# The lt flag is used for table format, to link to the row's name
	def _render(self, value):
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


	def encode(self, value):
		return value


	def decode(self, pd, value):
		return value


	def validate(self, value):
		"""Validate a value"""
		return value

	
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

@Vartype.register_new('none')
class vt_none(Vartype):
	"""Organizational vartype that cannot be used"""

	def validate(self, value):
		raise ValidationError, "This is an organizational parameter, and is not intended to be used."



###################################
# Float vartypes
###################################

@Vartype.register_new('float')
class vt_float(Vartype):
	"""Floating-point number"""

	def validate(self, value):
		return map(float, ci(value)) or None

	def process(self, value):
		return ['%g'%i for i in value] or ''


@Vartype.register_new('percent')
class vt_percent(Vartype):
	"""Percentage. 0 <= x <= 1"""
	keytype = "f"
	
	def validate(self, value):
		value = map(float, ci(value))
		for i in value:
			if not 0 <= i <= 1.0:
				raise ValidationError, "Range for percentage is 0 <= value <= 1.0; value was: %s"%i
		return value

	def process(self, value):
		return ['%0.0f'%(i*100.0) for i in value]



###################################
# Integer vartypes
###################################

@Vartype.register_new('int')
class vt_int(Vartype):
	"""Integer"""

	def validate(self, value):
		return map(int, ci(value))


@Vartype.register_new('coordinate')
class vt_coordinate(Vartype):
	"""Coordinates; tuples of floats."""
	keytype = None

	def validate(self, value):
		return [[float(x) for x in i] for i in ci(value)]


@Vartype.register_new('boolean')
class vt_boolean(vt_int):
	"""Boolean value. Accepts 0/1, True/False, T/F, Yes/No, Y/N, None."""

	def validate(self, value):
		t = ['t', 'y', 'yes', 'true', '1']
		f = ['f', 'n', 'no', 'false', 'none', '0']
		ret = []
		for i in ci(value):
			i = unicode(value).lower()
			if i in t:
				i = True
			elif i in f:
				i = False
			else:
				raise ValidationError, "Invalid boolean: %s"%unicode(value)
			ret.append(i)
		return ret


# ian: deprecated
@Vartype.register_new('recid')
class vt_recid(Vartype):
	"""Record name"""
	keytype = None	

	def validate(self, value):
		value = map(int, ci(value))
		for i in value:
			if i < 0:
				raise ValidationError, "Invalid Record name: %s"%value
		return value


@Vartype.register_new('name')
class vt_name(Vartype):
	"""Database object name"""
	keytype = None

	def validate(self, value):
		ret = []
		for i in ci(value):
			try:
				i = int(value)
			except ValueError:
				i = unicode(value or '')
			ret.append(i)
		return ret



###################################
# String vartypes
###################################

@Vartype.register_new('string')
class vt_string(Vartype):
	"""String"""

	def validate(self, value):
		return [unicode(x).strip() for x in ci(value)]

	def process(self, value):
		if self.markup:
			return [cgi.escape(i) for i in value]
		return value


@Vartype.register_new('choice')
class vt_choice(vt_string):
	"""One value from a defined list of choices"""
	
	def validate(self, value):
		value = [unicode(i).strip() for i in ci(value)]
		for v in value:
			if v not in self.pd.choices:
				raise ValidationError, "Invalid choice: %s"%v
		return value


@Vartype.register_new('rectype')
class vt_rectype(vt_string):
	"""RecordDef name"""

	def validate(self, value):
		value = [unicode(x).strip() for x in ci(value)]
		check_rectypes(self.engine, value)
		return value


@Vartype.register_new('text')
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


### iCalendar-like date types

class vt_duration(Vartype):
	"""TimeStart, OR, TimeStart-TimeStop"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		parse_date(value)
		return unicode(value).strip() or None


class vt_recurrence(Vartype):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view

	def validate(self, value):
		return unicode(value)

		
###################################
# Reference vartypes (uri, binary, hdf, etc.).
###################################

class vt_uri(Vartype):
	"""list of uris"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		value = ci(value)
		value = [unicode(i).strip() for i in value]
		for v in value:
			if not v.startswith("http://"):
				raise ValidationError, "Invalid URI: %s"%value
		return value
		# return [unicode(x) for x in value if x.startswith('http://')] or None


	def process(self, value):
		value = ci(value)
		if self.markup:
			value = [cgi.escape(i) for i in value]
			if not self.table:
				value = ['<a href="%s">%s</a>'%(i,i) for i in value]
		return value




###################################
# Mapping types
###################################

class vt_paramdict(Vartype):
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


class vt_dict(Vartype):
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

class vt_binary(Vartype):
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




###################################
# Internal record-record linkes
###################################

class vt_links(Vartype):
	"""references to other records; can be parent/child/cousin/etc."""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, value):
		value = ci(value)
		return [int(x) for x in value] or None



###################################
# User vartypes
###################################

class vt_user(Vartype):
	"""list of usernames"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, value):
		value = ci(value)
		check_usernames(self.engine, value)
		return [unicode(x).strip() for x in value] or None

	def process(self, value):
		value = ci(value)
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

	def validate(self, value):
		if not hasattr(value, '__iter__'):
			value = [[value],[],[],[]]

		for i in value:
			if not hasattr(i, '__iter__'):
				raise ValidationError, "Invalid permissions format: ", value

		value = [[unicode(y) for y in x] for x in value]
		if len(value) != 4:
			raise ValidationError, "Invalid permissions format: ", value

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

	# ian: todo... sort this out.
	def validate(self, value):
		return value

	def process(self, value):
		value = ci(value)
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
	"""History"""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, value):
		users = [i[0] for i in value]
		times = [i[1] for i in value]
		check_usernames(self.engine, users)
		return [(unicode(i[0]), unicode(i[1]), unicode(i[2]), i[3]) for i in value]


	def process(self, value):
		value = ci(value)
		return [unicode(i) for i in value]


class vt_groups(Vartype):
	"""Groups"""
	__metaclass__ = Vartype.register_view
	keytype = 's'

	def validate(self, value):
		value = ci(value)
		check_groupnames(self.engine, value)
		return set([unicode(i).strip() for i in value]) or None


	def process(self, engine, pd, value, rec, db):
		value = ci(value)
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
	key = engine.get_cache_key('recorddefnames')
	hit, rectypes = engine.check_cache(key)
	if not hit:
		rectypes = engine.db.getrecorddefnames()
		engine.store(key, rectypes)

	if set(values) - rectypes:
		raise ValidationError, "Unknown protocols: %s"%(", ".join(set(values)-rectypes))


def check_usernames(engine, values):
	key = engine.get_cache_key('usernames')
	hit, usernames = engine.check_cache(key)
	if not hit:
		usernames = engine.db.getusernames()
		engine.store(key, usernames)

	if set(values) - usernames:
		raise ValidationError, "Unknown users: %s"%(", ".join(set(values)-usernames))


def check_groupnames(engine, values):
	key = engine.get_cache_key('groupnames')
	hit, groupnames = engine.check_cache(key)
	if not hit:
		groupnames = engine.db.getgroupnames()
		engine.store(key, groupnames)

	if set(values) - groupnames:
		raise ValidationError, "Unknown groups: %s"%(", ".join(set(values)-groupnames))


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
	string = (string or '').strip()
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

	raise ValidationError()



def parse_time(string):
	string = string.strip().split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format in time_formats:
		try:
			return datetime.datetime.strptime(string, format).time(), string
		except ValueError, inst:
			pass

	raise ValidationError()


def parse_date(string):
	string = string.strip()
	if not string: return None, None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ')

	for format in date_formats:
		try:
			return datetime.datetime.strptime(string, format).date(), string
		except ValueError:
			pass
	raise ValidationError()


def parse_iso8601(d):
	"""Simple ISO 8601 Format parser"""
	# [YYYY][MM][DD]T[hh][mm]
	# 2007-03-01T13:00:00Z
	def strip(i):
		return i.replace('-','').replace(':','').replace(' ','')

	dd, _, dt = d.partition('T')	
	tz = ''
	for sep in ['Z', '-', '+']:
		if sep in dt:
			dt, _, tz = dt.partition(sep)
			tz = '%s%s'%(sep,tz)

	dd = strip(dd)
	dt = strip(dt)

	r = {}
	r['year'] = dd[0:4]
	r['month'] = dd[4:6]
	r['day'] = dd[6:8]

	r['hour'] = dt[0:2]
	r['minute'] = dt[2:4]
	r['second'] = dt[4:6]

	r2 = {}
	r2['tz'] = tz
	keys = ['year','month','day', 'hour','minute','second']
	for key in keys:
		if r.get(key):
			r2[key] = int(r.get(key))
	return r2
	
	
def parse_iso8601duration(d):
	"""
	Parse ISO 8601 duration format.
	
	From Wikipedia, ISO 8601 duration format is:
		P[n]Y[n]M[n]DT[n]H[n]M[n]S
	
	P is the duration designator (historically called "period") placed at the start of the duration representation.
	Y is the year designator that follows the value for the number of years.
	M is the month designator that follows the value for the number of months.
	W is the week designator that follows the value for the number of weeks.
	D is the day designator that follows the value for the number of days.
	T is the time designator that precedes the time components of the representation.
	H is the hour designator that follows the value for the number of hours.
	M is the minute designator that follows the value for the number of minutes.
	S is the second designator that follows the value for the number of seconds.	

	Examples:
	d = 'P1M2D' # 1 month, 2 days
	d = 'P1Y2M3DT4H5M6S' # 1 year, 2 months, 3 days, 4 hours, 5 minutes, 6 seconds
	d = 'P3W' # 3 weeks

	"""

	regex = re.compile('''
			(?P<type>.)
			((?P<weeks>[0-9,]+)W)?
			((?P<years>[0-9,]+)Y)?
			((?P<months>[0-9,]+)M)?
			((?P<days>[0-9,]+)D)?
			(T
				((?P<hours>[0-9,]+)H)?
				((?P<minutes>[0-9,]+)M)?
				((?P<seconds>[0-9,]+)S)?
			)?
			''', re.X)
	match = regex.search(d)
	rd = {} # return date
	
	# rdate['type'] = match.group('type')
	for key in ['weeks','years','months','days','hours','minutes','seconds']:
		if match.group(key):
			rd[key] = int(match.group(key))

	return rd



if __name__ == "__main__":
	pass


__version__ = "$Revision$".split(":")[1][:-1].strip()
