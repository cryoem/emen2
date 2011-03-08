import os
import time
import tarfile
import tempfile
import string
import random

import emen2.db.admin
import emen2.util.jsonutil
import emen2.util.listops



class Dumper(object):

	def __init__(self, db, outfile=None, recids=None, allrecords=False, allbdos=False, allusers=False, allgroups=True, allparamdefs=True, allrecorddefs=True, addfiles=True):
		mtime = time.time()
		
		
		self.outfile = outfile or "backup-%s.tar.gz"%(time.strftime("%Y.%m.%d-%H.%M.%S"))
		self.db = db

		# Initial items
		self.recids = set()
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
		root = 382351		
		recids = self.db.getchildren(root, recurse=-1)
		recids.add(root)

		if allrecords:
			recids |= self.db.getchildren(0, recurse=-1)
		
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
		

		print "Starting with %s records"%len(recids)		
		self.checkrecords(recids, addgroups=allgroups, addusers=allusers, addparamdefs=allparamdefs, addrecorddefs=allrecorddefs, addbdos=allbdos)

		remove = set([None])
		self.usernames -= remove
		self.groupnames -= remove
		self.recorddefnames -= remove
		self.paramdefnames -= remove
		self.bdos -= remove

		print "\n=====================\nStatistics:"
		print "\trecords: %s"%len(self.recids)
		print "\trecorddefs: %s"%len(self.recorddefnames)
		print "\tparamdefs: %s"%len(self.paramdefnames)
		print "\tusers: %s"%len(self.usernames)
		print "\tgroups: %s"%len(self.groupnames)		
		print "\tbdos: %s"%len(self.bdos)		
		print ""

		# tmp fix..
		self.usernames.add("bendubin-thaler")
		
		print "Writing output to %s"%self.outfile
		outfile = tarfile.open(self.outfile, "w:gz")
		self.taradd(outfile, "paramdefs.json", self.writetmp(self.dumpparamdefs))
		self.taradd(outfile, "recorddefs.json", self.writetmp(self.dumprecorddefs))
		self.taradd(outfile, "users.json", self.writetmp(self.dumpusers))
		self.taradd(outfile, "groups.json", self.writetmp(self.dumpgroups))
		self.taradd(outfile, "records.json", self.writetmp(self.dumprecords))
		self.taradd(outfile, "bdos.json", self.writetmp(self.dumpbdos))		

		if addfiles:
			for bdo in self.bdos:
				self.taraddfile(outfile, bdo)

		outfile.close()
		
	
	# def addfile(self, filename, filepath=None, tar=None, gen=None):
	# 	if tar:
	# 		if gen:
	# 			tmpfile = self.writetmp(self.dumpparamdefs)
		
	
	def taraddfile(self, tar, bdo):
		b = self.db.getbinary(bdo)
		try:
			name = b.name.replace(":", ".")
			filepath = b.filepath
			tar.add(arcname=name, name=filepath)
			print "Added %s to tarfile as %s"%(filepath, name)
		except Exception, inst:
			print "Could not add %s: %s"%(bdo, inst)
		
	
	
	def taradd(self, tar=None, arcname=None, filename=None):
		if tar:
			tar.add(arcname=arcname, name=filename)
			os.unlink(filename)
	
		
	def writetmp(self, method):
		fd, filename = tempfile.mkstemp() 
		with open(filename, "w") as f:
			for item in method():
				f.write(emen2.util.jsonutil.encode(item))
				f.write("\n")
		return filename
		
		

	def checkrecords(self, recids, addgroups=None, addusers=None, addparamdefs=None, addrecorddefs=None, addbdos=None):
		if not recids:
			return
			
		users = set()
		groups = set()
		pds = set()
		rds = set()
		bdos = set()
		
		for chunk in emen2.util.listops.chunk(recids-self.recids):
			self.recids |= set(chunk)
			recs = self.db.getrecord(chunk)
			rds |= set([rec.rectype for rec in recs])					

			for rec in recs:
				keys = set(rec.keys())	
			
				for pd in keys-self.paramdefnames-pds:
					pds.add(pd)
					p = self.db.getparamdef(pd)
					if p.vartype == "user":
						self.paramdefs_user.add(pd)
					elif p.vartype == "userlist":
						self.paramdefs_userlist.add(pd)
					elif p.vartype == "binary":
						self.paramdefs_binary.add(pd)
					elif p.vartype == "binaryimage":
						self.paramdefs_binaryimage.add(pd)
			
				users |= emen2.util.listops.combine(*rec['permissions'], dtype=set)				
				
				for key in keys&self.paramdefs_user:
					users.add(rec.get(key))
				for key in keys&self.paramdefs_userlist:
					users |= set(rec.get(key, []))
			
				for key in keys&self.paramdefs_binary:
					bdos |= set(rec.get(key, []))
				for key in keys&self.paramdefs_binaryimage:
					bdos.add(rec.get(key))
			
				groups |= rec['groups']	


		# Add in additional items
		if addgroups: groups |= addgroups
		if addusers: addusers |= addusers
		if addparamdefs: pds |= addparamdefs
		if addrecorddefs: rds |= addrecorddefs	
		if addbdos: bdos |= addbdos
				
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
		newrecids = set()
		newgroups = set()
		for chunk in emen2.util.listops.chunk(usernames):
			self.usernames |= set(chunk)
			users = self.db.getuser(chunk)

			for user in users:
				newrecids.add(user.record)
		
		# This will generate new users and groups to check..	
		self.checkrecords(newrecids)
		


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
		for chunk in emen2.util.listops.chunk(self.recids):
			t = time.time()
			recs = self.db.getrecord(chunk)
			found |= set([i.recid for i in recs])
			parents = self.db.getparents(chunk)
			children = self.db.getchildren(chunk)
			for rec in recs:
				rec["parents"] = parents.get(rec.recid, set()) & self.recids
				rec["children"] = children.get(rec.recid, set()) & self.recids
				yield rec

			cur += len(recs)
			self.printchunk(len(recs), cur=cur, total=len(self.recids), t=t, keytype="records")

		self.notfound(found, self.recids)
		


	def dumpparamdefs(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.paramdefnames):
			t = time.time()
			pds = self.db.getparamdef(chunk)
			found |= set([pd.name for pd in pds])
			parents = self.db.getparents(chunk, keytype="paramdef")
			children = self.db.getchildren(chunk, keytype="paramdef")
		
			for pd in pds:
				pd.parents = parents.get(pd.name, set()) & self.paramdefnames
				pd.children = children.get(pd.name, set()) & self.paramdefnames
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
			parents = self.db.getparents(chunk, keytype="recorddef")
			children = self.db.getchildren(chunk, keytype="recorddef")
		
			for rd in rds:
				rd.parents = parents.get(rd.name, set()) & self.recorddefnames
				rd.children = children.get(rd.name, set()) & self.recorddefnames
				yield rd

			cur += len(rds)
			self.printchunk(len(rds), cur=cur, total=len(self.recorddefnames), t=t, keytype="recorddefs")

		self.notfound(found, self.recorddefnames)




	def dumpusers(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.usernames):
			t = time.time()
			users = db.getuser(chunk)
			found |= set([user.username for user in users])
		
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
			
	





if __name__ == "__main__":
	import emen2.db.admin
	db = emen2.db.admin.opendb()
	d = Dumper(db=db)



