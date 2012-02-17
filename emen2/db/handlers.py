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


# Do NOT import ANY emen2 packages at the module level.


def thumbnail_from_binary(bdo, wait=True):
	"""given a binary instance, run the thumbnail builder as a child process"""
	import emen2.db.config
	tilepath = emen2.db.config.get('paths.TILEPATH')	
	filepath = bdo.get('filepath')
	filename = bdo.get('filename')
	name = bdo.get('name')

	# Note: In the future, this should find the right binary handler, then fork a child process
	# to run that handler and build thumbnails. However, since I switched to the plugin-based system
	# I still deciding how to proceed with invoking the right handler in a separate process WITHOUT
	# causing all of emen2 (e.g. config) to be opened each time. So, just run in process for now.
	try:
		handler = BinaryHandler.get_handler(filepath=filepath, filename=filename, name=name)
		handler.thumbnail(tilepath=tilepath)
	except Exception, e:
		print e


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

	def __init__(self, filename=None, filedata=None, fileobj=None, param='file_binary', filepath=None, name=None):
		self.filename = filename
		self.filedata = filedata
		self.fileobj = fileobj
		self.param = param
		self.readonly = True
		self.tmp = None

		# For testing and building binaries
		self.filepath = filepath
		self.name = name		
		

	def get(self, key, default=None):
		# Used for copying filename/filedata/fileobj/param into putbinary.
		return self.__dict__.get(key, default)


	##### Open the underlying data #####

	def open(self):
		'''Open the file'''
		if self.filepath:
			return open(self.filepath)

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

	def extract(self, **kwargs):
		return {}
		
	def thumbnail(self, **kwargs):
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
	def get_handler(cls, **kwargs):
		"""Return an appropriate file handler."""
		handler = None

		filename = kwargs.get('filename')		
		if filename:
			# Ignore compression
			f = filename.split(".")
			if f[-1] in ['gz', 'bz2', 'zip']:
				f.pop()
			# Use remaining file ext to find the handler
			if f:
				handler = f[-1]
			
		handler = cls._handlers.get(handler, cls)
		return handler(**kwargs)
	
	
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		