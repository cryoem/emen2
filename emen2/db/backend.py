"""Backend interface definitions."""

import abc

rni = NotImplementedError

class Connection(object):
    pass

class EMEN2DBEnv(object):
    def __init__(self, path=None):
        # Required attributes.
        self.path = path
        self.keytypes = {}
        self.dbenv = self.open()
        self.init()

    def create(self):
        raise rni
        
    def open(self):
        # return Connection
        raise rni

    def init(self):
        raise rni
            
    def close(self):
        raise rni

    def rebuild_indexes(self):
        raise rni
        
    def __getitem__(self, key, default=None):
        return self.keytypes.get(key, default)

class BaseDB(object):
    def __init__(self, filename, keyformat='str', dataformat='str', dataclass=None, dbenv=None, extension='bdb'):
        # Required attributes.
        self.filename = filename
        self.extension = extension
        self.dbenv = dbenv
        self.init()
        self.open()
    
    def init(self):
        raise rni
        
    def open(self):
        raise rni
        
    def close(self):
        raise rni
        
    def truncate(self):
        raise rni
        
def IndexDB(BaseDB):
    def get(self, key, default=None):
        raise rni
        
    def keys(self, minkey=None, maxkey=None):
        raise rni
        
    def items(self, minkey=None, maxkey=None):
        raise rni
        
    def removerefs(self, key, items):
        raise rni
        
    def addrefs(self, key, items):
        raise rni
        
def CollectionDB(BaseDB):
    def new(self, *args, **kwargs): 
        raise rni

    def exists(self, key): 
        raise rni

    def filter(self, names=None): 
        raise rni

    def keys(self): 
        raise rni

    def items(self): 
        raise rni

    def values(self): 
        raise rni

    def get(self, key, filt=True): 
        raise rni

    def gets(self, keys, filt=True): 
        raise rni

    def _get_data(self, key, txn=None): 
        raise rni

    def validate(self, items): 
        raise rni

    def put(self, item, commit=True): 
        raise rni

    def puts(self, items, commit=True): 
        raise rni

    def _puts(self, items): 
        raise rni

    def _put_data(self, name, item): 
        raise rni

    def delete(self, name): 
        raise rni

    def query(self, c=None, mode='AND', subset=None, keywords=None): 
        raise rni

    def getindex(self, param): 
        raise rni

    def rebuild_indexes(self): 
        raise rni

    def expand(self, names): 
        raise rni

    def parents(self, names, recurse=1): 
        raise rni

    def children(self, names, recurse=1): 
        raise rni

    def siblings(self, name): 
        raise rni

    def rel(self, names, recurse=1, rel='children', tree=False): 
        raise rni

    def pclink(self, parent, child): 
        raise rni

    def pcunlink(self, parent, child): 
        raise rni

    def relink(self, removerels=None, addrels=None): 
        raise rni

    def _bfs(self, key, rel='children', recurse=1):
        raise rni