import inspect
import time
import collections
import emen2.db
db = emen2.db.opendb(admin=True)

for k,v in sorted(db._publicmethods.items()):
    print "======== %s ========"%k
    args = inspect.getargspec(v)
    print "Method arguments:"
    for a,d in zip(args.args, args.defaults or []):
        if a in ['self', 'ctx', 'txn']:
            continue
        if d:
            print "\t", a.ljust(20), "Default:", d
        else:
            print "\t", a


    print
    print v.__doc__
    print "\n\n\n"