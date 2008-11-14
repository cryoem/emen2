import time
from UserDict import DictMixin


def format_string_obj(dict,keylist):
		"""prints a formatted version of an object's dictionary"""
		r=["{"]
		for k in keylist:
				if (k==None or len(k)==0) : r.append("\n")
				else:
						try:
								r.append("\n%s: %s"%(k,str(dict[k])))
						except:
								r.append("\n%s: None"%k)
		r.append(" }\n")
		return "".join(r)

class Context:
		"""Defines a database context (like a session). After a user is authenticated
		a Context is created, and used for subsequent access."""

		attr_user = set([])
		attr_admin = set(["ctxid","db","user","groups","host","time","maxidle"])
		attr_all = attr_user | attr_admin

		def __init__(self,ctxid=None,db=None,user=None,groups=None,host=None,maxidle=14400):
				self.ctxid=ctxid						# unique context id
				self.db=db										# Points to Database object for this context
				self.user=user								# validated username
				self.groups=groups or []						# groups for this user
				self.host=host								# ip of validated host for this context
				self.time=time.time()				 # last access time for this context
				self.maxidle=maxidle

		# Contexts cannot be serialized
		def __str__(self): return format_string_obj(self.__dict__,
																								["ctxid","user",
																								 "groups","time",
																								 "maxidle"])		
				
				
class User(DictMixin):
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
		attr_user = set(["privacy", 'modifytime'])
		attr_admin = set(["signupinfo","name","email","username","groups","disabled","password",
											"creator","creationtime","record"])
		attr_all = attr_user | attr_admin
		
		def __init__(self,d=None, **kwargs):
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
				kwargs.update(d or {})
				self.username=kwargs.get('username') 
				self.password=kwargs.get('password') 
				self.groups=kwargs.get('groups', [-4])
				self.disabled=kwargs.get('disabled',0) 
				self.privacy=kwargs.get('privacy',0) 
				self.creator=kwargs.get('creator',0) 
				self.creationtime=kwargs.get('creationtime')
				self.modifytime = kwargs.get('modifytime')
				self.record = kwargs.get('record') 
				self.name = kwargs.get('name')
				self.email = kwargs.get('email')
				self.signupinfo = {}

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

		def items_dict(self):
				ret = {}
				for k in self.attr_all:
						ret[k]=self.__dict__[k]
				return ret				


		def fromdict(self,d):
				for k,v in d.items():
						self.__dict__[k]=v
				self.validate()

		# ian: removed a bunch of methods that didn't actually work and weren't needed.										 
		
		#################################				 
		# validation methods
		#################################		 

		def validate(self):

				#if set(self.__dict__.keys())-self.attr_all:	
						#raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)
				for i in set(self.__dict__.keys())-self.attr_all:
					del self.__dict__[i]

				try:
						str(self.email)
				except:
						raise AttributeError,"Invalid value for email"
						
				if self.name != None:		 
						try:
								list(self.name)
								str(self.name)[0]
								str(self.name)[1]
								str(self.name)[2]
						except:
								raise AttributeError,"Invalid name format."

				try: 
						list(self.groups)
				except:
						raise AttributeError,"Groups must be a list."

				try:
						if self.record != None: int(self.record)
				except:
						raise AttributeError,"Record pointer must be integer"
				
				if self.privacy not in [0,1,2]:
						raise AttributeError,"User privacy setting may be 0, 1, or 2."

				if self.password != None and len(self.password) != 40:
						raise AttributeError,"Invalid password hash; use setpassword to update"

				if self.disabled not in [0,1]:
						raise AttributeError,"Disabled must be 0 (active) or 1 (disabled)"
				
				

class WorkFlow(DictMixin):
		"""Defines a workflow object, ie - a task that the user must complete at
		some point in time. These are intended to be transitory objects, so they
		aren't implemented using the Record class. 
		Implementation of workflow behavior is largely up to the
		external application. This simply acts as a repository for tasks"""

		attr_user = set(["desc","wftype","longdesc","appdata"])
		attr_admin = set(["wfid","creationtime"])
		attr_all = attr_user | attr_admin

		def __init__(self,d=None):
				self.wfid=None								# unique workflow id number assigned by the database
				self.wftype=None
				# a short string defining the task to complete. Applications
				# should select strings that are likely to be unique for
				# their own tasks
				self.desc=None								# A 1-line description of the task to complete
				self.longdesc=None						# an optional longer description of the task
				self.appdata=None						 # application specific data used to implement the actual activity
				self.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")

				if (d):
						self.update(d)


		#################################				 
		# repr methods
		#################################
				
		def __str__(self):
				return str(self.__dict__)

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

		def items_dict(self):
				ret = {}
				for k in self.attr_all:
						ret[k]=self.__dict__[k]
				return ret

		#################################				 
		# Validation methods
		#################################

		def validate(self):
			pass
				#if set(self.__dict__.keys())-self.attr_all:
				#		 raise AttributeError,"Invalid attributes: %s"%",".join(set(self.__dict__.keys())-self.attr_all)

import emen2.Database
emen2.Database.User = User
emen2.Database.Context = Context
emen2.Database.WorkFlow = WorkFlow