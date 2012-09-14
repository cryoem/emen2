# $Id$
'''
Module contents:

I. Views
    - class :py:class:`TemplateView`
    - class :py:class:`View`

II. View Plugins
    - class :py:class:`ViewPlugin`
    - class :py:class:`AdminView`
    - class :py:class:`AuthView`

'''

import sys
import os
import time
import collections
import functools

import jsonrpc.jsonutil

# emen2 imports
import emen2.util.listops
import emen2.web.routing
import emen2.web.resource
import emen2.db.config
import emen2.db.log


# Exported classes
__all__ = ['TemplateView', 'View', 'ViewPlugin', 'AdminView', 'AuthView']


##### I. Views #####

class TemplateContext(collections.MutableMapping):
    '''Template Context'''

    host = emen2.db.config.get('network.EMEN2HOST', 'localhost')
    port = emen2.db.config.get('network.EMEN2PORT', 80)
    
    def __init__(self, base=None):
        self.__base = {}
        self.__dict = self.__base.copy()
        self.__dict['ctxt'] = self

    def __getitem__(self, n):
        return self.__dict[n]

    def __setitem__(self, n, v):
        self.__dict[n] = v
        self.__dict.update(self.__base)

    def __delitem__(self, n):
        del self.__dict[n]
        self.__dict.update(self.__base)

    def __len__(self):
        return len(self.__dict)

    def __iter__(self):
        return iter(self.__dict)

    def __repr__(self):
        return '<TemplateContext: %r>' % self.__dict

    def copy(self):
        new = TemplateContext(self.__base)
        new.__dict.update(self.__dict)
        return new

    def set(self, name, value=None):
        self[name] = value

    def reverse(self, _name, *args, **kwargs):
        """Create a URL given a view Name and arguments"""

        full = kwargs.pop('_full', False)
        # webroot = emen2.db.config.get('network.EMEN2WEBROOT', '')

        result = emen2.web.routing.reverse(_name, *args, **kwargs)
        result = result.replace('//','/')
        if full:
            result = 'http://%s:%s%s' % (self.host, self.port, result)

        containsqs = '?' in result
        if not result.endswith('/') and not containsqs:
            result = '%s/' % result
        elif containsqs and '/?' not in result:
            result = result.replace('?', '/?', 1)

        return result



class TemplateView(emen2.web.resource.EMEN2Resource):
    '''An EMEN2Resource class that renders a result using a template.'''

    # Basic properties
    title = property(
        lambda self: self.ctxt.get('title'),
        lambda self, value: self.ctxt.set('title',value))

    template = property(
        lambda self: self.ctxt.get('template', '/simple'),
        lambda self, value: self.ctxt.set('template', value))


    def __init__(self, db=None, *args, **blargh):
        super(TemplateView, self).__init__()

        # Database connection
        self.db = db

        # Notifications and errors
        self._notify = []
        self._errors = []

        # Template Context
        # Init context with headers, errors, etc.
        # Then update with any extra arguments specified.
        self.ctxt = TemplateContext()
        self.ctxt.update(dict(
            title = '',
            NOTIFY = self._notify,
            ERRORS = self._errors,
            REQUEST_METHOD = self.request_method,
            REQUEST_LOCATION = self.request_location,
            REQUEST_HEADERS = self.request_headers,
            VERSION = emen2.__version__,
            EMEN2WEBROOT = emen2.db.config.get('network.EMEN2WEBROOT'),
            EMEN2DBNAME = emen2.db.config.get('customization.EMEN2DBNAME'),
            EMEN2LOGO = emen2.db.config.get('customization.EMEN2LOGO'),
            BOOKMARKS = emen2.db.config.get('bookmarks.BOOKMARKS', [])            
        ))

        # ETags
        self.etag = None

    def init(self, *arrgghs, **blarrgghs):
        pass


    #### Output methods #####

    def error(self, msg):
        '''Set the output to a simple error message.'''
        self.template = "/errors/error"
        self.title = 'Error'
        self.ctxt['errmsg'] = msg

    def redirect(self, location, title='Redirect', content='', auto=True, showlink=True):
        '''Redirect by setting Location header and
        using the redirect template'''
        content = content or """<p>Please <a href="%s">click here</a> if the page does not automatically redirect.</p>"""%(location)
        self.template = '/redirect'
        self.ctxt['title'] = title
        self.ctxt['content'] = content        
        self.ctxt['showlink'] = showlink
        location = location or '/'
        self.ctxt['location'] = location
        if auto:
            self.headers['Location'] = location.replace('//','/')

    def get_data(self):
        '''Render the template'''
        return emen2.db.config.templates.render_template(self.template, self.ctxt)




class View(TemplateView):
    '''A View that checks some DB specific details'''

    def init(self, *args, **kwargs):
        '''Run this before the requested view method.'''
        super(View, self).init(*args, **kwargs)
        user = {}
        admin = False
        ctx = getattr(self.db, '_getctx', lambda:None)()
        try:
            user = ctx.db.user.get(ctx.username)
            admin = ctx.checkadmin()
        except:
            pass

        self.ctxt.update(dict(
            HOST = getattr(ctx, 'host', None),
            USER = user,
            ADMIN = admin,
            DB = self.db
        ))



##### II. View plugins #####

# class ViewPlugin(object):
#     '''Parent class the interface for View plugins
# 
#     To write a view plugin, subclass this class and provide a iterable
#     classattribute called "preinit" which contains a list of methods
#     executed before the view method is called
# 
#     .. py:function:: preinit(self)'''
# 
#     @classmethod
#     def attach(cls, view):
#         '''Decorate a class with this method to add a :py:class:`ViewPlugin` to the class'''
#         view.preinit = view.preinit[:]
#         view.preinit.extend(cls.preinit)
#         return view
# 
# 
# class AdminView(ViewPlugin):
#     '''A :py:class:`ViewPlugin` which only allows Administrators to access a view'''
# 
#     preinit = []
# 
#     @preinit.append
#     def checkadmin(self):
#         context = self.db._getctx()
#         if not context.checkadmin():
#             raise emen2.web.responsecodes.ForbiddenError, 'User %r is not an administrator.' % context.username
# 
# 
# class AuthView(ViewPlugin):
#     '''A :py:class:`ViewPlugin` which only allows Authenticated Users to access a view'''
# 
#     preinit = []
# 
#     @preinit.append
#     def checkadmin(self):
#         context = self.db._getctx()
#         if not 'authenticated' in context.groups:
#             raise emen2.web.responsecodes.ForbiddenError, 'User %r is not authenticated.' % context.username


__version__ = "$Revision$".split(":")[1][:-1].strip()
