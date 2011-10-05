# $Id$
'''Contains Classses which should mirror HTTP resoponse codes'''
#NOTE: unittests in tests/responsecodes_test.py -- run after any changes


class HTTPResponseCode(Exception):
	'''Base class for setting HTTP Response codes.  If a view
	raises one of these, the resource should catch it and set
	the response code appropriately'''
	title = None
	code = 500
	def __init__(self, msg):
		Exception.__init__(self, msg)
		self.msg = msg
		self.headers = {}


class MethodNotSupported(HTTPResponseCode):
	code = 501


class HTTPCancelledResponse(HTTPResponseCode):
	code = 500
	

class HTTP200Response(HTTPResponseCode):
	code = 200


class HTTP300Response(HTTPResponseCode):
	code = 300


class HTTPMovedPermanently(HTTP300Response):
	'''If this is caught the resource should send a redirect'''
	code = 301
	def __init__(self, msg, dest):
		HTTP300Response.__init__(self, msg)
		self.headers['Location'] = unicode(dest).encode('utf-8')


class HTTPFound(HTTP300Response):
	'''If this is caught the resource should send a redirect'''
	code = 302
	def __init__(self, msg, dest):
		HTTP300Response.__init__(self, msg)
		self.headers['Location'] = unicode(dest).encode('utf-8')


class HTTPNotModified(HTTP300Response):
	code = 304


class HTTP400Response(HTTPResponseCode):
	code = 400


class UnauthorizedError(HTTP400Response):
	code = 401


class ForbiddenError(HTTP400Response):
	code = 403


class NotFoundError(HTTP400Response):
	title = 'Page Not Found'
	msg = 'The requested URL (%s) was not found on this server.'
	code = 404
	def __init__(self, msg):
		self.msg %= msg
		HTTP400Response.__init__(self, self.msg)


class MethodNotAllowedError(HTTP400Response):
	title = 'Method Not Allowed'
	msg = 'Method Not Allowed: %r'
	code = 405
	def __init__(self, msg):
		self.msg %= msg
		HTTP400Response.__init__(self, self.msg)


class GoneError(HTTP400Response):
	code = 410



__version__ = "$Revision$".split(":")[1][:-1].strip()