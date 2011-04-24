# $Id$

import time
import re
import traceback
import math
import os

# For file writing
import shutil
import hashlib
import cStringIO
import md5
import tempfile

import emen2.db.btrees
import emen2.db.dataobject

import emen2.db.config
g = emen2.db.config.g()





# ian: todo: better job at cleaning up broken files..
def write_binary(infile, ctx=None, txn=None):
	"""(Internal) Behind the scenes -- read infile out to a temporary file.
	The temporary file will be renamed to the final destination when everything else is cleared.
	@keyparam infile
	@keyparam dkey Binary Key -- see Binary.parse
	@return Temporary file path, the file size, and an md5 digest.
	"""
	# ian: todo: allow import by using a filename.

	# Get the basepath for the current storage area
	dkey = emen2.db.binary.Binary.parse('')

	closefd = True
	if hasattr(infile, "read"):
		# infile is a file-like object; do not close
		closefd = False
	else:
		# string data..
		infile = cStringIO.StringIO(infile)

	# Make the directory
	try:
		os.makedirs(dkey["basepath"])
	except:
		pass

	# Write out file to temporary storage in the day's basepath
	(fd, tmpfilepath) = tempfile.mkstemp(suffix=".upload", dir=dkey["basepath"])
	m = hashlib.md5()
	filesize = 0

	with os.fdopen(fd, "w+b") as f:
		for line in infile:
			f.write(line)
			m.update(line)
			filesize += len(line)

	if filesize == 0 and not ctx.checkadmin():
		raise ValueError, "Empty file!"

	if closefd:
		infile.close()

	md5sum = m.hexdigest()
	print "Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfilepath, filesize, md5sum)
	g.log.msg('LOG_INFO', "Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfilepath, filesize, md5sum))

	return tmpfilepath, filesize, md5sum




class Binary(emen2.db.dataobject.BaseDBObject):
	"""This class defines a pointer to a binary file stored on disk. Contains the following metadata: ID, filename, associated record ID, filesize, md5 checksum, and if the file is compressed or not. The path to the file will be resolved dynamically when accessed based on the storage paths specified in the config.

	@attr name Identifier of the form: bdo:YYYYMMDDXXXXX, where YYYYMMDD is date format and XXXXX is 5-char hex ID code of file for that day
	@attr filename Filename
	@attr filepath Path to file on disk (built from config file when retrieved from db)
	@attr record Record ID associated with file
	@attr filesize Size of file
	@attr md5 MD5 checksum of file
	@attr compress File is gzip compressed
	"""

	# These can all be set.. need to write validators.
	param_user = emen2.db.dataobject.BaseDBObject.param_user | set(["filename", "record", "compress", "filepath", "filesize", "md5"])	
	param_all = emen2.db.dataobject.BaseDBObject.param_all | param_user
	

	def init(self, d):
		self.__dict__['filename'] = None
		self.__dict__['record'] = None
		self.__dict__['md5'] = None
		self.__dict__['filesize'] = None
		self.__dict__['compress'] = False
		# ian: todo: handle filepath.
		

	def setContext(self, ctx=None):
		super(Binary, self).setContext(ctx=ctx)
		self.filepath = self.parse(self.name).get('filepath')

		if self.isowner():
			return True
			
		if self.record is not None:	
			rec = self._ctx.db.getrecord(self.record, filt=False)
			
		
	def validate_name(self, name):
		"""Validate the name of this object"""		
		if name in ['None', None]:
			return
		return self.parse(name)['name']


	def _set_md5(self, key, value, warning=False, vtm=None, t=None):
		if self.name != None:
			raise KeyError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())


	def _set_compress(self, key, value, warning=False, vtm=None, t=None):
		if self.name != None:
			raise KeyError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())


	def _set_filesize(self, key, value, warning=False, vtm=None, t=None):
		if self.name != None:
			raise KeyError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())
		

	def _set_filename(self, key, value, warning=False, vtm=None, t=None):
		# Sanitize filename.. This will allow unicode characters, and check for reserved filenames on linux/windows
		filename = value
		filename = "".join([i for i in filename if i.isalpha() or i.isdigit() or i in '.()-=_'])
		if filename.upper() in ['..', '.', 'CON', 'PRN', 'AUX', 'NUL',
										'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
										'COM6', 'COM7', 'COM8', 'COM9', 'LPT1',
										'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
										'LPT7', 'LPT8', 'LPT9']:
			filename = "renamed."+filename
		value = unicode(filename)
		return self._set(key, value, self.isowner())
	
	
	def validate(self, warning=False, vtm=None, t=None):
		if not self.filename or not self.md5 or not self.filesize >= 0:
			raise ValueError, "Binary needs filename, md5, and filesize."
		if self.record is None:
			raise ValueError, "Binary needs to reference a Record."
			
		

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
			if counter == None:
				counter = int(bdokey[9:13],16)

		else:
			bdokey = emen2.db.database.gettime() # "2010/10/10 01:02:03"
			year = int(bdokey[:4])
			mon = int(bdokey[5:7])
			day = int(bdokey[8:10])
			counter = counter or 0


		datekey = "%04d%02d%02d"%(year, mon, day)

		mp = [x for x in sorted(g.paths.BINARYPATH.keys()) if str(x)<=datekey]
		base = g.paths.BINARYPATH[mp[-1]]

		basepath = "%s/%04d/%02d/%02d/"%(base, year, mon, day)
		filepath = os.path.join(basepath, "%05X"%counter)
		name = "%s:%s%05X"%(prot, datekey, counter)

		return {"prot":prot, "year":year, "mon":mon, "day":day, "counter":counter, "datekey":datekey, "basepath":basepath, "filepath":filepath, "name":name}





class BinaryBTree(emen2.db.btrees.DBOBTree):
	def init(self):
		self.setkeytype('s', False)
		self.setdatatype('p', Binary)
		self.sequence = True
		super(BinaryBTree, self).init()		


	# Update the database sequence.. Probably move this to the parent class.
	def update_sequence(self, items, txn=None):
		# Which recs are new?
		newrecs = [i for i in items if i.name < 0]
		dkey = emen2.db.binary.Binary.parse('')
		datekey = dkey['datekey']
		name = dkey['name']

		# Get a blank bdo key
		if newrecs:
			basename = self.get_sequence(delta=len(newrecs), key=datekey, txn=txn)

		for offset, newrec in enumerate(newrecs):
			dkey = emen2.db.binary.Binary.parse(name, counter=offset+basename)
			newrec.__dict__['name'] = dkey['name']			
			newrec.__dict__['filepath'] = dkey['filepath']

		return {}
			

	def openindex(self, param, create=False):
		if param == 'filename':
			return emen2.db.btrees.IndexBTree(filename="index/bdosbyfilename", keytype="s", datatype="s", dbenv=self.dbenv)







__version__ = "$Revision$".split(":")[1][:-1].strip()
