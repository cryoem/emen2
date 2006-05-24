from emen2 import Database
from emen2.DBUtil import *
from emen2.emen2config import *
from sets import Set
import os
import pickle

DB=Database
db=DB.Database(EMEN2DBPATH)
ctx=db.login("root",ROOTPW)

project="Project_372"	# synaptotagmin
#project="Project_42"	# GroEL

# we keep track of objects that have already been copied,
# so we don't duplicate a LOT of network traffic
try:
	f=FILE("pathmap.pkl","r")
	pathmap=pickle.load(f)
	f.close()
except:
	pathmap={}

# restore the old binary data objects, since the database
# may have been regenerated since we last ran
try:
	f=FILE("bdobackup.pkl","r")
	binmap=pickle.load(f)
	f.close()
	for i,j in binmap.items:
		db._Database__bdocounter[i]=j
except:
	pass

# We are only copying over data from the GroEL project right now
parent=db.query("find identifier="+project,ctx)["data"][0]

# We're only looking for 'extfile' records with ccd or scan parents
extf=db.getindexbyrecorddef("extfile",ctx)
proj=db.getchildren(parent,ctxid=ctx,recurse=5)

scnccd=db.getindexbyrecorddef("scan",ctx)|db.getindexbyrecorddef("ccd",ctx)

poss=extf&proj
good=Set()
for i in poss:
	a=db.getparents(i,ctxid=ctx)
	for j in a:
		if j in scnccd: good.add(i)

print len(good)," binaries in ",project

for i in good:
	print "Record ",i
	rec=db.getrecord(i,ctx)
	oldpath=rec["path"]
	if oldpath[:4]=="bdo:" : continue
	if oldpath==None :
		print "No path"
		continue
	if pathmap.has_key(oldpath):
		ident=pathmap[oldpath]
		try:
			name,newpath=db.getbinary(ident)
			print "Existing entry: ",name,ident
			rec["path"]="bdo:"+ident
			rec.commit()
		except:
			print "Existing pathmap with no BDO: ",ident,oldpath
	else:
		ident,newpath=db.newbinary(rec["eventdate"],rec["identifier"],ctx)
		pathmap[oldpath]=ident
		print "New entry: ",ident
		print "cp %s %s"%(oldpath,newpath)
		os.system("cp %s %s"%(oldpath,newpath))
		rec["path"]="bdo:"+ident
		rec.commit()

		# see if we need to generate the tile file
		if os.access(newpath+".tile",os.F_OK) : continue

		f=None
		if oldpath[-7:]==".dm3.gz" :
			f="/tmp/file.dm3"
			os.system("gzip -d <%s >/tmp/file.dm3"%oldpath)
		if oldpath[-7:]==".mrc.gz" :
			f="/tmp/file.mrc"
			os.system("gzip -d <%s >/tmp/file.mrc"%oldpath)
		if oldpath[-4:]==".dm3" :
			f="/tmp/file.dm3"
			os.system("cp %s /tmp/file.dm3"%oldpath)
		if oldpath[-4:]==".mrc" :
			f="/tmp/file.mrc"
			os.system("cp %s /tmp/file.mrc"%oldpath)

		if (f) : os.system("e2tilefile.py %s --build=%s"%(newpath+".tile",f)

# dump all current results
binmap={}
for i in db._Database__bdocounter.keys(): binmap[i]=db._Database__bdocounter[i]
f=file("bdobackup.pkl","w")
pickle.dump(binmap,f)
f.close()

f=file("pathmap.pkl","w")
pickle.dump(pathmap,f)
f.close()
