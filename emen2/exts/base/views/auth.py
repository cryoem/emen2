# $Id$
from emen2.web.view import View

@View.register
class Auth(View):

    @View.add_matcher(r'^/auth/login/$')
    def login(self, username=None, password=None, msg='', errmsg='', **kwargs):
        self.template = '/auth/login'
        self.title = 'Login'
        self.ctxt["username"] = username
        if username != None:
            ctxid = self.db.auth.login(username, password, host=self.request_host)
            self.notify('Successfully logged in.')
            self.set_header('X-Ctxid', ctxid)
            self.redirect('/')

    @View.add_matcher(r'^/auth/logout/$')
    def logout(self, msg='', **kwargs):
        self.template = '/auth/login'
        self.title = 'Logout'
        self.db.auth.logout()
        self.notify('Successfully logged out.')
        self.set_header('X-Ctxid', '')

    @View.add_matcher(r'^/auth/password/change/$', name='password/change')
    def setpassword(self, **kwargs):
        self.template = '/auth/password.change'
        self.title = "Password Change"

        name = kwargs.pop("name",None) or self.db.auth.check.context()[0]
        opw = kwargs.pop("opw",None)
        on1 = kwargs.pop("on1",None)
        on2 = kwargs.pop("on2",None)

        self.ctxt['name'] = name
        if not on1 and not on2:
            pass

        elif on1 != on2:
            self.notify("New passwords did not match", error=True)

        else:
            try:
                self.db.user.setpassword(opw, on1, name=name)
                self.notify("Password changed successfully.")
            except Exception, errmsg:
                self.notify(errmsg, error=True)

    @View.add_matcher(r'^/auth/password/reset/$', name='password/reset')
    @View.add_matcher(r'^/auth/password/reset/(?P<name>.+)/(?P<secret>\w+)/$', name='password/reset/confirm')
    def resetpassword(self, email=None, name=None, secret=None, newpassword=None, **kwargs):
        self.template = '/auth/password.reset'
        self.title = "Reset Password"
        self.ctxt['name'] = name
        self.ctxt['email'] = email
        self.ctxt['secret'] = secret
        self.ctxt['newpassword'] = ''
        if name and secret and newpassword:
            try:
                self.db.user.setpassword(oldpassword=None, newpassword=newpassword, secret=secret, name=name)
                self.notify('The password for your account has been changed.')
            except Exception, errmsg:
                self.notify(errmsg, error=True)

        elif email:
            try:
                self.db.user.resetpassword(email)
                self.notify('Instructions for resetting your password have been sent to %s.'%email)
            except Exception, errmsg:
                self.notify(errmsg, error=True)

    @View.add_matcher(r'^/auth/email/change/$', name='email/change')
    def setemail(self, **kwargs):
        self.template = '/auth/email.change'
        self.title = "Change Email"

        name = kwargs.get("name") or self.db.auth.check.context()[0]
        opw = kwargs.get('opw', '')
        email = kwargs.get('email', '')

        self.ctxt['email'] = email

        if email:
            try:
                user = self.db.user.setemail(email, password=opw, name=name)
                if email == user.email:
                    self.notify('Email address successfully updated to %s.'%user.email)
                else:
                    self.notify('A verification email has been sent to %s.'%email)
            except Exception, errmsg:
                self.notify(errmsg, error=True)

    @View.add_matcher(r'^/auth/email/verify/(?P<email>.+)/(?P<secret>\w+)/$', name='email/verify')
    def verifyemail(self, email=None, secret=None, **kwargs):
        self.template = '/auth/email.verify'
        self.title = "Verify Email"

        if email and secret:
            try:
                user = self.db.user.setemail(email, secret=secret)
                self.notify("The email address for your account has been changed to %s"%user.email)
            except Exception, errmsg:
                self.notify(errmsg, error=True)


__version__ = "$Revision$".split(":")[1][:-1].strip()
