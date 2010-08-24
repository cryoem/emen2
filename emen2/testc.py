import getpass

import emen2
import emen2.db.config
parser = emen2.db.config.DBOptions()
parser.parse_args()
g = emen2.db.config.g()

db = emen2.opendb()
db.login("root", getpass.getpass())

# db._starttxn()
# txn = db._gettxn()
ddb = db._DBProxy__db
