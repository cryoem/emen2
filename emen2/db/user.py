import time
import operator
import hashlib
import random
import UserDict
import re
import weakref

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

import emen2.Database.exceptions
import emen2.Database.dataobject


# Old doc:
#
# """This defines a database user, note that group 0 membership is required to
#  add new records. Approved users are never deleted, only disabled,
#  for historical logging purposes. -1 group is for database administrators.
#  -2 group is read-only administrator. Only the metadata below is persistenly
#  stored in this record. Other metadata is stored in a linked "Person" Record
#  in the database itself once the user is approved.
#
# Parameters are: username,password (hashed),
# 				groups (list),disabled,
# 				privacy,creator,creationtime
# """ """


# ian: todo: upgrade to BaseDBObject
# class User(object, UserDict.DictMixin):
class User(emen2.Database.dataobject.BaseDBObject):

	# non-admin users can only change their privacy setting directly
	@property
	def attr_user(self):
		return set(["privacy", "modifytime", "password", "modifyuser", "signupinfo","_ctx"])
	@property
	def attr_admin(self):
		return set(["email","groups","username","disabled","creator","creationtime","record","childrecs"])

	#@property
	#def _ctx(self):
	#	return self._ctx
	#@_ctx.setter
	#def _ctx(self, value):
	#	self._ctx = value


	def init(self, d=None, **_k):
		"""User class, takes either a dictionary or a set of keyword arguments
		as an initializer

		Recognized keys:
			username --string
					username for logging in, First character must be a letter.
			password -- string
					sha1 hashed password
					TODO: should be salted but is not
			groups -- list
					user group membership
					TODO: should be made more flexible
					magic groups are:
							0 = add new records,
							-1 = administrator,
							-2 = read-only administrator
			disabled --int
					if this is set, the user will be unable to login
			privacy -- int
					1 conceals personal information from anonymous users,
					2 conceals personal information from all users
			creator -- int, string?
					administrator who approved record, link to username?
			record -- int
					link to the user record with personal information
			creationtime -- int or datetime?
			modifytime -- int or datetime?

			these are required for holding values until approved; email keeps
			original signup address. name is removed after approval.
			name -- string
			email --string
		"""
		_k.update(d)
		ctx = _k.pop('ctx', None)

		# these are basically required arguments...
		self.username = _k.get('username', None)
		self.username = re.sub("\W", "", self.username)

		self.password = self.__setpassword(_k.get('password',""))

		self.disabled = _k.get('disabled',0)
		self.privacy = _k.get('privacy',0)

		self.record = _k.get('record', None)

		self.signupinfo = _k.get('signupinfo', {})

		self.childrecs = _k.get('childrecs', {})

		self.creator = _k.get('creator',0)
		self.creationtime = _k.get('creationtime', None)
		self.modifytime = _k.get('modifytime', None)
		self.modifyuser = _k.get('modifyuser', None)

		self.email = _k.get('email', None)

		self.__setsecret()

		self._ctx = None
		self.setContext(ctx)


	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		try: odict['_ctx'] = None
		except BaseException, e: print e

		try: odict['userrec'] = None
		except: print e

		return odict


	#################################
	# mapping methods
	#################################

	def __delitem__(self, key):
		raise AttributeError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)


	def upgrade(self):
		pass




	#################################
	# User methods
	#################################
	def getuserrec(self, getrecord=True, lnf=False):
		if getrecord and self.record is not None:
			self.userrec = self._ctx.db.getrecord(self.record, filt=True) or {}
			self.displayname = self.__formatusername(lnf=lnf)
		else:
			self.userrec = {}
			self.displayname = self.username
			self.email = None


	def __formatusername(self, lnf=False):
		if not self.userrec:
			return self.username

		nf = self.userrec.get("name_first")
		nm = self.userrec.get("name_middle")
		nl = self.userrec.get("name_last")

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
			return self.username

		return uname



	#################################
	# validation methods
	#################################

######ed: TODO: move these validation routines to a validation class
	def validationwarning(self, msg, e=None, warning=False):
		if e == None: e = ValueError
		if warning: g.warn("Validation warning: %s: %s"%(self.username, msg))
		elif e: raise e, msg


	def validate(self, warning=False):
		for i in set(self.__dict__.keys())-self.attr_all:
			if not i.startswith('_'):
				del self.__dict__[i]


		try:
			if self.record != None:
				self.record = int(self.record)
		except BaseException, e:
			self.validationwarning("Record pointer must be integer", warning=warning)


		if self.privacy not in [0,1,2]:
			self.validationwarning("User privacy setting may be 0, 1, or 2.", warning=warning)


		if self.password != None and len(self.password) != 40:
			self.validationwarning("Invalid password hash; use setpassword to update", warning=warning)


		try:
			self.disabled = bool(self.disabled)
		except BaseException, e:
			self.validationwarning("Disabled must be 0 (active) or 1 (disabled)", warning=warning)


		# simple email checking...
		if not self.email:
			self.validationwarning("No email specified: '%s'"%self.email, warning=warning)

		self.email = unicode(self.email)
		if not re.match("(\S+@\S+)",self.email):
			self.validationwarning("Invalid email format '%s'"%self.email, warning=warning)


	def __hashpassword(self, password):
		return hashlib.sha1(unicode(password)).hexdigest()


	def checkpassword(self, password):
		if self.disabled:
			exception = (emen2.Database.exceptions.DisabledUserError,
						emen2.Database.exceptions.DisabledUserError.__doc__ % self.username)
			raise exception[0], exception[1]

		result = False
		if self._ctx and self._ctx.checkadmin(): result = True
		elif self.password == None: result = True
		elif self.password != None and self.__hashpassword(password) == self.password:
			result = True
		return result


	def __setpassword(self, password):
		if password and len(password) < 6:
			self.validationwarning("Password too short; minimum 6 characters required", warning=False)
		self.password = self.__hashpassword(password)


	def setpassword(self, oldpassword, newpassword):
		self.checkpassword(newpassword)
		self.__setpassword(newpassword)


	def setemail(self, value):
		self.email = value


	def getemail(self, value):
		return self.email



	def validate_secret(self, secret):
		if self.__secret == secret:
			self.__secret = None
			return True


	def __setsecret(self):
		self.__secret = hashlib.sha1(str(self.username) + str(id(self)) + str(time.time()) + str(random.random())).hexdigest()


	# def get_secret(self):
	# 		return self.__secret
	#
	#
	# def kill_secret(self):
	#	self.__secret = None

	# def create_childrecords(self):
	# 	'''create records to be chldren of person record.
	# 			childrecs format:
	# 				{ rectype : { 'data': {},
	# 									'parents': []
	# 				}}
	# 	'''
	# 	def _step(rectype, recdata):
	# 		data = recdata.get('data', recdata)
	# 		rec = self._ctx.db.newrecord(rectype)
	# 		rec.update(data)
	# 		return rec, recdata.get('parents', [])
	# 	return [_step(rectype, recdata) for rectype, recdata in self.childrecs.iteritems()]

