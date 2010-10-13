def opendb():
	import db.proxy
	return db.proxy.DBProxy()

