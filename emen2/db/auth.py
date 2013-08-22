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

SALT_BYTES = 22
HASH_TYPES = ['SHA-1', 'SHA-2', 'bcrypt', '2', '2a', 'PBKDF2', 'MD5']

class ExpirationAuth(object):
    """Expiration checking will be moved here."""
    pass

class PasswordAuth(object):
    """Manage password hashes.
    
    EMEN2 Passwords use a convention similar to bcrypt:
        $algorithm$rounds$salt$hash
    
    Example:

    >>> auth = emen2.db.auth.PasswordAuth()    
    >>> auth.hash('testqwerty', algorithm='sha1')
    '$sha1$0$L7V7n+K78MOG3JyicTWXIB$F1joLfgwg5YNL9ueMLqN80+S+M'

    Here, you can see the algorithm is 'sha1', the rounds are '0', the salt is
    'L7V7n+K78MOG3JyicTWXIB', and the SHA-1 hash is
    'F1joLfgwg5YNL9ueMLqN80+S+M'.
    
    Note that I included an extra $ between the salt and hash for simplicity's
    sake; bcrypt omits this.    
    """

    # def random(self, password):
    #     # Satisfy minimum complexity rules.
    #     base = "abAB09!@abAB09!@"
    #     rand = os.urandom(32).encode('base_64')
    #     return base+rand

    def checkhashed(self, password):
        # Small possibility this could be a false positive.
        try:
            parsed = self.parse(password)
        except ValueError:
            return False
        return True

    def validate(self, password):
        minlength = emen2.db.config.get('security.password_minlength')
        strength = emen2.db.config.get('security.password_strength')

        # We need to avoid double hashing.
        # Not the best solution...
        if self.checkhashed(password):
            return password
        
        # Check the minimum length.
        if not password or len(password) < minlength:
            raise emen2.db.exceptions.WeakPassword("Password too short; minimum %s characters required"%minlength)

        if not all([re.match(i, password) for i in strength]):
            raise emen2.db.exceptions.WeakPassword("Password not strong enough. Needs a lower case letter, an upper case letter, a number, and a symbol such as @, #, !, %, ^, etc.")

        # hash the password.
        return self.hash(password)
    
    def hash(self, password, salt=None, algorithm=None):
        """Hash the password."""
        salt = salt or ''
        password = password or ''
        algorithm = algorithm or emen2.db.config.get('security.password_algorithm')
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
            return self.old(password, salt)
    
    def check(self, password, hashed, algorithm=None):
        """Check a password."""
        algorithm = algorithm or self.parse(hashed)[0]
        return self.hash(password, salt=hashed, algorithm=algorithm) == hashed

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
        
    def old(self, password, salt):
        return hashlib.sha1(salt+password).hexdigest()    
        
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
        
class KerberosAuth(object):
    """Kerberos-based authentication."""
    def check(self, password, hashed):
        pass

