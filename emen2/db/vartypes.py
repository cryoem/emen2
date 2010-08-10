import cgi
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
g = emen2.db.config.g()

# convenience
Vartype = emen2.db.datatypes.Vartype


#def quote_html(func):
#	return lambda *args, **kwargs: cgi.escape(func(*args, **kwargs))




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

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return "%0.2f"%value




class vt_longfloat(Vartype):
	"""double-precision floating-point"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "f"
	
	def validate(self, engine, pd, value, db):
		return float(value)

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return "%0.2f"%value
	
	
	

class vt_choice(Vartype):
	"""string from a fixed enumerated list, eg "yes","no","maybe"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	
	def validate(self, engine, pd, value, db):
		return unicode(value) or None





class vt_list(Vartype):
	"""nested lists; e.g. permissions"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	
	def validate(self, engine, pd, value, db):
		return unicode(value)
	
	
	
		

class vt_string(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"

	def validate(self, engine, pd, value, db):
		return unicode(value) or None




class vt_rectype(Vartype):
	"""a string indexed as a whole, may have an extensible enumerated list or be arbitrary"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None

	def validate(self, engine, pd, value, db):
		return unicode(value)




class vt_text(Vartype):
	"""freeform text, fulltext (word) indexing, str or unicode"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	
	def validate(self, engine, pd, value, db):
		return unicode(value) or None


	def render_unicode(self, engine, pd, value, rec, db):
		return unicode(value).replace("\n","<br />")


	def render_html(self, engine, pd, value, rec, db, edit=0):
		if value == None:
			value = ""
		value = cgi.escape(value)
		value = markdown.markdown(value)
		if edit:
			value = '<span class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s<span class="label">Edit</span></span>'%(rec.recid, pd.name, pd.vartype, value)
		return value




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

	def validate(self, engine, pd, value, db):
		parse_time(value)
		return unicode(value) or None




class vt_date(Vartype):
	"""date, yyyy/mm/dd"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"

	def validate(self, engine, pd, value, db):
		parse_date(value)
		return unicode(value) or None




# ian: todo: high priority: see fixes in parse_datetime, extend to other date validators
class vt_datetime(Vartype):
	"""date/time, yyyy/mm/dd HH:MM:SS"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	
	def validate(self, engine, pd, value, db):
		return unicode(parse_datetime(value)) or None




class vt_intlist(Vartype):
	"""list of ints"""
	__metaclass__ = Vartype.register_view
	__indextype__ = 'd'
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [int(x) for x in value] or None




class vt_intlistlist(Vartype):
	"""list of int tuples: e.g. [[1,2],[3,4], ..]"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		return [[int(x) for x in i] for i in value] or None






class vt_floatlist(Vartype):
	"""list of floats"""
	__metaclass__ = Vartype.register_view
	__indextype__ = 'f'
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [float(x) for x in value] or None




class vt_stringlist(Vartype):
	"""list of strings"""
	__metaclass__ = Vartype.register_view
	__indextype__ = 's'
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db):
		return ", ".join(value or [])


	def render_html(self, engine, pd, value, rec, db, edit=0):
		if not value:
			value=[]
		if not hasattr(value,"__iter__"):
			value=[value]

		lis = ['<li>%s</li>'%cgi.escape(i) for i in value]
		if edit:
			lis.append('<li class="label">Edit</li>')		
			ul = '<ul class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s</ul>'%(rec.recid, pd.name, pd.vartype, "\n".join(lis))
		else:
			ul = '<ul>%s</ul>'%("\n".join(lis))

		return ul




class vt_uri(Vartype):
	"""link to a generic uri"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"

	def validate(self, engine, pd, value, db):
		return unicode(value) or None

	def render_html(self, engine, pd, value, rec, db, edit=0):
		if not value:
			value=[]
		if not hasattr(value,"__iter__"):
			value=[value]

		value = cgi.escape(value)
		href = '<a href="%s">%s</a>'%(value,value)
		if edit:
		 	href = '<span class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s<span class="label">Edit</span></span>'%(rec.recid, pd.name, pd.vartype, href)
		return href
		



class vt_urilist(Vartype):
	"""list of uris"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None

	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value=[value]
		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db):
		return ", ".join(value or [])

			
	def render_html(self, engine, pd, value, rec, db, edit=0):
		if not value:
			value=[]
		if not hasattr(value,"__iter__"):
			value=[value]

		lis = ['<li><a href="%s">%s</a></li>'%(cgi.escape(i), cgi.escape(i)) for i in value]
		if edit:
			lis.append('<li class="label">Edit</li>')		
			ul = '<ul class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s</ul>'%(rec.recid, pd.name, pd.vartype, "\n".join(lis))
		else:
			ul = '<ul>%s</ul>'%("\n".join(lis))

		return ul		
		



class vt_hdf(Vartype):
	"""url points to an HDF file"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	
	def validate(self, engine, pd, value, db):
		return unicode(value) or None





class vt_image(Vartype):
	"""url points to a browser-compatible image"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"
	
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


	def render_html(self, engine, pd, value, rec, db, edit=0):
		if not value:
			value = []
		if not hasattr(value,"__iter__"):
			value = [value]

		v = db.getbinary(value)
		lis = ['<li><a href="%s/download/%s/%s">%s</a></li>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename)) for i in v]
		if edit:
			lis.append('<li class="label">Edit</li>')		
			ul = '<ul class="editable_files" data-recid="%s" data-param="%s" data-vartype="%s">%s</ul>'%(rec.recid, pd.name, pd.vartype, "\n".join(lis))
		else:
			ul = '<ul>%s</ul>'%("\n".join(lis))

		return ul


		

class vt_binaryimage(Vartype):
	"""non browser-compatible image requiring extra 'help' to display... 'bdo:....'"""
	__metaclass__ = Vartype.register_view
	# ian: don't index this after all...
	__indextype__ = None #"s"
	
	def validate(self, engine, pd, value, db):
		return unicode(value) or None


	def render_unicode(self, engine, pd, value, rec, db):
		if not value:
			return ""
		try:
			i = db.getbinary(value)
			return '<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, i.filename, i.filename)
		except:
			return ""


	def render_html(self, engine, pd, value, rec, db, edit=0):
		if not value:
			return ""
		i = db.getbinary(value)
		href = ""
		if i:
			href = '<a href="%s/download/%s/%s">%s</a>'%(g.EMEN2WEBROOT, i.name, urllib.quote(i.filename), cgi.escape(i.filename))
		if edit:
			href = '<span class="editable_files" data-recid="%s" data-param="%s" data-vartype="%s">%s<span class="label">Edit</span></span>'%(rec.recid, pd.name, pd.vartype, href)
		return href





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



class vt_user(Vartype):
	"""user, by username"""
	__metaclass__ = Vartype.register_view
	__indextype__ = "s"

	def validate(self, engine, pd, value, db):
		key = engine.get_cache_key('usernames')
		hit, usernames = engine.check_cache(key)
		if not hit:
			usernames = db.getusernames()
			engine.store(key, usernames)

		if value in usernames:
			return unicode(value) or None

		raise ValueError


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None:
			return ""

		update_username_cache(engine, [value], db)
		hit, dn = engine.check_cache(engine.get_cache_key('displayname', value))
		return dn


	def render_html(self, engine, pd, value, rec, db, edit=0):
		if value == None:
			return ""

		update_username_cache(engine, [value], db)
		hit, dn = engine.check_cache(engine.get_cache_key('displayname', value))
		dn = '<a href="%s/db/user/%s/">%s</a>'%(g.EMEN2WEBROOT, value, dn)
		if edit:
			dn = '<span class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s<span class="label">Edit</span></span>'%(rec.recid, pd.name, pd.vartype, dn)
		return dn



class vt_userlist(Vartype):
	"""list of usernames"""
	__metaclass__ = Vartype.register_view
	__indextype__ = None
	
	def validate(self, engine, pd, value, db):
		if not hasattr(value,"__iter__"):
			value = [value]

		key = engine.get_cache_key('usernames')
		hit,usernames = engine.check_cache(key)
		if (not hit):
			usernames = db.getusernames()
			engine.store(key, usernames)

		if set(value) - usernames:
			raise ValueError

		return [unicode(x) for x in value] or None


	def render_unicode(self, engine, pd, value, rec, db):
		value = self.check_iterable(value)
		update_username_cache(engine, value, db)
		
		# Read values from cache and build list
		lis = []
		for v in value:
			key = engine.get_cache_key('displayname', v)
			hit, dn = engine.check_cache(key)
			lis.append(hit)
		return ", ".join(lis)
		
		
	def render_html(self, engine, pd, value, rec, db, edit=0):
		value = self.check_iterable(value)
		update_username_cache(engine, value, db)

		value = (cgi.escape(i) for i in value)
		lis = ['<li><a href="%s">%s</a></li>'%(i,i) for i in value]
		if edit:
			lis.append('<li class="label">Edit</li>')		
			ul = '<ul class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s</ul>'%(rec.recid, pd.name, pd.vartype, "\n".join(lis))

		else:
			ul = '<ul>%s</ul>'%("\n".join(lis))

		return ul		




# ian: todo: change to be more like vt_userlist
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


	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)


	def render_html(self, engine, pd, value, rec, db, edit=0):
		value = self.check_iterable(value)		
		users=[i[0] for i in value]
		update_username_cache(engine, users, db)
		lis = []
		for user, time, comment in value:
			key = engine.get_cache_key('displayname', user)
			hit, dn = engine.check_cache(key)
			t = '<div class="comment"><h4><a href="%s/db/user/%s/">%s</a> @ %s</h4>%s</div>'%(g.EMEN2WEBROOT, user, cgi.escape(dn), time, cgi.escape(comment))
			lis.append(t)

		if edit:
			lis.append('<p class="label">Add Comment</p>')
			lis = '<div class="editable" data-recid="%s" data-param="%s" data-vartype="%s">%s</div>'%(rec.recid, pd.name, pd.vartype, "\n".join(lis))
		else:
			lis = "\n".join(lis)

		return lis



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

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)



class vt_groups(Vartype):
	"""groups"""
	__metaclass__ = Vartype.register_view
	__vartype__ = "groups"
	__indextype__ = None
	def validate(self, engine, pd, value, db):
		return set([unicode(i) for i in value])

	def render_unicode(self, engine, pd, value, rec, db):
		if value == None: return ""
		return unicode(value)







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
	string = string.strip()
	if not string:
		return None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ').split(".")
	msecs = 0
	if len(string) > 1:
		msecs = int(string.pop().ljust(6,'0'))
	string = ".".join(string)

	for format, output in datetime_formats:
		try:
			string = datetime.datetime.strptime(string, format)
			return datetime.datetime.strftime(string, output)
		except ValueError, inst:
			#print inst
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
			return datetime.datetime.strptime(string, format).time()
		except ValueError, inst:
			#print inst
			pass

	raise ValueError()



def parse_date(string):
	string = string.strip()
	if not string: return None

	string = string.replace('/',' ').replace('-',' ').replace(',',' ')

	for format in date_formats:
		try:
			return datetime.datetime.strptime(string, format).date()
		except ValueError:
			pass

	raise ValueError()

