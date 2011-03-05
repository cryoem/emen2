import time

import emen2.db.admin
import emen2.util.jsonutil
import emen2.util.listops


class Dumper(object):

	def __init__(self, db, outfile="out.json"):
		self.db = db
		self.recids = set()
		self.recorddefnames = set()
		self.paramdefnames = set()
		self.usernames = set()
		self.groupnames = set()

		self.paramdefs_user = set()
		self.paramdefs_userlist = set()

		# This will start with a set of recids, then recurse to find all referenced items
		recids = self.db.getchildren(0, recurse=4)
		print "Starting with %s records"%len(recids)
		self.checkrecords(recids)

		remove = set([None])
		self.usernames -= remove
		self.groupnames -= remove
		self.recorddefnames -= remove
		self.paramdefnames -= remove

		print "\n=====================\nStatistics:"
		print "\trecords: %s"%len(self.recids)
		print "\trecorddefs: %s"%len(self.recorddefnames)
		print "\tparamdefs: %s"%len(self.paramdefnames)
		print "\tusers: %s"%len(self.usernames)
		print "\tgroups: %s"%len(self.groupnames)		
		print ""

		self.outfile = open(outfile, "w")
		self.dumpparamdefs()
		self.dumprecorddefs()
		self.dumpusers()
		self.dumpgroups()
		self.dumprecords()
		self.outfile.close()

		
		

	def checkrecords(self, recids):
		if not recids:
			return
			
		users = set()
		groups = set()
		pds = set()
		rds = set()
		
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
			
				users |= emen2.util.listops.combine(*rec['permissions'], dtype=set)				
				for key in keys&self.paramdefs_user:
					users.add(rec.get(key))
				for key in keys&self.paramdefs_userlist:
					users |= set(rec.get(key, []))
			
				groups |= rec['groups']	
				
		print "Next round..."
		print "\tusers: ", len(users-self.usernames)
		print "\tgroups: ", len(groups-self.groupnames)
		print "\trecorddefs: ", len(rds-self.recorddefnames)
		print "\tparamdefs: ", len(pds-self.paramdefnames)
		
		# start recursing..
		self.checkusers(users)
		self.checkgroups(groups)
		self.checkrecorddefs(rds)
		self.checkparamdefs(pds)



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
				
		

	def dumprecords(self, cur=0):
		found = set()
		for chunk in emen2.util.listops.chunk(self.recids):
			t = time.time()
			recs = self.db.getrecord(chunk)
			found |= set([i.recid for i in recs])
			parents = self.db.getparents(chunk)
			children = self.db.getparents(chunk)
			for rec in recs:
				rec["parents"] = parents.get(rec.recid, set()) & self.recids
				rec["children"] = children.get(rec.recid, set()) & self.recids
				self.outfile.write(emen2.util.jsonutil.encode(rec))
				self.outfile.write("\n");

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
			children = self.db.getparents(chunk, keytype="paramdef")
		
			for pd in pds:
				pd["parents"] = parents.get(pd.name, set()) & self.paramdefnames
				pd["children"] = children.get(pd.name, set()) & self.paramdefnames
				self.outfile.write(emen2.util.jsonutil.encode(pd))
				self.outfile.write("\n");

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
			children = self.db.getparents(chunk, keytype="recorddef")
		
			for rd in rds:
				rd["parents"] = parents.get(rd.name, set()) & self.recorddefnames
				rd["children"] = children.get(rd.name, set()) & self.recorddefnames
				self.outfile.write(emen2.util.jsonutil.encode(rd))
				self.outfile.write("\n");

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
				self.outfile.write(emen2.util.jsonutil.encode(user))
				self.outfile.write("\n");

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
				self.outfile.write(emen2.util.jsonutil.encode(group))
				self.outfile.write("\n");

			cur += len(groups)
			self.printchunk(len(groups), cur=cur, total=len(self.groupnames), t=t, keytype="groups")

		self.notfound(found, self.groupnames)
			

	
	def notfound(self, found, i):
		if i-found:
			print "Did not find: ", i-found
	
	
	
	def printchunk(self, chunksize, cur, total, t, keytype="record"):
		percent = (cur / float(total))*100
		persec = chunksize / (time.time()-t)
		print "%s %0.1f @ %0.1f keys/sec"%(keytype, percent, persec)
			
	

db = emen2.db.admin.opendb()
d = Dumper(db=db)
