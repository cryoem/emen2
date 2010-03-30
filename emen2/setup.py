import getpass
import shutil
import os
import sys
import emen2.config.config
import optparse
import sys


# command = sys.argv[1]

# if command == "init":
# 
# 	parser = optparse.OptionParser(add_help_option=False)
# 	parser.add_option("-h", "--home", type="string", help="DB_Home")
# 	parser.add_option('--help', action="help", help="Print help message")
# 	(options, args) = parser.parse_args(sys.argv[1:])
# 
# 	dbpath = options.home
# 	
# 	if os.path.exists(dbpath):
# 		raise Exception, "Existing DB Environment: %s"%dbpath
# 
# 	print "Seting up DB Environment in: %s"%dbpath
# 	os.makedirs(dbpath)
# 
# 	print "Copying base config files"
# 
# 	inconfig = emen2.config.config.get_filename('emen2', 'config/config.sample.yml')
# 	outconfig = "%s/config.yml"%(dbpath)
# 	print "%s -> %s"%(inconfig, outconfig)
# 	shutil.copy(inconfig, outconfig)
# 
# 	indb = emen2.config.config.get_filename('emen2', 'config/DB_CONFIG.sample')
# 	outdb = "%s/DB_CONFIG"%(dbpath)
# 	print "%s -> %s"%(indb,outdb)
# 	shutil.copy(indb,outdb)
# 
# 
# 
# elif command == "create":

import emen2.globalns
from emen2.config.config import g, DBOptions

parser = DBOptions()
parser.parse_args()

import emen2.Database.database

# Open DB Env
ddb = emen2.Database.database.DB(g.EMEN2DBPATH)

txn = ddb.newtxn()

ddb.create_db(txn=txn)

txn.commit()
