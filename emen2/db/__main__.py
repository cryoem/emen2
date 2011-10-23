# $Id$
"""Open an EMEN2 console with administrative privileges."""
import sys

if __name__ == "__main__":
	"""Run DB console as admin"""
	import emen2.db
	db = emen2.db.opendb(admin=True)

__version__ = "$Revision$".split(":")[1][:-1].strip()
