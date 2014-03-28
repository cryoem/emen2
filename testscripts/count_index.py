import time
import collections
            
if __name__ == "__main__":
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument('--keytype', default='record')
    opts.add_argument('--index', action='append')
    args = opts.parse_args()
    
    import emen2.db
    db = emen2.db.opendb(admin=True)
    for index in args.index:
        print "=======", index
        bycount = {}
        with db:
            for k,v in db._db.dbenv['record']._getindex(index)._items(txn=db._txn):
                print k, len(v)
                bycount[k] = len(v)
            
            for k,v in sorted(bycount.items(), key=lambda x:x[1]):
                print "key:", k, "count:", v
        
            