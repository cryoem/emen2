# $Id$
from emen2.util import db_manipulation
from itertools import chain
import operator

import emen2.db.config
g = emen2.db.config.g()


class DBQuery(object):
	def __init__(self, db):
		self.db = db
		self._data = None
		self._ops = []
		self._dirty = False

	def __lshift__(self, other):
		if hasattr(other, '__iter__'):
			self._ops.append(iter(other))
		else:
			self._ops.append(other.act)
		self._dirty = True
		return self

	def __repr__(self):
		return "DBQuery(%s, cache_dirty=%s)" % (self._data, self._dirty)

	def get_result(self):
		if self._dirty or self._data == None:
			data = self._data or set()
			for op in self._ops:
				if hasattr(op, '__iter__'):
					data = chain(data, op)
				else:
					data = op(data, self.db)
			self._ops = []
			self._data = data
			self._dirty = False
		return list(self._data)
	result = property(get_result)

	def reset(self):
		self._ops = []
		self._data = None
		self._dirty = False

class BoolOp(object):
	def __init__(self, op, *args):
		self._ops = args
		self._op = op
	def act(self, data, db):
		results = set()
		q = DBQuery(db)
		for item in self._ops:
			for pred in item:
				q << pred
			results = self._op(results, set(q.result))
			q.reset()
		for item in results:
			yield item


class Union(BoolOp):
	def __init__(self, *args):
		BoolOp.__init__(self, operator.or_, *args)

class Intersection(BoolOp):
	def __init__(self, *args):
		BoolOp.__init__(self, operator.and_, *args)


class GetRecord(object):
	def act(self, data, db):
		for recid in data:
			yield db.getrecord(recid)

class GetRecordDef(object):
	def act(self, data, db):
		for name in data:
			yield db.getrecorddef(name)

class GetChildren(object):
	def act(self, data, db):
		for recid in data:
			for child in db.getchildren(recid):
				yield child

class GetParents(object):
	def act(self, data, db):
		for recid in data:
			for child in db.getparents(recid):
				yield child

class ParamValue(object):
	def __init__(self, param_name=None):
		self.param_name = param_name
	def act(self, data, db):
		for val in data:
			res = db.getparamvalue(self.param_name, val)
			if bool(res) == True:
				yield res
			else:
				yield None

class FilterByRecordDef(object):
	def __init__(self, recorddefs):
		if hasattr(recorddefs, '__iter__'):
			self.recorddefs = recorddefs
		else:
			self.recorddefs = [recorddefs]
	def act(self, data, db):
		result = set([])
		for name in self.recorddefs:
			result.update(db.getindexbyrectype(name))
		if data:
			result = ( set(result) & set(data) ) or result

		for item in result:
			yield item

class FilterByContext(object):
	def act(self, data, db):
		if data:
			result = ( set(data) & set(db.getindexbycontext(ctxid=ctxid, host=host)) ) or data
		else:
			result = db.getindexbycontext(ctxid=ctxid, host=host)

		for item in result:
			yield item

class FilterByValue(object):
	def __init__(self, param_name, value):
		self.param_name = param_name
		self.value = value
	def act(self, data, db):
		if data:
			result = ( set(data) & set(db.getindexbyvalue(self.param_name, self.value)) ) or data
		else:
			result = db.getindexbyvalue(self.param_name, self.value)

		for item in result:
			yield item

class FilterByParamDef(object):
	def __init__(self, param_name):
		self.param_name = param_name
	def act(self, data, db):
		data = db.getrecord(data)
		for x  in data:
			if x[self.param_name] != None:
				yield x.recid

class FilterByParentType(object):
	def __init__(self, recorddef):
		self.recorddef = recorddef
	def act(self, data, db):
		queryset = [ (x, db.getparents(x)) for x in data ]
		for rec, parents in queryset:
			parents = db.groupbyrectype(parents)
			if parents.get(self.recorddef, False) != False:
				yield rec

class GetPath(object):
	def act(self, data, db):
		result = db_manipulation.DBTree(db).get_path_id(list(data))
		if not hasattr(result, '__iter__'):
			result = [result]
		for x in result:
			yield x

class GetRoot(object):
	def act(self, data, db):
		yield db_manipulation.DBTree(db).root

class Filter(object):
	def __init__(self, func):
		self.func = func
	def act(self, data, db):
		for x in data:
			if self.func(x):
				yield x

class Map(object):
	def __init__(self, func):
		self.func = func
	def act(self, data, db):
		for x in data:
			yield self.func(x)

class Select(object):
	def __init__(self, **kwargs):
		self._args = kwargs
	def act(self, data, db):
		data = set(data or [])
		for paramdef, value in self._args.items():
			data = FilterByValue(paramdef, value).act(data, db)
		for x in data:
			yield x

class EditRecord(object):
	def __init__(self, changes):
		'''
		Edit a records contents.

		@param changes: A dictionary of paramdef:value pairs
		'''
		self._changes = changes
	def act(self, data, db):
		'''data should be a sequence of records'''
		for rec in data:
			rec.update(self._changes)
			yield rec

class Commit(object):
	def act(self, data, db):
		for rec in data:
			db.puterecord(rec)
			yield rec

class Unlink(object):
	def __init__(self, parent):
		self._pid = parent
	def act(self, data, db):
		for rec in data:
			if hasattr(rec, 'recid'):
				id = rec.recid
			else:
				id = int(rec)
			db.pcunlink(self._pid, id)
			yield rec

class TryGet(object):
	def act(self, data, db):
		for rec in data:
			yield db.trygetrecord(rec)
__version__ = "$Revision$".split(":")[1][:-1].strip()
