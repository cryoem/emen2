from functools import partial
from itertools import chain
import emen2.Database
from emen2.subsystems.routing import URLRegistry


import emen2.debug as _d
d = _d.DebugState()

class IntegrityError(ValueError): pass

class DBTree(object):
    root = property(lambda self: self.__root)
    
    def __init__(self, db, ctxid, host=None, root=None):
        self.__db = db
        self.__ctxid = ctxid
        self.__host = host
        self.__root = root or min(db.getindexbyrecorddef('folder', ctxid=ctxid, host=host))
        self.getrecord = partial(db.getrecord, ctxid=ctxid, host=host) # make getrecord calls shorter

    def __getpath(self, path=None):
        if path != None:
            path = self.get_path_id(path)
        else:
            path = [self.root]
        return path
            
    def __dostuff(self, name, subfolders):
        for (rectype, rec) in subfolders:
            if (str(rec) == name) or (self.getrecord(rec)['indexby'] == name) \
                                or (self.getrecord(rec)['%s_name' % rectype] == name):
                yield (rectype, rec)
        
    def __unfold_dict(self, dict):
        for key in dict:
            for item in dict[key]:
                yield (key, item)
    
    def __select(self, data, **kwargs):
        for param in kwargs:
            data &= self.__db.getindexbyvalue(param, kwargs[param], ctxid=self.__ctxid, host=self.__host)
        # no return since sets are weakly referenced
        
    def __to_path(self, recid, path=None):
        path = path or []
        parents = self.__db.getparents(recid, ctxid=self.__ctxid, host=self.__host)
        if self.root not in parents:
            path.extend(self.__to_path(parents.pop(), path))
        path.append(str(recid))
        return path
    
    def getindex(self, recid):
        rec = self.getrecord(recid)
        index = str(recid)
#        name = rec['%s_name' % rectype]
#        if name:
#            index = name
        indexby = rec['indexby']
        if indexby:
            index = indexby
        return index
        
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
        children = self.__db.getchildren(cur_dir, keytype='record', ctxid=self.__ctxid, host=self.__host)
        subfolders = self.__unfold_dict(self.__db.groupbyrecorddef(children, self.__ctxid))
        if name == '*':
            result = subfolders
        else:
            result = self.__dostuff(name, subfolders)
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
            result.update([ elem[1] for elem in self.get_child_id('*', rec) ])
        self.__select(result, **kwargs)
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
            siblings = self.__unfold_dict(self.__db.groupbyrecorddef(siblings, self.__ctxid))
            result = [elem[1] for elem in self.__dostuff(name, siblings)]
        self.__select(result, **kwargs)
        return result
    
    def to_path(self, recid):
        return str.join('/', self.__to_path(recid))
    
    def reverse(self, name, *args, **kwargs):
        return '/db'+(URLRegistry.reverselookup(name, *args, **kwargs) or '')
    
    def render_view(self, recid, view):
        return db.renderview(recid, viewtype=view)


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