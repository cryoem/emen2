import time
import re
import traceback
import math

# import emen2.Database
import emen2.Database.dataobject
import emen2.Database.config
g = emen2.Database.config.g()



class Binary(emen2.Database.dataobject.BaseDBObject):
	"""This class defines a pointer to a binary file stored on disk. Contains the following metadata: ID, filename, associated record ID, filesize, md5 checksum, and if the file is compressed or not. The path to the file will be resolved dynamically when accessed based on the storage paths specified in the config.

	@attr name Identifier of the form: bdo:YYYYMMDDXXXXX, where YYYYMMDD is date format and XXXXX is 5-char hex ID code of file for that day
	@attr filename Filename
	@attr filepath Path to file on disk (built from config file when retrieved from db)
	@attr recid Record ID associated with file
	@attr filesize Size of file
	@attr md5 MD5 checksum of file
	@attr compress File is gzip compressed

	@attr creator
	@attr creationtime
	@attr modifyuser
	@attr modifytime

	"""

	attr_user = set(["filename", "compress", "filepath", "uri","recid","modifyuser","modifytime", "filesize", "md5","creator", "creationtime", "name"])

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
		"""Parse a 'bdo:2010010100001' type identifier into constituent parts to load from database and resolve location in the filesystem"""

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
			bdokey = emen2.Database.database.gettime()
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

