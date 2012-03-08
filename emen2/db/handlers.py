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
import optparse
import subprocess

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile


#################################################
# ** Do NOT import ANY emen2 packages here!! ** #
#################################################

def thumbnail_from_binary(bdo, force=False, wait=True):
	"""Given a Binary instance, run the thumbnail builder as a separate process"""
	import emen2.db.config
	tilepath = emen2.db.config.get('paths.TILEPATH')
	filepath = bdo.get('filepath')
	filename = bdo.get('filename')
	basename = bdo.get('name')
	
	# Sanitize the filename and pass compress= and ext=
	ext = ''
	compress = ''
	r = re.compile('[\w\-\.]', re.UNICODE)
	_filename = "".join(r.findall(filename)).lower()
	_filename = _filename.split(".")
	if _filename and _filename[-1] in ['gz', 'bz2']:
		compress = _filename.pop()
	if _filename:
		ext = _filename.pop()

	# Get the handler, check if we're going to build the thumbnail
	handler = BinaryHandler.get_handler(filepath=filepath, filename=filename)
	if not handler.file_exists():
		return
	if handler.thumbnail_exists(force=force):
		return

	# Prepare the command to run
	# grumble...
	args = []
	cmd = emen2.db.config.get_filename(handler.__module__)
	fix = ['.pyc', '.pyo']
	if cmd[-4:] in fix:
		for f in fix:
			cmd = cmd.replace(f, '.py')

	# Use a specific Python interpreter if configured
	python = emen2.db.config.get('EMAN2.EMAN2PYTHON')
	if python:
		args.append(python)

	args.append(cmd)
	args.append('--tilepath')
	args.append(tilepath)
	
	args.append('--basename')
	args.append(basename)
	
	if ext:
		args.append('--ext')
		args.append(ext)
	
	if compress:
		args.append('--compress')
		args.append(compress)

	args.append(handler.__class__.__name__)
	args.append(filepath)
		
	print "Generating thumbnails: %s"%args
	a = subprocess.Popen(args)
	if wait:
		a.wait()
	

def main(g):
	"""Use a Handler to build a thumbnail."""
	parser = ThumbnailOptions()
	options, (handler, filepath) = parser.parse_args()
	
	filename = (options.name or 'filename').replace(':', '')
	if options.ext:
		filename = '%s.%s'%(filename, options.ext)
	if options.compress:
		filename = '%s.%s'%(filename, options.compress)
	
	handler = g[handler](filepath=filepath, filename=filename)
	handler.thumbnail(basename=options.basename, tilepath=options.tilepath, force=options.force)
	

class ThumbnailError(Exception):
	pass



class ThumbnailOptions(optparse.OptionParser):
	"""Options to run a Binary thumbnail generator"""
	
	def __init__(self, *args, **kwargs):
		optparse.OptionParser.__init__(self, *args, **kwargs)
		self.add_option('--tilepath', type="string", help="Output directory; default is current directory")
		self.add_option('--basename', type="string", help="Binary name")
		self.add_option('--ext', type="string", help="Original filename extension")
		self.add_option('--compress', type="string", help="Compression type")
		self.add_option('--force', action="store_true", help="Force rebuild")
		usage = """%prog [options] <handler class> <input file>"""

	def parse_args(self, lc=True, *args, **kwargs):
		options, args = optparse.OptionParser.parse_args(self,  *args, **kwargs)
		if len(args) < 2:
			raise ValueError, "Handler class name and input file required"
		return options, args



##### File handler #####

class BinaryHandler(object):
	'''EMEN2 managed file.'''

	# This is used in a few different ways. It is used for files uploaded
	# to the web server. It can also be used with the File Handlers defined
	# below (e.g. to extract header metadata.) These can also be passed
	# as items to db.putbinary().
	# 
	# The original name of the file is self.filename. Sources can be a added in
	# the constructor, and may be a string of data (filedata), or a file-like
	# object supporting read() (fileobj). Consider the data to be read-only.
	# 
	# The getfilepath() method will return an on-disk filename that can be used
	# for operations that required a named file (e.g. EMAN2.) If the input
	# source is filedata or fileobj, it will write out to a temporary file in
	# the normal temp file storage area. The close() method will remove any
	# temporary files.
	
	# File type handlers
	_handlers = {}
	_allow_gzip = False

	def __init__(self, filename, filedata=None, fileobj=None, filepath=None, param='file_binary'):
		# Original filename
		self.filename = filename
		if not self.filename:
			raise ThumbnailError, "Filename required"

		# Parameter in the associated record
		self.param = param
		
		# Temporary files
		self._tmpfiles = []

		# One of the following is required: filepath / filedata / fileobj
		self.filepath = filepath
		self.filedata = filedata
		self.fileobj = fileobj
		if not any([self.filepath, self.filedata, self.fileobj]):
			raise ThumbnailError, "No data; can be filepath, filedata, or fileobj."

	def get(self, key, default=None):
		return self.__dict__.get(key, default)


	##### Open the underlying data #####
		
	def open(self):
		'''Open the file.
		:return: File-like object
		'''
		
		if self.filepath:
			# If there is a filepath, open and return that
			return open(self.filepath, "r")

		readfile = None
		if self.filedata:
			# Take a StringIO or string and make a StringIO
			readfile = cStringIO.StringIO(self.filedata)
		elif self.fileobj:
			# ... use the fileobj
			self.fileobj.seek(0)
			readfile = self.fileobj
		else:
			raise IOError, "No file given, or don't know how to read file.."
		return readfile

	def getfilepath(self, suffix=None):
		'''Write to temporary storage.
		:return: Temporary file path.
		'''
		
		if self.filepath:
			# If there is a filepath, return that
			return self.filepath
		
		# .. or copy the filedata/fileobj to a temporary file
		infile = self.open()

		# Make a temporary file
		suffix = suffix or '.tmp'
		(fd, tmpfile) = tempfile.mkstemp(suffix=suffix)
		with os.fdopen(fd, "w+b") as f:
			shutil.copyfileobj(infile, f)

		# infile.close()
			
		# TODO: Set as self.filepath, for subsequent calls to self.getfilepath().

		# TODO: Should probably fine a better way to remove the tmpfile.
		self._tmpfiles.append(tmpfile)
		return tmpfile

	def close(self):
		# Remove temporary files...
		for f in self._tmpfiles
		 	os.remove(f)
		


	##### Extract metadata and build thumbnails #####

	def extract(self, **kwargs):
		return {}

	def thumbnail(self, basename, tilepath, force=False):
		if not basename or not tilepath:
			raise ThumbnailError, "Base filename (basename) and output path (tilepath) are required."
		
		fp = self.getfilepath()
		if not os.access(fp, os.F_OK):
			raise ThumbnailError, "Could not access %s"%fp

		# These are used in self.getfilename()
		self._basename = basename
		self._tilepath = tilepath

		# Create a lock file to indicate work on this thumbnail has started
		lockfile = self.outfile('lock')
		if os.access(lockfile, os.F_OK) and not force:
			raise ThumbnailError, "Thumbnail already exists, or a previous attempt to build the thumbnail failed."

		with file(lockfile, 'w') as f:
			f.write(str(os.getpid()))

		# Check compression and file type
		compress = False
		ext = ''
		if self.filename:
			fn = self.filename.split(".")
			if fn[-1] == 'gz':
				compress = 'gzip'
				fn.pop()
			ext = fn.pop()

		if compress and not self._allow_gzip:
			# This handler does not accept gzip'd files, for whatever reason.
			pass
		elif compress:
			workfile = tempfile.mkstemp(suffix='.tmp')[1]
			cmd = "%s -d -c %s > %s"%(compress, fp, workfile)
			print "Decompressing: ", cmd
			os.system(cmd)
			try:
				self._thumbnail_build(workfile)
			except Exception, e:
				print "Could not build tiles:", e
				pass
			os.remove(workfile)				

		else:
			self._thumbnail_build(fp)

	def _thumbnail_build(self, workfile, **kwargs):
		pass

	def thumbnail_exists(self, force=False):
		"""Check if the file exists, or there is a current lock file."""
		if force:
			return False
		lockfile = self.outfile('lock')
		return os.access(lockfile, os.F_OK)

	def outfile(self, suffix):
		# Strip out the ":" in the binary name
		f = self._basename.replace(':', '.')
		return str(os.path.join(self._tilepath, '%s.%s'%(f, suffix)))

	def file_exists(self):
		return os.access(self.filepath, os.F_OK)

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
	
	
		
		
		
if __name__ == "__main__":
	main(globals())
		
		
		
		
		
		
		
		
		
		
		
