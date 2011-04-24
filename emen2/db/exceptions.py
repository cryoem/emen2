# $Id$

# class EMEN2Error(Exception):
# 	def __init__(self, value):
# 		self.value = value
# 	def __str__(self):
# 		return repr(self.value)

class SecurityError(Exception):
    "Security Error"

class SessionError(KeyError):
    "Session Expired"

class AuthenticationError(ValueError):
    "Invalid Account Name or Password"
    
class DisabledUserError(ValueError):
    "Disabled User"

class ValidationError(ValueError):
	"""Validation Error"""

class TimeError(Exception):
	"""Operation timed out"""

__version__ = "$Revision$".split(":")[1][:-1].strip()