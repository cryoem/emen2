import getpass
import shutil
import os
import sys
import emen2.config.config
import optparse
import sys


# #parser = optparse.OptionParser()
# parser = emen2.config.config.DBOptions()
# parser.add_option("--init", action="store_true", help="Create DB_HOME directory and copy base config files")
# parser.add_option("--create_db", action="store_true", help="After editing config file, create initial DB_HOME environment")
# (options, args) = parser.parse_args(lc=False, args=sys.argv)
# 
# # 
# # if len(args) < 2:
# # 	raise ValueError, "Need target DB_HOME directory"
# # 	
# # 

command = sys.argv[1]
dbpath = sys.argv[2]


if command == "init":
	
	if os.path.exists(dbpath):
		raise Exception, "Existing DB Environment: %s"%dbpath

	print "Seting up DB Environment in: %s"%dbpath
	os.makedirs(dbpath)

	print "Copying base config files"

	inconfig = emen2.config.config.get_filename('emen2', 'config/config.sample.yml')
	outconfig = "%s/config.yml"%(dbpath)
	print "%s -> %s"%(inconfig, outconfig)
	shutil.copy(inconfig, outconfig)

	indb = emen2.config.config.get_filename('emen2', 'config/DB_CONFIG.sample')
	outdb = "%s/DB_CONFIG"%(dbpath)
	print "%s -> %s"%(indb,outdb)
	shutil.copy(indb,outdb)



elif command == "create":

	import emen2.globalns
	from emen2.config.config import g, DBOptions

	parser = DBOptions()
	parser.parse_args()

	import emen2.Database.database

	# Open DB Env
	ddb = emen2.Database.database.DB()

	txn = ddb.newtxn()

	ddb.create_db(txn=txn)

	txn.commit()
	
