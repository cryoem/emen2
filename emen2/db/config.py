# $Id: config.py,v 1.171 2013/06/04 10:12:23 irees Exp $
"""This module manages EMEN2 configurations and options.

Methods:
    get_filename(package, resource)
    defaults()
    get(key, default=None)
    set(key, value)

Classes:
    DBOptions

"""

import os
import sys
import glob
import imp

import jsonrpc.jsonutil

# EMEN2 imports
# NOTHING else should import emen2.db.globalns.
# It is a PRIVATE module!
import emen2.db.globalns

# Note:
#     Be very careful about importing EMEN2 modules here!
#     This module is loaded by many others, it can create circular
#     dependencies very easily!

basestring = (str, unicode)

##### Mako template lookup #####

import mako
import mako.lookup

class AddExtLookup(mako.lookup.TemplateLookup):
    """This is a slightly modified TemplateLookup that
     adds '.mako' extension to all template names.

    Extends TemplateLookup methods:
        get_template        Adds '.mako' to filenames
        render_template        ""

    """
    def get_template(self, uri):
        return super(AddExtLookup, self).get_template('%s.mako'%uri)

    def render_template(self, name, ctxt):
        tmpl = self.get_template(name)
        return tmpl.render(**ctxt)

# Mako Template Loader
# Turn on HTML escaping by default. Use ${variable | n} to disable escaping.

# todo: fix jsonrpc, to escape forward slashes -- until then..
# ["from jsonrpc.jsonutil import encode as jsonencode"]

templates = AddExtLookup(
    input_encoding='utf-8', 
    imports=['from emen2.db.util import jsonencode'],
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

def get(key, default=None, rv=True):
    """Get a configuration value.

    :param key: Configuration key
    :keyword default: Default value if key is not found
    :return: Configuration value

    """
    result = Config.globalns.watch(key, default=default)
    if rv:
        result = result.get()
    return result

# This will eventually help lock
# the configuration for setting
def set(key, value):
    """Set a configuration value.

    :param key: Configuration key
    :param value: Configuration value

    """
    raise NotImplementedError, "Soon."


##### Email config helper #####

def mailconfig():
    from_addr = get('mail.from')
    smtphost = get('mail.smtphost') 
    return from_addr, smtphost


##### Extensions #####

def load_exts():
    for ext in Config.globalns.extensions.exts:
        load_ext(ext)

def load_views():
    for ext in Config.globalns.extensions.exts:
        load_view(ext)

def load_jsons(cb=None, *args, **kwargs):
    for ext in Config.globalns.extensions.exts:
        load_json(ext, cb=cb, *args, **kwargs)

def load_ext(ext):
    modulename = 'emen2.exts.%s'%ext
    # print "Loading extension...", modulename
    if modulename in sys.modules:
        # print "%s already loaded"%modulename
        return
    paths = list(Config.globalns.paths.exts)
    module = imp.find_module(ext, paths)
    ret = imp.load_module(ext, *module)
    # Extensions may have an optional "templates" directory,
    # which will be added to the template search path.
    templates.directories.insert(0, os.path.join(module[1], 'templates'))
    return ret

def load_view(ext):
    # Extensions may have an optional "views" module.
    modulename = 'emen2.exts.%s.views'%ext
    # print "Loading views...", modulename
    if modulename in sys.modules:
        # print "%s already loaded"%modulename
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



##### Configuration loader #####

class Config(object):
    globalns = emen2.db.globalns.GlobalNamespace()

    def load_file(self, fn):
        '''Load a single configuration file

        :param fn: the filename of the configuration file'''
        self.globalns.from_file(fn)

    def load_data(self, *args, **data):
        '''Load configuration variables into the namespace'''
        if args:
            for dct in args:
                self.load_data(**dct)

        for key, value in data.items():
            # This needs to use setattr() so @properties will work.
            setattr(self.globalns, key, value)

    def require_variable(self, var_name, value=None, err_msg=None):
        '''Assert that a certain variable has been loaded

        :param var_name: the variable to be checked
        :param value: the value it should have, if this is None, the value is ignored
        :param err_msg: the error message to be displayed if the variable is not found
        :raises ValueError: if the variable is not found'''

        #NOTE: if we want None to be a valid config option, this must change
        if value is not None and self.globalns.getattr(var_name, value) != value:
            raise ValueError(err_msg)
        elif self.globalns.getattr(var_name) is None:
            raise ValueError(err_msg)
        else:
            return True



##### Default OptionParser #####
# This has been converted to Twisted usage.Options parser
# to work with "twistd".

from twisted.python import usage

class DBOptions(usage.Options):
    """Base database options."""

    optFlags = [
        ['quiet', None, 'Quiet'],
        ['debug', None, 'Print debug'],
        ['version', None, 'EMEN2 Version'],
        ['create', None, 'Create new database environment'],
        ['nosnapshot', None, 'Disable Berkeley DB Multiversion Concurrency Control (Snapshot)']
    ]

    optParameters = [
        ['home', 'h', None, 'EMEN2 database environment directory'],
        ['ext', 'e', None, 'Add extension; can be comma-separated.'],
        ['loglevel', 'l', None, '']
    ]

    def opt_configfile(self, file_):
        self.setdefault('configfile', []).append(file_)

    opt_c = opt_configfile

    def postProcess(self):
        ## note that for optFlags self[option_name] is 1 if the option is given and 0 otherwise
        ##     this converts those values into the appropriate bools
        # these default to True:
        for option_name in ['create', 'quiet', 'debug', 'version']:
            self[option_name] = bool(self[option_name])

        # these default to False:
        for option_name in ['nosnapshot']:
            self[option_name] = not bool(self[option_name])

    def load_config(self):
        # Do additional processing during configuration loading
        pass


class UsageParser(object):

    def __init__(self, optclass=None, options=None):
        # Use the default DBOptions if none is provided
        if not optclass:
            optclass = DBOptions

        if not options:
            options = optclass()
            options.parseOptions()

        self.options = options
        self.config = Config()
        self.load_config()


    def load_config(self, **kw):
        if self.config.globalns.getattr('CONFIG_LOADED', False):
            return

        # Eventually 'with' will unlock/lock the globalns
        # with globalns:
        self._load_config(**kw)
        self.config.globalns.CONFIG_LOADED = True


    def _load_config(self, **kw):
        # Set EMEN2DBHOME from the options or environment variable.
        h = self.options.get('home', os.getenv("EMEN2DBHOME"))

        # print "EMEN2 config loader: %s"%h
        self.config.load_data(EMEN2DBHOME=h)

        # Load the base configuration.
        self.config.load_file(get_filename('emen2', 'db/config.base.json'))

        # Load other specified config files
        for f in self.options.get('configfile', []):
            self.config.load_file(f)

        # EMEN2DBHOME must have been specified in either -h, $EMEN2DBHOME,
        # or set a configuration file.
        self.config.require_variable(
            'EMEN2DBHOME',
            None,
            err_msg="You must specify an EMEN2 database environment, either using the -h (--home) argument or the environment variable $EMEN2DBHOME")
        if h is None:
            h = self.config.globalns.getattr('EMEN2DBHOME', h)

        # Load any config file in EMEN2DBHOME
        self.config.load_file(os.path.join(h, "config.json"))

        # Set default log levels
        log_level = self.config.globalns.getattr('log_level', 'INFO')
        if self.options['quiet']:
            log_level = 'ERROR'
        elif self.options['debug']:
            log_level = 'DEBUG'
        elif self.options['loglevel']:
            log_level = self.options['loglevel']
        self.config.load_data(log_level=log_level)

        # Make sure paths to log files exist
        if not os.path.exists(self.config.globalns.paths.log):
            os.makedirs(self.config.globalns.paths.log)

        # EXTPATHS points to directories containing emen2 ext modules.
        # This will be used with imp.find_module(ext, self.config.globalns.paths.exts)
        self.config.globalns.paths.exts.append(get_filename('emen2', 'exts'))
        if os.getenv('EMEN2EXTPATH'):
            for path in filter(None, os.getenv('EMEN2EXTPATH','').split(":")):
                self.config.globalns.paths.exts.append(path)

        self.config.globalns.paths.exts.append(os.path.join(h, 'exts'))

        # Add the extensions, including the 'base' extension
        exts = self.options.get('ext')
        if exts:
            exts = exts.split(',')
            if 'base' not in exts:
                exts.insert(0,'base')
            exts.extend(self.config.globalns.extensions.exts)
            self.config.globalns.extensions.exts = exts

        # Create new database?
        self.config.globalns.params.create = self.options['create']

        # Enable root user?
        # self.config.globalns.ENABLEROOT = self.values.enableroot or False

        # Do anything defined by the usage.Options class
        self.options.load_config()

        # Tell the logger that we're initialized!
        import emen2.db.log
        emen2.db.log.logger.init()


__version__ = "$Revision: 1.171 $".split(":")[1][:-1].strip()
