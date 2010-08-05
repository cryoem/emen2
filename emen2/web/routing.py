from __future__ import with_statement

### Unit-tested in emen2.tests.test_routing.py
### If you change anything run (from emen2 directory):
###	 PYTHONPATH=.. python tests/test_routing.py
### Also, make sure the tests reflect the current code

from functools import partial
from itertools import izip
from emen2.util import listops
import re
import sre_parse
import cgi

from emen2.web import responsecodes
import emen2.db.config
g = emen2.db.config.g()


class doubledict(object):
	def __init__(self, keys=None, values1=None, values2=None):
		if None in (keys, values1, values2):
			keys, values1, values2 = [],[],[]
		self.__dict_l = dict(zip(keys, values1))
		self.__dict_r = dict(zip(keys, values2))
	@classmethod
	def from_dict(cls, dct):
		self = cls.__new__(cls)
		self.__dict_l, self.__dict_r, self.__vl_vr = {}, {}, {}
		for k, (v_l, v_r) in dct.iteritems():
			self.__dict_l[k] = v_l
			self.__dict_r[k] = v_r
		return self
	def get(self, name, default=None):
		return self.get_left(name, default), self.get_right(name, default)
	__getitem__ = get
	def get_left(self, name, default=None):
		return self.__dict_l.get(name, default)
	def get_right(self, name, default=None):
		return self.__dict_r.get(name, default)
	def set(self, name, value, right=True):
		if right:
			self.__dict_r[name] = value
		else:
			self.__dict_l[name] = value
	__setitem__ = set
	def add(self, k, v_l, v_r):
		self.__dict_l[k] = v_l
		self.__dict_r[k] = v_r
	def keys(self):
		assert set(self.__dict_l) == set(self.__dict_r)
		return self.__dict_l.keys()
	def values(self):
		assert set(self.__dict_l) == set(self.__dict_r)
		return zip(self.__dict_l.values(), self.__dict_r.values())
	def items(self):
		assert set(self.__dict_l) == set(self.__dict_r)
		return zip(self.__dict_l.iterkeys(), self.__dict_l.itervalues(), self.__dict_r.itervalues())
	def iteritems(self):
		assert set(self.__dict_l) == set(self.__dict_r)
		return izip(self.__dict_l.iterkeys(), self.__dict_l.itervalues(), self.__dict_r.itervalues())
	def iteritems_l(self):
		return self.__dict_l.iteritems()
	def iteritems_r(self):
		return self.__dict_r.iteritems()
	def itervalues_l(self):
		return self.__dict_l.itervalues()
	def itervalues_r(self):
		return self.__dict_r.itervalues()




class URL(object):
	def __init__(self, name, **matchers):
		self.__name = name
		self.__matchers = doubledict()
		for nm, (matcher, callback) in matchers.iteritems():
			self.add_matcher(nm, matcher, callback)

	def add_matcher(self, method, matcher, cb):
		if not hasattr(matcher, 'match'): matcher = re.compile(matcher)
		# g.debug('method:', method, 'matcher:', matcher.pattern, 'cb:', cb.__name__, join=' ')
		self.__matchers.add(method, matcher, cb)


	def __repr__(self):
		try:
			result = '<URL %r>' % (self.__name)
		except: result = object.__repr__(self)
		return result

	def get_name(self): return self.__name
	name = property(get_name)

	def get_matcher(self, name):
		return self.__matchers.get_left(name)
	matcher = property(get_matcher)

	@staticmethod
	def method_notsupported(inp, *args, **kwargs):
		raise responsecodes.MethodNotAllowedError(inp)

	def get_callback(self, method='main', fallback=None):
		return self.__matchers.get_right(method, fallback)
	callback = property(get_callback)

	def merge(self, other):
		g.debug('merging, before:',self.__callbacks)
		# self.__callbacks.update((k,v) for k,v in other.__callbacks.iteritems() if k not in self.__callbacks)
		g.debug('merged, after:',self.__callbacks)

	def match(self, string):
		match = False
		result = '', False
		for key, matcher in self.__matchers.iteritems_l():
			match = matcher.match(string)
			if match:
				result = key, match
				break
		return result

class URLRegistry(object):
	if not g.getattr('URLRegistry', False):
		g.URLRegistry = {}
	URLRegistry = g.URLRegistry
	__prepend = ''

	def _match(self, inp):
		result = [None,None,None]
		for url in self.URLRegistry.values():
			tmp = url.match(inp)
			if tmp[1]:
				result[0] = tmp[0]
				result[1] = tmp[1].groupdict()
				result[2] = url
				break
		return result


	class __matcher(object):
		'internal class'
		def __init__(self, urlreg):
			self.__urlreg = urlreg
		def match(self, inp):
			self.__inp = inp
			return self
		def __enter__(self):
			return self.__urlreg._match(self.__inp)
		def __exit__(*args): pass

	def __init__(self, prepend='', default=True, onfail=('page not found', 'text/plain')):
		self.__prepend = prepend or self.__prepend
		self.__default = default
		self.__onfail = onfail
		self.__matcher = self.__matcher(self)
		self.match = self.__matcher.match
	def __setitem__(self, name, value):
		self.URLRegistry[name] = value
	def __getitem__(self, name):
		return self.URLRegistry[name].get_callback('main')
	def __delitem__(self, name):
		del self.URLRegistry[name]

	def toggle_default(self):
		self.__default = not self.__default
	def get_default(self):
		return self.__default
	def set_default(self, value):
		self.__default = bool(value)
	default = property(get_default, set_default)

	@staticmethod
	def onfail(inp):
		raise responsecodes.NotFoundError(inp)

	@staticmethod
	def onfail1(m1,m2):
		raise responsecodes.HTTPResponseCode, 'Method mismatch: %s, %s' % (m1,m2)

	def execute(self, inp, method='GET', fallback=None, **kw):
		result = None

		with self.match(inp) as (sub, groups, url):
			if url is not None:
				args = listops.adj_dict(groups, kw)
				cb = url.get_callback(sub, fallback='main')
				result = partial(cb, **args)

		if result is None and self.__default is True:
			result = lambda *args, **kwargs: self.onfail(inp)

		return result

	@classmethod
	def call_view(cls, name, *args, **kwargs):
		cb = cls.get(name).get_callback()
		return cb(*args, **kwargs)

	def register(self, url):
		name = url.name
		result = name in self.URLRegistry
		self[name] = url
		return result

	@classmethod
	def reset(cls):
		cls.URLRegistry = {}

	@classmethod
	def get(cls, name, default=None):
		return cls.URLRegistry.get(name, default)

	@classmethod
	def reverselookup(cls, __name_, *args, **kwargs):
		__name_ = __name_.split('/',1)
		if len(__name_) == 1: __name_.append('main')
		url = cls.get(__name_[0], None)
		if url is not None:
			result = cls.reverse_helper(url.get_matcher(__name_[1]), *args, **kwargs)
			result = str.join('', (cls.__prepend, result))
		else:
			result = '/error/'
		return result

	def is_reachable(self, url):
		with self.match(url) as (a,b):
			return a != None and b != None

	@classmethod
	def reverse_helper(cls, __regex_, *args, **kwargs):
		mc = MatchChecker(args, kwargs)
		result = re.sub(r'\(([^)]+)\)', mc, __regex_.pattern)
		qs = '&'.join( '%s=%s' % (k,v) for k,v in mc.get_unused_kwargs().items() )
		result = [result.replace('^', '').replace('$', ''),qs]
		if qs == '': result.pop()
		return '?'.join(result)

def force_unicode(string):
	result = string
	if isinstance(result, unicode):
		return result
	elif hasattr(result, '__unicode__'):
		return unicode(result)
	else:
		return unicode(result, 'utf-8', errors='replace')

# modified code from Django
class NoReverseMatch(Exception): pass
class MatchChecker(object):
	"Class used in reverse RegexURLPattern lookup."
	def __init__(self, args, kwargs):
		self.args, self.kwargs = map(str, args), dict([(x, str(y)) for x, y in kwargs.items()])
		self.used_kwargs = set([])
		self.current_arg = 0

	def get_next_posarg(self):
		try:
			result = self.args[self.current_arg]
			self.current_arg += 1
		except IndexError:
			result = None
		return result

	def get_kwarg(self, name):
		result = self.kwargs.get(name)
		if result is None:
			result = self.get_next_posarg()
		else:
			self.used_kwargs.add(name)
		return result

	def get_unused_kwargs(self):
		return dict( (k,v) for k,v in self.kwargs.iteritems() if k not in self.used_kwargs )


	NAMED_GROUP = re.compile(r'^\?P<(\w+)>(.*?)$', re.UNICODE)
	def __call__(self, match_obj):
		grouped = match_obj.group(1)
		#m = re.search(r'^\?P<(\w+)>(.*?)$', grouped, re.UNICODE)
		m = self.NAMED_GROUP.search(grouped)

		if m:
			value, test_regex = self.get_kwarg(m.group(1)), m.group(2)
		else:
			value, test_regex = self.get_next_posarg(), grouped
		if value is None:
			raise NoReverseMatch('Not enough arguments passed in')

		if not re.match(test_regex + '$', value, re.UNICODE):
			raise NoReverseMatch("Value %r didn't match regular expression %r" % (value, test_regex))
		return force_unicode(value)

if __name__ == '__main__':
	print doubledict()
	a = URL('test', GET=('asda(?P<asdasd>sd)', lambda *args, **kwargs: (args, kwargs)))
	print a.match('asdasd')[1].groupdict()
	ur = URLRegistry();ur.register(a)
