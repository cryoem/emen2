# $Id$
import sys
sys.path.extend(['/Users/edwlan/Programming/jsonrpc','/Users/edwlan/Programming/emen2/emen2'])

if __name__ == "__main__":
	import emen2.db
	db = emen2.db.opendb()

__version__ = "$Revision$".split(":")[1][:-1].strip()
