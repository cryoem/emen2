# $Id$

import emen2.clients
db = emen2.clients.opendb(name=None)

print db.getrecord(0)

__version__ = "$Revision$".split(":")[1][:-1].strip()
