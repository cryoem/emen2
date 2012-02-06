# $Id$

if __name__ == "__main__":
	import emen2.db.log
	emen2.db.log.log_init()
	import emen2.db
	db = emen2.db.opendb(admin=True)

__version__ = "$Revision$".split(":")[1][:-1].strip()
