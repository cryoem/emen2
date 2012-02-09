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

class BinaryHandler(object):
	'''EMEN2 managed file.'''

	# This is used in a few different ways. It is used for files uploaded
	# to the web server. It can also be used with the File Handlers defined
	# below (e.g. to extract header metadata.) These can also be passed
	# as items to db.putbinary() and stored as database Binary attachments.
	# 
	# The original name of the file is self.filename. Sources can be a added in
	# the constructor, and may be a string of data (filedata), or a file-like
	# object supporting read() (fileobj). Consider the data to be read-only.
	# 
	# The writetmp() method will return an on-disk filename that can be used
	# for operations that required a named file (e.g. EMAN2.) If the input
	# source is filedata or fileobj, it will write out to a temporary file in
	# the normal temp file storage area. The close() method will remove any
	# temporary files.
	
	# File type handlers
	_handlers = {}

	def __init__(self, filename=None, filedata=None, fileobj=None, param='file_binary', binary=None):
		self.filename = filename
		self.filedata = filedata
		self.fileobj = fileobj
		self.param = param
		self.binary = binary
		self.readonly = True
		self.tmp = None

	def get(self, key, default=None):
		# Used for copying filename/filedata/fileobj/param into putbinary.
		return self.__dict__.get(key, default)


	##### Open the underlying data #####

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

	##### Extract metadata and build thumbnails #####

	def extract(self):
		return {}
		
	def thumbnail(self):
		pass

	##### Handler registration #####

	@classmethod
	def register(cls, names):
		def f(o):
			for name in names:
				if name in cls._handlers:
					raise ValueError("""File handler %s already registered""" % name)
				cls._handlers[name] = o
			return o
		return f

	@classmethod
	def get_handler(cls, filename=None, filedata=None, fileobj=None, param='file_binary', binary=None):
		"""Return an appropriate file handler."""
		handler = None
		if binary and not filename:
			filename = binary.get('filename')
		
		if filename:
			f = filename.split(".")
			if f[-1] in ['gz', 'bz2', 'zip']:
				f.pop()
			if f:
				handler = f[-1]
			
		handler = cls._handlers.get(handler, cls)
		return handler(filename=filename, filedata=filedata, fileobj=fileobj, param=param, binary=binary)
	
	
	@classmethod
	def thumbnail_from_binary(cls, binary, **options):
		handler = cls.get_handler(binary=binary)
		handler.thumbnail(**options)
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		