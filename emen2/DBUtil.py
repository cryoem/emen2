from emen2 import Database
import time
import os

def doplot(data):
	out=file("outfile","w")
	for i in data: out.write("%f\t%f\n"%(i[0],i[1]))
	out.close()
	os.system("xmgrace outfile")

def dumpfile(data,fsp):
	out=file(fsp,"w")
	for i in data: out.write("%f\t%f\n"%(i[0],i[1]))
	out.close()
	
def recordcountbytype(db,ctxid):
	"""Prints a list of the number of records defined for
	every existing RecordDef"""
	names=db.getrecorddefnames()
	for rdn in names:
		print rdn,": ",len(db.getindexbyrecorddef(rdn,ctxid))

def histogramvalues(vals,mn,mx,bins,sep0,sepmax):
	"""This will histogram a list of numbers. If sep0 is true
	it will make a special bin for 0. If sepmax is true, it 
	will make a special bin for values >max"""

	n0=0
	nmax=0
	n=[0]*bins
	bw=(mx-mn)/(float(bins))

	for i in vals:
		if i==0 : n0+=1
		if i>mx : nmax+=1
		b=(i-mn)/bw
		try: n[b]+=1
		except: pass

	if sep0 : ret=[("0",n0)]
	else: ret=[]

	if mn==floor(mn) and bw==floor(bw) :
		for i,j in enumerate(n):
			ret.append(("%d-%d"%(mn+i*bw,mn+i*bw+bw)),j)
		ret.append(">%d"%mx,nmax)
	else:
		for i,j in enumerate(n):
			ret.append(("%1.2g-%1.2g"%(mn+i*bw,mn+i*bw+bw)),j)
		ret.append(">%1.2g"%mx,nmax)

	return ret

def histogramtext(hist):
	"""This will display a list of (string,int) tuples as a text histogram plot"""
	max=0
	maxl=0
	for i in hist:
		if i[1]>max : max=i[1]
		if len(i[0])+1>maxl : maxl=len(i[0])+1

	for i in range(16):
		print " "*(maxl/2),
		for j,k in enumerate(hist):
			if k>(16-i)*max/16 : print "*",
			else: print " "
			print " "*(maxl/2),
		print " "

	for k in hist:
		print k[0]+" "

def histogrambydate(db,reclist,bintime,ctxid):
	"""This will produce a histogram of the times all records
	in the passed list of ids were added to the database.
	bintime is in seconds. 3600 for hours, 86400 for days"""
	hist={}
	
	curtime=time.time()
	times=db.getrecordschangetime(reclist,ctxid)
	for i in times:
		t=int((Database.timetosec(i)-curtime)/bintime)
		try: hist[t]=hist[t]+1
		except: hist[t]=1
	
	r=hist.items()
	r.sort()
	return r
	
def histogrambymonth(db,reclist,ctxid):
	"""This will produce a histogram of the times all records
	in the passed list of ids were added to the database.
	Time is in months which may contain varying numbers of days"""
	hist={}
	
	times=db.getrecordschangetime(reclist,ctxid)
	
	curtime=time.localtime()
	year=curtime[0]
	month=curtime[1]
	
	for d in times:
		try:
			t=(int(d[:4])-year)*12+int(d[5:7])-month
		except: continue
		try: hist[t]=hist[t]+1
		except: hist[t]=1
	
	r=hist.items()
	r.sort()
	return r
	
def histogrambystring(db,reclist,param,ctxid):
	"""This will produce a histogram of the provided parameter name
	for all records in the provided list.
	Time is in months which may contain varying numbers of days"""
	hist={}
	
	for i in reclist:
		r=db.getrecord(i,ctxid)
		try: u=r[param]
		except: pass
		try: hist[u]=hist[u]+1
		except: hist[u]=1
	
	r=hist.items()
	r.sort()
	return r
	
def histogrambyvalue(db,reclist,param,binsize,ctxid):
	"""This will produce a histogram of the provided parameter name
	for all records in the provided list using the supplied bin size.
	Time is in months which may contain varying numbers of days"""
	hist={}
	
	for i in reclist:
		r=db.getrecord(i,ctxid)
		try: u=int(r[param]/binsize)
		except: pass
		try: hist[u]=hist[u]+1
		except: hist[u]=1
	
	r=hist.items()
	r.sort()
	return r
	
def splitbystring(db,reclist,param,ctxid):
	"""This will generate a dictionary of lists of recids
	split using the value of the provided parameter name
	for all records in the provided list.
	Time is in months which may contain varying numbers of days"""
	hist={}
	
	for i in reclist:
		r=db.getrecord(i,ctxid)
		try: u=r[param]
		except: pass
		try: hist[u].append(i)
		except: hist[u]=[i]
	
	return hist
	
