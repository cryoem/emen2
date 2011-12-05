# $Id$
"""Load a dumped database

Classes:
	BaseLoader
	Loader
"""

import os
import sys
import time
import tarfile
import tempfile
import string
import random
import collections
import getpass

import jsonrpc.jsonutil

# EMEN2 imports
import emen2.util.listops

def random_password(N):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))



class BaseLoader(object):
	def __init__(self, db=None, infile=None, path=''):
		self.infile = infile
		self.path = path
		# We will be using the private DB api somewhat..
		self.db = db


	def loadfile(self, infile=None, keytype=None):
		infile = infile or self.infile
		filename = os.path.join(self.path or '', infile or '')
		if not os.path.exists(filename):
			return

		with open(os.path.join(self.path, infile)) as f:
			for item in f:
				item = item.strip()
				if item and not item.startswith('/'):
					item = jsonrpc.jsonutil.decode(item)
					if keytype:
						if keytype == item.get('keytype'):
							# print item
							yield item
					else:
						yield item



class Loader(BaseLoader):
	def load(self, overwrite=False):
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


		##### PARAMDEFS #####

		pds = []
		for pd in self.loadfile(self.infile, keytype='paramdef'):
			pdc[pd.get('name')] |= set(pd.pop('parents', []))
			pd.pop('children', set())
			if pd.get('name') in existing_paramdefs and not overwrite:
				continue
			pds.append(pd)

		self.db.put(pds, keytype='paramdef')

		# Put the saved relationships back in..
		for k, v in pdc.items():
			for v2 in v: self.db.pclink(v2, k, keytype='paramdef')


		##### USERS #####

		users = []
		for user in self.loadfile(self.infile, keytype='user'):
			if user.get('name') in existing_usernames and not overwrite:
				continue

			origname = user.get('name')

			userrelmap[user.get('name')] = user.get('record')
			if user.get("record") != None:
				del user["record"]

			if not user.get('email') or user.get('email')=='None':
				user['email'] = '%s@localhost'%(user['name'])

			# hmm..
			if user.get("password") == None:
				print "User %s has no password! Generating random pass.."%user.get('name')
				user["password"] = random_password(8)

			users.append(user)

		self.db.put(users, keytype='user')


		##### GROUPS #####

		groups = []
		for group in self.loadfile(self.infile, keytype='group'):
			if group.get('name') in existing_groupnames and not overwrite:
				continue
			groups.append(group)

		self.db.put(groups, keytype='group')


		##### RECORDDEFS #####

		rds = []
		for rd in self.loadfile(self.infile, keytype='recorddef'):
			rdc[rd.get('name')] |= set(rd.pop('parents', []))
			rd.pop('children', set())
			if rd.get('name') in existing_recorddefs and not overwrite:
				continue
			rds.append(rd)

		self.db.put(rds, keytype='recorddef')

		for k, v in rdc.items():
			for v2 in v: self.db.pclink(v2, k, keytype='recorddef')


		##### RECORDS #####

		# loaded in chunks of 1000
		chunk = []
		for rec in self.loadfile(self.infile, keytype='record'):
			chunk.append(rec)
			if len(chunk) == 1000:
				self._commit_record_chunk(chunk, namemap=namemap, childmap=childmap)
				chunk = []

		if chunk:
			self._commit_record_chunk(chunk, namemap=namemap, childmap=childmap)

		for k, v in childmap.items():
			for v2 in v:
				self.db.pclink(namemap[k], namemap[v2])


		##### BDOS #####

		# for bdo in self.loadfile(self.infile, keytype='binary'):
		# 	# BDO names have colons -- this can cause issues on filesystems, so we change : -> . and back again
		# 	infile = bdo['name'].replace(":",".")
		# 	if not os.path.exists(infile):
		# 		infile = None
		#
		#	 use subscript instead of .get to make sure the record was mapped
		#	 self.db.put(bdokey=bdo.get('name'), record=namemap[bdo.get('record')], filename=bdo.get('filename'), infile=infile, clone=bdo)


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

		recs = self.db.put(chunk, keytype='record')

		for oldname, newname in zip(names, [rec.name for rec in recs]):
			namemap[oldname] = newname

		print "Commited %s recs in %s: %0.1f keys/s"%(len(recs), time.time()-t, len(recs)/(time.time()-t))





def main():
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--path', type="string", help="Directory containing JSON files")
	dbo.add_option('--file', type="string", help="JSON file containing all keytypes")
	(options, args) = dbo.parse_args()
	db = dbo.opendb()

	with db:
		if options.file:
			l = Loader(infile=options.file, db=db)
			l.load()
		elif options.path:
			l = Loader(path=options.path, db=db)
			l.load()


if __name__ == "__main__":
        main()




