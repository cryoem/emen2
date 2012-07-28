# $Id$
import unittest
import mock
from emen2.web import responsecodes

class TestResponseCodes(unittest.TestCase):
    def setUp(self):
        self.msg = 'This is a message'

    def testHttpResponseCode(self):
        rc = responsecodes.HTTPResponseCode(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.title, None)
        self.assertEqual(rc.headers, {})

    def testMethodNotSupported(self):
        rc = responsecodes.MethodNotSupported(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 501)

    def testHTTP200Response(self):
        rc = responsecodes.HTTP200Response(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 200)

    def testHTTP300Response(self):
        rc = responsecodes.HTTP300Response(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 300)

    def testHTTPMovedPermanently(self):
        dest = u'http://example.com'.encode('utf-8')
        rc = responsecodes.HTTPMovedPermanently(self.msg, dest)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 301)
        self.assertEqual(rc.headers['Location'], dest)

    def testHTTPFound(self):
        dest = u'http://example.com'.encode('utf-8')
        rc = responsecodes.HTTPFound(self.msg, dest)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 302)
        self.assertEqual(rc.headers['Location'], dest)

    def testHTTPNotModified(self):
        rc = responsecodes.HTTPNotModified(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 304)

    def testHTTP400Response(self):
        rc = responsecodes.HTTP400Response(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 400)

    def testUnauthorizedError(self):
        rc = responsecodes.UnauthorizedError(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 401)

    def testForbiddenError(self):
        rc = responsecodes.ForbiddenError(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 403)

    def testNotFoundError(self):
        rc = responsecodes.NotFoundError(self.msg)
        self.assertEqual(rc.msg, responsecodes.NotFoundError.msg % self.msg)
        self.assertEqual(rc.title, responsecodes.NotFoundError.title)
        self.assertEqual(rc.code, 404)

    def testMethodNotAllowedError(self):
        rc = responsecodes.MethodNotAllowedError(self.msg)
        self.assertEqual(rc.msg, responsecodes.MethodNotAllowedError.msg % self.msg)
        self.assertEqual(rc.title, responsecodes.MethodNotAllowedError.title)
        self.assertEqual(rc.code, 405)

    def testGoneError(self):
        rc = responsecodes.GoneError(self.msg)
        self.assertEqual(rc.msg, self.msg)
        self.assertEqual(rc.code, 410)

if __name__ == '__main__':
    unittest.main()

__version__ = "$Revision$".split(":")[1][:-1].strip()
