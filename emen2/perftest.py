from random import random
import time
from xmlrpclib import *

s=Server("http://arq2:8080/RPC2")
q=s.login("root","foobar")

t0=time.time()
for i in range(10000):
	rn=int(random()*250000)
	try: a=s.getrecord(rn,q,0)
	except: pass
t1=time.time()

print t1-t0, (t1-t0)/10000, 10000/(t1-t0)
