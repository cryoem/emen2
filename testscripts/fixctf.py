import emen2.db.admin
db = emen2.db.admin.opendb()

import collections
dates = collections.defaultdict(set)

recs = db.getrecord(db.getindexdictbyvalue('ctf_bfactor').keys())
for rec in recs:
	for hi in rec.get('history', []) + rec.get('comments', []):
		if hi[2] == 'ctf_bfactor' or hi[2].startswith('LOG: ctf_bfactor'):
			dates[hi[1][:7]].add(rec.recid)
			
for k,v in sorted(dates.items()):
	print k, len(v)
	
for i in ret:
	db.pclink(464552, i)	
	
for i in set(a.keys()) - ret:
	db.pclink(464553, i)	
	
db._committxn()