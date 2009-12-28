import emen2.globalns
import emen2.config.config
parser = emen2.config.config.DBOptions()
parser.parse_args()
g = emen2.globalns.GlobalNamespace('')
import emen2.Database.DBProxy
import emen2.Database.database

db = emen2.Database.DBProxy.DBProxy()
print db
ddb = db._DBProxy__db

#try:
#	print db._login("root",g.ROOTPW)
#except Exception, e:
#	print e
