import getpass
from emen2 import Database
from emen2.DBUtil import *
from emen2.emen2config2 import *
import os

DB=Database
db=DB.Database(g.EMEN2DBHOME,importmode=1)
ctx=db.login("root",getpass.getpass())
db.restore(ctx)
print db.checkcontext(ctx,None)

