import db.proxy
def opendb():
	return db.proxy.DBProxy()

