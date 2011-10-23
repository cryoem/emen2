# $Id$
"""Dump database contents

Classes:
	Dumper
"""

import os
import time
import tarfile
import tempfile
import string
import random
import shutil

import jsonrpc.jsonutil

# EMEN2 imports
import emen2.db.config
import emen2.util.listops



class Dumper(object):

	def __init__(self, db, root=None, outfile=None, names=None, addfiles=True, uri=None, **kwargs):
		mtime = time.time()
		self.root = root		
		self.uri = uri
		
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
		self.paramdefs_binary = set()

		# Initial items..
		if self.root != None:
			names = self.db.getchildren(self.root, recurse=-1)
			names.add(self.root)
		else:
			names = set()
		
		allgroup = set()
		alluser = set()
		allparamdef = set()
		allrecorddef = set()
		allbdos = set()
		
		if kwargs.get('all') or kwargs.get('allrecord'):
			names |= self.db.getchildren(0, recurse=-1)
		if kwargs.get('all') or kwargs.get('allgroup'):
			allgroup = self.db.getgroupnames()
		if kwargs.get('all') or kwargs.get('alluser'):
			alluser = self.db.getusernames()
		if kwargs.get('all') or kwargs.get('allparamdef'):
			allparamdef = self.db.getparamdefnames()
		if kwargs.get('all') or kwargs.get('allrecorddef'):
			allrecorddef = self.db.getrecorddefnames()		
		if kwargs.get('all') or kwargs.get('allbinary'):
			pass
			
		if kwargs.get('core'):
			addfiles = False
			kwargs['user'] = False
			kwargs['group'] = False
			kwargs['binary'] = False
			kwargs['paramdef'] = True
			kwargs['recorddef'] = True
			allparamdef = self.db.getchildren('core', keytype='paramdef')
			allparamdef |= set(['root','core'])
			allrecorddef = self.db.getchildren('core', keytype='recorddef')
			allrecorddef |= set(['root','core'])
	

		print "Starting with %s records"%len(names)		
		self.checkrecords(names, addgroups=allgroup, addusers=alluser, addparamdefs=allparamdef, addrecorddefs=allrecorddef, addbdos=allbdos)

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
		
		if kwargs.get('all') or kwargs.get('paramdef') or kwargs.get('allparamdef'):
			self.addfile(self.writetmp(self.dumpparamdefs), "paramdefs.json")

		if kwargs.get('all') or kwargs.get('recorddef') or kwargs.get('allrecorddef'):
			self.addfile(self.writetmp(self.dumprecorddefs), "recorddefs.json")

		if kwargs.get('all') or kwargs.get('user') or kwargs.get('alluser'):
			self.addfile(self.writetmp(self.dumpusers), "users.json")

		if kwargs.get('all') or kwargs.get('group') or kwargs.get('allgroup'):
			self.addfile(self.writetmp(self.dumpgroups), "groups.json")

		if kwargs.get('all') or kwargs.get('record') or kwargs.get('allrecord'):		
			self.addfile(self.writetmp(self.dumprecords), "records.json")

		if kwargs.get('all') or kwargs.get('binary') or kwargs.get('allbinary'):
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
				f.write(jsonrpc.jsonutil.encode(item))
				f.write("\n")
		return filename
		

	def checkrecords(self, names, addgroups=None, addusers=None, addparamdefs=None, addrecorddefs=None, addbdos=None):
			
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
				if self.uri:
					rec.uri = '%s/record/%s'%(self.uri, rec.name)
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
				if self.uri:
					pd.uri = '%s/paramdef/%s'%(self.uri, pd.name)
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
				if self.uri:
					rd.uri = '%s/recorddef/%s'%(self.uri, rd.name)				
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
			users = self.db.getuser(chunk)
			found |= set([user.name for user in users])
		
			for user in users:
				if self.uri:
					user.uri = '%s/user/%s'%(self.uri, user.name)
				
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
				if self.uri:
					group.uri = '%s/group/%s'%(self.uri, group.name)
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
				if self.uri:
					bdo.uri = '%s/binary/%s'%(self.uri,bdo.name)				
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
	dbo.add_option('--all', action='store_true', help='Export Everything')
	
	dbo.add_option('--paramdef', action='store_true', help='Export Found ParamDefs')
	dbo.add_option('--recorddef', action='store_true', help='Export Found RecordDefs')
	dbo.add_option('--record', action='store_true', help='Export Found Records')
	dbo.add_option('--user', action='store_true', help='Export Found Users')
	dbo.add_option('--group', action='store_true', help='Export Found Groups')
	dbo.add_option('--binary', action='store_true', help='Export Found Binaries')
	
	dbo.add_option('--allparamdef', action='store_true', help='Export All ParamDefs')
	dbo.add_option('--allrecorddef', action='store_true', help='Export All RecordDefs')
	dbo.add_option('--allrecord', action='store_true', help='Export All Records')
	dbo.add_option('--alluser', action='store_true', help='Export All Users')
	dbo.add_option('--allgroup', action='store_true', help='Export All Groups')
	dbo.add_option('--allbinary', action='store_true', help='Export All Binaries')

	dbo.add_option('--root', type="int", help="Root Record")
	dbo.add_option('--uri', type="string", help="Export with base URI")
	dbo.add_option('--core', action="store_true", help="Just dump core parameters and protocols")

	(options, args) = dbo.parse_args()

	copy_to_kw = {}
	for key in ['core', 'all','paramdef','recorddef','user','group','binary','allparamdef','allrecorddef','allrecord','alluser','allgroup','allbinary']:
		v = getattr(options, key, None)
		if v != None:
			copy_to_kw[key] = v

	db = dbo.opendb()
	with db:
		d = Dumper(db=db, root=options.root, uri=options.uri, **copy_to_kw)
	


if __name__ == "__main__":
	main()















