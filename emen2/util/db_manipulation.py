from functools import partial
from itertools import chain
import emen2.Database
from emen2.subsystems.routing import URLRegistry

from emen2.emen2config import *

class IntegrityError(ValueError): pass
class DBWrap(object):
	def __init__(self,db,ctxid,host=None):
		self.db=db
		self.ctxid=ctxid
		self.host=host
	def __getattribute__(self, name):
		_dict_ = object.__getattribute__(self, '__dict__')
		if _dict_.has_key(name): return _dict_[name]
		attr = object.__getattribute__(self, 'db')
		attr = getattr(attr, name)
		return partial(attr, ctxid=self.ctxid, host=self.host)

class DBTree(object):
	root = property(lambda self: self.__root)
	ctxid = property(lambda self: self.__ctxid)

	def __init__(self, db, ctxid, host=None, root=None):
		self.caching = False
		self.__db = db
		self.__ctxid = ctxid
		self.__host = host
		self.__root = root or min(db.getindexbyrecorddef('folder', ctxid=ctxid, host=host))
		self.db = DBWrap(self.__db, self.__ctxid, self.__host)
		self.getrecord = self.db.getrecord

	def __getpath(self, path=None):
		if path != None: path = self.get_path_id(path)
		else: path = [self.root]
		return path
			
	def __dostuff(self, name, subfolders):
		for (rectype, rec) in subfolders:
			if (str(rec) == name) or (self.getrecord(rec)['indexby'] == name):
				yield (rectype, rec)
		
	def __unfold_dict(self, dict):
		result = []
		[ [ result.append((key, item)) for item in items ] for key, items in dict.iteritems()]
		return result
				
	
	def __select(self, data, **kwargs):
		unionset = set()
		for param, value in kwargs.iteritems():
			unionset |= self.__db.getindexbyvalue(param, value, ctxid=self.__ctxid, host=self.__host)
		data &= unionset
		# no return since sets are weakly referenced
		
	def __to_path(self, recid, path=None):
		path = path or []
		parents = self.__db.getparents(recid, ctxid=self.__ctxid, host=self.__host)
		if self.root not in parents:
			path.extend(self.__to_path(parents.pop(), path))
		path.append(str(recid))
		return path
	
	def getindex(self, recid=None, rec=None):
		rec = self.getrecord(recid) if rec is None else rec
		index = rec.get('indexby', str(rec.recid))
		return index
	
	def get_title(self, recid, ident=''):
		return self.render_view(recid, 'recname').rpartition(':')[0::2]

	def chroot(self, recid):
		self.__root = recid
	
	def get_path_id(self, path, cur_dir=None):
		'''raises StopIteration if path does not exist'''
		cur_dir = cur_dir or self.root
		if path != []: # recurse if we are not at the end of the path list
			children = ( elem[1] for elem in self.get_child_id(path[0], cur_dir=cur_dir) )
			result = set()
			for recset in ( self.get_path_id(path[1:], recid) for recid in children ): # << recurse here
				result.update(recset)
		else: # if we are at the end of the path list, we must be where we want to be
			result = set([cur_dir])
		return result
	
	def get_child_id(self, name, cur_dir):
		'''returns first child with a given folder_name'''
#		ckey = self.get_cache_key('get_child_id', name, cur_dir)
#		hit, result = self.check_cache(ckey) or (False, None)
#		if hit is False:
		children = self.__db.getchildren(cur_dir, keytype='record', ctxid=self.__ctxid, host=self.__host)
		group = self.__db.groupbyrecorddef(children, ctxid=self.__ctxid, host=self.__host)
		subfolders = self.__unfold_dict(group)
		if name == '*': result = list(subfolders)
		else: result = list(self.__dostuff(name, subfolders))
#		if bool(result): self.store(ckey, result)
		return result
	
	def get_parents(self, path=None, **kwargs):
		path = self.__getpath(path)
		result = set()
		for rec in path:
			result.update(self.__db.getparents(rec, ctxid=self.__ctxid, host=self.__host))
		self.__select(result, **kwargs)
		return result
	
	def get_children(self, path=None, **kwargs):
		path = self.__getpath(path)
		result = set()
		for rec in path:
			new = [ elem[1] for elem in self.get_child_id('*', rec) ]
			result.update(new)
		if kwargs != {}: self.__select(result, **kwargs)
		return result
	
	def get_siblings(self, path=None, **kwargs):
		parents = self.get_parents(path)
		result = set()
		for parent in parents:
			result.update(self.__db.getchildren(parent, ctxid=self.__ctxid, host=self.__host))
		self.__select(result, **kwargs)
		return result
	
	def get_sibling(self, name, **kwargs):
		siblings = self.get_siblings()
		if name == '*':
			result = siblings
		else:
			siblings = self.__unfold_dict(self.__db.groupbyrecorddef(siblings, ctxid=self.__ctxid, host=self.__host))
			result = [elem[1] for elem in self.__dostuff(name, siblings)]
		self.__select(result, **kwargs)
		return result
	
	def to_path(self, recid):
		return str.join('/', self.__to_path(recid))
	
	def reverse(self, name, *args, **kwargs):
		return '/db'+(URLRegistry.reverselookup(name, *args, **kwargs) or '')
	
	def render_view(self, recid, view):
		return self.db.renderview(recid, viewtype=view)
	
	def get_user(self):
		un = self.__db.checkcontext(self.__ctxid, host=self.__host)[0]
		if un is not None:
			return self.__db.getuser(un, self.__ctxid)
		else:
			return None


def get_create(recdef, param, value, db, ctxid, host=None):
	record =  db.getindexbyvalue(param, value, ctxid, host)
	record = db.groupbyrecorddef(record, ctxid, host).get(recdef, set())
	if len(record) == 1:
		record = db.getrecord(record.pop(), ctxid)
	elif len(record) > 1:
		raise IntegrityError('Value Not Unique')
	else:
		record = db.newrecord(recdef, ctxid)
		record[param] = value
	return record