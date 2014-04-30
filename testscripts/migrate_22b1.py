import emen2.db
db = emen2.db.opendb(admin=True)

import datetime
import dateutil
import dateutil.parser
tzutc = dateutil.tz.tzutc()
tzlocal = dateutil.tz.gettz()
default = datetime.datetime(2011, 1, 1)

def parseutc(d):
    try:
        t = dateutil.parser.parse(d, default=default)
    except ValueError, e:
        print "Could not parse:", d, e
        return
    if not t.tzinfo:
        t = t.replace(tzinfo=tzlocal)
    t = t.astimezone(tzutc)
    # print "Converted to UTC       :", t.isoformat(), "\t\t", d    
    return t.isoformat()


with db:
    ctx = db._ctx
    txn = db._txn
    for name, item in db._db['record'].items(ctx=ctx, txn=txn):
        item.__dict__['name'] = unicode(item.__dict__['name'])
        for k in ['parents', 'children']:
            item.__dict__[k] = set(map(unicode, item.__dict__.get(k, [])))        
        db._db['record']._put_data(item.name, item, txn=txn)
        
    for name, item in db._db['binary'].items(ctx=ctx, txn=txn):
        if item.__dict__.get('record') is not None:
            item.__dict__['record'] = unicode(item.__dict__['record'])
        # These dates weren't properly converted by a previous script.
        item.__dict__['creationtime'] = parseutc(item.__dict__['creationtime'])
        item.__dict__['modifytime'] = parseutc(item.__dict__['modifytime'] or item.__dict__['creationtime'])    
        db._db['binary']._put_data(item.name, item, txn=txn)
    
    
    for name, item in db._db['user'].items(ctx=ctx, txn=txn):
        if item.__dict__['record'] is not None:
            item.__dict__['record'] = unicode(item.__dict__['record'])
        db._db['user']._put_data(item.name, item, txn=txn)

    
