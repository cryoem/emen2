import emen2.globalns
g = emen2.globalns.GlobalNamespace()
import bsddb3

USETXN = True
g.USETXN = True
RECOVER = True
g.RECOVER = True

# Berkeley DB Config flags
ENVOPENFLAGS = bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD | bsddb3.db.DB_INIT_MPOOL | bsddb3.db.DB_REGISTER
g.ENVOPENFLAGS = bsddb3.db.DB_CREATE | bsddb3.db.DB_THREAD | bsddb3.db.DB_INIT_MPOOL | bsddb3.db.DB_REGISTER
DBOPENFLAGS = bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE  | bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_MULTIVERSION 
g.DBOPENFLAGS = bsddb3.db.DB_THREAD | bsddb3.db.DB_CREATE  | bsddb3.db.DB_AUTO_COMMIT | bsddb3.db.DB_MULTIVERSION 
RMWFLAGS = 0
g.RMWFLAGS = 0


TXNFLAGS = bsddb3.db.DB_TXN_SNAPSHOT | bsddb3.db.DB_INIT_TXN | bsddb3.db.DB_INIT_LOCK |  bsddb3.db.DB_INIT_LOG
g.TXNFLAGS = bsddb3.db.DB_TXN_SNAPSHOT | bsddb3.db.DB_INIT_TXN | bsddb3.db.DB_INIT_LOCK |  bsddb3.db.DB_INIT_LOG
RECOVERFLAGS = bsddb3.db.DB_RECOVER
g.RECOVERFLAGS = bsddb3.db.DB_RECOVER


if USETXN:
	ENVOPENFLAGS |= TXNFLAGS
	g.ENVOPENFLAGS |= TXNFLAGS
	DBOPENFLAGS |= bsddb3.db.DB_AUTO_COMMIT
	g.DBOPENFLAGS |= bsddb3.db.DB_AUTO_COMMIT
	RMWFLAGS = bsddb3.db.DB_RMW
	g.RMWFLAGS = bsddb3.db.DB_RMW
	
if RECOVER:
	ENVOPENFLAGS |= RECOVERFLAGS
	g.ENVOPENFLAGS |= RECOVERFLAGS

