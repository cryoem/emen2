# $Id$

VERSION = "2.0rc5"

def opendb():
	import db.proxy
	return db.proxy.DBProxy()

__version__ = "$Revision$".split(":")[1][:-1].strip()
