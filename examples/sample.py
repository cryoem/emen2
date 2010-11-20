# $Id$
#!/bin/env python
# This is an XMLRPC test script which can be customized for a variety of simple tasks
# call it as sample.py <username>

import sys
import emen2.clients.emen2client

db = emen2.clients.opendb(username=sys.argv[1])

#print db.getrecord(0)

# Example 1 - query new subprojects by date
def subprojbydate(db):
	pass

def histogram():
	pass

__version__ = "$Revision$".split(":")[1][:-1].strip()
