# $Id$

import time
import operator
import hashlib
import random
import re
import weakref
import traceback


import emen2.db.exceptions
import emen2.db.dataobject
import emen2.db.config
g = emen2.db.config.g()



class User(emen2.db.dataobject.BaseDBObject):
	"""
	User record. This contains the basic metadata information for a single user account, including username, password, primary email address, active/disabled, timestamps, and link to more complete user profile. Group membership is stored in Group instances, and set here by db.getuser by checking an index. If available during db.getuser, a copy of the profile record and the user's "displayname" will also be set.

	These are normally created once and then manipulated using the appropriate API methods (setpassword, setemail, etc.) instead of get/modify/commit.

	@attr username Username for logging in, first character must be a letter, no spaces
	@attr password SHA1 hashed password
	@attr disabled True if user is disabled, unable to login
	@attr privacy Privacy level; 1 conceals personal information from anonymous users, 2 conceals personal information from all users
	@attr record Record ID containing additional profile information
	@attr email Semi-validated email address

	@attr groups Set by database when accessed
	@attr userrec Copy of profile record; set by database when accessed
	@attr displayname User "display name"; set by database when accessed

	@attr creationtime
	@attr creator
	@attr modifytime
	@attr modifyuser

	"""

	attr_user = set(["privacy", "modifytime", "password", "modifyuser", "signupinfo","email","groups","username","disabled","creator","creationtime","record","displayname","userrec"])
	name = property(lambda s:s.username)

	def init(self, d=None):
		# ian: todo: pw should be salted
		# these are basically required arguments...
		self.username = d.get('username')
		# re.sub("\W", "", d.get('username', None)).lower()
		self.password = None
		self._setpassword(d.get('password'))
		self.email = d.get('email', None)

		if not self.username or not self.email:
			raise ValueError, "Username, password, and email required"

		self.disabled = d.get('disabled',0)
		self.privacy = d.get('privacy',0)
		self.record = d.get('record', None)
		self.creator = d.get('creator',0)
		self.creationtime = d.get('creationtime', None)
		self.modifytime = d.get('modifytime', None)
		self.modifyuser = d.get('modifyuser', None)
		
		self.userrec = {}
		self.groups = set()
		self.displayname = None		
		self.signupinfo = d.get('signupinfo', {})

		# Secret takes the format:
		# action type, args, ctime for when the token is set, and secret
		self._secret = None




	#################################
	# User methods
	#################################


	def __getstate__(self):
		"""Context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		odict['_ctx'] = None
		odict['userrec'] = {}
		odict['displayname'] = self.username
		odict['groups'] = set()
		return odict


	#################################
	# Password methods
	#################################


	def _hashpassword(self, password):
		if password == None:
			password = ''
		if len(password) == 40:
			return password
		return hashlib.sha1(unicode(password)).hexdigest()


	def checkpassword(self, password):
		if self.disabled:
			exception = (emen2.db.exceptions.DisabledUserError, emen2.db.exceptions.DisabledUserError.__doc__%self.username)
			raise exception[0], exception[1]

		if self._ctx:
			if self._ctx.checkadmin():
				return True

		result = False
		if self.password != None and self._hashpassword(password) == self.password:
			result = True

		if result == False:
			time.sleep(2)

		return result


	def setpassword(self, oldpassword, newpassword, secret=None):
		if self.checkpassword(oldpassword):
			self._setpassword(newpassword)
		elif self._checksecret('resetpassword', None, secret):
			self._setpassword(newpassword)
		else:
			raise emen2.db.exceptions.SecurityError, "Invalid password or authentication token"
		self._delsecret()	


	def _setpassword(self, newpassword):
		if newpassword == None and self.username != "root":
			self.validationwarning("No password specified; minimum 6 characters required", warning=False)
		if len(newpassword) < 6:
			self.validationwarning("Password too short; minimum 6 characters required", warning=False)
		self.password = self._hashpassword(newpassword)



	def resetpassword(self):
		"""Reset the user password. This creates an internal 'secret' token that can be used to reset a password. The secret should never be accessible via public methods."""
		self._setsecret('resetpassword', None)
		

	#################################
	# email setting/validation
	#################################


	def setemail(self, email, password=None, secret=None):
		msg = "Invalid password or authentication token"
		ret = None
		
		if self._checksecret('setemail', email, secret):
			self.email = email
			ret = self.email
			self._delsecret()

		elif self.checkpassword(password):
			self._setsecret('setemail', email)				
		
		else:
			raise emen2.db.exceptions.SecurityError, msg

		return ret


	def getemail(self, value):
		return self.email


	#################################
	# Secrets for account password resets
	#################################


	def _checksecret(self, action, args, secret):
		print "Checking secret:"
		print action, args, secret
		print self._secret
		
		if self._ctx.checkadmin():
			return True
			
		# This should check expiration time...
		if action and secret and self._secret:
			if action == self._secret[0] and args == self._secret[1] and secret == self._secret[2]:
				return True

		return False


	def _setsecret(self, action, args):
		if self._secret:
			if action == self._secret[0] and args == self._secret[1]:
				return
				
		secret = hashlib.sha1(str(self.username) + str(id(self)) + str(time.time()) + str(random.random())).hexdigest()
		self._secret = (action, args, secret, time.time())


	def _delsecret(self):
		self._secret = None



	#################################
	# Displayname and profile Record
	#################################

	def getuserrec(self, lnf=False):
		"""Get the user profile record from the current Context"""
		if self.record is not None:
			self.userrec = self._ctx.db.getrecord(self.record, filt=True) or {}
			self.displayname = self._formatusername(lnf=lnf)


	def _formatusername(self, lnf=False):
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


	def validate(self, warning=False):
		for i in set(self.__dict__.keys())-self.attr_user:
			if not i.startswith('_'):
				del self.__dict__[i]

		# grumble..
		# ian: todo: fix this..
		self.username = re.sub("\W", "", self.username).lower()

		try:
			if self.record != None:
				self.record = int(self.record)
		except BaseException, e:
			self.validationwarning("Record pointer must be integer", warning=warning)


		if self.privacy not in [0,1,2]:
			self.validationwarning("User privacy setting may be 0, 1, or 2.", warning=warning)


		if self.password == None:
			self.validationwarning("No password set!", warning=warning)

		if self.password != None and len(self.password) != 40:
			self.validationwarning("Invalid password hash; use setpassword to update", warning=warning)

		try:
			self.disabled = bool(self.disabled)
		except BaseException, e:
			self.validationwarning("Disabled must be 0 (active) or 1 (disabled)", warning=warning)


		# simple email checking...
		# if not self.email:
		#	self.validationwarning("No email specified: '%s'"%self.email, warning=warning)
		if not self.email or self.email == 'None':
			self.email = ''

		self.email = unicode(self.email or '')
		if self.email:
			if not re.match("(\S+@\S+)",self.email):
				self.validationwarning("Invalid email format '%s'"%self.email, warning=warning)



__version__ = "$Revision$".split(":")[1][:-1].strip()
