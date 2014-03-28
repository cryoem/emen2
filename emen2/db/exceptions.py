"""Exceptions."""

class EMEN2Exception(Exception):
    def __init__(self, message=None, name=None, title=None):
        self.name = name
        self.title = title
        self.message = message or self.__doc__
    def __str__(self):
        return self.message

##### Security Errors #####
class SecurityError(EMEN2Exception):
    """Security error."""
    code = 401
            
##### Permissions error. #####
class PermissionsError(SecurityError):
    """Insufficient permissions."""
            
##### Authentication errors. #####
class AuthenticationError(SecurityError):
    """Invalid account name or password."""

# Expired session.
class SessionError(AuthenticationError):
    """Session expired."""

class TooManyAttempts(AuthenticationError):
    """Too many login attempts. Please try again later."""

# Disabled users.
class InactiveAccount(AuthenticationError):
    """Account disabled for inactivity."""

class DisabledUserError(AuthenticationError):
    """Disabled user."""
            
##### Password setting errors. #####
class PasswordReset(SecurityError):
    """Invalid password."""
    
class WeakPassword(PasswordReset):
    """Weak password."""

class ExpiredPassword(PasswordReset):
    """Expired password."""  

class RecycledPassword(PasswordReset):
    """Recycled password."""
            
##### Validation Errors #####
class ValidationError(EMEN2Exception):
    """Validation error."""

class ExistingKeyError(EMEN2Exception):
    """This account name or email is already in use."""
            
##### Time out #####
class TimeOutError(EMEN2Exception):
    """Operation timed out."""
            
##### Email #####
class EmailError(EMEN2Exception):
    """There was a problem sending an email."""
