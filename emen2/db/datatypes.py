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



class DatatypeManager(object):
    """Replacement class. Not ready yet."""
    _registered = {}

    @classmethod
    def register(cls, name):
        """Decorator used to register a :py:class:`~.vartypes.Vartype`

        :param str name: the name for the :py:class:`~.vartypes.Vartype`
        :returns: A function which takes a :py:class:`~.vartypes.Vartype` and registers it
        """
        def f(o):
            if name in cls._registered.keys():
                raise ValueError("""item %s already registered""" % name)
            #emen2.db.log.info("Registering %s"% name)
            o.name = property(lambda *_: name)
            cls._registered[name] = o
            return o
        return f



class Cacher(object):
    def __init__(self):
        self.cache = {}
        self.paramdefcache = {}
        self.caching = True

    def reset_cache(self):
        self.paramdefcache = {}
        self.cache = {}

    def start_caching(self):
        self.caching = True
        self.reset_cache()

    def stop_caching(self):
        self.caching = False
        self.reset_cache()

    def toggle_caching(self):
        self.caching = not self.caching

    def get_cache_key(self, *args, **kwargs):
        return (args, tuple(kwargs.items()))

    def store(self, key, result):
        self.cache[key] = result

    def check_cache(self, key):
        if self.cache.has_key(key):
            return True, self.cache[key]
        return False, None
    
    
class VartypeManager(object):
    """Registers available Vartypes, Properties, and Macros

    - Helper methods for access, validating, and rendering parameters
    - This class may be replaced in the future, by moving it to the
        appropriate Vartype/Property/Macro classes.
    """


    registered = {}
    vartypes = {}
    properties = {}
    macros = {}

    @classmethod
    def register_vartype(cls, name):
        """Decorator used to register a :py:class:`~.vartypes.Vartype`

        :param str name: the name for the :py:class:`~.vartypes.Vartype`
        :returns: A function which takes a :py:class:`~.vartypes.Vartype` and registers it
        """
        def f(o):
            if name in cls.vartypes.keys():
                raise ValueError("""vartype %s already registered""" % name)
            cls.registered[('vartype', name)] = o
            cls.vartypes[name] = o
            return o
        return f


    @classmethod
    def register_property(cls, name):
        def f(o):
            if name in cls.properties.keys():
                raise ValueError("""property %s already registered""" % name)
            cls.registered[('property', name)] = o
            cls.properties[name] = o
            return o
        return f


    @classmethod
    def register_macro(cls, name):
        def f(o):
            if name in cls.macros.keys():
                raise ValueError("""macro %s already registered""" % name)
            #emen2.db.log.info("REGISTERING MACRO (%s)"% name)
            cls.registered[('macro', name)] = o
            cls.macros[name] = o
            return o
        return f


    def __init__(self, db=None, keytype=None):
        self.db = db
        self.keytype = keytype
        self.cache = Cacher()



    ###################################
    # Validation
    ###################################

    def validate(self, pd, value):
        if value in NONEVALUES:
            return None

        if pd.property:
            value = self.properties[pd.property]().validate(self, pd, value, self.db)

        return self.vartypes[pd.vartype](cache=self.cache, db=self.db, pd=pd).validate(value)


    ###################################
    # Misc
    ###################################

    def get_vartype(self, name, *args, **kwargs):
        return self.vartypes[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_property(self, name, *args, **kwargs):
        return self.properties[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_macro(self, name, *args, **kwargs):
        return self.macros[name](cache=self.cache, db=self.db, *args, **kwargs)


    def get_vartypes(self):
        return self.vartypes.keys()


    def get_properties(self):
        return self.properties.keys()


    def get_macros(self):
        return self.macros.keys()



__version__ = "$Revision$".split(":")[1][:-1].strip()
