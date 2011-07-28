# $Id$
from __future__ import with_statement

import re
import sre_parse
import cgi

from functools import partial
from itertools import izip
from emen2.util import listops

import emen2.util.datastructures

from emen2.web import responsecodes
import emen2.db.config
g = emen2.db.config.g()



class URL(object):
	def __init__(self, name, **matchers):
		self._name = name
		self._matchers = emen2.util.datastructures.doubledict()
		for nm, (matcher, callback) in matchers.iteritems():
			self.add_matcher(nm, matcher, callback)

	def add_matcher(self, method, matcher, cb):
		if not hasattr(matcher, 'match'): matcher = re.compile(matcher)
		self._matchers.add(method, matcher, cb)


	def __repr__(self):
		try:
			result = '<URL %r>' % (self._name)
		except: result = object.__repr__(self)
		return result

	def get_name(self): return self._name
	name = property(get_name)

	def get_matcher(self, name):
		return self._matchers.get_left(name)
	matcher = property(get_matcher)

	@staticmethod
	def method_notsupported(inp, *args, **kwargs):
		raise responsecodes.MethodNotAllowedError(inp)

	def get_callback(self, method='main', fallback=None):
		return self._matchers.get_right(method, fallback)
	callback = property(get_callback)

	def merge(self, other):
		raise NotImplementedError
		# self._callbacks.update((k,v) for k,v in other._callbacks.iteritems() if k not in self._callbacks)

	def match(self, string):
		match = False
		result = '', False
		for key, matcher in self._matchers.iteritems_l():
			match = matcher.match(string)
			if match:
				result = key, match
				break
		return result

class URLRegistry(object):
	if not g.getattr('URLRegistry', False):
		g.URLRegistry = {}
	URLRegistry = g.URLRegistry
	_prepend = ''

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


	class _matcher(object):
		'internal class'
		def __init__(self, urlreg):
			self._urlreg = urlreg
		def match(self, inp):
			self._inp = inp
			return self
		def __enter__(self):
			return self._urlreg._match(self._inp)
		def __exit__(*args): pass

	def __init__(self, prepend='', default=True, onfail=('page not found', 'text/plain')):
		self._prepend = prepend or self._prepend
		self._default = default
		self._onfail = onfail
		self._matcher = self._matcher(self)
		self.match = self._matcher.match
	def __setitem__(self, name, value):
		self.URLRegistry[name] = value
	def __getitem__(self, name):
		return self.URLRegistry[name].get_callback('main')
	def __delitem__(self, name):
		del self.URLRegistry[name]

	def toggle_default(self):
		self._default = not self._default
	def get_default(self):
		return self._default
	def set_default(self, value):
		self._default = bool(value)
	default = property(get_default, set_default)

	@staticmethod
	def onfail(inp):
		raise responsecodes.NotFoundError(inp)

	@staticmethod
	def onfail1(m1,m2):
		raise responsecodes.HTTPResponseCode, 'Method mismatch: %s, %s' % (m1,m2)

	def execute(self, inp, fallback=None, **kw):
		result = None

		with self.match(inp) as (sub, groups, url):
			if url is not None:
				ks = groups.keys()
				args = listops.adjust(groups, kw)
				cb = url.get_callback(sub, fallback='main')
				args['reverseinfo'] = (url.name, dict( (k, args[k]) for k in ks))
				result = partial(cb, **args)

		if result is None and self._default is True:
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
	def reverselookup(cls, _name, *args, **kwargs):
		_name = _name.split('/',1)
		if len(_name) == 1: _name.append('main')
		url = cls.get(_name[0], None)
		if url is not None:
			result = cls.reverse_helper(url.get_matcher(_name[1]), *args, **kwargs)
			result = str.join('', (cls._prepend, result))
		else:
			result = '/error/'
		return result

	def is_reachable(self, url):
		with self.match(url) as (a,b):
			return a != None and b != None

	@classmethod
	def reverse_helper(cls, regex, *args, **kwargs):
		mc = MatchChecker(args, kwargs)
		result = re.sub(r'\(([^)]+)\)', mc, regex.pattern)
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
		self.args = emen2.util.datastructures.IndexedListIterator( (str(x) for x in args) )
		self.kwargs = dict(  ( x, str(y) ) for x, y in kwargs.items()  )
		self.used_kwargs = set([])

	def get_kwarg(self, name):
		result = self.kwargs.get(name)
		if result is None: result = self.args.next()
		else: self.used_kwargs.add(name)
		return result

	def get_unused_kwargs(self):
		return dict( (k,v) for k,v in self.kwargs.iteritems() if k not in self.used_kwargs )


	NAMED_GROUP = re.compile(r'^\?P<(\w+)>(.*?)$', re.UNICODE)
	def __call__(self, match_obj):
		grouped = match_obj.group(1)
		m = self.NAMED_GROUP.search(grouped)

		if m:
			value, test_regex = self.get_kwarg(m.group(1)), m.group(2)
		else:
			value, test_regex = self.lis.next(), grouped # get_next_posarg(), grouped
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
__version__ = "$Revision$".split(":")[1][:-1].strip()
