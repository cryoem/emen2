# $Id$
'''
Module contents:

I. Views
    - class :py:class:`TemplateView`
    - class :py:class:`View`
'''

import sys
import os
import time
import collections
import functools

import jsonrpc.jsonutil

# emen2 imports
import emen2.web.routing
import emen2.web.resource
import emen2.db.config
import emen2.db.log


##### I. Views #####

class TemplateContext(collections.MutableMapping):
    '''Template Context'''

    def __init__(self, d=None):
        self.__dict = {}
        self.__dict['ctxt'] = self
        self.__dict.update(d or {})
        
        self.notify = []
        self.errors = []
        self.title = 'No title'
        self.template = '/simple'
        self.version = emen2.__version__

    def __getitem__(self, n):
        return self.__dict[n]

    def __setitem__(self, n, v):
        self.__dict[n] = v

    def __delitem__(self, n):
        del self.__dict[n]

    def __len__(self):
        return len(self.__dict)

    def __iter__(self):
        return iter(self.__dict)

    def __repr__(self):
        return '<TemplateContext: %r>'%self.__dict

    def copy(self):
        return TemplateContext(self.__dict)

    def set(self, name, value=None):
        self[name] = value

    def reverse(self, _name, *args, **kwargs):
        """Create a URL given a view Name and arguments"""
        
        host = emen2.db.config.get('network.EMEN2HOST', 'localhost')
        port = emen2.db.config.get('network.EMEN2PORT', 80)
        full = kwargs.pop('_full', False)

        result = emen2.web.routing.reverse(_name, *args, **kwargs)
        result = result.replace('//','/')
        if full:
            result = 'http://%s:%s%s' % (host, port, result)

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
        lambda self: self.ctxt.title,
        lambda self, value: setattr(self.ctxt, "title", value))

    template = property(
        lambda self: self.ctxt.template,
        lambda self, value: setattr(self.ctxt, "template", value))

    def __init__(self, db=None, *args, **blargh):
        super(TemplateView, self).__init__()

        # Database connection
        self.db = db

        # Template Context
        # Init context with headers, errors, etc.
        # Then update with any extra arguments specified.
        self.ctxt = TemplateContext()
        self.ctxt.update(dict(
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

    def notify(self, msg, error=False):
        if not msg:
            return
        if error:
            self.ctxt.errors.append(msg)            
        else:
            self.ctxt.notify.append(msg)

    def simple(self, title=None, content=None):
        self.template = '/simple'
        self.title = title
        self.ctxt['content'] = content

    def error(self, msg):
        '''Set the output to a simple error message.'''
        self.template = "/errors/error"
        self.title = 'Error'
        self.ctxt['errmsg'] = msg

    def redirect(self, redirect, title='Redirect', content='', auto=True, showlink=True):
        '''Redirect by setting Location header and
        using the redirect template'''
        content = content or """<p>Please <a href="%s">click here</a> if the page does not automatically redirect.</p>"""%(redirect)
        self.template = '/redirect'
        self.title = title
        self.ctxt['content'] = content        
        self.ctxt['showlink'] = showlink
        redirect = redirect or '/'
        self.ctxt['redirect'] = redirect
        if auto:
            self._redirect = redirect.replace('//','/')

    def get_data(self):
        '''Render the template'''
        return emen2.db.config.templates.render_template(self.ctxt.template, self.ctxt)




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
            USER = user,
            ADMIN = admin,
            DB = self.db
        ))


__version__ = "$Revision$".split(":")[1][:-1].strip()
