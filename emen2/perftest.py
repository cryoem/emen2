from random import random
import time
from xmlrpclib import *

#s=Server("http://arq2:8080/RPC2")
s=Server("http://localhost:8080/RPC2")
q=s.login("root","foobar")

t0=time.time()
for i in range(10000):
	try: a=s.ping()
	except: pass
t1=time.time()

print "Ping: ",t1-t0, (t1-t0)/10000, 10000/(t1-t0)

t0=time.time()
for i in range(1000):
#	rn=int(random()*250000)
	rn=[int(random()*250000) for i in range(10)]
	try: a=s.getrecords(rn,q,0)
	except: pass
#	print len(str(a))
t1=time.time()

print "10/query:", t1-t0, (t1-t0)/10000, 10000/(t1-t0)

t0=time.time()
for i in range(10000):
	rn=int(random()*250000)
	try: a=s.getrecord(rn,q,0)
	except: pass
#	print len(str(a))
t1=time.time()

print "1/query: ",t1-t0, (t1-t0)/10000, 10000/(t1-t0)
