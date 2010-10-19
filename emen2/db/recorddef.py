# $Id$

import re

import emen2.db.dataobject
import emen2.db.validators
import emen2.db.config
g = emen2.db.config.g()



class RecordDef(emen2.db.dataobject.BaseDBObject):
	"""RecordDefs, aka Protocols, function as templates for Records. Each Record must be an instance of a defined RecordDef.
	The RecordDef defines the default parameters that make up a record, and a set of presentation formats ('views'). The 'mainview'
	is parsed for parameters and becomes the default view. Other important views that are used by the web interface are:

		recname			A simple title for each record built from record values
		tabularview		Columns to use in table views

	RecordDefs may have parent/child relationships, similar to Records.

	@attr name Name of RecordDef
	@attr desc_short Short description. Shown in many places in the interface as the label for this RecordDef.
	@attr desc_long Long description. Shown as help in new record page.
	@attr mainview Default protocol view. This should be an expanded form, similar to a lab notebook or experimental protocol. This should be IMMUTABLE, as it may describe a particular experiment. However, admins are allowed to edit the mainview if it is absolutely necessary.
	@attr views Dictionary of additional views. Usually recname/tabularview will be defined, as well as defaultview
	@attr private Mark this RecordDef as private. False for public access, True for private. If private, you must be admin or able to read a record of this type to access the RecordDef
	@attr typicalchld A list of RecordDefs that are generally seen as children of this RecordDef. This refers to Records, not the RecordDef ontology, which describes relationships between RecordDefs themselves. e.g., "grid_imaging" Records are often children of "subprojects."
	@attr params Dictionary of all params found in all views (keys), with any default values specified (as value)
	@attr paramsK List of all params found in all views
	@attr paramsR Parameters that are required for a Record of this RecordDef to validate.
	@attr owner Current owner of RecordDef. May be different than creator. Gives permission to edit views.
	@attr creator Creator
	@attr creationtime Creation time
	@attr modifyuser Last change user
	@attr modifytime Last change time
	@attr uri Source URI

	"""

	attr_user = set(["mainview","views","private","typicalchld","desc_long","desc_short","name","params", "paramsR", "paramsK","owner","creator","creationtime","uri"])


	def init(self, d=None):
		# the name of the current RecordDef, somewhat redundant, since also stored as key for index in Database
		self.name = d.get("name")

		# Dictionary of additional (named) views for the record
		self.views = d.get("views") or {"recname":"$$rectype $$creator $$creationtime"}

		# a string defining the experiment with embedded params
		# this is the primary definition of the contents of the record
		self.mainview = d.get("mainview") or "$$rectype $$creator $$creationtime"

		# if this is 1, this RecordDef may only be retrieved by its owner (which may be a group)
		# or by someone with read access to a record of this type
		self.private = d.get("private", 0)

		# A list of RecordDef names of typical child records for this RecordDef
		# implicitly includes subclasses of the referenced types
		self.typicalchld = d.get("typicalchld",[])

		# A dictionary keyed by the names of all params used in any of the views
		# values are the default value for the field.
		# this represents all params that must be defined to have a complete
		# representation of the record. Note, however, that such completeness
		# is NOT REQUIRED to have a valid Record
		self.params = {}

		# ordered keys from params()
		self.paramsK = []
		
		# required parameters (will throw exception on commit if empty)
		self.paramsR = set()

		# The owner of this record
		self.owner = d.get("owner") or self._ctx.username

		# original creator of the record
		self.creator = d.get("creator") or self._ctx.username

		# creation date
		self.creationtime = d.get("creationtime") or self._ctx.db.gettime()

		# Source of RecordDef
		self.uri = d.get("uri")

		# Short description
		self.desc_short = d.get("desc_short")

		# Long description
		self.desc_long = d.get("desc_long")

		self.findparams()



	def __setattr__(self,key,value):
		"""If mainview is updated, update params"""

		self.__dict__[key] = value

		if key == "mainview":
			self.findparams()


	#################################
	# RecordDef methods
	#################################

	def accessible(self):
		'''Does current Context allow access to this RecordDef?'''
		if not self._ctx:
			return False

		result = False
		if not self.private:
			result = True
		elif self._ctx.username == self.owner:
			result = True
		elif self._ctx.checkreadadmin():
			result = True
		return result


	def findparams(self):
		"""This will update the list of params by parsing the views"""

		t, d, r = parseparmvalues(self.mainview)

		for i in self.views.values():
			t2, d2, r2 = parseparmvalues(i)
			t |= t2
			r |= r2
			for j in t2:
				# ian: fix for: empty default value in a view unsets default value specified in mainview
				if not d.has_key(j):
					d[j] = d2.get(j)
				


		self.params = d
		self.paramsK = t
		self.paramsR = r






@RecordDef.register_validator
@emen2.db.validators.Validator.make_validator
class RecordDefValidator(emen2.db.validators.DefinitionValidator):

	def validate_name(self):
		if not self._obj.name:
			raise ValueError, "No RecordDef name given"

		self._obj.name = unicode(self._obj.name).lower()

		test = self._obj.name.replace("_","")
		if not test.isalnum() or not self._obj.name[0].isalpha():
			raise ValueError, "RecordDef name can only include a-z, A-Z, 0-9, underscore, and must start with a letter"


	def validate_recorddef(self):
		"""Validate RecordDef"""

		try:
			self._obj.views = dict(map(lambda x:(unicode(x[0]), unicode(x[1])), self._obj.views.items()))
		except:
			raise ValueError,"views must be dict"

		try:
			self._obj.typicalchld = map(unicode, self._obj.typicalchld)
		except:
			raise ValueError,"Invalid value for typicalchld; list of recorddefs required."

		try:
			if not self._obj.mainview: raise Exception
			self._obj.mainview = unicode(self._obj.mainview)
		except:
			raise
			raise ValueError,"mainview required"


		if not dict(self._obj.views).has_key("recname"):
			g.log.msg("LOG_WARNING", "recname view strongly suggested")


		if not self._obj.owner:
			g.log.msg("LOG_WARNING", "No owner")
			self._obj.owner = u"root"
			#raise ValueError, "No owner"
		self._obj.owner = unicode(self._obj.owner)

		if not self._obj.creator:
			g.log.msg("LOG_WARNING", "No creator")
			self._obj.creator = u"root"
			#raise ValueError, "No creator"
		self._obj.creator = unicode(self._obj.creator)


		if not self._obj.creationtime:
			self._obj.creationtime = emen2.db.database.gettime()
		self._obj.creationtime = unicode(self._obj.creationtime)

		try:
			self._obj.private=int(bool(self._obj.private))
		except:
			raise ValueError,"Invalid value for private; must be 0 or 1"



# ian: todo: make this a classmethod of RecordDef ?

def parseparmvalues(text):
	regex = re.compile(emen2.db.database.VIEW_REGEX)

	params = set()
	required = set()
	defaults = {}
	
	for match in regex.finditer(text):
		n = match.group('name')
		t = match.group('type')

		if not n:
			continue
		if t == '$' or t == '*':
			params.add(match.group('name'))
			if match.group('def'):
				defaults[n] = match.group('def')
		if t == '*':
			required.add(n)
			
	return params, defaults, required
			
			


# def parseparmvalues_old(text,noempty=0):
# 	"""This will extract parameter names $param or $param=value """
# 
# 	srch = re.finditer('\$\$([a-zA-Z0-9_\-]*)(?:(?:=)(?:(?:"([^"]*)")|([^ <>"]*)))?',text)
# 	params, vals = ret = [[],{}]
# 
# 	for name, a, b in (x.groups() for x in srch):
# 		if name is '':
# 			continue
# 		else:
# 			params.append(name)
# 			if a is None:
# 				val=b
# 			else:
# 				val=a
# 			if val != None:
# 				vals[name] = val
# 
# 	return ret









__version__ = "$Revision$".split(":")[1][:-1].strip()
