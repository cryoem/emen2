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
		##??
		if not hasattr(bids, '__iter__'):
			bids = [bids]

		# Query for BDOs
		if q:
			bdos = self.db.getbinary(q=q)
		else:
			bdos = self.db.getbinary(bids)

		# Found what we needed; close the transaction
		return bdos
		


	def render_cb(self, bdos, request, t=0, **_):
		# Override the EMEN2Resource default render callback
		files = {}
		for bdo in bdos:
			filename = bdo.get("filename")
			filepath = bdo.get("filepath")

			# If we're looking for a particular size or format..
			size = request.args.get('size')
			format = request.args.get('format', 'jpg')
			if size:
			 	thumbname = '%s.%s.%s'%(bdo.name.replace(':', '.'), size, format)
				filepath = os.path.join(emen2.db.config.get('paths.TILEPATH'), thumbname)
				if not os.access(filepath, os.F_OK):
					# Start the thumbnail build, return a spinner image.
					# ian: todo: thumbnail_from_binary could return an error image if failure.
					emen2.db.handlers.thumbnail_from_binary(bdo, wait=True)
					# filepath = emen2.db.config.get_filename('emen2', 'web/static/images/spinner.gif')
					
				files[filepath] = "%s.%s.%s"%(filename, size, format)
			else:
				files[filepath] = filename
			
			
			# This will trigger render_eb if the file is not found
			if not os.access(filepath, os.F_OK):
				raise IOError, "Could not access file"

		if len(files) > 1:
			return self._transfer_tar(files, request)
		
		return self._transfer_single(files, request)


	##### Process the result #####

	def _transfer_single(self, files, request):
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

		a = twisted.web.static.NoRangeStaticProducer(request, f)
		a.start()


	def _transfer_tar(self, files, request):
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
