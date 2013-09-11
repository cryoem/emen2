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
        render_template        

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

def json_strip_comments(data):
    """Remove JavaScript-style comments from a string."""
    r = re.compile('/\\*.*\\*/', flags=re.M|re.S)
    data = r.sub("", data)
    data = re.sub("\s//.*\n", "", data)
    return data

def get_filename(package, resource=None):
    """Get the absolute path to a file inside a given Python package."""
    d = sys.modules[package].__file__
    if resource:
        d = os.path.dirname(d)
        d = os.path.abspath(d)
        return os.path.join(d, resource)
    return d

##### Email config helper #####

def mailconfig():
    """Return mail configuration: from address, smtp host."""
    from_addr = get('mail.from')
    smtphost = get('mail.smtphost') 
    return from_addr, smtphost

##### Config #####

def get(key, default=None):
    return config.get(key, default)
    
def set(key, value):
    return config.set(key, value)

class Config(object):
    
    home = property(lambda self:self.data.get('home'))
    
    def __init__(self):
        self.data = {}
        self.load(get_filename('emen2', 'db/config.core.json'))
    
    def get(self, key, default=None):
        # Get a config value.
        # if not self.home:
        #    raise ValueError("No EMEN2DBHOME directory.")
        path = self._key_path(key)
        root = self.data
        for k in path:
            try:
                root = root[k]
            except Exception, e:
                raise KeyError("No such key: %s"%key)
        if path[0] == 'paths':
            return self._wrap_path(self.home, root)
        return root

    def set(self, key, value):
        print "setting...", key, value
        path = self._key_path(key)
        root = self.data
        for k in path[:-1]:
            try:
                root = root[k]
            except Exception, e:
                raise KeyError("No such key: %s"%key)
        root[path[-1]] = value
    
    def _key_path(self, key, root=None):
        if root is None:
            root = self.data
        return key.replace('/', '.').split('.')
    
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

    def update(self, d):
        for k,v in d.items():
            self._update(k, v, self.data)
    
    def _update(self, key, value, root=None):
        if root is None:
            root = self.data
        if hasattr(value, 'items'):
            root[key] = root.get(key, {})
            for k,v in value.items():
                self._update(k, v, root[key])
        else:
            root[key] = value

    def sethome(self, home):
        if not home:
            raise ValueError("No EMEN2DBHOME directory.")
        self.data['home'] = home
        self.load(os.path.join(self.home, 'config.json'))
        
    def load(self, infile):
        if not os.path.exists(infile):
            return
        with open(infile, 'r') as f:
            data = f.read()
        data = json_strip_comments(data)
        data = json.loads(data)
        self.update(data)
        
    # Helper methods    
    def setarg(self, arg):
        key, _, value = arg.partition("=")
        # This is an extremely crude conversion
        # to JSON bool/null/int/float.
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.lower() == "null":
            value = None
        elif value.isdigit():
            value = int(value)
        elif value.startswith('-') and value[1:].isdigit():
            value = int(value)
        elif "." in value:
            value = float(value)
        else:
            pass
        self.set(key, value)

# Configuration singleton.
config = Config()

class ExtHandler(object):        
    def load_exts(self):
        exts = config.get('extensions.exts')
        for i in exts:
            self.load_ext(i)
        
    def load_ext(self, ext):
        # Load an extension and place the 
        #   templates directory in the template search path.
        modulename = 'emen2.exts.%s'%ext
        if modulename in sys.modules:
            return
        module = imp.find_module(ext, self._ext_paths())
        ret = imp.load_module(ext, *module)
        # Extensions may have an optional "templates" directory,
        # which will be added to the template search path.
        templates.directories.insert(0, os.path.join(module[1], 'templates'))
    
    def load_views(self):
        exts = config.get('extensions.exts')
        for i in exts:
            self.load_view(i)
    
    def load_view(self, ext):
        modulename = 'emen2.exts.%s.views'%ext
        if modulename in sys.modules:
            return
        module = imp.find_module(ext, self._ext_paths())
        path = module[1]
        try:
            viewmodule = imp.find_module('views', [path])
        except ImportError, e:
            viewmodule = None
        if viewmodule:
            imp.load_module(modulename, *viewmodule)

    def _ext_paths(self):
        paths = [get_filename('emen2', 'exts')]
        paths += config.get('paths.exts') 
        if os.getenv('EMEN2EXTPATH'):
            for path in filter(None, os.getenv('EMEN2EXTPATH','').split(":")):
                paths.append(path)
        return paths
    
# Extension handler singleton.
exthandler = ExtHandler()    
    
##### Argparse options #####

class DBOptions(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        """A nice argument parser for EMEN2."""
        kwargs['add_help'] = False
        super(DBOptions, self).__init__(*args, **kwargs)
        self.add_argument("--home", "-h", help="EMEN2 database environment directory.")
        self.add_argument("--ext", "-e", help="Add extensions; can be comma-separated.", action="append")
        self.add_argument("--set", dest="setarg", help="Change setting, e.g.: web.port=8080", action="append")
        self.add_argument("--debug", help="Show debugging messages.", action="store_true")
        self.add_argument("--help", action='help', help='Show this help message and exit.')
    
    def parse_args(self, *args, **kwargs):
        """Convenience to insert home/ext/debug/etc into the configuration."""
        opts = super(DBOptions, self).parse_args(*args, **kwargs)

        if opts.home:
            config.sethome(opts.home)

        if opts.ext:
            exts = []
            for ext in opts.ext:
                exts.extend(ext.split(','))
            config.data['extensions']['exts'] = exts

        if opts.debug:
            import emen2.db.log
            emen2.db.log.logger.setlevel('DEBUG')

        if opts.setarg:
            for arg in opts.setarg:
                config.setarg(arg)
        
        exthandler.load_exts()
        return opts
        
##### Twisted Options #####
        
import twisted.python.usage
        
class DBOptionsTwisted(twisted.python.usage.Options):
    """Options for starting EMEN2 using twistd / emen2ctl."""

    optParameters = [
        ['home', 'h', None, 'EMEN2 database environment directory'],
        ['ext', 'e', None, 'Add extension; can be comma-separated.'],
    ]

    def postProcess(self):
        ## note that for optFlags self[option_name] is 1 if the option is given and 0 otherwise
        ##     this converts those values into the appropriate bools
        # these default to True:
        pass
        
