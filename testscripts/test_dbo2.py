class DBO2(object):
    def __init__(self, data=None):
        self.data = data or {}
    def __getattr__(self, key):
        if key in self.data:
            return self.data[key]
        raise KeyError
        
a = DBO2({'creator':'ianrees'})
print a.creator
print a.data
        