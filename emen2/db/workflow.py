# $Id$
import time
import operator
import hashlib
import random
import re
import weakref

import emen2.db.config
g = emen2.db.config.g()


# ian: todo: currently deprecated until this is rewritten

class WorkFlow(emen2.db.dataobject.BaseDBObject):
	"""Defines a workflow object, ie - a task that the user must complete at
	some point in time. These are intended to be transitory objects, so they
	aren't implemented using the Record class.
	Implementation of workflow behavior is largely up to the
	external application. This simply acts as a repository for tasks"""

	attr_user = set(["desc","wftype","longdesc","appdata", "wfid","creationtime"])

	def init(self, d=None):

		self.wfid = None								# unique workflow id number assigned by the database
		self.wftype = None

		# a short string defining the task to complete. Applications
		# should select strings that are likely to be unique for
		# their own tasks
		self.desc = None								# A 1-line description of the task to complete
		self.longdesc = None						# an optional longer description of the task
		self.appdata = None						 # application specific data used to implement the actual activity
		self.creationtime = gettime() #emen2.db.database.gettime()



	#################################
	# WorkFlow methods
	#################################


	#################################
	# Validation methods
	#################################
__version__ = "$Revision$".split(":")[1][:-1].strip()
