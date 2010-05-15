import getpass

import emen2
db = emen2.db()
db.login("root", getpass.getpass())
