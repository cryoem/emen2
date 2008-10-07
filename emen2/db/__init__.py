##############
# Database.py  Steve Ludtke  05/21/2004
##############

# TODO:
# read-only security index
# search interface
# XMLRPC interface
# XML parsing
# Database id's not supported yet


"""This module encapsulates an electronic notebook/oodb

Note that the database does have a security model, but it cannot be rigorously enforced at the python level.
That is, a programmer using this library will not be able to accidentally violate the security model, but
with sufficient intent and knowledge it is possible. To use this module securely it must be encapsulated
by another layer, say an xmlrpc server...
"""

from UserDict import DictMixin
from emen2.emen2config import *
from functools import partial
from xml.sax.saxutils import escape, unescape, quoteattr
import atexit
import operator
import os
import re
import hashlib
import sys
import traceback



#Set = set
__all__ = ['btrees', 'datastorage', 'user', 'database']
#from btrees import *
#from datastorage import *
#from user import *
#from database import * 

    


def get(self, key, default=None):
    try:
        return self[key]
    except KeyError:
        return default
DictMixin.get = get

def escape2(s):
    qc={'"':'&quot'}
    if not isinstance(s,str) : return "None"
    return escape(s,qc)


def timetosec(timestr):
    """takes a date-time string in the format yyyy/mm/dd hh:mm:ss and
    returns the standard time in seconds since the beginning of time"""
    try: return time.mktime(time.strptime(timestr,"%Y/%m/%d %H:%M:%S"))
    except: return time.mktime(time.strptime(timestr,"%Y/%m/%d"))

def timetostruc(timestr):
    """takes a date-time string in the format yyyy/mm/dd hh:mm:ss and
    returns the standard time in seconds since the beginning of time"""
    try: return time.strptime(timestr,"%Y/%m/%d %H:%M:%S")
    except: return time.strptime(timestr,"%Y/%m/%d")

WEEKREF=(0,31,59,90,120,151,181,212,243,273,304,334)
WEEKREFL=(0,31,60,91,121,152,182,213,244,274,305,335)
def timetoweekstr(timestr):
    """Converts a standard time string to yyyy-ww"""
    y=int(timestr[:4])
    m=int(timestr[5:7])
    d=int(timestr[8:10])
    if y%4==0 :
        d+=WEEKREFL[m-1]
    else:
        d+=WEEKREF[m-1]
    
    return "%s-%02d"%(timestr[:4],int(floor(d/7))+1)

def setdigits(x,n):
    """This will take x and round it up, to contain the nearest value with
the specified number of significant digits. ie 5722,2 -> 5800"""
    scl=10**(floor(log10(x))-n+1)
    return scl*ceil(x/scl)



################################################################<<<XXX>>>########################################################
class DictProxy(object):
    def __init__(self, dct):
        self.dict = dct
    def __getitem__(self, name):
        return self.dict[name]
    def get(self, name, default=None):
        return self.dict.get(name, default)
    def __repr__(self):
        return repr(self.dict)

