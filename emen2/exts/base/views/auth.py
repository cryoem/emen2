# $Id$
from emen2.web.view import View

@View.register
class Auth(View):

    # @View.provides('auth_login')
    @View.add_matcher(r'^/auth/login/$')
    def login(self, username=None, password=None, msg='', errmsg='', location=None, **kwargs):
        self.template = '/auth/login'
        self.title = 'Login'
        location = location or self.ctxt['EMEN2WEBROOT']
        if 'auth' in location or not location:
            location = self.ctxt['EMEN2WEBROOT']

        self.ctxt["username"] = username
        self.ctxt['location'] = location

        ctxid = None
        if username != None:
            ctxid = self.db.auth.login(username, password, host=self.request_host)
            msg = 'Successfully logged in'
            self.set_header('X-Ctxid', ctxid)
            self.redirect(location or '/')
            # self.set_header('Location', location or '/')

        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.notify.append(errmsg)




    # @View.provides('auth_logout')
    @View.add_matcher(r'^/auth/logout/$')
    def logout(self, msg='', location=None, **kwargs):
        self.template = '/auth/login'
        self.title = 'Logout'
        msg = ''
        errmsg = ''

        location = location or self.ctxt['EMEN2WEBROOT']
        if 'auth' in location or not location:
            location = self.ctxt['EMEN2WEBROOT']

        self.ctxt['location'] = location
        try:
            self.db.auth.logout()
            msg = 'Successfully logged out'
        except Exception, errmsg:
            pass

        self.set_header('Location', location or '/')
        self.set_header('X-Ctxid', '')

        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.errors.append(errmsg)



    @View.add_matcher(r'^/auth/password/change/$', name='password/change')
    def setpassword(self, location=None, **kwargs):
        self.template = '/auth/password.change'
        self.title = "Password Change"
        self.ctxt['location'] = location

        name = kwargs.pop("name",None) or self.db.auth.check.context()[0]
        opw = kwargs.pop("opw",None)
        on1 = kwargs.pop("on1",None)
        on2 = kwargs.pop("on2",None)

        msg = ''
        errmsg = ''

        self.ctxt['name'] = name

        if not on1 and not on2:
            pass

        elif on1 != on2:
            errmsg = "New passwords did not match"

        else:
            try:
                self.db.user.setpassword(opw, on1, name=name)
                msg = "Password changed successfully"
            except Exception, errmsg:
                pass

        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.errors.append(errmsg)



    @View.add_matcher(r'^/auth/password/reset/$', name='password/reset')
    @View.add_matcher(r'^/auth/password/reset/(?P<email>.+)/(?P<secret>\w+)/$', name='password/reset/confirm')
    def resetpassword(self, location=None, email=None, secret=None, newpassword=None, **kwargs):
        self.template = '/auth/password.reset'
        self.title = "Reset Password"
        self.ctxt['email'] = email
        self.ctxt['secret'] = secret
        self.ctxt['newpassword'] = ''
        self.ctxt['location'] = location
        msg = ''
        errmsg = ''

        if email:
            if secret and newpassword:
                try:
                    name = self.db.user.setpassword(oldpassword=None, newpassword=newpassword, secret=secret, name=email)
                    msg = 'The password for your account, %s, has been changed'%name
                except Exception, errmsg:
                    pass

            elif secret and not newpassword:
                # errmsg = "No new password given..."
                pass

            else:
                try:
                    self.db.user.resetpassword(email)
                    msg = 'Instructions for resetting your password have been sent to %s'%email
                except Exception, errmsg:
                    pass

        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.errors.append(errmsg)



    @View.add_matcher(r'^/auth/email/change/$', name='email/change')
    def setemail(self, location=None, **kwargs):
        self.template = '/auth/email.change'
        self.title = "Change Email"
        self.ctxt['location'] = location

        name = kwargs.get("name") or self.db.auth.check.context()[0]
        opw = kwargs.get('opw', None)
        email = kwargs.get('email', None)

        self.ctxt['email'] = email
        msg = ''
        errmsg = ''

        if email:
            try:
                ret = self.db.user.setemail(email, password=opw, name=name)
                if email == ret:
                    msg = 'Email address successfully updated to %s'%ret
                else:
                    msg = 'A verification email has been sent to %s'%email
                    
            except Exception, errmsg:
                ret = None


        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.errors.append(errmsg)



    @View.add_matcher(r'^/auth/email/verify/(?P<email>.+)/(?P<secret>\w+)/$', name='email/verify')
    def verifyemail(self, location=None, email=None, secret=None, **kwargs):
        self.template = '/auth/email.verify'
        self.title = "Verify Email"
        msg = ''
        errmsg = ''

        if email and secret:
            try:
                ret = self.db.user.setemail(email, secret=secret)
                msg = "The email address for your account has been changed to %s"%ret
            except Exception, errmsg:
                pass

        if msg:
            self.ctxt.notify.append(msg)
        if errmsg:
            self.ctxt.errors.append(errmsg)



__version__ = "$Revision$".split(":")[1][:-1].strip()
