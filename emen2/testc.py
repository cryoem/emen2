import emen2.globalns
import emen2.config.config
parser = emen2.config.config.DBOptions()
parser.parse_args()
g = emen2.globalns.GlobalNamespace('')
import emen2.Database.DBProxy


db = emen2.Database.DBProxy.DBProxy()

ddb = db._DBProxy__db

print db._login("root",g.ROOTPW)
