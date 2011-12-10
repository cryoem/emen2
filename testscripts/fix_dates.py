import datetime

import emen2.db
db = emen2.db.opendb(admin=True)

TIMESTR = ['%Y/%m/%d %H:%M:%S', '%Y/%m/%d', '%Y']
def parse(d, tz='Z'):
	p = None
	for t in TIMESTR:
		try:
			p = datetime.datetime.strptime(d, t)
		except Exception, e:
			pass
		if p:
			return p.isoformat()+tz
	if not p:
		print "Could not parse:", d
	return d
	

print "Test:"
print parse('2009')
print parse('2009/01/01')
print parse('2009/01/01 02:03:04')

t = []
t.append(parse('2009/01/01 02:03:01'))
t.append(parse('2009/01/01 02:03:02'))
t.append(parse('2009/01/01 02:03:03', tz='-06:00'))
t.append(parse('2009/01/01 02:03:04', tz='-06:00'))
t.append(parse('2009/01/01 02:03:05'))

print sorted(t)

import sys
sys.exit(0)

		
with db:
	
	pds = set(db.query([['vartype','==','datetime']], keytype='paramdef', count=0)['names'])
	pds -= set(['creationtime', 'modifytime'])
	print pds
	
	
	ctx = db._ctx
	txn = db._txn
	#for name in db._db.bdbs.record.keys(txn=txn): 
	for name in range(1000):
		print name
		rec = db.getrecord(name)
		if not rec:
			continue
			
		ct = rec.__dict__['creationtime']
		rec.__dict__['creationtime'] = parse(ct)
		rec.__dict__['modifytime'] = parse(rec.get('modifytime') or ct)

		newcomments = []
		for i in rec.__dict__['comments']:
			newcomments.append([i[0], parse(i[1]), i[2]])
		rec.__dict__['comments'] = newcomments
		
		newhistory = []
		for i in rec.__dict__['history']:
			newhistory.append([i[0], parse(i[1]), i[2], i[3]])
		rec.__dict__['history'] = newhistory
		
		for p in pds:
			if rec.params.get(p):
				rec.params[p] = parse(rec.params[p])
				

		