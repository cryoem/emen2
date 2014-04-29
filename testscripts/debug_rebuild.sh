python -m emen2.db.create --debug --rootpw=asdf1234

python -m emen2.db.load --debug \
    ~/src/emen2/emen2/db/base.json \
    ~/src/emen2/emen2/exts/em/json/em.json \
    ~/src/ext_ncmi/json/ncmi.json

python -m emen2.db.load --debug \
    --set validation.allow_invalid_email=true \
    ~/data/import/json/user.json \
    ~/data/import/json/group.json 

python -m emen2.db.load --debug \
    --set validation.allow_invalid_email=true \
    --set validation.allow_invalid_choice=true \
    --set validation.allow_invalid_reference=true \
    --set record.sequence=false \
    --update_record_max \
    --keytype=record \
    ~/data/import/json/record.json
