# $Id: user.py,v 1.115 2013/06/04 10:12:23 irees Exp $
"""User DBOs

Classes:
    BaseUser
    NewUser
    User
"""

import time
import operator
import hashlib
import random
import re
import weakref
import traceback
import random
import string

# EMEN2 imports
import emen2.db.exceptions
import emen2.db.dataobject

# DBO that contains a password and email address
class BaseUser(emen2.db.dataobject.BaseDBObject):

    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(['email', 'password'])
    attr_protected = emen2.db.dataobject.BaseDBObject.attr_protected | set(['email', 'password'])
    attr_required = set(['email', 'password'])

    def init(self, d):
        super(BaseUser, self).init(d)

        # Required initialization params
        self.__dict__['email'] = None
        self.__dict__['password'] = None

        # Secret takes the format:
        # action type, args, ctime for when the token is set, and secret
        self.__dict__['secret'] = None

    def _set_password(self, key, value):
        # This will always fail unless you're an admin
        #    setpassword requires either a password or auth token as arguments.
        self.setpassword(None, value)
        return set(['password'])
    
    def _set_email(self, key, value):
        # This will always fail unless you're an admin --
        #    setemail requires either a password or auth token as arguments.
        self.setemail(value)
        return set(['email'])

    def isowner(self):
        return super(BaseUser, self).isowner() or self._ctx.username == self.name

    ##### Password methods #####

    def _hashpassword(self, password):
        password = unicode(password or '')
        if len(password) == 40:
            return password
        return hashlib.sha1(unicode(password)).hexdigest()

    def validate_password(self, password):
        # Only root is allowed to have no password. All user accounts must have a password.
        password = unicode(password or '')
        if len(password) < 6 and self.name != 'root' and len(password) != 40:
            self.error("Password too short; minimum 6 characters required")
        return password

    def checkpassword(self, password):
        try:
            if self._ctx.checkadmin():
                return True
        except AttributeError:
            pass

        # This needs to work even if there is no Context set.
        if self.get('disabled'):
            self.error(e=emen2.db.exceptions.DisabledUserError)

        # Check the hashed password against the stored hashed password.
        if self.password and self._hashpassword(password) == self.password:
            return True
            
        # Sleep for 2 seconds any time there is a wrong password!!
        time.sleep(2)
        self.error(e=emen2.db.exceptions.AuthenticationError)

    def setpassword(self, oldpassword, newpassword, secret=None):
        # Check that we know the existing password, or an authentication secret
        # checkpassword will sleep 2 seconds for each failed attempt
        # checkpassword will raise exception for failed attempt
        if not (
            self.isnew()
            or self._checksecret('resetpassword', None, secret) 
            or self.checkpassword(oldpassword)
            ):
            self.error(e=emen2.db.exceptions.AuthenticationError)

        # You must be logged in as this user (or admin) AND know the old password.
        newpassword = self._hashpassword(self.validate_password(newpassword))
        self._set('password', newpassword, True)
        self._delsecret()

    def resetpassword(self):
        """Reset the user password. This creates an internal 'secret' token that can be used to reset a password.
        The secret should never be accessible via public methods.
        """
        # The second argument should be the email address
        self._setsecret('resetpassword', None)

    #################################
    # email setting/validation
    #################################

    def setemail(self, email, password=None, secret=None):
        email = self.validate_email(email)
        # Check that we know the existing password, or an authentication secret
        # Note that admin users always return True for _checksecret
        # Note: the auth token is bound both to the method (setemail) and the
        #     specific requested email address.
        # Note: email can be changed before first commit.
        if self.isnew():
            self._set('email', email, self.isowner())
        elif self._checksecret('setemail', email, secret):
            self._set('email', email, self.isowner())
            self._delsecret()
        elif self.checkpassword(password):
            self._setsecret('setemail', email)
        else:
            self.error(e=emen2.db.exceptions.AuthenticationError)
        return self.email

    #################################
    # Secrets for account password resets
    #################################

    def _makesecret(self, length=32):
        l = length / 2
        rg = random.SystemRandom()
        r = range(255)
        return ''.join(['%02x'%rg.choice(r) for i in range(l)])

    def _checksecret(self, action, args, secret):
        # I only want this to work on certain subclasses. See: User
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

    #################################
    # validation methods
    #################################

    def validate_email(self, email):
        # if not re.match('(\S+@\S+)', email):
        # After a long discussion in #python, it is impossible to validate
        #     emails other than checking for '@'
        # Note: Forcing emails to be stored as lower case.
        email = unicode(email or '').strip().lower()
        if not email or '@' not in email:
            self.error("Invalid email format '%s'"%email)
        return email


signupinfo = set(["name_first", "name_middle", "name_last", "comments",    "institution",
    "department", "address_street", "address_city", "address_state", "address_zipcode",
    "country", "uri", "phone_voice", "phone_fax"])

class NewUser(BaseUser):
    # displayname, userrec, and groups are unset when committing, so they can skip validation.
    attr_public = BaseUser.attr_public | set(['signupinfo'])

    def init(self, d):
        super(NewUser, self).init(d)
        # New users store signup info in a dict,
        #     which is committed as a 'person' record when approved
        self.__dict__['signupinfo'] = {}

    # Setters
    def _set_signupinfo(self, key, value):
        self.setsignupinfo(value)
        return set(['signupinfo'])

    def setsignupinfo(self, update):
        self._set('signupinfo', update)
        self.validate()

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

        # print "Validated signup...."
        # print newsignup
        self.__dict__['signupinfo'] = newsignup

    # def setContext(...)
    #    Don't let non-admin users read this?

class User(BaseUser):
    """User record. This contains the basic metadata information for a single user account, including username, password, primary email address, active/disabled, timestamps, and link to more complete user profile. Group membership is stored in Group instances, and set here by db.user.get by checking an index. If available during db.user.get, a copy of the profile record and the user's "displayname" will also be set.

    @attr name Username for logging in, first character must be a letter, no spaces
    @attr password SHA1 hashed password
    @attr disabled True if user is disabled, unable to login
    @attr privacy Privacy level; 1 conceals personal information from anonymous users, 2 conceals personal information from all users
    @attr record Record ID containing additional profile information
    @attr email Semi-validated email address
    @property groups Set by database when accessed
    @property userrec Copy of profile record; set by database when accessed
    @property displayname User "display name"; set by database when accessed
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

    #################################
    # Setters
    #################################

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

    #################################
    # "Secret" Authentication tokens
    #################################

    # I only have this method available on User, and not BaseUser.
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

    #################################
    # Enable/disable
    #################################
    # These will go through setattr -> setitem -> set_{param}

    def enable(self):
        self.disabled = False

    def disable(self):
        self.disabled = True

    def setprivacy(self, privacy):
        self.privacy = privacy

    #################################
    # Displayname and profile Record
    #################################

    def getdisplayname(self, lnf=False, record=None):
        """Get the user profile record from the current Context"""
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

        nf = self._userrec.get('name_first')
        nm = self._userrec.get('name_middle')
        nl = self._userrec.get('name_last')

        #if u["name_first"] and u["name_middle"] and u["name_last"]:
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

    #################################
    # Access methods
    #################################

    def setContext(self, ctx, hide=True):
        super(User, self).setContext(ctx)
        admin = self._ctx.checkreadadmin()
        ctxuser = self._ctx.username
        p = {}

        # secret is never made available except through direct btree.get().
        # This may cause the secret to be reset at some points...
        p['secret'] = None

        # Defaults for cached attributes..
        p['_userrec'] = {}
        p['_displayname'] = self.name
        p['_groups'] = set()

        # If the user has requested privacy, we return only basic info
        hide = self.privacy or self._ctx.username == 'anonymous'
        if admin or ctxuser == self.name:
            hide = False
        else:
            # This is a bug that needs to be fixed.
            p['password'] = None

        # You must access the User directly to get these attributes

        # Hide basic details from anonymous users
        if hide:
            p['email'] = None
            p['record'] = None

        self.__dict__.update(p)
        self.__dict__['_displayname'] = self.getdisplayname()




__version__ = "$Revision: 1.115 $".split(":")[1][:-1].strip()
