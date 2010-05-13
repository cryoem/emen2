import urllib2
import emen2.util.datastructures
#import emen2.Database

from emen2.subsystems.routing import URLRegistry

import emen2.globalns
g = emen2.globalns.GlobalNamespace()

class Context(object):
	'''Partial context for views that don't need db access'''
	def reverse(self, _name, *args, **kwargs):
		_full = kwargs.get('_full', False)
		prefix = '%s' % g.EMEN2WEBROOT
		if not prefix.endswith('/'): prefix = '%s/' % prefix
		if _full == True:
			prefix = 'http://%(host)s:%(port)s%(root)s' % dict(host=g.EMEN2HOST, port=g.EMEN2PORT, root=prefix)

		result = '%s%s%s' % (prefix, 'db', (
			URLRegistry.reverselookup(_name, *args, **kwargs).replace('//','/') or ''))
		if not result.endswith('/'): result = '%s/' % result
		return result


class DBTree(Context):
	'''emulates a tree structure on top of the Database'''
	root = property(lambda self: self.__root)
	ctxid = property(lambda self: self.__ctxid)

	def __init__(self, db=None, root=None):
		if db is not None:
			self.db = db
			self.__db = db

			# ian: don't disable this
			if 'folder' in db.getrecorddefnames() and root is None:
				self.__root = min(db.getindexbyrecorddef('folder') or [0])
			else:
				self.__root = root

			self.__initmethods()

		else: g.log.msg('LOG_WARNING', 'db is None...')

	def __initmethods(self):
		self.get_path_id = self.__db._wrapmethod(self.__get_path_id)

	def __get_path_id(self, path, cur_dir=None):
		'''
		takes a list iterates through it and follows parent-child relationships in the db
		selecting children with a recname parameter equal to the current list item

		empty list signifies current directory

		raises StopIteration if path does not exist
		'''
		cur_dir = cur_dir or self.root
		if path == []: # empty path == found result
			result = set([cur_dir])
		else: # recurse if we are not at the end of the path list
			children = self.get_child_id(path[0], cur_dir=cur_dir)
			result = reduce(set.union, self.__gpi_helper_1(path[1:], children), set())
		return result


	def __gpi_helper_1(self, path, children):
		for recid in children:
			yield self.__get_path_id(path, recid)


	def get_child_id(self, name, cur_dir):
		'''returns children of a record with a given recname'''
		children = self.__db.getchildren(cur_dir, filt=True)
		if name == '*':
			[(yield child) for child in children]
		else:
			for rec in self.__dostuff(name, children):
				yield rec


	def __dostuff(self, name, records):
		recnamep = self.__db.getindexbyvalue('name_folder', name)
		for rec in records:
			if (str(rec) == name) or (rec in recnamep):
				yield (rec)
			elif self.render_view(rec, 'recname') == name:
				yield (rec)


	def __select(self, data, **kwargs):
		for param, value in kwargs.iteritems():
			data &= self.__db.getindexbyvalue(param, value)
		# no return since sets are weakly referenced


	def __getpath(self, path=None):
		if path != None: path = self.get_path_id(path)
		else: path = [self.root]
		return path

	def __to_path(self, recid, path=None):
		path = path or []
		parents = self.__db.getparents(recid)
		if self.root not in parents:
			path.extend(self.__to_path(parents.pop(), path))
		path.append(self.getindex(recid))
		return path

	def getindex(self, recid=None, rec=None):
		rec = self.__db.getrecord(recid, filt=False) if rec is None else rec
		index = rec.get('name_folder', str(recid))
		if index == None:
			index = self.render_view(rec.recid, 'recname')
		return index

	def get_title(self, recid):
		return self.render_view(recid, 'recname').rpartition(':')[0::2]

	def chroot(self, recid):
		self.__root = recid




	def get_parents(self, path=None, **kwargs):
		path = self.__getpath(path)
		result = set()
		for rec in path:
			result.update(self.__db.getparents(rec))
		self.__select(result, **kwargs)
		return result

	def get_children(self, path=None, **kwargs):
		result = set()
		if path is None:
			result = self.db.getchildren(self.root)
		else:
			path = self.__getpath(path)
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
			result.update(self.__db.getchildren(parent))
		self.__select(result, **kwargs)
		return result

	def get_sibling(self, name, **kwargs):
		siblings = self.get_siblings()
		if name == '*':
			result = siblings
		else:
			result = [elem[1] for elem in self.__dostuff(name, siblings)]
		self.__select(result, **kwargs)
		return result

	def to_path(self, recid):
		#with self.__db:
		return urllib2.quote('/'.join(self.__to_path(recid)))

	def render_template_view(self, name, *args, **kwargs):
		return URLRegistry.call_view(name, db=self.__db, *args, **kwargs )

	def render_view(self, recid, view):
		return self.db.renderview(recid, viewtype=view)

	def get_user(self):
		un = self.__db.checkcontext()[0]
		if un is not None:
			return self.__db.getuser(un)
		else:
			return None

	def get_menu(self, depth=1):
		recs = self.db.getchildren(self.root, recurse=depth, tree=True)#, filt=True)
		folders = self.db.getindexbyrecorddef('folder')
		recs1 = {}
		keys = filter(lambda x: x in folders, recs)
		for key in keys:
			value = recs[key] & folders
			recs1[key] = value

		recs = emen2.util.datastructures.Tree(recs1, self.root,
									app=lambda x: (x, self.getindex(x)))

		return recs

	def __unfold_dict(self, dict):
		result = []
		[ [ result.append((key, item)) for item in items ] for key, items in dict.iteritems()]
		return result



