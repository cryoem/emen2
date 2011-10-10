# $Id$
'''Exceptions

Classes:
	SecurityError
	SessionError
	AuthenticationError
	DisabledUserError
	ValidationError
	ExistingKey
	TimeError
'''

# Security Errors
class SecurityError(Exception):
	"Security error"
	code = 401

class SessionError(SecurityError):
	"Session expired"

class AuthenticationError(SecurityError):
	"Invalid account name or password"

class DisabledUserError(SecurityError):
	"Disabled user"


# Validation Errors
class ValidationError(ValueError):
	"""Validation error"""

class ExistingKey(ValueError):
	"This account name or email is already in use"


# Time out
class TimeError(Exception):
	"""Operation timed out"""


__version__ = "$Revision$".split(":")[1][:-1].strip()
