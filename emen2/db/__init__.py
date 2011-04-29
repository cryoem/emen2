# $Id$

def opendb(admin=True):
	import emen2.db.config
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--admin', action="store_true", help="Open DB with an Admin (root) Context")
	(options, args) = dbo.parse_args()
	return dbo.opendb(admin=True)

__version__ = "$Revision$".split(":")[1][:-1].strip()
