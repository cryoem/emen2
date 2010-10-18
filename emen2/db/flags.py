# $Id$
import operator
from bsddb3.db import *

import emen2.db.config
g = emen2.db.config.g()


envopenflags = [
	DB_CREATE,
	DB_THREAD,
	DB_INIT_MPOOL,
	DB_INIT_TXN,
	DB_INIT_LOCK,
	DB_INIT_LOG,
	DB_REGISTER,
	DB_TXN_SNAPSHOT,
	DB_MULTIVERSION
	#DB_RECOVER
	# DB_FAILCHK # ian: todo: doesn't seem to be in bsddb3
]

dbopenflags = [
	DB_CREATE,
	DB_THREAD,
	DB_AUTO_COMMIT,
	DB_MULTIVERSION
]

txnflags = [DB_TXN_SNAPSHOT]

rmwflags = [DB_RMW]


with g as _g:
	_g.ENVOPENFLAGS = reduce(operator.__or__, envopenflags, 0)
	_g.DBOPENFLAGS = reduce(operator.__or__, dbopenflags, 0)
	_g.TXNFLAGS = reduce(operator.__or__, txnflags, 0)
	_g.RMWFLAGS = reduce(operator.__or__, rmwflags, 0)
__version__ = "$Revision$".split(":")[1][:-1].strip()
