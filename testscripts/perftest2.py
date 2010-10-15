# $Id$
from random import random
import time
from test import *

q=db.login("root","foobar")

t0=time.time()
for i in range(10000):
	rn=int(random()*250000)
	try: a=db.getrecord(rn,q)
	except: pass
t1=time.time()

print "10000 random reads from 250000", t1-t0, (t1-t0)/10000, 10000/(t1-t0)

t0=time.time()
for i in range(10000):
	rn=int(random()*10000)
	try: a=db.getrecord(rn,q)
	except: pass
t1=time.time()

print "10000 random reads from 10000",t1-t0, (t1-t0)/10000, 10000/(t1-t0)

t0=time.time()
for i in range(10000):
	rn=i+10000
	try: a=db.getrecord(rn,q)
	except: pass
t1=time.time()

print "10000 sequential reads from 10000",t1-t0, (t1-t0)/10000, 10000/(t1-t0)
__version__ = "$Revision$".split(":")[1][:-1].strip()
