import os
import sys
import time
import tarfile
import tempfile
import string
import random
import collections

import emen2.util.jsonutil
import emen2.util.listops


def random_password(N):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))



class Loader(object):
	def __init__(self, db, path=None):
		self.path = path
		self.db = db
	
	
	def load(self, rootemail=None, rootpw=None, overwrite=False):

		# Changed names
		userrelmap = {}
		namemap = {}

		# We're going to have to strip off children and save for later
		childmap = collections.defaultdict(set)
		pdc = collections.defaultdict(set)
		rdc = collections.defaultdict(set)
		
		# Current items...
		existing_usernames = self.db.getusernames()
		existing_groupnames = self.db.getgroupnames()
		existing_paramdefs = self.db.getparamdefnames()
		existing_recorddefs = self.db.getrecorddefnames()

		##########################
		# PARAMDEFS
		pds = []
		for pd in self.loadfile("paramdefs.json"):
			pdc[pd.get('name')] |= set(pd.pop('children', []))
			pd.pop('parents', set())
			if pd.get('name') in existing_paramdefs and not overwrite:
				continue			
			pds.append(pd)
			
		self.db.put(pds, keytype='paramdef', clone=True)

		# Put the saved relationships back in..
		for k, v in pdc.items():
			for v2 in v: self.db.pclink(k, v2, keytype='paramdef')


		##########################
		# USERS
		users = []
		for user in self.loadfile("users.json"):
			if user.get('name') in existing_usernames and not overwrite:
				continue
				
			origname = user.get('name')

			userrelmap[user.get('name')] = user.get('record')
			if user.get("record") != None:
				del user["record"]

			if user.get('name') == "root":
				if rootemail != None: user['email'] = rootemail
				if rootpw != None: user['password'] = rootpw

			if not user.get('email') or user.get('email')=='None':
				user['email'] = '%s@localhost'%(user['name'])
			
			# hmm..
			if user.get('name') != 'root' and user.get("password") == None:
				print "User %s has no password! Generating random pass.."%user.get('name')
				user["password"] = random_password(8)
			
			users.append(user)
			
		self.db.put(users, keytype='user', clone=True)


		##########################
		# GROUPS
		groups = []
		for group in self.loadfile("groups.json"):
			if group.get('name') in existing_groupnames and not overwrite:
				continue
			groups.append(group)
			
		self.db.put(groups, keytype='group', clone=True)


		##########################
		# RECORDDEFS
		rds = []
		for rd in self.loadfile("recorddefs.json"):
			rdc[rd.get('name')] |= set(rd.pop('children', []))
			rd.pop('parents', set())			
			if rd.get('name') in existing_recorddefs and not overwrite:
				continue
			rds.append(rd)

		self.db.put(rds, keytype='recorddef', clone=True)
		
		for k, v in rdc.items():
			for v2 in v: self.db.pclink(k, v2, keytype='recorddef')


		##########################
		# RECORDS
		# loaded in chunks of 100
		chunk = []
		for rec in self.loadfile("records.json"):
			chunk.append(rec)
			if len(chunk) == 1000:
				self._commit_record_chunk(chunk, namemap=namemap, childmap=childmap)
				chunk = []

		if chunk:
			self._commit_record_chunk(chunk, namemap=namemap, childmap=childmap)

		for k, v in childmap.items():
			for v2 in v:
				self.db.pclink(namemap[k], namemap[v2])
		
		
		##########################
		# BDOS
		for bdo in self.loadfile("bdos.json"):
			# BDO names have colons -- this can cause issues on filesystems, so we change : -> . and back again
			infile = bdo['name'].replace(":",".")
			if not os.path.exists(infile):
				infile = None

			# use subscript instead of .get to make sure the record was mapped
			# self.db.put(bdokey=bdo.get('name'), record=namemap[bdo.get('record')], filename=bdo.get('filename'), infile=infile, clone=bdo)

		
			


	def _commit_record_chunk(self, chunk, namemap=None, childmap=None):
		t = time.time()
		names = []
		
		for rec in chunk:
			if rec.get('children'):
				childmap[rec.get('name')] |= set(rec.get('children', []))
				del rec['children']
			if rec.get('parents'):
				del rec['parents']

			names.append(rec.get('name'))
			rec['name'] = None

		recs = self.db.put(chunk, keytype='record', clone=True)

		for oldname, newname in zip(names, [rec.name for rec in recs]):
			namemap[oldname] = newname

		print "Commited %s recs in %s: %0.1f keys/s"%(len(recs), time.time()-t, len(recs)/(time.time()-t))
		

				

	def loadfile(self, infile):
		try:
			with open(os.path.join(self.path, infile)) as f:
				for item in f:
					if item:
						item = emen2.util.jsonutil.decode(item)
						yield item
		except Exception, inst:
			print "Could not read %s: %s"%(infile, inst)
			






if __name__ == "__main__":
	# try:
	# 	path = sys.argv[1]
	# except:
	# 	path = "."
		
	parser = emen2.db.config.DBOptions()
	(options, args) = parser.parse_args()

	path = "."
	if len(args) > 0:
		path=args[0]

	import emen2.db.admin
	db = emen2.db.admin.opendb()

	with db:
		l = Loader(path=path, db=db)
		l.load()	




