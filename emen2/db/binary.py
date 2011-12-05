# $Id$
"""Database support for Binary attachments.

Classes:
	Binary: Binary (attachment) DBO
	BinaryDB: BTree for storing and access Binary instances
"""

import time
import re
import traceback
import math
import os

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile

# EMEN2 imports
import emen2.db.btrees
import emen2.db.dataobject
import emen2.db.config
import emen2.db.exceptions


class Binary(emen2.db.dataobject.BaseDBObject):
	"""Binary file stored on disk and managed by EMEN2.

	Provides following attributes:
		filename, record, md5, filesize, compress, filepath

	The Binary name has a specific format, bdo:YYYYMMDDXXXXX, where YYYYMMDD is
	date format and XXXXX is 5-char hex ID code of file for the day.

	The filename attribute is the original name of the uploaded file. The
	filesize attribute is the uncompressed size of the file, and the md5
	attribute is the MD5 checksum of the uncompressed file. The filename may be
	changed by an owner after a Binary is committed, but the contents (filesize
	and md5) cannot be changed. Files may be compressed after they have been
	created; in this case, the compress param will specify the compression
	scheme (gzip, bz2, etc.) and filesize_compress and md5_compress will have
	values for the compressed file.

	File names are checked to prevent illegal characters, and names such as "."
	and invalid file names on some platforms ("COM", "NUL", etc.).

	If the file is stored compressed on disk, the compressed attribute will
	contain either True (gzip compressed) or the compression scheme used.

	Binaries are generally associated with a Record, stored in the record
	attribute. Read permission on a Binary requires either ownership of the
	item, or read permission on the associated Record. The owner of the Binary
	can change which Record is associated.

	When a Binary is retrieved from the database, the filepath property will
	be accessible. This points to the physical file on disk containing the data.

	These BaseDBObject methods are extended:

		init			Set attributes
		setContext		Check read permissions and bind Context
		validate_name	Check the access protocol (bdo:YYYYMMDDXXXXX)
		validate		Check required attributes

	And the following method is provided:

		parse			Parse name


	:attr filename: File name
	:attr filesize: Size of the uncompressed file
	:attr md5: MD5 checksum of the uncompressed file
	:attr filesize_compress: Size of the compressed file
	:attr md5_compress: MD5 checksum of the compressed file
	:attr compress: File is gzip compressed
	:attr record: Associated Record
	:property filepath: Path to the file on disk
	"""
	# In the
	# future, the name will be a URN scheme, where 'bdo' is an access protocol
	# and the name is dependent on the scheme.

	attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(["filepath", "filename", "record", "compress", "filesize", "md5", "filesize_compress", "md5_compress"])
	filepath = property(lambda x:x._filepath)

	def init(self, d):
		self.__dict__['filename'] = None
		self.__dict__['record'] = None
		self.__dict__['md5'] = None
		self.__dict__['filesize'] = None
		self.__dict__['compress'] = False
		self.__dict__['filesize_compress'] = None
		self.__dict__['md5_compress'] = None
		self._filepath = None

	def setContext(self, ctx):
		super(Binary, self).setContext(ctx=ctx)
		self.__dict__['_filepath'] = self.parse(self.name).get('filepath')
		if self.isowner():
			return True
		if self.record is not None:
			rec = self._ctx.db.getrecord(self.record, filt=False)

	def validate_name(self, name):
		"""Validate the name of this object"""
		if name in ['None', None]:
			return
		return self.parse(name)['name']

	# filepath is set during setContext, and discarded during commit (todo)
	def _set_filepath(self, key, value, vtm=None, t=None):
		return set()

	# These immutable attributes only ever be set for a new Binary, before commit
	def _set_md5(self, key, value, vtm=None, t=None):
		if self.name:
			raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())

	def _set_md5_compress(self, key, value, vtm=None, t=None):
		if self.name:
			raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())

	def _set_compress(self, key, value, vtm=None, t=None):
		if self.name:
			raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())

	def _set_filesize(self, key, value, vtm=None, t=None):
		if self.name:
			raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())

	def _set_filesize_compress(self, key, value, vtm=None, t=None):
		if self.name:
			raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
		return self._set(key, value, self.isowner())

	# These can be changed normally
	def _set_filename(self, key, value, vtm=None, t=None):
		# Sanitize filename.. This will allow unicode characters,
		#	and check for reserved filenames on linux/windows
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

	def _set_record(self, key, value, vtm=None, t=None):
		return self._set(key, int(value), self.isowner())

	def validate(self, vtm=None, t=None):
		# Validate
		if self.filesize <= 0:
			raise emen2.db.exceptions.ValidationError, "No file specified"
		if not all([self.filename, self.md5, self.filesize >= 0]):
			raise emen2.db.exceptions.ValidationError, "Filename, filesize, and MD5 checksum are required"
		# This requirement has been relaxed.
		# if self.record is None:
		#	raise emen2.db.exceptions.ValidationError, "Record reference is required"

	# Write contents to a temporary file.
	def writetmp(self, filedata=None, fileobj=None):
		'''Write to temporary storage.
		:return: Temporary file path, the file size, and an md5 digest.
		'''
		if filedata:
			fileobj = cStringIO.StringIO(filedata)
		if not fileobj:
			raise ValueError, "No data to write to temporary file."

		fileobj.seek(0)

		# In narrow circumstances, this might not be the same filesystem
		# as the final file destination. So use a higher level tool like
		# shutil to rename the file, instead of just os.rename.
		dkey = self.parse('')

		if not os.path.exists(dkey['basepath']):
			os.makedirs(dkey['basepath'])
		(fd, tmpfile) = tempfile.mkstemp(dir=dkey['basepath'], suffix='.upload')

		m = hashlib.md5()
		filesize = 0
		# Copy to the output file, updating md5 and size
		with os.fdopen(fd, "w+b") as f:
			for line in fileobj:
				f.write(line)
				m.update(line)
				filesize += len(line)

		md5sum = m.hexdigest()
		emen2.db.log.info("Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfile, filesize, md5sum))
		# Update filesize/md5
		self.__dict__['filesize'] = filesize
		self.__dict__['md5'] = md5sum
		return tmpfile

	@staticmethod
	def parse(bdokey, counter=None):
		"""Parse a 'bdo:2010010100001' type identifier into constituent parts
		and resolve location in the filesystem."""

		prot, _, bdokey = (bdokey or "").rpartition(":")
		if not prot:
			prot = "bdo"

		# ian: todo: implement other BDO protocols, e.g. references to uris
		if prot not in ["bdo"]:
			raise Exception, "Invalid binary protocol: %s"%prot

		if bdokey:
			# Now process; must be 14 chars long..
			year = int(bdokey[:4])
			mon = int(bdokey[4:6])
			day = int(bdokey[6:8])
			if counter == None:
				counter = int(bdokey[9:13],16)
		else:
			# Timestamps are now in ISO8601 format
			# e.g.: "2011-10-16T02:00:00Z"
			bdokey = emen2.db.database.gettime()
			year = int(bdokey[:4])
			mon = int(bdokey[5:7])
			day = int(bdokey[8:10])
			counter = counter or 0

		# YYYYMMDD
		datekey = "%04d%02d%02d"%(year, mon, day)

		# Get the binary storage paths from config
		binarypaths = emen2.db.config.get('paths.BINARYPATH')

		# Find the last item matching the current date
		mp = [x for x in sorted(binarypaths.keys()) if str(x)<=datekey]
		base = binarypaths[mp[-1]]

		# Resolve the parsed bdo key to a directory (basepath) and file (filepath)
		basepath = "%s/%04d/%02d/%02d/"%(base, year, mon, day)
		filepath = os.path.join(basepath, "%05X"%counter)

		# The BDO name (bdo:YYYYMMDDXXXXX)
		name = "%s:%s%05X"%(prot, datekey, counter)

		return {
			"prot":prot,
			"year":year,
			"mon":mon,
			"day":day,
			"counter":counter,
			"datekey":datekey,
			"basepath":basepath,
			"filepath":filepath,
			"name":name
			}


class BinaryDB(emen2.db.btrees.DBODB):
	"""DBODB for Binaries

	Extends:
		update_sequence		Binaries are assigned a name based on date
		openindex			Indexed by: filename (maybe md5 in future)

	"""
	sequence = True
	dataclass = Binary

	# Update the database sequence.. Probably move this to the parent class.
	def update_sequence(self, items, txn=None):
		"""Assign a name based on date, and the counter for that day."""
		# Which recs are new?
		newrecs = [i for i in items if i.name < 0]
		dkey = emen2.db.binary.Binary.parse('')
		datekey = dkey['datekey']
		name = dkey['name']

		# Get a blank bdo key
		if newrecs:
			basename = self._set_sequence(delta=len(newrecs), key=datekey, txn=txn)

		for offset, newrec in enumerate(newrecs):
			dkey = emen2.db.binary.Binary.parse(name, counter=offset+basename)
			newrec.__dict__['name'] = dkey['name']
			newrec.__dict__['filepath'] = dkey['filepath']

		return {}

	def openindex(self, param, txn=None):
		"""Index on filename (and possibly MD5 in the future.)"""
		if param == 'filename':
			ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
		elif param == 'md5':
			ind = emen2.db.btrees.IndexDB(filename=self._indname(param), dbenv=self.dbenv)
		else:
			ind = super(BinaryDB, self).openindex(param, txn=txn)
		return ind



__version__ = "$Revision$".split(":")[1][:-1].strip()
