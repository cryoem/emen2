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

print t1-t0, (t1-t0)/10000, 10000/(t1-t0)
