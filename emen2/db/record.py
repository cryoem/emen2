# $Id$
import time
import UserDict
import collections
import operator
import weakref
import copy
import re

import emen2.db.btrees
import emen2.db.datatypes
import emen2.db.exceptions
import emen2.db.dataobject
import emen2.util.listops as listops

import emen2.db.config
g = emen2.db.config.g()

from . import validators

#	This class encapsulates a single database record. In a sense this is an instance
#	of a particular RecordDef, however, note that it is not required to have a value for
#	every field described in the RecordDef, though this will usually be the case.
#
#	To modify the params in a record use the normal obj[key]= or update() approaches.
#	Changes are not stored in the database until commit() is called. To examine params,
#	use obj[key]. There are a few special keys, handled differently:
#	creator,creationtime,permissions,comments,history,parents,children,groups
#
#	Record instances must ONLY be created by the Database class through retrieval or
#	creation operations. self._ctx will store information about security and
#	storage for the record.
#
#	Mechanisms for changing existing params are a bit complicated. In a sense, as in a
#	physical lab notebook, an original value can never be changed, only superceded.
#	All records have a 'magic' field called 'comments', which is an extensible array
#	of text blocks with immutable entries. 'comments' entries can contain new field
#	definitions, which will supercede the original definition as well as any previous
#	comments. Changing a field will result in a new comment being automatically generated
#	describing and logging the value change.
#
#	From a database standpoint, this is rather odd behavior. Such tasks would generally be
#	handled with an audit log of some sort. However, in this case, as an electronic
#	representation of a Scientific lab notebook, it is absolutely necessary
#	that all historical values are permanently preserved for any field, and there is no
#	particular reason to store this information in a separate file. Generally speaking,
#	such changes should be infrequent.
#
#	Naturally, as with anything in Python, anyone with code-level access to the database
#	can override this behavior by changing 'params' directly rather than using
#	the supplied access methods. There may be appropriate uses for this when constructing
#	a new Record before committing changes back to the database.


class Record(emen2.db.dataobject.PermissionsDBObject):

	# recid goes by 'name' now for common behavior
	recid = property(lambda s:s.name)

	# history, rectype can't be set by user. recid is for backwards compatbility, but can't be set.
	# rectype is required RecordDef
	# comments goes through addcomment
	# remaining items, if there is a valid ParamDef for that key, go through _setoob.
	param_user = emen2.db.dataobject.PermissionsDBObject.param_user | set(['comments'])
	param_all = emen2.db.dataobject.PermissionsDBObject.param_all | param_user | set(['history', 'rectype', 'name'])
	param_required = set(['rectype'])


	def init(self, d):			
		super(Record, self).init(d)
		
		# Required initialization params
		self.__dict__['rectype'] = d.pop('rectype')

		# Other built-ins. These might get moved to the base class.
		self.__dict__['comments'] = []
		self.__dict__['history'] = []		
		self.__dict__['_params'] = {}

		# Check if we can access RecordDef
		# rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
		# t = dict([ (x,y) for x,y in rd.params.items() if y != None])



	#################################
	# repr methods
	#################################

	def __unicode__(self):
		ret = ["%s (%s)\n"%(unicode(self.name), self.rectype)]
		for i,j in self.items():
			ret.append(u"%12s:	%s\n"%(unicode(i),unicode(j)))
		return u"".join(ret)


	def __str__(self):
		return self.__unicode__().encode('utf-8')


	def __repr__(self):
		return "<Record id: %s rectype: %s at %x>" % (self.name, self.rectype, id(self))


	def json_equivalent(self):
		"""Returns a dictionary of current values"""
		ret = {}
		ret.update(self._params)
		for i in self.param_all:
			ret[i] = getattr(self, i, None)
		return ret



	#################################
	# Setters
	#################################

	def _set_comments(self, key, value, warning=False, vtm=None, t=None):
		return self.addcomment(value, t=t)


	# in Record, params not in self.param_user are put in self._params{}.
	def _setoob(self, key, value, warning=False, vtm=None, t=None):		
		# This has already been validated through __setitem__
		if self._params.get(key) == value:
			# print ":: No change: ", key, value
			return set()
		self.vw(key) # Check permissions
		self._addhistory(key, t=t)
		# print ":: Setting param key/value", key, value
		self._params[key] = value
		return set([key])


	#################################
	# mapping methods;
	#		UserDict.DictMixin provides the remainder
	#################################

	def __getitem__(self, key, default=None):
		"""Default behavior is similar to .get: return None as default"""
		if key in self.param_all:
			return getattr(self, key, default)
		else:		
			return self._params.get(key, default)


	# def __delitem__(self,key):
	# 	"""Only params can be deleted, not attributes"""
	# 	try:
	# 		del self._params[key]
	# 	except:
	# 		raise KeyError,"Cannot delete key %s"%key


	def keys(self):
		"""All retrievable keys for this record"""
		return self._params.keys() + list(self.param_all)


	def getparamkeys(self):
		"""Returns parameter keys without special values like owner, creator, etc."""
		return self._params.keys()



	##########################
	# Comments and history
	##########################

	def _addhistory(self, param, t=None):
		# Changes aren't logged on uncommitted records
		if self.name < 0:
			return

		if not param:
			raise Exception, "Unable to add item to history log"

		vtm, t = self._vtmtime(t=t)			
		self.history.append((unicode(self._ctx.username), unicode(t), unicode(param), self._params.get(param)))


	def addcomment(self, value, vtm=False, t=None):
		self.vw('comments', self.commentable(), 'Insufficient permissions to add comment')

		vtm, t = self._vtmtime(vtm, t)
		cp = set()
		if value == None:
			return set()
		
		newcomments = []	
		if hasattr(value, "__iter__"):
			check = [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in value]
			existing = [(unicode(i[0]), unicode(i[1]), unicode(i[2])) for i in self.comments]
			for c in check:
				if c not in existing:
					newcomments.append(c[2])
		else:
			newcomments.append(unicode(value))

		# newcomments2 = []
		# updvalues = {}		
		for value in newcomments:
			d = {}
			if not value.startswith("LOG"): # legacy fix..
				d = emen2.db.recorddef.parseparmvalues(value)[1]

			if d.has_key("comments"):
				# Always abort
				self.error("Cannot set comments inside a comment", warning=False)
						
			# Now update the values of any embedded params
			for i,j in d.items():
				cp |= self.__setitem__(i, j, vtm=vtm, t=t)

			# Store the comment string itself
			self.comments.append((unicode(self._ctx.username), unicode(t), unicode(value)))
			cp.add('comments')
		
		return cp


	def revision(self, revision=None):
		"""This will return information about the record's revision history"""

		history = copy.copy(self.history)
		comments = copy.copy(self.comments)
		comments.append((self.get('creator'), self.get('creationtime'), 'Created'))
		paramcopy = {}

		bydate = collections.defaultdict(list)
		
		for i in filter(lambda x:x[1]>=revision, history):
			bydate[i[1]].append([i[0], i[2], i[3]])

		for i in filter(lambda x:x[1]>=revision, comments):
			bydate[i[1]].append([i[0], None, i[2]])
			
		revs = sorted(bydate.keys(), reverse=True)

		for rev in revs:				
			for item in bydate.get(rev, []):
				# user, param, oldval
				if item[1] == None:
					continue
				if item[1] in paramcopy.keys():
					newval = paramcopy.get(item[1])
				else:
					newval = self.get(item[1])
	
				paramcopy[item[1]] = copy.copy(item[2])				
				# item[2] = newval

		return bydate, paramcopy
		


	#################################
	# validation methods
	#################################

	
	def validate_name(self, name):
		"""Validate the name of this object"""		
		if name in ['None', None]:
			return
		try:
			name = int(name)			
		except:
			self.error("Name must be an integer")
		return name



	def validate(self, warning=False, vtm=None, t=None):
		# Cut out any None's
		pitems = self._params.items()
		for k,v in pitems:
			if not v and v != 0 and v != False:
				del self._params[k]
		
		# Check the rectype and any required parameters
		vtm, t = self._vtmtime(vtm=vtm, t=t)
		cachekey = vtm.get_cache_key('recorddef', self.rectype)
		hit, rd = vtm.check_cache(cachekey)
		if not hit:
			rd = self._ctx.db.getrecorddef(self.rectype, filt=False)
			vtm.store(cachekey, rd)
	
		for param in rd.paramsR:
			if self.get(param) == None:
				self.error("%s is a required parameter"%(param), warning=warning)
	
		self.__dict__['rectype'] = unicode(rd.name)
		
	
	#################################
	# pickle methods
	#################################

	def __setstate__(self, d):
		# Backwards compatibility..
		if not d.has_key('_params'):			
			d["modifyuser"] = d["_Record__params"].pop("modifyuser", None)
			d["modifytime"] = d["_Record__params"].pop("modifytime", None)
			d["uri"] = d["_Record__params"].pop("uri", None)

			d["_params"] = d["_Record__params"]
			d["history"] = d["_Record__history"]
			d["comments"] = d["_Record__comments"]
			d["permissions"] = d["_Record__permissions"]
			d["groups"] = d["_Record__groups"]

			d["creator"] = d["_Record__creator"]
			d["creationtime"] = d["_Record__creationtime"]
			d["parents"] = set()
			d["children"] = set()

			for i in ["_Record__ptest", 
				"_Record__ptest", 
				"_Record__params", 
				"_Record__history", 
				"_Record__comments", 
				"_Record__permissions", 
				"_Record__groups", 
				"_Record__creator", 
				"_Record__creationtime"]:
				try:
					del d[i]
				except:
					pass		
		
		# recid/username -> 'name'.
		if d.has_key('name'):
			d['name'] = d.pop('name')

		return self.__dict__.update(d)





class RecordBTree(emen2.db.btrees.RelateBTree):

	def init(self):
		self.setkeytype('d', False)
		self.setdatatype('p', emen2.db.record.Record)
		self.sequence = True
		super(RecordBTree, self).init()


	# ian: todo: add a Context Manager for handling Transactions in EMEN2DBEnv.. Merge with DBProxy..

	def openindex(self, param, create=False):
		# print "Attempting to open index %s"%param
		# RecordBTree maintains an index-of-indexes for faster querying
		if param == 'indexkeys':
			return emen2.db.btrees.IndexBTree(filename="index/indexkeys", dbenv=self.dbenv)

		create = True # disable this check, and always create index.

		# Check the paramdef to see if it's indexed
		pd = self.bdbs.paramdef.get(param)
		if not pd or pd.vartype not in self.bdbs.indexablevartypes or not pd.indexed:
			return None

		vtm = emen2.db.datatypes.VartypeManager()
		tp = vtm.getvartype(pd.vartype).keytype

		filename = "index/params/%s"%(pd.name)
		if not create and not os.access(filename, os.F_OK):
			raise KeyError, "No index for %s"%pd.name

		return emen2.db.btrees.IndexBTree(keytype=tp, datatype='d', filename=filename, dbenv=self.dbenv)



	# Update the database sequence.. Probably move this to the parent class.
	def update_sequence(self, items, txn=None):
		# Which recs are new?
		newrecs = [i for i in items if i.name < 0]
		namemap = {}

		# Reassign new record IDs and update record counter
		if newrecs:
			basename = self.get_sequence(delta=len(newrecs), txn=txn)
			g.log.msg("LOG_DEBUG","Setting counter: %s -> %s"%(basename, basename + len(newrecs)))

		# We have to manually update the rec.__dict__['name'] because this is normally considered a reserved attribute.
		for offset, newrec in enumerate(newrecs):
			oldname = newrec.name
			newrec.__dict__['name'] = offset + basename
			namemap[oldname] = newrec.name		

		return namemap
	
	
	
	def delete(self, names, ctx=None, txn=None):
		recs = self.cgets(names, ctx=ctx, txn=txn)
		crecs = []
		for rec in recs:
			rec.setpermissions([[],[],[],[]])
			if rec.parents and rec.children:
				rec["comments"] = "Record hidden by unlinking from parents %s and children %s"%(", ".join([unicode(x) for x in rec.parents]), ", ".join([unicode(x) for x in rec.children]))
			elif rec.parents:
				rec["comments"] = "Record hidden by unlinking from parents %s"%", ".join([unicode(x) for x in rec.parents])
			elif rec.children:
				rec["comments"] = "Record hidden by unlinking from children %s"%", ".join([unicode(x) for x in rec.children])
			else:
				rec["comments"] = "Record hidden"
			
			rec['deleted'] = True
			rec['children'] = set()
			rec['parents'] = set()
			crecs.append(rec)
		
		return self.cputs(crecs, ctx=ctx, txn=txn)	


	# This builds UP instead of prunes DOWN; filter does the opposite..
	def names(self, names=None, ctx=None, txn=None, **kwargs):
		if names is not None:
			return self._filter(names, rectype=kwargs.get('rectype'), ctx=ctx, txn=txn)

		if ctx.checkreadadmin():
			return set(xrange(self.get_max(txn=txn)))

		ind = self.getindex("permissions")
		indg = self.getindex("groups")
		ret = ind.get(ctx.username, set(), txn=txn)
		for group in sorted(ctx.groups, reverse=True):
			ret |= indg.get(group, set(), txn=txn)

		return ret
		
		
	def _filter(self, names, rectype=None, ctx=None, txn=None):
		names = self.expand(names, ctx=ctx, txn=txn)

		if rectype:
			ind = self.getindex('rectype')
			# rdnames = self.bdbs.recorddef.expand(kwargs.get('rectype'), ctx=ctx, txn=txn)
			rdnames = self.bdbs.recorddef.cgets(listops.check_iterable(rectype), ctx=ctx, txn=txn)
			rd = set()
			for i in rdnames:
				rd |= ind.get(i.name, txn=txn)
			names &= rd

		if ctx.checkreadadmin():
			return names

		# ian: indexes are now faster, generally...
		if len(names) < 1000:
			crecs = self.cgets(names, ctx=ctx, txn=txn)
			return set([i.name for i in crecs])

		# Make a copy
		find = copy.copy(names)

		# Use the permissions/groups index
		ind = self.getindex('permissions')
		indg = self.getindex('groups')

		find -= ind.get(ctx.username, set(), txn=txn)
		for group in sorted(ctx.groups):
			if find:
				find -= indg.get(group, set(), txn=txn)

		return names - find


		
	

__version__ = "$Revision$".split(":")[1][:-1].strip()
