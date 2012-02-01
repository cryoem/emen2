# $Id$
"""EMEN2: An object-oriented scientific database."""

def opendb(config=None, **kwargs):
	"""Open a database."""
	# Import the config first and parse
	import emen2.db.config
	cmd = emen2.db.config.UsageParser()
	import emen2.db.database
	return emen2.db.database.DB.opendb(**kwargs)
	

__version__ = "$Revision$".split(":")[1][:-1].strip()