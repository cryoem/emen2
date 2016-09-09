# $Id: create.py,v 1.3 2013/05/21 21:21:51 irees Exp $
"""Create a new database."""

import os
import sys
import time
import tarfile
import tempfile
import string
import random
import collections
import getpass
import json
import jsonrpc.jsonutil

# EMEN2 imports
import emen2.util.listops
import emen2.db.config

class CreateOptions(emen2.db.config.DBOptions):
    def parseArgs(self):
        pass

if __name__ == "__main__":
    import emen2.db
    db = emen2.db.opendb(admin=True)
    db._db.dbenv.create()
    emen2.db.database.setup(db=db)
            
        