# $Id$
class SecurityError(Exception):
    "Exception for a security violation"

class SessionError(KeyError):
    "Session Expired"

class AuthenticationError(ValueError):
    "Invalid Username or Password"
    
class DisabledUserError(ValueError):
    "User %s disabled"

class FieldError(Exception):
    "Exception for problems with Field definitions"

class ValidationError(ValueError):
	"""Validation Error"""
__version__ = "$Revision$".split(":")[1][:-1].strip()
