# This script prepares core paramdefs, recorddefs, users, and groups for distribution.
# It writes output JSON output files


from emen2.testc import *

import emen2.util.jsonutil

recorddefs = set(['core'])
paramdefs = set(['core'])


recorddefs |= db.getchildren('core', keytype='recorddef')
rds = []
for rd in db.getrecorddef(recorddefs):
	children = db.getchildren(rd.name, keytype='recorddef') & recorddefs
	paramdefs |= rd.paramsK
	rd = dict(rd)
	rd['children'] = children
	rds.append(rd)



paramdefs |= db.getchildren('core', keytype='paramdef')
pds = []
for pd in db.getparamdef(paramdefs):
	children = db.getchildren(pd.name, keytype='paramdef') & paramdefs
	if pd.name == "core": children |= (paramdefs-set(['core']))
	pd = dict(pd)
	pd['children'] = children
	pds.append(pd)





users = [
	{'username':'root', 'signupinfo':{'name_first':'Admin'}}
	]



groups = [
	{"name":"admin", "displayname": "Administrators", "permissions":[[],[],[],['root']]},
	{"name":"readadmin", "displayname": "Read-only Administrators"},
	{"name":"create", "displayname": "Record Creation Priveleges"},
	{"name":"anon", "displayname": "Anonymous Access"},
	{"name":"authenticated", "displayname": "Authenticated Users"},
	{"name":"publish", "displayname": "Published Data"}
	]


def write(filename, d):
	ret = emen2.util.jsonutil.encode(d, escape_unicode=True)
	f = open(filename, 'w')
	f.write(ret)
	f.close()


write('paramdefs.json', pds)
write('recorddefs.json', rds)
write('users.json', users)
write('groups.json', groups)


