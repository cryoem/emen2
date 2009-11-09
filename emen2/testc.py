import emen2.Database.DBProxy
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

db = emen2.Database.DBProxy.DBProxy()
ddb = db._DBProxy__db

print db._login("root",g.ROOTPW)
