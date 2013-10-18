"""User DBOs."""

import time
import operator
import random
import re
import weakref
import traceback
import random
import string
import email.utils
import uuid

# EMEN2 imports
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.config
import emen2.db.auth

class BaseUser(emen2.db.dataobject.BaseDBObject):
    """Base User DBO, email address, password, first/middle/last name, and displayname.
    
    Passwords are currently hashed with bcrypt. The password is never exposed
    via the API; you have to directly retreive the item from the DB without
    going through get / setContext.
    
    Users also contain a 'secret'. This is used to keep track of password reset
    tokens, approval tokens, etc. Like password, this is never exposed via the API.
    The secret contains (requested action, arguments, time, token). It's managed using
    checksecret, _setsecret, _delsecret.
        
    Password reset are done by setting a secret token with resetpassword(),
    sending the token to the registered email address, and calling setpassword()
    with the token.
    
    Email addresses are validated in a similar way: setemail() sets the token,
    sends it via email to the registered email address, and is provided again
    to setemail() to verify the owner requested the change.
    
    There are many schools of thought on email validation. Technically, the
    only rule is that '@' must be present, and the only foolproof way to
    check an email is to send a message and see if it is received. However,
    modern emails are fairly uniform, and we will use Python's
    email.utils.parseaddr() to validate the input. The result is stored
    lower-case.
    
    The configuration settings security.email_blacklist and
    security.email_whitelist are also applied. These are lists of
    regular expressions checked against the email. Any hit in the
    blacklist will raise an error. If a whitelist is specified, at least
    one hit in the whitelist is required. See also: _validate_email()

    Note: the actual verification email is currently handled in the public API
    methods. See database.py.

    Note: Previously, SHA-1 hashes were used. These accounts are allowed to
    continue operating. In the future, I may add a configuration setting to
    force these passwords to expire, or to provide a migration process to
    bcrypt when a user logs in.
        
    These BaseDBObject methods are overridden:

        init            Init
        setContext      Check read permissions, bind Context, strip out password/secrets.
        validate        Check required parameters.
        checkpassword   Check the password.
        setpassword     Set the password; requires password or secret token.
        resetpassword   Set the password reset secret token.
        setemail        Set the email; requires password and secret token (2 step process.)
        login           Check the password and optionally check account inactivity or expired passwords.
      
    :attr email: email
    :attr password: Hashed password.
    """

    public = emen2.db.dataobject.BaseDBObject.public | set(['email', 'password', 'name_first', 'name_middle', 'name_last', 'displayname', 'secret'])

    def init(self, d):
        super(BaseUser, self).init(d)

        # Email and password
        self.data['email'] = None
        self.data['password'] = None        

        # Names
        self.data['name_first'] = ''
        self.data['name_middle'] = ''
        self.data['name_last'] = ''
        self.data['displayname'] = ''

        # Secret takes the format:
        # action type, args, ctime for when the token is set, and secret
        self.data['secret'] = None

        
    def setContext(self, ctx, hide=True):
        # Hide the secret during setContext.
        super(BaseUser, self).setContext(ctx)
        self.data.pop('secret', None)

    def validate(self):
        """Require email and password to be set."""
        super(BaseUser, self).validate()
        if not self.password: 
            raise self.error('No password set.')
        if not self.email:
            raise self.error('No email set.')

    def isowner(self):
        """Always allow the user to modify their own user DBO."""
        if self.name == self.ctx.username:
            return True
        return super(BaseUser, self).isowner()

    ##### Name and display name #####

    def _set_name_first(self, key, value):
        # These should trigger an update to _set_displayname.
        self._set(key, self._strip(value), self.isowner())
        self._set_displayname(None, None)
    
    def _set_name_last(self, key, value):
        self._set(key, self._strip(value), self.isowner())
        self._set_displayname(None, None)
        
    def _set_name_middle(self, key, value):
        self._set(key, self._strip(value), self.isowner())
        self._set_displayname(None, None)
        
    def _set_displayname(self, key, value):
        self._set('displayname', self.getdisplayname(), self.isowner())

    ##### Login #####

    def login(self, password, events=None):
        # Disabled users cannot login.
        # This needs to work even if there is no Context set.
        # Return a Context?
        if self.get('disabled'):
            raise self.error(e=emen2.db.exceptions.DisabledUserError)

        # Check the password.
        if not self.checkpassword(password):
            raise self.error(e=emen2.db.exceptions.AuthenticationError)

        # Check for expired password or inactive account.
        # These will raise an ExpiredPassword Exception on failure.
        auth = emen2.db.auth.PasswordAuth(name=self.name)
        auth.checkexpired(password, events=events)
        auth.checkinactive(events=events)

    ##### Password methods #####

    def _set_password(self, key, value):
        self.setpassword(value)
        # """Can't set password this way. Use user.setpassword().""" ??
        # return
    
    def _validate_password(self, password, events=None):
        password = unicode(password or '').strip()
        # Validate the new password.
        auth = emen2.db.auth.PasswordAuth()
        hashpassword = auth.validate(password)
        # Check the password hasn't been used recently.
        auth.checkrecycle(password, events=events)
        # Return the password hash.
        return hashpassword

    def setpassword(self, newpassword, password=None, secret=None, events=None):
        """Set the user password.
        
        You must provide either the existing password or an authentication secret.
        """
        # Check that we have permission to update the password.
        # Check that it's:
        #   a new user,
        #   or we know an authentication secret
        #   or we know the existing password, 
        if self.isnew():
            pass
        elif self.checksecret('resetpassword', None, secret):
            pass
        elif self.checkpassword(password):
            pass
        elif self.checkadmin():
            pass
        else:
            raise self.error(e=emen2.db.exceptions.AuthenticationError)

        hashpassword = self._validate_password(newpassword, events=events)
        
        # Remove any secrets, if set.
        self._delsecret() 
        # Finally, set the password.
        self._set('password', hashpassword, True)
        
    def checkpassword(self, password):
        """Check the user password."""
        if getattr(self, 'ctx', None):
            if self.ctx.checkadmin():
                return True
        auth = emen2.db.auth.PasswordAuth()
        return auth.check(password, self.password)

    def resetpassword(self):
        """Reset the user password. 

        This creates an internal 'secret' token that can be used to reset a
        password. This should be sent to the user's registered email address.

        The secret must never be accessible via public methods.
        """
        # The second argument should be the email address
        self._setsecret('resetpassword', None)

    ##### email setting/validation #####

    def _set_email(self, key, value):
        self.setemail(value)
    
    def _validate_email(self, value):
        # After a long discussion in #python, it is impossible to validate
        #     emails other than checking for '@'
        # Note: Forcing emails to be stored as lower case.
        value = self._strip(value)
        _, value = email.utils.parseaddr(value)
        value = value.strip().lower()
        if '@' not in value:
            raise self.error("Invalid email: %s"%value)
        
        blacklist = emen2.db.config.get('security.email_blacklist')
        if blacklist and any([re.search(i, value) for i in blacklist]):
            raise self.error("Disallowed email: %s"%value)
        whitelist = emen2.db.config.get('security.email_whitelist')
        if whitelist and not any([re.search(i, value) for i in whitelist]):
            raise self.error("Disallowed email: %s"%value)            
        return value

    def setemail(self, value, password=None, secret=None):
        """Email address must contain '@' and a host. Stored lower-case.

        You must provide either a password, or an authentication secret.
        """
        # Check that:
        #   it's a new user
        #   or we know an authentication secret
        #   or we know the existing password, 
        # Note: admin users always return True for checksecret
        # Note: the auth token is bound both to the method (setemail) and the
        #     specific requested email address.
        value = self._validate_email(value)
        if self.isnew():
            self._set('email', value, self.isowner())
        elif self.checksecret('setemail', value, secret):
            self._delsecret()
            self._set('email', value, True)
        elif self.checkpassword(password):
            self._setsecret('setemail', value)
        else:
            raise self.error(e=emen2.db.exceptions.AuthenticationError)

    ##### Secrets for account password resets #####

    def checksecret(self, action, args, secret):
        secretattr = self.data.get('secret', None)
        if action and secret and secretattr:
            # Maximum age is 1 day.
            age = time.time()-secretattr[3]
            if age >= (60 * 60 * 24):
                return False
            if action == secretattr[0] and args == secretattr[1] and secret == secretattr[2]:
                return True
        return False

    def _setsecret(self, action, args):
        # Generate random secret.
        secret = emen2.db.database.getrandomid()
        self.data['secret'] = (action, args, secret, time.time())

    def _delsecret(self):
        self.data['secret'] = None

    ##### Displayname and profile Record #####

    def getdisplayname(self, lnf=False):
        """Format display name."""
        # Yes, this is not very pretty.
        nf = self.data.get('name_first')
        nm = self.data.get('name_middle')
        nl = self.data.get('name_last')
        if nf and nm and nl:
            if lnf:
                uname = "%s, %s %s" % (nl, nf, nm)
            else:
                uname = "%s %s %s" % (nf, nm, nl)
        elif nf and nl:
            if lnf:
                uname = "%s, %s" % (nl, nf)
            else:
                uname = "%s %s" % (nf, nl)
        elif nl:
            uname = nl
        elif nf:
            uname = nf
        else:
            return self.name
        return uname


class NewUser(BaseUser):
    """New User.
    
    This is a container for signup information. It is convered to a User when
    approved.
    
    The signup information is kept in 'signupinfo'. This will be converted to a
    'person' record when approved.
    
    :attr signupinfo: Dictionary containing signup information.
    """
    public = BaseUser.public | set(['signupinfo'])

    def init(self, d):
        super(NewUser, self).init(d)
        # New users store signup info in a dict,
        #     which is committed as a 'person' record when approved
        self.data['signupinfo'] = {}

    def _validate_signupinfo(self, rec):
        # Check signupinfo
        newsignup = {}
        # Check child recs
        childrecs = rec.pop('childrecs', [])
        childrecs = [self._validate_signupinfo(i) for i in childrecs]        
        # Validate this dict
        if not rec.get('rectype'):
            self.error(msg='No rectype specified!')
        for param, value in rec.items():
            try:
                value = self._validate(param, value)
            except Exception, e:
                raise self.error(msg=e.message)
            newsignup[param] = value
        if childrecs:
            newsignup['childrecs'] = childrecs

        # print "Validated signupinfo:", newsignup
        return newsignup

    def _set_signupinfo(self, key, value):
        self.setsignupinfo(value)

    def setsignupinfo(self, value):
        self._set('signupinfo', self._validate_signupinfo(value), self.isnew() or self.isowner())

class User(BaseUser):
    """User. 
    
    This contains the basic metadata information for a single user account,
    including username, password, primary email address, active/disabled,
    timestamps, and link to more complete user profile. Group membership is
    stored in Group instances, and set here by db.user.get by checking an
    index. If available during db.user.get, a copy of the profile record and
    the user's "displayname" will also be set.

    A User can specify a 'privacy' level as an integer. The default, 0, allows
    other users to see the link to the 'person' record, stored in the 'record'
    parameter. 1 hides the link to anonymous users, 2 hides the link from all
    other users.

    :attr disabled: Disable this account.
    :attr privacy: Privacy level
    :attr record: Record ID containing additional profile information
    :property groups: Set by database when accessed
    :property displayname: User "display name"; set by database when accessed
    """
    
    public = BaseUser.public | set(['privacy', 'disabled', 'record'])

    def init(self, d):
        super(User, self).init(d)
        # Enabled/disabled, privacy level, and record ID pointer
        self.data['disabled'] = False
        self.data['privacy'] = 0
        self.data['record'] = None
        self.groups = set()
        self.userrec = {}

    def setContext(self, ctx, hide=True):
        super(User, self).setContext(ctx)
        admin = self.ctx.checkreadadmin()
        ctxuser = self.ctx.username

        # secret is never made available through normal get().
        self.data.pop('secret', None)

        # Hide the password hash if not root or owner.
        if not (admin or ctxuser == self.name):
            self.data.pop('password', None)

        # If the user has requested privacy, we return only basic info
        if ctxuser == 'anonymous':
            self.data.pop('email', None)
        if not admin and self.name != ctxuser:
            if self.privacy == 2:
                self.data.pop('record', None)
            if self.privacy > 0:
                self.data.pop('email', None)

    def _set_disabled(self, key, value):
        self.disable(value)

    def _set_privacy(self, key, value):
        self.setprivacy(value)
        
    def _set_record(self, key, value):
        # TODO: better validation.
        # Only admin can change profile record.
        self._set(key, self._strip(value), self.ctx.checkadmin())

    ##### Enable/disable #####
    
    def enable(self):
        """Enable the user."""
        self.disable(False)

    def disable(self, state=True):
        """Disable the user."""
        # Only admin can change enabled/disabled
        state = bool(state)
        if self.name == self.ctx.username and state:
            raise self.error("Cannot disable self!")
        self._set('disabled', state, self.ctx.checkadmin())

    def setprivacy(self, privacy):
        """Set privacy level."""
        # Users can set their own privacy level
        privacy = int(privacy)
        if privacy not in [0,1,2]:
            raise self.error("User privacy setting may be 0, 1, or 2.")
        self._set('privacy', privacy, self.isowner())

