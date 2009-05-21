from emen2.emen2config import *
import time
from emen2.subsystems.routing import URLRegistry
from functools import partial
from itertools import chain
import emen2.util.datastructures
import emen2.Database


class IntegrityError(ValueError): pass

class DBTree(object):
	'''emulates a tree structure on to of the Database'''
	root = property(lambda self: self.__root)
	ctxid = property(lambda self: self.__ctxid)

	def __init__(self, db, ctxid, host=None, root=None):
		self.__db = db
		self.__ctxid = ctxid
		self.__host = host
		self.__root = root or min(db.getindexbyrecorddef('folder') or [0])
		self.db = self.__db

	def __getpath(self, path=None):
		if path != None: path = self.get_path_id(path)
		else: path = [self.root]
		return path
			
		
	def __unfold_dict(self, dict):
		result = []
		[ [ result.append((key, item)) for item in items ] for key, items in dict.iteritems()]
		return result
				
	
	def __select(self, data, **kwargs):
		for param, value in kwargs.iteritems():
			data &= self.__db.getindexbyvalue(param, value)#, ctxid=self.__ctxid, host=self.__host)
		# no return since sets are weakly referenced
		
	def __to_path(self, recid, path=None):
		path = path or []
		parents = self.__db.getparents(recid)#, ctxid=self.__ctxid, host=self.__host)
		if self.root not in parents:
			path.extend(self.__to_path(parents.pop(), path))
		path.append(str(recid))
		return path
	
	def getindex(self, recid=None, rec=None):
		rec = self.__db.getrecord(recid) if rec is None else rec
		index = rec.get('recname', str(recid))
		return index
	
	def get_title(self, recid):
		return self.render_view(recid, 'recname').rpartition(':')[0::2]

	def chroot(self, recid):
		self.__root = recid
		
	
	def get_path_id(self, path, cur_dir=None):
		'''
		takes a list iterates through it and follows parent-child relationships in the db
		selecting children with a recname parameter equal to the current list item
		
		empty list signifies current directory
		
		raises StopIteration if path does not exist
		'''
		cur_dir = cur_dir or self.root
		if path != []: # recurse if we are not at the end of the path list
			children = ( elem for elem in self.get_child_id(path[0], cur_dir=cur_dir) )
			result = set()
			for recset in ( self.get_path_id(path[1:], recid) for recid in children ): # << recurse here
				result.update(recset)
		else: # if we are at the end of the path list, we must be where we want to be
			result = set([cur_dir])
		return result
	
	
	def get_child_id(self, name, cur_dir):
		'''returns children of a record with a given recname'''
		children = self.__db.getchildren(cur_dir, filt=True)
		if name == '*': 
			[(yield child) for child in children]
		else:
			for rec in self.__dostuff(name, children):
				yield (rec)
	
	def get_parents(self, path=None, **kwargs):
		path = self.__getpath(path)
		result = set()
		for rec in path:
			result.update(self.__db.getparents(rec))#, ctxid=self.__ctxid, host=self.__host))
		self.__select(result, **kwargs)
		return result

	def get_children(self, path=None, **kwargs):
		path = self.__getpath(path)
		result = set()
		for rec in path:
			new = [ elem for elem in self.get_child_id('*', rec) ]
			if len(result) == 0:
				result.update(new)
			else:
				result.intersection_update(new)
		if kwargs != {}: self.__select(result, **kwargs)
		return result
	
	def get_siblings(self, path=None, **kwargs):
		parents = self.get_parents(path)
		result = set()
		for parent in parents:
			result.update(self.__db.getchildren(parent))#, ctxid=self.__ctxid, host=self.__host))
		self.__select(result, **kwargs)
		return result
	
	def __dostuff(self, name, records):
		for rec in records:
			g.debug(rec)
			if (str(rec) == name) or (self.__db.getrecord(rec)['recname'] == name):
				yield (rec)
	
	def get_sibling(self, name, **kwargs):
		siblings = self.get_siblings()
		if name == '*':
			result = siblings
		else:
			result = [elem[1] for elem in self.__dostuff(name, siblings)]
		self.__select(result, **kwargs)
		return result
	
	def to_path(self, recid):
		return str.join('/', self.__to_path(recid))
	
	def reverse(self, _name, *args, **kwargs):
		return g.EMEN2WEBROOT+'/db'+(URLRegistry.reverselookup(_name, *args, **kwargs) or '')+'/'
	
	def render_template_view(self, name, *args, **kwargs):
		return URLRegistry.call_view(name, db=self.__db, *args, **kwargs )#ctxid=self.__ctxid, host=self.__host, 
	
	def render_view(self, recid, view):
		return self.db.renderview(recid, viewtype=view)
	
	def get_user(self):
		un = self.__db.checkcontext()[0]
		if un is not None:
			return self.__db.getuser(un)
		else:
			return None
	
	def get_menu(self, depth=1):
		recs = self.db.getchildren(self.root, recurse=depth, tree=True, filt=True)
		folders = self.db.getindexbyrecorddef('folder')
		recs1 = {}
		keys = filter(lambda x: x in folders, recs)
		for key in keys:
			value = recs[key] & folders
			recs1[key] = value
		#t3 = time.time();g.debug.msg('LOG_INFO', 'start::', t3)
		recs = emen2.util.datastructures.Tree(recs1, self.root,
									app=lambda x: (x, self.getindex(x)))
		#t4 = time.time();g.debug.msg('LOG_INFO', 'elapsed::', t4-t3)
		return recs
		
def get_create(recdef, param, value, db, ctxid, host=None):
	record = db.getindexbyvalue(param, value, ctxid, host)
	record = db.groupbyrecorddef(record, ctxid, host).get(recdef, set())
	if len(record) == 1:
		record = db.getrecord(record.pop(), ctxid)
	elif len(record) > 1:
		raise IntegrityError('Value Not Unique')
	else:
		record = db.newrecord(recdef, ctxid)
		record[param] = value
	return record
