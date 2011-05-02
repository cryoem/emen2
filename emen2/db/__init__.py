# $Id$

def opendb():
	import config
	dbo = config.DBOptions(loginopts=True)
	(options, args) = dbo.parse_args()
	return dbo.opendb()

__version__ = "$Revision$".split(":")[1][:-1].strip()
