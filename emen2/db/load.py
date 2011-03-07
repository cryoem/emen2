import os
import time
import tarfile
import tempfile
import string
import random

import emen2.util.jsonutil
import emen2.util.listops


def random_password(N):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))



class Loader(object):
	def __init__(self, db, path=None):
		self.path = path
		self.db = db
	
	
	def load(self, rootemail=None, rootpw=None, warning=True):

		# Changed recids
		userrelmap = {}
		recidmap = {}

		# We're going to have to strip off children and save for later -- put* needs support for this..
		childmap = {}
		pdc = {}
		rdc = {}


		for user in self.loadfile("users.json"):
			origname = user.get("username")

			userrelmap[user.get('username')] = user.get('record')
			if user.get("record") != None:
				del user["record"]

			if user.get("username") == "root":
				if rootemail: user['email'] = rootemail
				if rootpw: user['password'] = rootpw

			# hmm..
			if user.get("password") == None:
				print "User %s has no password! Generating random pass.."%user.get('username')
				user["password"] = random_password(8)

			u = self.db.putuser(user, warning=warning)
			# if u.username != origname:
			# 	print "USERNAME CHANGED!", origname, u.username


		for pd in self.loadfile("paramdefs.json"):
			pdc[pd.get('name')] = pd.pop('children', set())
			pd.pop('parents', set())			
			self.db.putparamdef(pd, warning=warning)


		for rd in self.loadfile("recorddefs.json"):
			rdc[rd.get('name')] = rd.pop('children', set())
			rd.pop('parents', set())			
			self.db.putrecorddef(rd, warning=warning)


		# Put the saved relationships back in..
		for k, v in pdc.items():
			for v2 in v: self.db.pclink(k, v2, keytype='paramdef')
		
		for k, v in rdc.items():
			for v2 in v: self.db.pclink(k, v2, keytype='recorddef')



		chunk = []
		for rec in self.loadfile("records.json"):
			chunk.append(rec)
			if len(chunk) == 1000:
				self._commit_record_chunk(chunk, recidmap=recidmap, childmap=childmap)
				chunk = []


		if chunk:
			self._commit_record_chunk(chunk, recidmap=recidmap, childmap=childmap)




	def _commit_record_chunk(self, chunk, recidmap=None, childmap=None):
		t = time.time()
		childmap = childmap or {}
		recidmap = recidmap or {}
		recids = []
		
		for rec in chunk:
			if rec.get('children'):
				childmap[rec.get('recid')] = rec.get('children')
				del rec['children']
				del rec['parents']

			recids.append(rec.get('recid'))
			rec['recid'] = None

		recs = self.db.putrecord(chunk, clone=True)

		for oldrecid, newrecid in zip(recids, [rec.recid for rec in recs]):
			recidmap[oldrecid] = newrecid

		print "Commited %s recs in %s: %0.1f keys/s"%(len(recs), time.time()-t, len(recs)/(time.time()-t))
		
				

	def loadfile(self, infile):
		with open(os.path.join(self.path, infile)) as f:
			for item in f:
				if item:
					item = emen2.util.jsonutil.decode(item)
					yield item






if __name__ == "__main__":
	pass





		
# for user in users:
# 	if user.get('username') == 'root':
# 		user['password'] = rootpw
# 		user['email'] = rootemail
# 	self.adduser(user, ctx=ctx, txn=txn)
# 
# for group in groups:
# 	self.putgroup(group, ctx=ctx, txn=txn)
# 
# # Load skeletons -- use utils/export.py to create these JSON files
# paramdefs = load_skeleton('paramdefs')
# recorddefs = load_skeleton('recorddefs')
# users = load_skeleton('users')
# groups = load_skeleton('groups')
# 
# # We're going to have to strip off children and save for later -- put*def needs support for this..
# pdc = {}
# rdc = {}
# for pd in paramdefs:
# 	pdc[pd.get('name')] = pd.pop('children', set())
# 	self.putparamdef(pd, ctx=ctx, txn=txn)
# 
# for rd in recorddefs:
# 	rdc[rd.get('name')] = rd.pop('children', set())
# 	self.putrecorddef(rd, ctx=ctx, txn=txn)
# 
# for k, v in pdc.items():
# 	for v2 in v: self.pclink(k, v2, keytype='paramdef', ctx=ctx, txn=txn)
# 
# for k, v in rdc.items():
# 	for v2 in v: self.pclink(k, v2, keytype='recorddef', ctx=ctx, txn=txn)
# 
# # Put the 'Root' record first, so it will have recid 0
# # rootrec = self.newrecord('folder', ctx=ctx, txn=txn)
# # rootrec["name_folder"] = "Root Record"
# # self.putrecord(rootrec, ctx=ctx, txn=txn)
# 
# for user in users:
# 	if user.get('username') == 'root':
# 		user['password'] = rootpw
# 		user['email'] = rootemail
# 	self.putuser(user, ctx=ctx, txn=txn)
# 
# for group in groups:
# 	self.putgroup(group, ctx=ctx, txn=txn)
# 
# # Wait for the groups are committed -- then go back and add authenticated to recid 0
# # self.addgroups(0, ['authenticated'], ctx=ctx, txn=txn)


