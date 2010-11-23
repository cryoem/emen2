# $Id$

import cgi
import operator
import collections
import urllib
import time, datetime
import htmlentitydefs
import re

try:
	import markdown
except:
	markdown = None

	
import emen2.db.datatypes
import emen2.db.config
import emen2.util.listops
g = emen2.db.config.g()


class Vartype(object):

	keytype = None

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
		emen2.db.datatypes.VartypeManager._register_vartype(name, cls)

	def __init__(self):
		# typical modes: html, unicode, edit
		self.modes={
			"html":self.render_html,
			"htmledit":self.render_htmledit,
			"htmledit_table":self.render_htmledit_table
			}


	def getvartype(self):
		return self.__vartype__


	def getkeytype(self):
		return self.keytype


	def render(self, engine, pd, value, mode, rec, db):
		return self.modes.get(mode, self.render_unicode)(engine, pd, value, rec, db)


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None:
			return ""
		return unicode(value)


	# This is the default HTML renderer for single-value items. It is important to cgi.escape the values!!
	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		if value != None:
			value = cgi.escape(unicode(value))
		return self._render_html_single(engine, pd, value, rec, db, edit, showlabel, lt=lt)
		

	def render_htmledit(self, engine, pd, value, rec, db):
		"""Mark field as editable, but do not show controls"""
		return self.render_html(engine, pd, value, rec, db=db, edit=1)


	def render_htmledit_table(self, engine, pd, value, rec, db):
		"""Mark field as editable, but do not show controls"""
		return self.render_html(engine, pd, value, rec, db=db, edit=1, showlabel='', lt=True)


	# after pre-processing values into markup
	# the LT flag is used for table format, to link to the row's recid
	def _render_html_list(self, engine, pd, value, rec, db, edit=0, showlabel=True, elem_class='editable', lt=False):
		if not value:
			if edit and showlabel:
				showlabel = '<img src="%s/static/images/blank.png" class="label underline" alt="No value" />'%g.EMEN2WEBROOT
			if edit:
				return '<span class="%s" data-recid="%s" data-param="%s">%s</span>'%(elem_class, rec.recid, pd.name, showlabel)				
			return '<span></span>'

		if lt:
			lis = ['<li><a href="%s/record/%s">%s</a></li>'%(g.EMEN2WEBROOT, rec.recid, i) for i in value]
		else:
			lis = ['<li>%s</li>'%i for i in value]
			

		if not edit:
			return '<ul>%s</ul>'%("\n".join(lis))

		if showlabel:
			lis.append('<li class="nobullet"><span class="edit label"><img src="%s/static/images/edit.png" alt="Edit" /></span></li>'%g.EMEN2WEBROOT)		
		return '<ul class="%s" data-recid="%s" data-param="%s" data-vartype="%s">%s</ul>'%(elem_class, rec.recid, pd.name, pd.vartype, "\n".join(lis))


	# after pre-processing values into markup
	def _render_html_single(self, engine, pd, value, rec, db, edit=0, showlabel=True, elem='span', elem_class='editable', lt=False):
		if not value:
			if edit and showlabel:
				showlabel = '<img src="%s/static/images/blank.png" class="label underline" alt="No value" />'%g.EMEN2WEBROOT
			if edit:
				return '<%s class="%s" data-recid="%s" data-param="%s">%s</%s>'%(elem, elem_class, rec.recid, pd.name, showlabel, elem)
			return '<%s></%s>'%(elem, elem)

		if lt:
			value = '<a href="%s/record/%s">%s</a>'%(g.EMEN2WEBROOT, rec.recid, value)

		if not edit:
			return value
			
		if showlabel:
			showlabel = '<span class="edit label"><img src="%s/static/images/edit.png" alt="Edit" /></span>'%g.EMEN2WEBROOT
		return '<%s class="%s" data-recid="%s" data-param="%s" data-vartype="%s">%s%s</%s>'%(elem, elem_class, rec.recid, pd.name, pd.vartype, value, showlabel, elem)


	def encode(self, value):
		return value


	def decode(self, pd, value):
		return value


	def validate(self, engine, pd, value, db):
		# return a validated value
		return value


	def reindex(self, items):
		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)
		for recid, new, old in items:
			if new == old:
				continue
			delrefs[old].add(recid)
			addrefs[new].add(recid)

		if None in addrefs: del addrefs[None]
		if None in delrefs: del delrefs[None]

		return addrefs, delrefs





class vt_iter(object):
	def reindex(self, items):
		# items format: [recid, newval, oldval]
		addrefs = collections.defaultdict(set)
		delrefs = collections.defaultdict(set)
		for recid, new, old in items:
			if new == old:
				continue
			
			new = set(new or [])
			old = set(old or [])
			for n in new-old:
				addrefs[n].add(recid)

			for o in old-new:
				delrefs[o].add(recid)

		if None in addrefs: del addrefs[None]
		if None in delrefs: del delrefs[None]

		return addrefs, delrefs




# Float vartypes
	
class vt_float(Vartype):
	"""single-precision floating-point"""
	__metaclass__ = Vartype.register_view
	keytype = "f"

	def validate(self, engine, pd, value, db):
		return float(value)

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return "%0.2f"%value



class vt_longfloat(vt_float):
	"""double-precision floating-point"""
	__metaclass__ = Vartype.register_view
	



class vt_floatlist(vt_iter, vt_float):
	"""list of floats"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [float(x) for x in value] or None





# Integer vartypes
	
class vt_int(Vartype):
	"""32-bit integer"""
	__metaclass__ = Vartype.register_view
	keytype = "d"
	def validate(self, engine, pd, value, db):
		return int(value)
	

class vt_longint(vt_int):
	"""64-bit integer"""
	__metaclass__ = Vartype.register_view



class vt_intlist(vt_iter, vt_int):
	"""list of ints"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [int(x) for x in value] or None



class vt_intlistlist(vt_int):
	"""list of int tuples: e.g. [[1,2],[3,4], ..]"""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, engine, pd, value, db):
		return [[int(x) for x in i] for i in value] or None



class vt_boolean(vt_int):
	"""boolean"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		try:
			return bool(int(value))
		except:
			if unicode(value).lower() in ("t","y","true"): return True
			if unicode(value).lower() in ("f","n","false"): return False
			raise ValueError,"Invalid boolean: %s"%unicode(value)





class vt_recid(Vartype):
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, engine, pd, value, db):
		return int(value)
	
	
	


# String vartypes

class vt_string(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, engine, pd, value, db):
		return unicode(value) or None



class vt_choice(vt_string):
	"""string from a fixed enumerated list, eg "yes","no","maybe"""
	__metaclass__ = Vartype.register_view

	
	
class vt_rectype(vt_string):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view




class vt_stringlist(vt_iter, vt_string):
	"""list of strings"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None

	def render_unicode(self, engine, pd, value, rec, db):
		return ", ".join(value or [])

	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		value = emen2.util.listops.check_iterable(value)
		value = [cgi.escape(i) for i in value]			
		return self._render_html_list(engine, pd, value, rec, db, edit, showlabel, lt=lt)




class vt_text(vt_string):
	"""freeform text, fulltext (word) indexing, str or unicode"""
	__metaclass__ = Vartype.register_view

	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		if value != None:
			value = cgi.escape(unicode(value))
			if markdown:
				value = markdown.markdown(value)
		return self._render_html_single(engine, pd, value, rec, db, edit, showlabel, elem='div', lt=lt)


	def reindex(self, items):
		"""(Internal) calculate param index updates for vartype == text"""

		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)
		for item in items:
			if item[1]==item[2]:
				continue
				
			for i in self.__reindex_getindexwords(item[1]):
				addrefs[i].append(item[0])

			for i in self.__reindex_getindexwords(item[2]):
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



	__reindex_getindexwords_m = re.compile('([a-zA-Z]+)|([0-9][.0-9]+)')  #'[\s]([a-zA-Z]+)[\s]|([0-9][.0-9]+)'
	def __reindex_getindexwords(self, value, ctx=None, txn=None):
		"""(Internal) Split up a text param into components"""
		if value == None: return []
		value = unicode(value).lower()
		return set((x[0] or x[1]) for x in self.__reindex_getindexwords_m.findall(value))







# Time vartypes (keytype is string)

# ian: todo: high priority: see fixes in parse_datetime, extend to other date validators
class vt_datetime(vt_string):
	"""date/time, yyyy/mm/dd HH:MM:SS"""
	__metaclass__ = Vartype.register_view
	keytype = "s"
	
	def validate(self, engine, pd, value, db):
		return unicode(parse_datetime(value)[1]) or None
		
		

class vt_time(vt_datetime):
	"""time, HH:MM:SS"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		parse_time(value)
		return unicode(value) or None



class vt_date(vt_datetime):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		parse_date(value)
		return unicode(value) or None








# Reference vartypes (uri, binary, hdf, etc.).

class vt_ref(Vartype):
	keytype = "s"



class vt_uri(vt_ref):
	"""link to a generic uri"""
	__metaclass__ = Vartype.register_view

	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		if value != None:
			value = cgi.escape(unicode(value))
			value = '<a href="%s">%s</a>'%(value,value)
		return self._render_html_single(engine, pd, value, rec, db, edit, showlabel)



class vt_urilist(vt_iter, vt_ref):
	"""list of uris"""
	__metaclass__ = Vartype.register_view

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db):
		return ", ".join(value or [])


	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		value = emen2.util.listops.check_iterable(value)
		value = [cgi.escape(i) for i in value]
		value = ['<a href="%s">%s</a>'%(i,i) for i in value]
		return self._render_html_list(engine, pd, value, rec, db, edit, showlabel)





# Binary vartypes

# ian: todo: strict validation; these can actually take any arbitrary string
class vt_binary(vt_iter, Vartype):
	"""BDO reference"""
	__metaclass__ = Vartype.register_view
	keytype = None
	
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value = [value]
		return [unicode(x) for x in value] or None


	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		value = emen2.util.listops.check_iterable(value)
		try:
			v = db.getbinary(value)
			value = ['<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename)) for i in v]	
		except:
			value = ['Error getting binary %s'%i for i in value]
		return self._render_html_list(engine, pd, value, rec, db, edit, showlabel, elem_class="editable_files")

		

class vt_binaryimage(Vartype):
	"""non browser-compatible image requiring extra 'help' to display... 'bdo:....'"""
	__metaclass__ = Vartype.register_view
        keytype = None

	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		if value != None:
			try:
				i = db.getbinary(value)
				value = '<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename))
			except:
				value = "Error getting binary %s"%value
		return self._render_html_single(engine, pd, value, rec, db, edit, showlabel, elem_class="editable_files")



class vt_hdf(vt_binary):
	"""BDO or URI points to an HDF file"""
	__metaclass__ = Vartype.register_view
	keytype = None



class vt_image(vt_binary):
	"""BDO or URI points to a browser-compatible image"""
	__metaclass__ = Vartype.register_view
	keytype = None







# Internal record-record linkes

class vt_links(vt_iter, Vartype):
	"""references to other records; can be parent/child/cousin/etc."""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [int(x) for x in value] or None





# dict -- I don't think this is used anywhere.

# class vt_dict(Vartype):
# 	"""dict"""
# 	__metaclass__ = Vartype.register_view
# 	keytype = None
# 	
# 	def validate(self, engine, pd, value, db):
# 		return dict(value) or None




# User vartypes

class vt_user(Vartype):
	"""user, by username"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, engine, pd, value, db):
		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)

		if value in usernames:
			return unicode(value) or None

		raise ValueError, "Unknown user: %s"%value


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None:
			return ""

		update_username_cache(engine, [value], db)
		hit, dn = engine.check_cache(engine.get_cache_key('displayname', value))
		return dn


	# ian: todo: make these nice .userboxes ?
	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		if value:
			update_username_cache(engine, [value], db)
			hit, dn = engine.check_cache(engine.get_cache_key('displayname', value))
			value = '<a href="%s/user/%s/">%s</a>'%(g.EMEN2WEBROOT, value, dn)
		return self._render_html_single(engine, pd, value, rec, db, edit, showlabel)



class vt_userlist(vt_iter, Vartype):
	"""list of usernames"""
	__metaclass__ = Vartype.register_view
	keytype = "s"
	
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value = [value]

		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if (not hit):
			usernames = db.getusernames()
			engine.store(key, usernames)

		if set(value) - usernames:
			raise ValueError, "Unknown users: %s"%(set(value) - usernames)

		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db):
		value = emen2.util.listops.check_iterable(value)
		update_username_cache(engine, value, db)
		
		# Read values from cache and build list
		lis = []
		for v in value:
			key = engine.get_cache_key('displayname', v)
			hit, dn = engine.check_cache(key)
			lis.append(dn)
		return ", ".join(lis)
		

	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		value = emen2.util.listops.check_iterable(value)
		update_username_cache(engine, value, db)

		lis = []
		for i in value:
			key = engine.get_cache_key('displayname', i)
			hit, dn = engine.check_cache(key)
			lis.append('<a href="%s/user/%s">%s</a>'%(g.EMEN2WEBROOT, i,dn))			

		return self._render_html_list(engine, pd, lis, rec, db, edit, showlabel)




# ian: todo: change to be more like vt_userlist
class vt_acl(Vartype):
	"""permissions access control list; nested lists of users"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "acl"
	keytype = "s"

	
	def validate(self, engine, pd, value, db):
		# print "acl validating: ", value
		# value = emen2.util.listops.check_iterable(value)
		if not hasattr(value, '__iter__'):
			value = ((value,),(),(),())
		
		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)

		users = reduce(lambda x,y:x+y, value)
		if set(users) - usernames:
			raise ValueError

		return [[unicode(y) for y in x] for x in value]


	def render_unicode(self, engine, pd, value, rec, db):
		if not value: return ""
		value=reduce(lambda x,y:x+y, value)

		unames = {}
		for user in db.getuser(value, lnf=True):
			unames[user.username] = user.displayname

		levels=["Read","Comment","Write","Admin"]
		ret=[]
		for level,names in enumerate(value):
			namesr=[unames.get(i,"(%s)"%i) for i in names]
			ret.append("%s: %s"%(levels[level],", ".join(namesr)))
		return ". ".join(ret)



	def reindex(self, items):
		"""(Internal) Calculate secrindex updates"""
		# g.log.msg('LOG_DEBUG', "Calculating security updates...")
		addrefs = collections.defaultdict(list)
		delrefs = collections.defaultdict(list)
		for recid, new, old in items:

			nperms = set(reduce(operator.concat, new or (), ()))
			operms = set(reduce(operator.concat, old or (), ()))

			for user in nperms - operms:
				addrefs[user].append(recid)
				
			for user in operms - nperms:
				delrefs[user].append(recid)

		return addrefs, delrefs



class vt_comments(Vartype):
	"""comments"""
	__metaclass__ = Vartype.register_view
	keytype = None
	
	def validate(self, engine, pd, value, db):
		users=[i[0] for i in value]
		times=[i[1] for i in value]
		values=[i[2] for i in value]

		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)

		if set(users) - usernames:
			raise ValueError

		return [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in value]


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)


	def render_html(self, engine, pd, value, rec, db, edit=False, showlabel=True, lt=False):
		value = emen2.util.listops.check_iterable(value)
		users=[i[0] for i in value]
		update_username_cache(engine, users, db)

		lis = []
		for user, time, comment in value:
			key = engine.get_cache_key('displayname', user)
			hit, dn = engine.check_cache(key)
			t = '<h4><a href="%s/user/%s">%s</a> @ %s</h4>%s'%(g.EMEN2WEBROOT, user, cgi.escape(dn), time, cgi.escape(comment))
			lis.append(t)

		return self._render_html_list(engine, pd, lis, rec, db, edit, showlabel, elem_class='comment')




class vt_history(Vartype):
	"""history"""
	__metaclass__ = Vartype.register_view
	keytype = None

	def validate(self, engine, pd, value, db):
		users=[i[0] for i in value]
		times=[i[1] for i in value]

		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)

		if set(users) - usernames:
			raise ValueError

		return [(unicode(i[0]), unicode(i[1]), unicode(i[2]), i[3]) for i in value]

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)




class vt_groups(vt_iter, Vartype):
	"""groups"""
	__metaclass__ = Vartype.register_view
	keytype = "s"

	def validate(self, engine, pd, value, db):
		value = emen2.util.listops.check_iterable(value)
		return set([unicode(i) for i in value])

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None:
			return ""
		return unicode(value)





###########################
# Helper methods

def update_username_cache(engine, values, db):
	# Check cache
	to_cache = []
	for v in values:
		key = engine.get_cache_key('displayname', v)
		hit, dn = engine.check_cache(key)
		if not hit:
			to_cache.append(v)

	if to_cache:
		users = db.getuser(to_cache, lnf=True, filt=True)
		for user in users:
			key = engine.get_cache_key('displayname', user.username)
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
