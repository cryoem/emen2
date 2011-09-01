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
import emen2.util.listops

def random_password(N):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))



def setup(rootpw=None, rootemail=None, db=None):
	"""Initialize a new DB.
	@keyparam rootpw Root Account Password
	@keyparam rootemail Root Account email
	"""
	
	if not rootpw or not rootemail:
		import pwd
		import platform
		host = platform.node() or 'localhost'
		defaultemail = "%s@%s"%(pwd.getpwuid(os.getuid()).pw_name, host)

		print "\n=== New Database Setup ==="
		rootemail = rootemail or raw_input("Admin (root) email (default %s): "%defaultemail) or defaultemail
		rootpw = rootpw or getpass.getpass("Admin (root) password (default: none): ")

		while len(rootpw) < 6:
			if len(rootpw) == 0:
				print "Warning! No root password!"
				rootpw = ''
				break
			elif len(rootpw) < 6:
				print "Warning! If you set a password, it needs to be more than 6 characters."
				rootpw = getpass.getpass("Admin (root) password (default: none): ")

	loader = Loader(db=db, infile=emen2.db.config.get_filename('emen2', 'db/skeleton.json'))
	loader.load(rootemail=rootemail, rootpw=rootpw)



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
		for pd in self.loadfile(self.infile, keytype='paramdef'):
			pdc[pd.get('name')] |= set(pd.pop('parents', []))
			pd.pop('children', set())
			if pd.get('name') in existing_paramdefs and not overwrite:
				continue
			pds.append(pd)

		self.db.put(pds, keytype='paramdef', clone=True)

		# Put the saved relationships back in..
		for k, v in pdc.items():
			for v2 in v: self.db.pclink(v2, k, keytype='paramdef')


		##########################
		# USERS
		users = []
		if rootemail:
			users.append({'name':'root','email':rootemail, 'password':rootpw})
			
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

		self.db.put(users, keytype='user', clone=True)

		##########################
		# GROUPS
		groups = []
		for group in self.loadfile(self.infile, keytype='group'):
			if group.get('name') in existing_groupnames and not overwrite:
				continue
			groups.append(group)

		self.db.put(groups, keytype='group', clone=True)


		##########################
		# RECORDDEFS
		rds = []
		for rd in self.loadfile(self.infile, keytype='recorddef'):
			rdc[rd.get('name')] |= set(rd.pop('parents', []))
			rd.pop('children', set())
			if rd.get('name') in existing_recorddefs and not overwrite:
				continue
			rds.append(rd)

		self.db.put(rds, keytype='recorddef', clone=True)

		for k, v in rdc.items():
			for v2 in v: self.db.pclink(v2, k, keytype='recorddef')


		##########################
		# RECORDS
		# loaded in chunks of 100
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


		##########################
		# BDOS
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

		recs = self.db.put(chunk, keytype='record', clone=True)

		for oldname, newname in zip(names, [rec.name for rec in recs]):
			namemap[oldname] = newname

		print "Commited %s recs in %s: %0.1f keys/s"%(len(recs), time.time()-t, len(recs)/(time.time()-t))





def main():
	dbo = emen2.db.config.DBOptions()
	dbo.add_option('--new', action="store_true", help="Initialize a new DB with default items.")
	dbo.add_option('--path', type="string", help="Directory containing JSON files")
	dbo.add_option('--file', type="string", help="JSON file containing all keytypes")
	dbo.add_option('--nopassword', action="store_true", help="Do not prompt for root email or password")
	(options, args) = dbo.parse_args()
	db = dbo.opendb()

	with db:
		if options.new:
			if options.nopassword:
				setup(db=db, rootemail='root@localhost', rootpw='123456')
			else:
				setup(db=db)

		if options.file:
			l = Loader(infile=options.file, db=db)
			l.load()
		elif options.path:
			l = Loader(path=options.path, db=db)
			l.load()


if __name__ == "__main__":
        main()




