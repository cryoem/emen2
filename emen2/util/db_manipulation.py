from functools import partial
import emen2.Database

import emen2.debug as _d
d = _d.DebugState()

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

class IntegrityError(ValueError): pass

class DBTree(object):
    root = property(lambda self: self.__root)
    
    def __init__(self, db, ctxid, host=None, root=None):
        self.__db = db
        self.__ctxid = ctxid
        self.__host = host
        self.__root = root or min(db.getindexbyrecorddef('folder', ctxid=ctxid, host=host))

    def get_path_id(self, path, cur_dir=None, dbinfo=None):
        '''raises StopIteration if path does not exist'''
        dbinfo=dbinfo or {}
        cur_dir = cur_dir or self.root
            
        if path != []: # recurse if we are not at the end of the path list
            tmp = self.get_child_id(path[0], cur_dir=cur_dir, **dbinfo)
            return self.get_path_id(path[1:], tmp, dbinfo)
        
        else: # if we are at the end of the path list, we must be where we want to be
            return cur_dir
    
    def get_child_id(self, name, cur_dir):
        '''returns first child with a given folder_name'''
        ctxid = self.__ctxid
        host = self.__host
        children = self.__db.getchildren(cur_dir, keytype='record', ctxid=ctxid, host=host)
        subfolders = self.__unfold_dict(self.__db.groupbyrecorddef(children, ctxid))
        return self.__dostuff(name, subfolders).next()[1]
    
    def __dostuff(self, name, subfolders):
        getrecord = partial(self.__db.getrecord, ctxid=self.__ctxid, host=self.__host) # make getrecord calls shorter
        for (rectype, rec) in subfolders:
            if (str(rec) == name) or (getrecord(rec)['%s_name' % rectype] == name):
                yield (rectype, rec)
        
    def __unfold_dict(self, dict):
        for key in dict:
            for item in dict[key]:
                yield (key, item)

def get_child_id(name, db, ctxid, cur_dir=None, host=None):
    return DBTree(db, ctxid, host).get_child_id(name, cur_dir=cur_dir)

def get_child(name, db, ctxid, cur_dir, host=None):
    '''returns first child with a given folder_name'''
    return db.getrecord(get_child_id(name, db, ctxid, cur_dir), ctxid)

def get_path_id(path, cur_dir=None, dbinfo=None):
    db, ctxid, host = dbinfo['db'], dbinfo['ctxid'], dbinfo['host']
    return DBTree(db, ctxid, host).get_path_id(path, cur_dir=cur_dir)

def get_path(path, cur_dir=None, dbinfo=None):
    '''raises StopIteration if path does not exist'''
    db, ctxid, host = dbinfo['db'], dbinfo['ctxid'], dbinfo['host']
    return db.getrecord(get_path_id(path, cur_dir, dbinfo), ctxid, host=host)
        
def get_root_id(db, ctxid, host=None):
    return DBTree(db, ctxid, host).root

def get_root(db, ctxid, host=None):
    return db.getrecord(get_root_id(db, ctxid, host))
