import Database
import time

def recordcountbytype(db,ctxid):
	"""Prints a list of the number of records defined for
	every existing RecordDef"""
	names=db.getrecorddefnames()
	for rdn in names:
		print rdn,": ",len(db.getindexbyrecorddef(rdn,ctxid))

def histogramrecdefbydate(db,recdefname,bintime,ctxid):
	"""This will produce a histogram of the times all records
	of  the given RecordDef were added to the database.
	bintime is in seconds. 3600 for hours, 86400 for days"""
	rec=db.getindexbyrecorddef(recdefname,ctxid)
	hist={}
	
	for i in rec:
		r=db.getrecord(i,ctxid)
		t=int((Database.timetosec(r["eventdate"])-time.time())/bintime)
		try: hist[t]=hist[t]+1
		except: hist[t]=1
	
	r=hist.items()
	r.sort()
	return r
	
def histogramrecdefbymonth(db,recdefname,ctxid):
	"""This will produce a histogram of the times all records
	of the given RecordDef were added to the database.
	Time is in months which may contain varying numbers of days"""
	rec=db.getindexbyrecorddef(recdefname,ctxid)
	hist={}
	
	for i in rec:
		r=db.getrecord(i,ctxid)
		d=r["eventdate"]
		t=(int(d[:4])-2000)*12+int(d[5:7])
		try: hist[t]=hist[t]+1
		except: hist[t]=1
	
	r=hist.items()
	r.sort()
	return r
	
def histogramrecdefbyuser(db,recdefname,ctxid):
	"""This will produce a histogram of the times all records
	of the given RecordDef were added to the database.
	Time is in months which may contain varying numbers of days"""
	rec=db.getindexbyrecorddef(recdefname,ctxid)
	hist={}
	
	for i in rec:
		r=db.getrecord(i,ctxid)
		u=r["inputuser"]
		try: hist[u]=hist[u]+1
		except: hist[u]=1
	
	r=hist.items()
	r.sort()
	return r
	