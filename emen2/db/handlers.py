# $Id: handlers.py,v 1.39 2013/02/28 00:49:55 irees Exp $
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
import sys

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile

##########################################################
# ** Do NOT import ANY EMEN2 or EMAN2 packages here!! ** #
##########################################################

def thumbnail_from_binary(bdo, force=False, wait=False, priority=0):
    """Given a Binary instance, run the thumbnail builder as a separate process
    
    Returns a status:
        "completed"
        "building"
        "error"

    """
    # Import the EMEN2 modules here to prevent circular imports.
    import emen2.db.config
    import emen2.db.binary
    import emen2.db.queues
    
    # Paths and filenames
    previewpath = emen2.db.binary.Binary.parse(bdo.get('name')).get('previewpath')
    filepath = bdo.get('filepath')
    filename = bdo.get('filename')

    # Sanitize the filename to check compress= and ext=
    ext = ''
    compress = ''
    r = re.compile('[\w\-\.]', re.UNICODE)
    _filename = "".join(r.findall(filename)).lower()
    _filename = _filename.split(".")
    if _filename and _filename[-1] in ['gz', 'bz2']:
        compress = _filename.pop()
    if _filename:
        ext = _filename.pop()

    # Get the handler.
    handler = BinaryHandler.get_handler(filepath=filepath, filename=filename)

    # If the thumbnail is currently building, or an error occurred previously,
    # then return that status.
    status = handler.thumbnail_status(previewpath)
    if status in ["building", "error"]:
        return status
    
    # Prepare the command to run.
    
    # Grumble... Come up with a better way to get the script name.
    args = [sys.executable]
    cmd = emen2.db.config.get_filename(handler.__module__)
    fix = ['.pyc', '.pyo']
    if cmd[-4:] in fix:
        for f in fix:
            cmd = cmd.replace(f, '.py')

    args.append(cmd)

    # Add the command arguments.
    args.append('--previewpath')
    args.append(previewpath)
    
    if compress:
        args.append('--compress')
        args.append(compress)

    args.append(handler.__class__.__name__)
    args.append(filepath)
    
    if wait:
        # Run directly and wait.
        a = subprocess.Popen(args)
        a.wait()
        return "complete"
    
    # Otherwise, add to the task queue.
    emen2.db.queues.processqueue.add_task(args, name=filepath, priority=priority)
    return "building"
    
    

def main(g):
    """Use a Handler to build a thumbnail."""
    # g is the module namespace...
    parser = ThumbnailOptions()
    options, (handler, filepath) = parser.parse_args()
    
    filename = 'filename'
    if options.ext:
        filename = '%s.%s'%(filename, options.ext)
    if options.compress:
        filename = '%s.%s'%(filename, options.compress)
    
    # Get the handler and build the thumbnail.
    handler = g[handler](filepath=filepath, filename=filename)
    handler.thumbnail(previewpath=options.previewpath, force=options.force)
    
    
    
##### Exceptions and Options #####    

class ThumbnailError(Exception):
    pass


class ThumbnailOptions(optparse.OptionParser):
    """Options to run a Binary thumbnail generator."""
    
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, *args, **kwargs)
        self.add_option('--previewpath', type="string", help="Base output")
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
    '''EMEN2 managed file.

    This is used in a few different ways. It is used for files uploaded
    to the web server. It can also be used with the File Handlers defined
    below (e.g. to extract header metadata.) Handlers can also be passed
    as items to db.binary.put.
    
    The original name of the file is self.filename. Sources can be a added in
    the constructor, and may be a string of data (filedata), or a file-like
    object supporting read() (fileobj). Consider the data to be read-only.
    '''

    # The self._getfilepath() method will return an on-disk filename that can be used
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
        # ian: note... doesn't have to be set during init -- the 
        # web resource will do it later for PUT/POST'd files.
        self.filepath = filepath
        self.filedata = filedata
        self.fileobj = fileobj
        # if not any([self.filepath, self.filedata, self.fileobj]):
        #    raise ThumbnailError, "No data; can be filepath, filedata, or fileobj."


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

    # Making this a private method for now
    def _getfilepath(self, suffix=None):
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
        # TODO: Set as self.filepath, for subsequent calls to self._getfilepath().
        # TODO: Should probably fine a better way to remove the tmpfile.
        self._tmpfiles.append(tmpfile)
        return tmpfile

    def close(self):
        # Remove temporary files...
        for f in self._tmpfiles:
             os.remove(f)


    ##### Extract metadata and build thumbnails #####

    def extract(self, **kwargs):
        return {}

    def thumbnail(self, previewpath, force=False):
        fp = self._getfilepath()
        if not os.access(fp, os.F_OK):
            raise ThumbnailError, "Could not access: %s"%fp

        # This is used in self._outfile()
        self._previewpath = previewpath

        # Make sure the output directory exists..
        pdir = os.path.dirname(self._previewpath)
        if not os.path.exists(pdir):
            try:
                os.makedirs(pdir)
            except OSError:
                pass

        # Create a status file to indicate work on this thumbnail has started
        statusfile = self._outfile('status')
        
        # Write out "building" to the status file.
        with file(statusfile, 'w') as f:
            f.write("building")

        # Check compression and file type
        compress = False
        ext = ''
        if self.filename:
            fn = self.filename.split(".")
            if fn[-1] == 'gz':
                compress = 'gzip'
                fn.pop()
            ext = fn.pop()

        # Build the thumbnail.
        if compress and not self._allow_gzip:
            # This handler does not accept gzip'd files, for whatever reason.
            pass
            
        elif compress:
            # Decompress the file
            workfile = tempfile.mkstemp(suffix='.tmp')[1]
            cmd = "%s -d -c %s > %s"%(compress, fp, workfile)
            os.system(cmd)
            try:
                self._thumbnail_build(workfile)
            except Exception, e:
                emen2.db.log.error("Could not build tiles: %s"%e)
                pass
            os.remove(workfile)
        else:
            self._thumbnail_build(fp)

        # Finished the thumbnail; remove the status file.
        try:
            os.remove(statusfile)
        except:
            pass

    def _thumbnail_build(self, workfile, **kwargs):
        # Override this method to actually build the thumbnails.
        pass

    def thumbnail_status(self, previewpath):
        """Check the thumbnail status from the status file."""
        self._previewpath = previewpath
        
        if not os.access(self.filepath, os.F_OK):
            return "error"
        
        statusfile = self._outfile('status')
        if not os.access(statusfile, os.F_OK):
            return "completed"
        
        f = open(statusfile, "r")
        status = f.read().strip()
        f.close()
        return status

    def _outfile(self, suffix):
        return '%s.%s'%(self._previewpath, suffix)

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
            if f[-1].lower() in ['gz', 'bz2', 'zip']:
                f.pop()
            # Use remaining file ext to find the handler
            if f:
                handler = f[-1].lower()
            
        handler = cls._handlers.get(handler, cls)
        return handler(**kwargs)
    
    
    
    
    
@BinaryHandler.register(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'ai', 'pdf', 'eps', 'mpeg'])
class ImageHandler(BinaryHandler):
    def build_scale(self, img, outfile, tilesize=256):
        # ImageMagick...
        # convert -resize 128x128 -background white -gravity center -format jpg -quality 75 bdo:2010011400000  bdo:2010011400000.thumb.jpg
        args = []
        args.append('convert')
        
        args.append('-resize')
        args.append('%sx%s'%(tilesize, tilesize))

        args.append('-gravity')
        args.append('center')
        
        args.append('-format')
        args.append('jpg')
        
        args.append('-quality')
        args.append('80')
        
        if tilesize <= 128:
            args.append('-extent')
            args.append('%sx%s'%(tilesize, tilesize))

        args.append(img)
        args.append(outfile)

        a = subprocess.Popen(args)
        a.wait()
        

    def _thumbnail_build(self, workfile):
        self.build_scale(workfile, self._outfile('thumb.jpg'), tilesize=128)
        self.build_scale(workfile, self._outfile('small.jpg'), tilesize=512)
        self.build_scale(workfile, self._outfile('medium.jpg'), tilesize=1024)

    
        
        
if __name__ == "__main__":
    main(globals())
        
        
        
