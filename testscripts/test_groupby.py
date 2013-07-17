import re
import collections
import emen2.db
db = emen2.db.opendb(admin=True)

# db.groupby([['rectype','==','project*']])
db.groupby([['project_investigators', 'any']]) # , subset=['455434']