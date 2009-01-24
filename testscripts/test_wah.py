from test import *

z=db.getindexdictbyvalue("date_occurred",None,ctxid)
y=db.getindexdictbyvalue("creationtime",None,ctxid)
ct=set()
for k,v in z.items():
	if v > "2004/01/01":
		ct.add(k)

#print len(ct)

c=db.getchildren(136,ctxid=ctxid)# & ct
projects=db.groupbyrecorddef(c,ctxid)["project"]
count={}
#gi=db.getindexbyrecorddef("grid_imaging",ctxid)
gi=db.getindexbyrecorddef("ccd",ctxid) | db.getindexbyrecorddef("micrograph",ctxid) 

results={}
hists={}
tc=0
tc2=0

header=["Year / Project"]
for i in projects:

	hist={}
	for year in range(1900,2008+1):
		hist[year]={}
		for month in range(1,12+1):
			hist[year][month]=[]
	
	pc=db.getchildren(i,ctxid=ctxid,recurse=30)
	project_gi=pc & gi #& ct
	
	for j in project_gi:
		try:
			date=z[j].split(" ")[0].split("/")
		except:
			date=y[j].split(" ")[0].split("/")
			
		try:	
			year=int(date[0])
			month=int(date[1])
			#print "date: %s == %s == %s %s"%(j,date,year,month)
			hist[year][month].append(j)
			tc+=1
		except:
			print "pass"

	tc2+=len(project_gi)
	
	hists[i]=hist

	rec=db.getrecord(i,ctxid)
	header.append('"%s (%s) count: %s"'%(rec["name_project"],rec["name_pi"],len(project_gi)))

		
#print hist
print tc

print ",".join(header)

for year in range(2004,2008+1):
	for month in range(1,12+1):
		#print "%s / %s"%(year,month)
		row=['"%s / %s"'%(year,month)]
		for i in projects:
			try:
				row.append('"%s"'%len(hists[i][year][month]))
			except:
				row.append('"0"')

		#print "======================"
		print ",".join(row)