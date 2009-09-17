from test import *

# a=db.query(constraints=[["name_project","contains","Nano"]], ignorecase=True, childof=136)
# print a
# a=db.getrecord(a)
# for i in a:
# 	print i["name_project"]

val = "Wa"


#print ctx
recs = None
#recs = db.getrecord(range(270390,272390), filt=False)
#print recs

for i in range(10):
	print "go!"
	q = db.query(
		boolmode="OR",
		recs = recs,
		constraints=[
			["name_last", "contains", val]
			],
		returnrecs=True
		)


print q



	#	["name_first","contains",val], 
	#	["name_middle","contains",val],
	#	["name_last","contains",val],
	#	["username","contains",val]