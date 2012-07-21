# $Id$
import time
import re
import os
import time
import tarfile
import StringIO
import cStringIO

import twisted.web.static

import jsonrpc.jsonutil

# emen2 imports
import emen2.web.resource
from emen2.web.view import View
import emen2.web.responsecodes
import emen2.db.exceptions
import emen2.db.handlers

@View.register
class Download(View):

	contentTypes = twisted.web.static.loadMimeTypes()

	contentEncodings = {
			".gz" : "gzip",
			".bz2": "bzip2"
			}

	defaultType = 'application/octet-stream'

	@View.add_matcher('^/download/$', name='multi')
	@View.add_matcher('^/download/(?P<bids>.+)/(?P<filename>.+)/$')
	def main(self, bids, filename=None, size=None, format=None, q=None):
		if not hasattr(bids, '__iter__'):
			bids = [bids]

		# Query for BDOs
		if q:
			bdos = self.db.binary.get(q=q)
		else:
			bdos = self.db.binary.get(bids)

		# Found what we needed; close the transaction
		return bdos
		


	def render_result(self, bdos, request, t=0, **_):
		# Process the returned BDOs into files to send
		size = request.args.get('size')
		format = request.args.get('format', 'jpg')
		files = {}
		cache = True
		
		for bdo in bdos:
			filename = bdo.get("filename")
			filepath = bdo.get("filepath")
			previewpath = emen2.db.binary.Binary.parse(bdo.get('name')).get('previewpath')
			
			if size:
				# Thumbnail requested
				thumbpath = '%s.%s.%s'%(previewpath, size, format)
				# print "Thumbnail: Checking for...", thumbpath
				if os.access(thumbpath, os.F_OK):
					# Return the thumbnail
					files[thumbpath] = '%s.%s.%s'%(filename, size, format)
				else:
					# Build the thumbnail; return a spinner image
					cache = False
					status = emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
					files[emen2.db.config.get_filename('emen2', 'web/static/images/handler.%s.png'%status)] = 'handler.%s.png'%status


			elif os.access(filepath, os.F_OK):
				# Found the file
				files[filepath] = filename
			
			else:
				# This will trigger render_eb if the file is not found
				raise IOError, "Could not access file"


		if len(files) > 1:
			return self._transfer_tar(files, request)
		
		return self._transfer_single(files, request, cache=cache)


	##### Process the result #####

	def _transfer_single(self, files, request, cache=True):
		# Download a single file
		filepath, filename = files.items()[0]
		mimetype, encoding = twisted.web.static.getTypeAndEncoding(filename, self.contentTypes, self.contentEncodings, self.defaultType)

		# If we're saving a gzip, we'll let the browser expand it by setting encoding:gzip.
		if filename[-3:] == ".gz":
			filename = filename[:-3]
			encoding = "gzip"

		fsize = os.stat(filepath).st_size
		f = open(filepath)

		if request.postpath[-1] == "save":
			request.setHeader('Content-Disposition', 'attachment; filename=%s'%filename.encode('utf-8'))

		request.setHeader('Content-Length', str(fsize))
		request.setHeader('Content-Type', mimetype)
		request.setHeader('Content-Encoding', encoding)
		if cache:
			request.setHeader('Cache-Control', 'max-age=86400')

		a = twisted.web.static.NoRangeStaticProducer(request, f)
		a.start()


	def _transfer_tar(self, files, request, cache=False):
		# Download multiple files using TarPipe
		request.setHeader('Content-Disposition', 'attachment; filename=archive.tar')
		request.setHeader('Content-Type', 'application/x-tar')
		request.setHeader('Content-Encoding', 'application/octet-stream')

		a = twisted.web.static.NoRangeStaticProducer(request, TarPipe(files))
		a.start()
		
		
		

class TarPipe(object):
	"""This class implements a compression pipe suitable for asynchronous
	process."""

	# ian: todo: stream in added gz files, and write compressed tar output. Basically repackaged a bunch of .gz's to a .tar.gz with non-gz's inside.
	def __init__(self, files={}):
		self.pos = 0
		self.files = files

		# StringIO.StringIO.__init__(self)
		self.cbuffer = cStringIO.StringIO()
		# self.cbuffer = ''
		self.tarfile = tarfile.open(mode='w|', fileobj=self)


	def close(self):
		pass


	def _addnextfile(self):
		if not self.files:
			return

		key = self.files.keys()[0]
		filename = self.files.pop(key)

		self.pos = 0
		self.cbuffer.seek(self.pos)
		self.cbuffer.truncate(0)

		self.tarfile.add(key, arcname=filename)
		# print "Added %s / %s.. buffer size is %s. %s files left"%(key, filename, 0, len(self.files))

		if len(self.files) == 0:
			# print "Closing tarfile"
			self.tarfile.close()

		self.cbuffer.seek(self.pos)


	def write(self, data):
		self.cbuffer.write(data)


	def read(self, size=65536):
		data = self.cbuffer.read(size) # [self.pos:self.pos+size]

		if len(data) == 0:
			self._addnextfile()
			data = self.cbuffer.read(size) #[self.pos:self.pos+size]

		self.pos += len(data)
		# print "set pos to %s"%self.pos

		return data



__version__ = "$Revision$".split(":")[1][:-1].strip()
