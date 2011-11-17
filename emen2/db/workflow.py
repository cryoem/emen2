# $Id$
"""Workflow

Classes:
	Workflow
	WorkflowDB

"""

import time
import operator
import hashlib
import random
import re
import weakref

# EMEN2 imports
import emen2.db.btrees

# ian: todo: currently deprecated until this is rewritten

class WorkFlow(emen2.db.dataobject.BaseDBObject):
	"""Workflow.

	Provides the following additional attributes:
		wfid			Unique ID assigned by database
		wftype			Application-defined WorkFlow type
		desc_short		Short summary of WorkFlow
		desc_long		Detailed WorkFlow description
		appdata			Application-defined data

	Defines a workflow object, ie - a task that the user must complete at some
	point in time. These are intended to be transitory objects, so they aren't
	implemented using the Record class. Implementation of workflow behavior is
	largely up to the external application. This simply acts as a repository
	for tasks
	"""



	def init(self, d=None):
		# unique workflow id number assigned by the database
		self.wfid = None
		self.wftype = None

		# A 1-line description of the task to complete
		self.desc_short = None

		# an optional longer description of the task
		self.desc_long = None

		# application specific data used to implement the actual activity
		self.appdata = None



class WorkFlowDB(emen2.db.btrees.DBODB):
	dataclass = WorkFlow


__version__ = "$Revision$".split(":")[1][:-1].strip()
