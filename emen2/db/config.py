import re
import os
import sys
import glob
import imp
import json
import argparse

##### Mako template lookup #####

import mako
import mako.lookup

class AddExtLookup(mako.lookup.TemplateLookup):
    """This is a slightly modified TemplateLookup that
     adds '.mako' extension to all template names.

    Extends TemplateLookup methods:
        get_template           Adds '.mako' to filenames
        render_template        ""

    """
    def get_template(self, uri):
        return super(AddExtLookup, self).get_template('%s.mako'%uri)

    def render_template(self, name, ctxt):
        tmpl = self.get_template(name)
        return tmpl.render(**ctxt)

# Mako Template Loader
# Turn on HTML escaping by default. Use ${variable | n} to disable escaping.
templates = AddExtLookup(
    input_encoding='utf-8', 
    imports=['from emen2.utils import jsonencode'],
    default_filters=['h'],
    )

##### Config methods #####

def get_filename(package, resource=None):
    """Get the absolute path to a file inside a given Python package"""
    d = sys.modules[package].__file__
    if resource:
        d = os.path.dirname(d)
        d = os.path.abspath(d)
        return os.path.join(d, resource)
    return d

##### Email config helper #####

def mailconfig():
    from_addr = get('mail.from')
    smtphost = get('mail.smtphost') 
    return from_addr, smtphost

##### Extensions #####

def load_exts():
    for ext in config.get('extensions.exts'):
        load_ext(ext)

def load_views():
    for ext in config.get('extensions.exts'):
        load_view(ext)

def load_jsons(cb=None, *args, **kwargs):
    for ext in config.get('extensions.exts'):
        load_json(ext, cb=cb, *args, **kwargs)

def load_ext(ext):
    modulename = 'emen2.exts.%s'%ext
    if modulename in sys.modules:
        return
    paths = config.get('paths.exts')
    module = imp.find_module(ext, paths)
    ret = imp.load_module(ext, *module)
    # Extensions may have an optional "templates" directory,
    # which will be added to the template search path.
    templates.directories.insert(0, os.path.join(module[1], 'templates'))
    return ret

def load_view(ext):
    modulename = 'emen2.exts.%s.views'%ext
    if modulename in sys.modules:
        return
    paths = list(Config.globalns.paths.exts)
    module = imp.find_module(ext, paths)
    path = module[1]
    try:
        viewmodule = imp.find_module('views', [path])
    except ImportError, e:
        viewmodule = None
    if viewmodule:
        imp.load_module(modulename, *viewmodule)

def load_json(ext, cb=None, *args, **kwargs):
    path = resolve_ext(ext)
    if not cb:
        return
    for j in sorted(glob.glob(os.path.join(path, 'json', '*.json'))):
        cb(j, *args, **kwargs)

def resolve_ext(ext):
    paths = list(Config.globalns.paths.exts)
    return imp.find_module(ext, paths)[1]

##### Config #####

def get(key, default=None):
    return config.get(key, default)
    
def set(key, value):
    return config.set(key, value)

class Config(object):
    def __init__(self):
        self.data = {}
        self.home = 'test'
        self.loaded = False
        self.load(get_filename('emen2', 'db/config.core.json'))
        
    def load(self, infile):
        with open(infile, 'r') as f:
            data = f.read()
        data = json_strip_comments(data)
        data = json.loads(data)
        self.data = data
    
    def _wrap_path(self, root, d):
        # Recursively prefix string values with root path.
        if isinstance(d, basestring):
            if not d.startswith('/'):
                d = os.path.join(root, d)
        elif hasattr(d, 'items'):
            for k,v in d.items():
                d[k] = self._wrap_path(root, v)
        elif hasattr(d, '__iter__'):
            d = [self._wrap_path(root, i) for i in d]
        return d
    
    def get(self, key):
        path = key.replace('/', '.').split('.')
        ret = self.data
        for k in path:
            try:
                ret = ret[k]
            except Exception, e:
                raise KeyError("No such key: %s"%key)
        if path[0] == 'paths':
            return self._wrap_path(self.home, ret)
        return ret

    def set(self, key, value):
        raise NotImplementedError

config = Config()

##### Argparse options #####

class DBOptionsAP(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(DBOptionsAP, self).__init__(*args, **kwargs)
        self.add_argument("--home", help="EMEN2 database environment directory.")
        self.add_argument("--ext", "-e", help="Add extensions; can be comma-separated.")
        self.add_argument("--debug", help="Debug", action="store_true")
        self.add_argument("--version", help="Version", action="store_true")
        
if __name__ == "__main__":
    # Test
    config.load(sys.argv[1])
    print config.get('paths.binary')
    print config.get('record.sequence')
    print config.get('users.group_defaults')
    print config.get('security/email_whitelist')
    
    
    