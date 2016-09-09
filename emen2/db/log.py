# $Id: log.py,v 1.29 2013/05/31 23:22:10 irees Exp $
"""EMEN2 logging

Functions:
    msg
    info
    init
    error
    warn
    debug
    security
    index
    commit
"""


import traceback
import functools
import os.path
import sys

import twisted.python.log

from twisted.python import util
from twisted.python.log import _safeFormat, textFromEventDict

import emen2.db.config

class PrintLogger(object):
    def emit(self, eventDict):
        print eventDict

class SubLogger(twisted.python.log.FileLogObserver):
    pass

class WebLogger(twisted.python.log.FileLogObserver):
    def emit(self, eventDict):
        messages = eventDict.get("message")
        for message in messages:
            util.untilConcludes(self.write, message+"\n")
            util.untilConcludes(self.flush)

class ErrorLogger(twisted.python.log.FileLogObserver):
    pass
    
class EMEN2Logger(object):
    log_levels = dict(
            DEBUG=-1,
            TXN=1,
            INIT=2,
            INDEX=3,
            INFO=4,
            COMMIT=5,
            WEB=6,
            WARN=8,
            SECURITY=9,
            ERROR=10,
            CRITICAL=11,
            ALL=0
    )
    
    def __init__(self):
        """Initialize logging system."""
        # print "EMEN2Logger.__init__"
        self.started = False
        self.log_level = 0
        self.loggers = {}
        # Turn on logging to stdout by default
        # twisted.python.log.startLogging(sys.stdout, setStdout=False)

    def init(self):
        """Start logging system."""
        # The configuration has been loaded
        self.logpath = emen2.db.config.get("paths.log")
        self.log_level = self.log_levels.get(emen2.db.config.get('log_level', 0))

    def start(self):
        """Start file-backed logging."""
        self.started = True

        # Open the various log files.        
        if not self.logpath:
            raise Exception, "No log path set"
            
        self.loggers["INFO"] = SubLogger(open(os.path.join(self.logpath, "emen2.log"), "a+"))
        self.loggers["SECURITY"] = SubLogger(open(os.path.join(self.logpath, "security.log"), "a+"))
        self.loggers["ERROR"] = ErrorLogger(open(os.path.join(self.logpath, "error.log"), "a+"))
        self.loggers["WEB"] = WebLogger(open(os.path.join(self.logpath, "access.log"), "a+"))

    def stop(self):
        """Stop file-backed logging."""
        self.started = False
        for k,v in self.loggers.items():
            v.close()

    def emit(self, e):
        """Twisted log file observer function."""
        level = e.get("system", "INFO")
        output = self.loggers.get(level, self.loggers["INFO"])
        output.emit(e)

    def log(self, message, level='INFO'):
        """Print or write the log message."""
        priority = self.log_levels.get(level, 0)        
        if priority < self.log_level:
            return

        # If we're using twisted logging, pass through...
        if self.started: 
            twisted.python.log.msg(message, system=level)
        else:
            pass
            try:
                print "[%s]"%level, unicode(message).encode('utf-8')
            except UnicodeDecodeError:
                print message
            
# Create the logger
logger = EMEN2Logger()

def print_exception():
    traceback.print_exc()

def msg(msg='', level='INFO'):
    logger.log(msg, level)

# Aliases
info = functools.partial(msg, level='INFO')
init = functools.partial(msg, level='INIT')
error = functools.partial(msg, level='ERROR')
warn = functools.partial(msg, level='WARN')
debug = functools.partial(msg, level='DEBUG')
security = functools.partial(msg, level='SECURITY')
index = functools.partial(msg, level='INDEX')
commit = functools.partial(msg, level='COMMIT')
web = functools.partial(msg, level='WEB')
