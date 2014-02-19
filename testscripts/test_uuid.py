import uuid
import time
import math
import os

# There are 12219292800000 ms between the UUID epoch and UNIX epoch.
EPOCH_OFFSET = 0x0b1d069b5400

def timeuuid(t=None):
    t = (t or time.time()) * 1000.0 + EPOCH_OFFSET
    return '%012x'%t

def untime(timestamp):
    return (int(timestamp[0:12], 16) - EPOCH_OFFSET) / 1000.0


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


if __name__ == "__main__":
    test()