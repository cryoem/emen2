import time
import operator
import hashlib
import random
import UserDict
import re
import weakref

import emen2.globalns
g = emen2.globalns.GlobalNamespace()


# ian: todo: currently deprecated until this is rewritten

class WorkFlow(object, UserDict.DictMixin):
	"""Defines a workflow object, ie - a task that the user must complete at
	some point in time. These are intended to be transitory objects, so they
	aren't implemented using the Record class.
	Implementation of workflow behavior is largely up to the
	external application. This simply acts as a repository for tasks"""

	attr_user = set(["desc","wftype","longdesc","appdata","_ctx"])
	attr_admin = set(["wfid","creationtime"])
	attr_all = attr_user | attr_admin

	def __init__(self, _d=None, **_k):

		_k.update(d or {})
		ctx = _k.get('ctx',None)


		self.wfid = None								# unique workflow id number assigned by the database
		self.wftype = None
		# a short string defining the task to complete. Applications
		# should select strings that are likely to be unique for
		# their own tasks
		self.desc = None								# A 1-line description of the task to complete
		self.longdesc = None						# an optional longer description of the task
		self.appdata = None						 # application specific data used to implement the actual activity
		self.creationtime = gettime() #emen2.Database.database.gettime()

		if (_d):
			self.update(_d)

		self.setContext(ctx)


	def __getstate__(self):
		"""the context and other session-specific information should not be pickled"""
		odict = self.__dict__.copy() # copy the dict since we change it
		try: del odict['_ctx']
		except:	pass
		return odict


	def setContext(self, ctx=None):
		if not ctx:
			return
		self._ctx = ctx #weakref.proxy(ctx)


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
	def validate(self, warning=False):
		pass
