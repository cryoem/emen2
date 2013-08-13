"""Exceptions."""

class EMEN2Exception(Exception):
    pass

# Security Errors
class SecurityError(EMEN2Exception):
    """Security error."""
    code = 401

class SessionError(SecurityError):
    """Session expired."""

class AuthenticationError(SecurityError):
    """Invalid account name or password."""

class DisabledUserError(SecurityError):
    """Disabled user."""

class PasswordReset(SecurityError):
    """Invalid password."""
    def __init__(self, message=None, name=None):
        self.name = name
        self.message = message or "Invalid password."
    def __str__(self):
        return self.message
    
class ExpiredPassword(PasswordReset):
    """Expired password."""  

class RecycledPassword(PasswordReset):
    """Recycled password."""
    
# Validation Errors
class ValidationError(EMEN2Exception):
    """Validation error."""

class ExistingKeyError(EMEN2Exception):
    """This account name or email is already in use."""

# Time out
class TimeError(EMEN2Exception):
    """Operation timed out."""

