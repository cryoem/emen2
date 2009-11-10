import emen2.Database.DBProxy
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

parser = emen2.config.config.DBOptions()
parser.parse_args()

db = emen2.Database.DBProxy.DBProxy()
ddb = db._DBProxy__db

print db._login("root",g.ROOTPW)
