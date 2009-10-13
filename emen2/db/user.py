import time
from UserDict import DictMixin
import operator
import hashlib


import emen2.Database.database
import emen2.Database.datastorage
import emen2.globalns
g = emen2.globalns.GlobalNamespace()


import hashlib
import random


def format_string_obj(dict,keylist):
		"""prints a formatted version of an object's dictionary"""
		r=["{"]
		for k in keylist:
				if (k==None or len(k)==0) : r.append("\n")
				else:
						try:
								r.append("\n%s: %s"%(k,unicode(dict[k])))
						except:
								r.append("\n%s: None"%k)
		r.append(" }\n")
		return "".join(r)



class Context:
		"""Defines a database context (like a session). After a user is authenticated
		a Context is created, and used for subsequent access."""

		attr_user = set()
		attr_admin = set()
		attr_all = attr_user | attr_admin


		# ian: todo: put current txn in ctx?
		def __init__(self, ctxid=None, db=None, username=None, user=None, groups=None, host=None, maxidle=14400):

				self.db = db	# Points to Database object for this context

				self.ctxid = ctxid	# unique context id
				if not self.ctxid:
					self.ctxid = hashlib.sha1(username + unicode(host) + unicode(time.time()) + unicode(random.random())).hexdigest()


				self._user = user	# validated user instance, w/ user record, displayname, groups
				self.username = username # login name, fall back if user.username does not exist

				self.host = host # ip of validated host for this context
				self.time = time.time()	# last access time for this context
				self.maxidle = maxidle
				
				if db != None:
					self.getuser()



		def getuser(self, txn=None):
			# the _user has to be set before we can add the user record....
			self._user = self.db.getuser(self.username, getrecord=False, ctx=self, txn=txn)
			self._user = self.db.getuser(self.username, getrecord=True, ctx=self, txn=txn)


		def __getgroups(self):
			if self._user:
				return self._user.groups
			return set(["anon"])

		groups = property(__getgroups)


		def checkadmin(self):
			if ("admin" in self.groups):
					return True
			return False


		def checkreadadmin(self):
			if ("admin" in self.groups) or ("readadmin" in self.groups):
					return True
			return False


		def checkcreate(self):
			if "create" in self.groups or "admin" in self.groups:
					return True
			return False




class Group(object, DictMixin):

	attr_user = set(["privacy", "modifytime","modifyuser","permissions"])
	attr_admin = set(["name","disabled","creator","creationtime"])
	attr_all = attr_user | attr_admin


	def __init__(self, d=None, **kwargs):
		kwargs.update(d or {})
		ctx = kwargs.get('ctx',None)

		self.name = kwargs.get('name')
		self.disabled = kwargs.get('disabled',False)
		self.privacy = kwargs.get('privacy',False)
		self.creator = kwargs.get('creator',None)
		self.creationtime = kwargs.get('creationtime',None)
		self.modifytime = kwargs.get('modifytime',None)
		self.modifyuser = kwargs.get('modifyuser',None)

		self.setpermissions(kwargs.get('permissions'))

		if ctx:
			self.creator = ctx.username
			self.adduser(3, self.creator)
			self.creationtime = ctx.db.gettime()
			self.validate(ctx=ctx)

		#self.__permissions = kwargs.get('permissions')



	def members(self):
		return set(reduce(operator.concat, self.__permissions))


	def owners(self):
		return self.__permissions[3]


	def adduser(self, level, users, reassign=1):

		level=int(level)

		p = [set(x) for x in self.__permissions]
		if not -1 < level < 4:
			raise Exception, "Invalid permissions level; 0 = read, 1 = comment, 2 = write, 3 = owner"

		if not hasattr(users,"__iter__"):
			users=[users]

		# Strip out "None"
		users = set(filter(lambda x:x != None, users))

		if not users:
			return

		if reassign:
			p = [i-users for i in p ]

		p[level] |= users

		p[0] -= p[1] | p[2] | p[3]
		p[1] -= p[2] | p[3]
		p[2] -= p[3]

		self.setpermissions(p)


	##########################################
	# taken from Record
	##########################################

	def removeuser(self, users):

		p = [set(x) for x in self.__permissions]
		if not hasattr(users,"__iter__"):
			users = [users]
		users = set(users)
		p = [i-users for i in p]

		self.setpermissions(p)
		#self.__permissions = tuple([tuple(i) for i in p])


	def __partitionints(self, i):
		ints = []
		strs = []
		for j in i:
			try:
				ints.append(int(j))
			except:
				strs.append(unicode(j))
		return ints + strs


	def __checkpermissionsformat(self, value):
		if value == None:
			value = ((),(),(),())

		try:
			if len(value) != 4:
				raise ValueError
			for j in value:
				if not hasattr(value,"__iter__"):
					raise ValueError
		except ValueError:
			#self.validationwarning("invalid permissions format: %s"%value)
			raise

		r = [self.__partitionints(i) for i in value]

		return tuple(tuple(x) for x in r)


	def setpermissions(self, value):
		#if not self.isowner():
		#	raise SecurityError, "Insufficient permissions to change permissions"
		self.__permissions = self.__checkpermissionsformat(value)


	def getpermissions(self):
		return self.__permissions



	################################

	def validate(self, ctx=None):
		return True

	####
	#def isowner(self):
	#	return

	################################
	# mapping methods
	################################
	def __getitem__(self,key):
		if key == "permissions":
			return self.getpermissions()
		return self.__dict__.get(key)

	def __setitem__(self,key,value):
		if key == "permissions":
			return self.setpermissions(value)
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key

	def __delitem__(self,key):
		raise AttributeError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)



class User(object, DictMixin):
	"""This defines a database user, note that group 0 membership is required to
	 add new records. Approved users are never deleted, only disabled,
	 for historical logging purposes. -1 group is for database administrators.
	 -2 group is read-only administrator. Only the metadata below is persistenly
	 stored in this record. Other metadata is stored in a linked "Person" Record
	 in the database itself once the user is approved.

	Parameters are: username,password (hashed),
					groups (list),disabled,
					privacy,creator,creationtime
	"""

	# non-admin users can only change their privacy setting directly
	attr_user = set(["privacy", "modifytime", "password", "modifyuser", "signupinfo"])
	attr_admin = set(["email","groups","username","disabled","creator","creationtime","record","childrecs"])
	attr_all = attr_user | attr_admin


	def __init__(self, _d=None, **kwargs):
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



		_d = _d or {}
		kwargs.update( (k,v) for k,v in _d.iteritems() if k not in kwargs)

		ctx = kwargs.get('ctx',None)


		self.username = kwargs.get('username')
		self.password = kwargs.get('password')

		self.disabled = kwargs.get('disabled',0)
		self.privacy = kwargs.get('privacy',0)

		self.record = kwargs.get('record')

		self.signupinfo = {}
		
		self.childrecs = kwargs.get('childrecs', {})

		self.creator = kwargs.get('creator',0)
		self.creationtime = kwargs.get('creationtime')
		self.modifytime = kwargs.get('modifytime')
		self.modifyuser = kwargs.get('modifyuser')

		self.email = kwargs.get('email')

		self.__secret = kwargs.get('secret')

		# read only attributes, set at getuser time
		# self.groups = None
		# self.userrec = None
		# self.email = None

		# self.groups = set() #kwargs.get('groups', [-4])
		# self.name = kwargs.get('name')


		if ctx:
			pass



	#################################
	# mapping methods
	#################################

	def __getitem__(self,key):
		return self.__dict__.get(key)
		#return self.__dict__[key]

	def __setitem__(self,key,value):
		if key in self.attr_all:
			self.__dict__[key]=value
		else:
			raise KeyError,"Invalid key: %s"%key

	def __delitem__(self,key):
		raise AttributeError,"Key deletion not allowed"

	def keys(self):
		return tuple(self.attr_all)


	#################################
	# User methods
	#################################


	#################################
	# validation methods
	#################################

	def validate(self, ctx=None):
		#if set(self.__dict__.keys())-self.attr_all:
			#raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)

		for i in set(self.__dict__.keys())-self.attr_all:
			if not i.startswith('_'):
				del self.__dict__[i]

		try:
			if self.record != None:
				self.record = int(self.record)
		except BaseException, e:
			raise ValueError,"Record pointer must be integer"


		if self.privacy not in [0,1,2]:
			raise ValueError,"User privacy setting may be 0, 1, or 2."


		if self.password != None and len(self.password) != 40:
			raise ValueError,"Invalid password hash; use setpassword to update"


		try:
			self.disabled = bool(self.disabled)
		except BaseException, e:
			raise ValueError,"Disabled must be 0 (active) or 1 (disabled)"


		# simple email checking...
		if not self.email:
			raise ValueError,"Invalid email '%s'"%self.email
			
		self.email = unicode(self.email)
		if not re.match("(\S+@\S+)",self.email):
			raise ValueError,"Invalid email '%s'"%self.email




	def checkpassword(self, password):
		pass
		
		
	def setpassword(self, oldpassword, newpassword):
		if len(newpassword) < 6:
			raise ValueError, "Password too short; minimum 6 characters required"

		s = hashlib.sha1(newpassword).hexdigest()

		if self.password != None and s != self.password:
			raise SecurityError, "Could not update password; incorrect password given"
		self.password = s
		
	def setemail(self, value):
		self.email = value


	def getemail(self, value):
		return self.email
		
	
		
		

	def validate_secret(self, secret):
		result = self.__secret == secret
		return result


	def get_secret(self):
			return self.__secret


	def kill_secret(self):
		self.__secret = None


	def create_childrecords(self, ctx, txn=None):
		'''create records to be chldren of person record.
				childrecs format:
					{ rectype : { 'data': {},
										'parents': []
					}}
		'''
		def _step(rectype, recdata):
			data = recdata.get('data', recdata)
			rec = ctx.db.newrecord(rectype, ctx=ctx, txn=txn)
			rec.update(data)
			return rec, recdata.get('parents', [])
		return [_step(rectype, recdata) for rectype, recdata in self.childrecs.iteritems()]




class WorkFlow(object, DictMixin):
	"""Defines a workflow object, ie - a task that the user must complete at
	some point in time. These are intended to be transitory objects, so they
	aren't implemented using the Record class.
	Implementation of workflow behavior is largely up to the
	external application. This simply acts as a repository for tasks"""

	attr_user = set(["desc","wftype","longdesc","appdata"])
	attr_admin = set(["wfid","creationtime"])
	attr_all = attr_user | attr_admin

	def __init__(self, d=None, **kwargs):

		kwargs.update(d or {})
		ctx = kwargs.get('ctx',None)


		self.wfid=None								# unique workflow id number assigned by the database
		self.wftype=None
		# a short string defining the task to complete. Applications
		# should select strings that are likely to be unique for
		# their own tasks
		self.desc=None								# A 1-line description of the task to complete
		self.longdesc=None						# an optional longer description of the task
		self.appdata=None						 # application specific data used to implement the actual activity
		self.creationtime=time.strftime(emen2.Database.database.TIMESTR)

		if (d):
			self.update(d)


		if ctx:
			# update with ctx info...
			pass


	#################################
	# repr methods
	#################################

	def __str__(self):
			return unicode(self.__dict__)

	#################################
	# mapping methods
	#################################

	def __getitem__(self,key):
			return self.__dict__[key]

	def __setitem__(self,key,value):
			#if key in self.attr_all:
			self.__dict__[key]=value
			#else:
			#raise AttributeError,"Invalid attribute: %s"%key

	def __delitem__(self,key):
			raise AttributeError,"Attribute deletion not allowed"

	def keys(self):
			return tuple(self.attr_all)


	#################################
	# WorkFlow methods
	#################################


	#################################
	# Validation methods
	#################################

	def validate(self, ctx=None):
		pass
		#if set(self.__dict__.keys())-self.attr_all:
		#		 raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)



import emen2.Database
emen2.Database.User = User
emen2.Database.Context = Context
emen2.Database.WorkFlow = WorkFlow
emen2.Database.Group = Group
