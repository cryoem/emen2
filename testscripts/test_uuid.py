import uuid
import time
import math
import os

def timeuuid():
    # Modified UUID4 where first 48 bits represent time, seconds since unix epoch.
    # The remainder are the UUID version bits and random data.
    randbytes = 10
    a, b = math.modf(time.time())
    r = tuple(map(ord, os.urandom(randbytes)))
    return "%08x-%04x"%(b, a*2**16) + ("%02x-"*randbytes)%r

    
for i in range(100):
    print timeuuid()