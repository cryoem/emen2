from emen2.web import routing
import unittest

class TestURL(unittest.TestCase):
	def test_init(self):
		a = 3
		name = 'name'
		matcher = 'matcher'
		sub = 'main'
		url = routing.URL(name, **{sub:(matcher, lambda: a)})

		self.assertEqual(name, url.name)
		self.assertTrue(url.get_matcher(sub) is not None)
		self.assertEqual(matcher, url.get_matcher(sub).pattern)

	def test_match(self):
		name = 'main'
		match = '213'
		url = routing.URL(name, **{name:('(?P<a>[0-9][0-9]+)', lambda a:int(a))})

		sub, mtch = url.match('213')
		self.assertEqual(sub, name)
		self.assertNotEqual(mtch, False)
		self.assertEqual(mtch.groupdict()['a'], match)
		self.assertEqual(url.get_callback(sub)(match), int(match))




class TestRouting(unittest.TestCase):
	def setUp(self):
		self.URLRegistry = routing.URLRegistry()

		def test(format, **a):
			return format % a

		with self.URLRegistry.url('Test') as url:
			url.add_matcher('main', r'(?P<areacode>[0-9]{3}?) *(?P<prefix>[0-9]{3})[- ]*(?P<suffix>[0-9]{4})', test)
			url.add_matcher('sub1', r'(?P<zipcode>[0-9]{5})$', test)
			url.add_matcher('sub2', r'(?P<areacode>[0-9]{3}?)/(?P<prefix>[0-9]{3})/(?P<suffix>[0-9]{4})', test)

	def test_register_1(self):
		URL = routing.URL('Test1', main=('^/$', lambda x, **_: x))
		self.URLRegistry.register(URL)

		x=1
		self.assertEqual(x, self.URLRegistry.execute('/', x=x)())
		self.assertEqual(x, self.URLRegistry.execute('/')(x=x))

	def test_register_2(self):
		no = '1235550100'
		result = '(123) 555-0100'
		format = '(%(areacode)s) %(prefix)s-%(suffix)s'

		self.assertEqual(result, self.URLRegistry.execute(no, format='(%(areacode)s) %(prefix)s-%(suffix)s')())
		self.assertEqual(result, self.URLRegistry.execute(no)(format='(%(areacode)s) %(prefix)s-%(suffix)s'))

	def test_register_3(self):
		URL1 = routing.URL('Test1', main=('^/$', lambda x, **_: x))
		self.URLRegistry.register(URL1)

		URL2 = routing.URL('Test1', sub=('^/asd$', lambda x, **_: x*2))
		self.URLRegistry.register(URL2)

		x=1
		self.assertEqual(x, self.URLRegistry.execute('/', x=x)())
		self.assertEqual(x, self.URLRegistry.execute('/')(x=x))

		self.assertEqual(x*2, self.URLRegistry.execute('/asd', x=x)())
		self.assertEqual(x*2, self.URLRegistry.execute('/asd')(x=x))

	def test_reverse_1(self):
		zipcode = 12345
		reversed = self.URLRegistry.reverselookup('Test/sub1', zipcode=zipcode)
		reconstituted = int(self.URLRegistry.execute(reversed)('%(zipcode)s'))
		self.assertEqual(zipcode, reconstituted)

	def test_reverse_2(self):
		areacode = '123'
		prefix = '555'
		suffix = '0101'
		reversed = self.URLRegistry.reverselookup('Test/sub2', areacode=areacode, prefix=prefix, suffix=suffix)
		reconstituted = self.URLRegistry.execute(reversed)('%(areacode)s %(prefix)s %(suffix)s').split()
		for x,y in zip([areacode, prefix, suffix], reconstituted):
			self.assertEqual(x,y)

if __name__ == '__main__':
	unittest.main()
