rm -rf $EMEN2DBHOME
python -m emen2.db.create --rootpw=abcd1234
python -m emen2.db.load emen2/db/base.json emen2/exts/em/json/em.json ~/Dropbox/src/ext_ncmi/json/ncmi.json
python -m emen2.db.load ~/data/import/user.json ~/data/import/group.json 

