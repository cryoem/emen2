# ts.py  Steven Ludtke  06/2004
# This module provides the resources needed for HTTP and XMLRPC servers using Twist
# Note that the login methods return a ctxid (context id). This id is required
# by most of the other database calls for determining permissions. Context ids
# have a limited lifespan

#from twisted.web.resource import Resource
from emen2 import Database
#from twisted.web import xmlrpc
#import xmlrpclib
#import os
#from sets import Set
from emen2.emen2config import *

# we open the database as part of the module initialization
db=None
DB=Database 

def startup(path):
	global db
	db=Database.Database(EMEN2DBPATH)
	

