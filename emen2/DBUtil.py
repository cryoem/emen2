import Database
import time

def recordcountbytype(db,ctxid):
	"""Prints a list of the number of records defined for
	every existing RecordDef"""
	names=db.getrecorddefnames()
	for rdn in names:
		print rdn,": ",len(db.getindexbyrecorddef(rdn,ctxid))

def histogrambydate(db,reclist,bintime,ctxid):
	"""This will produce a histogram of the times all records
	in the passed list of ids were added to the database.
	bintime is in seconds. 3600 for hours, 86400 for days"""
	hist={}
	
	for i in reclist:
		r=db.getrecord(i,ctxid)
		t=int((Database.timetosec(r["eventdate"])-time.time())/bintime)
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
	
	for i in reclist:
		r=db.getrecord(i,ctxid)
		d=r["eventdate"]
		t=(int(d[:4])-2000)*12+int(d[5:7])
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
	
