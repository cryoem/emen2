from random import random
from time import time
from xmlrpclib import *

s=Server("http://arq2:8080/RPC2")
q=s.login("root","foobar")

t0=time()
for i in range 100000:
	rn=int(random()*250000)
	a=s.getrecord(rn,q,0)
t1=time()

print t1-t0, (t1-t0)/100000, 100000/(t1-t0)
