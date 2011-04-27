# $Id$
import emen2
import emen2.db.config

if __name__ == "__main__":
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--uri', type="string", help="Export with base URI")
	(options, args) = dbo.parse_args()
	db = dbo.admindb()
	
__version__ = "$Revision$".split(":")[1][:-1].strip()
