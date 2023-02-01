# $Id: exceptions.py,v 1.19 2012/07/28 06:31:17 irees Exp $
"""Exceptions

Exceptions:
    SecurityError
    SessionError
    AuthenticationError
    DisabledUserError
    ValidationError
    ExistingKeyError
    TimeError
"""

# Security Errors
class SecurityError(Exception):
    "Security error."
    code = 401

class SessionError(SecurityError):
    "Session expired."

class AuthenticationError(SecurityError):
    "Invalid account name or password."

class DisabledUserError(SecurityError):
    "Disabled user."

# Validation Errors
class ValidationError(ValueError):
    """Validation error."""

class ExistingKeyError(ValueError):
    "This account name or email is already in use."

# Time out
class TimeError(Exception):
    """Operation timed out."""

__version__ = "$Revision: 1.19 $".split(":")[1][:-1].strip()
