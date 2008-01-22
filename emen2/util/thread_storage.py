import thread

class ThreadStorage(object):
    storage = {}
    def __init__(self, key=None):
        if key == None:
            key = thread.get_ident()
        if self.storage.get(key, False) == False:
            self.storage[key] = {} 
        self.__storage = self.storage[key]
    def __getitem__(self, name):
        return self.__storage[name]
    def __setitem__(self, name, value):
        self.__storage[name] = value
    def __getattribute__(self, name):
        try:
            result = object.__getattribute__(self, name)
        except AttributeError:
            result = getattr(object.__getattribute__(self, '_%s__storage' % self.__class__.__name__), name)
        return result
