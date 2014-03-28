rm -rf $EMEN2DBHOME
python -m emen2.db.create --debug --rootpw=abcd1234
python -m emen2.db.load --debug emen2/db/base.json emen2/exts/em/json/em.json ~/Dropbox/src/ext_ncmi/json/ncmi.json
python -m emen2.db.load --debug ~/data/import/user.json ~/data/import/group.json 
python -m emen2.db.load --debug --set validation.allow_invalid_choice=True --set validation.allow_invalid_reference=True --set record.sequence=False --keytype=record ~/data/import/record.json
