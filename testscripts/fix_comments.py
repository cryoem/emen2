import re
import collections
import emen2.db
db = emen2.db.opendb()
block = 1000000
count = 0

finder_sig = re.compile('LOG: \$\$(\w+) .+: (.*)')
finder_old = re.compile('LOG: (\w+) .+: (.*)')

#with db:
db._starttxn()

ctx = db._getctx()
txn = db._gettxn()
b = []
for i in range(count, count+block):
    rec = db._db.dbenv["record"]._get_data(i, txn=txn)
    if not rec:
        break

    creationtime = rec['creationtime']
    creator = rec['creator']
    performed_by = rec.get('performed_by', creator)
    if creator == 'root' and creator != performed_by:
        rec.__dict__['creator'] = performed_by
        
    history = rec.history[:]
    comments = rec.comments[:]    
    
    newcomments = []
    for comment in comments:
        if comment[2].startswith('LOG'):
            param, value = None, None
            sig = finder_sig.match(comment[2])
            if sig:
                param, value = sig.groups()
            sig = finder_old.match(comment[2])
            if sig:
                 param, value = sig.groups()
        
            if param:
                try:
                    value = eval(value)
                except:
                    pass

            # print "Building history.."
            item = [comment[0], comment[1], param, value]
            history.append(item)
        else:
            newcomments.append(comment)
            
    
    if rec.get('comments_text'):
        item = [creator, creationtime, rec.get('comments_text')]
        print rec.name, rec.get('comments_text')
        del rec.params['comments_text']
        comments.append(item)


    # print "Sorting comments and history"
    rec.__dict__['comments'] = sorted(newcomments, key=lambda x:x[1])
    rec.__dict__['history'] = sorted(history, key=lambda x:x[1])        
    # print rec.__dict__['comments']

    db._db.dbenv["record"]._put(rec.name, rec, txn=txn)

db._committxn()