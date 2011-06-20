# $Id$
import unittest
import mock
import sys
import emen2.db.database
import emen2.db.proxy
import emen2.db.config
import emen2.web.view

class TestView(unittest.TestCase):
	@mock.patch('emen2.db.database.DB', new=mock.Mock())
	@mock.patch('emen2.db.proxy.DBProxy', new=mock.Mock())
	@mock.patch('emen2.db.config.g', new=mock.Mock())
	def setUp(self, *args):
		self.view = emen2.web.view.View(db=mock.Mock())

	def testView(self):
		self.assert_(hasattr(self.view, 'template'))
		self.assert_(isinstance(self.view.template, basestring))
		self.assert_(hasattr(self.view, 'mimetype'))
		self.assert_(isinstance(self.view.mimetype, basestring))
		self.assert_(issubclass(self.view.js_files, emen2.web.view.BaseJS))
		self.assert_(hasattr(self.view, 'css_files'))
		self.assert_(issubclass(self.view.css_files, emen2.web.view.BaseCSS))
		self.assertEqual(self.view.page, None)

	def testMimetype(self):
		mimetype = 'text/xml'
		self.view.mimetype = mimetype
		self.assertEqual(self.view.mimetype, mimetype)
		self.assertEqual(self.view.headers['content-type'], mimetype)

	def testTemplate(self):
		template = '/page/page'
		self.view.template = template
		self.assertEqual(self.view.template, template)
	
	@mock.patch('emen2.db.database.DB', new=mock.Mock())
	@mock.patch('emen2.db.proxy.DBProxy', new=mock.Mock())
	@mock.patch('emen2.db.config.g', new=mock.Mock())
	def testRaw(self):
		op = self.view.page
		page = 'asdasdasd'
		self.view.page = page
		self.assertEqual(self.view.page, page)
		self.assertFalse(self.view.is_raw())
		self.view.make_raw()
		self.assertTrue(self.view.is_raw())
		self.assertEqual(str(self.view), page)
		self.assertTrue(len(list(self.view)) == 2)

if __name__ == '__main__':
	unittest.main()
__version__ = "$Revision$".split(":")[1][:-1].strip()
