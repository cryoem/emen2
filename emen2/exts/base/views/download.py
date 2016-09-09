# $Id: download.py,v 1.34 2013/05/14 09:19:12 irees Exp $
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

def renamefile(filename, count=0):
    if not count:
        return filename
    parts = filename.split(".")
    fn = parts[:-1] + ["%s"%count] + parts[-1:]
    return ".".join(fn)

@View.register
class Download(View):

    contentTypes = twisted.web.static.loadMimeTypes()

    contentEncodings = {
            ".gz" : "gzip",
            ".bz2": "bzip2"
            }

    defaultType = 'application/octet-stream'

    @View.add_matcher('^/download/$', name='multi')
    @View.add_matcher('^/download/(?P<bids>[^/]*)/(?P<filename>[^/]*)/$')
    @View.add_matcher('^/binary/(?P<bids>[^/]*/)/$', name='binary')
    def main(self, bids, filename=None, size=None, format=None, q=None, rename=None, tar=None):
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
        rename = request.args.get('rename', False)
        tar = request.args.get('tar', None)
        files = {}
        cache = True
        
        for bdo in bdos:
            name = bdo.get('name', 'none')
            record = bdo.get('record', 'none')
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
                if rename == 'name':
                    filename = "%s.%s"%(bdo.get('name', 'none').replace('bdo:', ''), filename)
                elif rename == 'record':
                    filename = "%s.%s"%(bdo.get('record', 'none'), filename)
                files[filepath] = filename
            
            else:
                # This will trigger render_eb if the file is not found
                raise IOError, "Could not access file"

        # Check for files that have the same name...
        seen = []
        for k,v in files.items():
            if v in seen:
                files[k] = renamefile(v, count=seen.count(v)+1)
            seen.append(v)
            
        if tar or len(files) > 1:
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
        t = emen2.db.database.utcnow()[:10]
        request.setHeader('Content-Disposition', 'attachment; filename=archive-%s.tar'%t)
        request.setHeader('Content-Type', 'application/x-tar')
        request.setHeader('Content-Encoding', 'application/octet-stream')
        a = twisted.web.static.NoRangeStaticProducer(request, TarPipe(files))
        a.start()
        

class TarPipe(object):
    def __init__(self, files={}):
        self.files = files
        self.buffer = cStringIO.StringIO()
        self.tarfile = tarfile.open(mode='w', fileobj=self.buffer)

    def close(self):
        pass

    def _addnextfile(self):
        if not self.files:
            # print "...Closing tarfile"
            self.tarfile.close()
            return
            
        key = self.files.keys()[0]
        filename = self.files.pop(key)

        self.buffer.seek(0)
        self.buffer.truncate(0)
        
        # print "Adding %s: %s... %s files left"%(key, filename, len(self.files))
        self.tarfile.add(key, arcname=filename)
        self.buffer.seek(0)

    def read(self, size=256**2):
        data = self.buffer.read(size)
        if not data:
            self._addnextfile()
            data = self.buffer.read(size)
        return data




__version__ = "$Revision: 1.34 $".split(":")[1][:-1].strip()
