from test import *

projects=[195071, 240869, 186968, 258436 ,260078 ,105022 ,259594 ,84317 ,106652 ,297072 ,237383 ,269593 ,256542 ,192882,82702,199092,259506,256541,259392,198821,255427,322277,260113,287850,299528,236924,272587,255771,250454,269669,257677,296114,256776,287776,311576,258435,248191,247193,234986,241449,294760,276545,175742,200425,237235,241129,259080,259579,297657,280710,253807]
#projects=[0]

from sets import Set


minyear=2004

z=db.getindexdictbyvalue("date_occurred",None,ctxid)
y=db.getindexdictbyvalue("creationtime",None,ctxid)

# ct = all recs 2004+
#ct=Set()
#for k,v in y.items():
#	if v > "%s/01/01"%minyear:
#		ct.add(k)

#print "len(ct)"
#print len(ct)
#c=db.getchildren(136,ctxid=ctxid)# & ct
#projects=db.groupbyrecorddef(c,ctxid)["project"]

type="gis"
typename="count"

# gis = grid imaging sessions
if type=="gis":
	gi=db.getindexbyrecorddef("grid_imaging",ctxid)
	typename="Grid Imaging Sessions"
# gi = all image types
elif type=="gi":
	gi=db.getindexbyrecorddef("ccd",ctxid) | db.getindexbyrecorddef("micrograph",ctxid) 
	typename="Images (CCD+Micrograph)"
elif type=="all":
	gi=db.getrecordnames(ctxid)
	typename="NCMIDB Total Records"

#gis &= ct
#gi &= ct

#print "len(gi)"
#print len(gi)

ptype={}
count={}
header={}
results={}
hists={}
tc=0
tc2=0
tc3=0
tcc={}

for i in projects:

	tc=0
	hist={}

	pc=db.getchildren(i,ctxid=ctxid,recurse=50)
	#print "children %s = %s"%(i,len(pc))
	tc3+=len(pc)
	project_gi=pc & gi #& ct
	#project_gis=pc & gi & ct
	
	#project_gis=pc & gis
	
	for j in project_gi:
		try:
			date=z[j].split(" ")[0].split("/")
		except:
			date=y[j].split(" ")[0].split("/")
			
		try:
			year=int(date[0])
			month=int(date[1])
		except:
			year=0
			month=1	

		if not hist.has_key(year):
			hist[year]={}
			for month in range(1,12+1):
				hist[year][month]=[]
		
		if year >= minyear:
			tc += 1	

		try:
			hist[year][month].append(j)
		except:
			print "Invalid year/month: %s/%s"%(year,month)
	#print hist.keys()
	
	hists[i]=hist
	tcc[i]=tc
	
	
	rec=db.getrecord(i,ctxid)
	header[i]='%s (%s)'%(rec["name_project"],rec["name_pi"])
	#header[i]="Test"
	if not ptype.has_key(rec["project_type"]): ptype[rec["project_type"]]=Set()
	ptype[rec["project_type"]].add(i)


# sv=[]
# for k,v in hists.items():
# 	try:
# 		c=len(reduce(operator.add, reduce(operator.add, [i.values() for i in v.values()])))
# 		sv.append((k,c))
# 	except:
# 		sv.append((k,0))


import operator
sl=[j[0] for j in sorted(tcc.items(), key=operator.itemgetter(1), reverse=1)]


print "\n\n\n"
print '"%s by Project Type"'%(typename)
print "\n"


for k,v in ptype.items():
	print '\n"Project Type: %s"'%k
	for z in sorted([(i,tcc[i]) for i in v], key=operator.itemgetter(1), reverse=1):
		print '"%s","%s"'%(header[z[0]], tcc[z[0]])


print "\n\n\n"
print '"%s by Project / Date"'%(typename)
print "\n"


h=['"date"']
for p in sl:
	h.append('"%s"'%header[p])
print ",".join(h)
	
for year in range(minyear, 2008+1):
	for month in range(1, 12+1):
		row=['"%s/%s"'%(year, month)]
		for i in sl:
			try:
				row.append('"%s"'%(len(hists[i][year][month])))
			except:
				row.append('"0"')
		print ",".join(row)
		
f=['"total"']
for p in sl:
	f.append('"%s"'%tcc[p])
print ",".join(f)
		
		
		
print "\n\n\n"