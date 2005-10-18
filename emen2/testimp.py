# This opens the database in the special 'import' mode
import Database
from DBUtil import *
import os

DB=Database
db=DB.Database(os.getenv("HOME")+"/db",importmode=1)
ctx=db.login("root","foobar")
print db.checkcontext(ctx,None)

