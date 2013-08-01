import collections
import emen2.db
db = emen2.db.opendb(admin=True)
counts = {}

rds = db.recorddef.filter()
for rd in rds:
    print "...", rd
    allrd = db.record.findbyrectype(rd)
    children = db.rel.children(allrd)
    red = set()
    for k,v in children.items():
        red |= v
    groups = db.record.groupbyrectype(red)
    groups2 = {}
    for k,v in groups.items():
        groups2[k] = len(v)
    counts[rd] = groups2


print "\n\n============\n\n"

for k,v in counts.items():
    print "\n",k
    for k2,v2 in sorted(v.items(), key=lambda x:x[1], reverse=True):
        print "\t", k2, v2

