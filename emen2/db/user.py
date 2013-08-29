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



# DBO that contains a password and email address
class BaseUser(emen2.db.dataobject.BaseDBObject):
    """Base User DBO, with an email address and a password.
    
    Passwords are currently hashed with bcrypt. The password is never exposed
    via the API; you have to directly retreive the item from the DB without
    going through get/setContext.
    
    Users also contain a 'secret'. This is used to keep track of password reset
    tokens, approval tokens, etc. Like password, this is never exposed via the API.
    The secret contains (requested action, arguments, time, token). It's managed using
    _checksecret, _setsecret, _delsecret.
        
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
        validate        Check required parameters
        checkpassword   Check the password; raise PermissionsError if failed.
        setpassword     Set the password; requires password or secret token.
        resetpassword   Set the password reset secret token.
        setemail        Set the email; requires password and secret token (2 step process.)
        login           Check the password and optionally check account inactivity or expired passwords.
      
    :attr email: email
    :attr password: Hashed password.
    """

    public = emen2.db.dataobject.BaseDBObject.public | set(['email', 'password', 'name_first', 'name_middle', 'name_last', 'displayname'])

    def init(self, d):
        super(BaseUser, self).init(d)

        # Email and password
        self.data['email'] = None
        self.data['password'] = None

        # Secret takes the format:
        # action type, args, ctime for when the token is set, and secret
        self.data['secret'] = None

    def setContext(self, ctx, hide=True):
        super(BaseUser, self).setContext(ctx)
        self.data.pop('secret', None)

    def validate(self):
        super(BaseUser, self).validate()
        if not self.password: 
            traceback.print_stack()
            raise self.error('No password set.')
        if not self.email:
            raise self.error('No email set.')

    def isowner(self):
        if self.name == self.ctx.username:
            return True
        return super(BaseUser, self).isowner()

    ##### Account inactive or expired password #####

    def login(self, password, events=None):
        # Disabled users cannot login.
        # This needs to work even if there is no Context set.
        if self.get('disabled'):
            raise self.error(e=emen2.db.exceptions.DisabledUserError)

        # Check the password. Will raise an exception on failure.
        self.checkpassword(password)

        # Check for expired password.
        # If no events, nothing to do here.
        if not events:
            return

        # Check this account isn't expired.
        expire_initial = emen2.db.config.get('security.password_expire_initial')
        expire = emen2.db.config.get('security.password_expire')
        inactive = emen2.db.config.get('security.user_inactive')

        # Check the password hasn't expired; will raise ExpiredPassword.
        if expire:
            last_password = events.gethistory(param='password', limit=1)
            if last_password:
                last_password = last_password[0][0]
            elif expire_initial:
                raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="Please set a new password before your initial login.", title="Initial login")
            else:
                last_password = self.creationtime
            password_diff = emen2.db.database.utcdifference(last_password)
            # print "last_password?", last_password, password_diff, expire
            if password_diff > expire:
                emen2.db.log.security("Login failed: expired password for %s, password age was %s, max age is %s"%(self.name, password_diff, expire))
                raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="This password has expired.")        

        # Check the user hasn't been inactive; will raise InactiveAccount.
        if inactive:
            last_context = events.gethistory(param='context', limit=1)
            if last_context:
                last_context = last_context[0][0]
                inactive_diff = emen2.db.database.utcdifference(last_context)
                # print "last_context?", last_context, inactive_diff, inactive
                if inactive_diff > inactive:
                    emen2.db.log.security("Login failed: inactive account for %s, last login was %s, max inactivity is %s"%(self.name, inactive_diff, inactive))
                    raise emen2.db.exceptions.InactiveAccount(name=self.name, message="This account has expired due to inactivity.")



    ##### Name and display name #####

    def _set_name_first(self, key, value):
        pass
    
    def _set_name_last(self, key, value):
        pass
        
    def _set_name_middle(self, key, value):
        pass
        
    def _set_displayname(self, key, value):
        pass

    ##### Password methods #####

    def _set_password(self, key, value):
        # This will always fail unless you're an admin:
        #   you need to specify the current password or a secret auth token.
        self.setpassword(None, value)
    
    def _validate_password(self, value, recycle=None, events=None):
        # Validate the new password.
        value = unicode(value or '').strip()
        auth = emen2.db.auth.PasswordAuth()
        hashpassword = auth.validate(value)

        # Check we haven't recycled an existing password.
        recycle = emen2.db.config.get('security.password_recycle')
        if events and recycle:
            error = emen2.db.exceptions.RecycledPassword(name=self.name, message="You may not re-use a previously used password.")
            auth = emen2.db.auth.PasswordAuth()
            if auth.check(value, self.password):
                raise error
            for previous in events.gethistory(param='password', limit=recycle):
                if auth.check(value, previous[3]):
                    raise error
        return hashpassword

    def setpassword(self, oldpassword, newpassword, secret=None, events=None):
        """Set the user password.
        
        You must provide either a password, or an authentication secret.
        """
        # Check that we have permission to update the password.
        # Check that it's:
        #   a new user,
        #   or we know an authentication secret
        #   or we know the existing password, 
        # checkpassword will raise exception for failed attempt
        if self.isnew():
            pass
        elif self._checksecret('resetpassword', None, secret):
            pass
        elif self.checkpassword(oldpassword):
            pass
        else:
            raise self.error(e=emen2.db.exceptions.AuthenticationError)

        hashpassword = self._validate_password(newpassword, events=events)
        
        # Remove any secrets, if set.
        self._delsecret() 
        # Finally, set the password.
        self._set('password', hashpassword, True)
        
    def checkpassword(self, password):
        """Check the user password. Will raise a PermissionsError if failed."""
        # Check legacy SHA-1 based password hashes..
        # TODO: Perhaps expire these accounts and require password reset?
        auth = emen2.db.auth.PasswordAuth()
        if auth.check(password, self.password, algorithm='SHA-1'):
            return True

        # Check the password.
        if auth.check(password, self.password):
            return True

        raise self.error(e=emen2.db.exceptions.AuthenticationError)

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
        # This will always fail unless you're an admin:
        #   you need to specify the current password or a secret auth token.
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
        # Note: admin users always return True for _checksecret
        # Note: the auth token is bound both to the method (setemail) and the
        #     specific requested email address.
        value = self._validate_email(value)
        if self.isnew():
            self._set('email', value, self.isowner())
        elif self._checksecret('setemail', value, secret):
            self._set('email', value, True)
            self._delsecret()
        elif self.checkpassword(password):
            self._setsecret('setemail', value)
        else:
            raise self.error(e=emen2.db.exceptions.AuthenticationError)

    ##### Secrets for account password resets #####

    def _makesecret(self):
        # Use uuid4 as the secret.
        return uuid.uuid4().hex

    def _checksecret(self, action, args, secret):
        try:
            if self.ctx.checkadmin():
                return True
        except Exception, e:
            pass

        if not hasattr(self, 'secret'):
            self.data['secret'] = None

        # This should check expiration time...
        if action and secret and getattr(self, 'secret', None):
            if action == self.secret[0] and args == self.secret[1] and secret == self.secret[2]:
                return True
        return False

    def _setsecret(self, action, args):
        if not hasattr(self, 'secret'):
            self.data['secret'] = None

        if self.secret:
            if action == self.secret[0] and args == self.secret[1]:
                return

        # Generate random secret.
        secret = self._makesecret()
        self.data['secret'] = (action, args, secret, time.time())

    def _delsecret(self):
        self.data['secret'] = None

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
    :property userrec: Copy of profile record; set by database when accessed
    :property displayname: User "display name"; set by database when accessed
    """
    
    public = BaseUser.public | set(['privacy', 'disabled', 'userrec', 'groups', 'record'])

    def init(self, d):
        super(User, self).init(d)
        # Enabled/disabled, privacy level, and record ID pointer
        self.data['disabled'] = False
        self.data['privacy'] = 0
        self.data['record'] = None
        self.userrec = {}
        self.displayname = self.name
        self.groups = set()

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

        # Cached attributes.
        self.userrec = {}
        self.displayname = self.getdisplayname()
        self.groups = set()

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
        self._set(key, state, self.ctx.checkadmin())

    def setprivacy(self, privacy):
        """Set privacy level."""
        # Users can set their own privacy level
        privacy = int(privacy)
        if privacy not in [0,1,2]:
            raise self.error("User privacy setting may be 0, 1, or 2.")
        self._set(key, privacy, self.isowner())

    ##### Displayname and profile Record #####

    def getdisplayname(self, lnf=False, record=None):
        """Get the user profile record and return the display name."""
        if self.record is None:
            if self.privacy:
                return "(private)"
            return unicode(self.name)

        if not self.userrec:
            if not record:
                record = self.ctx.db.record.get(self.record) or {}
            self.userrec = record

        return self._formatdisplayname(lnf=lnf)

    def _formatdisplayname(self, lnf=False):
        if not self.userrec:
            return self.name
        # Yes, this is not very pretty.
        nf = self.userrec.get('name_first')
        nm = self.userrec.get('name_middle')
        nl = self.userrec.get('name_last')
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
