import getpass

import emen2.globalns
from emen2.config.config import g, DBOptions

parser = DBOptions()
parser.parse_args()

import emen2.Database.database

# Open DB Env
ddb = emen2.Database.database.DB()

txn = ddb.newtxn()

ddb.create_db(txn=txn)

txn.commit()