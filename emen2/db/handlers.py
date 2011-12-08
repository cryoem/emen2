# $Id$
'''File handlers

'''
import shutil
import time
import re
import collections
import traceback
import math
import os
import signal

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile

# EMEN2 imports
import emen2.db.config
import emen2.db.exceptions
import emen2.db.log


##### File handler #####

class EMEN2File(object):
	'''File.

	This is used in a few different ways. It is used for files uploaded
	to the web server. It can also be used with the File Handlers defined
	below (e.g. to extract header metadata.) These can also be passed
	as items to db.putbinary() and stored as database Binary attachments.

	The original name of the file is self.filename. Sources can be a added in
	the constructor, and may be a string of data (filedata), or a file-like
	object supporting read() (fileobj). Consider the data to be read-only.

	The writetmp() method will return an on-disk filename that can be used
	for operations that required a named file (e.g. EMAN2.) If the input
	source is filedata or fileobj, it will write out to a temporary file in
	the normal temp file storage area. The close() method will remove any
	temporary files.
	'''

	def __init__(self, filename, filedata=None, fileobj=None, param='file_binary'):
		self.filename = filename
		self.filedata = filedata
		self.fileobj = fileobj
		self.param = param
		self.readonly = True
		self.tmp = None

	def get(self, key, default=None):
		# Used for copying filename/filedata/fileobj/param into putbinary.
		return self.__dict__.get(key, default)

	def open(self):
		'''Open the file'''
		readfile = None
		if self.filedata:
			# This is fine; strings are immutable,
			# cStringIO will reuse the buffer
			readfile = cStringIO.StringIO(self.filedata)
		elif self.fileobj:
			# ... use the fileobj
			self.fileobj.seek(0)
			readfile = self.fileobj
		else:
			raise IOError, "No file given, or don't know how to read file.."
		return readfile

	def close(self):
		# Should remove temporary file...
		pass

	def writetmp(self, path=None, suffix=None):
		'''Write to temporary storage.
		:return: Temporary file path.
		'''
		# Get a file handle
		infile = self.open()

		# Make a temporary file
		args = {}
		if suffix:
			args['suffix'] = suffix
		if path:
			args['dir'] = path

		(fd, tmpfile) = tempfile.mkstemp(**args)
		with os.fdopen(fd, "w+b") as f:
			shutil.copyfileobj(infile, f)

		return tmpfile

	def extract(self):
		return {}

		
##### File handlers #####

class Handler(object):
	rectypes = []
	extensions = []
	_handlers = {}

	def __init__(self, files=None):
		self.files = files

	def extract(self):
		return {}

	def thumbnail(self, f):
		pass

	def filter_ext(sef, files, exts):
		ret = []
		for f in files:
			b, _, ext = f.filename.rpartition(".")
			if ext.lower() in exts:
				ret.append(f)
		return ret

	@classmethod
	def register(cls, name):
		def f(o):
			if name in cls._handlers:
				raise ValueError("""Handler %s already registered""" % name)
			# emen2.db.log.info("REGISTERING HANDLER (%s)"% name)
			cls._handlers[name] = o
			return o
		return f

	@classmethod
	def get_handler(cls, handler):
		return cls._handlers.get(handler, cls)

