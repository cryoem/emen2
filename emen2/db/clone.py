#!/usr/bin/env python
# $Id$
from __future__ import with_statement

import sys
import getpass
import os

import emen2.db.admin

import emen2.clients
import emen2.clients.controllers

class CloneController(emen2.clients.controllers.EMEN2ClientController):

	def setparser_add_option(self):
		self.parser.add_option("--defs", action="store_true", help="Import params and recorddefs", default=0)
		self.parser.add_option("--users", action="store_true", help="Import users", default=0)
		self.parser.add_option("--records", action="store_true", help="Import records", default=0)
		self.parser.add_option("--bids", action="store_true", help="Import recorddefs", default=0)
		self.parser.add_option("--recordrels", action="store_true", help="Record relationships", default=0)


	def openlocaldb(self):
		self.localdb = emen2.db.admin.opendb()


	def run(self):
		self.check_args()

		# Login
		if not self.options.username:
			self.options.username = "anonymous"
			self.options.password = "anonymous"
			
		self.login()
		self.openlocaldb()

		with self.localdb:
			self.recmap = {}

			if self.options.defs:
				self._run_defs()


			if self.options.records or self.options.bids:
				self._update_recmap()


			if self.options.records:
				self._run_getrecords()
				self._run_putrecords()
				self._run_rels()


		# These will run in their own txn's...
		if self.options.bids:
			self._run_bids()



	def _run_defs(self):

		pdnames = self.db.getparamdefnames()
		rdnames = self.db.getrecorddefnames()

		pds = self.db.getparamdef(pdnames)
		rds = self.db.getrecorddef(rdnames)

		pdchildren = self.db.getchildtree(pdnames, -1, None, "paramdef")
		rdchildren = self.db.getchildtree(rdnames, -1, None, "recorddef")

		for pd in pds:
			pd["uri"] = "%s/paramdef/%s"%(self.db._host,pd["name"])	
			self.localdb.putparamdef(pd)

		for rd in rds:
			rd["uri"] = "%s/recorddef/%s"%(self.db._host,rd["name"])	
			self.localdb.putrecorddef(rd)

		for k,v in pdchildren.items():
			for v2 in v:
				self.localdb.pclink(k, v2, keytype="paramdef")

		for k,v in rdchildren.items():
			for v2 in v:
				self.localdb.pclink(k, v2, keytype="recorddef")



	def _update_recmap(self):
		self.recmap = {}
		try:
			localuris = self.localdb.getindexdictbyvalue("uri")
			for k,v in localuris.items():
				v = int(v.split("/")[-1])
				self.recmap[v] = k
		except Exception, e:
			print "Error getting local URI: %s"%e

		# print self.recmap


	def _run_getrecords(self):
		self.precs = []
		self.precs = self.db.getindexbypermissions(None, ["publish"]) # self.db.getrecord(pub_ids)
		self.precs = self.db.getrecord(self.precs)
		print "Got %s published records"%len(self.precs)



	def _run_putrecords(self):

		crecs = []

		for rec in self.precs:
			rec["uri"] = "%s/record/%s"%(self.db._host, rec["recid"])
			rec["permissions"] = ((),(),(),())
			rec["groups"] = ["anon"]
			rec["recid"] = int(rec["recid"])

			localid = self.recmap.get(rec["recid"])
			
			if localid != None:
				print "Found local ID %s for remote record %s"%(localid, rec["recid"])
				rec["recid"] = localid

			else:
				print "Remote record ID %s is new; unsetting recid to commit as new"%rec["recid"]
				rec["recid"] = None

			crecs.append(rec)


		print "Committing..."

		newrecids = self.localdb.putrecord(crecs, warning=True)



	def _run_rels(self):
		self._update_recmap()

		print "Updating mapping"

		remoteparents = self.db.getparenttree(self.recmap.keys(), -1)
		remotechildren = self.db.getchildtree(self.recmap.keys(), -1)

		# print remoteparents
		# print "--------"
		# print remotechildren

		#localparents = self.localdb.getparents(self.recmap.values())
		#localchildren = self.localdb.getchildren(self.recmap.values())
		# localrels = []
		# 		for k,v in localparents.items():
		# 			for i in v:
		# 				localrels.append((i,k))
		# 		for k,v in localchildren.items():
		# 			for i in v:
		# 				localrels.append((k,i))

		# remoterels = []
		# for k,v in remoteparents.items():
		# 	# we're using v[k] because it's a pain to pass kwargs to xmlrpc for now...
		# 	for i in v[k]:
		# 		k = int(k)
		# 		i = int(i)
		# 		remoterels.append((self.recmap.get(i),self.recmap.get(k)))
		# 
		# for k,v in remotechildren.items():
		# 	for i in v[k]:
		# 		k = int(k)
		# 		i = int(i)
		# 		remoterels.append((self.recmap.get(k),self.recmap.get(i)))

		remoterels = []
		for k,v in remoteparents.items():
			for i in v:
				remoterels.append((self.recmap.get(int(i)),self.recmap.get(int(k))))
		
		for k,v in remotechildren.items():
			for i in v:
				remoterels.append((self.recmap.get(int(k)),self.recmap.get(int(i))))
			

		#localrels = set(filter(lambda x:x[0] != None and x[1] != None, localrels))
		remoterels = set(filter(lambda x:x[0] != None and x[1] != None, remoterels))

		#delrels = localrels - remoterels
		#addrels = remoterels - localrels

		# self.localdb.pclinks(remoterels) # - localrels)
		for link in remoterels:
			self.localdb.pclink(link[0], link[1])
		
		#localdb.pcunlinks(localrels - remoterels)



	def _run_bids(self):
		bdos = self.db.getbinary(self.recmap.keys())
		
		bdolen = len(bdos)
		for count, bdo in enumerate(bdos):
			print "\n=============\n%s"%bdo.get('name')

			recid = self.recmap.get(bdo.get('recid'))
			
			found = False
			try:
				localbdo = self.localdb.getbinary(bdo.get('name'))
				if localbdo:
					if os.access(localbdo.get('filepath'), os.F_OK):
						print "This BDO appears to exist locally: %s. Skipping."%localbdo.get('name')
						found = True
					else:
						print "localbdo %s exists -- but no local file!"%localbdo.get('name')

			except Exception, inst:
				pass

			if found:
				continue
				
			print "Downloading %s for bdokey %s recid %s"%(bdo.get('filename'), bdo.get('name'), recid)
			
			dbt = emen2.clients.handlers.DownloadTransport(db=self.db, bdo=bdo, compress=False, pos=(count+1,bdolen))
			filename = dbt.action()

			print "Done downloading -- importing into db"

			try:
				infile = open(filename, 'rb')
				self.localdb.putbinary(bdokey=bdo.get('name'), recid=recid, infile=infile)
				infile.close()
			except Exception, inst:
				print inst

			if filename:
				os.unlink(filename)
			

	# def _run_download(self):
	# 	bdos = self.localdb.getbinary(self.recmap.values())
	# 	bdolen = len(bdos)
	# 	for count, bdo in enumerate(bdos):
	# 		dbt = emen2.clients.handlers.DBTransferFile(bdo=bdo, db=self.db)
	# 		# here we set the filename to the local bdo filepath
	# 		dbt.download_print(filename=bdo.get("filepath"), overwrite=False, decompress=False, pos=(count+1,bdolen))




	def _run_users(self):
		pass



try:
	args = sys.argv[1:]
	args = args[args.index("--")+1:]
except:
	pass

a = CloneController(args=args)
a.run()

__version__ = "$Revision$".split(":")[1][:-1].strip()



