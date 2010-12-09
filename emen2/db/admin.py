# $Id$

import pickle
import imp
import sys
import time
import getpass
import pickle


import emen2
import emen2.db.config

# Provide quick access to an admin context in a local console.
# At the local console level, we have to rely on UNIX permissions to keep the db and files safe -- this doesn't provide any capabilities that a user could not acquire for themselves if they have read/write permissions to the actual db files. Any user with that level of access could recreate the script below on their own and run it just as easily. EMEN2 can only provide real security if it is accessed through the network RPC -- XMLRPC or JSON-RPC -- which does not allow arbitrary contexts to be created, or database files to be written to directly.

def opendb(args=None):
	if args:
		parser = emen2.db.config.DBOptions()
		(options, args) = parser.parse_args()
	db = emen2.opendb()
	ctx = db._DBProxy__db._makerootcontext()
	db._DBProxy__ctx = ctx
	return db
	
	
if __name__ == "__main__":
	db = opendb()	
	
__version__ = "$Revision$".split(":")[1][:-1].strip()
