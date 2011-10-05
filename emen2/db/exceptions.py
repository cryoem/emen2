# $Id$

# class EMEN2Error(Exception):
# 	def __init__(self, value):
# 		self.value = value
# 	def __str__(self):
# 		return repr(self.value)

class SecurityError(Exception):
    "Security error"

class SessionError(KeyError):
    "Session expired"

class AuthenticationError(ValueError):
    "Invalid account name or password"

class ExistingAccount(ValueError):
	"This account name or email is already in use"

class DisabledUserError(ValueError):
    "Disabled user"

class ValidationError(ValueError):
	"""Validation error"""

class TimeError(Exception):
	"""Operation timed out"""



__version__ = "$Revision$".split(":")[1][:-1].strip()
