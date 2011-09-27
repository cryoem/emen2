# $Id$
import re
import sre_parse
import cgi
import contextlib

from functools import partial
from itertools import izip

import emen2.web.events
import emen2.util.registry
import emen2.util.datastructures
import emen2.web.events
from emen2.web import responsecodes
from emen2.util import listops

import emen2.db.config
g = emen2.db.config.g()


def resolve(name=None, path=None):
	"""Resolve a route using either a route name or path URI.
	This method returns a callable, and any keywords parsed from the path URI.
	Bind the DB handle by passing it to the callable. This will produce a second
	callable that will instantiate the View and run the View's method.

	Example:
	
	# Get the callback
	cb, kwargs = routing.resolve(path='/record/1')

	# Update the keyword arguments
	kwargs['blah'] = True

	# Create the view and run the routed method
	view = cb(db=db)(**kwargs)

	# Render the View
	print view	
	"""
	return URLRegistry.resolve(name=name, path=path)



def execute(_execute_name, db=None, *args, **kwargs):
	"""Find and execute a route by name.
	The route name (e.g. 'Home/main') must be the first positional argument.
	"""
	cb, matched = URLRegistry.resolve(name=_execute_name)
	matched.update(kwargs)
	view = cb(db=db)(*args, **kwargs)
	return view
	
	
def execute_path(_execute_path, db=None, *args, **kwargs):
	"""Find and execute a route by a path URI.
	The route path (e.g. '/home/') must be the first positional argument.
	"""	
	cb, matched = URLRegistry.resolve(path=_execute_path)
	matched.update(kwargs)
	view = cb(db=db)(*args, **kwargs)
	return view



def reverse(*args, **kwargs):
	pass
	

def add(*args, **kwargs):
	pass	
	

class URL(object):
	"""Private"""
	
	def __init__(self, name, matcher, cb):
		print "URL:", name, matcher, cb
		self.name = name
		if not hasattr(matcher, 'match'):
			matcher = re.compile(matcher)
		self.matcher = matcher
		self.cb = cb

	def match(self, path):
		result = None
		match = self.matcher.match(path)
		if match:
			result = match.groupdict()
		return result


@emen2.util.registry.Registry.setup
class URLRegistry(emen2.util.registry.Registry):
	"""Private"""
	
	_prepend = ''
	events = emen2.web.events.EventRegistry()
	child_class = URL

	def __init__(self, prepend='', default=True):
		self._prepend = prepend or self._prepend
		self._default = default

	# Default route
	def get_default(self):
		return self._default
	
	def set_default(self, value):
		self._default = bool(value)
	
	default = property(get_default, set_default)


	# Not Found
	@staticmethod
	def onfail(inp):
		raise responsecodes.NotFoundError(inp)


	# Find a match for a path
	@classmethod
	def resolve(cls, path=None, name=None):
		if (not path and not name) or (path and name):
			raise ValueError, "You must specify either a path or a name"

		# print "Resolving...", path
		# Return a callback and found arguments
		result = None, None

		# Look at all the URLs in the registry
		for url in cls.registry.values():
			# Return a result if found
			# print "Checking:", url.name
			if path:
				tmp = url.match(path)
				if tmp != None:
					return url.cb, tmp
			elif name:
				if name == url.name:
					return url.cb, {}

		raise responsecodes.NotFoundError(path or name)


	# Test resolve a route
	@classmethod
	def is_reachable(cls, url):
		cb, groups = cls.resolve(url)
		return cb != None and groups != None


	# Registration
	@classmethod
	def register(cls, url):
		'''Add a URL object to the registry.  If a URL with the same "name" is already
		registered, merge the two into the previously registered one.

		@returns true if a url was already registered with the same name
		'''
		p = cls()
		url = emen2.util.registry.Registry.register(p, url)
		cls.events.event('web.routing.url.register')(url)
		return url


	# Reverse lookup
	@classmethod
	def reverse(cls, _name, *args, **kwargs):
		'''reverse: take a name and arguments, and return a url'''
		return '/error'
		
		_name = _name.split('/',1)
		if len(_name) == 1: _name.append('main')
		url = cls.get(_name[0], None)
		result = '/error/'
		if url is not None:
			result = cls._reverse_helper(url.get_matcher(_name[1]), *args, **kwargs)
			result = str.join('', (cls._prepend, result))

		return result


	@classmethod
	def _reverse_helper(cls, regex, *args, **kwargs):
		mc = MatchChecker(args, kwargs)
		result = re.sub(r'\(([^)]+)\)', mc, regex.pattern)

		qs = '&'.join( '%s=%s' % (k,v) for k,v in mc.get_unused_kwargs().items() )
		result = [result.replace('^', '').replace('$', ''),qs]
		if qs == '':
			result.pop()

		return '?'.join(result)




################################
# Modified code from Django

class NoReverseMatch(Exception):
	pass


class MatchChecker(object):
	"Class used in reverse RegexURLPattern lookup."
	def __init__(self, args, kwargs):
		self.args = emen2.util.datastructures.IndexedListIterator( (str(x) for x in args) )
		self.kwargs = dict(  ( x, str(y) ) for x, y in kwargs.items()  )
		self.used_kwargs = set([])

	def get_arg(self, name):
		result = self.kwargs.get(name)
		if result is None:
			result = self.args.next()
		else:
			self.used_kwargs.add(name)
		return result

	def get_unused_kwargs(self):
		return dict( (k,v) for k,v in self.kwargs.iteritems() if k not in self.used_kwargs )

	NAMED_GROUP = re.compile(r'^\?P<(\w+)>(.*?)$', re.UNICODE)

	def __call__(self, match_obj):
		grouped = match_obj.group(1)
		m = self.NAMED_GROUP.search(grouped)

		if m:
			value, test_regex = self.get_arg(m.group(1)), m.group(2)
		else:
			value, test_regex = self.args.next(), grouped

		if value is None:
			raise NoReverseMatch('Not enough arguments passed in')

		if not re.match(test_regex + '$', value, re.UNICODE):
			raise NoReverseMatch("Value %r didn't match regular expression %r" % (value, test_regex))

		return force_unicode(value)


def force_unicode(string):
	result = string
	if isinstance(result, unicode):
		return result
	elif hasattr(result, '__unicode__'):
		return unicode(result)
	else:
		return unicode(result, 'utf-8', errors='replace')



if __name__ == '__main__':
	from emen2.util.datastructures import doubledict
	print doubledict()
	a = URL('test', GET=('asda(?P<asdasd>sd)', lambda *args, **kwargs: (args, kwargs)))
	print a.match('asdasd')[1].groupdict()
	ur = URLRegistry();ur.register(a)


__version__ = "$Revision$".split(":")[1][:-1].strip()
