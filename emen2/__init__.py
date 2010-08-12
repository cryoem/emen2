import collections
# add OrderedDict from py2.7 to collections
if not hasattr('collections', 'OrderedDict'):
	import util.ordereddict
del collections

import db.proxy
def opendb():
	return db.proxy.DBProxy()

