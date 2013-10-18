"""Authentication."""
# This used to be part of the User class, but it's become
# large and complicate enough to put in its own module.

import os
import re

# Hash functions.
import hashlib
try:
    import bcrypt
except:
    bcrypt = None

import emen2.db.exceptions
import emen2.db.config
# import emen2.timeutil

SALT_BYTES = 22
HASH_TYPES = ['SHA-1', 'SHA-2', 'bcrypt', '2', '2a', 'PBKDF2', 'MD5', 'legacy']


class Hasher(object):
    """Manage password hashes.
    
    EMEN2 Passwords use a convention similar to bcrypt:
        $algorithm$rounds$salt$hash
    
    Example:

    >>> auth = emen2.db.auth.Hasher()    
    >>> auth.hash('testqwerty', algorithm='sha1')
    '$sha1$0$L7V7n+K78MOG3JyicTWXIB$F1joLfgwg5YNL9ueMLqN80+S+M'

    Here, you can see the algorithm is 'sha1', the rounds are '0', the salt is
    'L7V7n+K78MOG3JyicTWXIB', and the SHA-1 hash is
    'F1joLfgwg5YNL9ueMLqN80+S+M'.
    
    Note that I included an extra $ between the salt and hash for simplicity's
    sake; bcrypt omits this.    
    """

    def check(self, password, hashed, algorithm=None):
        """Check a password."""
        algorithm = algorithm or self.parse(hashed)[0]
        password = password or ""
        return self.hash(password, salt=hashed, algorithm=algorithm) == hashed

    def hash(self, password, algorithm, salt=None):
        """Hash the password."""
        if algorithm not in HASH_TYPES:
            raise NotImplementedError("Unknown password hashing algorithm: %s"%algorithm)
        if algorithm == 'SHA-1':
            return self.sha1(password, salt)
        elif algorithm == 'SHA-2':
            return self.sha2(password, salt)
        elif algorithm in ['2', '2a', 'bcrypt']:
            return self.bcrypt(password, salt)
        elif algorithm == 'PBKDF2':
            return self.pbkdf2(password, salt)
        elif algorithm == 'MD5':
            return self.md5(password, salt)
        elif algorithm == 'legacy':
            return self.legacy(password, salt)
            
    def checkhashed(self, password):
        ret = False
        try:
            self.parse(password)
            ret = True
        except:
            pass
        return ret
    
    def gen_salt(self):
        return os.urandom(SALT_BYTES).encode('base_64')[:SALT_BYTES]
    
    def get_salt(self, salt=None):
        if not salt or not salt.startswith('$'):
            return None
        return salt.split("$")[3][:SALT_BYTES]
    
    def parse(self, password):
        password = password or ''
        p = password.split('$')
        if len(p) == 4:
            algorithm = p[1]
            rounds = p[2]
            salt = p[3][:SALT_BYTES]
            hashedpassword = p[3][SALT_BYTES:]
        elif len(p) == 5:
            algorithm = p[1]
            rounds = p[2]
            salt = p[3][:SALT_BYTES]
            hashedpassword = p[4]
        elif len(password) == 40:
            algorithm = 'MD5'
            rounds = 0
            salt = ''
            hashedpassword = password
        else:
            raise ValueError("Could not parse password hash.")
        if algorithm not in HASH_TYPES:
            raise NotImplementedError("Unknown password hashing algorithm: %s"%algorithm)            
        return algorithm, rounds, salt, hashedpassword
    
    def format_password(self, algorithm, rounds, salt, hashedpassword):
        return """$%s$%s$%s$%s"""%(algorithm, rounds, salt, hashedpassword)
            
    def legacy(self, password, salt):
        return hashlib.sha1(salt+password).hexdigest()    
        
    def md5(self, password, salt):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.md5(salt+password).digest().encode('base_64')[:-3]
        return self.format_password('md5', 0, salt, h)

    def sha1(self, password, salt):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.sha1(salt+password).digest().encode('base_64')[:-3]
        return self.format_password('sha1', 0, salt, h)

    def sha2(self, password, salt):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.sha512(salt+password).digest().encode('base_64')[:-3]
        return self.format_password('sha2', 0, salt, h)

    def bcrypt(self, password, salt):
        if not bcrypt:
            raise ImportError('Hash algorithm bcrypt not available')
        # Check that we've been given a valid salt. 
        # bcrypt.hashpw will raise ValueError otherwise.
        if not salt or not salt.startswith('$'):
            salt = bcrypt.gensalt()
        return bcrypt.hashpw(password, salt)

    def pbkdf2(self, password, salt):
        raise NotImplementedError("Hash algorithm PBKDF2 coming soon.")
        
class PasswordAuth(object):
    """Check and validate passwords."""
    
    def __init__(self, name=None):
        self.hasher = Hasher()
        # TODO: Temporary..
        self.name = name
        self.creationtime = 0
    
    def validate(self, password, events=None):
        minlength = emen2.db.config.get('security.password_minlength')
        strength = emen2.db.config.get('security.password_strength')
        algorithm = emen2.db.config.get('security.password_algorithm')

        # TODO: Find a better way check this..
        # Check if the password is already hashed;
        if self.hasher.checkhashed(password):
            return password

        # Check the minimum length.
        if not password or len(password) < minlength:
            raise emen2.db.exceptions.WeakPassword("Password too short; minimum %s characters required"%minlength)

        if not all([re.match(i, password) for i in strength]):
            raise emen2.db.exceptions.WeakPassword("Password not strong enough. Needs a lower case letter, an upper case letter, a number, and a symbol such as @, #, !, %, ^, etc.")

        # Hash the password.
        return self.hasher.hash(password, algorithm)

    def check(self, password, hashed, algorithm=None):
        """Check a password."""
        return self.hasher.check(password, hashed, algorithm=algorithm)
    
    def checkrecycle(self, password, events=None):
        # Check we haven't recycled an existing password.
        recycle = emen2.db.config.get('security.password_recycle')
        if not recycle:
            return
        if not recycle:
            return
        
        error = emen2.db.exceptions.RecycledPassword(name=self.name, message="You may not re-use a previously used password.")
        # if self.check(password, self.password):
        #    raise error
        for previous in events.gethistory(param='password', limit=recycle):
            if self.check(password, previous[3]):
                raise error        
        
    def checkexpired(self, password, events=None):
        expire_initial = emen2.db.config.get('security.password_expire_initial')
        expire = emen2.db.config.get('security.password_expire')
        if not (expire or expire_initial):
            return
        if not events:
            return
        
        # Check the password hasn't expired; will raise ExpiredPassword.
        last_password = events.gethistory(param='password', limit=1)
        if last_password:
            last_password = last_password[0][0]
        elif expire_initial:
            raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="Please set a new password before your initial login.", title="Initial login")
        else:
            last_password = self.creationtime

        password_diff = emen2.db.database.utcdifference(last_password)
        if password_diff > expire:
            emen2.db.log.security("Login failed: expired password for %s, password age was %s, max age is %s"%(self.name, password_diff, expire))
            raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="This password has expired.")        
        
    def checkinactive(self, events=None):
        inactive = emen2.db.config.get('security.user_inactive')
        if not inactive:
            return
        if not events:
            return

        last_context = events.gethistory(param='context', limit=1)
        if not last_context:
            return

        last_context = last_context[0][0]
        inactive_diff = emen2.db.database.utcdifference(last_context)
        # print "last_context?", last_context, inactive_diff, inactive
        if inactive_diff > inactive:
            emen2.db.log.security("Login failed: inactive account for %s, last login was %s, max inactivity is %s"%(self.name, inactive_diff, inactive))
            raise emen2.db.exceptions.InactiveAccount(name=self.name, message="This account has expired due to inactivity.")
        
class KerberosAuth(object):
    """Kerberos-based authentication."""
    def check(self, password, hashed):
        pass

