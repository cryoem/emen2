# $Id$

def opendb(*args, **kwargs):
	import config
	dbo = config.DBOptions(loginopts=True)
	(options, args) = dbo.parse_args()
	return dbo.opendb(*args, **kwargs)

__version__ = "$Revision$".split(":")[1][:-1].strip()
