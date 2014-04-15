"""Various helper functions for sorting, filtering, transforming data, etc."""
import uuid
import time
import math
import os
import collections
import itertools
from UserDict import DictMixin
from functools import partial
            
# There are 12219292800000 ms between the UUID epoch and UNIX epoch.
EPOCH_OFFSET = 0x0b1d069b5400
def timeuuid(t=None):
    """This function returns a modified version 4 UUID. 
    The first 48 bits are the number of miliseconds
    since 1582-10-15 00:00:00.
    """
    t = (t or time.time()) * 1000.0 + EPOCH_OFFSET
    r = '%012x'%t + '%02x'*10%tuple(map(ord, os.urandom(10)))
    # Convert to an int
    return uuid.UUID(int=int(r, 16), version=4).hex

def untimeuuid(timestamp):
    return (int(timestamp[0:12], 16) - EPOCH_OFFSET) / 1000.0
            
# Temporary fix --
import jsonrpc.jsonutil
def jsonencode(*args, **kwargs):
    """Safer JSON encoding."""
    return jsonrpc.jsonutil.encode(*args, **kwargs).replace('/', r'\/')

filter_none = lambda x:x or x==0
def check_iterable(value):
    """Check if a value is iterable; if not, return [value]. Removes None values."""
    if not hasattr(value,"__iter__"):
        value = [value]
    return filter(filter_none, value)

def typepartition(names, *types):
    """Partition objects by type.
    
    >>> typepartition([1,'a'], int, str)
    [[1], ['a']]
    """
    ret = collections.defaultdict(list)
    other = list()
    for name in names:
        found = False
        for t in types:
            if isinstance(name, t):
                found = True
                ret[t].append(name)
        if not found:
            other.append(name)

    return [ret.get(t, []) for t in types]+[other]

def dictbykey(l, key='name'):
    """Take a list of items, return a dict keyed by the specified key."""
    return dict((i.get(key), i) for i in l)

def test():
    print "Ten IDs:"
    for i in range(10):
        print timeuuid()

    # Check that the current time can be converted.
    now = time.time()
    tnow = timeuuid(now)
    t = untime(tnow)
    print "Now?               ", tnow, t, time.gmtime(t)
    assert math.fabs(t - now) < 0.001

    # Check the beginning of time.
    begin = '0'*12
    t = untime(begin)
    print "Beginning of time? ", begin, t, time.gmtime(t)
    assert t == EPOCH_OFFSET / -1000
    assert list(time.gmtime(t))[:6] == [1582, 10, 15, 0, 0, 0]

    # Check the end of time
    end = 'f'*12
    t = untime(end)
    print "End of time?       ", end, t, time.gmtime(t)
    assert list(time.gmtime(t))[:6] == [10502, 5, 17, 5, 31, 50]

    # Check UNIX epoch.
    offset = '%012x'%EPOCH_OFFSET
    t = untime(offset)
    print "UNIX Epoch?        ", offset, t, time.gmtime(t)
    assert t == 0.0
    
