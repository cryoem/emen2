# $Id: fix_paramdefs.py,v 1.10 2012/07/28 06:31:19 irees Exp $
raise Exception, "Needs to be updated"

from test import *

vp = valid_properties
rvp = {}
for k,v in vp.items():
    for i in v[1]:
        rvp[i]=k
    for i in v[2]:
        rvp[i]=k

rvp[None]="none"
rvp[""]="empty"
#print rvp

import jsonrpc.jsonutil
jsvp = {}
for k,v in vp.items():
    jsvp[k]=[v[0],v[1].keys()]
print jsonrpc.jsonutil.encode(jsvp)



#import sys
#sys.exit(0)

for i in db.getparamdefnames():
     z=db.getparamdef(i)
     if z.defaultunits != None and z.defaultunits != "":
        try:
            if rvp[z.defaultunits] != z.property:
                print "Need to fix: %s"%z.name
                print "\tdu: %s\n\tprop: %s -> %s"%(z.defaultunits, z.property, rvp[z.defaultunits])
                z.property=rvp[z.defaultunits]
                db.putparamdef(z)

        except:
            print "wtf %s, %s"%(z.name, z.defaultunits)


__version__ = "$Revision: 1.10 $".split(":")[1][:-1].strip()
