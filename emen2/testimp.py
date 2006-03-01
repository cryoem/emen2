from emen2 import Database
from emen2.DBUtil import *
from emen2.emen2config import *
import os

DB=Database
db=DB.Database(EMEN2DBPATH,importmode=1)
ctx=db.login("root","foobar")
print db.checkcontext(ctx,None)

