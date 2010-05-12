import time
import re
import traceback
import math
import UserDict

import emen2.globalns
g = emen2.globalns.GlobalNamespace('')

# validation
import emen2.Database.subsystems.dataobject
import emen2.Database.subsystems.dbtime


class Binary(emen2.Database.subsystems.dataobject.BaseDBObject):
	"""This class defines a pointer to a binary file stored on disk. The path to the file will be built dynamically based on the storage paths specified in the config. These are not designed to be changed manually; they are only created and managed by DB public methods.

	@attr name Identifier of the form: bdo:YYYYMMDDXXXXX, where YYYYMMDD is date format and XXXXX is 5-char hex ID code of file for that day
	@attr filename Filename
	@attr filepath Path to file on disk (built from config file when retrieved from db)
	@attr recid Record ID associated with file
	@attr filesize Size of file
	@attr md5 MD5 checksum of file
	@attr compress File is gzip compressed
	@attr creator Creator
	@attr creationtime Creation time
	@attr modifyuser Last change user
	@attr modifytime Last change time

	"""

	validators = []

	@property
	def attr_user(self):
		return set(["filename", "compress", "filepath", "uri","recid","modifyuser","modifytime", "filesize", "md5"])


	@property
	def attr_admin(self):
		return set(["creator", "creationtime", "name"])


	#@property
	#def _ctx(self):
	#	return self._ctx


	attr_vartypes = {
		"recid":"int",
		"filename":"string",
		"uri":"string",
		"modifyuser":"user",
		"modifytime":"datetime",
		"creator":"user",
		"creationtime":"datetime",
		"name":"str",
		"md5":"str",
		"filesize":"int"
		}


	@staticmethod
	def parse(bdokey, counter=None):

		prot, _, bdokey = (bdokey or "").rpartition(":")

		if not prot:
			prot = "bdo"

		# ian: todo: implement other BDO protocols, e.g. references to uris
		if prot not in ["bdo"]:
			raise Exception, "Invalid binary storage protocol: %s"%prot


		# Now process; must be 14 chars long..
		if bdokey:
			year = int(bdokey[:4])
			mon = int(bdokey[4:6])
			day = int(bdokey[6:8])
			counter = int(bdokey[9:13],16)

		else:
			bdokey = emen2.Database.subsystems.dbtime.gettime()
			year = int(bdokey[:4])
			mon = int(bdokey[5:7])
			day = int(bdokey[8:10])
			counter = counter or 0


		datekey = "%04d%02d%02d"%(year, mon, day)

		mp = [x for x in sorted(g.BINARYPATH.keys()) if str(x)<=datekey]
		base = g.BINARYPATH[mp[-1]]

		basepath = "%s/%04d/%02d/%02d/"%(base, year, mon, day)
		filepath = basepath + "%05X"%counter
		name = "%s:%s%05X"%(prot, datekey, counter)

		return {"prot":prot, "year":year, "mon":mon, "day":day, "counter":counter, "datekey":datekey, "basepath":basepath, "filepath":filepath, "name":name}

