"""Backend interface definitions."""

import abc

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
        pass

    def open(self):
        # return Connection
        pass

    def init(self):
        pass
            
    def close(self):
        pass

    def rebuild_indexes(self):
        pass
        
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
        pass
        
    def open(self):
        pass
        
    def close(self):
        pass
        
    def truncate(self):
        pass
        
def IndexDB(BaseDB):
    def get(self, key, default=None):
        pass
        
    def keys(self, minkey=None, maxkey=None):
        pass
        
    def items(self, minkey=None, maxkey=None):
        pass
        
    def removerefs(self, key, items):
        pass
        
    def addrefs(self, key, items):
        pass
        
def CollectionDB(BaseDB):
    def new(self, *args, **kwargs): 
        pass

    def exists(self, key): 
        pass

    def filter(self, names=None): 
        pass

    def keys(self): 
        pass

    def items(self): 
        pass

    def values(self): 
        pass

    def get(self, key, filt=True): 
        pass

    def gets(self, keys, filt=True): 
        pass

    def _get_data(self, key, txn=None): 
        pass

    def validate(self, items): 
        pass

    def put(self, item, commit=True): 
        pass

    def puts(self, items, commit=True): 
        pass

    def _puts(self, items): 
        pass

    def _put_data(self, name, item): 
        pass

    def delete(self, name, flags=0): 
        pass

    def query(self, c=None, mode='AND', subset=None, keywords=None): 
        pass

    def getindex(self, param): 
        pass

    def rebuild_indexes(self): 
        pass

    def expand(self, names): 
        pass

    def parents(self, names, recurse=1): 
        pass

    def children(self, names, recurse=1): 
        pass

    def siblings(self, name): 
        pass

    def rel(self, names, recurse=1, rel='children', tree=False): 
        pass

    def pclink(self, parent, child): 
        pass

    def pcunlink(self, parent, child): 
        pass

    def relink(self, removerels=None, addrels=None): 
        pass

    def _bfs(self, key, rel='children', recurse=1):
        pass