# This script prepares core paramdefs, recorddefs, users, and groups for distribution.
# It writes output JSON output files


from emen2.testc import *

import emen2.util.jsonutil

recorddefs = set(['core'])
paramdefs = set(['core'])


recorddefs |= db.getchildren('core', keytype='recorddef')
rds = db.getrecorddef(recorddefs)
for rd in rds:
	rd.children = db.getchildren(rd.name, keytype='recorddef') & recorddefs
	paramdefs |= rd.paramsK



paramdefs |= db.getchildren('core', keytype='paramdef')
pds = db.getparamdef(paramdefs)
for pd in pds:
	pd.children = db.getchildren(pd.name, keytype='paramdef') & paramdefs
	if pd.name == "core": pd.children |= (paramdefs-set(['core']))



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


