# $Id: responsecodes.py,v 1.9 2012/07/28 06:31:19 irees Exp $
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
    '''Set the response status to 501'''
    code = 501


class HTTPCancelledResponse(HTTPResponseCode):
    '''Set the response status to 500'''
    code = 500


class HTTP200Response(HTTPResponseCode):
    '''Set the response status to 200'''
    code = 200


class HTTP300Response(HTTPResponseCode):
    '''Set the response status to 300'''
    code = 300


class HTTPMovedPermanently(HTTP300Response):
    '''Set the response status to 301.

    If this is caught the resource should send a redirect'''
    code = 301
    def __init__(self, msg, dest):
        HTTP300Response.__init__(self, msg)
        self.headers['Location'] = unicode(dest).encode('utf-8')


class HTTPFound(HTTP300Response):
    '''Set the response status to 302

    If this is caught the resource should send a redirect'''
    code = 302
    def __init__(self, msg, dest):
        HTTP300Response.__init__(self, msg)
        self.headers['Location'] = unicode(dest).encode('utf-8')


class HTTPNotModified(HTTP300Response):
    '''Set the response status to 304'''
    code = 304


class HTTP400Response(HTTPResponseCode):
    '''Set the response status to 400'''
    code = 400


class UnauthorizedError(HTTP400Response):
    '''Set the response status to 401'''
    code = 401


class ForbiddenError(HTTP400Response):
    '''Set the response status to 403'''
    code = 403


class NotFoundError(HTTP400Response):
    '''Set the response status to 404 (Not Found)'''
    title = 'Page Not Found'
    msg = 'The requested URL (%s) was not found on this server.'
    code = 404
    def __init__(self, msg):
        self.msg %= msg
        HTTP400Response.__init__(self, self.msg)


class MethodNotAllowedError(HTTP400Response):
    '''Set the response status to 405'''
    title = 'Method Not Allowed'
    msg = 'Method Not Allowed: %r'
    code = 405
    def __init__(self, msg):
        self.msg %= msg
        HTTP400Response.__init__(self, self.msg)


class GoneError(HTTP400Response):
    '''Set the response status to 410'''
    code = 410



__version__ = "$Revision: 1.9 $".split(":")[1][:-1].strip()
