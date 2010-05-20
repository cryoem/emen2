import cgi

import emen2.db.datatypes
import emen2.util.parse_datetime
import emen2.db.config
g = emen2.db.config.g()

# convenience
Vartype = emen2.db.datatypes.Vartype

def quote_html(func):
	return func
	#return lambda *args, **kwargs: cgi.escape(func(*args, **kwargs))


class vt_int(Vartype):
	"""32-bit integer"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "d"
	def validate(self, engine, pd, value, db):
		return int(value)


class vt_longint(Vartype):
	"""64-bit integer"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "d"
	def validate(self, engine, pd, value, db):
		return int(value)


class vt_float(Vartype):
	"""single-precision floating-point"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "f"
	def validate(self, engine, pd, value, db):
		return float(value)

	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if value == None: return ""
		return "%s"%unicode(float(value))
		#return "%0.2f"%value


class vt_longfloat(Vartype):
	"""double-precision floating-point"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "f"
	def validate(self, engine, pd, value, db):
		return float(value)
		#return "%0.2f"%float(value)


class vt_choice(Vartype):
	"""string from a fixed enumerated list, eg "yes","no","maybe"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None



class vt_list(Vartype):
	"""nested lists; e.g. permissions"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value)



class vt_string(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"

	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None


class vt_rectype(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None

	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value)



class vt_text(Vartype):
	"""freeform text, fulltext (word) indexing, str or unicode"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None

	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		return unicode(value).replace("\n","<br />")


import htmlentitydefs
import re
class vt_html(Vartype):
	"""freeform text, fulltext (word) indexing, str or unicode"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	def validate(self, engine, pd, value, db):
		return unicode(value) or None


	def encode(self, value):
		value = value or ""
		result = []
		for x in value:
			n = htmlentitydefs.codepoint2name.get(ord(x))
			if n is not None: x = '&%s;' % n
			result.append(x)
		return ''.join(result)


	#def decode(self, pd, value):
	#	expanded = [htmlentitydefs.name2codepoint.get(y,y) for y in [x[1] or x[2] for x in re.findall('(&([^;]+);|([^&]))', value)]]
	#	result = []
	#	for x in expanded:
	#		if isinstance(x, int):
	#			result.append(chr(x))
	#		else:
	#			result.append(x)
	#	return ''.join(result)



class vt_time(Vartype):
	"""time, HH:MM:SS"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		emen2.util.parse_datetime.parse_time(value)
		return unicode(value) or None


class vt_date(Vartype):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		emen2.util.parse_datetime.parse_date(value)
		return unicode(value) or None


# ian: todo: high priority: see fixes in parse_datetime, extend to other date validators
class vt_datetime(Vartype):
	"""date/time, yyyy/mm/dd HH:MM:SS"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(emen2.util.parse_datetime.parse_datetime(value)) or None


class vt_intlist(Vartype):
	"""list of ints"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [int(x) for x in value] or None


class vt_floatlist(Vartype):
	"""list of floats"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [float(x) for x in value] or None


class vt_stringlist(Vartype):
	"""list of strings"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None
		
	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		return ", ".join(value or [])
	


class vt_url(Vartype):
	"""link to a generic url"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None



class vt_hdf(Vartype):
	"""url points to an HDF file"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None



class vt_image(Vartype):
	"""url points to a browser-compatible image"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None



class vt_binary(Vartype):
	"""url points to an arbitrary binary... ['bdo:....','bdo:....','bdo:....']"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None


class vt_binaryimage(Vartype):
	"""non browser-compatible image requiring extra 'help' to display... 'bdo:....'"""
	__metaclass__ = Vartype.register_view
	# ian: don't index this after all...
	__indextype__ = None #"s"
	@quote_html
	def validate(self, engine, pd, value, db):
		return unicode(value) or None


class vt_child(Vartype):
	"""link to dbid/recid of a child record"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None #"child"
	def validate(self, engine, pd, value, db):
		return int(value)


class vt_links(Vartype):
	"""references to other records; can be parent/child/cousin/etc."""
	__metaclass__ = Vartype.register_view
	__vartype__ = "links"
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [int(x) for x in value] or None


class vt_link(Vartype):
	"""lateral link to related record dbid/recid"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None #"link"
	def validate(self, engine, pd, value, db):
		return int(value)


class vt_boolean(Vartype):
	"""boolean"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "d"
	def validate(self, engine, pd, value, db):
		try:
			return bool(int(value))
		except:
			if unicode(value).lower() in ("t","y","true"): return True
			if unicode(value).lower() in ("f","n","false"): return False
			raise ValueError,"Invalid boolean: %s"%unicode(value)


class vt_dict(Vartype):
	"""dict"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		return dict(value) or None


class vt_user(Vartype):
	"""user, by username"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	def validate(self, engine, pd, value, db):
		# ian: todo: What if usernames list becomes huge? Do this on a per-username to check basis. But for now OK.
		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)		

		if value in usernames:
			return unicode(value) or None
			
		raise ValueError	


	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if value == None:
			return ""

		key = engine.get_cache_key('getuserdisplayname', value)
		hit, dn = engine.check_cache(key)
		if not hit:
			dn = db.getuserdisplayname(value, lnf=True, filt=True) or "(%s)"%value
			engine.store(key, dn)

		return dn



class vt_userlist(Vartype):
	"""list of usernames"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value = [value]

		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)		

		if set(value) - usernames:
			raise ValueError

		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if not value:
			return ""
		if not hasattr(value,"__iter__"):
			value=[value]

		ret = []
		to_cache = []

		for v in value:
			key = engine.get_cache_key('getuserdisplayname', v)
			hit, dn = engine.check_cache(key)
			if not hit:
				to_cache.append(v)
		
		if to_cache:
			for k,v in db.getuserdisplayname(to_cache, lnf=True, filt=True).items():
				key = engine.get_cache_key('getuserdisplayname', k)
				engine.store(key, v)
				
				
		for v in value:
			key = engine.get_cache_key('getuserdisplayname', v)
			hit, dn = engine.check_cache(key)
			ret.append(dn or "(%s)"%v)
			
		return ", ".join(ret)



class vt_acl(Vartype):
	"""permissions access control list; nested lists of users"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "acl"
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		
		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)		

		users = reduce(lambda x,y:x+y, value)		
		if set(users) - usernames:
			raise ValueError
			
		return [[unicode(y) for y in x] for x in value]



	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if not value: return ""
		value=reduce(lambda x,y:x+y, value)
		unames=db.getuserdisplayname(value, lnf=True)
		levels=["Read","Comment","Write","Admin"]
		ret=[]
		for level,names in enumerate(value):
			namesr=[unames.get(i,"(%s)"%i) for i in names]
			ret.append("%s: %s"%(levels[level],", ".join(namesr)))
		return ". ".join(ret)


class vt_comments(Vartype):
	"""comments"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "comments"
	__indextype__ = None
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


	@quote_html
	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if value == None: return ""
		return unicode(value)


class vt_history(Vartype):
	"""history"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "history"
	__indextype__ = None
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

	@quote_html
	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if value == None: return ""
		return unicode(value)


class vt_groups(Vartype):
	"""groups"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "groups"
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		return set([unicode(i) for i in value])

	@quote_html
	def render_unicode(self, engine, pd, value, rec, db, render_cache=None):
		if value == None: return ""
		return unicode(value)



