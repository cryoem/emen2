# $Id$

#!/usr/bin/python
import os
import time
import urllib
import time
import sys
import traceback
import subprocess

import httplib
import urllib
import urllib2
import xmlrpclib


def trykill(pid, signall, waittime):
	try:
		os.kill(pid, signall)
		return True
	except Exception, inst:
		g.log_error("\terror: %s"%inst)
		time.sleep(waittime)



def notifycallback():
	# email or SMS admin...
	g.log_init("Note: !!")


def readpid():
	pid = None
	try:
		f = open(g.paths.EMEN2JOBFILE, "r")
		pid = int(f.readlines()[-1].strip())
		f.close()
	except:
		pass
	return pid



def ping():
	try:
		db = xmlrpclib.ServerProxy("http://%s:%s%s/RPC2"%('localhost', g.EMEN2PORT, g.EMEN2WEBROOT), allow_none=1)
		t = db.gettime()
	except:
		return False
	return True



def start():
	with open(g.paths.EMEN2ERRLOG, 'w') as errfile:
		errfile.truncate()

		if ping():
			g.log_init("Server appears to be running; manual restart necessary")
			return

		g.log_init("Starting EMEN2 server")

		try:
			try:
				newpid = os.fork()
				if newpid > 0:
					return
			except OSError,e:
				g.log_error('First fork failed, exiting')
				g.log_error('err msg: %s' % e)
				return

			os.setsid()
			os.umask(0)

			g.log.capturestdout()
			g.log.closestdout()
			os.close(0)
			os.close(1)
			os.close(2)

			try:
				newpid = os.fork()
				if newpid > 0:
					pidfile = g.paths.EMEN2JOBFILE
					g.log_init("Writing newpid: %s -> %s"%(newpid, pidfile))
					with file(pidfile, 'w') as pidfile:
						pidfile.seek(0)
						pidfile.write('%s'%newpid)
					return

			except OSError:
				g.log_error('Second fork failed, exiting')
				return


			import emen2.web.server
			emen2.web.server.inithttpd()


		except Exception, e:
			sys.stderr = errfile
			sys.stdout = sys.stderr
			sys.stderr.seek(0)
			traceback.print_exc()
			return





def log_archive():
	import emen2.db.database
	# Open DB Env
	ddb = emen2.db.database.DB(maint=True)
	ddb.log_archive(remove=True, checkpoint=True)
	ddb.close()




def main():

	global g
	import emen2.db.config

	parser = emen2.db.config.DBOptions()
	parser.add_option("--ping", action="store_true", help="Make sure the DB is running before any action")
	parser.add_option("--noping", action="store_true", help="Make sure the DB is dead before any action")
	parser.add_option("--log_archive", action="store_true", help="Archive completed log files")
	parser.add_option("--start", action="store_true", help="Start server")
	parser.add_option("--shutdown", action="store_true", help="Stop server")
	parser.add_option("--stop", dest="shutdown", action="store_true", help="Stop server")
	parser.add_option("--restart", action="store_true", help="Restart server")
	(options, args) = parser.parse_args()

	g = emen2.db.config.g()

	options.pid = readpid()

	if options.ping or options.noping:
		pingresult = ping()
	if options.ping and not pingresult:
		g.log_init("Server ping failed!")
		return

	if options.noping and pingresult:
		g.log_init("Server is still up!")
		return


	if options.restart or options.shutdown:
		waittime = 1

		if not options.pid:
			g.log_init("No server PID; Manual kill may be necessary")

		else:
			g.log_init("Attempting to end process %s"%options.pid)
			success = False
			for count in range(10):
				success = trykill(options.pid, 1, waittime)
				options.recover = True

			if not success:
				g.log_init("\tNo success after %s retries (%s seconds); sending sigkill"%(count, count*waittime))
				success = trykill(options.pid, 9, waittime)

			if success:
				os.unlink(g.paths.EMEN2JOBFILE)


	# Usually the server flags take care of this
	# if options.recover:
	# 	g.log_init("Running db_recovery")
	# 	g.debug(g.db_recover)
	# 	r = "%s -h %s"%(g.db_recover, g.EMEN2DBHOME)
	# 	r = subprocess.Popen(r)
	# 	r.wait()


	if options.restart or options.start:
		start()


	if options.log_archive:
		log_archive()





# Reindex script...

# import emen2.db.admin
# db = emen2.db.admin.opendb()
# 
# with db:
# 	txn = db._gettxn()
# 	ctx = db._getctx()
# 	db._DBProxy__db._rebuild_all(ctx=ctx, txn=txn)
# 
# 
# __version__ = "$Revision$".split(":")[1][:-1].strip()



# Reset password...

# import getpass
# import emen2.db.admin
# import emen2.db.config
# 
# parser = emen2.db.config.DBOptions()
# parser.add_option("--user", type="string", help="Account to reset password", default="root")
# (options, args) = parser.parse_args()
# 
# print "Changing password for %s"%options.user
# newpass = getpass.getpass("New password: ")
# 
# db = emen2.db.admin.opendb()
# db.setpassword("", newpass, username=options.user)
# 



# New database

# import getpass
# import shutil
# import os
# import sys
# import optparse
# import sys
# 
# import emen2.db.config
# parser = emen2.db.config.DBOptions()
# parser.parse_args()
# g = emen2.db.config.g()
# 
# import emen2.db.database
# 
# rootpw = g.getprivate('ROOTPW')
# if not rootpw:
# 	rootpw = getpass.getpass("root password for new database:")
# 
# # Open DB Env
# ddb = emen2.db.database.DB(g.EMEN2DBHOME)
# 
# txn = ddb.newtxn()
# 
# ddb.create_db(rootpw=rootpw, txn=txn)
# 
# txn.commit()









if __name__ == "__main__":
	main()

__version__ = "$Revision$".split(":")[1][:-1].strip()
