import emen2.Database.proxy
import getpass

db = emen2.db()
rootpw = getpass.getpass()
db.login("root", rootpw)
