import emen2.db
db = emen2.db.opendb(admin=True)
with db:
    db._db.dbenv.log_archive()