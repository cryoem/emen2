# This script parses Database.py and updates the function definitions in TwistSupport.py

a=file("Database.py","r")
dblines=a.readlines()
a.close()

a=file("TwistSupport.py","r")
tslines=a.readlines()
a.close()

for i,j in enumerate(dblines):
	if "class Database" in j: break
	
dbdefs=[j[5:-1] for j in dblines[i:] if j[1:5]=="def " and j[5:7]!='__']

# now find each function in Database.py within TwistSupport
# add or modify as necessary
for i in dbdefs:
	fn='_'+i.split('(')[0]+'('		# function name
	
	for j,k in enumerate(tslines):
		if fn in k:
			if (i.split('(')[1])!=(k.split('(')[1][:-1]) :
#				print "'"+i.split('(')[1]+"'\n'"+k.split('(')[1][:-1]+"'"
				tslines[j]="#"+tslines[j]+"\tdef xmlrpc_"+i+"\n"
			break
	else:
		tslines.append("\tdef xmlrpc_"+i+"\n")

a=file("x.py","w")
for i in tslines: a.write(i)
a.close()
