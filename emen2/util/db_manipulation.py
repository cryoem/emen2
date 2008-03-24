from functools import partial
import emen2.Database
import g

#from g import debug

def get_path_id(path, cur_dir=None, dbinfo=None):
    '''raises StopIteration if path does not exist'''
    dbinfo=dbinfo or {}
    
    if cur_dir == None: # if cur_dir not supplied, assume an absolute path
        cur_dir = get_root_id(**dbinfo)
        
    if path != []: # recurse if we are not at the end of the path list
#        try:
        tmp = get_child_id(path[0], cur_dir=cur_dir, **dbinfo)
#        except StopIteration:
#            return cur_dir
        return get_path_id(path[1:], tmp, dbinfo)
    else: # if we are at the end of the path list, we must be where we want to be
        return cur_dir
    
def get_child_id(name, db, ctxid, cur_dir, host=None):
    '''returns first child with a given folder_name'''
    getrecord = partial(db.getrecord, ctxid=ctxid, host=host) # make getrecord calls shorter
    children = db.getchildren(cur_dir, keytype='record', ctxid=ctxid, host=host)
    g.debug('children: %s\nsubfolders: %s' % (children, db.groupbyrecorddef(children, ctxid)))
    subfolders = unfold_dict(db.groupbyrecorddef(children, ctxid))
    return ((rectype, rec) for (rectype, rec) in subfolders # get all children of the current record 
                if  (getrecord(rec)['%s_name' % rectype] == name) or (str(rec) == name) # who have the right folder name or record id
              ).next()[1]  # only return the first match
        


def get_root_id(db, ctxid, host=None):
    '''gets the folder with the lowest id
    NOTE: a better implementation might take a record and recurse upward to a record without a parent'''
    return min(db.getindexbyrecorddef('folder', ctxid=ctxid, host=host))


def get_child(name, db, ctxid, cur_dir, host=None):
    '''returns first child with a given folder_name'''
    return db.getrecord(get_child_id(name, db, ctxid, cur_dir), ctxid)

def get_root(db, ctxid, host=None):
    return db.getrecord(get_root_id(db, ctxid), ctxid)

def get_path(path, cur_dir=None, dbinfo=None):
    '''raises StopIteration if path does not exist'''
    db, ctxid = dbinfo['db'], dbinfo['ctxid']
    g.debug('path == %s' % path)
    return db.getrecord(get_path_id(path, cur_dir, dbinfo), ctxid)

#def find_in_set(recset, dbinfo=None):
#        dbinfo=dbinfo or {}
        
def unfold_dict(dict):
    '''
    returns a generator which yields (key,item) pairs:
    
    >>> a = unfold_dict(dict(a=[1,2,3], b=[2], c=[3], d=[123123,123123,23445]))
    >>> a.next()
    ('a', 1)
    '''
    for key in dict:
        for item in dict[key]:
            yield (key, item)
    
    #[ [  (yield  (key, item)) for item in dict[key] ] for key in dict ]