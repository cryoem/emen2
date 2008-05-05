from emen2 import Database
from emen2.DBUtil import *
from emen2.emen2config import *
from sets import Set
import os
import pickle

DB=Database
db=DB.Database(EMEN2DBPATH)
ctx=db.login("root",ROOTPW)

# list of tuples describing all binary object keys
bin=db.getbinarynames(ctx)
print len(bin)

for i in bin:
	for j in range(i[1]):
		key=i[0]+"%05X"%j
		try:
			name,path=db.getbinary(key,ctx)
		except:
			print "Id %s not found !!!"%key
			continue
		
		# see if we need to generate the tile file
		if os.access(path+".tile",os.F_OK) : 
			print path
			continue

		print "New tile file: %s.tile"%path
		f=None
		if name[-7:]==".dm3.gz" :
			f="/tmp/file.dm3"
			os.system("gzip -d <%s >/tmp/file.dm3"%path)
		if name[-7:]==".mrc.gz" :
			f="/tmp/file.mrc"
			os.system("gzip -d <%s >/tmp/file.mrc"%path)
		if name[-4:]==".dm3" :
			f="/tmp/file.dm3"
			os.system("cp %s /tmp/file.dm3"%path)
		if name[-4:]==".mrc" :
			f="/tmp/file.mrc"
			os.system("cp %s /tmp/file.mrc"%path)

		if (f) : os.system("e2tilefile.py %s --build=%s"%(path+".tile",f))


