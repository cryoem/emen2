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
from emen2.subsystems import macro #
from functools import partial
from xml.sax.saxutils import escape, unescape, quoteattr
import atexit
import operator
import os
import re
import hashlib
import sys
import traceback



Set = set

from btrees import *
from datastorage import *
from user import *
from database import * 

    


def get(self, key, default=None):
    try:
        return self[key]
    except KeyError:
        return default
DictMixin.get = get

def DB_cleanup():
    """This does at_exit cleanup. It would be nice if this were always called, but if python is killed
    with a signal, it isn't. This tries to nicely close everything in the database so no recovery is
    necessary at the next restart"""
    sys.stdout.flush()
    print >>sys.stderr, "Closing %d BDB databases"%(len(BTree.alltrees)+len(IntBTree.alltrees)+len(FieldBTree.alltrees))
    if DEBUG>2: print >>sys.stderr, len(BTree.alltrees), 'BTrees'
    for i in BTree.alltrees.keys():
        if DEBUG>2: sys.stderr.write('closing %s\n' % str(i))
        i.close()
        if DEBUG>2: sys.stderr.write('%s closed\n' % str(i))
    if DEBUG>2: print >>sys.stderr, '\n', len(IntBTree.alltrees), 'IntBTrees'
    for i in IntBTree.alltrees.keys():
        i.close()
        if DEBUG>2: sys.stderr.write('.')
    if DEBUG>2: print >>sys.stderr, '\n', len(FieldBTree.alltrees), 'FieldBTrees'
    for i in FieldBTree.alltrees.keys():
        i.close()
        if DEBUG>2: sys.stderr.write('.')
    if DEBUG>2: sys.stderr.write('\n')
# This rmakes sure the database gets closed properly at exit
atexit.register(DB_cleanup)


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



# vartypes is a dictionary of valid data type names keying a tuple
# with an indexing type and a validation/normalization
# function for each. Currently the validation functions are fairly stupid.
# some types aren't currently indexed, but should be eventually







                            
        

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



#    #@write,private
#    def __validaterecordaddchoices(self,record,ctxid,host=None):
#        """add options for extensible paramdef choices."""
#        
#        for i in record.keys():
#            pd=self.__paramdefs[i.lower()]
#            # if string/choices, add option. if choices/choices, raise exception (invalid value)
#            if pd.vartype=="string" and isinstance(pd.choices,tuple):
#                if record[i].title() not in pd.choices:
#                    # ian: fixed a typo that seemed to be causing lots of grief (record[i].ctxid). it was missed because of exception handler.
#                    self.addparamchoice(i,record[i],ctxid)
