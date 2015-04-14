"""Authentication."""
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

class HashType(object):
    """Manage password hashes.
    
    EMEN2 Passwords use a convention similar to bcrypt:
        $algorithm$rounds$salt$hash
    
    Example:

    >>> auth = emen2.db.auth.HashSHA1()
    >>> auth.hashpw('testqwerty')
    '$SHA-1$0$L7V7n+K78MOG3JyicTWXIB$F1joLfgwg5YNL9ueMLqN80+S+M'

    Here, you can see the algorithm is 'SHA-1', the rounds are '0', the salt is
    'L7V7n+K78MOG3JyicTWXIB', and the SHA-1 hash is
    'F1joLfgwg5YNL9ueMLqN80+S+M'.
    
    Note that I included an extra $ between the salt and hash for simplicity's
    sake; bcrypt omits this.    
    """
    HASHTYPES = {}
    algorithm = None

    @classmethod
    def getcls(self, password=None, algorithm=None):
        password = password or ''
        p = (password or '').split('$')
        if len(p) >= 4:
            algorithm = p[1]
        elif len(password) == 40:
            algorithm = 'MD5'
            
        if algorithm == 'SHA-1':
            return HashSHA1
        elif algorithm == 'SHA-2':
            return HashSHA2 
        elif algorithm in ['2', '2a', 'bcrypt']:
            return HashBCrypt
        elif algorithm == 'PBKDF2':
            return HashPBKDF2
        elif algorithm == 'MD5':
            return HashMD5
        elif algorithm == 'legacy':
            return HashLegacy
        else:
            raise NotImplementedError("Unknown password hashing algorithm: %s"%algorithm)

    def parse(self, password):
        password = password or ''
        p = password.split('$')
        if len(p) == 4:
            rounds = p[2]
            salt = p[3][:SALT_BYTES]
            hashedpassword = p[3][SALT_BYTES:]
        elif len(p) == 5:
            rounds = p[2]
            salt = p[3][:SALT_BYTES]
            hashedpassword = p[4]
        elif len(password) == 40:
            rounds = 0
            salt = ''
            hashedpassword = password
        else:
            raise ValueError("Could not parse password hash.")
        return rounds, salt, hashedpassword
    
    def format_password(self, rounds, salt, hashedpassword):
        return """$%s$%s$%s$%s"""%(self.algorithm, rounds, salt, hashedpassword)
            
    def check(self, password, hashed):
        """Check a password."""
        return self.hashpw(password, salt=hashed) == hashed

    def hashpw(self, password, salt=None):
        """Hash the password."""
        raise NotImplementedError
            
    def checkhashed(self, password):
        try:
            self.parse(password)
            return True
        except:
            return False
    
    def gen_salt(self):
        return os.urandom(SALT_BYTES).encode('base_64')[:SALT_BYTES]
    
    def get_salt(self, salt=None):
        if not salt or not salt.startswith('$'):
            return None
        return salt.split("$")[3][:SALT_BYTES]
    
class HashSHA1(HashType):
    algorithm = 'SHA-1'
    def hashpw(self, password, salt=None):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.sha1(salt+password).digest().encode('base_64')[:-3]
        return self.format_password(0, salt, h)

class HashLegacy(HashType):
    algorithm = 'legacy'
    def hashpw(self, password, salt=None):
        salt = ''
        return hashlib.sha1(salt+password).hexdigest()    

class HashMD5(HashType):
    algorithm = 'MD5'        
    def hashpw(self, password, salt=None):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.md5(salt+password).digest().encode('base_64')[:-3]
        return self.format_password(0, salt, h)

class HashSHA2(HashType):
    algorithm = 'SHA-2'
    def hashpw(self, password, salt=None):
        salt = self.get_salt(salt) or self.gen_salt()
        h = hashlib.sha512(salt+password).digest().encode('base_64')[:-3]
        return self.format_password(0, salt, h)

class HashBCrypt(HashType):
    algorithm = 'bcrypt'
    def hashpw(self, password, salt=None):
        if not bcrypt:
            raise ImportError('Hash algorithm bcrypt not available')
        # Check that we've been given a valid salt. 
        # bcrypt.hashpw will raise ValueError otherwise.
        if not salt or not salt.startswith('$'):
            salt = bcrypt.gensalt()
        return bcrypt.hashpw(password, salt)

class HashPBKDF2(HashType):
    algorithm = 'PBKDF2'
    def hashpw(self, password, salt=None):
        raise NotImplementedError("Hash algorithm PBKDF2 coming soon.")
        



class PasswordAuth(object):
    """Check and validate passwords."""
    
    def __init__(self, name=None, history=None, contexts=None):
        self.hasher = HashBCrypt()
        # TODO: Temporary..
        self.name = name
        self.creationtime = 0
        # Password history and past logins
        self.history = history
        self.contexts = contexts
    
    def validate(self, password):
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
    
    def checkrecycle(self, password):
        # Check we haven't recycled an existing password.
        recycle = emen2.db.config.get('security.password_recycle')
        if not recycle:
            return
        if not self.history:
            return
        for previous in self.history.find(key='password', limit=recycle):
            if self.check(password, previous.get('value')):
                raise emen2.db.exceptions.RecycledPassword(name=self.name, message="You may not re-use a previously used password.")
        
    def checkexpired(self, password):
        expire_initial = emen2.db.config.get('security.password_expire_initial')
        expire = emen2.db.config.get('security.password_expire')
        if not (expire or expire_initial):
            return
        if not self.history:
            return
        
        # Check the password hasn't expired; will raise ExpiredPassword.
        # Find the time of the last password; 
        #   if no password change event, and expire_initial, then raise ExpiredPassword
        #   else, the password change event was account creation.
        last_password = self.history.find(key='password', limit=1)
        if last_password:
            last_password = last_password[0].get('time')
        elif expire_initial:
            raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="Please set a new password before your initial login.", title="Initial login")
        else:
            last_password = self.creationtime

        # Time since the last password
        #   if time since last password > expire time, raise ExpiredPassword
        password_diff = emen2.db.database.utcdifference(last_password)
        if password_diff > expire:
            emen2.db.log.security("Login failed: expired password for %s, password age was %s, max age is %s"%(self.name, password_diff, expire))
            raise emen2.db.exceptions.ExpiredPassword(name=self.name, message="This password has expired.")        
        
    def checkinactive(self, lastcontext=None):
        raise NotImplementedError
        inactive = emen2.db.config.get('security.user_inactive')
        if not inactive:
            return
        if not lastcontext:
            return
        inactive_diff = emen2.db.database.utcdifference(lastcontext)
        # print "lastcontext?", last_context, inactive_diff, inactive
        if inactive_diff > inactive:
            emen2.db.log.security("Login failed: inactive account for %s, last login was %s, max inactivity is %s"%(self.name, inactive_diff, inactive))
            raise emen2.db.exceptions.InactiveAccount(name=self.name, message="This account has expired due to inactivity.")
        
class KerberosAuth(object):
    """Kerberos-based authentication."""
    def check(self, password, hashed):
        pass


if __name__ == "__main__":
    # Test
    for i in ['legacy', 'MD5', 'SHA-1', 'SHA-2', 'bcrypt']:
        password = 'Asdf1234@!'
        h = HashType.getcls(algorithm=i)()
        hashpw = h.hashpw(password)
        check = h.check(password, hashpw)
        assert check
        fail = h.check("incorrectpassword", hashpw)
        assert fail == False
        
    
    
