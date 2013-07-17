# $Id$
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

# Use bcrypt for passwords.
# This is no longer optional.
import bcrypt
import hashlib

# EMEN2 imports
import emen2.db.exceptions
import emen2.db.dataobject

MINLENGTH = 8

# DBO that contains a password and email address
class BaseUser(emen2.db.dataobject.BaseDBObject):
    """Base User DBO.

    Allows an email address and a password.
    
    The password is never exposed via the API; you have to directly retreive
    the item from the DB without going through get/setContext.
    
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
    
    Note: the actual email is currently handled in the public API methods. See
    database.py.
    
    These BaseDBObject methods are overridden:

        init            Set attributes
        setContext      Check read permissions, bind Context, strip out password/secrets.
        validate        Check required attributes
        checkpassword   Check the password; raise SecurityError if failed.
        setpassword     Set the password; requires password or secret token.
        resetpassword   Set the password reset secret token.
        setemail        Set the email; requires password and secret token (2 step process.)
      
    :attr email: email
    :attr password: Hashed (bcrypt) password.
    """

    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(['email'])

    def init(self, d):
        super(BaseUser, self).init(d)

        # Required initialization params
        self.__dict__['email'] = None
        self.__dict__['password'] = None

        # Secret takes the format:
        # action type, args, ctime for when the token is set, and secret
        self.__dict__['secret'] = None

    def setContext(self, ctx, hide=True):
        super(BaseUser, self).setContext(ctx)
        self.__dict__['secret'] = None

    def validate(self):
        super(BaseUser, self).validate()
        if not self.password: 
            self.error('No password set.')
        if not self.email:
            self.error('No email set.')
        self._validate_email(self.email)

    ##### Setters #####

    def _set_password(self, key, value):
        # This will always fail unless you're an admin --
        #   you need to specify the current password or a secret auth token.
        self.setpassword(None, value)
        return set(['password'])
    
    def _set_email(self, key, value):
        # This will always fail unless you're an admin --
        #   you need to specify the current password or a secret auth token.
        self.setemail(value)
        return set(['email'])

    ##### Password methods #####

    def _hashpassword(self, password, salt=None):
        return bcrypt.hashpw(unicode(password or ''), salt or bcrypt.gensalt())

    def _hashpassword_old(self, password, salt=None):
        password = unicode(salt or '') + unicode(password or '')
        return hashlib.sha1(unicode(password)).hexdigest()

    def _validate_password(self, password):
        # All accounts must have a password.
        password = unicode(password or '')
        if len(password) < MINLENGTH:
            self.error("Password too short; minimum %s characters required"%MINLENGTH)
        # ... add additional strength checking here ...
        return password

    def checkpassword(self, password):
        """Check the user password. Will raise a SecurityError if failed."""
        # Disabled users cannot login.
        # This needs to work even if there is no Context set.
        if self.get('disabled'):
            self.error(e=emen2.db.exceptions.DisabledUserError)

        # Also check legacy MD5 based password hashes..
        # TODO: Convert the password to bcrypt hashed pw when found.
        # TODO: Perhaps expire these accounts and require password reset?
        # raise MigratePasswordException...?
        if self._hashpassword_old(password) == self.password:
            return True

        # Check the bcrypt-hashed password.
        if self._hashpassword(password, salt=self.password) == self.password:
            return True
            
        self.error(e=emen2.db.exceptions.AuthenticationError)

    def setpassword(self, oldpassword, newpassword, secret=None):
        """Set the user password.
        
        You must provide either a password, or an authentication secret.
        """
        # Check that it's:
        #   a new user,
        #   or we know an authentication secret
        #   or we know the existing password, 
        # checkpassword will raise exception for failed attempt
        newpassword = self._hashpassword(self._validate_password(newpassword))
        if self.isnew():
            self._set('password', newpassword, self.isowner())
        elif self._checksecret('resetpassword', None, secret):
            self._set('password', newpassword, self.isowner())
            self._delsecret()
        elif self.checkpassword(oldpassword):
            self._set('password', newpassword, self.isowner())
        else:
            self.error(e=emen2.db.exceptions.AuthenticationError)

    def resetpassword(self):
        """Reset the user password. 

        This creates an internal 'secret' token that can be used to reset a
        password. This should be sent to the user's registered email address.

        The secret must never be accessible via public methods. Only via email.
        """
        # The second argument should be the email address
        self._setsecret('resetpassword', None)

    ##### email setting/validation #####

    def _validate_email(self, value):
        # After a long discussion in #python, it is impossible to validate
        #     emails other than checking for '@'
        # However, in the modern world, I don't think I need to worry about
        # things like UUCP. So, I think I'll just use Python's
        # email.utils.parse_addr.
        # Note: Forcing emails to be stored as lower case.
        _, value = email.utils.parseaddr(value)
        value = value.strip().lower()
        if '@' not in value:
            self.error("Invalid email: %s"%value)
        return value

    def setemail(self, value, password=None, secret=None):
        """Set email address.
        
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
            self._set('email', value, self.isowner())
            self._delsecret()
        elif self.checkpassword(password):
            self._setsecret('setemail', value)
        else:
            self.error(e=emen2.db.exceptions.AuthenticationError)
        return self.email

    ##### Secrets for account password resets #####

    def _makesecret(self):
        # Use uuid4 as the secret.
        return uuid.uuid4().hex

    def _checksecret(self, action, args, secret):
        try:
            if self._ctx.checkadmin():
                return True
        except Exception, e:
            pass

        if not hasattr(self, 'secret'):
            self.__dict__['secret'] = None

        # This should check expiration time...
        if action and secret and getattr(self, 'secret', None):
            if action == self.secret[0] and args == self.secret[1] and secret == self.secret[2]:
                return True
        return False

    def _setsecret(self, action, args):
        # secret is set using __dict__ (like _ctx/_ptest) because it's a secret, and not a normal attribute.
        if not hasattr(self, 'secret'):
            self.__dict__['secret'] = None

        if self.secret:
            if action == self.secret[0] and args == self.secret[1]:
                return

        # Generate random secret.
        secret = self._makesecret()
        self.__dict__['secret'] = (action, args, secret, time.time())

    def _delsecret(self):
        self.__dict__['secret'] = None


# Parameters allowed during New User signup.
signupinfo = set(["name_first", "name_middle", "name_last", "comments", "institution",
    "department", "address_street", "address_city", "address_state", "address_zipcode",
    "country", "uri", "phone_voice", "phone_fax"])

class NewUser(BaseUser):
    """New User.
    
    This is a container for signup information. It is convered to a User when approved.
    
    The signup information is kept in 'signupinfo'. This will be converted to a
    'person' record when approved.
    
    :attr signupinfo: Dictionary containing signup information.
    """
    attr_public = BaseUser.attr_public | set(['signupinfo'])

    def init(self, d):
        super(NewUser, self).init(d)
        # New users store signup info in a dict,
        #     which is committed as a 'person' record when approved
        self.__dict__['signupinfo'] = {}

    def validate(self):
        super(NewUser, self).validate()

        # Check signupinfo
        required = set(["name_first","name_last"])
        newsignup = {}

        for param, value in self.signupinfo.items():
            if not value:
                continue
            # These will be transferred to a Record
            try:
                value = self.validate_param(param, value)
            except ValueError:
                emen2.db.log.info("NewUser Validation: Couldn't validate new user signup field %s: %s"%(param, value))
                continue
            newsignup[param] = value

        for param in required:
            if not newsignup.get(param):
                raise ValueError, "Required param %s"%param

        if self.signupinfo.get('child'):
            newsignup['child'] = self.signupinfo['child']

        self.__dict__['signupinfo'] = newsignup

    def _set_signupinfo(self, key, value):
        self.setsignupinfo(value)
        return set(['signupinfo'])

    def setsignupinfo(self, update):
        self._set('signupinfo', update)
        self.validate()


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
    attribute. 1 hides the link to anonymous users, 2 hides the link from all
    other users.

    :attr disabled: Disable this account.
    :attr privacy: Privacy level
    :attr record: Record ID containing additional profile information
    :property groups: Set by database when accessed
    :property userrec: Copy of profile record; set by database when accessed
    :property displayname: User "display name"; set by database when accessed
    """
    
    attr_public = BaseUser.attr_public | set(['privacy', 'disabled', 'displayname', 'userrec', 'groups', 'record'])

    # These get set during setContext and cleared before commit
    userrec = property(lambda s:s._userrec)
    displayname = property(lambda s:s._displayname)
    groups = property(lambda s:s._groups)

    def init(self, d):
        super(User, self).init(d)
        # Enabled/disabled, privacy level, and record ID pointer
        self.__dict__['disabled'] = False
        self.__dict__['privacy'] = 0
        self.__dict__['record'] = None

    def setContext(self, ctx, hide=True):
        super(User, self).setContext(ctx)
        admin = self._ctx.checkreadadmin()
        ctxuser = self._ctx.username
        p = {}

        # secret is never made available except through direct get().
        # This may cause the secret to be reset at some points...
        p['secret'] = None
        if not (admin or self._ctx.username == self.name):
            p['password'] = None
        
        # Defaults for cached attributes..
        p['_userrec'] = {}
        p['_displayname'] = self.name
        p['_groups'] = set()

        # If the user has requested privacy, we return only basic info
        hide = self.privacy or self._ctx.username == 'anonymous'
        if admin or ctxuser == self.name:
            hide = False
        # Hide basic details from anonymous users
        if hide:
            p['email'] = None
            p['record'] = None

        self.__dict__.update(p)
        self.__dict__['_displayname'] = self.getdisplayname()

    # Users can set their own privacy level
    def _set_privacy(self, key, value):
        value = int(value)
        if value not in [0,1,2]:
            self.error("User privacy setting may be 0, 1, or 2.")
        return self._set(key, value, self.isowner())

    # Only admin can change enabled/disabled or record reference
    def _set_disabled(self, key, value):
        value = bool(value)
        if self.name == self._ctx.username and value:
            self.error("Cannot disable self!")
        return self._set(key, value, self._ctx.checkadmin())

    def _set_record(self, key, value):
        return self._set(key, value, self._ctx.checkadmin())

    ##### Enable/disable #####
    # These will go through setattr -> setitem -> set_{param}

    def enable(self):
        """Enable the user."""
        self.disabled = False

    def disable(self):
        """Disable the user."""
        self.disabled = True

    def setprivacy(self, privacy):
        """Set privacy level."""
        self.privacy = privacy

    ##### Displayname and profile Record #####

    def getdisplayname(self, lnf=False, record=None):
        """Get the user profile record and return the display name."""
        if self.record is None:
            return unicode(self.name)

        if not self._userrec:
            if not record:
                record = self._ctx.db.record.get(self.record) or {}
            self._set('_userrec', record, True)

        # self._set('_displayname', d, True)
        return self._formatusername(lnf=lnf)

    def _formatusername(self, lnf=False):
        if not self._userrec:
            return self.name
        # Yes, this is not very pretty.
        nf = self._userrec.get('name_first')
        nm = self._userrec.get('name_middle')
        nl = self._userrec.get('name_last')
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


__version__ = "$Revision$".split(":")[1][:-1].strip()