import os
import time
import tarfile
import tempfile
import string
import random
import shutil

import emen2.db.admin
import emen2.db.config
import emen2.util.jsonutil
import emen2.util.listops



class Dumper(object):

	def __init__(self, db, root=None, outfile=None, names=None, allrecords=False, allbdos=False, allusers=False, allgroups=True, allparamdefs=True, allrecorddefs=True, addfiles=True):
		mtime = time.time()
		self.root = root		
		
		# self.outfile = outfile or "backup-%s.tar.gz"%(time.strftime("%Y.%m.%d-%H.%M.%S"))
		self.db = db

		# Initial items
		self.names = set()
		self.recorddefnames = set()
		self.paramdefnames = set()
		self.usernames = set()
		self.groupnames = set()
		self.bdos = set()

		# We need these to find additional users and groups and bdos
		self.paramdefs_user = set()
		self.paramdefs_userlist = set()
		self.paramdefs_binary = set()
		self.paramdefs_binaryimage = set()

		# Initial items..
		# root = 382351
		names = self.db.getchildren(self.root, recurse=-1)
		names.add(self.root)

		if allrecords:
			names |= self.db.getchildren(0, recurse=-1)
		
		if allgroups:
			allgroups = self.db.getgroupnames()
		if allusers:
			allusers = self.db.getgroupnames()
		if allparamdefs:
			allparamdefs = self.db.getparamdefnames()
		if allrecorddefs:
			allrecorddefs = self.db.getrecorddefnames()		
		# if allbdos:
		# 	...
		

		print "Starting with %s records"%len(names)		
		self.checkrecords(names, addgroups=allgroups, addusers=allusers, addparamdefs=allparamdefs, addrecorddefs=allrecorddefs, addbdos=allbdos)

		remove = set([None])
		self.usernames -= remove
		self.groupnames -= remove
		self.recorddefnames -= remove
		self.paramdefnames -= remove
		self.bdos -= remove

		print "\n=====================\nStatistics:"
		print "\trecords: %s"%len(self.names)
		print "\trecorddefs: %s"%len(self.recorddefnames)
		print "\tparamdefs: %s"%len(self.paramdefnames)
		print "\tusers: %s"%len(self.usernames)
		print "\tgroups: %s"%len(self.groupnames)		
		print "\tbdos: %s"%len(self.bdos)		
		print ""

		# tmp fix..
		self.usernames.add("bendubin-thaler")
		
		#print "Writing output to %s"%self.outfile
		#outfile = tarfile.open(self.outfile, "w:gz")
		
		self.addfile(self.writetmp(self.dumpparamdefs), "paramdefs.json")
		self.addfile(self.writetmp(self.dumprecorddefs), "recorddefs.json")
		self.addfile(self.writetmp(self.dumpusers), "users.json")
		self.addfile(self.writetmp(self.dumpgroups), "groups.json")
		self.addfile(self.writetmp(self.dumprecords), "records.json")
		self.addfile(self.writetmp(self.dumpbdos), "bdos.json")

		if addfiles:
			for bdo in self.bdos:
				self.addbdo(bdo)

	

	def addfile(self, filepath, filename):
		print "Adding %s to backup as %s"%(filepath, filename)
		if not os.path.exists(filename):
			shutil.copyfile(filepath, filename)
		else:
			print "WARNING!! File exists %s exists, skipping!"%filename



	def addbdo(self, bdo):
		b = self.db.getbinary(bdo)
		try:
			filename = b.name.replace(":", ".")
			filepath = b.filepath
			self.addfile(filepath, filename)
		except Exception, inst:
			print "Could not add %s: %s"%(bdo, inst)
		
	
	
	def writetmp(self, method):
		fd, filename = tempfile.mkstemp()
		with open(filename, "w") as f:
			for item in method():
				f.write(emen2.util.jsonutil.encode(item))
				f.write("\n")
		return filename
		

	def checkrecords(self, names, addgroups=None, addusers=None, addparamdefs=None, addrecorddefs=None, addbdos=None):
		if not names:
			return
			
		users = set()
		groups = set()
		pds = set()
		rds = set()
		bdos = set()		
		for chunk in emen2.util.listops.chunk(names-self.names):
			self.names |= set(chunk)
			record = self.db.getrecord(chunk)
			for i in self.db.findrecorddef(record=record):
				rds.add(i.name)
			for i in self.db.findparamdef(record=record):
				pds.add(i.name)
			for i in self.db.finduser(record=record):
				users.add(i.name)
			for i in self.db.findgroup(record=record):
				groups.add(i.name)
			for i in self.db.findbinary(record=record):
				bdos.add(i.name)

		# Add in additional items
		if addgroups:
			groups |= addgroups
		if addusers:
			addusers |= addusers
		if addparamdefs:
			pds |= addparamdefs
		if addrecorddefs:
			rds |= addrecorddefs	
		if addbdos:
			bdos |= addbdos
				
		print "Next round..."
		print "\tusers: ", len(users-self.usernames)
		print "\tgroups: ", len(groups-self.groupnames)
		print "\trecorddefs: ", len(rds-self.recorddefnames)
		print "\tparamdefs: ", len(pds-self.paramdefnames)
		print "\tbdos: ", len(bdos-self.bdos)
		# 		
		# start recursing..
		
		self.checkusers(users)
		self.checkgroups(groups)
		self.checkrecorddefs(rds)
		self.checkparamdefs(pds)
		self.checkbdos(bdos)


	def checkusers(self, usernames):
		usernames -= self.usernames
		if not usernames:
			return
			
		# print "Checking users: ", len(usernames)
		newnames = set()
		newgroups = set()
		for chunk in emen2.util.listops.chunk(usernames):
			self.usernames |= set(chunk)
			users = self.db.getuser(chunk)

			for user in users:
				newnames.add(user.record)
		
		# This will generate new users and groups to check..	
		self.checkrecords(newnames)
		


	def checkgroups(self, groupnames):
		groupnames -= self.groupnames
		if not groupnames:
			return

		# print "Checking groups: ", len(groupnames)
		newusers = set()
		for chunk in emen2.util.listops.chunk(groupnames):
			self.groupnames |= set(chunk)
			groups = self.db.getgroup(chunk)
			for group in groups:
				newusers.add(group.creator)
				#newusers.add(group.modifyuser)
			
		self.checkusers(newusers)
		
		
	
	def checkrecorddefs(self, recorddefnames):
		recorddefnames -= self.recorddefnames
		if not recorddefnames:
			return
			
		# print "Checking recorddefs: ", len(recorddefnames)
		newparamdefs = set()
		newusers = set()
		for chunk in emen2.util.listops.chunk(recorddefnames):
			self.recorddefnames |= set(chunk)
			recorddefs = self.db.getrecorddef(chunk)
			for rd in recorddefs:
				newusers.add(rd.creator)
				#newusers.add(rd.modifyuser)
				newparamdefs |= set(rd.paramsK)
		
		self.checkusers(newusers)
		self.checkparamdefs(newparamdefs)
		
		
		
	def checkparamdefs(self, paramdefnames):
		paramdefnames -= self.paramdefnames
		if not paramdefnames:
			return
			
		# print "Checking paramdefs: ", len(paramdefnames)
		newusers = set()
		for chunk in emen2.util.listops.chunk(paramdefnames):
			self.paramdefnames |= set(chunk)
			paramdefs = self.db.getparamdef(chunk)	
			for pd in paramdefs:
				newusers.add(pd.creator)
				#newusers.add(pd.modifyuser)
				
		self.checkusers(newusers)
				
	
	def checkbdos(self, bdos):
		bdos -= self.bdos
		if not bdos:
			return
			
		newbdos = set()
		for chunk in emen2.util.listops.chunk(bdos):
			self.bdos |= set(chunk)
						
				
		
	# The dump* methods are generators that spit out JSON-encoded DBO's
	def dumprecords(self, cur=0):
		found = set()
		# reorganize the names slightly...
		ordered_names = sorted(self.names)
		if self.root != None and self.root in self.names:
			ordered_names.remove(self.root)
			ordered_names.insert(0, self.root)

		for chunk in emen2.util.listops.chunk(ordered_names):
			t = time.time()
			recs = self.db.getrecord(chunk)
			found |= set([i.name for i in recs])
			for rec in recs:
				rec.parents &= self.names
				rec.children &= self.names
				yield rec

			cur += len(recs)
			self.printchunk(len(recs), cur=cur, total=len(self.names), t=t, keytype="records")

		self.notfound(found, self.names)
		


	def dumpparamdefs(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.paramdefnames):
			t = time.time()
			pds = self.db.getparamdef(chunk)
			found |= set([pd.name for pd in pds])	
			for pd in pds:
				pd.parents &= self.paramdefnames
				pd.children &= self.paramdefnames
				yield pd
				
			cur += len(pds)
			self.printchunk(len(pds), cur=cur, total=len(self.paramdefnames), t=t, keytype="paramdefs")

		self.notfound(found, self.paramdefnames)

		
			
	def dumprecorddefs(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.recorddefnames):
			t = time.time()
			rds = self.db.getrecorddef(chunk)
			found |= set([rd.name for rd in rds])
			for rd in rds:
				rd.parents &= self.recorddefnames
				rd.children &= self.recorddefnames
				yield rd

			cur += len(rds)
			self.printchunk(len(rds), cur=cur, total=len(self.recorddefnames), t=t, keytype="recorddefs")

		self.notfound(found, self.recorddefnames)




	def dumpusers(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.usernames):
			t = time.time()
			users = db.getuser(chunk)
			found |= set([user.name for user in users])
		
			for user in users:
				yield user

			cur += len(users)
			self.printchunk(len(users), cur=cur, total=len(self.usernames), t=t, keytype="users")
		
		self.notfound(found, self.usernames)
	
	
	
	def dumpgroups(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.groupnames):
			t = time.time()
			groups = self.db.getgroup(chunk)
			found |= set([group.name for group in groups])
		
			for group in groups:
				yield group

			cur += len(groups)
			self.printchunk(len(groups), cur=cur, total=len(self.groupnames), t=t, keytype="groups")

		self.notfound(found, self.groupnames)


	def dumpbdos(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.bdos):
			t = time.time()
			bdos = self.db.getbinary(chunk)
			found |= set([bdo.name for bdo in bdos])
			
			for bdo in bdos:
				yield bdo
				
			cur += len(bdos)
			self.printchunk(len(bdos), cur=cur, total=len(self.bdos), t=t, keytype="bdos")

		self.notfound(found, self.bdos)
			

	
	def notfound(self, found, i):
		if i-found:
			print "Did not find: ", i-found
	
	
	
	def printchunk(self, chunksize, cur, total, t, keytype="record"):
		percent = (cur / float(total))*100
		persec = chunksize / (time.time()-t)
		print "%s %0.1f @ %0.1f keys/sec"%(keytype, percent, persec)
			
	


def main():
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--uri', type="string", help="Export with base URI")
	(options, args) = dbo.parse_args()
	db = dbo.opendb()
	print db.checkcontext()
	print db.getrecord(0)
	
	# import emen2.db.admin
	# db = emen2.db.admin.opendb()
	# d = Dumper(root=382351, db=db)
	


if __name__ == "__main__":
	main()















