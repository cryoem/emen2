# $Id$
"""Deprecated..."""


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
    

__version__ = "$Revision$".split(":")[1][:-1].strip()
