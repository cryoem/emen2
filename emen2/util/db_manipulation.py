# $Id$
import urllib2
import emen2.util.datastructures
#import emen2.db

from emen2.web.routing import URLRegistry

import emen2.db.config
g = emen2.db.config.g()

#class Context(object):
#	'''Partial context for views that don't need db access'''
#	def reverse(self, _name, *args, **kwargs):
#		_full = kwargs.get('_full', False)
#		prefix = '%s' % g.EMEN2WEBROOT
#		if not prefix.endswith('/'): prefix = '%s/' % prefix
#
#		result = '%s%s%s' % (prefix, 'db', (
#			URLRegistry.reverselookup(_name, *args, **kwargs).replace('//','/') or ''))
#		containsqs = '?' in result
#		if not result.endswith('/') and not containsqs: result = '%s/' % result
#		elif containsqs and '/?' not in result: result = result.replace('?', '/?', 1)
#		return result


#class DBTree(Context):
#	'''emulates a tree structure on top of the Database'''
#	root = property(lambda self: self._root)
#	ctxid = property(lambda self: self._ctxid)
#
#	def __init__(self, db=None, root=None):
#		if db is not None:
#			self.db = db
#			self._db = db
#
#			# ian: don't disable this
#			if 'folder' in db.getrecorddefnames() and root is None:
#				self._root = min(db.getindexbyrecorddef('folder') or [0])
#			else:
#				self._root = root
#
#			self._initmethods()
#
#		else: g.log.msg('LOG_WARNING', 'db is None...')
#
#	def _initmethods(self):
#		self.get_path_id = self._db._wrapmethod(self._get_path_id)
#
#	def _get_path_id(self, path, cur_dir=None):
#		'''
#		takes a list iterates through it and follows parent-child relationships in the db
#		selecting children with a recname parameter equal to the current list item
#
#		empty list signifies current directory
#
#		raises StopIteration if path does not exist
#		'''
#		cur_dir = cur_dir or self.root
#		if path == []: # empty path == found result
#			result = set([cur_dir])
#		else: # recurse if we are not at the end of the path list
#			children = self.get_child_id(path[0], cur_dir=cur_dir)
#			result = reduce(set.union, self._gpi_helper_1(path[1:], children), set())
#		return result
#
#
#	def _gpi_helper_1(self, path, children):
#		for name in children:
#			yield self._get_path_id(path, name)
#
#
#	def get_child_id(self, name, cur_dir):
#		'''returns children of a record with a given recname'''
#		children = self._db.getchildren(cur_dir)
#		if name == '*':
#			[(yield child) for child in children]
#		else:
#			for rec in self._dostuff(name, children):
#				yield rec
#
#
#	def _dostuff(self, name, records):
#		recnamep = self._db.getindexbyvalue('name_folder', name)
#		for rec in records:
#			if (str(rec) == name) or (rec in recnamep):
#				yield (rec)
#			elif self.render_view(rec, 'recname') == name:
#				yield (rec)
#
#
#	def _select(self, data, **kwargs):
#		for param, value in kwargs.iteritems():
#			data &= self._db.getindexbyvalue(param, value)
#		# no return since sets are weakly referenced
#
#
#	def _getpath(self, path=None):
#		if path != None: path = self.get_path_id(path)
#		else: path = [self.root]
#		return path
#
#	def _to_path(self, name, path=None):
#		path = path or []
#		parents = self._db.getparents(name)
#		if self.root not in parents:
#			path.extend(self._to_path(parents.pop(), path))
#		path.append(self.getindex(name))
#		return path
#
#	def getindex(self, name=None, rec=None):
#		rec = self._db.getrecord(name, filt=False) if rec is None else rec
#		index = rec.get('name_folder', str(name))
#		if index == None:
#			index = self.render_view(rec.name, 'recname')
#		return index
#
#	def get_title(self, name):
#		return self.render_view(name, 'recname').rpartition(':')[0::2]
#
#	def chroot(self, name):
#		self._root = name
#
#
#
#
#	def get_parents(self, path=None, **kwargs):
#		path = self._getpath(path)
#		result = set()
#		for rec in path:
#			result.update(self._db.getparents(rec))
#		self._select(result, **kwargs)
#		return result
#
#	def get_children(self, path=None, **kwargs):
#		result = set()
#		if path is None:
#			result = self.db.getchildren(self.root)
#		else:
#			path = self._getpath(path)
#			for rec in path:
#				new = [ elem for elem in self.get_child_id('*', rec) ]
#				if len(result) == 0:
#					result.update(new)
#				else:
#					result.intersection_update(new)
#		if kwargs != {}: self._select(result, **kwargs)
#		return result
#
#	def get_siblings(self, path=None, **kwargs):
#		parents = self.get_parents(path)
#		result = set()
#		for parent in parents:
#			result.update(self._db.getchildren(parent))
#		self._select(result, **kwargs)
#		return result
#
#	def get_sibling(self, name, **kwargs):
#		siblings = self.get_siblings()
#		if name == '*':
#			result = siblings
#		else:
#			result = [elem[1] for elem in self._dostuff(name, siblings)]
#		self._select(result, **kwargs)
#		return result
#
#	def to_path(self, name):
#		#with self._db:
#		return urllib2.quote('/'.join(self._to_path(name)))
#
#	def render_template_view(self, name, *args, **kwargs):
#		return URLRegistry.call_view(name, db=self._db, *args, **kwargs )
#
#	def render_view(self, name, view):
#		return self.db.renderview(name, viewtype=view)
#
#	def get_user(self):
#		un = self._db.checkcontext()[0]
#		if un is not None:
#			return self._db.getuser(un)
#		else:
#			return None
#
#	def get_menu(self, depth=1):
#		recs = self.db.getchildtree(self.root, recurse=depth)
#		folders = self.db.getindexbyrecorddef('folder')
#		recs1 = {}
#		keys = filter(lambda x: x in folders, recs)
#		for key in keys:
#			value = recs[key] & folders
#			recs1[key] = value
#
#		recs = emen2.util.datastructures.Tree(recs1, self.root,
#									app=lambda x: (x, self.getindex(x)))
#
#		return recs
#
#	def _unfold_dict(self, dict):
#		result = []
#		[ [ result.append((key, item)) for item in items ] for key, items in dict.iteritems()]
#		return result
#
#
#
__version__ = "$Revision$".split(":")[1][:-1].strip()
