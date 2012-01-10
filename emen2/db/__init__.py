# $Id$
"""EMEN2: An object-oriented scientific database."""

def opendb(*args, **kwargs):
	"""Helper method for opening DB with default options"""
	import config
	dbo = config.DBOptions()
	(options, args) = dbo.parse_args()
	return dbo.opendb(*args, **kwargs)

__version__ = "$Revision$".split(":")[1][:-1].strip()
