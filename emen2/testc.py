import atexit
import emen2.globalns
import emen2.config.config
parser = emen2.config.config.DBOptions()
parser.parse_args()
g = emen2.globalns.GlobalNamespace('')
import emen2.Database.DBProxy
import emen2.Database.database

#@atexit.register
def _atexit():
	global db
	try:
		if (raw_input('commit txn [y/N]? ') or 'n').lower().startswith('y'):
			db._committxn()
		else:
			db._aborttxn()
	except NameError,e:
		print e


db = emen2.Database.DBProxy.DBProxy()
ddb = db._DBProxy__db

db._login("root", g.ROOTPW)
db._starttxn()
txn = db._gettxn()
ctx = db._getctx()