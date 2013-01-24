# $Id$
"""Vartype, Property, and Macro managers

Classes:
    VartypeManager:
        = Registers available Vartypes, Properties, and Macros
        - Helper methods for access, validating, and rendering parameters
        - This class may be replaced in the future, by moving it to the
            appropriate Vartype/Property/Macro classes.
"""

import re
import cgi

NONEVALUES = [None, "", "N/A", "n/a", "None"]

import emen2.db.properties
import emen2.db.vartypes
import emen2.db.macros

class ExtensionManager(object):
    """Example."""
    ##### Extensions #####
    registered = {}
    @classmethod
    def register(cls, name):
        def f(o):
            if name in cls.registered:
                raise ValueError("""%s is already registered""" % name)
            cls.registered[name] = o
            return o
        return f



class Cacher(object):
    def __init__(self):
        self.cache = {}

    def reset_cache(self):
        self.cache = {}

    def get_cache_key(self, *args, **kwargs):
        return (args, tuple(kwargs.items()))

    def store(self, key, result):
        self.cache[key] = result

    def check_cache(self, key):
        if self.cache.has_key(key):
            return True, self.cache[key]
        return False, None
    
    
class VartypeManager(object):
    """This is going away."""

    def __init__(self, db=None, keytype=None):
        self.db = db
        self.keytype = keytype
        self.cache = Cacher()

    ###################################
    # Misc
    ###################################

    def get_vartype(self, name, *args, **kwargs):
        return emen2.db.vartypes.Vartype.registered[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_property(self, name, *args, **kwargs):
        return emen2.db.properties.Property.registered[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_macro(self, name, *args, **kwargs):
        return emen2.db.macros.Macro.registered[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_vartypes(self):
        return emen2.db.vartypes.Vartype.registered.keys()


    def get_properties(self):
        return emen2.db.properties.Property.registered.keys()


    def get_macros(self):
        return emen2.db.macros.Macro.registered.keys()



__version__ = "$Revision$".split(":")[1][:-1].strip()
