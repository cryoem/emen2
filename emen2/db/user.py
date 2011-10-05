# $Id$

import time
import operator
import hashlib
import random
import re
import weakref
import traceback

import emen2.db.btrees
import emen2.db.exceptions
import emen2.db.dataobject

import emen2.db.config
g = emen2.db.config.g()


# DBO that contains a password and email address
class BaseUser(emen2.db.dataobject.BaseDBObject):

	param_all = emen2.db.dataobject.BaseDBObject.param_all | set(['email', 'password'])
	param_required = set(['email', 'password'])
	username = property(lambda s:s.name)

	def init(self, d):
		super(BaseUser, self).init(d)

		# Required initialization params
		self.__dict__['email'] = self.validate_email(d.pop('email'))
		self.__dict__['password'] = self._hashpassword(self.validate_password(d.pop('password')))

		# Secret takes the format:
		# action type, args, ctime for when the token is set, and secret
		self.__dict__['_secret'] = None


	# Setters
	def _set_password(self, key, value, vtm=None, t=None):
		self.setpassword(None, value)
		return set(['password'])


	def _set_email(self, key, value, vtm=None, t=None):
		# This will always fail unless you're an admin --
		#	setemail requires either a password or auth token as arguments.
		self.setemail(value)
		return set(['email'])


	def isowner(self):
		return super(BaseUser, self).isowner() or self._ctx.username == self.name


	#################################
	# Password methods
	#################################

	def _hashpassword(self, password):
		password = unicode(password or '')
		if len(password) == 40:
			return password
		return hashlib.sha1(unicode(password)).hexdigest()


	def validate_password(self, password):
		# Only root is allowed to have no password. All user accounts must have a password.
		password = unicode(password or '')
		if len(password) < 6 and self.name != 'root':
			self.error("Password too short; minimum 6 characters required")
		return password


	def checkpassword(self, password):
		# This needs to work even if there is no Context set.
		if self.disabled:
			self.error(e=emen2.db.exceptions.DisabledUserError)

		# No password will always fail!
		if self.password and self._hashpassword(password) == self.password:
			return True
			
		try:
			if self._ctx.checkadmin():
				return True
		except AttributeError:
			pass

		# Sleep for 2 seconds any time there is a wrong password!!
		time.sleep(2)
		self.error(e=emen2.db.exceptions.AuthenticationError)


	def setpassword(self, oldpassword, newpassword, secret=None):
		# Check that we know the existing password, or an authentication secret
		# checkpassword will sleep 2 seconds for each failed attempt
		if not (self._checksecret('resetpassword', None, secret) or self.checkpassword(oldpassword)):
			self.error(e=emen2.db.exceptions.AuthenticationError)
		# You must be logged in as this user (or admin) AND know the old password.
		newpassword = self._hashpassword(self.validate_password(newpassword))
		self._set('password', newpassword, True)
		self._delsecret()


	def resetpassword(self):
		"""Reset the user password. This creates an internal 'secret' token that can be used to reset a password.
		The secret should never be accessible via public methods.
		"""
		# The second argument should be the email address
		self._setsecret('resetpassword', None)


	#################################
	# email setting/validation
	#################################

	def setemail(self, email, password=None, secret=None):
		email = self.validate_email(email)

		# Check that we know the existing password, or an authentication secret
		# Note: the auth token is bound both to the method (setemail) and the
		# 	specific requested email address.
		if self._checksecret('setemail', email, secret):
			self._set('email', email, self.isowner())
			self._delsecret()

		elif self.checkpassword(password):
			self._setsecret('setemail', email)

		else:
			self.error(e=emen2.db.exceptions.AuthenticationError)

		return self.email


	#################################
	# Secrets for account password resets
	#################################

	def _checksecret(self, action, args, secret):
		# I only want this to work on certain subclasses. See: User
		return False


	def _setsecret(self, action, args):
		# secret is set using __dict__ (like _ctx/_ptest) because it's a secret, and not a normal attribute.
		if not hasattr(self, '_secret'):
			self.__dict__['_secret'] = None

		if self._secret:
			if action == self._secret[0] and args == self._secret[1]:
				return

		secret = hashlib.sha1(str(self.name) + str(id(self)) + str(time.time()) + str(random.random())).hexdigest()
		self.__dict__['_secret'] = (action, args, secret, time.time())


	def _delsecret(self):
		self.__dict__['_secret'] = None


	#################################
	# validation methods
	#################################

	def validate_email(self, email):
		# if not re.match('(\S+@\S+)', email):
		# After a long discussion in #python, it is impossible to validate
		# 	emails other than checking for '@'
		email = unicode(email or '')
		if not email or '@' not in email:
			self.error("Invalid email format '%s'"%email)
		return email






signupinfo = set(["name_first", "name_middle", "name_last", "comments",	"institution",
	"department", "address_street", "address_city", "address_state", "address_zipcode",
	"country", "uri", "phone_voice", "phone_fax"])


class NewUser(BaseUser):
	# displayname, userrec, and groups are unset when committing, so they can skip validation.
	param_all = BaseUser.param_all | set(['signupinfo'])

	def validate_create(self):
		# Anyone can create a NewUSer
		return True


	def init(self, d):
		super(NewUser, self).init(d)
		# New users store signup info in a dict,
		# 	which is committed as a 'person' record when approved
		self.__dict__['signupinfo'] = {}


	# Setters
	def _set_signupinfo(self, key, value, vtm=None, t=None):
		self.setsignupinfo(value)
		return set(['signupinfo'])


	def setsignupinfo(self, update):
		self._set('signupinfo', update)
		self.validate()


	def validate(self, vtm=None, t=None):
		super(NewUser, self).validate(vtm=vtm, t=t)

		# Check signupinfo
		required = set(["name_first","name_last"])
		newsignup = {}

		for param, value in self.signupinfo.items():
			if not value:
				continue
				
			# These will be transferred to a Record
			try:
				value = self.validate_param(param, value, vtm=vtm)
			except ValueError:
				print "Couldn't validate new user signup field %s: %s"%(param, value)
				continue

			newsignup[param] = value

		for param in required:
			if not newsignup.get(param):
				raise ValueError, "Required param %s"%param


		if self.signupinfo.get('child'):
			newsignup['child'] = self.signupinfo['child']

		# print "Validated signup...."
		# print newsignup
		self.__dict__['signupinfo'] = newsignup


	# def setContext(...)
	#	Don't let non-admin users read this?





class User(BaseUser):
	"""User record. This contains the basic metadata information for a single user account, including username, password, primary email address, active/disabled, timestamps, and link to more complete user profile. Group membership is stored in Group instances, and set here by db.getuser by checking an index. If available during db.getuser, a copy of the profile record and the user's "displayname" will also be set.

	@attr name Username for logging in, first character must be a letter, no spaces
	@attr password SHA1 hashed password
	@attr disabled True if user is disabled, unable to login
	@attr privacy Privacy level; 1 conceals personal information from anonymous users, 2 conceals personal information from all users
	@attr record Record ID containing additional profile information
	@attr email Semi-validated email address
	@property groups Set by database when accessed
	@property userrec Copy of profile record; set by database when accessed
	@property displayname User "display name"; set by database when accessed
	"""

	# displayname, userrec, and groups are unset when committing, so they can skip validation.
	param_all = BaseUser.param_all | set(['privacy', 'disabled', 'displayname', 'userrec', 'groups', 'record'])

	# These get set during setContext and cleared before commit
	userrec = property(lambda s:s._userrec)
	displayname = property(lambda s:s._displayname)
	groups = property(lambda s:s._groups)


	def init(self, d):
		super(User, self).init(d)
		# Enabled/disabled, privacy level, and record ID pointer
		self.__dict__['disabled'] = False
		self.__dict__['privacy'] = 0
		self.__dict__['record'] = None


	# Validate
	def validate_create(self):
		if not self._ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Only admins may create new Users"


	#################################
	# Setters
	#################################

	# These are unvalidated parameters because they cleared when committing
	# They return an empty set because they don't really modify the User.

	def _set_groups(self, key, value, vtm=None, t=None):
		self._set('_groups', value, True)
		return set()

	def _set_displayname(self, key, value, vtm=None, t=None):
		self._set('_displayname', value, True)
		return set()

	def _set_userrec(self, key, value, vtm=None, t=None):
		self._set('_userrec', value, True)
		return set()


	# Users can set their own privacy level
	def _set_privacy(self, key, value, vtm=None, t=None):
		value = int(value)
		if value not in [0,1,2]:
			self.error("User privacy setting may be 0, 1, or 2.")
		return self._set(key, value, self.isowner())


	# Only admin can change enabled/disabled or record reference

	def _set_disabled(self, key, value, vtm=None, t=None):
		if self.name == self._ctx.username and value:
			self.error("Cannot disable self!")
		return self._set(key, bool(value), self._ctx.checkadmin())


	def _set_record(self, key, value, vtm=None, t=None):
		if value != None:
			value = int(value)
		return self._set(key, value, self._ctx.checkadmin())



	#################################
	# "Secret" Authentication tokens
	#################################

	# I only have this method available on User, and not BaseUser.
	def _checksecret(self, action, args, secret):
		#if and self._ctx.checkadmin():
		#	return True

		if not hasattr(self, '_secret'):
			self.__dict__['_secret'] = None

		# This should check expiration time...
		if action and secret and self._secret:
			if action == self._secret[0] and args == self._secret[1] and secret == self._secret[2]:
				return True

		return False


	#################################
	# Enable/disable
	#################################
	# These will go through setattr -> setitem -> set_{param}

	def enable(self):
		self.disabled = False


	def disable(self):
		self.disabled = True


	def setprivacy(self, privacy):
		self.privacy = privacy




	#################################
	# Displayname and profile Record
	#################################

	def getdisplayname(self, lnf=False, record=None):
		"""Get the user profile record from the current Context"""
		if self.record is None:
			return

		if not self._userrec:
			if not record:
				record = self._ctx.db.getrecord(self.record) or {}
			self._set('_userrec', record, True)

		d = self._formatusername(lnf=lnf)
		self._set('_displayname', d, True)
		return d


	def _formatusername(self, lnf=False):
		if not self._userrec:
			return self.name

		nf = self._userrec.get('name_first')
		nm = self._userrec.get('name_middle')
		nl = self._userrec.get('name_last')

		#if u["name_first"] and u["name_middle"] and u["name_last"]:
		if nf and nm and nl:
			if lnf:
				uname = "%s, %s %s" % (nl, nf, nm)
			else:
				uname = "%s %s %s" % (nf, nm, nl)

		elif nf and nl:
			if lnf:
				uname = "%s, %s" % (nl, nf)
			else:
				uname = "%s %s" % (nf, nl)

		elif nl:
			uname = nl

		elif nf:
			uname = nf

		else:
			return self.name

		return uname



	#################################
	# Access methods
	#################################

	def setContext(self, ctx, hide=True):
		super(User, self).setContext(ctx)

		# If the user has requested privacy, we return only basic info
		hide = self._ctx.username == 'anonymous' or self.privacy
		if self._ctx.checkreadadmin():
			hide = False

		p = {}
		if self._ctx.username != self.name and not self._ctx.checkreadadmin():
			p['password'] = None

		# You must access the User directly to get these attributes
		p['_secret'] = None

		# Hide basic details from anonymous users
		if hide:
			p['email'] = None
			p['record'] = None

		p['_userrec'] = {}
		p['_displayname'] = self.name
		p['_groups'] = set()

		self.__dict__.update(p)
		self.getdisplayname()





class UserDB(emen2.db.btrees.DBODB):
	dataclass = User

	def getbyemail(self, name, filt=True, ctx=None, txn=None):
		"""Lookup a user by name or email address. This is not a setContext lookup;
		cgets will also expand email addresses to usernames.
		"""
		name = unicode(name or '').strip()
		if not self.exists(name, txn=txn):
			found = self.getindex('email', txn=txn).get(name, txn=txn)
			if found:
				name = found.pop()
		return self.get(name, filt=filt, txn=txn)


	def expand(self, names, ctx=None, txn=None):
		"""Expand names, e.g. expanding * into children, or using an email address for a user"""
		if not isinstance(names, set):
			names = set(names)

		# Grumble.. some things like old-style binaries may have None for a user field.
		names -= set([None])

		# ian: todo: need to benchmark this...
		ind = self.getindex('email', txn=txn)
		add = set()
		remove = set()
		for i in names:
			if not self.exists(i, txn=txn):
				add |= ind.get(i, txn=txn)
				remove.add(i)

		names -= remove
		names |= add
		return names


	def new(self, *args, **kwargs):
		txn = kwargs.get('txn', None)

		# DB.new. This will check the main bdb for an existing name.
		user = super(UserDB, self).new(*args, **kwargs)

		# Check  if this email already exists
		indemail = self.getindex('email', txn=txn)
		if indemail.get(user.email, txn=txn):
			raise emen2.db.exceptions.ExistingAccount

		return user


	def openindex(self, param, txn=None):
		if param == 'email':
			ind = emen2.db.btrees.IndexDB(filename=self._indname(param), keytype='s', datatype='s', dbenv=self.dbenv)
		else:
			ind = super(UserDB, self).openindex(param, txn=txn)
		return ind


	def names(self, names=None, ctx=None, txn=None, **kwargs):
		# You need to be logged in to view this.
		if not ctx or ctx.username == 'anonymous':
			return set()
		return super(UserDB, self).names(names=names, ctx=ctx, txn=txn)




class NewUserDB(emen2.db.btrees.DBODB):
	dataclass = NewUser

	def new(self, *args, **kwargs):
		txn = kwargs.get('txn', None)
		newuser = super(NewUserDB, self).new(*args, **kwargs)

		# Check if any pending accounts have this email address
		for k,v in self.items(txn=txn):
			if newuser.email == v.email:
				raise emen2.db.exceptions.ExistingAccount, emen2.db.exceptions.ExistingAccount.__doc__

		# Check if this email already exists
		indemail = self.dbenv.user.getindex('email', txn=txn)
		if self.dbenv.user.exists(newuser.name, txn=txn) or indemail.get(newuser.email, txn=txn):
			raise emen2.db.exceptions.ExistingAccount, emen2.db.exceptions.ExistingAccount.__doc__

		return newuser


	def names(self, names=None, ctx=None, txn=None, **kwargs):
		# This requires admin access
		if not ctx or not ctx.checkadmin():
			raise emen2.db.exceptions.SecurityError, "Admin rights needed to view user queue"
		return super(NewUserDB, self).names(names=names, ctx=ctx, txn=txn)




__version__ = "$Revision$".split(":")[1][:-1].strip()
