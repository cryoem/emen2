class SecurityError(Exception):
    "Exception for a security violation"

# ian
class SessionError(KeyError):
    "Session Expired"

# ed
class AuthenticationError(ValueError):
    "Invalid Username or Password"
    
# ed
class DisabledUserError(ValueError):
    "User %s disabled"

class FieldError(Exception):
    "Exception for problems with Field definitions"
